def sidebar_context(request):
    """
    Injects variables needed by base.html into every template context
    automatically — no view needs to pass these manually.
    """
    context = {}

    if not request.user.is_authenticated:
        return context

    if request.user.is_admin_user:
        from accounts.models import User
        from appointments.models import Appointment

        context['pending_staff_count'] = User.objects.filter(
            role='staff', is_active=False
        ).count()

        context['pending_appt_count'] = Appointment.objects.filter(
            status='pending'
        ).count()

    elif request.user.is_medical_staff:
        from appointments.models import Appointment
        import datetime

        context['today_appt_count'] = Appointment.objects.filter(
            staff=request.user,
            date=datetime.date.today(),
            status__in=['pending', 'confirmed']
        ).count()

    return context
