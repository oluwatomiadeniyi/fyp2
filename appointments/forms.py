from django import forms
from .models import Appointment, AppointmentFeedback, StaffSchedule

W  = 'form-control'
S  = 'form-select'
TA = lambda r=3: forms.Textarea(attrs={'class': W, 'rows': r})
FC = lambda ph='': forms.TextInput(attrs={'class': W, 'placeholder': ph})


class AppointmentBookingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'}),
        help_text='Appointments are Monday – Friday only.'
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': W, 'type': 'time'}),
        help_text='Clinic hours: 08:00 – 17:00'
    )

    class Meta:
        model  = Appointment
        fields = ['appointment_type', 'priority', 'staff', 'date', 'time', 'reason', 'symptoms']
        widgets = {
            'appointment_type': forms.Select(attrs={'class': S}),
            'priority':         forms.Select(attrs={'class': S}),
            'staff':            forms.Select(attrs={'class': S}),
            'reason':           TA(4),
            'symptoms':         TA(3),
        }
        labels = {
            'staff': 'Preferred Doctor / Nurse (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        self.fields['staff'].queryset  = User.objects.filter(
            role='staff', is_active=True, is_available=True
        ).order_by('last_name')
        self.fields['staff'].required  = False
        self.fields['staff'].empty_label = '— Any available staff —'
        self.fields['symptoms'].required = False

    def clean_date(self):
        import datetime
        d = self.cleaned_data['date']
        if d < datetime.date.today():
            raise forms.ValidationError('Please choose a future date.')
        if d.weekday() >= 5:
            raise forms.ValidationError('Clinic is open Monday–Friday only.')
        return d

    def clean_time(self):
        import datetime
        t = self.cleaned_data['time']
        open_time  = datetime.time(8, 0)
        close_time = datetime.time(17, 0)
        if not (open_time <= t <= close_time):
            raise forms.ValidationError('Please choose a time between 08:00 and 17:00.')
        return t


class AppointmentStatusForm(forms.ModelForm):
    """Staff use this to update status, add notes, diagnosis, prescription."""
    follow_up_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'}),
        help_text='Leave blank if no follow-up needed.'
    )

    class Meta:
        model  = Appointment
        fields = ['status', 'notes', 'diagnosis', 'prescription',
                  'follow_up_date', 'referred_to', 'cancellation_reason']
        widgets = {
            'status':              forms.Select(attrs={'class': S}),
            'notes':               TA(4),
            'diagnosis':           TA(3),
            'prescription':        TA(3),
            'referred_to':         FC('Hospital or specialist name, if referred'),
            'cancellation_reason': TA(2),
        }


class RescheduleForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': W, 'type': 'time'})
    )

    class Meta:
        model  = Appointment
        fields = ['date', 'time']

    def clean_date(self):
        import datetime
        d = self.cleaned_data['date']
        if d < datetime.date.today():
            raise forms.ValidationError('Please choose a future date.')
        if d.weekday() >= 5:
            raise forms.ValidationError('Clinic is open Monday–Friday only.')
        return d


class CancelForm(forms.Form):
    reason = forms.CharField(
        required=False,
        label='Reason for cancellation (optional)',
        widget=TA(2)
    )


class FeedbackForm(forms.ModelForm):
    RATING_CHOICES = [(i, '★' * i) for i in range(1, 6)]
    rating = forms.ChoiceField(choices=RATING_CHOICES,
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))

    class Meta:
        model  = AppointmentFeedback
        fields = ['rating', 'comment', 'would_recommend']
        widgets = {
            'comment':          TA(3),
            'would_recommend':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StaffScheduleForm(forms.ModelForm):
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'class': W, 'type': 'time'}))
    end_time   = forms.TimeField(widget=forms.TimeInput(attrs={'class': W, 'type': 'time'}))

    class Meta:
        model  = StaffSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': S}),
        }

    def clean(self):
        cleaned = super().clean()
        start   = cleaned.get('start_time')
        end     = cleaned.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError('End time must be after start time.')
        return cleaned
