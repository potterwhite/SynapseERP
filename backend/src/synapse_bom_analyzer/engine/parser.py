# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (Engine parsing module for BOM Analyzer)

import pandas as pd
from typing import List, Optional

KEY_COLS = ["值", "封装", "备注"]
QUANTITY_COL_NAME = "需求数"
# --- MODIFIED: Use a non-translatable, internal key name ---
SOURCE_FILE_COL = "source_file"
# --- END MODIFICATION ---
REQUIRED_COLS = ["序号", QUANTITY_COL_NAME] + KEY_COLS


def func_3_0_find_header_row(dataframe: pd.DataFrame) -> Optional[int]:
    for index, row in dataframe.iterrows():
        row_values = list(row.values)
        if "序号" in row_values and QUANTITY_COL_NAME in row_values:
            return index
    return None


def func_2_0_parse_excel_files(uploaded_files: list) -> List[pd.DataFrame]:
    all_materials_dataframes = []
    for file in uploaded_files:
        try:
            filename = file.name
            excel_file_handler = pd.ExcelFile(file)
            for sheet_name in excel_file_handler.sheet_names:
                df_raw = pd.read_excel(
                    excel_file_handler, sheet_name=sheet_name, header=None
                )
                header_row_index = func_3_0_find_header_row(df_raw)
                if header_row_index is None:
                    continue
                df_structured = pd.read_excel(
                    excel_file_handler, sheet_name=sheet_name, header=header_row_index
                )
                df_structured = df_structured.dropna(subset=["序号"])
                for col in REQUIRED_COLS:
                    if col not in df_structured.columns:
                        df_structured[col] = ""

                df_structured[SOURCE_FILE_COL] = filename

                all_needed_cols = REQUIRED_COLS + [SOURCE_FILE_COL]
                df_clean = df_structured[
                    [col for col in all_needed_cols if col in df_structured.columns]
                ]

                all_materials_dataframes.append(df_clean)
        except Exception as e:
            print(
                f"Error: An exception occurred while processing file {getattr(file, 'name', 'N/A')}: {e}"
            )
            continue
    return all_materials_dataframes
