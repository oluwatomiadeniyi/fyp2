from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import HealthRecord, Prescription, Vaccination, MedicalDocument
from .forms import (HealthRecordForm, PrescriptionFormSet,
                    VaccinationForm, MedicalDocumentForm, RecordFilterForm)


# ── Access helpers ─────────────────────────────────────────────────────────────

def _require_staff(request):
    if not (request.user.is_medical_staff or request.user.is_admin_user):
        messages.error(request, 'Only medical staff can perform this action.')
        return True
    return False


# ── Health record list ─────────────────────────────────────────────────────────

@login_required
def record_list(request):
    user = request.user
    form = RecordFilterForm(request.GET or None)

    if user.is_student:
        # Students only see their own non-confidential records
        qs = HealthRecord.objects.filter(
            student=user, is_confidential=False
        ).select_related('attending_staff', 'appointment')
    elif user.is_medical_staff:
        qs = HealthRecord.objects.filter(
            attending_staff=user
        ).select_related('student', 'appointment')
    else:
        qs = HealthRecord.objects.all().select_related('student', 'attending_staff')

    # Apply filters
    if form.is_valid():
        q = form.cleaned_data.get('q')
        vt = form.cleaned_data.get('visit_type')
        df = form.cleaned_data.get('date_from')
        dt = form.cleaned_data.get('date_to')
        if q and not user.is_student:
            qs = qs.filter(
                Q(student__first_name__icontains=q) |
                Q(student__last_name__icontains=q) |
                Q(student__matric_number__icontains=q) |
                Q(diagnosis__icontains=q)
            )
        if vt:
            qs = qs.filter(visit_type=vt)
        if df:
            qs = qs.filter(visit_date__gte=df)
        if dt:
            qs = qs.filter(visit_date__lte=dt)

    paginator = Paginator(qs, 15)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'health_records/list.html', {
        'page_obj': page,
        'form': form,
    })


# ── Create health record ───────────────────────────────────────────────────────

@login_required
def create_record(request):
    if _require_staff(request):
        return redirect('dashboard')

    # Pre-fill student/appointment from query params (coming from appointment detail)
    initial = {}
    appt_id = request.GET.get('appointment')
    if appt_id:
        from appointments.models import Appointment
        try:
            appt = Appointment.objects.get(pk=appt_id)
            initial['student']     = appt.student
            initial['appointment'] = appt
            initial['visit_date']  = appt.date
            initial['visit_type']  = appt.appointment_type
        except Appointment.DoesNotExist:
            pass

    form    = HealthRecordForm(request.POST or None,
                               initial=initial, staff_user=request.user)
    formset = PrescriptionFormSet(request.POST or None)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        record                 = form.save(commit=False)
        record.attending_staff = request.user
        record.save()

        formset.instance = record
        formset.save()

        # Mark the linked appointment as completed
        if record.appointment and record.appointment.status != 'completed':
            record.appointment.status = 'completed'
            record.appointment.save()

        messages.success(request,
            f'Health record created for {record.student.get_full_name()}.')
        return redirect('record_detail', pk=record.pk)

    return render(request, 'health_records/form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Health Record',
        'action': 'Create',
    })


# ── Record detail ──────────────────────────────────────────────────────────────

@login_required
def record_detail(request, pk):
    user = request.user

    if user.is_student:
        record = get_object_or_404(
            HealthRecord, pk=pk, student=user, is_confidential=False
        )
    elif user.is_medical_staff:
        record = get_object_or_404(HealthRecord, pk=pk)
    else:
        record = get_object_or_404(HealthRecord, pk=pk)

    medications = record.medications.all()
    documents   = record.documents.all()

    return render(request, 'health_records/detail.html', {
        'record': record,
        'medications': medications,
        'documents': documents,
    })


# ── Edit record ────────────────────────────────────────────────────────────────

@login_required
def edit_record(request, pk):
    if _require_staff(request):
        return redirect('dashboard')

    record  = get_object_or_404(HealthRecord, pk=pk)
    form    = HealthRecordForm(request.POST or None,
                               instance=record, staff_user=request.user)
    formset = PrescriptionFormSet(request.POST or None, instance=record)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Health record updated.')
        return redirect('record_detail', pk=record.pk)

    return render(request, 'health_records/form.html', {
        'form': form,
        'formset': formset,
        'record': record,
        'title': 'Edit Health Record',
        'action': 'Save Changes',
    })


# ── Delete record ──────────────────────────────────────────────────────────────

@login_required
def delete_record(request, pk):
    if _require_staff(request):
        return redirect('dashboard')
    record = get_object_or_404(HealthRecord, pk=pk)
    if request.method == 'POST':
        student_name = record.student.get_full_name()
        record.delete()
        messages.success(request,
            f'Health record for {student_name} deleted.')
        return redirect('record_list')
    return render(request, 'health_records/confirm_delete.html', {'record': record})


# ── Student's full medical history (staff view) ────────────────────────────────

@login_required
def student_history(request, student_pk):
    if _require_staff(request):
        return redirect('dashboard')

    from accounts.models import User
    student = get_object_or_404(User, pk=student_pk, role='student')
    records = HealthRecord.objects.filter(
        student=student
    ).select_related('attending_staff').order_by('-visit_date')
    vaccinations = Vaccination.objects.filter(student=student).order_by('-date_given')

    return render(request, 'health_records/student_history.html', {
        'student': student,
        'records': records,
        'vaccinations': vaccinations,
    })


# ── Upload document ────────────────────────────────────────────────────────────

@login_required
def upload_document(request, record_pk):
    if _require_staff(request):
        return redirect('dashboard')

    record = get_object_or_404(HealthRecord, pk=record_pk)
    form   = MedicalDocumentForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        doc             = form.save(commit=False)
        doc.record      = record
        doc.uploaded_by = request.user
        doc.save()
        messages.success(request, 'Document uploaded.')
        return redirect('record_detail', pk=record.pk)

    return render(request, 'health_records/upload_document.html', {
        'form': form, 'record': record,
    })


# ── Delete document ────────────────────────────────────────────────────────────

@login_required
def delete_document(request, pk):
    if _require_staff(request):
        return redirect('dashboard')
    doc = get_object_or_404(MedicalDocument, pk=pk)
    record_pk = doc.record.pk
    if request.method == 'POST':
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Document removed.')
    return redirect('record_detail', pk=record_pk)


# ── Vaccinations ───────────────────────────────────────────────────────────────

@login_required
def vaccination_list(request):
    if _require_staff(request):
        return redirect('dashboard')

    q  = request.GET.get('q', '').strip()
    qs = Vaccination.objects.select_related('student', 'administered_by').order_by('-date_given')
    if q:
        qs = qs.filter(
            Q(student__first_name__icontains=q) |
            Q(student__last_name__icontains=q) |
            Q(student__matric_number__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'health_records/vaccinations.html', {
        'page_obj': page, 'q': q,
    })


@login_required
def add_vaccination(request):
    if _require_staff(request):
        return redirect('dashboard')

    form = VaccinationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        vacc = form.save(commit=False)
        vacc.administered_by = request.user
        vacc.save()
        messages.success(request,
            f'Vaccination recorded for {vacc.student.get_full_name()}.')
        return redirect('vaccination_list')

    return render(request, 'health_records/vaccination_form.html', {
        'form': form, 'title': 'Record Vaccination',
    })
