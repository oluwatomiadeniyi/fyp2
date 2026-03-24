from django.db import models
from django.conf import settings


class HealthRecord(models.Model):
    """
    A clinical record created by staff after a consultation.
    One record per visit — linked to an appointment when possible.
    """

    VISIT_TYPE_CHOICES = [
        ('consultation',  'General Consultation'),
        ('followup',      'Follow-up Visit'),
        ('emergency',     'Emergency'),
        ('mental_health', 'Mental Health'),
        ('dental',        'Dental'),
        ('eye',           'Eye Care'),
        ('lab',           'Laboratory Test'),
        ('vaccination',   'Vaccination'),
        ('physical',      'Physical Examination'),
        ('referral',      'Referral'),
    ]

    OUTCOME_CHOICES = [
        ('treated',        'Treated & Discharged'),
        ('admitted',       'Admitted'),
        ('referred',       'Referred Externally'),
        ('followup',       'Follow-up Scheduled'),
        ('no_treatment',   'No Treatment Required'),
        ('deceased',       'Deceased'),
    ]

    # ── Participants ────────────────────────────────────────────────────
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='health_records',
        limit_choices_to={'role': 'student'}
    )
    attending_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='records_created',
        limit_choices_to={'role': 'staff'}
    )
    appointment = models.OneToOneField(
        'appointments.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='health_record'
    )

    # ── Visit info ──────────────────────────────────────────────────────
    visit_date  = models.DateField()
    visit_type  = models.CharField(max_length=20, choices=VISIT_TYPE_CHOICES,
                      default='consultation')
    outcome     = models.CharField(max_length=20, choices=OUTCOME_CHOICES,
                      default='treated')

    # ── Vitals ─────────────────────────────────────────────────────────
    temperature_c    = models.DecimalField(max_digits=4, decimal_places=1,
                           null=True, blank=True, verbose_name='Temperature (°C)')
    blood_pressure   = models.CharField(max_length=15, blank=True,
                           verbose_name='Blood Pressure (mmHg)',
                           help_text='e.g. 120/80')
    pulse_rate       = models.PositiveIntegerField(null=True, blank=True,
                           verbose_name='Pulse Rate (bpm)')
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True,
                           verbose_name='Respiratory Rate (breaths/min)')
    oxygen_saturation = models.DecimalField(max_digits=4, decimal_places=1,
                            null=True, blank=True,
                            verbose_name='Oxygen Saturation (%)')
    weight_kg        = models.DecimalField(max_digits=5, decimal_places=1,
                           null=True, blank=True, verbose_name='Weight (kg)')
    height_cm        = models.DecimalField(max_digits=5, decimal_places=1,
                           null=True, blank=True, verbose_name='Height (cm)')

    # ── Clinical ────────────────────────────────────────────────────────
    chief_complaint  = models.TextField(verbose_name='Chief Complaint / Presenting Symptoms')
    history          = models.TextField(blank=True, verbose_name='History of Presenting Illness')
    examination      = models.TextField(blank=True, verbose_name='Physical Examination Findings')
    diagnosis        = models.TextField(verbose_name='Diagnosis')
    treatment        = models.TextField(blank=True, verbose_name='Treatment / Management')
    prescription     = models.TextField(blank=True, verbose_name='Prescription')
    lab_results      = models.TextField(blank=True, verbose_name='Lab Results / Investigations')
    notes            = models.TextField(blank=True, verbose_name='Additional Notes')
    follow_up_date   = models.DateField(null=True, blank=True,
                           verbose_name='Follow-up Date')
    referred_to      = models.CharField(max_length=200, blank=True,
                           verbose_name='Referred To (if applicable)')
    is_confidential  = models.BooleanField(default=False,
                           verbose_name='Mark as confidential (student cannot view)')

    # ── Timestamps ──────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date', '-created_at']
        indexes  = [
            models.Index(fields=['student', 'visit_date']),
            models.Index(fields=['attending_staff', 'visit_date']),
        ]

    def __str__(self):
        return (f"{self.student.get_full_name()} — "
                f"{self.get_visit_type_display()} on {self.visit_date}")

    def get_bmi(self):
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            h = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (h * h), 1)
        return None

    def get_outcome_badge_class(self):
        return {
            'treated':      'success',
            'admitted':     'warning',
            'referred':     'info',
            'followup':     'primary',
            'no_treatment': 'secondary',
            'deceased':     'dark',
        }.get(self.outcome, 'secondary')


class Prescription(models.Model):
    """Individual drug items within a health record's prescription."""

    FREQUENCY_CHOICES = [
        ('od',  'Once daily (OD)'),
        ('bd',  'Twice daily (BD)'),
        ('tds', 'Three times daily (TDS)'),
        ('qds', 'Four times daily (QDS)'),
        ('prn', 'As needed (PRN)'),
        ('stat','Immediately (STAT)'),
        ('nocte','At night (Nocte)'),
    ]

    ROUTE_CHOICES = [
        ('oral',   'Oral'),
        ('iv',     'Intravenous (IV)'),
        ('im',     'Intramuscular (IM)'),
        ('sc',     'Subcutaneous (SC)'),
        ('topical','Topical'),
        ('inhaled','Inhaled'),
        ('rectal', 'Rectal'),
        ('eye',    'Eye drops'),
        ('ear',    'Ear drops'),
    ]

    record     = models.ForeignKey(HealthRecord, on_delete=models.CASCADE,
                     related_name='medications')
    drug_name  = models.CharField(max_length=200)
    dosage     = models.CharField(max_length=100, help_text='e.g. 500mg, 10ml')
    frequency  = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    route      = models.CharField(max_length=10, choices=ROUTE_CHOICES, default='oral')
    duration   = models.CharField(max_length=50, help_text='e.g. 5 days, 2 weeks')
    instructions = models.CharField(max_length=200, blank=True,
                       help_text='e.g. Take after food, avoid alcohol')
    dispensed  = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.drug_name} {self.dosage} — {self.get_frequency_display()}"


class Vaccination(models.Model):
    """Vaccination / immunisation records for a student."""

    VACCINE_CHOICES = [
        ('hepatitis_b',  'Hepatitis B'),
        ('yellow_fever', 'Yellow Fever'),
        ('meningitis',   'Meningococcal (Meningitis)'),
        ('tetanus',      'Tetanus / Td'),
        ('covid19',      'COVID-19'),
        ('hpv',          'HPV'),
        ('typhoid',      'Typhoid'),
        ('malaria',      'Malaria (Prophylaxis)'),
        ('influenza',    'Influenza'),
        ('other',        'Other'),
    ]

    student         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='vaccinations', limit_choices_to={'role': 'student'}
    )
    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='vaccinations_given',
        limit_choices_to={'role': 'staff'}
    )
    vaccine         = models.CharField(max_length=30, choices=VACCINE_CHOICES)
    other_vaccine   = models.CharField(max_length=100, blank=True,
                          help_text='Specify if "Other" selected')
    batch_number    = models.CharField(max_length=50, blank=True)
    date_given      = models.DateField()
    next_due_date   = models.DateField(null=True, blank=True)
    notes           = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_given']

    def __str__(self):
        return f"{self.student.get_full_name()} — {self.get_vaccine_display()} on {self.date_given}"


class MedicalDocument(models.Model):
    """File attachments on a health record — lab results, X-rays, reports."""

    DOC_TYPE_CHOICES = [
        ('lab',      'Lab Result'),
        ('xray',     'X-Ray'),
        ('scan',     'Scan / Ultrasound'),
        ('referral', 'Referral Letter'),
        ('report',   'Medical Report'),
        ('other',    'Other'),
    ]

    record      = models.ForeignKey(HealthRecord, on_delete=models.CASCADE,
                      related_name='documents')
    doc_type    = models.CharField(max_length=15, choices=DOC_TYPE_CHOICES)
    title       = models.CharField(max_length=200)
    file        = models.FileField(upload_to='medical_docs/%Y/%m/')
    notes       = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='documents_uploaded'
    )

    def __str__(self):
        return f"{self.title} ({self.get_doc_type_display()}) — {self.record.student.get_full_name()}"
