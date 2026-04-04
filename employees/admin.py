import pandas as pd
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from employees.forms import UploadEmployeeExcelForm
from .models import Employee, EmployeeProfile
from django.db import transaction


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "department", "phone", "designation", "joining_date")
    search_fields = ("name", "email")
    list_filter = ("department", "joining_date")

    change_list_template = "admin/employee_list.html"

    # 🔹 Custom URL
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("upload-excel/", self.upload_excel, name="employee_upload_excel"),
        ]
        return custom_urls + urls

    # 🔹 Upload Logic
    def upload_excel(self, request):
        if request.method == "POST":
            form = UploadEmployeeExcelForm(request.POST, request.FILES)

            if form.is_valid():
                file = request.FILES["file"]

                try:
                    df = pd.read_excel(file)

                    # ✅ Normalize columns
                    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

                    # ✅ Required columns (based on your Excel)
                    required_columns = {
                        "name",
                        "email",
                        "phone",
                        "department",
                        "designation",
                        "joining_date"
                    }

                    if not required_columns.issubset(df.columns):
                        self.message_user(
                            request,
                            f"Missing columns: {required_columns - set(df.columns)}",
                            level=messages.ERROR,
                        )
                        return redirect("../")

                    # ✅ Dynamic mapping from model choices
                    department_map = dict((v, k) for k, v in Employee.DEPT_CHOICES)
                    designation_map = dict((v, k) for k, v in Employee.DESG_CHOICES)

                    created_count = 0
                    updated_count = 0
                    skipped_rows = []

                    # 🔒 Transaction
                    with transaction.atomic():
                        for index, row in df.iterrows():
                            try:
                                email = row.get("email")

                                if pd.isna(email):
                                    skipped_rows.append(index)
                                    continue

                                # 🔥 Map department & designation
                                dept_value = str(row.get("department")).strip()
                                desig_value = str(row.get("designation")).strip()

                                department_code = department_map.get(dept_value)
                                designation_code = designation_map.get(desig_value)

                                # ❌ Skip invalid values
                                if not department_code or not designation_code:
                                    skipped_rows.append(index)
                                    continue

                                # 📅 Handle joining date safely
                                joining_date = None
                                if pd.notna(row.get("joining_date")):
                                    try:
                                        joining_date = pd.to_datetime(row["joining_date"]).date()
                                    except:
                                        pass

                                employee, created = Employee.objects.update_or_create(
                                    email=email,
                                    defaults={
                                        "name": row.get("name", ""),
                                        "phone":row.get("phone", ""),
                                        "department": department_code,
                                        "designation": designation_code,
                                        "joining_date": joining_date,
                                    },
                                )

                                if created:
                                    created_count += 1
                                else:
                                    updated_count += 1

                            except Exception:
                                skipped_rows.append(index)

                    # ✅ Final message
                    self.message_user(
                        request,
                        f"Upload Successful → Created: {created_count}, Updated: {updated_count}, Skipped: {len(skipped_rows)}"
                    )

                except Exception as e:
                    self.message_user(request, f"Error: {e}", level=messages.ERROR)

                return redirect("../")

        else:
            form = UploadEmployeeExcelForm()

        return render(request, "admin/upload_employee_excel.html", {"form": form})

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "employee")
    search_fields = ("user__username", "user__email", "employee__name", "employee__email")
