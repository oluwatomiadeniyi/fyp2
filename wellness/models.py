from django.db import models
from django.conf import settings
from django.utils import timezone


class WellnessLog(models.Model):
    """Daily self-reported wellness check-in by a student."""

    MOOD_CHOICES = [
        (5, 'Excellent'),
        (4, 'Good'),
        (3, 'Okay'),
        (2, 'Low'),
        (1, 'Very Low'),
    ]

    STRESS_CHOICES = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Moderate'),
        (4, 'High'),
        (5, 'Very High'),
    ]

    SLEEP_CHOICES = [
        ('lt4',  'Less than 4 hours'),
        ('4to6', '4 – 6 hours'),
        ('6to8', '6 – 8 hours'),
        ('gt8',  'More than 8 hours'),
    ]

    ACTIVITY_CHOICES = [
        ('none',     'None'),
        ('light',    'Light (walk, stretch)'),
        ('moderate', 'Moderate (30+ min exercise)'),
        ('intense',  'Intense (gym, sport, run)'),
    ]

    APPETITE_CHOICES = [
        ('poor',    'Poor'),
        ('fair',    'Fair'),
        ('good',    'Good'),
        ('very_good','Very Good'),
    ]

    user             = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='wellness_logs', limit_choices_to={'role': 'student'}
    )
    date             = models.DateField(default=timezone.localdate)

    # Core metrics
    mood             = models.IntegerField(choices=MOOD_CHOICES)
    stress_level     = models.IntegerField(choices=STRESS_CHOICES)
    sleep_hours      = models.CharField(max_length=10, choices=SLEEP_CHOICES)
    physical_activity = models.CharField(max_length=10, choices=ACTIVITY_CHOICES,
                            default='none')
    appetite         = models.CharField(max_length=10, choices=APPETITE_CHOICES,
                            default='good')

    # Symptoms today
    has_headache     = models.BooleanField(default=False, verbose_name='Headache')
    has_fever        = models.BooleanField(default=False, verbose_name='Fever')
    has_fatigue      = models.BooleanField(default=False, verbose_name='Fatigue / Tiredness')
    has_nausea       = models.BooleanField(default=False, verbose_name='Nausea')
    has_anxiety      = models.BooleanField(default=False, verbose_name='Anxiety')
    has_pain         = models.BooleanField(default=False, verbose_name='Body Pain')
    other_symptoms   = models.CharField(max_length=200, blank=True,
                           verbose_name='Other Symptoms')

    # Free text
    notes            = models.TextField(blank=True,
                           verbose_name='How are you feeling today?',
                           help_text='Optional — describe your day in a few words')

    # Water & nutrition
    water_glasses    = models.PositiveIntegerField(default=0,
                           verbose_name='Glasses of water today',
                           help_text='1 glass ≈ 250 ml')
    meals_today      = models.PositiveIntegerField(default=3,
                           verbose_name='Number of meals eaten today')

    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering        = ['-date', '-created_at']
        unique_together = ['user', 'date']   # one log per day per student

    def __str__(self):
        return (f"{self.user.get_full_name()} — "
                f"{self.date} (Mood: {self.get_mood_display()})")

    def get_mood_color(self):
        return {5: 'success', 4: 'primary', 3: 'warning',
                2: 'danger', 1: 'dark'}.get(self.mood, 'secondary')

    def get_stress_color(self):
        return {1: 'success', 2: 'primary', 3: 'warning',
                4: 'danger', 5: 'dark'}.get(self.stress_level, 'secondary')

    def active_symptoms(self):
        symptoms = []
        if self.has_headache: symptoms.append('Headache')
        if self.has_fever:    symptoms.append('Fever')
        if self.has_fatigue:  symptoms.append('Fatigue')
        if self.has_nausea:   symptoms.append('Nausea')
        if self.has_anxiety:  symptoms.append('Anxiety')
        if self.has_pain:     symptoms.append('Body Pain')
        if self.other_symptoms: symptoms.append(self.other_symptoms)
        return symptoms

    def wellness_score(self):
        """Simple 0–100 score based on key metrics."""
        score  = self.mood * 10              # 10–50
        score += (6 - self.stress_level) * 5  # 5–25
        sleep_pts = {'lt4': 0, '4to6': 5, '6to8': 15, 'gt8': 10}
        score += sleep_pts.get(self.sleep_hours, 0)
        activity_pts = {'none': 0, 'light': 3, 'moderate': 7, 'intense': 10}
        score += activity_pts.get(self.physical_activity, 0)
        # Deduct for symptoms
        symptom_count = sum([self.has_headache, self.has_fever, self.has_fatigue,
                             self.has_nausea, self.has_anxiety, self.has_pain])
        score -= symptom_count * 3
        return max(0, min(100, score))


class MentalHealthAssessment(models.Model):
    """
    PHQ-9 style mental health self-assessment.
    Students can fill this periodically; staff can view results.
    """

    FREQ_CHOICES = [
        (0, 'Not at all'),
        (1, 'Several days'),
        (2, 'More than half the days'),
        (3, 'Nearly every day'),
    ]

    user         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='mental_assessments'
    )
    date         = models.DateField(default=timezone.localdate)

    # PHQ-9 questions
    q1_interest  = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Little interest or pleasure in doing things')
    q2_depressed = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Feeling down, depressed, or hopeless')
    q3_sleep     = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Trouble falling or staying asleep, or sleeping too much')
    q4_tired     = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Feeling tired or having little energy')
    q5_appetite  = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Poor appetite or overeating')
    q6_failure   = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Feeling bad about yourself')
    q7_focus     = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Trouble concentrating on things')
    q8_movement  = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Moving or speaking slowly, or being fidgety/restless')
    q9_selfharm  = models.IntegerField(choices=FREQ_CHOICES, default=0,
                       verbose_name='Thoughts that you would be better off dead')

    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def total_score(self):
        return (self.q1_interest + self.q2_depressed + self.q3_sleep +
                self.q4_tired + self.q5_appetite + self.q6_failure +
                self.q7_focus + self.q8_movement + self.q9_selfharm)

    def severity(self):
        s = self.total_score()
        if s <= 4:  return ('Minimal',  'success')
        if s <= 9:  return ('Mild',     'primary')
        if s <= 14: return ('Moderate', 'warning')
        if s <= 19: return ('Moderately Severe', 'danger')
        return ('Severe', 'dark')

    def __str__(self):
        label, _ = self.severity()
        return f"{self.user.get_full_name()} — PHQ-9 ({label}) on {self.date}"


class WellnessGoal(models.Model):
    """Personal wellness goals a student sets for themselves."""

    CATEGORY_CHOICES = [
        ('sleep',    'Sleep'),
        ('exercise', 'Exercise'),
        ('water',    'Hydration'),
        ('diet',     'Nutrition'),
        ('mental',   'Mental Health'),
        ('medical',  'Medical'),
        ('other',    'Other'),
    ]

    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='wellness_goals'
    )
    category    = models.CharField(max_length=15, choices=CATEGORY_CHOICES)
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    is_achieved = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_achieved', '-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.title}"
