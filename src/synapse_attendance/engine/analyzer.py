# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.1-20250905

import toml
import requests
import os
import logging
from pathlib import Path
import pandas as pd
import warnings
import numpy as np
from typing import Dict, Any
from synapse import __version__

# Get a logger instance specific to this module.
# This is the standard best practice.
logger = logging.getLogger(__name__)

class AttendanceAnalyzer:
    """
    A rule-driven engine for attendance data analysis.
    
    This engine is the core of the attendance module. It processes raw punch data
    from an Excel file and generates summary reports based on a flexible set of
    rules. The rules can be loaded from a local TOML file or fetched from a
    remote URL, allowing for dynamic configuration.
    """
    VERSION = __version__

    def __init__(self, rules_path: str = None, remote_rules_url: str = None):
        """
        Initialize the analyzer.
        
        Prioritizes loading rules from 'remote_rules_url'. If it fails or is 
        not provided, it falls back to a local 'rules_path'. If neither is 
        provided, it loads the default rules packaged with the library.
        """
        self.df: pd.DataFrame | None = None
        self.summary_df_detailed: pd.DataFrame | None = None
        self.summary_df_public: pd.DataFrame | None = None
        self.is_loaded: bool = False
        self.is_analyzed: bool = False
        self.target_sheet_name: str = "打卡详情"
        self.rules: Dict[str, Any] = {}

        try:
            # Prioritize loading from the remote URL.
            if remote_rules_url:
                logger.info("Attempting to load remote rules from: %s", remote_rules_url)
                response = requests.get(remote_rules_url, timeout=5)
                response.raise_for_status()
                self.rules = toml.loads(response.text)
                logger.info("Remote rules loaded successfully.")
                return

            # Fallback to a local file if provided.
            if rules_path:
                logger.info("Loading local rules from: %s", rules_path)
                self.rules = toml.load(rules_path)
                logger.info("Local rules loaded successfully.")
                return
            
            # Default fallback to the packaged rules.
            base_path = Path(__file__).resolve().parent
            default_rules_path = base_path / "rules/default_rules.toml"
            logger.info("Loading default packaged rules from: %s", default_rules_path)
            self.rules = toml.load(default_rules_path)
            logger.info("Default packaged rules loaded successfully.")

        except Exception as e:
            logger.error("Critical failure in loading rules configuration: %s", e, exc_info=True)
            self.rules = {}

    # --- Data Loading & Pre-processing ---
    
    def _find_header_row(self, file_path_or_obj, sheet_name) -> int | None:
        """Locate the header row in the Excel sheet."""
        header_keywords = ["姓名", "日期", "打卡类型"]
        try:
            df_no_header = pd.read_excel(
                file_path_or_obj, sheet_name=sheet_name, engine="openpyxl", header=None
            )
            for i, row in df_no_header.iterrows():
                row_str_series = row.astype(str)
                if all(
                    row_str_series.str.contains(key, na=False).any()
                    for key in header_keywords
                ):
                    return i
        except Exception as e:
            logger.warning("Could not perform header search: %s", e)
        return None

    def load_data_from_file(self, file_path_or_obj) -> bool:
        """Load and clean data from the provided Excel file object or path."""
        try:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("ignore", UserWarning)
                header_row = self._find_header_row(file_path_or_obj, self.target_sheet_name)
                if header_row is None:
                    logger.error("Could not find header in sheet '%s'.", self.target_sheet_name)
                    return False

                logger.debug("Header row found at index: %d", header_row)
                self.df = pd.read_excel(
                    file_path_or_obj,
                    sheet_name=self.target_sheet_name,
                    engine="openpyxl",
                    header=header_row,
                )

            self.df.dropna(how="all", inplace=True)
            required_columns = ["姓名", "日期", "应打卡时间", "实际打卡时间", "打卡状态", "打卡类型", "假勤申请"]
            if not all(col in self.df.columns for col in required_columns):
                logger.error("Missing required columns. Required: %s", required_columns)
                return False

            # Convert the '日期' column to datetime objects first.
            date_series = pd.to_datetime(self.df["日期"].astype(str).str.split(" ").str[0], format="%Y/%m/%d", errors='coerce')
            # Then, safely extract the date part from each element.
            self.df["日期"] = date_series.apply(lambda x: x.date() if pd.notnull(x) else None)
            
            # Remove duplicate punch records.
            initial_rows = len(self.df)
            subset_cols = ["姓名", "日期", "打卡类型", "实际打卡时间", "应打卡时间"]
            self.df.drop_duplicates(subset=subset_cols, keep="first", inplace=True)
            final_rows = len(self.df)
            if initial_rows > final_rows:
                logger.info("Data Cleaning: Removed %d duplicate records.", initial_rows - final_rows)

            self.is_loaded = True
            return True
        except Exception as e:
            logger.error("Failed to load data from file: %s", e, exc_info=True)
            return False
    
    # --- Analysis Pipeline ---

    def analyze(self):
        """Run the full three-stage analysis pipeline."""
        if not self.is_loaded:
            raise ValueError("Data is not loaded. Call load_data_from_file() first.")
        if not self.rules:
            raise ValueError("Rules are not loaded. Cannot perform analysis.")

        logger.info("Starting analysis v%s...", self.VERSION)
        self._stage_1_calculate_raw_deltas()
        self._stage_2_analyze_work_units()
        self._stage_3_generate_summary_reports()
        self.is_analyzed = True
        logger.info("Analysis complete.")

    def _stage_1_calculate_raw_deltas(self):
        """Stage 1: Calculate raw time differences for lateness and early quits."""
        logger.debug("Pipeline - Stage 1: Calculating raw time deltas...")
        should_punch_time = pd.to_datetime(self.df["应打卡时间"], format="%H:%M", errors="coerce").dt.time
        actual_punch_time = pd.to_datetime(self.df["实际打卡时间"], format="%H:%M", errors="coerce").dt.time
        
        self.df["raw_late_minutes"] = 0
        self.df["raw_early_quit_minutes"] = 0
        
        valid_times = pd.notna(should_punch_time) & pd.notna(actual_punch_time)
        dummy_date = pd.to_datetime("1970-01-01").date()
        
        for i in self.df[valid_times].index:
            actual_dt = pd.to_datetime(f"{dummy_date} {actual_punch_time[i]}")
            should_dt = pd.to_datetime(f"{dummy_date} {should_punch_time[i]}")
            delta_seconds = (actual_dt - should_dt).total_seconds()
            
            if self.df.at[i, "打卡类型"] == "上班" and delta_seconds > 0:
                self.df.at[i, "raw_late_minutes"] = round(delta_seconds / 60)
            elif self.df.at[i, "打卡类型"] == "下班" and delta_seconds < 0:
                self.df.at[i, "raw_early_quit_minutes"] = round(-delta_seconds / 60)

    def _stage_2_analyze_work_units(self):
        """Stage 2: Apply all business logic and policies to each work unit."""
        logger.debug("Pipeline - Stage 2: Applying policies to work units...")
        metric_cols = ["attendance_units", "absent_units", "missing_punch_count", "late_count", "late_minutes", "early_quit_count", "early_quit_minutes", "voluntary_overtime_minutes", "punitive_overtime_minutes"]
        for col in metric_cols:
            self.df[col] = 0.0
        
        punches_per_unit = self.rules.get("attendance_policy", {}).get("punches_per_unit", 2)
        self.df["work_unit"] = (pd.to_datetime(self.df["应打卡时间"], format="%H:%M", errors="coerce").dt.hour < 13)
        
        grouped = self.df.groupby(["姓名", "日期", "work_unit"])
        
        for (name, date, work_unit_bool), group in grouped:
            # Business trip logic
            is_business_trip = group["假勤申请"].str.contains("出差", na=False).any()
            missing_punches = group["打卡状态"].str.contains("缺卡").sum()
            
            if missing_punches > 0 and is_business_trip:
                logger.debug("Identified Business Trip for %s on %s. Marking as attended.", name, date)
                self.df.loc[group.index[0], "attendance_units"] = 1
                continue

            # Attendance logic
            valid_punches_group = group[~group["打卡状态"].str.contains("失效", na=False)]
            if len(valid_punches_group) == punches_per_unit and missing_punches == 0:
                self._process_attended_unit(valid_punches_group)
            elif len(group) == punches_per_unit and missing_punches == punches_per_unit:
                logger.debug("Identified Absent unit for %s on %s.", name, date)
                self.df.loc[group.index[0], "absent_units"] = 1
            else:
                logger.debug("Identified Missing Punch for %s on %s.", name, date)
                self.df.loc[group.index, "missing_punch_count"] = group["打卡状态"].str.contains("缺卡").astype(int)
        
        self.df.drop(columns=["work_unit"], inplace=True)

    def _stage_3_generate_summary_reports(self):
        """Stage 3: Aggregate all metrics and create final summary reports."""
        logger.debug("Pipeline - Stage 3: Aggregating results...")
        agg_map = {
            "attendance_units": ("attendance_units", "sum"), "absent_units": ("absent_units", "sum"),
            "missing_punch_count": ("missing_punch_count", "sum"), "late_count": ("late_count", "sum"),
            "total_late_minutes": ("late_minutes", "sum"), "early_quit_count": ("early_quit_count", "sum"),
            "total_early_quit_minutes": ("early_quit_minutes", "sum"),
            "voluntary_overtime_minutes": ("voluntary_overtime_minutes", "sum"),
            "punitive_overtime_minutes": ("punitive_overtime_minutes", "sum"),
        }
        summary = self.df.groupby("姓名").agg(**agg_map).reset_index()
        
        summary["attendance_days"] = summary["attendance_units"] / 2
        summary["absent_days"] = summary["absent_units"] / 2
        
        # Process overtime hours based on rounding rules.
        total_overtime_minutes = summary["voluntary_overtime_minutes"] + summary["punitive_overtime_minutes"]
        total_overtime_hours = total_overtime_minutes / 60
        overtime_policy = self.rules.get("overtime_policy", {})
        rounding_rule = overtime_policy.get("rounding_rule", "none")
        
        if rounding_rule == "floor_half_hour":
            summary["total_overtime_hours"] = np.floor(total_overtime_hours * 2) / 2
        elif rounding_rule == "floor_with_threshold":
            threshold = overtime_policy.get("rounding_threshold", 0.9)
            summary["total_overtime_hours"] = np.floor(total_overtime_hours + (1 - threshold))
        else: # "none"
            summary["total_overtime_hours"] = total_overtime_hours.round(2)

        # Generate reports based on column definitions in rules.
        reporting_policy = self.rules.get("reporting", {})
        detailed_cols = reporting_policy.get("detailed_columns", [])
        public_cols = reporting_policy.get("public_columns", [])
        self.summary_df_detailed = summary[[c for c in detailed_cols if c in summary.columns]]
        self.summary_df_public = summary[[c for c in public_cols if c in summary.columns]]

        # Clean up the raw dataframe before exposing it.
        if "假勤申请" in self.df.columns:
            self.df.drop(columns=["假勤申请"], inplace=True)

    # --- Helper methods for policy application ---

    def _process_attended_unit(self, group: pd.DataFrame):
        """Process a single, valid 'Attended Unit'."""
        self.df.loc[group.index[0], "attendance_units"] = 1
        on_duty_row = group[group["打卡类型"] == "上班"].iloc[0]
        off_duty_row = group[group["打卡类型"] == "下班"].iloc[0]

        if self.rules.get("late_policy", {}).get("enabled") and on_duty_row["raw_late_minutes"] > 0:
            is_severe = self._process_lateness(on_duty_row, self.rules["late_policy"])
            if is_severe: self._calculate_punitive_overtime(on_duty_row, off_duty_row)

        if self.rules.get("early_quit_policy", {}).get("enabled") and off_duty_row["raw_early_quit_minutes"] > 0:
            self.df.at[off_duty_row.name, "early_quit_count"] = 1
            self.df.at[off_duty_row.name, "early_quit_minutes"] = off_duty_row["raw_early_quit_minutes"]

        # Convert the single time string to a Timestamp object
        on_duty_time_obj = pd.to_datetime(on_duty_row["应打卡时间"], format="%H:%M", errors="coerce")
        # Directly access the .hour attribute from the Timestamp object
        is_afternoon = not on_duty_time_obj.hour < 13
        if self.rules.get("overtime_policy", {}).get("enabled") and is_afternoon:
            self._calculate_voluntary_overtime(off_duty_row, self.rules["overtime_policy"])

    def _process_lateness(self, on_duty_row: pd.Series, policy: Dict) -> bool:
        """Apply lateness rules. Return True if severe."""
        idx, late_mins = on_duty_row.name, on_duty_row["raw_late_minutes"]
        grace = policy.get("grace_period", {})
        normal = policy.get("normal_late", {})
        severe = policy.get("severe_late", {})
        
        if grace.get("enabled") and late_mins < grace.get("threshold_minutes", 2):
            self.df.at[idx, "late_minutes"] = late_mins
        elif normal.get("enabled") and normal.get("lower_bound_minutes", 2) <= late_mins < normal.get("upper_bound_minutes", 60):
            self.df.at[idx, "late_minutes"] = late_mins
            self.df.at[idx, "late_count"] = 1
        elif severe.get("enabled") and late_mins >= severe.get("threshold_minutes", 60):
            self.df.at[idx, "late_count"] = 1
            return True
        return False

    def _calculate_punitive_overtime(self, on_duty_row: pd.Series, off_duty_row: pd.Series):
        """Calculate overtime caused by a severe lateness penalty."""
        dummy_date = pd.to_datetime("1970-01-01").date()
        actual_on_duty_time = pd.to_datetime(on_duty_row["实际打卡时间"], format="%H:%M").time()
        should_off_duty_time = pd.to_datetime(off_duty_row["应打卡时间"], format="%H:%M").time()
        start_dt = pd.to_datetime(f"{dummy_date} {actual_on_duty_time}")
        end_dt = pd.to_datetime(f"{dummy_date} {should_off_duty_time}")
        delta_seconds = (end_dt - start_dt).total_seconds()
        if delta_seconds > 0:
            self.df.at[on_duty_row.name, "punitive_overtime_minutes"] = round(delta_seconds / 60)

    def _calculate_voluntary_overtime(self, off_duty_row: pd.Series, policy: Dict):
        """Calculate voluntary overtime based on policy."""
        dummy_date = pd.to_datetime("1970-01-01").date()
        actual_off_duty_time = pd.to_datetime(off_duty_row["实际打卡时间"], format="%H:%M").time()
        should_off_duty_time = pd.to_datetime(off_duty_row["应打卡时间"], format="%H:%M").time()
        start_dt = pd.to_datetime(f"{dummy_date} {should_off_duty_time}")
        end_dt = pd.to_datetime(f"{dummy_date} {actual_off_duty_time}")
        delta_minutes = (end_dt - start_dt).total_seconds() / 60
        effective_overtime = delta_minutes - policy.get("start_after_minutes", 30)
        if effective_overtime > 0:
            self.df.at[off_duty_row.name, "voluntary_overtime_minutes"] = round(effective_overtime)
    
    # --- Public Methods for Retrieving Results ---

    def get_detailed_summary(self) -> pd.DataFrame | None:
        """Return the detailed summary DataFrame if analysis is complete."""
        return self.summary_df_detailed if self.is_analyzed else None
    
    def get_public_summary(self) -> pd.DataFrame | None:
        """Return the public summary DataFrame if analysis is complete."""
        return self.summary_df_public if self.is_analyzed else None

    def get_raw_processed_dataframe(self) -> pd.DataFrame | None:
        """Return the raw, processed DataFrame after data loading."""
        return self.df if self.is_loaded else None
