from django.contrib import admin
from .models import WellnessLog, MentalHealthAssessment, WellnessGoal


@admin.register(WellnessLog)
class WellnessLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'date', 'mood', 'stress_level',
                     'sleep_hours', 'physical_activity']
    list_filter   = ['mood', 'stress_level', 'physical_activity', 'date']
    search_fields = ['user__first_name', 'user__last_name', 'user__matric_number']
    date_hierarchy = 'date'
    ordering       = ['-date']


@admin.register(MentalHealthAssessment)
class MHAdmin(admin.ModelAdmin):
    list_display  = ['user', 'date', 'total_score']
    list_filter   = ['date']
    search_fields = ['user__first_name', 'user__last_name']
    ordering      = ['-date']

    def total_score(self, obj):
        return obj.total_score()
    total_score.short_description = 'PHQ-9 Score'


@admin.register(WellnessGoal)
class GoalAdmin(admin.ModelAdmin):
    list_display  = ['user', 'category', 'title', 'is_achieved', 'target_date']
    list_filter   = ['category', 'is_achieved']
    search_fields = ['user__first_name', 'user__last_name', 'title']

