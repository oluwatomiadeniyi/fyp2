"""
Sends appointment reminder emails to all students with confirmed
appointments scheduled for tomorrow.

Run manually:
    python manage.py send_reminders

Schedule via Windows Task Scheduler or cron to run daily at e.g. 8am:
    # cron (Linux/Mac):
    0 8 * * * /path/to/env/bin/python /path/to/manage.py send_reminders

    # Windows Task Scheduler:
    Program: C:\\path\\to\\env\\Scripts\\python.exe
    Arguments: C:\\path\\to\\manage.py send_reminders
"""
import datetime
from django.core.management.base import BaseCommand
from appointments.models import Appointment
from accounts import notifications as notify


class Command(BaseCommand):
    help = 'Send reminder emails for appointments scheduled tomorrow'

    def handle(self, *args, **options):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

        appointments = Appointment.objects.filter(
            date=tomorrow,
            status=Appointment.STATUS_CONFIRMED,
            reminder_sent=False,
        ).select_related('student', 'staff')

        if not appointments.exists():
            self.stdout.write('No reminders to send today.')
            return

        sent = 0
        failed = 0
        for appt in appointments:
            try:
                notify.send_appointment_reminder(appt)
                appt.reminder_sent = True
                appt.save(update_fields=['reminder_sent'])
                sent += 1
                self.stdout.write(
                    f'  ✓ Reminder sent → {appt.student.get_full_name()} '
                    f'({appt.student.email}) for {appt.date}'
                )
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  ✗ Failed → {appt.student.get_full_name()} | {e}'
                    )
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone — {sent} reminder(s) sent, {failed} failed.'
        ))
