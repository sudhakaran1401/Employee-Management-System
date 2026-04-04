import calendar
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.urls import reverse
from django.db.models.functions import TruncMonth
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from employees.decorators import is_admin, is_hr, is_employee
from employees.models import Employee, EmployeeProfile
from utils.filters import apply_common_filters
from .forms import SalaryForm, SalaryReportForm
from .models import SalaryHistory
from reportlab.lib.enums import TA_CENTER


def _hr_or_admin(user):
    return is_admin(user) or is_hr(user)

@login_required
def create_salary(request):

    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("Only HR/Admin can create payroll records.")

    message = None

    if request.method == "POST":
        form = SalaryForm(request.POST)

        if form.is_valid():
            salary = form.save(commit=False)

            # 🔍 Check duplicate salary
            if SalaryHistory.objects.filter(
                employee=salary.employee,
                pay_month=salary.pay_month
            ).exists():

                message = {
                    "type": "warning",
                    "text": "Salary already exists for this employee and month."
                }

            else:
                salary.save()

                message = {
                    "type": "success",
                    "text": "Salary created successfully!"
                }

                # 🔥 IMPORTANT: Reset form after success
                form = SalaryForm()

        else:
            error_text = None
            for errors in form.errors.values():
                for error in errors:
                    error_text = error
                    break
                if error_text:
                    break

            message = {
                "type": "error",
                "text": error_text or "Invalid form data"
            }

    else:
        form = SalaryForm()

    return render(request, "payroll/create_salary.html", {
        "form": form,
        "is_update": False,
        "message": message
    })

@login_required
def update_salary(request, pk):

    salary = get_object_or_404(SalaryHistory, pk=pk)
    message = None

    if request.method == "POST":
        form = SalaryForm(request.POST, instance=salary)

        if form.is_valid():
            updated_salary = form.save(commit=False)

            if SalaryHistory.objects.filter(
                employee=updated_salary.employee,
                pay_month=updated_salary.pay_month
            ).exclude(id=salary.id).exists():

                message = {
                    "type": "warning",
                    "text": "Salary already exists for this employee and month."
                }

            else:
                updated_salary.save()
                message = {
                    "type": "success",
                    "text": "Salary updated successfully!"
                }

        else:
            error_text = None
            for errors in form.errors.values():
                for error in errors:
                    error_text = error
                    break
                if error_text:
                    break

            message = {
                "type": "error",
                "text": error_text or "Invalid form data"
            }

        return render(request, "payroll/create_salary.html", {
            "form": form,
            "is_update": True,
            "message": message
        })

    else:
        form = SalaryForm(instance=salary)

    return render(request, "payroll/create_salary.html", {
        "form": form,
        "is_update": True
    })

def get_filtered_salary_queryset(request):
    qs = SalaryHistory.objects.all()

    employee = request.GET.get("employee") or None
    year = request.GET.get("year") or None
    month = request.GET.get("month")

    if month in ["", None, "0"]:
        month = None

    if employee:
        qs = qs.filter(employee_id=employee)

    if year:
        try:
            qs = qs.filter(pay_month__year=int(year))
        except ValueError:
            pass

    if month:
        try:
            qs = qs.filter(pay_month__month=int(month))
        except ValueError:
            pass

    return qs

@login_required
def admin_salary_list(request):

    if not request.user.is_staff:
        return HttpResponseForbidden()

    form = SalaryReportForm(request.GET or None)

    rows = get_filtered_salary_queryset(request).order_by("-pay_month")

    return render(request, "payroll/salary_history_admin.html", {
        "form": form,
        "rows": rows,
        "page_obj": rows, 
        "filter_applied": any([
            request.GET.get("employee"),
            request.GET.get("year"),
            request.GET.get("month")
        ]),
        "csv_download_url": reverse("salary_download_csv"),
        "pdf_download_url": reverse("salary_download_pdf"),
    })

@login_required
def employee_salary_history(request, employee_id=None):

    if request.user.is_staff:
        employee = get_object_or_404(Employee, id=employee_id)
    else:
        profile = EmployeeProfile.objects.filter(user=request.user).first()
        employee = profile.employee

    qs = SalaryHistory.objects.filter(employee=employee).order_by("-pay_month")

    return render(request, "payroll/salary_history_employee.html", {
        "rows": qs,
        "page_obj": qs, 
        "employee": employee
    })

@login_required
def all_salary_history(request):

    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("Only HR/Admin can view salary history.")

    rows = SalaryHistory.objects.select_related("employee").order_by("-pay_month")

    return render(request, "payroll/all_salary_history.html", {
        "rows": rows,
        "page_obj": rows,   
    })

@login_required
def payslip_view(request, employee_id):

    salary = get_object_or_404(
        SalaryHistory.objects.select_related("employee"),
        pk=employee_id
    )

    return render(request, "payroll/payslip_view.html", {
        "salary": salary
    })

@login_required
def payslip_pdf(request, employee_id):

    salary = get_object_or_404(SalaryHistory.objects.select_related("employee"), pk=employee_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="payslip.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    center_style = ParagraphStyle(
    name='Center',
    parent=styles['Normal'],
    alignment=TA_CENTER
    )

    title_style = ParagraphStyle(
        name='TitleCenter',
        parent=styles['Title'],
        alignment=TA_CENTER
    )

    # ================= HEADER =================
    elements.append(Paragraph("<b>YOUR COMPANY PVT LTD</b>", title_style))
    elements.append(Paragraph("Chennai, Tamil Nadu", center_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Salary Slip - March 2026</b>", center_style))
    elements.append(Spacer(1, 20))

    # ================= EMPLOYEE + BANK =================
    info_data = [
        ["Employee ID", salary.employee.id, "Bank Name", "HDFC Bank"],
        ["Name", salary.employee.name, "Account No", "XXXX1234"],
        ["Department", salary.employee.department, "IFSC", "HDFC0001234"],
        ["Designation", salary.employee.designation, "PAN", "ABCDE1234F"],
    ]

    info_table = Table(info_data, colWidths=[120, 150, 120, 150])
    info_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('BACKGROUND', (2,0), (2,-1), colors.lightgrey),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # ================= SALARY TABLE =================
    salary_data = [
        ["Earnings", "Amount", "Deductions", "Amount"],
        ["Basic", salary.basic, "PF", salary.pf],
        ["HRA", salary.hra, "Tax", salary.tax],
        ["Allowances", salary.allowances, "Other", salary.other_deductions],
        ["Gross", salary.gross, "Total Deduction", salary.total_deductions],
        ["NET PAY", salary.net_pay, "", ""],
    ]

    salary_table = Table(salary_data, colWidths=[120, 100, 120, 100])
    salary_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),

        # Highlight Net Pay
        ('BACKGROUND', (0,-1), (1,-1), colors.white),
        ('SPAN', (2,-1), (3,-1)),
    ]))

    elements.append(salary_table)
    elements.append(Spacer(1, 20))

    # ================= ATTENDANCE =================
    attendance_data = [
        ["Working Days", "30"],
        ["Paid Days", "28"],
        ["LOP", "2"],
    ]

    attendance_table = Table(attendance_data, colWidths=[200, 200])
    attendance_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
    ]))

    elements.append(attendance_table)
    elements.append(Spacer(1, 30))

    # ================= FOOTER =================
    elements.append(Paragraph("Note: This is a system-generated payslip.", styles['Normal']))
    elements.append(Spacer(1, 30))

    signature_table = Table([
        ["Employer Signature", "", "Employee Signature"]
    ], colWidths=[180, 60, 180])

    signature_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (0,0), 0.5, colors.black),
        ('LINEABOVE', (2,0), (2,0), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))

    elements.append(signature_table)

    doc.build(elements)
    return response


def salary_chart_api(request):

    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("Only HR/Admin can view charts.")
    
    qs = get_filtered_salary_queryset(request)

    data = (
        qs.annotate(month=TruncMonth("pay_month"))
        .values("month")
        .annotate(
            total=Sum("basic") + Sum("hra") + Sum("allowances")
                  - (Sum("pf") + Sum("tax") + Sum("other_deductions"))
        )
        .order_by("month")
    )

    labels = [d["month"].strftime("%b %Y") for d in data]
    totals = [float(d["total"] or 0) for d in data]

    return JsonResponse({
        "labels": labels,
        "data": totals
    })

@login_required
def salary_download_csv(request):
    qs = apply_common_filters(
        SalaryHistory.objects.select_related("employee"),
        request,
        "pay_month"
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="salary_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Employee", "Department", "Month", "Gross", "Deduction", "Net Pay", "Paid date"
    ])

    for r in qs:
        writer.writerow([
            r.employee.name,
            r.employee.department,
            r.pay_month.strftime("%b %Y"),
            r.gross,
            r.total_deductions,
            r.net_pay,
            r.paid_date.strftime("%d-%m-%Y") if r.paid_date else "-"
        ])

    return response

@login_required
def salary_download_pdf(request):

    employee_id = request.GET.get("employee")
    month = request.GET.get("month")
    year = request.GET.get("year")

    qs = apply_common_filters(
        SalaryHistory.objects.select_related("employee"),
        request,
        "pay_month"
    )

    employee_name = None

    if employee_id:
        record = qs.filter(employee__id=employee_id).first()
        if record:
            employee_name = record.employee.name

    if not employee_name:
        employee_name = "All Employees"

    month_name = None
    if month and month.isdigit():
        month_name = calendar.month_name[int(month)]
    else:
        month_name = month

    title_text = "Salary Report"

    if employee_name != "All Employees" and month_name and year:
        title_text += f" - {employee_name} ({month_name} {year})"

    elif employee_name != "All Employees" and year:
        title_text += f" - {employee_name} ({year})"

    elif employee_name != "All Employees":
        title_text += f" - {employee_name}"

    elif month_name and year:
        title_text += f" - {month_name} {year}"

    elif year:
        title_text += f" - Year {year}"

    else:
        title_text += " - All Employees"


    total_payrolls = qs.count()
    total_net_pay = qs.aggregate(total=Sum('stored_net_pay'))['total'] or 0

    chart_data = (
        qs.values("pay_month")
        .annotate(total_net=Sum("stored_net_pay"))
        .order_by("pay_month")
    )

    months = [d["pay_month"].strftime("%b %Y") for d in chart_data]
    totals = [d["total_net"] for d in chart_data]

    buffer = BytesIO()
    plt.figure()
    plt.plot(months, totals, marker='o')
    plt.title("Monthly Net Pay Trend")
    plt.xlabel("Month")
    plt.ylabel("Net Pay")
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="salary_report.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>{title_text}</b>", styles['Title']))
    elements.append(Spacer(1, 15))

    card_data = [
        ["Total Payrolls", total_payrolls],
        ["Total Net Pay", f"₹ {total_net_pay}"]
    ]

    card_table = Table(card_data, colWidths=[250, 150])
    card_table.setStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')
    ])

    elements.append(card_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Salary Chart</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))

    chart_image = Image(buffer, width=500, height=250)
    elements.append(chart_image)
    elements.append(Spacer(1, 20))

    table_data = [["Employee", "Department", "Month", "Gross", "Deduction", "Net Pay", "Paid Date"]]

    for r in qs:
        table_data.append([
            r.employee.name,
            r.employee.department,
            r.pay_month.strftime("%b %Y"),
            r.gross,
            r.total_deductions,
            r.net_pay,
            r.paid_date.strftime("%d %b %Y") if r.paid_date else "-"
        ])

    table = Table(table_data, repeatRows=1)

    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ])

    elements.append(Paragraph("<b>Employee Salaries</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(table)

    doc.build(elements)

    return response