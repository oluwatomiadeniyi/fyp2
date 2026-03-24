from django import forms
from django.forms import inlineformset_factory
from .models import HealthRecord, Prescription, Vaccination, MedicalDocument

W  = 'form-control'
S  = 'form-select'
TA = lambda r=3: forms.Textarea(attrs={'class': W, 'rows': r})
FC = lambda ph='': forms.TextInput(attrs={'class': W, 'placeholder': ph})
NUM = lambda ph='': forms.NumberInput(attrs={'class': W, 'placeholder': ph})


class HealthRecordForm(forms.ModelForm):
    visit_date     = forms.DateField(
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )
    follow_up_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )

    class Meta:
        model  = HealthRecord
        fields = [
            'student', 'appointment', 'visit_date', 'visit_type', 'outcome',
            # vitals
            'temperature_c', 'blood_pressure', 'pulse_rate',
            'respiratory_rate', 'oxygen_saturation', 'weight_kg', 'height_cm',
            # clinical
            'chief_complaint', 'history', 'examination', 'diagnosis',
            'treatment', 'prescription', 'lab_results', 'notes',
            'follow_up_date', 'referred_to', 'is_confidential',
        ]
        widgets = {
            'student':            forms.Select(attrs={'class': S}),
            'appointment':        forms.Select(attrs={'class': S}),
            'visit_type':         forms.Select(attrs={'class': S}),
            'outcome':            forms.Select(attrs={'class': S}),
            'temperature_c':      NUM('e.g. 36.5'),
            'blood_pressure':     FC('e.g. 120/80'),
            'pulse_rate':         NUM('bpm'),
            'respiratory_rate':   NUM('breaths/min'),
            'oxygen_saturation':  NUM('e.g. 98.5'),
            'weight_kg':          NUM('kg'),
            'height_cm':          NUM('cm'),
            'chief_complaint':    TA(3),
            'history':            TA(3),
            'examination':        TA(4),
            'diagnosis':          TA(3),
            'treatment':          TA(3),
            'prescription':       TA(3),
            'lab_results':        TA(3),
            'notes':              TA(2),
            'referred_to':        FC('Hospital / specialist name'),
            'is_confidential':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # staff_user is passed so we can filter appointment choices
        self.staff_user = kwargs.pop('staff_user', None)
        super().__init__(*args, **kwargs)

        from accounts.models import User
        from appointments.models import Appointment

        self.fields['student'].queryset = User.objects.filter(
            role='student').order_by('last_name', 'first_name')
        self.fields['student'].empty_label = '— Select student —'

        # Only show confirmed/completed appointments (sensible choices)
        self.fields['appointment'].queryset = Appointment.objects.filter(
            status__in=['confirmed', 'completed']
        ).select_related('student').order_by('-date')
        self.fields['appointment'].required  = False
        self.fields['appointment'].empty_label = '— Link to appointment (optional) —'

    def clean(self):
        cleaned = super().clean()
        f_date  = cleaned.get('follow_up_date')
        v_date  = cleaned.get('visit_date')
        if f_date and v_date and f_date <= v_date:
            self.add_error('follow_up_date',
                'Follow-up date must be after the visit date.')
        return cleaned


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model  = Prescription
        fields = ['drug_name', 'dosage', 'frequency', 'route',
                  'duration', 'instructions', 'dispensed']
        widgets = {
            'drug_name':    FC('Drug / medicine name'),
            'dosage':       FC('e.g. 500mg'),
            'frequency':    forms.Select(attrs={'class': S}),
            'route':        forms.Select(attrs={'class': S}),
            'duration':     FC('e.g. 5 days'),
            'instructions': FC('e.g. Take after food'),
            'dispensed':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Inline formset: multiple prescriptions on one record form
PrescriptionFormSet = inlineformset_factory(
    HealthRecord, Prescription,
    form=PrescriptionForm,
    extra=2, can_delete=True,
    fields=['drug_name', 'dosage', 'frequency', 'route',
            'duration', 'instructions', 'dispensed']
)


class VaccinationForm(forms.ModelForm):
    date_given    = forms.DateField(
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )
    next_due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )

    class Meta:
        model  = Vaccination
        fields = ['student', 'vaccine', 'other_vaccine', 'batch_number',
                  'date_given', 'next_due_date', 'notes']
        widgets = {
            'student':       forms.Select(attrs={'class': S}),
            'vaccine':       forms.Select(attrs={'class': S}),
            'other_vaccine': FC('Specify vaccine name'),
            'batch_number':  FC('Batch / lot number'),
            'notes':         TA(2),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        self.fields['student'].queryset = User.objects.filter(
            role='student').order_by('last_name', 'first_name')
        self.fields['student'].empty_label = '— Select student —'


class MedicalDocumentForm(forms.ModelForm):
    class Meta:
        model  = MedicalDocument
        fields = ['doc_type', 'title', 'file', 'notes']
        widgets = {
            'doc_type': forms.Select(attrs={'class': S}),
            'title':    FC('Document title / description'),
            'file':     forms.FileInput(attrs={'class': 'form-control'}),
            'notes':    TA(2),
        }


class RecordFilterForm(forms.Form):
    """Search / filter form for the record list."""
    q          = forms.CharField(required=False,
                     widget=FC('Search by name or matric number'))
    visit_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All types')] + list(HealthRecord.VISIT_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': S})
    )
    date_from  = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )
    date_to    = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )
