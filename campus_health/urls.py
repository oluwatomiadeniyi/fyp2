from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


class AppRestrictedAdmin(AdminSite):
    """
    Block any user with an app role (admin/staff/student) from
    accessing the Django admin panel, even if they are a superuser.
    The /admin/ panel is reserved for developer/technical accounts only.
    App admins manage everything through the application interface.
    """
    def has_permission(self, request):
        if not request.user.is_authenticated or not request.user.is_active:
            return False
        # Any user with an app role is blocked from Django admin
        role = getattr(request.user, 'role', None)
        if role in ('admin', 'staff', 'student'):
            return False
        # Only raw superusers with no app role can access Django admin
        return request.user.is_superuser

    def login(self, request, extra_context=None):
        # Redirect app users to the application dashboard
        if request.user.is_authenticated:
            role = getattr(request.user, 'role', None)
            if role in ('admin', 'staff', 'student'):
                return redirect('dashboard')
        return super().login(request, extra_context)


# Replace the default admin site class so all model registrations
# (in accounts/admin.py, appointments/admin.py etc.) are preserved
admin.site.__class__ = AppRestrictedAdmin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('appointments/', include('appointments.urls')),
    path('health-records/', include('health_records.urls')),
    path('wellness/', include('wellness.urls')),
    path('analytics/', include('analytics.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)