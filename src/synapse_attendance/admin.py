# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905

from django.contrib import admin
from .models import Employee, AttendanceReport

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the Employee model.
    """
    list_display = ('full_name', 'employee_id', 'user', 'created_at')
    search_fields = ('full_name', 'employee_id', 'user__username')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the AttendanceReport model.
    """
    list_display = (
        'employee', 
        'start_date', 
        'end_date', 
        'status', 
        'attendance_days', 
        'total_overtime_hours', 
        'late_count', 
        'generated_at'
    )
    search_fields = ('employee__full_name',)
    list_filter = ('status', 'start_date', 'generated_at')
    readonly_fields = ('generated_at',)
    fieldsets = (
        (None, {
            'fields': ('employee', ('start_date', 'end_date'), 'status')
        }),
        ('Analysis Results', {
            'classes': ('collapse',),
            'fields': (
                ('attendance_days', 'absent_days'),
                ('late_count', 'total_late_minutes'),
                ('early_quit_count', 'total_early_quit_minutes'),
                'missing_punch_count',
                'total_overtime_hours',
            ),
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('generated_at', 'raw_data_snapshot'),
        }),
    )
