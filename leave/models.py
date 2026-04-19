from django.db import models
from django.core.exceptions import ValidationError
from employees.models import Employee


class LeaveRequest(models.Model):

    LEAVE_TYPES = [
        ("SICK", "Sick Leave"),
        ("CASUAL", "Casual Leave"),
        ("ANNUAL", "Annual Leave"),
    ]

    STATUS = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests"
    )

    leave_type = models.CharField(
        max_length=10,
        choices=LEAVE_TYPES,
        default="CASUAL"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    reason = models.TextField(blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS,
        default="PENDING"
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-applied_at"]

    # ⚠️ safe validation (does NOT break old data)
    def clean(self):
        if not self.start_date or not self.end_date:
            return

        if self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date")

        # 🔥 IMPORTANT FIX
        if not self.employee_id:
            return

        overlap = LeaveRequest.objects.filter(
            employee=self.employee,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(id=self.id)

        if overlap.exists():
            raise ValidationError("Leave overlaps with existing request")
        
    @property
    def total_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type} - {self.status}"


class LeaveBalance(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)

    sick_leave = models.IntegerField(default=15)
    casual_leave = models.IntegerField(default=15)
    annual_leave = models.IntegerField(default=20)

    class Meta:
        verbose_name = "Leave Balance"
        verbose_name_plural = "Leave Balances"

    def total_allowed(self):
        return self.sick_leave + self.casual_leave + self.annual_leave

    def __str__(self):
        return f"{self.employee.name} Leave Balance"