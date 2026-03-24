from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import User, EmergencyContact
from .forms import (
    StudentRegistrationForm, StaffRegistrationForm, LoginForm,
    PersonalInfoForm, AcademicInfoForm, MedicalInfoForm,
    NotificationPrefsForm, EmergencyContactForm, CustomPasswordChangeForm,
)
from . import notifications as notify


# ── Public pages ──────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')


def login_view(request):
    if request.user.is_authenticated:
        return render(request, 'accounts/already_logged_in.html')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        name = user.first_name or user.username
        messages.success(request, f'Welcome back, {name}!')
        return redirect(request.GET.get('next', 'dashboard'))
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been signed out.')
    # Support ?next= so we can redirect back to login after switching accounts
    next_url = request.GET.get('next', 'login')
    return redirect(next_url)


def register_student(request):
    if request.user.is_authenticated:
        return render(request, 'accounts/already_logged_in.html')
    form = StudentRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        notify.send_welcome(user)
        messages.success(request, 'Account created! Please complete your medical profile.')
        return redirect('profile_medical')
    return render(request, 'accounts/register_student.html', {'form': form})


def register_staff(request):
    """Public staff registration is disabled — admin creates staff accounts directly."""
    from django.http import Http404
    raise Http404


# ── Admin: create a staff account ─────────────────────────────────────────────

@login_required
def create_staff(request):
    """Only admins can create staff accounts."""
    if not request.user.is_admin_user:
        messages.error(request, 'Only administrators can create staff accounts.')
        return redirect('dashboard')

    form = StaffRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Capture plain password before hashing so we can email it
        plain_password = form.cleaned_data.get('password1', '')
        staff = form.save(is_active=True)
        notify.send_staff_account_created(staff, plain_password)
        messages.success(request,
            f'Staff account created for {staff.get_full_name()}. '
            f'Login credentials have been emailed to {staff.email}.')
        return redirect('pending_staff')

    return render(request, 'accounts/create_staff.html', {'form': form})


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}

    if user.is_student:
        # Warn if profile is incomplete
        if not user.profile_complete():
            messages.warning(request,
                'Your profile is incomplete. Please fill in your medical information.')

        # Placeholder querysets — will be real once those apps are built
        context['upcoming_appointments'] = []
        context['recent_wellness']       = []

    elif user.is_medical_staff:
        context['today_appointments'] = []
        context['pending_count']      = 0

    elif user.is_admin_user:
        from appointments.models import Appointment
        context['total_students']    = User.objects.filter(role='student').count()
        context['total_staff']       = User.objects.filter(role='staff', is_active=True).count()
        context['pending_staff']     = User.objects.filter(role='staff', is_active=False).count()
        context['total_appointments'] = Appointment.objects.count()
        context['appts_pending']     = Appointment.objects.filter(status='pending').count()

    return render(request, 'accounts/dashboard.html', context)


# ── Profile ───────────────────────────────────────────────────────────────────

@login_required
def profile_personal(request):
    form = PersonalInfoForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Personal information updated.')
        return redirect('profile_personal')
    return render(request, 'accounts/profile.html', {
        'form': form,
        'active_tab': 'personal',
    })


@login_required
def profile_academic(request):
    if not request.user.is_student:
        return redirect('profile_personal')

    form = AcademicInfoForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Academic information updated.')
        return redirect('profile_academic')
    return render(request, 'accounts/profile.html', {
        'form': form,
        'active_tab': 'academic',
    })


@login_required
def profile_medical(request):
    if not request.user.is_student:
        return redirect('profile_personal')

    form = MedicalInfoForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Medical information updated.')
        return redirect('profile_medical')
    return render(request, 'accounts/profile.html', {
        'form': form,
        'active_tab': 'medical',
    })


@login_required
def profile_emergency(request):
    contacts = request.user.emergency_contacts.all()
    return render(request, 'accounts/profile.html', {
        'contacts': contacts,
        'active_tab': 'emergency',
    })


@login_required
def profile_settings(request):
    form = NotificationPrefsForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Preferences saved.')
        return redirect('profile_settings')
    return render(request, 'accounts/profile.html', {
        'form': form,
        'active_tab': 'settings',
    })


# ── Emergency contacts ────────────────────────────────────────────────────────

@login_required
def add_emergency_contact(request):
    form = EmergencyContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        contact = form.save(commit=False)
        contact.user = request.user
        contact.save()
        messages.success(request, 'Emergency contact added.')
        return redirect('profile_emergency')
    return render(request, 'accounts/emergency_contact_form.html', {
        'form': form, 'action': 'Add',
    })


@login_required
def edit_emergency_contact(request, pk):
    contact = get_object_or_404(EmergencyContact, pk=pk, user=request.user)
    form = EmergencyContactForm(request.POST or None, instance=contact)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Contact updated.')
        return redirect('profile_emergency')
    return render(request, 'accounts/emergency_contact_form.html', {
        'form': form, 'action': 'Edit',
    })


@login_required
def delete_emergency_contact(request, pk):
    contact = get_object_or_404(EmergencyContact, pk=pk, user=request.user)
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Contact removed.')
    return redirect('profile_emergency')


# ── Password change ───────────────────────────────────────────────────────────

@login_required
def change_password(request):
    form = CustomPasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)   # keeps the user logged in
        messages.success(request, 'Password changed successfully.')
        return redirect('profile_settings')
    return render(request, 'accounts/profile.html', {
        'form': form,
        'active_tab': 'password',
    })


# ── Staff / Admin views ───────────────────────────────────────────────────────

@login_required
def student_directory(request):
    if not (request.user.is_medical_staff or request.user.is_admin_user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    q   = request.GET.get('q', '').strip()
    dept = request.GET.get('dept', '').strip()

    students = User.objects.filter(role='student').order_by('last_name', 'first_name')
    if q:
        students = students.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(matric_number__icontains=q) | Q(department__icontains=q) |
            Q(email__icontains=q)
        )
    if dept:
        students = students.filter(department__icontains=dept)

    departments = User.objects.filter(role='student').values_list(
        'department', flat=True).distinct().order_by('department')

    return render(request, 'accounts/student_directory.html', {
        'students': students,
        'departments': departments,
        'q': q,
        'dept': dept,
    })


@login_required
def student_detail(request, pk):
    """Staff / Admin: view a student's full profile."""
    if not (request.user.is_medical_staff or request.user.is_admin_user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    student = get_object_or_404(User, pk=pk, role='student')
    return render(request, 'accounts/student_detail.html', {'student': student})


@login_required
def pending_staff(request):
    """Admin: manage all staff accounts."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    all_staff   = User.objects.filter(role='staff', is_active=True).order_by('last_name')
    inactive    = User.objects.filter(role='staff', is_active=False).order_by('last_name')
    return render(request, 'accounts/pending_staff.html', {
        'all_staff': all_staff,
        'inactive':  inactive,
    })


@login_required
def approve_staff(request, pk):
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    staff_user = get_object_or_404(User, pk=pk, role='staff')
    if request.method == 'POST':
        staff_user.is_active = True
        staff_user.save()
        messages.success(request, f'{staff_user.get_full_name()} has been activated.')
    return redirect('pending_staff')


@login_required
def deactivate_staff(request, pk):
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    staff_user = get_object_or_404(User, pk=pk, role='staff')
    if request.method == 'POST':
        staff_user.is_active = False
        staff_user.save()
        messages.success(request, f'{staff_user.get_full_name()} has been deactivated.')
    return redirect('pending_staff')
