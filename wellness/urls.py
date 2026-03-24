from django.urls import path
from . import views

urlpatterns = [
    path('',                            views.wellness_home,            name='wellness_home'),
    path('log/',                        views.log_wellness,             name='log_wellness'),
    path('log/<int:pk>/edit/',          views.edit_wellness_log,        name='edit_wellness_log'),
    path('log/<int:pk>/delete/',        views.delete_wellness_log,      name='delete_wellness_log'),
    path('history/',                    views.wellness_history,         name='wellness_history'),
    path('mental-health/',              views.mental_health_assessment, name='mental_health'),
    path('mental-health/<int:pk>/',     views.mental_health_results,    name='mh_result'),
    path('goals/',                      views.goals,                    name='wellness_goals'),
    path('goals/<int:pk>/toggle/',      views.toggle_goal,              name='toggle_goal'),
    path('goals/<int:pk>/delete/',      views.delete_goal,              name='delete_goal'),
    path('student/<int:student_pk>/',   views.student_wellness_summary, name='student_wellness'),
]
