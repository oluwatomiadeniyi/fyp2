import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator

from .models import Appointment, AppointmentFeedback, StaffSchedule
from .forms import (AppointmentBookingForm, AppointmentStatusForm,
                    RescheduleForm, CancelForm, FeedbackForm, StaffScheduleForm)
from accounts import notifications as notify


# ── Helpers ────────────────────────────────────────────────────────────────────

def _student_only(request):
    if not request.user.is_student:
        messages.error(request, 'Only students can perform this action.')
        return True
    return False

def _staff_only(request):
    if not (request.user.is_medical_staff or request.user.is_admin_user):
        messages.error(request, 'Access denied.')
        return True
    return False


# ── Appointment list ───────────────────────────────────────────────────────────

@login_required
def appointment_list(request):
    user   = request.user
    status = request.GET.get('status', '')
    atype  = request.GET.get('type', '')
    date_q = request.GET.get('date', '')

    if user.is_student:
        qs = Appointment.objects.filter(student=user)
    elif user.is_medical_staff:
        qs = Appointment.objects.filter(staff=user)
    else:
        qs = Appointment.objects.all()

    qs = qs.select_related('student', 'staff')

    if status:  qs = qs.filter(status=status)
    if atype:   qs = qs.filter(appointment_type=atype)
    if date_q:  qs = qs.filter(date=date_q)

    paginator = Paginator(qs, 15)
    page      = paginator.get_page(request.GET.get('page'))

    # Counts for the tabs
    base = Appointment.objects.filter(student=user) if user.is_student else (
           Appointment.objects.filter(staff=user)   if user.is_medical_staff else
           Appointment.objects.all())

    counts = {
        'all':       base.count(),
        'pending':   base.filter(status='pending').count(),
        'confirmed': base.filter(status='confirmed').count(),
        'completed': base.filter(status='completed').count(),
        'cancelled': base.filter(status='cancelled').count(),
    }

    return render(request, 'appointments/list.html', {
        'page_obj':      page,
        'status':        status,
        'atype':         atype,
        'date_q':        date_q,
        'counts':        counts,
        'status_choices': Appointment.STATUS_CHOICES,
        'type_choices':   Appointment.TYPE_CHOICES,
    })


# ── Book appointment ───────────────────────────────────────────────────────────

@login_required
def book_appointment(request):
    if _student_only(request):
        return redirect('dashboard')

    form = AppointmentBookingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appt         = form.save(commit=False)
        appt.student = request.user
        appt.save()

        notify.send_appointment_booked(appt)
        messages.success(request,
            f'Appointment booked for {appt.date.strftime("%A, %d %B %Y")} at '
            f'{appt.time.strftime("%H:%M")}. '
            f'Status: Pending — a staff member will confirm shortly.')
        return redirect('appointment_detail', pk=appt.pk)

    # Show existing upcoming appointments as context
    upcoming = Appointment.objects.filter(
        student=request.user,
        date__gte=datetime.date.today(),
        status__in=['pending', 'confirmed']
    ).order_by('date', 'time')

    return render(request, 'appointments/book.html', {
        'form': form,
        'upcoming': upcoming,
    })


# ── Appointment detail ─────────────────────────────────────────────────────────

@login_required
def appointment_detail(request, pk):
    user = request.user
    if user.is_student:
        appt = get_object_or_404(Appointment, pk=pk, student=user)
    elif user.is_medical_staff:
        appt = get_object_or_404(Appointment, pk=pk, staff=user)
    else:
        appt = get_object_or_404(Appointment, pk=pk)

    has_feedback = hasattr(appt, 'feedback')
    return render(request, 'appointments/detail.html', {
        'appt': appt,
        'has_feedback': has_feedback,
    })


# ── Update status (staff / admin) ──────────────────────────────────────────────

@login_required
def update_status(request, pk):
    if _staff_only(request):
        return redirect('dashboard')

    if request.user.is_medical_staff:
        appt = get_object_or_404(Appointment, pk=pk, staff=request.user)
    else:
        appt = get_object_or_404(Appointment, pk=pk)

    form = AppointmentStatusForm(request.POST or None, instance=appt)
    if request.method == 'POST' and form.is_valid():
        form.save()
        _notify_status_changed(appt)
        messages.success(request, f'Appointment updated to "{appt.get_status_display()}".')
        return redirect('appointment_detail', pk=appt.pk)

    return render(request, 'appointments/update_status.html', {
        'form': form, 'appt': appt,
    })


# ── Reschedule ─────────────────────────────────────────────────────────────────

@login_required
def reschedule(request, pk):
    user = request.user
    if user.is_student:
        appt = get_object_or_404(Appointment, pk=pk, student=user,
                                  status__in=['pending', 'confirmed'])
    else:
        appt = get_object_or_404(Appointment, pk=pk)

    form = RescheduleForm(request.POST or None, instance=appt)
    if request.method == 'POST' and form.is_valid():
        appt.status = Appointment.STATUS_PENDING   # back to pending after reschedule
        form.save()
        messages.success(request, 'Appointment rescheduled. Staff will re-confirm.')
        return redirect('appointment_detail', pk=appt.pk)

    return render(request, 'appointments/reschedule.html', {
        'form': form, 'appt': appt,
    })


# ── Cancel ─────────────────────────────────────────────────────────────────────

@login_required
def cancel_appointment(request, pk):
    user = request.user
    if user.is_student:
        appt = get_object_or_404(Appointment, pk=pk, student=user,
                                  status__in=['pending', 'confirmed'])
    else:
        appt = get_object_or_404(Appointment, pk=pk)

    form = CancelForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appt.status              = Appointment.STATUS_CANCELLED
        appt.cancellation_reason = form.cleaned_data.get('reason', '')
        appt.save()
        notify.send_appointment_cancelled(appt)
        messages.success(request, 'Appointment cancelled.')
        return redirect('appointment_list')

    return render(request, 'appointments/cancel.html', {
        'form': form, 'appt': appt,
    })


# ── Quick confirm / complete (staff shortcuts) ─────────────────────────────────

@login_required
def quick_confirm(request, pk):
    if _staff_only(request): return redirect('dashboard')
    appt        = get_object_or_404(Appointment, pk=pk, staff=request.user)
    appt.status = Appointment.STATUS_CONFIRMED
    appt.save()
    notify.send_appointment_confirmed(appt)
    messages.success(request, 'Appointment confirmed.')
    return redirect(request.META.get('HTTP_REFERER', 'appointment_list'))


@login_required
def quick_complete(request, pk):
    if _staff_only(request): return redirect('dashboard')
    appt        = get_object_or_404(Appointment, pk=pk, staff=request.user)
    appt.status = Appointment.STATUS_COMPLETED
    appt.save()
    notify.send_appointment_completed(appt)
    messages.success(request, 'Appointment marked as completed.')
    return redirect(request.META.get('HTTP_REFERER', 'appointment_list'))


# ── Feedback ───────────────────────────────────────────────────────────────────

@login_required
def submit_feedback(request, pk):
    if _student_only(request): return redirect('dashboard')
    appt = get_object_or_404(Appointment, pk=pk, student=request.user,
                              status=Appointment.STATUS_COMPLETED)

    if hasattr(appt, 'feedback'):
        messages.info(request, 'You already submitted feedback for this appointment.')
        return redirect('appointment_detail', pk=pk)

    form = FeedbackForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        fb             = form.save(commit=False)
        fb.appointment = appt
        fb.save()
        messages.success(request, 'Thank you for your feedback!')
        return redirect('appointment_detail', pk=pk)

    return render(request, 'appointments/feedback.html', {
        'form': form, 'appt': appt,
    })


# ── Staff schedule ─────────────────────────────────────────────────────────────

@login_required
def manage_schedule(request):
    if not request.user.is_medical_staff:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    slots = StaffSchedule.objects.filter(staff=request.user)
    form  = StaffScheduleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        slot       = form.save(commit=False)
        slot.staff = request.user
        slot.save()
        messages.success(request, 'Availability slot added.')
        return redirect('manage_schedule')

    return render(request, 'appointments/schedule.html', {
        'slots': slots, 'form': form,
    })


@login_required
def delete_schedule_slot(request, pk):
    slot = get_object_or_404(StaffSchedule, pk=pk, staff=request.user)
    if request.method == 'POST':
        slot.delete()
        messages.success(request, 'Slot removed.')
    return redirect('manage_schedule')


# ── Staff: today's appointments ────────────────────────────────────────────────

@login_required
def today_appointments(request):
    if _staff_only(request): return redirect('dashboard')

    if request.user.is_medical_staff:
        appts = Appointment.objects.filter(
            staff=request.user, date=datetime.date.today()
        ).select_related('student').order_by('time')
    else:
        appts = Appointment.objects.filter(
            date=datetime.date.today()
        ).select_related('student', 'staff').order_by('time')

    return render(request, 'appointments/today.html', {'appts': appts})


# ── Notification helpers (console-only for now) ────────────────────────────────

def _notify_booked(appt):
    from django.core.mail import send_mail
    try:
        send_mail(
            subject=f'Appointment Booked — {appt.get_appointment_type_display()}',
            message=(
                f'Dear {appt.student.first_name},\n\n'
                f'Your appointment has been booked for {appt.date} at {appt.time}.\n'
                f'Reason: {appt.reason}\n\n'
                f'It is currently pending confirmation from medical staff.\n\n'
                f'Campus Health Team'
            ),
            from_email=None,
            recipient_list=[appt.student.email],
            fail_silently=True,
        )
    except Exception:
        pass


def _notify_status_changed(appt):
    from django.core.mail import send_mail
    if not appt.student.email:
        return
    try:
        send_mail(
            subject=f'Appointment {appt.get_status_display()} — Campus Health',
            message=(
                f'Dear {appt.student.first_name},\n\n'
                f'Your appointment on {appt.date} at {appt.time} has been '
                f'updated to: {appt.get_status_display().upper()}.\n\n'
                f'{"Notes: " + appt.notes if appt.notes else ""}\n\n'
                f'Campus Health Team'
            ),
            from_email=None,
            recipient_list=[appt.student.email],
            fail_silently=True,
        )
    except Exception:
        pass


# ── Admin: assign a doctor to an appointment ──────────────────────────────────

@login_required
def assign_doctor(request, pk):
    """Admin selects which available doctor handles an appointment."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    appt = get_object_or_404(Appointment, pk=pk)

    # Only available, active staff
    from accounts.models import User
    available_staff = User.objects.filter(
        role='staff', is_active=True, is_available=True
    ).order_by('last_name', 'first_name')

    # Annotate each staff with their confirmed appointments on the same date
    # so admin can see workload
    from django.db.models import Count, Q as DQ
    staff_with_load = []
    for s in available_staff:
        load = Appointment.objects.filter(
            staff=s,
            date=appt.date,
            status__in=['pending', 'confirmed']
        ).count()
        staff_with_load.append({'staff': s, 'load': load})

    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        if staff_id:
            try:
                doctor = User.objects.get(pk=staff_id, role='staff', is_active=True)
                appt.staff  = doctor
                appt.status = Appointment.STATUS_CONFIRMED
                appt.save()
                notify.send_appointment_confirmed(appt)
                notify.send_doctor_assigned_to_staff(appt)
                messages.success(request,
                    f'{doctor.get_full_name()} assigned to '
                    f'{appt.student.get_full_name()}\'s appointment. '
                    f'Status set to Confirmed.')
            except User.DoesNotExist:
                messages.error(request, 'Selected doctor not found.')
        else:
            messages.error(request, 'Please select a doctor.')
        return redirect('assign_doctor', pk=pk)

    return render(request, 'appointments/assign_doctor.html', {
        'appt': appt,
        'staff_with_load': staff_with_load,
    })


# ── Admin: list of unassigned / pending appointments ──────────────────────────

@login_required
def unassigned_appointments(request):
    """Admin dashboard for appointments that need a doctor assigned."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    # Pending with no staff, or pending with staff but not yet confirmed
    unassigned = Appointment.objects.filter(
        status=Appointment.STATUS_PENDING,
    ).select_related('student', 'staff').order_by('date', 'time')

    # Also show upcoming confirmed ones grouped by doctor
    confirmed = Appointment.objects.filter(
        status=Appointment.STATUS_CONFIRMED,
        date__gte=datetime.date.today(),
    ).select_related('student', 'staff').order_by('staff__last_name', 'date', 'time')

    return render(request, 'appointments/unassigned.html', {
        'unassigned': unassigned,
        'confirmed':  confirmed,
    })


# ── Staff: my assigned patients ───────────────────────────────────────────────

@login_required
def my_patients(request):
    """Staff sees all students currently assigned to them."""
    if not request.user.is_medical_staff:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    # Distinct students with confirmed or completed appointments with this doctor
    from accounts.models import User
    patient_ids = Appointment.objects.filter(
        staff=request.user,
        status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_COMPLETED]
    ).values_list('student_id', flat=True).distinct()

    patients = User.objects.filter(pk__in=patient_ids).order_by('last_name', 'first_name')

    # For each patient, get their latest appointment with this doctor
    patient_data = []
    for patient in patients:
        latest = Appointment.objects.filter(
            student=patient, staff=request.user
        ).order_by('-date', '-time').first()
        upcoming = Appointment.objects.filter(
            student=patient, staff=request.user,
            status=Appointment.STATUS_CONFIRMED,
            date__gte=datetime.date.today()
        ).order_by('date', 'time').first()
        patient_data.append({
            'patient': patient,
            'latest':  latest,
            'upcoming': upcoming,
        })

    return render(request, 'appointments/my_patients.html', {
        'patient_data': patient_data,
    })
