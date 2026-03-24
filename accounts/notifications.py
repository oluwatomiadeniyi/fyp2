"""
Campus Health — Email Notification Utility
==========================================
All outgoing emails are sent from here.
In development:  EMAIL_BACKEND = console  → prints to terminal
In production:   EMAIL_BACKEND = smtp     → real emails via Gmail / SendGrid etc.

Usage (from any view or signal):
    from accounts.notifications import notify
    notify.appointment_booked(appointment)
    notify.appointment_confirmed(appointment)
    notify.welcome(user)
    ...
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def _send(subject, template, context, recipient_email, recipient_name=''):
    """
    Internal helper — renders an HTML email template and sends it.
    Falls back gracefully if sending fails (never crashes the view).
    """
    if not recipient_email:
        return

    try:
        html_body  = render_to_string(template, context)
        text_body  = strip_tags(html_body)

        msg = EmailMultiAlternatives(
            subject    = subject,
            body       = text_body,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [f'{recipient_name} <{recipient_email}>'.strip()
                          if recipient_name else recipient_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info(f'Email sent: "{subject}" → {recipient_email}')

    except Exception as e:
        # Never let a failed email crash the view
        logger.warning(f'Email failed: "{subject}" → {recipient_email} | {e}')


# ── Public notification functions ─────────────────────────────────────────────

def send_welcome(user):
    """Sent when a student registers."""
    _send(
        subject   = 'Welcome to Campus Health & Wellness',
        template  = 'notifications/welcome.html',
        context   = {'user': user},
        recipient_email = user.email,
        recipient_name  = user.get_full_name(),
    )


def send_appointment_booked(appointment):
    """Sent to student when they book an appointment."""
    _send(
        subject   = f'Appointment Booked — {appointment.get_appointment_type_display()}',
        template  = 'notifications/appointment_booked.html',
        context   = {'appointment': appointment},
        recipient_email = appointment.student.email,
        recipient_name  = appointment.student.get_full_name(),
    )


def send_appointment_confirmed(appointment):
    """Sent to student when admin assigns a doctor and confirms."""
    _send(
        subject   = 'Your Appointment Has Been Confirmed',
        template  = 'notifications/appointment_confirmed.html',
        context   = {'appointment': appointment},
        recipient_email = appointment.student.email,
        recipient_name  = appointment.student.get_full_name(),
    )


def send_appointment_cancelled(appointment):
    """Sent to student when appointment is cancelled."""
    _send(
        subject   = 'Appointment Cancelled',
        template  = 'notifications/appointment_cancelled.html',
        context   = {'appointment': appointment},
        recipient_email = appointment.student.email,
        recipient_name  = appointment.student.get_full_name(),
    )


def send_appointment_completed(appointment):
    """Sent to student after visit is marked completed — includes prescription if any."""
    _send(
        subject   = 'Visit Summary — Campus Health Centre',
        template  = 'notifications/appointment_completed.html',
        context   = {'appointment': appointment},
        recipient_email = appointment.student.email,
        recipient_name  = appointment.student.get_full_name(),
    )


def send_appointment_reminder(appointment):
    """Sent the day before a confirmed appointment."""
    _send(
        subject   = f'Reminder: Appointment Tomorrow at {appointment.time.strftime("%H:%M")}',
        template  = 'notifications/appointment_reminder.html',
        context   = {'appointment': appointment},
        recipient_email = appointment.student.email,
        recipient_name  = appointment.student.get_full_name(),
    )


def send_staff_account_created(staff_user, plain_password):
    """Sent to a newly created staff member with their login credentials."""
    _send(
        subject   = 'Your Campus Health Staff Account',
        template  = 'notifications/staff_account_created.html',
        context   = {
            'user':           staff_user,
            'plain_password': plain_password,
        },
        recipient_email = staff_user.email,
        recipient_name  = staff_user.get_full_name(),
    )


def send_doctor_assigned_to_staff(appointment):
    """Notify the assigned doctor that a new appointment is waiting."""
    if not appointment.staff:
        return
    _send(
        subject   = f'New Appointment Assigned — {appointment.date.strftime("%d %b %Y")}',
        template  = 'notifications/doctor_assigned.html',
        context   = {'appointment': appointment},
        recipient_email = appointment.staff.email,
        recipient_name  = appointment.staff.get_full_name(),
    )
