from django import forms

from utils.basefilterform import BaseReportFilterForm
from .models import Employee


class EmployeeForm(forms.ModelForm):
    joining_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    # Template-compat fields (not stored in DB in current model)
    dob = forms.DateField(required=True, widget=forms.DateInput(attrs={"type": "date"}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    salary = forms.DecimalField(required=False, min_value=0)

    class Meta:
        model = Employee
        fields = [
            "name",
            "email",
            "phone",
            "designation",
            "department",
            "joining_date",
            "photo",
            "dob",
            "address",
            "salary",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
            "dob": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone"}),
            "designation": forms.Select(attrs={"class": "form-select", "placeholder": "Designation"}),
            "department": forms.Select(attrs={"class": "form-select", "placeholder": "Department"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style form-only fields to match the Bootstrap look used by templates.
        self.fields["dob"].widget.attrs.update({"class": "form-control"})
        self.fields["address"].widget.attrs.update({"class": "form-control", "placeholder": "Address"})
        self.fields["salary"].widget.attrs.update({"class": "form-control", "placeholder": "Salary"})

    def save(self, commit=True):
        # Save only Employee model fields. Extra fields are intentionally ignored
        # to keep the existing DB/model structure unchanged.
        return super().save(commit=commit)


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        # Import locally to avoid import-time errors if leave app loads later.
        from leave.models import LeaveRequest

        model = LeaveRequest
        fields = ["start_date", "end_date", "reason"]

class EmployeeReportFilterForm(BaseReportFilterForm):
    pass

class UploadEmployeeExcelForm(forms.Form):
    file = forms.FileField(label="Upload Excel File")