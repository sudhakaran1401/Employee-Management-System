from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Employee, EmployeeProfile

@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance: User, created: bool, **kwargs):
    if not created:
        return

    # Try linking by email (best practice)
    if instance.email:
        emp = Employee.objects.filter(email=instance.email).first()
        if emp and not hasattr(instance, "employee_profile"):
            EmployeeProfile.objects.create(user=instance, employee=emp)
