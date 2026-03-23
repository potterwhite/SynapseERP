"""
DRF API views for the Attendance Analyzer.

Endpoints:
  POST /api/attendance/analyze/   — upload Excel file, return analysis JSON
  GET  /api/attendance/download/  — download Excel report (session-based)

The analysis engine is unchanged; only the presentation layer is new.
"""

from __future__ import annotations

import io
import os

import pandas as pd
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse

from .engine.analyzer import AttendanceAnalyzer

_SESSION_KEY = "analyzer_summary_df_json"
_FILENAME_KEY = "original_filename"


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def api_analyze(request: Request) -> Response:
    """
    POST /api/attendance/analyze/
    Body: multipart/form-data  { excel_file: <binary> }

    Returns JSON with detailed_report and public_report table data,
    plus an analysis_id (session key) for subsequent download.
    """
    uploaded_file = request.FILES.get("excel_file")
    if not uploaded_file:
        return Response(
            {"detail": "No file uploaded. Please provide 'excel_file'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    remote_rules_url = getattr(settings, "ATTENDANCE_ANALYZER_RULE_URL", None)
    analyzer = AttendanceAnalyzer(remote_rules_url=remote_rules_url)

    if not analyzer.load_data_from_file(uploaded_file):
        return Response(
            {"detail": "Failed to parse the uploaded file. Check format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        analyzer.analyze()
    except Exception as exc:
        return Response(
            {"detail": f"Analysis error: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Store raw summary in session for download
    if analyzer.summary_df is not None:
        request.session[_SESSION_KEY] = analyzer.summary_df.to_json(orient="split")
        request.session[_FILENAME_KEY] = uploaded_file.name

    def df_to_table(df: pd.DataFrame | None) -> dict | None:
        if df is None:
            return None
        return {
            "headers": list(df.columns),
            "rows": df.values.tolist(),
        }

    return Response(
        {
            "filename": uploaded_file.name,
            "analysis_id": request.session.session_key,
            "detailed_report": df_to_table(analyzer.get_detailed_summary()),
            "public_report": df_to_table(analyzer.get_public_summary()),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_download(request: Request) -> HttpResponse:
    """
    GET /api/attendance/download/?report_type=detailed&lang=zh-hans

    Streams the Excel file built from the session-cached summary DataFrame.
    """
    from django.utils.translation import activate, gettext
    from openpyxl.styles import Alignment
    from urllib.parse import quote

    summary_json = request.session.get(_SESSION_KEY)
    if not summary_json:
        return Response(
            {"detail": "No analysis result in session. Run /api/attendance/analyze/ first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    original_filename = request.session.get(_FILENAME_KEY, "report.xlsx")
    summary_df = pd.read_json(io.StringIO(summary_json), orient="split")

    remote_rules_url = getattr(settings, "ATTENDANCE_ANALYZER_RULE_URL", None)
    analyzer = AttendanceAnalyzer(remote_rules_url=remote_rules_url)
    analyzer.summary_df = summary_df
    analyzer.is_analyzed = True

    report_type = request.query_params.get("report_type", "detailed")
    lang_code = request.query_params.get("lang", settings.LANGUAGE_CODE)
    activate(lang_code)

    report_df = (
        analyzer.get_public_summary()
        if report_type == "public"
        else analyzer.get_detailed_summary()
    )
    if report_df is None:
        return Response(
            {"detail": "Error generating report."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    sheet_name = gettext("Report")
    output_buffer = io.BytesIO()
    with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
        report_df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        wrap_alignment = Alignment(wrap_text=True, vertical="top")
        for col_idx, col_name in enumerate(report_df.columns, 1):
            if "详情" in col_name or "Details" in col_name:
                col_letter = chr(ord("A") + col_idx - 1)
                worksheet.column_dimensions[col_letter].width = 50
                for cell in worksheet[col_letter]:
                    cell.alignment = wrap_alignment
    output_buffer.seek(0)

    base_name, _ext = os.path.splitext(original_filename)
    report_type_suffix = gettext("Public") if report_type == "public" else gettext("Detailed")
    filename_utf8 = f"{base_name}_{report_type_suffix}.xlsx"
    filename_ascii = f"{base_name.encode('ascii', 'ignore').decode()}_{report_type}.xlsx"
    encoded_filename = quote(filename_utf8)

    response = HttpResponse(
        output_buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f"attachment; filename=\"{filename_ascii}\"; filename*=UTF-8''{encoded_filename}"
    )
    return response
