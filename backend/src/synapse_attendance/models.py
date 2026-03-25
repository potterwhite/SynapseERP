# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905

from django.db import models
from django.utils import timezone
from django.conf import settings

class Employee(models.Model):
    """
    Represents an employee.
    
    This model stores basic employee information. It can be extended
    with more fields like department, position, etc.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employee_profile',
        help_text="Link to the Django User model for authentication."
    )
    employee_id = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="The unique identifier for the employee in the company system."
    )
    full_name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="The full name of the employee, used for matching in reports."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

class AttendanceReport(models.Model):
    """
    Stores the summary of an attendance analysis run.
    
    This model captures the high-level results for an employee over
    a specific period, allowing for historical data tracking.
    """
    class ReportStatus(models.TextChoices):
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        ERROR = 'ERROR', 'Error'

    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='reports'
    )
    
    # Report period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Key metrics from the analysis
    attendance_days = models.FloatField(default=0)
    total_overtime_hours = models.FloatField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    total_late_minutes = models.FloatField(default=0)
    early_quit_count = models.PositiveIntegerField(default=0)
    total_early_quit_minutes = models.FloatField(default=0)
    missing_punch_count = models.PositiveIntegerField(default=0)
    absent_days = models.FloatField(default=0)
    
    # Metadata
    status = models.CharField(
        max_length=20, 
        choices=ReportStatus.choices, 
        default=ReportStatus.PROCESSING
    )
    generated_at = models.DateTimeField(default=timezone.now)
    raw_data_snapshot = models.JSONField(
        blank=True, 
        null=True, 
        help_text="A JSON snapshot of the summary DataFrame for auditing."
    )

    class Meta:
        verbose_name = "Attendance Report"
        verbose_name_plural = "Attendance Reports"
        ordering = ['-generated_at', 'employee__full_name']
        unique_together = ('employee', 'start_date', 'end_date')

    def __str__(self):
        return f"Report for {self.employee.full_name} ({self.start_date} to {self.end_date})"
