
def apply_common_filters(qs, request, date_field):
    month = request.GET.get("month")
    year = request.GET.get("year")
    employee = request.GET.get("employee")

    if month:
        qs = qs.filter(**{f"{date_field}__month": month})

    if year:
        qs = qs.filter(**{f"{date_field}__year": year})

    if employee:
        qs = qs.filter(employee_id=employee)

    return qs