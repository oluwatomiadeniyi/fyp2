from django.contrib import admin
from .models import HealthRecord, Prescription, Vaccination, MedicalDocument


class PrescriptionInline(admin.TabularInline):
    model  = Prescription
    extra  = 1
    fields = ['drug_name', 'dosage', 'frequency', 'route', 'duration', 'dispensed']


class MedicalDocumentInline(admin.TabularInline):
    model  = MedicalDocument
    extra  = 0
    fields = ['doc_type', 'title', 'file', 'uploaded_by']
    readonly_fields = ['uploaded_by']


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display   = ['student', 'visit_date', 'visit_type', 'diagnosis',
                      'outcome', 'attending_staff', 'is_confidential']
    list_filter    = ['visit_type', 'outcome', 'is_confidential', 'visit_date']
    search_fields  = ['student__first_name', 'student__last_name',
                      'student__matric_number', 'diagnosis', 'chief_complaint']
    date_hierarchy = 'visit_date'
    ordering       = ['-visit_date']
    inlines        = [PrescriptionInline, MedicalDocumentInline]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Participants', {
            'fields': ['student', 'attending_staff', 'appointment']
        }),
        ('Visit', {
            'fields': ['visit_date', 'visit_type', 'outcome', 'is_confidential']
        }),
        ('Vitals', {
            'fields': ['temperature_c', 'blood_pressure', 'pulse_rate',
                       'respiratory_rate', 'oxygen_saturation',
                       'weight_kg', 'height_cm'],
            'classes': ['collapse'],
        }),
        ('Clinical', {
            'fields': ['chief_complaint', 'history', 'examination',
                       'diagnosis', 'treatment', 'prescription',
                       'lab_results', 'notes']
        }),
        ('Outcome', {
            'fields': ['follow_up_date', 'referred_to']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display  = ['student', 'vaccine', 'date_given', 'next_due_date',
                     'administered_by', 'batch_number']
    list_filter   = ['vaccine', 'date_given']
    search_fields = ['student__first_name', 'student__last_name',
                     'student__matric_number', 'batch_number']
    date_hierarchy = 'date_given'


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'doc_type', 'record', 'uploaded_by', 'uploaded_at']
    list_filter  = ['doc_type']
