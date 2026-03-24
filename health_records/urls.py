from django.urls import path
from . import views

urlpatterns = [
    path('',                                views.record_list,       name='record_list'),
    path('create/',                         views.create_record,     name='create_record'),
    path('<int:pk>/',                       views.record_detail,     name='record_detail'),
    path('<int:pk>/edit/',                  views.edit_record,       name='edit_record'),
    path('<int:pk>/delete/',               views.delete_record,     name='delete_record'),
    path('<int:record_pk>/upload/',        views.upload_document,   name='upload_document'),
    path('documents/<int:pk>/delete/',    views.delete_document,   name='delete_document'),
    path('student/<int:student_pk>/',     views.student_history,   name='student_history'),
    path('vaccinations/',                  views.vaccination_list,  name='vaccination_list'),
    path('vaccinations/add/',             views.add_vaccination,   name='add_vaccination'),
]
