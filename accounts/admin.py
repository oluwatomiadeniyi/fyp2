from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmergencyContact


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['username', 'get_full_name', 'role', 'email',
                      'department', 'level', 'is_active', 'created_at']
    list_filter    = ['role', 'is_active', 'gender', 'department', 'level']
    search_fields  = ['username', 'email', 'first_name', 'last_name',
                      'matric_number', 'staff_id', 'department']
    ordering       = ['-created_at']
    list_editable  = ['role', 'is_active']   # ← edit role directly from the list view

    # ── Shown when ADDING a new user ────────────────────────────────
    # Django's default add_fieldsets only asks for username + password.
    # We extend it so role, name and email are set at creation time.
    add_fieldsets = (
        ('Account', {
            'classes': ('wide',),
            'fields':  ('username', 'password1', 'password2'),
        }),
        ('Role — set this first!', {
            'classes': ('wide',),
            'description': (
                'Choose the correct role before saving. '
                'Student = patient, Staff = doctor/nurse, Admin = system admin.'
            ),
            'fields': ('role', 'is_active'),
        }),
        ('Basic info', {
            'classes': ('wide',),
            'fields':  ('first_name', 'last_name', 'email', 'phone'),
        }),
    )

    # ── Shown when EDITING an existing user ─────────────────────────
    fieldsets = (
        # Role is the very first thing — hard to miss
        ('Role & Status', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser'),
        }),
        ('Login', {
            'fields': ('username', 'password'),
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone',
                'date_of_birth', 'gender', 'profile_photo',
                'address', 'nationality', 'state_of_origin',
            ),
        }),
        ('Academic Info (Students)', {
            'fields': (
                'matric_number', 'department', 'faculty',
                'level', 'hall_of_residence',
            ),
            'classes': ('collapse',),
        }),
        ('Medical Info', {
            'fields': (
                'blood_group', 'genotype', 'height_cm', 'weight_kg',
                'allergies', 'chronic_conditions', 'current_medications',
                'past_surgeries', 'disability',
                'immunization_up_to_date', 'hiv_status',
                'has_nhis', 'nhis_number', 'insurance_provider',
            ),
            'classes': ('collapse',),
        }),
        ('Staff Info', {
            'fields': ('staff_id', 'specialization', 'qualification', 'is_available'),
            'classes': ('collapse',),
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'sms_notifications'),
            'classes': ('collapse',),
        }),
    )

    actions = ['approve_staff_accounts', 'make_staff_role', 'make_admin_role']

    @admin.action(description='✅ Approve & activate selected staff accounts')
    def approve_staff_accounts(self, request, queryset):
        count = queryset.filter(role='staff').update(is_active=True)
        self.message_user(request, f'{count} staff account(s) approved and activated.')

    @admin.action(description='Set selected users → Medical Staff role')
    def make_staff_role(self, request, queryset):
        count = queryset.update(role='staff', is_active=True)
        self.message_user(request, f'{count} user(s) set to Medical Staff.')

    @admin.action(description='Set selected users → Admin role')
    def make_admin_role(self, request, queryset):
        count = queryset.update(role='admin', is_active=True)
        self.message_user(request, f'{count} user(s) set to Admin.')


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display  = ['name', 'user', 'relationship', 'phone', 'is_primary']
    list_filter   = ['relationship', 'is_primary']
    search_fields = ['name', 'phone', 'user__first_name', 'user__last_name']