"""
Smart Intelligence Layer — Campus Health & Wellness System
==========================================================
This module provides the "smart" features of the system:

  1. get_at_risk_status(user)     → detects at-risk students from wellness patterns
  2. get_wellness_insights(user)  → generates plain-English trend insights
  3. get_appointment_recommendation(user) → recommends booking if patterns are poor

All functions are pure — they only read from the database, never write.
They are called from views and results passed directly to templates.
"""

import datetime
from django.db.models import Avg


# ── 1. At-risk detection ──────────────────────────────────────────────────────

def get_at_risk_status(user):
    """
    Analyse a student's recent wellness data and return a dict describing
    whether they are at risk and why.

    Returns:
        {
          'is_at_risk': bool,
          'level': 'high' | 'medium' | None,
          'reasons': [list of plain-English reason strings],
          'flags': {
              'low_mood_streak': int,       days of consecutive mood <= 2
              'high_stress_streak': int,    days of consecutive stress >= 4
              'high_phq9': bool,            latest PHQ-9 score >= 10
              'severe_phq9': bool,          latest PHQ-9 score >= 15
              'low_score_streak': int,      days of consecutive wellness score < 40
          }
        }
    """
    from wellness.models import WellnessLog, MentalHealthAssessment

    today = datetime.date.today()
    reasons = []
    flags = {
        'low_mood_streak':    0,
        'high_stress_streak': 0,
        'high_phq9':          False,
        'severe_phq9':        False,
        'low_score_streak':   0,
    }

    # ── Check last 7 days of wellness logs ────────────────────────────────
    recent_logs = list(
        WellnessLog.objects.filter(
            user=user,
            date__gte=today - datetime.timedelta(days=6)
        ).order_by('-date')
    )

    if recent_logs:
        # Consecutive low mood (mood <= 2) counting backwards from most recent
        mood_streak = 0
        for log in recent_logs:
            if log.mood <= 2:
                mood_streak += 1
            else:
                break
        flags['low_mood_streak'] = mood_streak

        # Consecutive high stress (stress >= 4) counting backwards
        stress_streak = 0
        for log in recent_logs:
            if log.stress_level >= 4:
                stress_streak += 1
            else:
                break
        flags['high_stress_streak'] = stress_streak

        # Consecutive low wellness score (< 40) counting backwards
        score_streak = 0
        for log in recent_logs:
            if log.wellness_score() < 40:
                score_streak += 1
            else:
                break
        flags['low_score_streak'] = score_streak

    # ── Check latest PHQ-9 assessment ─────────────────────────────────────
    latest_phq9 = MentalHealthAssessment.objects.filter(user=user).first()
    if latest_phq9:
        score = latest_phq9.total_score()
        if score >= 15:
            flags['severe_phq9'] = True
            flags['high_phq9']   = True
        elif score >= 10:
            flags['high_phq9'] = True

    # ── Build reasons list ────────────────────────────────────────────────
    if flags['low_mood_streak'] >= 3:
        reasons.append(
            f"Low mood reported for {flags['low_mood_streak']} consecutive days"
        )
    if flags['high_stress_streak'] >= 3:
        reasons.append(
            f"High stress reported for {flags['high_stress_streak']} consecutive days"
        )
    if flags['low_score_streak'] >= 3:
        reasons.append(
            f"Wellness score below 40 for {flags['low_score_streak']} consecutive days"
        )
    if flags['severe_phq9']:
        score = latest_phq9.total_score()
        reasons.append(
            f"PHQ-9 score of {score} indicates moderately severe or severe depression"
        )
    elif flags['high_phq9']:
        score = latest_phq9.total_score()
        reasons.append(
            f"PHQ-9 score of {score} indicates moderate depression symptoms"
        )

    # ── Determine risk level ──────────────────────────────────────────────
    is_at_risk = len(reasons) > 0
    if flags['severe_phq9'] or flags['low_mood_streak'] >= 5 or flags['high_stress_streak'] >= 5:
        level = 'high'
    elif is_at_risk:
        level = 'medium'
    else:
        level = None

    return {
        'is_at_risk': is_at_risk,
        'level':      level,
        'reasons':    reasons,
        'flags':      flags,
    }


# ── 2. Wellness trend insights ────────────────────────────────────────────────

def get_wellness_insights(user):
    """
    Compare this week's wellness metrics to last week and generate
    plain-English insight strings with an icon and colour.

    Returns a list of dicts:
        [
          {
            'icon':    'bi bi-emoji-smile',
            'color':   'success' | 'warning' | 'info' | 'danger',
            'message': 'Your average mood this week is higher than last week.',
          },
          ...
        ]
    """
    from wellness.models import WellnessLog

    today       = datetime.date.today()
    week_start  = today - datetime.timedelta(days=6)
    prev_start  = today - datetime.timedelta(days=13)
    prev_end    = today - datetime.timedelta(days=7)

    this_week = WellnessLog.objects.filter(user=user, date__gte=week_start)
    last_week = WellnessLog.objects.filter(
        user=user, date__gte=prev_start, date__lte=prev_end
    )

    this_avg = this_week.aggregate(
        mood=Avg('mood'), stress=Avg('stress_level')
    )
    last_avg = last_week.aggregate(
        mood=Avg('mood'), stress=Avg('stress_level')
    )

    insights = []
    this_count = this_week.count()

    # ── Logging streak ────────────────────────────────────────────────────
    # Count consecutive logged days going backwards from today
    streak = 0
    for i in range(30):
        check_date = today - datetime.timedelta(days=i)
        if WellnessLog.objects.filter(user=user, date=check_date).exists():
            streak += 1
        else:
            break

    if streak >= 7:
        insights.append({
            'icon':    'bi bi-fire',
            'color':   'success',
            'message': f"You've logged {streak} days in a row — outstanding consistency!"
        })
    elif streak >= 3:
        insights.append({
            'icon':    'bi bi-calendar-check',
            'color':   'success',
            'message': f"You've logged {streak} days in a row — keep it up!"
        })
    elif this_count == 0:
        insights.append({
            'icon':    'bi bi-calendar-x',
            'color':   'warning',
            'message': "You haven't logged this week yet. Regular check-ins help track your wellbeing."
        })

    # ── Mood comparison ───────────────────────────────────────────────────
    if this_avg['mood'] and last_avg['mood']:
        diff = this_avg['mood'] - last_avg['mood']
        if diff >= 0.5:
            insights.append({
                'icon':    'bi bi-emoji-smile-fill',
                'color':   'success',
                'message': f"Your average mood this week is higher than last week — things seem to be improving."
            })
        elif diff <= -0.5:
            insights.append({
                'icon':    'bi bi-emoji-frown',
                'color':   'warning',
                'message': "Your average mood this week is lower than last week. Consider speaking to someone if you're struggling."
            })
        else:
            insights.append({
                'icon':    'bi bi-emoji-neutral',
                'color':   'info',
                'message': "Your mood has been consistent this week compared to last week."
            })
    elif this_avg['mood']:
        m = this_avg['mood']
        if m >= 4:
            insights.append({
                'icon':    'bi bi-emoji-smile-fill',
                'color':   'success',
                'message': f"Your average mood this week is {m:.1f}/5 — you're doing great!"
            })
        elif m <= 2:
            insights.append({
                'icon':    'bi bi-emoji-frown',
                'color':   'danger',
                'message': f"Your average mood this week is {m:.1f}/5. Please don't hesitate to seek support."
            })

    # ── Stress comparison ─────────────────────────────────────────────────
    if this_avg['stress'] and last_avg['stress']:
        diff = this_avg['stress'] - last_avg['stress']
        if diff >= 0.5:
            insights.append({
                'icon':    'bi bi-lightning-charge',
                'color':   'warning',
                'message': "Your stress level is higher this week than last week. Try to find time to rest."
            })
        elif diff <= -0.5:
            insights.append({
                'icon':    'bi bi-wind',
                'color':   'success',
                'message': "Your stress level is lower this week than last week — well done."
            })

    # ── Low logs this week ────────────────────────────────────────────────
    if 1 <= this_count <= 2 and streak < 3:
        insights.append({
            'icon':    'bi bi-info-circle',
            'color':   'info',
            'message': f"You've only logged {this_count} time{'s' if this_count > 1 else ''} this week. Daily check-ins give more accurate insights."
        })

    return insights


# ── 3. Appointment recommendation ─────────────────────────────────────────────

def get_appointment_recommendation(user):
    """
    Determine whether to show a "book a consultation" recommendation
    based on recent wellness patterns.

    Returns a dict or None:
        {
          'show':    True,
          'reason':  "Based on your recent wellness logs...",
          'type':    'mental_health' | 'general',
        }
    """
    from wellness.models import WellnessLog, MentalHealthAssessment

    today = datetime.date.today()

    # Get last 5 logs
    recent = list(
        WellnessLog.objects.filter(
            user=user,
            date__gte=today - datetime.timedelta(days=6)
        ).order_by('-date')[:5]
    )

    if len(recent) < 3:
        return None  # not enough data to make a recommendation

    # Count how many of the recent logs have concerning metrics
    low_mood_count    = sum(1 for l in recent if l.mood <= 2)
    high_stress_count = sum(1 for l in recent if l.stress_level >= 4)
    low_score_count   = sum(1 for l in recent if l.wellness_score() < 40)

    # Check PHQ-9
    latest_phq9 = MentalHealthAssessment.objects.filter(user=user).first()
    high_phq9 = latest_phq9 and latest_phq9.total_score() >= 10

    # Check they haven't already booked a recent appointment
    from appointments.models import Appointment
    recent_booking = Appointment.objects.filter(
        student=user,
        status__in=['pending', 'confirmed'],
        date__gte=today
    ).exists()

    if recent_booking:
        return None  # already has a pending/confirmed booking — don't nag

    # Mental health recommendation (highest priority)
    if high_phq9 or (low_mood_count >= 3 and high_stress_count >= 2):
        return {
            'show':   True,
            'reason': (
                "Based on your recent wellness logs and mental health assessment, "
                "we recommend booking a mental health consultation with one of our counsellors."
            ),
            'type':   'mental_health',
        }

    # General wellness recommendation
    if low_mood_count >= 3 or (high_stress_count >= 3 and low_score_count >= 3):
        return {
            'show':   True,
            'reason': (
                "Based on your recent wellness logs, we recommend booking a general "
                "health consultation. Talking to a doctor can help."
            ),
            'type':   'general',
        }

    return None
