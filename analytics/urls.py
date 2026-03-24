from django.urls import path
from . import views

urlpatterns = [
    path('',        views.analytics_dashboard, name='analytics_dashboard'),
    path('staff/',  views.staff_report,         name='staff_report'),
]
