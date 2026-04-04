from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from employees.models import Employee

class Command(BaseCommand):
    help = "Assign roles based on department"

    def handle(self, *args, **kwargs):

        # Get groups
        admin_group = Group.objects.get(name="ADMIN")
        hr_group = Group.objects.get(name="HR")
        employee_group = Group.objects.get(name="EMPLOYEE")

        employees = Employee.objects.all()

        for emp in employees:
            user = emp.user  # assuming linked

            if not user:
                self.stdout.write(self.style.WARNING(f"No user for {emp.name}"))
                continue

            # Clear old groups
            user.groups.clear()

            # Assign role based on department
            if emp.department == "HR":
                user.groups.add(hr_group)
                user.is_staff = True

            elif emp.department == "ADMIN":
                user.groups.add(admin_group)
                user.is_staff = True

            else:
                user.groups.add(employee_group)
                user.is_staff = False

            user.save()

            self.stdout.write(self.style.SUCCESS(f"Assigned role to {emp.name}"))

        self.stdout.write(self.style.SUCCESS("All roles assigned successfully!"))