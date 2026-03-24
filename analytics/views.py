import json
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncDate


@login_required
def analytics_dashboard(request):
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    from accounts.models import User
    from appointments.models import Appointment
    from health_records.models import HealthRecord
    from wellness.models import WellnessLog, MentalHealthAssessment

    today   = datetime.date.today()
    month_ago = today - datetime.timedelta(days=30)

    # ── Summary counts ─────────────────────────────────────────────────
    stats = {
        'total_students':      User.objects.filter(role='student').count(),
        'total_staff':         User.objects.filter(role='staff', is_active=True).count(),
        'pending_staff':       User.objects.filter(role='staff', is_active=False).count(),
        'total_appointments':  Appointment.objects.count(),
        'appts_this_month':    Appointment.objects.filter(date__gte=month_ago).count(),
        'appts_today':         Appointment.objects.filter(date=today).count(),
        'pending_appts':       Appointment.objects.filter(status='pending').count(),
        'total_records':       HealthRecord.objects.count(),
        'records_this_month':  HealthRecord.objects.filter(visit_date__gte=month_ago).count(),
        'wellness_logs_month': WellnessLog.objects.filter(date__gte=month_ago).count(),
    }

    # ── Appointments by status (pie) ───────────────────────────────────
    appt_status = list(
        Appointment.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    appt_status_labels = json.dumps([a['status'].replace('_', ' ').title() for a in appt_status])
    appt_status_data   = json.dumps([a['count'] for a in appt_status])

    # ── Appointments by type (bar) ─────────────────────────────────────
    appt_type = list(
        Appointment.objects.values('appointment_type')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    appt_type_labels = json.dumps([a['appointment_type'].replace('_', ' ').title() for a in appt_type])
    appt_type_data   = json.dumps([a['count'] for a in appt_type])

    # ── Monthly appointments (last 6 months, line) ─────────────────────
    monthly_appts = list(
        Appointment.objects
        .filter(date__gte=today - datetime.timedelta(days=180))
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_labels = json.dumps([m['month'].strftime('%b %Y') for m in monthly_appts])
    monthly_data   = json.dumps([m['count'] for m in monthly_appts])

    # ── Students by department (top 8) ────────────────────────────────
    dept_counts = list(
        User.objects.filter(role='student')
        .exclude(department='')
        .values('department')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    dept_labels = json.dumps([d['department'] for d in dept_counts])
    dept_data   = json.dumps([d['count'] for d in dept_counts])

    # ── Students by level ─────────────────────────────────────────────
    level_counts = list(
        User.objects.filter(role='student')
        .exclude(level='')
        .values('level')
        .annotate(count=Count('id'))
        .order_by('level')
    )
    level_labels = json.dumps([l['level'] for l in level_counts])
    level_data   = json.dumps([l['count'] for l in level_counts])

    # ── Wellness: avg mood last 30 days ────────────────────────────────
    daily_mood = list(
        WellnessLog.objects
        .filter(date__gte=month_ago)
        .values('date')
        .annotate(avg_mood=Avg('mood'), avg_stress=Avg('stress_level'))
        .order_by('date')
)

    mood_labels = json.dumps([d['date'].strftime('%d %b') for d in daily_mood])
    mood_data_ch = json.dumps([
        round(float(d['avg_mood']), 2) if d['avg_mood'] is not None else 0
        for d in daily_mood
    ])
    stress_data_ch = json.dumps([
        round(float(d['avg_stress']), 2) if d['avg_stress'] is not None else 0
        for d in daily_mood
    ])

    # ── Top diagnoses ──────────────────────────────────────────────────
    top_diagnoses = (
        HealthRecord.objects
        .exclude(diagnosis='')
        .values('diagnosis')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # ── Recent appointments feed ───────────────────────────────────────
    recent_appts = (
        Appointment.objects
        .select_related('student', 'staff')
        .order_by('-created_at')[:8]
    )

    # ── Mental health severity distribution ────────────────────────────
    mh_assessments = MentalHealthAssessment.objects.filter(date__gte=month_ago)
    mh_severity = {'Minimal': 0, 'Mild': 0, 'Moderate': 0,
                   'Moderately Severe': 0, 'Severe': 0}
    for a in mh_assessments:
        label, _ = a.severity()
        mh_severity[label] = mh_severity.get(label, 0) + 1
    mh_labels = json.dumps(list(mh_severity.keys()))
    mh_data   = json.dumps(list(mh_severity.values()))

    # ── Blood group distribution ───────────────────────────────────────
    blood_groups = list(
        User.objects.filter(role='student')
        .exclude(blood_group__in=['', 'unknown'])
        .values('blood_group')
        .annotate(count=Count('id'))
        .order_by('blood_group')
    )
    bg_labels = json.dumps([b['blood_group'] for b in blood_groups])
    bg_data   = json.dumps([b['count'] for b in blood_groups])

    return render(request, 'analytics/dashboard.html', {
        'stats':            stats,
        'top_diagnoses':    top_diagnoses,
        'recent_appts':     recent_appts,
        # Chart data
        'appt_status_labels': appt_status_labels,
        'appt_status_data':   appt_status_data,
        'appt_type_labels':   appt_type_labels,
        'appt_type_data':     appt_type_data,
        'monthly_labels':     monthly_labels,
        'monthly_data':       monthly_data,
        'dept_labels':        dept_labels,
        'dept_data':          dept_data,
        'level_labels':       level_labels,
        'level_data':         level_data,
        'mood_labels':        mood_labels,
        'mood_data':          mood_data_ch,
        'stress_data':        stress_data_ch,
        'mh_labels':          mh_labels,
        'mh_data':            mh_data,
        'bg_labels':          bg_labels,
        'bg_data':            bg_data,
    })


@login_required
def staff_report(request):
    """Per-staff appointment and record summary — admin only."""
    if not request.user.is_admin_user:
        return redirect('dashboard')

    from accounts.models import User
    from appointments.models import Appointment
    from health_records.models import HealthRecord

    staff_list = User.objects.filter(role='staff', is_active=True).annotate(
        total_appts=Count('appointments_as_staff'),
        completed_appts=Count(
            'appointments_as_staff',
            filter=Q(appointments_as_staff__status='completed')
        ),
        total_records=Count('records_created'),
    ).order_by('-total_appts')

    return render(request, 'analytics/staff_report.html', {'staff_list': staff_list})
