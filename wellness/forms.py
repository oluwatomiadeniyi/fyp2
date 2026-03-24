from django import forms
from .models import WellnessLog, MentalHealthAssessment, WellnessGoal

W  = 'form-control'
S  = 'form-select'
TA = lambda r=3: forms.Textarea(attrs={'class': W, 'rows': r})
CH = lambda: forms.CheckboxInput(attrs={'class': 'form-check-input'})
NUM = lambda mn=0, mx=20: forms.NumberInput(attrs={'class': W, 'min': mn, 'max': mx})


class WellnessLogForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )

    # Explicitly declare integer choice fields so Django doesn't add
    # an empty "-------" option, which causes silent validation failures.
    mood = forms.ChoiceField(
        choices=WellnessLog.MOOD_CHOICES,
        widget=forms.Select(attrs={'class': S}),
    )
    stress_level = forms.ChoiceField(
        choices=WellnessLog.STRESS_CHOICES,
        widget=forms.Select(attrs={'class': S}),
    )

    class Meta:
        model  = WellnessLog
        fields = [
            'date', 'mood', 'stress_level', 'sleep_hours',
            'physical_activity', 'appetite',
            'has_headache', 'has_fever', 'has_fatigue',
            'has_nausea', 'has_anxiety', 'has_pain',
            'other_symptoms', 'notes', 'water_glasses', 'meals_today',
        ]
        widgets = {
            'sleep_hours':       forms.Select(attrs={'class': S}),
            'physical_activity': forms.Select(attrs={'class': S}),
            'appetite':          forms.Select(attrs={'class': S}),
            'has_headache':      CH(),
            'has_fever':         CH(),
            'has_fatigue':       CH(),
            'has_nausea':        CH(),
            'has_anxiety':       CH(),
            'has_pain':          CH(),
            'other_symptoms':    forms.TextInput(attrs={'class': W,
                                     'placeholder': 'Any other symptoms today'}),
            'notes':             TA(3),
            'water_glasses':     NUM(0, 20),
            'meals_today':       NUM(0, 10),
        }

    def clean_mood(self):
        # ChoiceField returns a string; model expects an integer
        return int(self.cleaned_data['mood'])

    def clean_stress_level(self):
        return int(self.cleaned_data['stress_level'])

    def clean_date(self):
        import datetime
        d = self.cleaned_data['date']
        if d > datetime.date.today():
            raise forms.ValidationError("You can't log a future date.")
        return d


class MentalHealthForm(forms.ModelForm):
    """PHQ-9 self-assessment form."""

    class Meta:
        model  = MentalHealthAssessment
        fields = ['q1_interest', 'q2_depressed', 'q3_sleep', 'q4_tired',
                  'q5_appetite', 'q6_failure', 'q7_focus', 'q8_movement',
                  'q9_selfharm', 'notes']
        widgets = {
            'q1_interest':  forms.RadioSelect(),
            'q2_depressed': forms.RadioSelect(),
            'q3_sleep':     forms.RadioSelect(),
            'q4_tired':     forms.RadioSelect(),
            'q5_appetite':  forms.RadioSelect(),
            'q6_failure':   forms.RadioSelect(),
            'q7_focus':     forms.RadioSelect(),
            'q8_movement':  forms.RadioSelect(),
            'q9_selfharm':  forms.RadioSelect(),
            'notes':        TA(3),
        }


class WellnessGoalForm(forms.ModelForm):
    target_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': W, 'type': 'date'})
    )

    class Meta:
        model  = WellnessGoal
        fields = ['category', 'title', 'description', 'target_date', 'is_achieved']
        widgets = {
            'category':    forms.Select(attrs={'class': S}),
            'title':       forms.TextInput(attrs={'class': W,
                               'placeholder': 'e.g. Sleep 8 hours every night'}),
            'description': TA(2),
            'is_achieved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }