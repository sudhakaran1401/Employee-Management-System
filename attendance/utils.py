from attendance.models import Attendance

def can_mark_attendance(employee, date):
    
    existing = Attendance.objects.filter(
        employee=employee,
        date=date
    ).first()

    # No record → allow
    if not existing:
        return True, None

    # Empty record → allow
    if existing.status == "------":
        return True, existing

    # Already marked → block
    return False, existing.status