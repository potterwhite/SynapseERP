# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (Engine aggregation module for BOM Analyzer)

import pandas as pd
from typing import List

from .parser import KEY_COLS, QUANTITY_COL_NAME, SOURCE_FILE_COL


def func_3_0_custom_aggregator(group: pd.DataFrame) -> pd.Series:
    """
    A custom aggregation function with intelligent breakdown logic.
    """
    total_quantity = group[QUANTITY_COL_NAME].sum()

    if total_quantity > 0:
        # If total is > 0, show breakdown with quantities (but only for non-zero entries).
        details_list = [
            f"{row[SOURCE_FILE_COL]}: {row[QUANTITY_COL_NAME]}"
            for index, row in group.iterrows()
            if row[QUANTITY_COL_NAME] > 0
        ]
        details_string = "\n".join(sorted(details_list))
    else:
        # If total is 0, just list the unique source files.
        source_files = sorted(group[SOURCE_FILE_COL].unique())
        details_string = "\n".join(source_files)

    result = {
        "total_quantity": total_quantity,
        "quantity_details": details_string,
        **{col: group[col].iloc[0] for col in KEY_COLS},
    }
    return pd.Series(result)


def func_2_1_aggregate_materials(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """
    The main aggregation function. It filters garbage, aggregates data,
    and flags suspicious entries.
    """
    if not dataframes:
        return pd.DataFrame()

    master_df = pd.concat(dataframes, ignore_index=True)
    master_df[QUANTITY_COL_NAME] = (
        pd.to_numeric(master_df[QUANTITY_COL_NAME], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    # Step 1: Filter out garbage data (must happen before filling NaN).
    header_blacklist = ["值", "封装", "备注"]
    master_df = master_df[~master_df["值"].fillna("").isin(header_blacklist)]
    master_df = master_df.dropna(subset=KEY_COLS, how="all")

    # Step 2: Now, safely fill any remaining NaN values for string operations.
    for col in KEY_COLS:
        master_df[col] = master_df[col].fillna("").astype(str)
    if SOURCE_FILE_COL in master_df.columns:
        master_df[SOURCE_FILE_COL] = master_df[SOURCE_FILE_COL].fillna("").astype(str)

    # Step 3: Prepare for grouping.
    temp_grouping_cols = []
    for col in KEY_COLS:
        temp_col_name = f"{col}_lower"
        master_df[temp_col_name] = master_df[col].str.lower()
        temp_grouping_cols.append(temp_col_name)

    if master_df.empty:
        return pd.DataFrame()

    # Step 4: Aggregate the data.
    aggregated_df = (
        master_df.groupby(temp_grouping_cols)
        .apply(func_3_0_custom_aggregator, include_groups=False)
        .reset_index()
    )

    # --- FINAL FIX: Ensure all three anomaly detection rules are present ---
    # Step 5: Flag suspicious data for highlighting.
    cond1 = aggregated_df["total_quantity"] == 0
    cond2 = aggregated_df["值"] == ""
    cond3 = aggregated_df["封装"] == ""

    # Combine all three conditions with an OR operator.
    aggregated_df["is_suspicious"] = cond1 | cond2 | cond3
    # --- END OF FINAL FIX ---

    final_df = aggregated_df.drop(columns=temp_grouping_cols)
    return final_df
