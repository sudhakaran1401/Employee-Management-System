from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from employees.models import Employee


class Command(BaseCommand):
    help = "Assign roles to users based on employee department"

    def handle(self, *args, **kwargs):

        admin_group, _ = Group.objects.get_or_create(name="ADMIN")
        hr_group, _ = Group.objects.get_or_create(name="HR")
        employee_group, _ = Group.objects.get_or_create(name="EMPLOYEE")

        employees = Employee.objects.all()

        if not employees.exists():
            self.stdout.write(self.style.WARNING("No employees found"))
            return

        for emp in employees:

            user = User.objects.filter(email=emp.email).first()

            if not user:
                self.stdout.write(
                    self.style.WARNING(f" No user found for {emp.name} ({emp.email})")
                )
                continue

            user.groups.clear()

            dept = emp.department.strip().upper() if emp.department else ""

            if dept == "HR":
                user.groups.add(hr_group)
                user.is_staff = True

            elif dept == "ADMIN":
                user.groups.add(admin_group)
                user.is_staff = True
                user.is_superuser = True   # optional

            else:
                user.groups.add(employee_group)
                user.is_staff = False

            user.save()

            self.stdout.write(
                self.style.SUCCESS(f"Role assigned to {emp.name} ({dept})")
            )

        self.stdout.write(self.style.SUCCESS(" All roles assigned successfully!"))