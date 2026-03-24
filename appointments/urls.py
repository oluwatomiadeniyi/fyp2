from django.urls import path
from . import views

urlpatterns = [
    path('',                            views.appointment_list,     name='appointment_list'),
    path('book/',                       views.book_appointment,     name='book_appointment'),
    path('today/',                      views.today_appointments,   name='today_appointments'),
    path('<int:pk>/',                   views.appointment_detail,   name='appointment_detail'),
    path('<int:pk>/update/',            views.update_status,        name='update_status'),
    path('<int:pk>/reschedule/',        views.reschedule,           name='reschedule'),
    path('<int:pk>/cancel/',            views.cancel_appointment,   name='cancel_appointment'),
    path('<int:pk>/confirm/',           views.quick_confirm,        name='quick_confirm'),
    path('<int:pk>/complete/',          views.quick_complete,       name='quick_complete'),
    path('<int:pk>/feedback/',          views.submit_feedback,      name='submit_feedback'),
    path('schedule/',                   views.manage_schedule,      name='manage_schedule'),
    path('schedule/<int:pk>/delete/',   views.delete_schedule_slot, name='delete_schedule_slot'),
    path('unassigned/',              views.unassigned_appointments, name='unassigned_appointments'),
    path('<int:pk>/assign/',          views.assign_doctor,           name='assign_doctor'),
    path('my-patients/',             views.my_patients,             name='my_patients'),
]