from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from django import forms
from .models import LeaveRequest, Employee
import pandas as pd

from .models import LeaveRequest

class LeaveUploadForm(forms.Form):
    file = forms.FileField()

def process_excel(file):
    df = pd.read_excel(file)

    objects = []

    for _, row in df.iterrows():

        # Optional: basic validation skip empty rows
        if pd.isna(row["Employee"]) or pd.isna(row["Start Date"]):
            continue
        employee_name = row["Employee"]

        employee = Employee.objects.filter(name=employee_name).first()

        if not employee:
            print(f"Skipping: {employee_name}")
            continue

        leave_type_raw = str(row["Leave Type"]).strip().upper()

        if "SICK" in leave_type_raw:
            leave_type_value = "SICK"
        elif "CASUAL" in leave_type_raw:
            leave_type_value = "CASUAL"
        elif "ANNUAL" in leave_type_raw:
            leave_type_value = "ANNUAL"
        else:
            print(f"Skipping invalid leave type: {leave_type_raw}")
            continue

        reason = "" if pd.isna(row.get("Reason")) else str(row.get("Reason")).strip()

        obj = LeaveRequest(
            employee=employee,
            leave_type=leave_type_value,
            start_date=pd.to_datetime(row["Start Date"]).date(),
            end_date=pd.to_datetime(row["End Date"]).date(),
            reason=reason,
            applied_at=pd.to_datetime(row["Applied Date"]).date(),
            status=row["Status"]
        )

        objects.append(obj)

    LeaveRequest.objects.bulk_create(objects, batch_size=500)

    return len(objects)

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "employee",
        "leave_type",
        "total_days",
        "start_date",
        "end_date",
        "reason",
        "applied_at",
        "status"
    )

    list_filter = ("status", "leave_type")
    search_fields = ("employee_name", "employee_email")

    change_list_template = "admin/leave_request_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("upload-excel/", self.upload_excel_view),
        ]
        return custom_urls + urls

    def upload_excel_view(self, request):

        if request.method == "POST":
            form = LeaveUploadForm(request.POST, request.FILES)

            if form.is_valid():
                file = form.cleaned_data["file"]

                count = process_excel(file)

                self.message_user(
                    request,
                    f"🚀 {count} records uploaded successfully!"
                )

                return redirect("..")  

        else:
            form = LeaveUploadForm()

        return render(
            request,
            "admin/upload_leave_request_excel.html",
            {"form": form}
        )
    
    def save_model(self, request, obj, form, change):
        obj.full_clean()   
        super().save_model(request, obj, form, change)