import csv
from datetime import timedelta
from attendance.models import Attendance
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from attendance.utils import can_mark_attendance
from utils.file_name import generate_filename
from utils.filters import apply_common_filters
from utils.pdf_generate import render_pdf_report
from .forms import LeaveReportFilterForm, LeaveRequestForm
from .models import LeaveRequest
from employees.models import Employee, EmployeeProfile
from django.http import HttpResponse


def _employee_only(user):
    return user.groups.filter(name="EMPLOYEE").exists()


def _hr_or_admin(user):
    return user.is_superuser or user.groups.filter(name__in=["HR", "ADMIN"]).exists()


@login_required
def apply_leave(request):
    if not _employee_only(request.user):
        return HttpResponseForbidden("Only employees can apply for leave.")

    profile = EmployeeProfile.objects.filter(user=request.user).first()
    if not profile or not profile.employee:
        return HttpResponseForbidden("Employee profile not linked.")

    message = None

    if request.method == "POST":
        form = LeaveRequestForm(request.POST)

        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = profile.employee

            if leave.start_date > leave.end_date:
                message = {
                    "type": "error",
                    "text": "Start date cannot be after end date."
                }

            elif LeaveRequest.objects.filter(
                employee=leave.employee,
                start_date__lte=leave.end_date,
                end_date__gte=leave.start_date
            ).exists():

                message = {
                    "type": "warning",
                    "text": "Leave overlaps with existing request."
                }

            else:
                leave.save()
                message = {
                    "type": "success",
                    "text": "Leave request submitted successfully!"
                }
                form = LeaveRequestForm()

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

        return render(request, "leave/apply_leaves.html", {
            "form": form,
            "is_update": False,
            "message": message
        })

    else:
        form = LeaveRequestForm()

    return render(request, "leave/apply_leaves.html", {
        "form": form,
        "is_update": False
    })

@login_required
def update_leave(request, leave_id):
    if not _employee_only(request.user):
        return HttpResponseForbidden("Only employees can update leave.")

    profile = EmployeeProfile.objects.filter(user=request.user).first()
    if not profile or not profile.employee:
        return HttpResponseForbidden("Employee profile not linked.")

    leave = get_object_or_404(LeaveRequest, id=leave_id, employee=profile.employee)

    message = None

    if leave.status == "APPROVED":
        message = {
            "type": "error",
            "text": "Cannot update an approved leave request."
        }
        return render(request, "leave/apply_leaves.html", {
            "form": LeaveRequestForm(instance=leave),
            "is_update": True,
            "message": message
        })

    if request.method == "POST":
        form = LeaveRequestForm(request.POST, instance=leave)

        if form.is_valid():
            updated_leave = form.save(commit=False)
            updated_leave.employee = profile.employee

            if updated_leave.start_date > updated_leave.end_date:
                message = {
                    "type": "error",
                    "text": "Start date cannot be after end date."
                }

            elif LeaveRequest.objects.filter(
                employee=updated_leave.employee,
                start_date__lte=updated_leave.end_date,
                end_date__gte=updated_leave.start_date
            ).exclude(id=leave.id).exists():

                message = {
                    "type": "warning",
                    "text": "Leave overlaps with another request."
                }

            else:
                updated_leave.save()
                message = {
                    "type": "success",
                    "text": "Leave updated successfully!"
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

        return render(request, "leave/apply_leaves.html", {
            "form": form,
            "is_update": True,
            "message": message
        })

    else:
        form = LeaveRequestForm(instance=leave)

    return render(request, "leave/apply_leaves.html", {
        "form": form,
        "is_update": True
    })

@login_required
def my_leave_requests(request):

    profile = EmployeeProfile.objects.select_related("employee").filter(user=request.user).first()

    if not profile:
        return HttpResponseForbidden("No profile linked.")

    leave_requests = LeaveRequest.objects.filter(
        employee=profile.employee
    ).order_by("-applied_at")

    return render(request, "leave/my_requests.html", {
        "leave_requests": leave_requests,
        "page_obj": leave_requests,
        "viewer_role": "Employee",
    })


@login_required
def pending_leave_requests(request, employee_id=None):

    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("Only HR/Admin allowed.")

    if employee_id:
        leave_requests = LeaveRequest.objects.filter(
            employee_id=employee_id
        ).order_by("-applied_at")
    else:
        leave_requests = LeaveRequest.objects.filter(
            status="PENDING"
        ).order_by("-applied_at")

    return render(request, "leave/my_requests.html", {
        "leave_requests": leave_requests,
        "viewer_role": "HR",
    })


@login_required
def approve_leave(request, pk: int):
    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("Only HR/Admin can approve leave requests.")

    leave = LeaveRequest.objects.filter(id=pk).first()

    if leave:
        leave.status = "APPROVED"
        leave.save()

        current = leave.start_date

        while current <= leave.end_date:

            allowed, data = can_mark_attendance(leave.employee, current)

            if allowed:
                if data:
                    data.status = "Leave"
                    data.save()
                else:
                    Attendance.objects.create(
                        employee=leave.employee,
                        date=current,
                        status="Leave"
                    )

            current += timedelta(days=1)

    return redirect(request.GET.get('next', 'hr_all_leave_requests'))


@login_required
def reject_leave(request, pk: int):
    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("Only HR/Admin can reject leave requests.")

    leave = LeaveRequest.objects.filter(id=pk).first()
    if leave:
        leave.status = "REJECTED"               
        leave.save()
    return redirect(request.GET.get('next', 'hr_all_leave_requests'))
    

def calculate_leave_days(queryset):
    total = 0
    for leave in queryset:
        total += (leave.end_date - leave.start_date).days + 1
    return total

@login_required
def leave_balance(request):

    if not _employee_only(request.user):
        return HttpResponseForbidden("Only employees can view leave balance.")

    profile = EmployeeProfile.objects.filter(user=request.user).first()

    if not profile or not profile.employee:
        return HttpResponseForbidden("Employee profile not linked.")

    employee = profile.employee

    # TOP CARDS → submission counts
    total = LeaveRequest.objects.filter(employee=employee).count()

    approved = LeaveRequest.objects.filter(employee=employee,status="APPROVED").count()
    pending = LeaveRequest.objects.filter(employee=employee,status="PENDING").count()
    rejected = LeaveRequest.objects.filter(employee=employee,status="REJECTED").count()
    sick_leaves = LeaveRequest.objects.filter(employee=employee,leave_type="SICK",status="APPROVED")
    casual_leaves = LeaveRequest.objects.filter(employee=employee,leave_type="CASUAL",status="APPROVED")
    annual_leaves = LeaveRequest.objects.filter(employee=employee,leave_type="ANNUAL",status="APPROVED")

    sick_applied = calculate_leave_days(sick_leaves)
    casual_applied = calculate_leave_days(casual_leaves)
    annual_applied = calculate_leave_days(annual_leaves)

    total_applied = sick_applied + casual_applied + annual_applied

    # leave limits
    SICK_MAX = 15
    CASUAL_MAX = 15
    ANNUAL_MAX = 20
    TOTAL_MAX = SICK_MAX + CASUAL_MAX + ANNUAL_MAX

    context = {
        "employee": employee,

        # top cards
        "total": total,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,

        # bottom cards
        "sick_applied": sick_applied,
        "casual_applied": casual_applied,
        "annual_applied": annual_applied,
        "total_applied": total_applied,

        "SICK_MAX": SICK_MAX,
        "CASUAL_MAX": CASUAL_MAX,
        "ANNUAL_MAX": ANNUAL_MAX,
        "TOTAL_MAX": TOTAL_MAX,

        "viewer_role": "Employee",
    }

    return render(request, "leave/leave_balance.html", context)


@login_required
def leave_balance_by_employee(request, employee_id):
    # HR/Admin can see any employee's balance
    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("Only HR/Admin can view employee leave balance.")

    employee = get_object_or_404(Employee, id=employee_id)

    total = LeaveRequest.objects.filter(employee=employee).count()

    approved = LeaveRequest.objects.filter(
        employee=employee,
        status="APPROVED"
    ).count()

    pending = LeaveRequest.objects.filter(
        employee=employee,
        status="PENDING"
    ).count()

    rejected = LeaveRequest.objects.filter(
        employee=employee,
        status="REJECTED"
    ).count()

    sick_leaves = LeaveRequest.objects.filter(
        employee=employee,
        leave_type="SICK",
        status="APPROVED"
    )

    casual_leaves = LeaveRequest.objects.filter(
        employee=employee,
        leave_type="CASUAL",
        status="APPROVED"
    )

    annual_leaves = LeaveRequest.objects.filter(
        employee=employee,
        leave_type="ANNUAL",
        status="APPROVED"
    )

    sick_applied = calculate_leave_days(sick_leaves)
    casual_applied =calculate_leave_days(casual_leaves)
    annual_applied =calculate_leave_days(annual_leaves)

    total_applied = sick_applied + casual_applied + annual_applied

    SICK_MAX = 15
    CASUAL_MAX = 15
    ANNUAL_MAX = 20
    TOTAL_MAX = SICK_MAX + CASUAL_MAX + ANNUAL_MAX

    return render(request, "leave/leave_balance.html", {
        "employee": employee,

        "total": total,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,

        "sick_applied": sick_applied,
        "casual_applied": casual_applied,
        "annual_applied": annual_applied,
        "total_applied": total_applied,

        "SICK_MAX": SICK_MAX,
        "CASUAL_MAX": CASUAL_MAX,
        "ANNUAL_MAX": ANNUAL_MAX,
        "TOTAL_MAX": TOTAL_MAX,

        "viewer_role": "HR",
    })


@login_required
def hr_all_leave_requests(request):

    leave_requests = LeaveRequest.objects.all().order_by('-applied_at')

    return render(request, 'leave/leave_requests.html', {
        'leave_requests': leave_requests,
        "page_obj": leave_requests,  # ✅
        'viewer_role': "HR",
    })

@login_required
def leave_report(request):

    form = LeaveReportFilterForm(request.GET or None)
    leave_requests = LeaveRequest.objects.select_related("employee").all()

    filter_applied = False

    if form.is_valid():
        month = form.cleaned_data.get("month")
        year = form.cleaned_data.get("year")
        employee = form.cleaned_data.get("employee")

        filters = {}

        if month:
            filters["applied_at__month"] = int(month)
        if year:
            filters["applied_at__year"] = int(year)
        if employee:
            filters["employee"] = employee

        if filters:
            filter_applied = True
            leave_requests = leave_requests.filter(**filters)
        else:
            leave_requests = LeaveRequest.objects.none()

    leave_requests = leave_requests.order_by('-applied_at')

    total = leave_requests.count()
    approved = leave_requests.filter(status="APPROVED").count()
    pending = leave_requests.filter(status="PENDING").count()
    rejected = leave_requests.filter(status="REJECTED").count()

    return render(request, "leave/leave_report.html", {
        "form": form,
        "leave_requests": leave_requests,
        "page_obj": leave_requests,  # ✅
        "is_hr": True,
        "filter_applied": filter_applied,
        "total": total,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "csv_download_url": reverse("leave_report_download_csv"),
        "pdf_download_url": reverse("leave_report_download_pdf"),
    })

@login_required
def leave_report_download_csv(request):
    qs = apply_common_filters(
        LeaveRequest.objects.select_related("employee"),
        request,
        "start_date"
    )

    response = HttpResponse(content_type='text/csv')
    title = "Leave Report"

    year = request.GET.get("year")
    month = request.GET.get("month")
    employee_id = request.GET.get("employee")

    employee_name = None
    if employee_id:
        emp = Employee.objects.filter(id=employee_id).first()
        if emp:
            employee_name = emp.name

    filename = generate_filename(title, year, month, employee_name, "csv")

    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        "Employee", "Department", "Leave Type", "Days", "Start Date",
        "End Date", "Reason", "Applied Date", "Status"
    ])

    for r in qs:
        writer.writerow([
            r.employee.name,
            r.employee.department,
            r.get_leave_type_display(),
            r.total_days,
            r.start_date,
            r.end_date,
            r.reason,
            r.applied_at.strftime("%d-%m-%Y") if r.applied_at else "-",
            r.status
        ])

    return response

@login_required
def leave_report_download_pdf(request):

    # ================= FILTERS =================
    year = request.GET.get("year")
    month = request.GET.get("month")
    employee_id = request.GET.get("employee")

    # Convert safely
    year = int(year) if year else None
    month = int(month) if month else None

    # ================= QUERY =================
    leaves = LeaveRequest.objects.select_related("employee").all()

    if year:
        leaves = leaves.filter(start_date__year=year)

    if month:
        leaves = leaves.filter(start_date__month=month)

    if employee_id:
        leaves = leaves.filter(employee_id=employee_id)

    # ================= SUMMARY =================
    applied = leaves.count()
    approved = leaves.filter(status="APPROVED").count()
    pending = leaves.filter(status="PENDING").count()
    rejected = leaves.filter(status="REJECTED").count()

    # ================= TABLE =================
    headers = [
        "Employee", "Department", "Leave Type", "Days", "Start Date",
        "End Date", "Reason", "Applied Date", "Status"
    ]

    rows = [
        [
            l.employee.name,
            l.employee.department,
            l.leave_type,
            l.total_days,
            str(l.start_date),
            str(l.end_date),
            l.reason or "-",
            l.applied_at.strftime("%d %b %Y") if l.applied_at else "-",
            l.status
        ]
        for l in leaves
    ]


    # ================= EMPLOYEE NAME =================
    emp_name = None
    if employee_id:
        emp = Employee.objects.filter(id=employee_id).first()
        if emp:
            emp_name = emp.name

    # ================= RESPONSE =================

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="leave_report.pdf"'

    # ================= PDF =================
    return render_pdf_report(
        response,
        title="Leave Report",
        summary_labels=["Applied", "Approved", "Pending", "Rejected"],
        summary_values=[applied, approved, pending, rejected],
        table_title="Leave Details",
        table_headers=headers,
        table_rows=rows,
        month=month,          # ✅ now defined
        year=year,            # ✅ now defined
        employee_name=emp_name
    )

@login_required
def my_leave_balance(request):
    employee = get_object_or_404(Employee, user=request.user)
    qs = LeaveRequest.objects.filter(employee=employee)

    # status counts
    total = qs.count()
    approved = qs.filter(status="APPROVED").count()
    pending = qs.filter(status="PENDING").count()
    rejected = qs.filter(status="REJECTED").count()

    # type counts
    sick = qs.filter(leave_type="SICK").count()
    casual = qs.filter(leave_type="CASUAL").count()
    annual = qs.filter(leave_type="ANNUAL").count()
    total = qs.filter(leave_type="TOTAL").count()

    return render(request, "leave/leave_balance.html", {
        "employee": employee,
        "viewer_role": "EMPLOYEE",
        "total": total,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "sick": sick,
        "casual": casual,
        "annual": annual,
    })

