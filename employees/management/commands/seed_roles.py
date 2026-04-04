from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

ROLE_NAMES = ["ADMIN", "HR", "EMPLOYEE"]

class Command(BaseCommand):
    help = "Create default role groups (ADMIN, HR, EMPLOYEE)."

    def handle(self, *args, **options):
        created = 0
        for name in ROLE_NAMES:
            _, was_created = Group.objects.get_or_create(name=name)
            created += 1 if was_created else 0

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created} groups (existing groups kept)."
        ))
