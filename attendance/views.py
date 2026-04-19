import calendar
import csv
from calendar import monthrange
from collections import Counter
from datetime import date, timedelta
from types import SimpleNamespace
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from reportlab.lib.pagesizes import A4
from attendance.forms import AttendanceForm, MonthlyReportForm
from attendance.models import Attendance
from attendance.utils import can_mark_attendance
from employees.models import Employee, EmployeeProfile
from leave.models import LeaveRequest
from utils.filters import apply_common_filters
from utils.pdf_generate import render_pdf_report
from attendance.models import Attendance

def _hr_or_admin(user):
    return user.is_superuser or user.groups.filter(name__in=["HR", "ADMIN"]).exists()

def _employee_only(user):
    return user.groups.filter(name="EMPLOYEE").exists()


@login_required
def daily_calendar(request, employee_id=None):
    is_hr = _hr_or_admin(request.user)

    employees = []
    if is_hr:
        employees = Employee.objects.all().order_by("name")

    return render(
        request,
        "attendance/attendance_calendar.html",
        {
            "is_hr": is_hr,
            "employees": employees,
        },
    )

def get_filtered_attendance_queryset(request, user):
    qs = Attendance.objects.all()

    year = request.GET.get("year") or None
    month = request.GET.get("month")
    employee = request.GET.get("employee") or None

    # Normalize month
    if month in ["", None, "0"]:
        month = None

    # Apply filters
    if year:
        try:
            qs = qs.filter(date__year=int(year))
        except ValueError:
            pass

    if month:
        try:
            qs = qs.filter(date__month=int(month))
        except ValueError:
            pass

    # Role-based employee filtering
    if _hr_or_admin(user):
        if employee:
            qs = qs.filter(employee_id=employee)
    else:
        profile = EmployeeProfile.objects.filter(user=user).first()
        if profile:
            qs = qs.filter(employee=profile.employee)

    return qs


@login_required
def admin_attendance_list(request):

    if not _hr_or_admin(request.user):
        return HttpResponseForbidden("Only HR/Admin allowed.")

    form = MonthlyReportForm(
        request.GET or None,
        is_hr=True,
        user=request.user
    )

    rows = get_filtered_attendance_queryset(request, request.user).order_by("-date")

    context = {
        "form": form,
        "rows": rows,
        "filter_applied": any([
            request.GET.get("year"),
            request.GET.get("month") not in ["", None, "0"],
            request.GET.get("employee")
        ])
    }

    return render(request, "attendance/admin_attendance_list.html", context)

@login_required
def mark_attendance(request, employee_id=None):

    is_employee_mode = "/me/" in request.path

    profile = EmployeeProfile.objects.filter(user=request.user).first()

    if not profile or not profile.employee:
        return HttpResponseForbidden("Employee profile not linked.")

    emp = profile.employee
    message = None 

    if is_employee_mode:
        employee = emp
        employees = None
    else:
        if request.user.is_staff:
            if employee_id:
                employee = get_object_or_404(Employee, id=employee_id)
            else:
                employee = None
            employees = Employee.objects.all()
        else:
            employee = emp
            employees = None

    form = AttendanceForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            attendance = form.save(commit=False)

            if is_employee_mode:
                attendance.employee = emp
            else:
                selected_employee_id = request.POST.get("employee")
                attendance.employee = get_object_or_404(Employee, id=selected_employee_id)

           
            allowed, data = can_mark_attendance(attendance.employee, attendance.date)

            if not allowed:
                message = {
                    "type": "error",
                    "text": f"Attendance already marked as {data}"
                }

            else:
                if data:
                    data.status = attendance.status
                    data.check_in = attendance.check_in
                    data.check_out = attendance.check_out
                    data.save()
                else:
                    attendance.save()

                message = {
                    "type": "success",
                    "text": "Attendance marked successfully!"
                }

                form = AttendanceForm()

        else:

            error_text = None
            for errors in form.errors.values():
                for error in errors:
                    error_text = error
                    break
                if error_text:
                    break

            message = {
                "type": "danger",
                "text": error_text or "Invalid form data"
            }

    return render(request, "attendance/mark_attendance.html", {
        "form": form,
        "employees": employees,
        "employee": employee,
        "is_employee_mode": is_employee_mode,
        "message": message 
    })

@login_required
def my_attendance(request):

    profile = EmployeeProfile.objects.filter(user=request.user).first()

    if not profile or not profile.employee:
        return HttpResponseForbidden("Employee profile not linked.")

    records = Attendance.objects.filter(
        employee=profile.employee
    ).order_by("-date")

    return render(
        request,
        "attendance/attendance_list.html",
        {"records": records},
    )


@login_required
def attendance_list(request):

    # 🔥 Detect mode from URL
    is_employee_mode = "/me/" in request.path

    profile = EmployeeProfile.objects.filter(user=request.user).first()

    if not profile or not profile.employee:
        return HttpResponseForbidden("Employee profile not linked.")

    emp = profile.employee

    # 🔥 FIXED DATA SCOPE
    if is_employee_mode:
        # Employee mode → only own data
        records = Attendance.objects.select_related("employee").filter(
            employee=emp
        ).order_by("date")
        employees = [emp]

    else:
        # HR mode
        if request.user.is_superuser or request.user.groups.filter(name__in=["HR", "ADMIN"]).exists():
            records = Attendance.objects.select_related("employee").all().order_by("date")
            employees = Employee.objects.all()
        else:
            records = Attendance.objects.select_related("employee").filter(
                employee=emp
            ).order_by("date")
            employees = [emp]

    # 🔁 Existing logic (unchanged)
    final_records = []

    if records.exists():
        start_date = records.first().date
        end_date = records.last().date

        current = start_date

        while current <= end_date:
            for e in employees:

                attendance = records.filter(employee=e, date=current).first()

                if attendance:
                    final_records.append(SimpleNamespace(
                        employee=attendance.employee,
                        date=attendance.date,
                        status=attendance.status,
                        check_in=attendance.check_in,
                        check_out=attendance.check_out,
                        remarks=getattr(attendance, "remarks", None)
                    ))
                else:
                    leave = LeaveRequest.objects.filter(
                        employee=e,
                        status="APPROVED",
                        start_date__lte=current,
                        end_date__gte=current
                    ).first()

                    if leave:
                        final_records.append(SimpleNamespace(
                            employee=e,
                            date=current,
                            status="Leave",
                            check_in=None,
                            check_out=None,
                            remarks=f"{leave.leave_type} LEAVE"
                        ))

            current += timedelta(days=1)

    final_records = final_records[::-1]

    return render(request, "attendance/attendance_list.html", {
        "attendance_records": final_records,
        "page_obj": final_records,
        "viewer_role": "HR" if (not is_employee_mode and (
            request.user.is_superuser or request.user.groups.filter(name__in=["HR", "ADMIN"]).exists()
        )) else "EMP"
    })

def _get_monthly_attendance_stats(user, year=None, month=None, employee_id=None):

    qs = Attendance.objects.all()

    if year:
        try:
            qs = qs.filter(date__year=int(year))
        except ValueError:
            pass

    if month:
        try:
            qs = qs.filter(date__month=int(month))
        except ValueError:
            pass

    employee = None

    # HR/Admin
    if _hr_or_admin(user):
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
            employee = Employee.objects.filter(id=employee_id).first()

    else:
        profile = EmployeeProfile.objects.filter(user=user).first()
        if profile:
            employee = profile.employee
            qs = qs.filter(employee=employee)

    present = qs.filter(status="Present").count()
    holiday = qs.filter(status="Holiday").count()

    leave_days = 0

    if employee and year and month:
        year = int(year)
        month = int(month)

        month_start = date(year, month, 1)
        month_end = date(year, month, calendar.monthrange(year, month)[1])

        leaves = LeaveRequest.objects.filter(
            employee=employee,
            status="APPROVED",
            start_date__lte=month_end,
            end_date__gte=month_start
        )

        for leave in leaves:
            start = max(leave.start_date, month_start)
            end = min(leave.end_date, month_end)
            leave_days += (end - start).days + 1

    stats = {
        "Present": present,
        "Leave": leave_days,
        "Holiday": holiday
    }

    return qs, stats


def generate_processed_records(user, records, is_hr, start_date, end_date):

    if is_hr:
        employees = Employee.objects.all()
    else:
        profile = EmployeeProfile.objects.filter(user=user).first()
        employees = [profile.employee] if profile else []

    processed_records = []
    current = start_date

    while current <= end_date:
        for emp in employees:

            attendance = records.filter(employee=emp, date=current).first()

            if attendance:
                processed_records.append(SimpleNamespace(
                    employee=attendance.employee,
                    date=attendance.date,
                    status=attendance.status,
                    check_in=attendance.check_in,
                    check_out=attendance.check_out,
                    notes=getattr(attendance, "remarks", None)
                ))
            else:
                leave_exists = LeaveRequest.objects.filter(
                    employee=emp,
                    status="APPROVED",
                    start_date__lte=current,
                    end_date__gte=current
                ).exists()

                if leave_exists:
                    processed_records.append(SimpleNamespace(
                        employee=emp,
                        date=current,
                        status="Leave",
                        check_in=None,
                        check_out=None,
                        notes="On Leave"
                    ))
                else:
                    continue  

        current += timedelta(days=1)

    return processed_records

@login_required
def attendance_report(request):

    is_hr = _hr_or_admin(request.user)

    form = MonthlyReportForm(request.GET or None, is_hr=is_hr, user=request.user)

    year = request.GET.get("year")
    month = request.GET.get("month")
    employee_id = request.GET.get("employee")

    records, _ = _get_monthly_attendance_stats(
        request.user, year, month, employee_id
    )

    processed_records = []

    if year or month:

        year = int(year) if year else date.today().year
        month = int(month) if month else None

        if month:
            start_date = date(year, month, 1)
            end_date = date(year, month, monthrange(year, month)[1])
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        if is_hr:
            if employee_id:
                employees = Employee.objects.filter(id=employee_id)  # ✅ FIX
            else:
                employees = Employee.objects.all()
        else:
            profile = EmployeeProfile.objects.filter(user=request.user).first()
            employees = [profile.employee] if profile else []

        current = start_date

        while current <= end_date:
            for emp in employees:

                attendance = records.filter(employee=emp, date=current).first()

                if attendance:
                    processed_records.append(attendance)
                else:
                    leave_exists = LeaveRequest.objects.filter(
                        employee=emp,
                        status="APPROVED",
                        start_date__lte=current,
                        end_date__gte=current
                    ).exists()

                    if leave_exists:
                        processed_records.append(SimpleNamespace(
                            employee=emp,
                            date=current,
                            status="Leave",
                            check_in=None,
                            check_out=None,
                            remarks="On Leave"
                        ))

            current += timedelta(days=1)

    counter = Counter([r.status for r in processed_records])

    stats = {
        "Present": counter.get("Present", 0),
        "Leave": counter.get("Leave", 0),
        "Holiday": counter.get("Holiday", 0),
    }

    return render(request, "attendance/attendance_report.html", {
        "form": form,
        "records": processed_records,
        "page_obj": processed_records,  # ✅ important
        "stats": stats,
        "is_hr": is_hr,
        "filter_applied": any([year, month, employee_id]),
        "csv_download_url": reverse("attendance_download_csv"),
        "pdf_download_url": reverse("attendance_download_pdf"),
    })

@login_required
def attendance_status_chart(request):

    year = request.GET.get("year")
    month = request.GET.get("month")
    employee_id = request.GET.get("employee")

    if not (year or month):
        return JsonResponse({"data": [0, 0, 0]})

    year = int(year) if year else date.today().year
    month = int(month) if month else None

    records, _ = _get_monthly_attendance_stats(
        request.user, year, month, employee_id
    )

    is_hr = _hr_or_admin(request.user)

    # employee scope
    if is_hr:
        if employee_id:
            employees = Employee.objects.filter(id=employee_id)  # ✅ FIX
        else:
            employees = Employee.objects.all()
    else:
        profile = EmployeeProfile.objects.filter(user=request.user).first()
        employees = [profile.employee] if profile else []

    # date range
    if month:
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

    processed_records = []
    current = start_date

    while current <= end_date:
        for emp in employees:

            attendance = records.filter(employee=emp, date=current).first()

            if attendance:
                processed_records.append(attendance)

            else:
                leave_exists = LeaveRequest.objects.filter(
                    employee=emp,
                    status="APPROVED",
                    start_date__lte=current,
                    end_date__gte=current
                ).exists()

                if leave_exists:
                    processed_records.append(SimpleNamespace(
                        status="Leave"
                    ))

        current += timedelta(days=1)

    counter = Counter([r.status for r in processed_records])

    return JsonResponse({
        "data": [
            counter.get("Present", 0),
            counter.get("Leave", 0),
            counter.get("Holiday", 0)
        ]
    })

@login_required
def attendance_events(request):

    profile = EmployeeProfile.objects.filter(user=request.user).first()

    if not profile:
        return JsonResponse([], safe=False)

    employee = profile.employee

    attendance_records = Attendance.objects.filter(employee=employee)

    leave_records = LeaveRequest.objects.filter(
        employee=employee,
        status="APPROVED"
    )

    events = []

    for r in attendance_records:

        if r.status == "Present":
            color = "#28a745"
        #elif r.status == "Absent":
        #    color = "#ffc107"
        elif r.status == "Leave":
            color = "#dc3545"
        else:
            color = "#007bff"

        events.append({
            "title": f"{employee.name} - {r.status}",
            "start": r.date.strftime("%Y-%m-%d"),
            "color": color
        })

    for leave in leave_records:

        current = leave.start_date

        while current <= leave.end_date:

            events.append({
                "title": f"{employee.name} - {leave.leave_type}",
                "start": current.strftime("%Y-%m-%d"),
                "color": "#dc3545"
            })

            current += timedelta(days=1)

    return JsonResponse(events, safe=False)

@login_required
def attendance_download_csv(request):

    year = request.GET.get("year")
    month = request.GET.get("month")
    employee_id = request.GET.get("employee")

    records, _ = _get_monthly_attendance_stats(
        request.user, year, month, employee_id
    )

    year = int(year) if year else date.today().year
    month = int(month) if month else None

    if month:
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

    if _hr_or_admin(request.user):
        if employee_id:
            employees = Employee.objects.filter(id=employee_id)
        else:
            employees = Employee.objects.all()
    else:
        profile = EmployeeProfile.objects.filter(user=request.user).first()
        employees = [profile.employee] if profile else []

    processed_records = []
    current = start_date

    while current <= end_date:
        for emp in employees:

            attendance = records.filter(employee=emp, date=current).first()

            if attendance:
                processed_records.append(attendance)
            else:
                leave_obj = LeaveRequest.objects.filter(
                    employee=emp,
                    status="APPROVED",
                    start_date__lte=current,
                    end_date__gte=current
                ).first()

                if leave_obj:
                    processed_records.append(SimpleNamespace(
                        employee=emp,
                        date=current,
                        status="Leave",
                        check_in=None,
                        check_out=None,
                        remarks=leave_obj.leave_type
                    ))

        current += timedelta(days=1)

    
    response = HttpResponse(content_type='text/csv')

    title = "Attendance Report"

    file_title = title.replace(" ", "_")

    if year:
        if month:
            month_name = calendar.month_name[int(month)]
            file_title += f"_{month_name}_{year}"
        else:
            file_title += f"_{year}"

    # Employee name (if selected)
    employee_name = None
    if employee_id:
        emp_obj = Employee.objects.filter(id=employee_id).first()
        if emp_obj:
            employee_name = emp_obj.name
            file_title += f"_{employee_name.replace(' ', '_')}"

    filename = f"{file_title}.csv"

    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    writer.writerow([
        "Employee", "Department", "Date", "Status", "Check-in", "Check-out", "Notes"
    ])

    for r in processed_records:
        writer.writerow([
            r.employee.name,
            r.employee.department,
            r.date,
            r.status,
            r.check_in if r.check_in else "-",
            r.check_out if r.check_out else "-",
            getattr(r, "remarks", "-")
        ])

    return response

@login_required
def attendance_download_pdf(request):

    year = request.GET.get("year")
    month = request.GET.get("month")
    employee_id = request.GET.get("employee")

    records, _ = _get_monthly_attendance_stats(
        request.user, year, month, employee_id
    )

    year = int(year) if year else date.today().year
    month = int(month) if month else None

    if month:
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

    if _hr_or_admin(request.user):
        if employee_id:
            employees = Employee.objects.filter(id=employee_id)
        else:
            employees = Employee.objects.all()
    else:
        profile = EmployeeProfile.objects.filter(user=request.user).first()
        employees = [profile.employee] if profile else []
    
    emp_name = None
    if employee_id:
        emp = Employee.objects.filter(id=employee_id).first()
        if emp:
            emp_name = emp.name

    processed_records = []
    current = start_date

    while current <= end_date:
        for emp in employees:

            attendance = records.filter(employee=emp, date=current).first()

            if attendance:
                processed_records.append(attendance)
            else:
                leave_exists = LeaveRequest.objects.filter(
                    employee=emp,
                    status="APPROVED",
                    start_date__lte=current,
                    end_date__gte=current
                ).first()

                if leave_exists:
                    processed_records.append(SimpleNamespace(
                        employee=emp,
                        date=current,
                        status="Leave",
                        check_in=None,
                        check_out=None,
                        remarks=leave_exists.leave_type
                    ))

        current += timedelta(days=1)

    present = 0
    leave = 0
    holiday = 0

    for r in processed_records:
        if r.status == "Present":
            present += 1
        elif r.status == "Leave":
            leave += 1
        elif r.status == "Holiday":
            holiday += 1

    headers = [
        "Employee", "Department", "Date",
        "Status", "Check-in", "Check-out", "Notes"
    ]

    rows = [
        [
            r.employee.name,
            r.employee.department,
            str(r.date),
            r.status,
            str(r.check_in) if r.check_in else "-",
            str(r.check_out) if r.check_out else "-",
            getattr(r, "remarks", "-")
        ]
        for r in processed_records
    ]
 
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'

    return render_pdf_report(
        response,
        title="Attendance Report",
        summary_labels=["Present", "Leave", "Holiday"],
        summary_values=[present, leave, holiday],
        table_title="Attendance Details",
        table_headers=headers,
        table_rows=rows,
        month=month,
        year=year,
        employee_name=emp_name if emp_name else None
    )