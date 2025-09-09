# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (View layer for the BOM Analyzer)

import io
import datetime
import pandas as pd
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from .engine.writer import func_2_2_generate_excel_output, func_3_0_format_dataframe

BOM_DATAFRAME_SESSION_KEY = "bom_analyzer_aggregated_df_json"
BOM_FILENAMES_SESSION_KEY = "bom_analyzer_filenames_list"


@require_http_methods(["GET", "POST"])
def analysis_view(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        if BOM_DATAFRAME_SESSION_KEY in request.session:
            del request.session[BOM_DATAFRAME_SESSION_KEY]
        if BOM_FILENAMES_SESSION_KEY in request.session:
            del request.session[BOM_FILENAMES_SESSION_KEY]
        return render(request, "synapse_bom_analyzer/upload.html")

    uploaded_files = request.FILES.getlist("bom_files")
    if not uploaded_files:
        context = {
            "error_message": _(
                "No files were selected. Please choose one or more files to upload."
            )
        }
        return render(request, "synapse_bom_analyzer/upload.html", context, status=400)

    try:
        filenames = [file.name for file in uploaded_files]
        from .engine.parser import func_2_0_parse_excel_files
        from .engine.aggregator import func_2_1_aggregate_materials

        parsed_dataframes = func_2_0_parse_excel_files(uploaded_files)
        if not parsed_dataframes:
            raise ValueError(
                _(
                    "Could not find any valid BOM data in the uploaded files. Please check the file format."
                )
            )

        aggregated_df_raw = func_2_1_aggregate_materials(parsed_dataframes)
        if aggregated_df_raw.empty:
            raise ValueError(
                _(
                    "No valid material entries were found after filtering. Please check file content."
                )
            )

        request.session[BOM_DATAFRAME_SESSION_KEY] = aggregated_df_raw.to_json(
            orient="split"
        )
        request.session[BOM_FILENAMES_SESSION_KEY] = filenames

        df_formatted = func_3_0_format_dataframe(aggregated_df_raw)

        # --- NEW FINAL FIX for Django Template ---
        # Convert multi-line columns to HTML <br> tags
        breakdown_col = str(_("Quantity Breakdown"))
        if breakdown_col in df_formatted.columns:
            df_formatted[breakdown_col] = df_formatted[breakdown_col].str.replace(
                "\n", "<br>", regex=False
            )

        # Prepare headers, excluding the 'is_suspicious' column for display
        report_headers = [h for h in df_formatted.columns if h != "is_suspicious"]

        # Convert the DataFrame into a list of lists, which is easy for templates
        report_data = []
        for index, row in df_formatted.iterrows():
            row_data = {
                "is_suspicious": row.get("is_suspicious", False),
                "values": [
                    row[h] for h in report_headers
                ],  # A list of cell values for this row
            }
            report_data.append(row_data)
        # --- END OF FIX ---

        context = {
            "filenames": filenames,
            "report_headers": report_headers,
            "report_data": report_data,
        }
        return render(request, "synapse_bom_analyzer/result.html", context)

    except Exception as e:
        if BOM_DATAFRAME_SESSION_KEY in request.session:
            del request.session[BOM_DATAFRAME_SESSION_KEY]
        if BOM_FILENAMES_SESSION_KEY in request.session:
            del request.session[BOM_FILENAMES_SESSION_KEY]
        context = {
            "error_message": _("An error occurred during analysis: %(error)s")
            % {"error": str(e)}
        }
        return render(request, "synapse_bom_analyzer/upload.html", status=500)


# download_report_view remains the same.
def download_report_view(request: HttpRequest) -> HttpResponse:
    aggregated_json = request.session.get(BOM_DATAFRAME_SESSION_KEY)
    if not aggregated_json:
        return HttpResponseRedirect(reverse("synapse_bom_analyzer:analyze"))

    aggregated_df_raw = pd.read_json(io.StringIO(aggregated_json), orient="split")
    output_buffer = func_2_2_generate_excel_output(aggregated_df_raw)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(
        output_buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="aggregated_bom_{timestamp}.xlsx"'
    )
    return response
