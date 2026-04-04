from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from employees.models import Employee, EmployeeProfile

import openpyxl

class Command(BaseCommand):
    help = 'Import users from Excel and link to employees'

    def handle(self, *args, **kwargs):
        file_path = 'employee_credentials.xlsx'  # place file in project root

        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active

        for row in sheet.iter_rows(min_row=2, values_only=True):
            name, username, password = row

            # Find employee by name
            emp = Employee.objects.filter(name=name).first()

            if not emp:
                self.stdout.write(self.style.WARNING(f"Employee not found: {name}"))
                continue

            # Create user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": emp.email
                }
            )

            user.set_password(password)
            user.save()

            # Link profile
            EmployeeProfile.objects.get_or_create(
                user=user,
                employee=emp
            )

            self.stdout.write(self.style.SUCCESS(f"Linked: {name}"))

        self.stdout.write(self.style.SUCCESS("Import completed!"))