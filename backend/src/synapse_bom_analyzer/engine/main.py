# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (Engine main entry point for BOM Analyzer)

import io
from typing import List, Optional

# Import the main functions from our modularized engine components.
from .parser import func_2_0_parse_excel_files
from .aggregator import func_2_1_aggregate_materials
from .writer import func_2_2_generate_excel_output


def func_1_0_process_boms(uploaded_files: List) -> Optional[io.BytesIO]:
    """
    The main entry point for the BOM processing engine.

    This function orchestrates the entire workflow by calling the specialized
    functions from the parser, aggregator, and writer modules in sequence.

    Workflow:
    1. Parse the raw uploaded files into a list of clean DataFrames.
    2. Aggregate the data from all DataFrames into a single, consolidated list.
    3. Generate a final, formatted Excel file in an in-memory buffer.

    Args:
        uploaded_files (List): A list of uploaded file objects from the Django view.

    Returns:
        Optional[io.BytesIO]: An in-memory buffer containing the generated Excel file
                              if processing is successful and data is found.
                              Returns None if no valid BOM data is found in any of the files.
    """
    # Step 1: Parse all uploaded files to extract BOM data.
    # The result is a list of DataFrames, one for each valid BOM sheet found.
    parsed_dataframes = func_2_0_parse_excel_files(uploaded_files)

    # If the parser returns an empty list, it means no valid BOM data was found.
    # We should stop here and return None to signal this to the caller (the view).
    if not parsed_dataframes:
        return None

    # Step 2: Aggregate the parsed data.
    # This combines all data into a single DataFrame and sums the quantities.
    aggregated_dataframe = func_2_1_aggregate_materials(parsed_dataframes)

    # Step 3: Generate the final Excel output file in a memory buffer.
    # This takes the aggregated data and makes it into a polished report.
    output_excel_buffer = func_2_2_generate_excel_output(aggregated_dataframe)

    # Return the final result to the view.
    return output_excel_buffer
