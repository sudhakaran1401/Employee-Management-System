from django import forms
from utils.basefilterform import BaseReportFilterForm
from .models import LeaveRequest
from employees.models import Employee

class LeaveRequestForm(forms.ModelForm):

    LEAVE_TYPE_CHOICES = [
        ("SICK", "Sick Leave"),
        ("CASUAL", "Casual Leave"),
        ("ANNUAL", "Annual Leave"),
    ]

    leave_type = forms.ChoiceField(
        choices=LEAVE_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    
    class Meta:
        model = LeaveRequest
        fields = ["start_date", "end_date", "leave_type", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "leave_type": forms.Select(attrs={"class": "form-control"}),
            "reason": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before start date.")
        return cleaned


class LeaveReportFilterForm(BaseReportFilterForm):

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        empty_label="-------",
        widget=forms.Select(attrs={"class": "form-select"})
    )