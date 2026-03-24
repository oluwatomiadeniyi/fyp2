from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime


class Appointment(models.Model):

    # ── Status ─────────────────────────────────────────────────────────
    STATUS_PENDING   = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_NO_SHOW   = 'no_show'
    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_NO_SHOW,   'No Show'),
    ]

    # ── Type ───────────────────────────────────────────────────────────
    TYPE_CHOICES = [
        ('general',      'General Consultation'),
        ('followup',     'Follow-up Visit'),
        ('emergency',    'Emergency'),
        ('mental_health','Mental Health'),
        ('dental',       'Dental'),
        ('eye',          'Eye Care'),
        ('lab',          'Laboratory Test'),
        ('vaccination',  'Vaccination'),
        ('physical',     'Physical Examination'),
        ('referral',     'Referral Review'),
    ]

    # ── Priority ───────────────────────────────────────────────────────
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('normal', 'Normal'),
        ('high',   'High'),
        ('urgent', 'Urgent'),
    ]

    # ── Participants ────────────────────────────────────────────────────
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='appointments_as_student',
        limit_choices_to={'role': 'student'}
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='appointments_as_staff',
        limit_choices_to={'role': 'staff'}
    )

    # ── Details ─────────────────────────────────────────────────────────
    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    priority         = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status           = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING)

    date             = models.DateField()
    time             = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=30)

    reason           = models.TextField(help_text='Reason for the visit')
    symptoms         = models.TextField(blank=True, help_text='Current symptoms if any')

    # ── Staff-only fields ────────────────────────────────────────────────
    notes              = models.TextField(blank=True, help_text='Clinical notes (staff only)')
    diagnosis          = models.TextField(blank=True)
    prescription       = models.TextField(blank=True)
    follow_up_date     = models.DateField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    referred_to        = models.CharField(max_length=200, blank=True,
                             help_text='External doctor/hospital if referred')

    # ── Tracking ─────────────────────────────────────────────────────────
    reminder_sent = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        indexes  = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['staff', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return (f"{self.student.get_full_name()} — "
                f"{self.get_appointment_type_display()} on {self.date} at {self.time}")

    @property
    def is_upcoming(self):
        return (self.date >= datetime.date.today() and
                self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED])

    @property
    def is_past(self):
        return self.date < datetime.date.today()

    def get_status_badge_class(self):
        return {
            'pending':   'warning',
            'confirmed': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
            'no_show':   'secondary',
        }.get(self.status, 'secondary')

    def get_priority_badge_class(self):
        return {
            'low':    'secondary',
            'normal': 'info',
            'high':   'warning',
            'urgent': 'danger',
        }.get(self.priority, 'secondary')


class AppointmentFeedback(models.Model):
    appointment      = models.OneToOneField(Appointment, on_delete=models.CASCADE,
                           related_name='feedback')
    rating           = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment          = models.TextField(blank=True)
    would_recommend  = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback — {self.appointment} ({self.rating}/5)"


class StaffSchedule(models.Model):
    """
    Defines when a staff member is available each week.
    Students see these slots when booking.
    """
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'),
    ]

    staff       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='schedule', limit_choices_to={'role': 'staff'}
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering        = ['day_of_week', 'start_time']
        unique_together = ['staff', 'day_of_week', 'start_time']

    def __str__(self):
        return (f"{self.staff.get_full_name()} — "
                f"{self.get_day_of_week_display()} "
                f"{self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}")
