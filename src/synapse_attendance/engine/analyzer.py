# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.3.0-20250907 (Refactored for robustness, readability, and modular structure)

import toml
import requests
import logging
import re
from pathlib import Path
import pandas as pd
import warnings
import numpy as np
from typing import Dict, Any
from synapse import __version__
from django.utils.translation import gettext_lazy as _, gettext


# ==============================================================================
# Translatable Strings for rules.toml
# This block is ONLY for Django's makemessages command to find these strings
# since the .toml file is loaded from a remote URL and cannot be scanned directly.
# These strings are used for report column headers and downloaded filenames.
# ==============================================================================
_("Name")
_("Attendance Days")
_("Total Overtime (h)")
_("Late Count")
_("Early Quit Count")
_("Absent Days")
_("Total Late (min)")
_("Total Early Quit (min)")
_("Missing Punch Count")
_("Missing Punch Details")
_("Manual Review Details")
_("Attendance Report")
_("Public")
_("Detailed")
_("Report")
_("Missing Punch")
_("Manual Review Needed")
_("Unrecognized Status at")
# ==============================================================================

logger = logging.getLogger(__name__)


class AttendanceAnalyzer:
    """
    A rule-driven engine for attendance data analysis.

    This engine processes raw punch data from an Excel file and generates summary
    reports based on a flexible set of rules. It uses a three-stage pipeline for
    clarity and robustness, designed for high maintainability.
    """

    VERSION = __version__

    def __init__(self, rules_path: str = None, remote_rules_url: str = None):
        """Initializes the analyzer and loads the rule set."""
        self.df: pd.DataFrame | None = None
        self.summary_df: pd.DataFrame | None = None
        self.is_loaded: bool = False
        self.is_analyzed: bool = False
        self.rules: Dict[str, Any] = self._load_rules(rules_path, remote_rules_url)

    # ==========================================================================
    # SECTION A: PUBLIC API & ORCHESTRATION
    # ==========================================================================

    def load_data_from_file(self, file_path_or_obj) -> bool:
        """Loads and pre-processes attendance data from an Excel file."""
        try:
            self.df = self._helper_read_excel(file_path_or_obj)
            if self.df is None:
                return False
            self._helper_clean_and_validate_data()
            self.is_loaded = True
            return True
        except Exception as e:
            logger.error("Failed to load data from file: %s", e, exc_info=True)
            return False

    def analyze(self):
        """Runs the full three-stage analysis pipeline."""
        if not self.is_loaded:
            raise ValueError("Data is not loaded. Call load_data_from_file() first.")
        if not self.rules:
            raise ValueError("Rules are not loaded. Cannot perform analysis.")

        logger.info("Starting analysis v%s...", self.VERSION)
        self._stage1_calculate_raw_deltas()
        self._stage2_analyze_work_units()
        self._stage3_generate_summary_reports()
        self.is_analyzed = True
        logger.info("Analysis complete.")

    def get_detailed_summary(self) -> pd.DataFrame | None:
        return self._get_report("detailed_columns")

    def get_public_summary(self) -> pd.DataFrame | None:
        return self._get_report("public_columns")

    def get_raw_processed_dataframe(self) -> pd.DataFrame | None:
        return self.df if self.is_loaded else None

    # ==========================================================================
    # SECTION B: STAGE-WISE PIPELINE IMPLEMENTATION
    # ==========================================================================

    def _stage1_calculate_raw_deltas(self):
        """Calculates raw time differences for lateness and early quits."""
        logger.debug("Pipeline - Stage 1: Calculating raw time deltas...")
        should_punch_time = pd.to_datetime(
            self.df["应打卡时间"], format="%H:%M", errors="coerce"
        )
        actual_punch_time = pd.to_datetime(
            self.df["实际打卡时间"], format="%H:%M", errors="coerce"
        )
        delta_minutes = (actual_punch_time - should_punch_time).dt.total_seconds() / 60
        is_on_duty = self.df["打卡类型"] == "上班"
        is_off_duty = self.df["打卡类型"] == "下班"
        self.df["raw_late_minutes"] = np.where(
            is_on_duty & (delta_minutes > 0), delta_minutes, 0
        ).round()
        self.df["raw_early_quit_minutes"] = np.where(
            is_off_duty & (delta_minutes < 0), -delta_minutes, 0
        ).round()

    def _stage2_analyze_work_units(self):
        """Applies a clear, priority-based business logic pipeline to each work unit."""
        logger.debug("Pipeline - Stage 2: Applying policies to work units...")
        metric_cols = [
            "attendance_units",
            "absent_units",
            "missing_punch_count",
            "late_count",
            "late_minutes",
            "early_quit_count",
            "early_quit_minutes",
            "voluntary_overtime_minutes",
            "punitive_overtime_minutes",
        ]
        for col in metric_cols:
            self.df[col] = 0.0
        self.df["missing_punch_review_details"] = ""
        self.df["manual_review_details"] = ""

        att_policy = self.rules["attendance_policy"]
        punches_per_unit = att_policy["punches_per_unit"]
        trip_keywords = att_policy.get("business_trip_keywords", [])

        def build_strict_prefix_regex(key):
            prefixes = att_policy.get(key, [])
            if not prefixes:
                return "$^"
            escaped_prefixes = [re.escape(p) for p in prefixes]
            suffix_pattern = r"(?: |\(|（|\d+分钟|$)"
            return f"^(?:{'|'.join(escaped_prefixes)}){suffix_pattern}"

        ignored_regex = build_strict_prefix_regex("ignored_prefixes")
        manual_review_regex = build_strict_prefix_regex("manual_review_prefixes")
        valid_regex = build_strict_prefix_regex("valid_punch_prefixes")
        missing_regex = build_strict_prefix_regex("missing_punch_prefixes")
        trip_regex = "|".join(trip_keywords) if trip_keywords else "$^"

        self.df["work_unit_is_am"] = (
            pd.to_datetime(
                self.df["应打卡时间"], format="%H:%M", errors="coerce"
            ).dt.hour
            < 13
        )
        employee_list = self.df["姓名"].unique()
        grouped = self.df.groupby(["姓名", "日期", "work_unit_is_am"])

        for group_key, group in grouped:
            name, date, is_am = group_key
            unit_str = f"{date} ({'AM' if is_am else 'PM'})"

            is_business_trip = (
                group["假勤申请"].str.contains(trip_regex, na=False, regex=True).any()
            )
            if is_business_trip:
                self.df.loc[group.index[0], "attendance_units"] = 1
                continue

            clean_group = group[
                ~group["打卡状态"].str.contains(ignored_regex, na=False, regex=True)
            ]
            if len(clean_group) > punches_per_unit:
                clean_group = self._policy_clean_duplicate_punches(clean_group)

            valid_punches = clean_group[
                clean_group["打卡状态"].str.contains(valid_regex, na=False, regex=True)
            ]
            valid_count = len(valid_punches)
            missing_count = (
                clean_group["打卡状态"]
                .str.contains(missing_regex, na=False, regex=True)
                .sum()
            )
            manual_review_explicit_count = (
                clean_group["打卡状态"]
                .str.contains(manual_review_regex, na=False, regex=True)
                .sum()
            )
            total_clean_records = len(clean_group)
            known_records_count = (
                valid_count + missing_count + manual_review_explicit_count
            )
            unknown_records_count = total_clean_records - known_records_count

            if (
                valid_count == punches_per_unit
                and total_clean_records == punches_per_unit
            ):
                self._policy_process_attended_unit(valid_punches)
            elif (
                missing_count == punches_per_unit
                and total_clean_records == punches_per_unit
            ):
                self.df.loc[group.index[0], "absent_units"] = 1
            elif valid_count > 0 and missing_count > 0:
                missing_punch_mask = group["打卡状态"].str.contains(
                    missing_regex, na=False, regex=True
                )
                self.df.loc[group.index[missing_punch_mask], "missing_punch_count"] = 1
                details_text = f"{_('Missing Punch')}: {unit_str}"
                self.df.loc[group.index[0], "missing_punch_review_details"] = (
                    details_text
                )
            else:
                if manual_review_explicit_count > 0:
                    details_text = f"{_('Manual Review Needed')}: {unit_str}"
                    self.df.loc[group.index[0], "manual_review_details"] = details_text
                if unknown_records_count > 0:
                    all_statuses = clean_group["打卡状态"]
                    is_valid = all_statuses.str.contains(
                        valid_regex, na=False, regex=True
                    )
                    is_missing = all_statuses.str.contains(
                        missing_regex, na=False, regex=True
                    )
                    is_manual = all_statuses.str.contains(
                        manual_review_regex, na=False, regex=True
                    )
                    unhandled_statuses = all_statuses[
                        ~(is_valid | is_missing | is_manual)
                    ]
                    unhandled_texts = ", ".join(unhandled_statuses.tolist())
                    details_text = (
                        f"{_('Unrecognized Status at')} {unit_str}: '{unhandled_texts}'"
                    )
                    self.df.loc[group.index[0], "manual_review_details"] = details_text
                if missing_count > 0:
                    self.df.loc[
                        group.index[
                            group["打卡状态"].str.contains(
                                missing_regex, na=False, regex=True
                            )
                        ],
                        "missing_punch_count",
                    ] = 1

        self.df.drop(columns=["work_unit_is_am"], inplace=True)

    def _stage3_generate_summary_reports(self):
        """Aggregates all metrics and creates the final summary report."""
        agg_map = {
            "attendance_units": ("attendance_units", "sum"),
            "absent_units": ("absent_units", "sum"),
            "missing_punch_count": ("missing_punch_count", "sum"),
            "late_count": ("late_count", "sum"),
            "total_late_minutes": ("late_minutes", "sum"),
            "early_quit_count": ("early_quit_count", "sum"),
            "total_early_quit_minutes": ("early_quit_minutes", "sum"),
            "voluntary_overtime_minutes": ("voluntary_overtime_minutes", "sum"),
            "punitive_overtime_minutes": ("punitive_overtime_minutes", "sum"),
            "missing_punch_review_details": (
                "missing_punch_review_details",
                lambda x: "\n".join(s for s in x if s),
            ),
            "manual_review_details": (
                "manual_review_details",
                lambda x: "\n".join(s for s in x if s),
            ),
        }
        summary = self.df.groupby("姓名").agg(**agg_map).reset_index()
        summary["attendance_days"] = summary["attendance_units"] / 2
        summary["absent_days"] = summary["absent_units"] / 2
        summary["total_overtime_hours"] = self._policy_calculate_overtime_hours(summary)
        self.summary_df = summary

    # ==========================================================================
    # SECTION C: POLICY HELPERS (Called by Stage 2 & 3)
    # ==========================================================================

    def _policy_process_attended_unit(self, group: pd.DataFrame):
        """Processes a single, valid 'Attended Unit'."""
        on_duty_group = group[group["打卡类型"] == "上班"]
        off_duty_group = group[group["打卡类型"] == "下班"]
        if on_duty_group.empty or off_duty_group.empty:
            return
        on_duty_row = on_duty_group.iloc[0]
        off_duty_row = off_duty_group.iloc[0]
        self.df.loc[group.index[0], "attendance_units"] = 1
        late_policy = self.rules.get("late_policy", {})
        if late_policy.get("enabled") and on_duty_row["raw_late_minutes"] > 0:
            if self._policy_apply_lateness_rules(on_duty_row, late_policy):
                self._policy_calculate_punitive_overtime(on_duty_row, off_duty_row)
        early_policy = self.rules.get("early_quit_policy", {})
        if early_policy.get("enabled") and off_duty_row["raw_early_quit_minutes"] > 0:
            self.df.at[off_duty_row.name, "early_quit_count"] = 1
            self.df.at[off_duty_row.name, "early_quit_minutes"] = off_duty_row[
                "raw_early_quit_minutes"
            ]
        overtime_policy = self.rules.get("overtime_policy", {})
        is_afternoon_unit = not group["work_unit_is_am"].iloc[0]
        if overtime_policy.get("enabled") and is_afternoon_unit:
            self._policy_calculate_voluntary_overtime(off_duty_row, overtime_policy)

    def _policy_apply_lateness_rules(
        self, on_duty_row: pd.Series, policy: Dict
    ) -> bool:
        """Applies lateness rules. Returns True if lateness is 'severe'."""
        idx, late_mins = on_duty_row.name, on_duty_row["raw_late_minutes"]
        grace = policy.get("grace_period", {})
        normal = policy.get("normal_late", {})
        severe = policy.get("severe_late", {})
        if grace.get("enabled") and late_mins < grace.get("threshold_minutes", 5):
            self.df.at[idx, "late_minutes"] = late_mins
            return False
        if normal.get("enabled") and normal.get(
            "lower_bound_minutes", 5
        ) <= late_mins < normal.get("upper_bound_minutes", 30):
            self.df.at[idx, "late_minutes"] = late_mins
            self.df.at[idx, "late_count"] = 1
            return False
        if severe.get("enabled") and late_mins >= severe.get("threshold_minutes", 30):
            self.df.at[idx, "late_count"] = 1
            return True
        return False

    def _policy_calculate_overtime_hours(self, summary_df: pd.DataFrame) -> pd.Series:
        """Applies rounding rules to total overtime minutes."""
        total_overtime_minutes = (
            summary_df["voluntary_overtime_minutes"]
            + summary_df["punitive_overtime_minutes"]
        )
        total_overtime_hours = total_overtime_minutes / 60
        policy = self.rules.get("overtime_policy", {})
        rounding_rule = policy.get("rounding_rule", "none")
        if rounding_rule == "floor_half_hour":
            return np.floor(total_overtime_hours * 2) / 2
        if rounding_rule == "floor_with_threshold":
            threshold = policy.get("rounding_threshold", 0.9)
            return np.floor(total_overtime_hours + (1 - threshold))
        return total_overtime_hours.round(2)

    def _policy_calculate_punitive_overtime(
        self, on_duty_row: pd.Series, off_duty_row: pd.Series
    ):
        start_dt = pd.to_datetime(
            on_duty_row["实际打卡时间"], format="%H:%M", errors="coerce"
        )
        end_dt = pd.to_datetime(
            off_duty_row["应打卡时间"], format="%H:%M", errors="coerce"
        )
        if (
            pd.notna(start_dt)
            and pd.notna(end_dt)
            and (delta_seconds := (end_dt - start_dt).total_seconds()) > 0
        ):
            self.df.at[on_duty_row.name, "punitive_overtime_minutes"] = round(
                delta_seconds / 60
            )

    def _policy_calculate_voluntary_overtime(
        self, off_duty_row: pd.Series, policy: Dict
    ):
        start_dt = pd.to_datetime(
            off_duty_row["应打卡时间"], format="%H:%M", errors="coerce"
        )
        end_dt = pd.to_datetime(
            off_duty_row["实际打卡时间"], format="%H:%M", errors="coerce"
        )
        if pd.notna(start_dt) and pd.notna(end_dt):
            delta_minutes = (end_dt - start_dt).total_seconds() / 60
            if (
                effective_overtime := delta_minutes
                - policy.get("start_after_minutes", 30)
            ) > 0:
                self.df.at[off_duty_row.name, "voluntary_overtime_minutes"] = round(
                    effective_overtime
                )

    def _policy_clean_duplicate_punches(self, group: pd.DataFrame) -> pd.DataFrame:
        """Keeps earliest 'On-Duty' and latest 'Off-Duty' punches."""
        group = group.copy()
        group["time_obj"] = pd.to_datetime(
            group["实际打卡时间"], format="%H:%M", errors="coerce"
        ).dt.time
        group.dropna(subset=["time_obj"], inplace=True)
        on_duty = group[group["打卡类型"] == "上班"].sort_values("time_obj").head(1)
        off_duty = (
            group[group["打卡类型"] == "下班"]
            .sort_values("time_obj", ascending=False)
            .head(1)
        )
        return pd.concat([on_duty, off_duty]).drop(columns=["time_obj"])

    # ==========================================================================
    # SECTION D: INTERNAL HELPERS
    # ==========================================================================

    def _load_rules(self, local_path: str, remote_url: str) -> Dict:
        """Loads rules, prioritizing remote, then local, then default."""
        try:
            if remote_url:
                response = requests.get(remote_url, timeout=5)
                response.raise_for_status()
                return toml.loads(response.text)
            rules_path = (
                local_path
                or Path(__file__).resolve().parent / "rules/default_rules.toml"
            )
            with open(rules_path, "r", encoding="utf-8") as f:
                return toml.load(f)
        except Exception as e:
            logger.error("CRITICAL FAILURE loading rules: %s", e, exc_info=True)
            return {}

    def _helper_read_excel(self, file_path_or_obj) -> pd.DataFrame | None:
        """Finds header and reads the Excel sheet into a DataFrame."""
        target_sheet = self.rules.get("data_source", {}).get("sheet_name", "打卡详情")
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("ignore", UserWarning)
            header_row = self._helper_find_header_row(file_path_or_obj, target_sheet)
            if header_row is None:
                logger.error("Could not find header in sheet '%s'.", target_sheet)
                return None
            return pd.read_excel(
                file_path_or_obj,
                sheet_name=target_sheet,
                engine="openpyxl",
                header=header_row,
            )

    def _helper_find_header_row(self, file_path_or_obj, sheet_name) -> int | None:
        """Locates the header row based on keywords."""
        keywords = self.rules.get("data_source", {}).get(
            "header_keywords", ["姓名", "日期"]
        )
        try:
            df = pd.read_excel(
                file_path_or_obj, sheet_name=sheet_name, engine="openpyxl", header=None
            )
            for i, row in df.iterrows():
                if all(
                    row.astype(str).str.contains(key, na=False).any()
                    for key in keywords
                ):
                    return i
        except Exception as e:
            logger.warning("Could not perform header search: %s", e)
        return None

    def _helper_clean_and_validate_data(self):
        """Performs cleaning and validation on the loaded DataFrame."""
        self.df.dropna(how="all", inplace=True)
        required_cols = self.rules.get("data_source", {}).get("required_columns", [])
        if not all(col in self.df.columns for col in required_cols):
            missing = set(required_cols) - set(self.df.columns)
            raise ValueError(f"Missing required columns in source file: {missing}")
        text_cols_to_clean = ["姓名", "打卡状态", "打卡类型", "假勤申请"]
        for col in text_cols_to_clean:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
        self.df["日期"] = pd.to_datetime(
            self.df["日期"].astype(str).str.split(" ").str[0],
            format="%Y/%m/%d",
            errors="coerce",
        ).dt.date
        initial_rows = len(self.df)
        subset_cols = ["姓名", "日期", "打卡类型", "实际打卡时间", "应打卡时间"]
        self.df.drop_duplicates(subset=subset_cols, keep="first", inplace=True)
        if (removed_count := initial_rows - len(self.df)) > 0:
            logger.info(
                "Data Cleaning: Removed %d duplicate punch records.", removed_count
            )

    def _get_report(self, columns_key: str) -> pd.DataFrame | None:
        """
        Helper to generate a report view from the main summary DataFrame.
        This version handles the new dictionary-based column configuration
        and translates display names before returning the report.
        """
        if not self.is_analyzed or self.summary_df is None:
            return None
        report_cols_config = self.rules.get("reporting", {}).get(columns_key, [])
        if not report_cols_config:
            return self.summary_df
        column_keys = [
            col["key"]
            for col in report_cols_config
            if col["key"] in self.summary_df.columns
        ]
        report_df = self.summary_df[column_keys].copy()
        translated_names_map = {
            col["key"]: gettext(col["display_name"])
            for col in report_cols_config
            if col["key"] in column_keys
        }
        report_df.rename(columns=translated_names_map, inplace=True)
        return report_df
