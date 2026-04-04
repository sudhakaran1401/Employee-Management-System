from datetime import date, datetime
from decimal import Decimal

from django.db import models
from employees.models import Employee
from calendar import monthrange
from attendance.models import Attendance 
from leave.models import LeaveRequest

class SalaryHistory(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="salary_history"
    )

    pay_month = models.DateField(
        help_text="Use any date in the month (e.g., 2026-02-01)"
    )

    is_locked = models.BooleanField(default=False)

    amt_per_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    worked_days = models.IntegerField(default=0)
    leave_taken = models.IntegerField(default=0)

    basic = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    pf = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    stored_gross = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stored_total_deductions = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stored_net_pay = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    paid_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "pay_month"],
                name="unique_employee_month_salary"
            )
        ]
        ordering = ["-pay_month"]

    @property
    def gross(self):
        return self.basic + self.hra + self.allowances

    @property
    def total_deductions(self):
        return self.pf + self.tax + self.other_deductions

    @property
    def net_pay(self):
        return self.gross - self.total_deductions

    def save(self, *args, **kwargs):

        year = self.pay_month.year
        month = self.pay_month.month

        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        leave_requests = LeaveRequest.objects.filter(
            employee=self.employee,
            status="APPROVED",
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        current_month_leaves = 0

        for leave in leave_requests:
            leave_start = max(leave.start_date, start_date)
            leave_end = min(leave.end_date, end_date)
            current_month_leaves += (leave_end - leave_start).days + 1

        previous_leaves_qs = LeaveRequest.objects.filter(
            employee=self.employee,
            status="APPROVED",
            end_date__lt=start_date
        )

        previous_leaves = 0

        for leave in previous_leaves_qs:
            previous_leaves += (leave.end_date - leave.start_date).days + 1

        total_leaves_used = previous_leaves + current_month_leaves

        FIXED_DAYS = Decimal("30")
        daily_amount = self.amt_per_day or Decimal("0")

        monthly_salary = daily_amount * FIXED_DAYS

        TOTAL_LEAVE_BALANCE = 50

        if total_leaves_used <= TOTAL_LEAVE_BALANCE:
            payable_salary = monthly_salary
        else:
            extra_leaves = total_leaves_used - TOTAL_LEAVE_BALANCE
            deduction = daily_amount * Decimal(extra_leaves)
            payable_salary = monthly_salary - deduction

        self.basic = payable_salary * Decimal("0.70")
        self.hra = payable_salary * Decimal("0.20")
        self.allowances = payable_salary * Decimal("0.10")

        self.pf = payable_salary * Decimal("0.05")
        self.tax = payable_salary * Decimal("0.02")
        self.other_deductions = self.other_deductions or Decimal("0")

        self.stored_gross = self.basic + self.hra + self.allowances
        self.stored_total_deductions = self.pf + self.tax + self.other_deductions
        self.stored_net_pay = self.stored_gross - self.stored_total_deductions

        self.worked_days = 30
        self.leave_taken = current_month_leaves

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.name} - {self.pay_month}"