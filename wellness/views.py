import datetime
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count

from .models import WellnessLog, MentalHealthAssessment, WellnessGoal
from .forms import WellnessLogForm, MentalHealthForm, WellnessGoalForm


# ── Wellness dashboard ─────────────────────────────────────────────────────────

@login_required
def wellness_home(request):
    user  = request.user
    today = datetime.date.today()

    # Check if already logged today
    today_log = WellnessLog.objects.filter(user=user, date=today).first()

    # Last 30 days of logs for chart
    logs = WellnessLog.objects.filter(
        user=user,
        date__gte=today - datetime.timedelta(days=29)
    ).order_by('date')

    # Chart data
    chart_labels = [l.date.strftime('%d %b') for l in logs]
    mood_data    = [l.mood          for l in logs]
    stress_data  = [l.stress_level  for l in logs]
    score_data   = [l.wellness_score() for l in logs]

    # Averages
    avg = logs.aggregate(
        avg_mood=Avg('mood'),
        avg_stress=Avg('stress_level'),
    )

    # Recent 7 logs for the table
    recent_logs = WellnessLog.objects.filter(user=user).order_by('-date')[:7]

    # Active goals
    goals = WellnessGoal.objects.filter(user=user, is_achieved=False)

    # Latest mental health assessment
    latest_mh = MentalHealthAssessment.objects.filter(user=user).first()

    return render(request, 'wellness/home.html', {
        'today_log':     today_log,
        'recent_logs':   recent_logs,
        'goals':         goals,
        'latest_mh':     latest_mh,
        'avg':           avg,
        'chart_labels':  json.dumps(chart_labels),
        'mood_data':     json.dumps(mood_data),
        'stress_data':   json.dumps(stress_data),
        'score_data':    json.dumps(score_data),
    })


# ── Log today ──────────────────────────────────────────────────────────────────

@login_required
def log_wellness(request):
    today = datetime.date.today()

    # If already logged today, redirect to edit
    existing = WellnessLog.objects.filter(user=request.user, date=today).first()
    if existing:
        return redirect('edit_wellness_log', pk=existing.pk)

    form = WellnessLogForm(request.POST or None, initial={'date': today})
    if request.method == 'POST' and form.is_valid():
        log      = form.save(commit=False)
        log.user = request.user
        log.save()

        score = log.wellness_score()
        if score >= 70:
            messages.success(request, f'Great check-in! Your wellness score today is {score}/100.')
        elif score >= 40:
            messages.info(request, f'Check-in saved. Wellness score: {score}/100. Keep going!')
        else:
            messages.warning(request,
                f'Check-in saved (score: {score}/100). Consider speaking to a counsellor if '
                'you are feeling persistently low.')

        return redirect('wellness_home')

    return render(request, 'wellness/log_form.html', {
        'form': form, 'title': "Today's Check-In", 'action': 'Submit',
    })


@login_required
def edit_wellness_log(request, pk):
    log  = get_object_or_404(WellnessLog, pk=pk, user=request.user)
    form = WellnessLogForm(request.POST or None, instance=log)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Log updated.')
        return redirect('wellness_home')
    return render(request, 'wellness/log_form.html', {
        'form': form, 'title': f'Edit Log — {log.date}', 'action': 'Save Changes',
    })


@login_required
def wellness_history(request):
    logs = WellnessLog.objects.filter(
        user=request.user
    ).order_by('-date')

    return render(request, 'wellness/history.html', {'logs': logs})


@login_required
def delete_wellness_log(request, pk):
    log = get_object_or_404(WellnessLog, pk=pk, user=request.user)
    if request.method == 'POST':
        log.delete()
        messages.success(request, 'Log deleted.')
    return redirect('wellness_history')


# ── Mental health assessment ───────────────────────────────────────────────────

@login_required
def mental_health_assessment(request):
    form = MentalHealthForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        assessment      = form.save(commit=False)
        assessment.user = request.user
        assessment.save()

        label, css = assessment.severity()
        if assessment.total_score() >= 15:
            messages.warning(request,
                f'Your PHQ-9 score suggests {label} depression symptoms. '
                'We strongly recommend speaking with a counsellor at the health centre.')
        elif assessment.total_score() >= 10:
            messages.info(request,
                f'Your PHQ-9 score suggests {label} symptoms. '
                'Consider booking a mental health consultation.')
        else:
            messages.success(request,
                f'Assessment complete. Your score indicates {label} symptoms.')

        return redirect('wellness_home')

    # Show previous assessments
    past = MentalHealthAssessment.objects.filter(user=request.user).order_by('-date')[:5]
    return render(request, 'wellness/mental_health.html', {
        'form': form, 'past': past,
    })


@login_required
def mental_health_results(request, pk):
    assessment = get_object_or_404(MentalHealthAssessment, pk=pk, user=request.user)
    label, css = assessment.severity()
    return render(request, 'wellness/mh_result.html', {
        'assessment': assessment, 'label': label, 'css': css,
    })


# ── Goals ──────────────────────────────────────────────────────────────────────

@login_required
def goals(request):
    user        = request.user
    active      = WellnessGoal.objects.filter(user=user, is_achieved=False)
    achieved    = WellnessGoal.objects.filter(user=user, is_achieved=True)
    form        = WellnessGoalForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        goal      = form.save(commit=False)
        goal.user = user
        goal.save()
        messages.success(request, 'Goal added!')
        return redirect('wellness_goals')

    return render(request, 'wellness/goals.html', {
        'form': form, 'active': active, 'achieved': achieved,
    })


@login_required
def toggle_goal(request, pk):
    goal = get_object_or_404(WellnessGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.is_achieved = not goal.is_achieved
        goal.save()
        if goal.is_achieved:
            messages.success(request, f'🎉 Goal achieved: "{goal.title}"')
    return redirect('wellness_goals')


@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(WellnessGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal removed.')
    return redirect('wellness_goals')


# ── Staff: view a student's wellness summary ───────────────────────────────────

@login_required
def student_wellness_summary(request, student_pk):
    if not (request.user.is_medical_staff or request.user.is_admin_user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    from accounts.models import User
    student = get_object_or_404(User, pk=student_pk, role='student')

    logs = WellnessLog.objects.filter(
        user=student,
        date__gte=datetime.date.today() - datetime.timedelta(days=29)
    ).order_by('date')

    avg = logs.aggregate(avg_mood=Avg('mood'), avg_stress=Avg('stress_level'))
    latest_mh = MentalHealthAssessment.objects.filter(user=student).first()

    chart_labels = json.dumps([l.date.strftime('%d %b') for l in logs])
    mood_data    = json.dumps([l.mood for l in logs])
    stress_data  = json.dumps([l.stress_level for l in logs])

    return render(request, 'wellness/student_summary.html', {
        'student': student,
        'logs': logs,
        'avg': avg,
        'latest_mh': latest_mh,
        'chart_labels': chart_labels,
        'mood_data': mood_data,
        'stress_data': stress_data,
    })
