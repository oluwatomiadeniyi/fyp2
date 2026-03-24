from django.contrib import admin
from .models import Appointment, AppointmentFeedback, StaffSchedule


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ['student', 'staff', 'appointment_type', 'date', 'time',
                     'status', 'priority', 'created_at']
    list_filter   = ['status', 'appointment_type', 'priority', 'date']
    search_fields = ['student__first_name', 'student__last_name',
                     'student__matric_number', 'staff__first_name',
                     'staff__last_name', 'reason']
    ordering      = ['-date', '-time']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Participants', {'fields': ['student', 'staff']}),
        ('Appointment', {'fields': ['appointment_type', 'priority', 'status',
                                    'date', 'time', 'duration_minutes',
                                    'reason', 'symptoms']}),
        ('Clinical Notes (Staff Only)', {'fields': ['notes', 'diagnosis',
                                                     'prescription', 'follow_up_date',
                                                     'referred_to']}),
        ('Other', {'fields': ['cancellation_reason', 'reminder_sent',
                               'created_at', 'updated_at']}),
    ]

    actions = ['mark_confirmed', 'mark_completed', 'mark_no_show']

    @admin.action(description='Mark selected as Confirmed')
    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')

    @admin.action(description='Mark selected as Completed')
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')

    @admin.action(description='Mark selected as No Show')
    def mark_no_show(self, request, queryset):
        queryset.update(status='no_show')


@admin.register(AppointmentFeedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'rating', 'would_recommend', 'created_at']
    list_filter  = ['rating', 'would_recommend']


@admin.register(StaffSchedule)
class StaffScheduleAdmin(admin.ModelAdmin):
    list_display = ['staff', 'day_of_week', 'start_time', 'end_time', 'is_active']
    list_filter  = ['day_of_week', 'is_active', 'staff']
