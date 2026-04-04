import csv
from datetime import date
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, Q
from django.urls import reverse
from employees.forms import EmployeeForm, EmployeeReportFilterForm
from utils.pdf_generate import render_pdf_report
from .decorators import is_admin, is_hr, is_employee
from .models import Employee, EmployeeProfile
from leave.models import LeaveBalance, LeaveRequest
from attendance.models import Attendance
from payroll.models import SalaryHistory

def login_view(request):
    message = None

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.is_superuser or user.is_staff:
                return redirect('hr_dashboard')
            else:
                return redirect('employee_dashboard')

        else:
            message = {
                "type": "error",
                "text": "Invalid username or password"
            }

    return render(request, "registration/login.html", {
        "message": message
    })


def logout_view(request):
    logout(request)
    return redirect('login')

def _hr_or_admin(user):
    return is_admin(user) or is_hr(user)

@login_required
def home(request):
    return render(request, 'home.html') 

@login_required
def my_profile(request):
    profile = EmployeeProfile.objects.filter(user=request.user).first()

    if not profile:
        return render(request, 'employees/no_profile.html')

    return render(request, 'employees/employee_profile.html', {
        'employee': profile.employee,
        'viewer_role': 'EMPLOYEE'
    })

@login_required
def employee_profile(request, employee_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("You don't have access to this page.")

    emp = get_object_or_404(Employee, id=employee_id)

    return render(request, "employees/employee_profile.html", {
        "employee": emp,
        "viewer_role": "HR"  # show full buttons
    })

@login_required
def post_login_redirect(request):
    user = request.user
    if is_admin(user) or is_hr(user):
        return redirect("hr_dashboard")
    if is_employee(user):
        return redirect("employee_dashboard")
    return redirect("home")


@login_required
def hr_dashboard(request):

    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("You don't have access to this page.")

    today = date.today()

    year = request.GET.get("year")
    month = request.GET.get("month")
    day = request.GET.get("date")

    filters_applied = any([year, month, day])

    total_employees = 0
    pending_leaves = 0
    approved_leaves = 0
    rejected_leaves = 0

    today_attendance = 0
    present_count = 0
    absent_count = 0
    payroll_records_this_month = 0

    dept_labels = []
    dept_counts = []

    attendance_labels = ["Present", "Absent"]
    attendance_counts = [0, 0]

    payroll_labels = []
    payroll_totals = []

    if filters_applied:
        leave_base = LeaveRequest.objects.all()

        if year:
            leave_base = leave_base.filter(applied_at__year=int(year))

        if month:
            leave_base = leave_base.filter(applied_at__month=int(month))

        if day:
            leave_base = leave_base.filter(applied_at__day=int(day))

        pending_leaves = leave_base.filter(status="PENDING").count()
        approved_leaves = leave_base.filter(status="APPROVED").count()
        rejected_leaves = leave_base.filter(status="REJECTED").count()

        employee_base = Employee.objects.all()

        if year and month and day:
            filter_date = date(int(year), int(month), int(day))
            employee_base = employee_base.filter(joining_date__lte=filter_date)

        elif year and month:
            employee_base = employee_base.filter(
                joining_date__year__lt=int(year)
            ) | employee_base.filter(
                joining_date__year=int(year),
                joining_date__month__lte=int(month)
            )

        elif year:
            employee_base = employee_base.filter(joining_date__year__lte=int(year))

        total_employees = employee_base.count()

        attendance_base = Attendance.objects.all()

        if year:
            attendance_base = attendance_base.filter(date__year=int(year))

        if month:
            attendance_base = attendance_base.filter(date__month=int(month))

        if day:
            attendance_base = attendance_base.filter(date__day=int(day))

        if year and month and day:
            filter_date = date(int(year), int(month), int(day))
            attendance_base = attendance_base.filter(
                employee__joining_date__lte=filter_date
            )

        present_count = attendance_base.filter(status="Present").count()

        leave_range_qs = LeaveRequest.objects.filter(status="APPROVED")

        if year and month and day:
            selected_date = date(int(year), int(month), int(day))

            leave_range_qs = leave_range_qs.filter(
                start_date__lte=selected_date,
                end_date__gte=selected_date
            )

            absent_count = leave_range_qs.count()

        elif year and month:
            leave_range_qs = leave_range_qs.filter(
                start_date__year=int(year),
                start_date__month=int(month)
            )

            leave_days = 0
            for leave in leave_range_qs:
                leave_days += (leave.end_date - leave.start_date).days + 1

            absent_count = leave_days

        elif year:
            leave_range_qs = leave_range_qs.filter(
                start_date__year=int(year)
            )

            leave_days = 0
            for leave in leave_range_qs:
                leave_days += (leave.end_date - leave.start_date).days + 1

            absent_count = leave_days

        today_attendance = present_count + absent_count
        attendance_counts = [present_count, absent_count]

    
        payroll_qs = SalaryHistory.objects.all()

        if year:
            payroll_qs = payroll_qs.filter(pay_month__year=int(year))

        if month:
            payroll_qs = payroll_qs.filter(pay_month__month=int(month))

        payroll_records_this_month = payroll_qs.count()

        payroll_data = (
            payroll_qs
            .values("pay_month__year", "pay_month__month")
            .annotate(total=Sum("stored_net_pay"))
            .order_by("pay_month__year", "pay_month__month")
        )

        for item in payroll_data:
            y = item["pay_month__year"]
            m = item["pay_month__month"]

            payroll_labels.append(date(y, m, 1).strftime("%b %Y"))
            payroll_totals.append(float(item["total"] or 0))

        dept_data = (
            employee_base
            .values("department")
            .annotate(count=Count("id"))
        )

        dept_labels = [d["department"] for d in dept_data]
        dept_counts = [d["count"] for d in dept_data]

    return render(request, "dashboard/hr_dashboard.html", {

        "total_employees": total_employees,

        "pending_leaves": pending_leaves,
        "approved_leaves": approved_leaves,
        "rejected_leaves": rejected_leaves,

        "today_attendance": today_attendance,
        "present_count": present_count,
        "absent_count": absent_count,
        "payroll_records_this_month": payroll_records_this_month,

        "dept_labels": dept_labels,
        "dept_counts": dept_counts,

        "attendance_labels": attendance_labels,
        "attendance_counts": attendance_counts,

        "payroll_labels": payroll_labels,
        "payroll_totals": payroll_totals,

        "today": today,

        "years": range(2020, today.year + 2),
        "months": [
            (1,"Jan"), (2,"Feb"), (3,"Mar"), (4,"Apr"),
            (5,"May"), (6,"Jun"), (7,"Jul"), (8,"Aug"),
            (9,"Sep"), (10,"Oct"), (11,"Nov"), (12,"Dec")
        ],
        "day_range": range(1, 32)
    })

@login_required
def employee_dashboard(request):

    def _employee_only(user):
        return user.is_superuser or user.groups.filter(name="EMPLOYEE").exists()

    if not _employee_only(request.user):
        return HttpResponseForbidden("You don't have access to this page.")

    profile = EmployeeProfile.objects.select_related("employee").filter(user=request.user).first()

    if not profile:
        return HttpResponseForbidden("No EmployeeProfile linked. Contact HR.")

    emp = profile.employee
    today = date.today()

    year = request.GET.get("year")
    month = request.GET.get("month")
    day = request.GET.get("date")

    year = int(year) if year else None
    month = int(month) if month else None
    day = day if day else None

    filters_applied = any([year, month, day])

    attendance_base = Attendance.objects.filter(employee=emp)

    if year:
        attendance_base = attendance_base.filter(date__year=year)

    if month:
        attendance_base = attendance_base.filter(date__month=month)

    if day:
        if "-" in day:
            attendance_base = attendance_base.filter(date=day)
        else:
            attendance_base = attendance_base.filter(date__day=day)

    month_labels = []
    worked_days_data = []
    my_attendance_month = 0

    if filters_applied:

        attendance_qs = attendance_base.filter(status=("Present"))

        if year and not month:

            monthly_data = (
                attendance_qs
                .values("date__month")
                .annotate(total=Count("id"))
            )

            attendance_dict = {
                item["date__month"]: item["total"]
                for item in monthly_data
            }

            my_attendance_month = sum(attendance_dict.values())

            for m in range(1, 13):
                month_labels.append(date(int(year), m, 1).strftime("%b"))
                worked_days_data.append(attendance_dict.get(m, 0))

        elif month:

            m = int(month)

            month_count = attendance_qs.count()

            my_attendance_month = month_count

            month_labels.append(date(today.year, m, 1).strftime("%b"))
            worked_days_data.append(month_count)

        else:

            count = attendance_qs.count()

            my_attendance_month = count

            month_labels.append("Filtered")
            worked_days_data.append(count)

    balance = LeaveBalance.objects.get_or_create(employee=emp)[0]

    approved_leaves = LeaveRequest.objects.filter(
        employee=emp,
        status="APPROVED"
    )

    if filters_applied:

        if year:
            approved_leaves = approved_leaves.filter(start_date__year=year)

        if month:
            approved_leaves = approved_leaves.filter(start_date__month=month)

        if day and "-" in day:
            approved_leaves = approved_leaves.filter(start_date=day)

    total_approved_days = sum(leave.total_days for leave in approved_leaves)

    total_allowed = (
        balance.sick_leave +
        balance.casual_leave +
        balance.annual_leave
    )

    leave_balance = total_allowed - total_approved_days if filters_applied else 0

    payroll_month_labels = []
    payroll_month_data = []
    salary_count = 0

    if filters_applied:

        payroll_qs = SalaryHistory.objects.filter(employee=emp)

        if year:
            payroll_qs = payroll_qs.filter(pay_month__year=year)

        if month:
            payroll_qs = payroll_qs.filter(pay_month__month=month)

        payroll_qs = (
            payroll_qs
            .values("pay_month__month")
            .annotate(total=Sum("stored_net_pay"))
        )

        payroll_dict = {
            item["pay_month__month"]: float(item["total"] or 0)
            for item in payroll_qs
        }

        if year and not month:

            for m in range(1, 13):
                payroll_month_labels.append(date(int(year), m, 1).strftime("%b"))
                payroll_month_data.append(payroll_dict.get(m, 0))

            salary_count = sum(1 for v in payroll_dict.values() if v > 0)

        elif month:

            m = int(month)
            payroll_month_labels.append(date(today.year, m, 1).strftime("%b"))
            payroll_month_data.append(payroll_dict.get(m, 0))

            salary_count = 1 if payroll_dict.get(m) else 0

    salary_qs = SalaryHistory.objects.filter(employee=emp)

    if filters_applied:

        if year:
            salary_qs = salary_qs.filter(pay_month__year=year)

        if month:
            salary_qs = salary_qs.filter(pay_month__month=month)

        latest_salary = salary_qs.order_by("-pay_month").first()

    else:
        latest_salary = 0

    return render(request, "dashboard/employee_dashboard.html", {
        "profile": profile,
        "my_attendance_month": my_attendance_month,
        "attendance_month_labels": month_labels,
        "attendance_month_data": worked_days_data,
        "my_approved_leaves": approved_leaves,
        "leave_balance": leave_balance,
        "payroll_month_labels": payroll_month_labels,
        "payroll_month_data": payroll_month_data,
        "latest_salary": latest_salary,
        "salary_count": salary_count,
        "today": today,
        "years": range(2020, today.year + 2),
        "months": [
            (1,"Jan"), (2,"Feb"), (3,"Mar"), (4,"Apr"),
            (5,"May"), (6,"Jun"), (7,"Jul"), (8,"Aug"),
            (9,"Sep"), (10,"Oct"), (11,"Nov"), (12,"Dec")
        ],
        "day_range": range(1, 32)
    })

@login_required
def employee_list(request):

    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("You don't have access.")

    q = (request.GET.get("q") or "").strip()

    qs = Employee.objects.all().order_by("name")

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q))

    return render(request, "employees/employee_list.html", {
        "employees": qs,
        "page_obj": qs, 
        "q": q,
    })


@login_required
def employee_create(request):

    message = None

    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES)

        if form.is_valid():
            email = form.cleaned_data.get("email")
            phone = form.cleaned_data.get("phone")

            if Employee.objects.filter(email=email).exists():
                message = {
                    "type": "warning",
                    "text": "Employee with this email already exists."
                }

            elif phone and Employee.objects.filter(phone=phone).exists():
                message = {
                    "type": "warning",
                    "text": "Employee with this phone already exists."
                }

            else:
                form.save()
                message = {
                    "type": "success",
                    "text": "Employee created successfully!"
                }
                form = EmployeeForm()

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
        form = EmployeeForm()

    return render(request, "employees/employee_form.html", {
        "form": form,
        "is_update": False,
        "message": message
    })


@login_required
def employee_update(request, emp_id):

    employee = get_object_or_404(Employee, id=emp_id)
    message = None

    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES, instance=employee)

        if form.is_valid():
            email = form.cleaned_data.get("email")
            phone = form.cleaned_data.get("phone")

            if Employee.objects.filter(email=email).exclude(id=employee.id).exists():
                message = {
                    "type": "warning",
                    "text": "Email already exists."
                }

            elif phone and Employee.objects.filter(phone=phone).exclude(id=employee.id).exists():
                message = {
                    "type": "warning",
                    "text": "Phone number already exists."
                }

            else:
                form.save()
                message = {
                    "type": "success",
                    "text": "Employee updated successfully!"
                }
                return redirect("employee_list")

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
        form = EmployeeForm(instance=employee)

    return render(request, "employees/employee_form.html", {
        "form": form,
        "is_update": True,
        "message": message
    })

@login_required
def employee_delete(request, employee_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("You don't have access to this page.")

    emp = get_object_or_404(Employee, id=employee_id)

    if request.method == "POST":
        emp.delete()
        return redirect("employee_list")

    return render(request, "employees/employee_delete.html", {"employee": emp})


@login_required
def employee_detail(request, employee_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("You don't have access to this page.")

    emp = get_object_or_404(Employee, id=employee_id)

    return render(request, "employees/employee_profile.html", {
        "employee": emp,
        "viewer_role": "HR"
    })

@login_required
def employee_joining_report(request):

    form = EmployeeReportFilterForm(request.GET or None)

    qs = Employee.objects.all()

    month = request.GET.get("month")
    year = request.GET.get("year")

    if year:
        qs = qs.filter(joining_date__year=int(year))

    if month:
        qs = qs.filter(joining_date__month=int(month))

    filter_applied = any([month, year])

    context = {
        "form": form,
        "employees": qs,
        "filter_applied": filter_applied, 
        "csv_download_url": reverse("employee_download_csv"),
        "pdf_download_url": reverse("employee_download_pdf"),
    }

    return render(request, "employees/employees_list_report.html", context)

def employee_chart_api(request):

    month = request.GET.get("month")
    year = request.GET.get("year")

    qs = Employee.objects.all()

    if year:
        qs = qs.filter(joining_date__year=int(year))

    if month:
        qs = qs.filter(joining_date__month=int(month))

    data = qs.values("department").annotate(count=Count("id"))

    labels = [d["department"] or "No Dept" for d in data]
    counts = [d["count"] for d in data]

    return JsonResponse({
        "labels": labels,
        "data": counts,
    })

@login_required
def employee_download_csv(request):
    qs = Employee.objects.all()

    # Apply filters
    month = request.GET.get("month")
    year = request.GET.get("year")

    if year:
        qs = qs.filter(joining_date__year=int(year))
    if month:
        qs = qs.filter(joining_date__month=int(month))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Email", "Phone", "Department", "Designation", "Joining Date"])

    for e in qs:
        writer.writerow([
            e.name,
            e.email,
            e.phone,
            e.department,
            e.designation,
            e.joining_date
        ])

    return response


@login_required
def employee_download_pdf(request):
    month = request.GET.get("month")
    year = request.GET.get("year")

    employees = Employee.objects.all()

    if month and year:
        employees = employees.filter(
            joining_date__year=year,
            joining_date__month=month
        )
    elif year:
        employees = employees.filter(
            joining_date__year=year
        )

    # ================= SUMMARY (NO COUNTER) =================
    dept_counts = {}

    for e in employees:
        dept = e.department or "Unknown"
        if dept in dept_counts:
            dept_counts[dept] += 1
        else:
            dept_counts[dept] = 1

    # ================= TABLE =================
    headers = [
        "Name", "Email", "Phone", "Department", "Designation", "Joining Date"
    ]

    rows = [
        [
            e.name,
            e.email,
            e.phone,
            e.department,
            e.designation,
            e.joining_date
        ]
        for e in employees
    ]

    # ================= RESPONSE =================
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="employee_report.pdf"'

    # ================= REUSABLE PDF =================
    return render_pdf_report(
        response,
        month=month,
        year=year,
        employee_name=None,
        title="Employee Report",
        summary_labels=list(dept_counts.keys()),
        summary_values=list(dept_counts.values()),
        table_title="Employee Details",
        table_headers=headers,
        table_rows=rows

    )
