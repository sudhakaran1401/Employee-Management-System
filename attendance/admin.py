import pandas as pd
from datetime import datetime, timedelta
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from attendance.forms import UploadExcelForm
from .models import Attendance
from employees.models import Employee


def split_date_range(date_range_str):
    start_str, end_str = date_range_str.split(' - ')
    start_date = datetime.strptime(start_str.strip(), "%b %d %Y")
    end_date = datetime.strptime(end_str.strip(), "%b %d %Y")

    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.date())
        current += timedelta(days=1)

    return dates


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "date", "status", "check_in", "check_out")
    list_filter = ("status", "date")
    search_fields = ("employee__name", "employee__email")

    change_list_template = "admin/attendance_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-excel/', self.upload_excel),
        ]
        return custom_urls + urls

    def upload_excel(self, request):
        if request.method == "POST":
            form = UploadExcelForm(request.POST, request.FILES)

            if form.is_valid():
                excel_file = request.FILES["excel_file"]
                df = pd.read_excel(excel_file)

                for _, row in df.iterrows():
                    try:
                        employee = Employee.objects.get(id=row["employee_id"])
                    except Employee.DoesNotExist:
                        continue

                    date_value = str(row["date"])

                    if " - " in date_value:
                        dates = split_date_range(date_value)
                    else:
                        dates = [pd.to_datetime(date_value).date()]

                    for single_date in dates:
                        Attendance.objects.update_or_create(
                            employee=employee,
                            date=single_date,
                            defaults={
                                "status": "Present",
                                "check_in": row["check_in"] if pd.notna(row["check_in"]) else None,
                                "check_out": row["check_out"] if pd.notna(row["check_out"]) else None,
                                "notes": row.get("notes", "")
                            }
                        )

                self.message_user(request, "Excel uploaded successfully")
                return redirect("../")

        else:
            form = UploadExcelForm()

        return render(request, "admin/upload_attendance_excel.html", {"form": form})