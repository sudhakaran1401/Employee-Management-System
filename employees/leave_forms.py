from django import forms
from .models import LeaveBalance

class LeaveBalanceForm(forms.ModelForm):
    class Meta:
        model = LeaveBalance
        fields = ["year", "annual_leaves", "used_leaves"]
        widgets = {
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "annual_leaves": forms.NumberInput(attrs={"class": "form-control"}),
            "used_leaves": forms.NumberInput(attrs={"class": "form-control"}),
        }
