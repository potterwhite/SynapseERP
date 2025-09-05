# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905

from django.shortcuts import render
from django.views import View
from django.http import HttpRequest, HttpResponse
from django.conf import settings

# Import the core engine from our own framework
from synapse_attendance.engine.analyzer import AttendanceAnalyzer

class AnalysisView(View):
    """
    A view to handle the attendance analysis process.
    
    - GET: Displays the file upload form.
    - POST: Processes the uploaded Excel file and displays the results.
    This view is stateless and does not interact with the database.
    """
    template_name = 'synapse_attendance/upload.html'
    result_template_name = 'synapse_attendance/result.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        """Handle GET requests by displaying the upload form."""
        return render(request, self.template_name)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Handle POST requests for file upload and analysis."""
        uploaded_file = request.FILES.get('excel_file')
        
        if not uploaded_file:
            context = {'error_message': 'No file was uploaded. Please select a file.'}
            return render(request, self.template_name, context, status=400)

        # NOTE: For now, we load rules from the default packaged file.
        # In a real Django project, this URL would come from settings.
        # remote_rules_url = settings.SYNAPSE_RULES_URL
        #analyzer = AttendanceAnalyzer(remote_rules_url=None)
        remote_rules_url = getattr(settings, 'ATTENDANCE_ANALYZER_RULE_URL', None)
        analyzer = AttendanceAnalyzer(remote_rules_url=remote_rules_url)

        if not analyzer.load_data_from_file(uploaded_file):
            context = {
                'error_message': 'Failed to load data. The file might be corrupted or in the wrong format.'
            }
            return render(request, self.template_name, context, status=400)
        
        try:
            analyzer.analyze()
            detailed_summary = analyzer.get_detailed_summary()
            public_summary = analyzer.get_public_summary()

            context = {
                'filename': uploaded_file.name,
                'detailed_html': detailed_summary.to_html(classes='table', index=False, border=0),
                'public_html': public_summary.to_html(classes='table', index=False, border=0),
            }
            return render(request, self.result_template_name, context)

        except Exception as e:
            # Catch potential errors during the analysis phase.
            print(f"ERROR: Analysis failed - {e}")
            context = {
                'error_message': f'An error occurred during analysis: {e}'
            }
            return render(request, self.template_name, context, status=500)
