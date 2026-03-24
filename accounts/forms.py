from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import User, EmergencyContact


# ── helpers ──────────────────────────────────────────────────────────────────
WIDGET_CLASS = 'form-control'
SELECT_CLASS = 'form-select'
CHECK_CLASS  = 'form-check-input'

def fc(placeholder='', extra_class=WIDGET_CLASS, **kwargs):
    """Shorthand: returns a TextInput with Bootstrap class."""
    return forms.TextInput(attrs={'class': extra_class, 'placeholder': placeholder, **kwargs})

def ta(placeholder='', rows=3):
    return forms.Textarea(attrs={'class': WIDGET_CLASS, 'placeholder': placeholder, 'rows': rows})

def sel():
    return forms.Select(attrs={'class': SELECT_CLASS})

def date_input():
    return forms.DateInput(attrs={'class': WIDGET_CLASS, 'type': 'date'})


# ── Student Registration ──────────────────────────────────────────────────────
class StudentRegistrationForm(UserCreationForm):
    # Personal
    first_name    = forms.CharField(max_length=50, widget=fc('First name'))
    last_name     = forms.CharField(max_length=50, widget=fc('Last name'))
    email         = forms.EmailField(widget=forms.EmailInput(attrs={'class': WIDGET_CLASS, 'placeholder': 'Email address'}))
    phone         = forms.CharField(max_length=20, widget=fc('e.g. 08012345678'))
    date_of_birth = forms.DateField(widget=date_input(), label='Date of Birth')
    gender        = forms.ChoiceField(choices=[('','-- Select --')] + list(User.GENDER_CHOICES), widget=sel())

    # Academic
    matric_number     = forms.CharField(max_length=20, label='Matric Number', widget=fc('e.g. CSC/2021/001'))
    department        = forms.CharField(max_length=150, widget=fc('e.g. Computer Science'))
    faculty           = forms.CharField(max_length=150, widget=fc('e.g. Faculty of Science'), label='Faculty / College')
    level             = forms.ChoiceField(choices=[('','-- Select --')] + list(User.LEVEL_CHOICES), widget=sel())
    hall_of_residence = forms.CharField(max_length=150, required=False,
                            widget=fc('Leave blank if off-campus'), label='Hall of Residence')
    state_of_origin   = forms.ChoiceField(choices=[('','-- Select --')] + list(User.STATE_CHOICES), widget=sel())

    # Password fields — keep Bootstrap class
    password1 = forms.CharField(label='Password',
                    widget=forms.PasswordInput(attrs={'class': WIDGET_CLASS, 'placeholder': 'Create a password'}))
    password2 = forms.CharField(label='Confirm Password',
                    widget=forms.PasswordInput(attrs={'class': WIDGET_CLASS, 'placeholder': 'Repeat the password'}))

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone',
                  'date_of_birth', 'gender', 'matric_number', 'department',
                  'faculty', 'level', 'hall_of_residence', 'state_of_origin',
                  'password1', 'password2']
        widgets = {'username': fc('Choose a username')}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_STUDENT
        if commit:
            user.save()
        return user


# ── Staff Registration ────────────────────────────────────────────────────────
class StaffRegistrationForm(UserCreationForm):
    first_name     = forms.CharField(max_length=50, widget=fc('First name'))
    last_name      = forms.CharField(max_length=50, widget=fc('Last name'))
    email          = forms.EmailField(widget=forms.EmailInput(attrs={'class': WIDGET_CLASS}))
    phone          = forms.CharField(max_length=20, widget=fc('Phone number'))
    staff_id       = forms.CharField(max_length=20, label='Staff ID', widget=fc('e.g. MED/STF/001'))
    specialization = forms.CharField(max_length=150, widget=fc('e.g. General Practitioner, Nurse'))
    qualification  = forms.CharField(max_length=250, widget=fc('e.g. MBBS, RN, B.Pharm'))

    password1 = forms.CharField(label='Password',
                    widget=forms.PasswordInput(attrs={'class': WIDGET_CLASS}))
    password2 = forms.CharField(label='Confirm Password',
                    widget=forms.PasswordInput(attrs={'class': WIDGET_CLASS}))

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone',
                  'staff_id', 'specialization', 'qualification', 'password1', 'password2']
        widgets = {'username': fc('Choose a username')}

    def save(self, commit=True, is_active=True):
        user = super().save(commit=False)
        user.role      = User.ROLE_STAFF
        user.is_active = is_active
        if commit:
            user.save()
        return user


# ── Login ─────────────────────────────────────────────────────────────────────
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = fc('Username or matric number')
        self.fields['password'].widget = forms.PasswordInput(
            attrs={'class': WIDGET_CLASS, 'placeholder': 'Password'})


# ── Profile — Personal tab ────────────────────────────────────────────────────
class PersonalInfoForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=date_input(), required=False)

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email', 'phone',
                  'date_of_birth', 'gender', 'nationality',
                  'state_of_origin', 'address', 'profile_photo']
        widgets = {
            'first_name':    fc(),
            'last_name':     fc(),
            'email':         forms.EmailInput(attrs={'class': WIDGET_CLASS}),
            'phone':         fc(),
            'gender':        sel(),
            'state_of_origin': sel(),
            'nationality':   fc(),
            'address':       ta('Your home / current address', rows=2),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ── Profile — Academic tab ────────────────────────────────────────────────────
class AcademicInfoForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['matric_number', 'department', 'faculty', 'level',
                  'hall_of_residence']
        widgets = {
            'matric_number':     fc(),
            'department':        fc(),
            'faculty':           fc(),
            'level':             sel(),
            'hall_of_residence': fc(),
        }


# ── Profile — Medical tab ─────────────────────────────────────────────────────
class MedicalInfoForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['blood_group', 'genotype', 'height_cm', 'weight_kg',
                  'allergies', 'chronic_conditions', 'current_medications',
                  'past_surgeries', 'disability', 'immunization_up_to_date',
                  'hiv_status', 'has_nhis', 'nhis_number', 'insurance_provider']
        widgets = {
            'blood_group':      sel(),
            'genotype':         sel(),
            'height_cm':        forms.NumberInput(attrs={'class': WIDGET_CLASS, 'placeholder': 'e.g. 175'}),
            'weight_kg':        forms.NumberInput(attrs={'class': WIDGET_CLASS, 'placeholder': 'e.g. 70'}),
            'allergies':        ta('List all known allergies, or write "None"'),
            'chronic_conditions': ta('e.g. Asthma, Diabetes — write "None" if none'),
            'current_medications': ta('Medication name, dosage, frequency'),
            'past_surgeries':   ta('Year and reason if known'),
            'disability':       fc('Any disability or special need'),
            'hiv_status':       sel(),
            'nhis_number':      fc('Your NHIS number'),
            'insurance_provider': fc('e.g. AIICO, Leadway'),
        }


# ── Profile — Notification preferences ───────────────────────────────────────
class NotificationPrefsForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['email_notifications', 'sms_notifications']
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': CHECK_CLASS}),
            'sms_notifications':   forms.CheckboxInput(attrs={'class': CHECK_CLASS}),
        }


# ── Emergency Contact ─────────────────────────────────────────────────────────
class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model  = EmergencyContact
        fields = ['name', 'relationship', 'phone', 'alt_phone', 'email', 'address', 'is_primary']
        widgets = {
            'name':         fc('Full name'),
            'relationship': sel(),
            'phone':        fc('Primary phone number'),
            'alt_phone':    fc('Alternative phone (optional)'),
            'email':        forms.EmailInput(attrs={'class': WIDGET_CLASS, 'placeholder': 'Email (optional)'}),
            'address':      ta('Address (optional)', rows=2),
            'is_primary':   forms.CheckboxInput(attrs={'class': CHECK_CLASS}),
        }


# ── Password Change ───────────────────────────────────────────────────────────
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = WIDGET_CLASS
