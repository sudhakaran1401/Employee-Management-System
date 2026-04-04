from django import forms

from utils.basefilterform import BaseReportFilterForm
from .models import Attendance
from employees.models import Employee

class AttendanceForm(forms.ModelForm):

    class Meta:
        model = Attendance
        fields = ["date", "status", "check_in", "check_out", "notes"]

        widgets = {
            "date": forms.DateInput(attrs={"type": "date","class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "check_in": forms.TimeInput(attrs={"type": "time","class": "form-control"}),
            "check_out": forms.TimeInput(attrs={"type": "time","class": "form-control"}),
            "notes": forms.TextInput(attrs={"class": "form-control"}),
        }

class MonthlyReportForm(BaseReportFilterForm):

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )


    def __init__(self, *args, **kwargs):
        is_hr = kwargs.pop("is_hr", False)
        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if not is_hr:
            self.fields.pop("employee")

        else:
            self.fields["employee"].queryset = Employee.objects.all().order_by("name")


# 🔹 Upload Form
class UploadExcelForm(forms.Form):
    excel_file = forms.FileField()