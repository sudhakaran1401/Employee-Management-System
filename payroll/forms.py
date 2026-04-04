from django import forms
from utils.basefilterform import BaseReportFilterForm
from .models import SalaryHistory
from employees.models import Employee
from django import forms

class SalaryForm(forms.ModelForm):
    class Meta:
        model = SalaryHistory
        fields = [
            "employee", "pay_month", "amt_per_day",
            "basic", "hra", "allowances",
            "pf", "tax", "other_deductions",
            "paid_date", "notes"
        ]
        widgets = {
            "amt_per_day": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "employee": forms.Select(attrs={"class": "form-select"}),
            "pay_month": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            'basic': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'hra': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'allowances': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'pf': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            "paid_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.TextInput(attrs={"class": "form-control"}),
        }

class SalaryReportForm(BaseReportFilterForm):

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    

class ExcelUploadForm(forms.Form):
    file = forms.FileField()
