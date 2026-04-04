from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.html import format_html
import pandas as pd
from .models import SalaryHistory
from employees.models import Employee
from .forms import ExcelUploadForm


@admin.register(SalaryHistory)
class SalaryHistoryAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'employee',
        'pay_month',
        'gross',
        'total_deductions',
        'net_pay',
        'paid_date',
    )

    list_filter = ('pay_month', 'is_locked')

    search_fields = ('employee__name', 'pay_month')

    ordering = ('-pay_month',)

    change_list_template = "admin/salary_list.html"

    def pay_month(self, obj):
        return obj.pay_month.strftime("%b %Y")   # Mar 2026

    pay_month.short_description = "Pay Month"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-excel/', self.upload_excel, name='upload_excel'),
        ]
        return custom_urls + urls
    
    def upload_excel(self, request):
        if request.method == "POST":
            form = ExcelUploadForm(request.POST, request.FILES)

            if form.is_valid():
                file = request.FILES['file']

                try:
                    df = pd.read_excel(file)

                    df.columns = df.columns.str.strip().str.lower()

                    for _, row in df.iterrows():
                        employee = Employee.objects.get(id=row['employee_id'])

                        SalaryHistory.objects.create(
                            employee=employee,
                            pay_month=row['pay_month'],
                            basic=row['basic'],
                            hra=row['hra'],
                            allowances=row['allowances'],
                            pf=row['pf'],
                            tax=row['tax'],
                            other_deductions=row['other_deductions'],
                            stored_gross=row['gross'],
                            stored_total_deductions=row['total_deductions'],
                            stored_net_pay=row['net_pay'],

                            paid_date=row.get('paid_date', None)
                        )

                    self.message_user(request, "Excel uploaded successfully ")

                except Exception as e:
                    self.message_user(request, f"Error: {e}", level=messages.ERROR)

                return redirect("../")

        else:
            form = ExcelUploadForm()

        return render(request, "admin/upload_salary_excel.html", {"form": form})