from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                    views.home,             name='home'),
    path('login/',              views.login_view,        name='login'),
    path('logout/',             views.logout_view,       name='logout'),
    path('register/student/',   views.register_student,  name='register_student'),
    path('register/staff/',     views.register_staff,    name='register_staff'),

    # Dashboard
    path('dashboard/',          views.dashboard,         name='dashboard'),

    # Profile tabs
    path('profile/',                     views.profile_personal,  name='profile_personal'),
    path('profile/academic/',            views.profile_academic,  name='profile_academic'),
    path('profile/medical/',             views.profile_medical,   name='profile_medical'),
    path('profile/emergency/',           views.profile_emergency, name='profile_emergency'),
    path('profile/settings/',            views.profile_settings,  name='profile_settings'),
    path('profile/change-password/',     views.change_password,   name='change_password'),

    # Emergency contacts
    path('profile/emergency/add/',             views.add_emergency_contact,    name='add_emergency_contact'),
    path('profile/emergency/<int:pk>/edit/',    views.edit_emergency_contact,   name='edit_emergency_contact'),
    path('profile/emergency/<int:pk>/delete/',  views.delete_emergency_contact, name='delete_emergency_contact'),

    # Student directory (staff + admin)
    path('students/',          views.student_directory, name='student_directory'),
    path('students/<int:pk>/', views.student_detail,    name='student_detail'),

    # Staff management (admin only)
    # NOTE: these do NOT start with 'admin/' to avoid clashing with Django's /admin/ panel
    path('manage/staff/',                  views.pending_staff,    name='pending_staff'),
    path('manage/staff/create/',           views.create_staff,     name='create_staff'),
    path('manage/staff/<int:pk>/approve/', views.approve_staff,    name='approve_staff'),
    path('manage/staff/<int:pk>/deactivate/', views.deactivate_staff, name='deactivate_staff'),
]