from django.contrib import admin
from .models import LeaveRequest

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "employee","leave_type", "total_days","start_date", "end_date", "reason", "applied_at", "status")
    list_filter = ("status",)
    search_fields = ("employee__name", "employee__email")
