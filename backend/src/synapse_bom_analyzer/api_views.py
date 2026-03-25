# Copyright (c) 2026 PotterWhite
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
DRF API views for the BOM Analyzer.

Endpoints:
  POST /api/bom/analyze/    — upload BOM Excel files, return analysis JSON
  GET  /api/bom/download/   — download aggregated Excel (session-based)
"""

from __future__ import annotations

import datetime
import io

import pandas as pd
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from .engine.parser import func_2_0_parse_excel_files
from .engine.aggregator import func_2_1_aggregate_materials
from .engine.writer import func_2_2_generate_excel_output, func_3_0_format_dataframe

_DF_SESSION_KEY = "bom_analyzer_aggregated_df_json"
_FILENAMES_SESSION_KEY = "bom_analyzer_filenames_list"


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def api_analyze(request: Request) -> Response:
    """
    POST /api/bom/analyze/
    Body: multipart/form-data  { bom_files: <binary>, bom_files: <binary>, … }

    Returns JSON with headers, rows, and per-row is_suspicious flag.
    """
    uploaded_files = request.FILES.getlist("bom_files")
    if not uploaded_files:
        return Response(
            {"detail": "No files uploaded. Provide one or more 'bom_files'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    filenames = [f.name for f in uploaded_files]

    try:
        parsed = func_2_0_parse_excel_files(uploaded_files)
        if not parsed:
            return Response(
                {"detail": "Could not find valid BOM data in the uploaded files."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        aggregated_raw = func_2_1_aggregate_materials(parsed)
        if aggregated_raw.empty:
            return Response(
                {"detail": "No valid material entries found after filtering."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Persist raw DF in session for download
        request.session[_DF_SESSION_KEY] = aggregated_raw.to_json(orient="split")
        request.session[_FILENAMES_SESSION_KEY] = filenames

        df_formatted = func_3_0_format_dataframe(aggregated_raw)

        # Build header list excluding internal flag column
        report_headers = [h for h in df_formatted.columns if h != "is_suspicious"]

        rows = []
        for _, row in df_formatted.iterrows():
            rows.append(
                {
                    "is_suspicious": bool(row.get("is_suspicious", False)),
                    "values": [row[h] for h in report_headers],
                }
            )

        return Response(
            {
                "filenames": filenames,
                "analysis_id": request.session.session_key,
                "report": {
                    "headers": report_headers,
                    "rows": rows,
                },
            }
        )

    except Exception as exc:
        request.session.pop(_DF_SESSION_KEY, None)
        request.session.pop(_FILENAMES_SESSION_KEY, None)
        return Response(
            {"detail": f"Analysis error: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_download(request: Request) -> HttpResponse:
    """GET /api/bom/download/"""
    aggregated_json = request.session.get(_DF_SESSION_KEY)
    if not aggregated_json:
        return Response(
            {"detail": "No analysis result in session. Run /api/bom/analyze/ first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

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
