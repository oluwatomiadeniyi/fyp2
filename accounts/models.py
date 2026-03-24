from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):

    # ── Roles ──────────────────────────────────────────────────────────
    ROLE_STUDENT = 'student'
    ROLE_STAFF   = 'staff'
    ROLE_ADMIN   = 'admin'
    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_STAFF,   'Medical Staff'),
        (ROLE_ADMIN,   'Admin'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other / Prefer not to say'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('unknown', 'Unknown'),
    ]

    LEVEL_CHOICES = [
        ('100', '100 Level'),
        ('200', '200 Level'),
        ('300', '300 Level'),
        ('400', '400 Level'),
        ('500', '500 Level'),
        ('600', '600 Level'),
        ('PGD', 'PGD'),
        ('MSC', 'M.Sc'),
        ('PHD', 'Ph.D'),
    ]

    STATE_CHOICES = [
        ('Abia', 'Abia'), ('Adamawa', 'Adamawa'), ('Akwa Ibom', 'Akwa Ibom'),
        ('Anambra', 'Anambra'), ('Bauchi', 'Bauchi'), ('Bayelsa', 'Bayelsa'),
        ('Benue', 'Benue'), ('Borno', 'Borno'), ('Cross River', 'Cross River'),
        ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'), ('Edo', 'Edo'),
        ('Ekiti', 'Ekiti'), ('Enugu', 'Enugu'), ('FCT', 'FCT - Abuja'),
        ('Gombe', 'Gombe'), ('Imo', 'Imo'), ('Jigawa', 'Jigawa'),
        ('Kaduna', 'Kaduna'), ('Kano', 'Kano'), ('Katsina', 'Katsina'),
        ('Kebbi', 'Kebbi'), ('Kogi', 'Kogi'), ('Kwara', 'Kwara'),
        ('Lagos', 'Lagos'), ('Nasarawa', 'Nasarawa'), ('Niger', 'Niger'),
        ('Ogun', 'Ogun'), ('Ondo', 'Ondo'), ('Osun', 'Osun'),
        ('Oyo', 'Oyo'), ('Plateau', 'Plateau'), ('Rivers', 'Rivers'),
        ('Sokoto', 'Sokoto'), ('Taraba', 'Taraba'), ('Yobe', 'Yobe'),
        ('Zamfara', 'Zamfara'),
    ]

    GENOTYPE_CHOICES = [
        ('AA', 'AA'), ('AS', 'AS'), ('AC', 'AC'),
        ('SS', 'SS'), ('SC', 'SC'), ('CC', 'CC'),
        ('unknown', 'Unknown'),
    ]

    # ── Core fields (all users) ─────────────────────────────────────────
    role          = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone         = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender        = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address       = models.TextField(blank=True)

    # ── Student-specific fields ─────────────────────────────────────────
    matric_number      = models.CharField(
        max_length=20, blank=True, null=True, unique=True,
        verbose_name='Matric Number',
        help_text='Your official university matriculation number'
    )
    department         = models.CharField(max_length=150, blank=True, verbose_name='Department')
    faculty            = models.CharField(max_length=150, blank=True, verbose_name='Faculty / College')
    level              = models.CharField(max_length=5, choices=LEVEL_CHOICES, blank=True, verbose_name='Level')
    hall_of_residence  = models.CharField(max_length=150, blank=True, verbose_name='Hall of Residence',
                             help_text='Leave blank if you live off-campus')
    state_of_origin    = models.CharField(max_length=30, choices=STATE_CHOICES, blank=True, verbose_name='State of Origin')
    nationality        = models.CharField(max_length=60, blank=True, default='Nigerian')

    # ── Medical information ─────────────────────────────────────────────
    blood_group        = models.CharField(max_length=8, choices=BLOOD_GROUP_CHOICES,
                             blank=True, default='unknown', verbose_name='Blood Group')
    genotype           = models.CharField(max_length=8, choices=GENOTYPE_CHOICES,
                             blank=True, default='unknown', verbose_name='Genotype')
    height_cm          = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True,
                             verbose_name='Height (cm)')
    weight_kg          = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True,
                             verbose_name='Weight (kg)')
    allergies          = models.TextField(blank=True,
                             verbose_name='Known Allergies',
                             help_text='e.g. Penicillin, peanuts, latex — write "None" if none')
    chronic_conditions = models.TextField(blank=True,
                             verbose_name='Chronic Conditions / Disabilities',
                             help_text='e.g. Asthma, diabetes, epilepsy — write "None" if none')
    current_medications = models.TextField(blank=True,
                             verbose_name='Current Medications',
                             help_text='List any medication you take regularly')
    past_surgeries     = models.TextField(blank=True,
                             verbose_name='Past Surgeries / Hospitalisations',
                             help_text='Include year and reason if possible')
    disability         = models.CharField(max_length=200, blank=True,
                             verbose_name='Disability / Special Needs',
                             help_text='Any physical or learning disability we should know about')
    immunization_up_to_date = models.BooleanField(default=False,
                             verbose_name='Immunisations up to date?')
    hiv_status         = models.CharField(max_length=20, blank=True,
                             choices=[('positive','Positive'), ('negative','Negative'),
                                      ('unknown','Unknown / Not tested')],
                             verbose_name='HIV Status (confidential)')

    # ── Medical insurance ───────────────────────────────────────────────
    has_nhis           = models.BooleanField(default=False, verbose_name='Has NHIS card?')
    nhis_number        = models.CharField(max_length=30, blank=True, verbose_name='NHIS Number')
    insurance_provider = models.CharField(max_length=100, blank=True, verbose_name='Other Insurance Provider')

    # ── Staff-specific fields ───────────────────────────────────────────
    staff_id       = models.CharField(max_length=20, blank=True, null=True, verbose_name='Staff ID')
    specialization = models.CharField(max_length=150, blank=True, verbose_name='Specialization / Role')
    qualification  = models.CharField(max_length=250, blank=True, verbose_name='Qualifications')
    is_available   = models.BooleanField(default=True, verbose_name='Currently available for appointments?')

    # ── Notification preferences ────────────────────────────────────────
    email_notifications = models.BooleanField(default=True)
    sms_notifications   = models.BooleanField(default=False)

    # ── Timestamps ──────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # ── Convenience properties ──────────────────────────────────────────
    @property
    def is_student(self):       return self.role == self.ROLE_STUDENT
    @property
    def is_medical_staff(self): return self.role == self.ROLE_STAFF
    @property
    def is_admin_user(self):    return self.role == self.ROLE_ADMIN

    def get_age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def get_bmi(self):
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            h = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (h * h), 1)
        return None

    def bmi_category(self):
        bmi = self.get_bmi()
        if bmi is None:         return ''
        if bmi < 18.5:          return 'Underweight'
        if bmi < 25:            return 'Normal'
        if bmi < 30:            return 'Overweight'
        return 'Obese'

    def profile_complete(self):
        """Returns True if the student has filled in the most important fields."""
        required = [self.first_name, self.last_name, self.phone,
                    self.date_of_birth, self.gender, self.matric_number,
                    self.department, self.level, self.blood_group]
        return all(required)


class EmergencyContact(models.Model):
    RELATIONSHIP_CHOICES = [
        ('parent',   'Parent'),
        ('sibling',  'Sibling'),
        ('spouse',   'Spouse / Partner'),
        ('guardian', 'Guardian'),
        ('relative', 'Other Relative'),
        ('friend',   'Friend'),
    ]

    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts')
    name         = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    phone        = models.CharField(max_length=20)
    alt_phone    = models.CharField(max_length=20, blank=True, verbose_name='Alternative Phone')
    email        = models.EmailField(blank=True)
    address      = models.TextField(blank=True)
    is_primary   = models.BooleanField(default=False, verbose_name='Primary contact?')

    class Meta:
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.relationship}) — {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            EmergencyContact.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
