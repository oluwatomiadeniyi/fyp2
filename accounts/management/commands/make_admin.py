"""
Usage:
    python manage.py make_admin <username>

Promotes an existing user with role='admin' to also have
is_staff=True and is_superuser=True so that Django's internals
work correctly, while the app still treats them as an app-admin
(not a Django admin panel user — that is blocked separately).
"""
from django.core.management.base import BaseCommand, CommandError
from accounts.models import User


class Command(BaseCommand):
    help = 'Promote a user with role=admin to also be a superuser'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str,
                            help='Username of the admin user to promote')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist.')

        if user.role != 'admin':
            raise CommandError(
                f'User "{username}" has role "{user.role}", not "admin". '
                f'Update their role to "admin" first.'
            )

        user.is_staff     = True
        user.is_superuser = True
        user.is_active    = True
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f'✓ "{username}" is now a superuser with role=admin.\n'
            f'  They can log in at /login/ and access all admin features.\n'
            f'  They CANNOT access the Django /admin/ panel '
            f'(it checks role and blocks admin/staff/student).'
        ))
