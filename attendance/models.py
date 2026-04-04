from django.db import models
from employees.models import Employee

class Attendance(models.Model):

    STATUS = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Leave", "Leave"),
        ("Holiday", "Holiday"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS,
        default="Present"
    )

    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)

    notes = models.CharField(max_length=255, blank=True)

    class Meta:

        unique_together = ("employee", "date")

        ordering = ["-date"]

        indexes = [
            models.Index(fields=["employee", "date"])
        ]

    def __str__(self):
        return f"{self.employee} | {self.date} | {self.status}"