# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (View layer for the Attendance Analyzer)

import os
import re
import io
import pandas as pd
from django.shortcuts import render
from django.views import View
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.utils.translation import activate, gettext_lazy as _, gettext
from openpyxl.styles import Alignment
from urllib.parse import quote

from .engine.analyzer import AttendanceAnalyzer

# A constant for the session key to avoid using magic strings.
ANALYZER_SESSION_KEY = "analyzer_summary_df_json"


class AnalysisView(View):
    """
    Handles the attendance analysis process.
    - GET: Displays the file upload form.
    - POST: Processes the uploaded Excel file, stores the results in the user's session,
            and displays the analysis reports in the browser.
    """

    template_name = "synapse_attendance/upload.html"
    result_template_name = "synapse_attendance/result.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Handles GET requests by displaying the file upload form."""
        return render(request, self.template_name)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Handles POST requests for file upload and analysis."""
        uploaded_file = request.FILES.get("excel_file")
        if not uploaded_file:
            context = {
                "error_message": _("No file was uploaded. Please select a file.")
            }
            return render(request, self.template_name, context, status=400)

        remote_rules_url = getattr(settings, "ATTENDANCE_ANALYZER_RULE_URL", None)
        analyzer = AttendanceAnalyzer(remote_rules_url=remote_rules_url)

        if not analyzer.load_data_from_file(uploaded_file):
            context = {
                "error_message": _(
                    "Failed to load data. The file might be corrupted or in the wrong format."
                )
            }
            return render(request, self.template_name, context, status=400)

        try:
            analyzer.analyze()

            # Store the raw summary DataFrame in the session for later use (e.g., downloads).
            if analyzer.summary_df is not None:
                summary_json = analyzer.summary_df.to_json(orient="split")
                request.session[ANALYZER_SESSION_KEY] = summary_json
                request.session["original_filename"] = uploaded_file.name

            # Get the translated, formatted reports for HTML display.
            detailed_summary = analyzer.get_detailed_summary()
            public_summary = analyzer.get_public_summary()

            # For HTML display, newlines in detail columns must be converted to <br> tags.
            # We operate on a copy to keep the original data in the session pristine.
            html_detailed = pd.DataFrame()
            if detailed_summary is not None:
                html_detailed = detailed_summary.copy()
                for col in html_detailed.select_dtypes(include=["object"]).columns:
                    html_detailed[col] = html_detailed[col].str.replace(
                        "\n", "<br>", regex=False
                    )

            context = {
                "filename": uploaded_file.name,
                "detailed_html": html_detailed.to_html(
                    classes="table", index=False, border=0, escape=False
                ),
                "public_html": public_summary.to_html(
                    classes="table", index=False, border=0, escape=False
                ),
            }
            return render(request, self.result_template_name, context)

        except Exception as e:
            # If any error occurs, clear potentially stale data from the session.
            if ANALYZER_SESSION_KEY in request.session:
                del request.session[ANALYZER_SESSION_KEY]
            if "original_filename" in request.session:
                del request.session["original_filename"]

            logging.error("Analysis failed in view", exc_info=True)
            context = {
                "error_message": _("An error occurred during analysis: %(error)s")
                % {"error": e}
            }
            return render(request, self.template_name, context, status=500)


def download_report_view(request: HttpRequest) -> HttpResponse:
    """
    Handles GET requests to download a previously generated report as an Excel file.
    It retrieves the analysis data from the session, regenerates the report in the
    requested language, and serves it as a file download.
    """
    summary_json = request.session.get(ANALYZER_SESSION_KEY)
    original_filename = request.session.get("original_filename", "report.xlsx")
    if not summary_json:
        return HttpResponseRedirect(reverse("synapse_attendance:analyze"))

    # Recreate the DataFrame from the JSON stored in the session.
    summary_df = pd.read_json(io.StringIO(summary_json), orient="split")
    remote_rules_url = getattr(settings, "ATTENDANCE_ANALYZER_RULE_URL", None)

    # Instantiate a new analyzer and load the summary data into it.
    analyzer = AttendanceAnalyzer(remote_rules_url=remote_rules_url)
    analyzer.summary_df = summary_df
    analyzer.is_analyzed = True

    # Get parameters from the request URL.
    report_type = request.GET.get("report_type", "detailed")
    lang_code = request.GET.get("lang", settings.LANGUAGE_CODE)

    # Activate the requested language for this specific request.
    activate(lang_code)

    # Regenerate the requested report, which will now have translated column headers.
    report_df = (
        analyzer.get_public_summary()
        if report_type == "public"
        else analyzer.get_detailed_summary()
    )
    if report_df is None:
        return HttpResponse(_("Error generating report."), status=500)

    # Get translated strings for the Excel file components.
    sheet_name = gettext("Report")

    # Create the Excel file in an in-memory buffer.
    output_buffer = io.BytesIO()
    with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
        report_df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        wrap_alignment = Alignment(wrap_text=True, vertical="top")

        # Apply text wrapping style to columns containing detail strings.
        for col_idx, col_name in enumerate(report_df.columns, 1):
            if (
                "详情" in col_name or "Details" in col_name
            ):  # Heuristic to find detail columns
                col_letter = chr(ord("A") + col_idx - 1)
                worksheet.column_dimensions[col_letter].width = 50
                for cell in worksheet[col_letter]:
                    cell.alignment = wrap_alignment

    output_buffer.seek(0)

    # Construct a meaningful, translated, and safe filename.
    base_name, ext = os.path.splitext(original_filename)
    report_type_suffix = (
        gettext("Public") if report_type == "public" else gettext("Detailed")
    )

    filename_utf8 = f"{base_name}_{report_type_suffix}{ext or '.xlsx'}"
    filename_ascii = (
        f"{base_name.encode('ascii', 'ignore').decode()}_{report_type}.xlsx"
    )

    # Create the HTTP response for file download.
    response = HttpResponse(
        output_buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Set the Content-Disposition header according to RFC 6266 for robust non-ASCII support.
    encoded_filename = quote(filename_utf8)
    response["Content-Disposition"] = (
        f"attachment; filename=\"{filename_ascii}\"; filename*=UTF-8''{encoded_filename}"
    )

    return response
