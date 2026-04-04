from django import forms
from django.conf import settings
from decimal import Decimal
from .models import SalaryHistory

class SalaryHistoryForm(forms.ModelForm):
    pay_month = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    paid_on = forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))

    # NEW: choose auto-calc or manual
    auto_calculate = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = SalaryHistory
        fields = [
            "pay_month",
            "gross_base",  # NEW
            "basic", "hra", "allowances",
            "pf", "tax", "other_deductions",
            "paid_on", "notes",
        ]
        widgets = {
            "gross_base": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Monthly gross/CTC"}),
            "basic": forms.NumberInput(attrs={"class": "form-control"}),
            "hra": forms.NumberInput(attrs={"class": "form-control"}),
            "allowances": forms.NumberInput(attrs={"class": "form-control"}),
            "pf": forms.NumberInput(attrs={"class": "form-control"}),
            "tax": forms.NumberInput(attrs={"class": "form-control"}),
            "other_deductions": forms.NumberInput(attrs={"class": "form-control"}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Notes (optional)"}),
        }

    def clean(self):
        cleaned = super().clean()
        auto = cleaned.get("auto_calculate")
        gross_base = cleaned.get("gross_base") or Decimal("0")

        if auto and gross_base > 0:
            basic_pct = Decimal(str(getattr(settings, "SALARY_BASIC_PCT", 50))) / 100
            hra_pct = Decimal(str(getattr(settings, "SALARY_HRA_PCT", 20))) / 100
            allow_pct = Decimal(str(getattr(settings, "SALARY_ALLOW_PCT", 30))) / 100

            basic = (gross_base * basic_pct).quantize(Decimal("0.01"))
            hra = (gross_base * hra_pct).quantize(Decimal("0.01"))
            allowances = (gross_base * allow_pct).quantize(Decimal("0.01"))

            cleaned["basic"] = basic
            cleaned["hra"] = hra
            cleaned["allowances"] = allowances

            # auto deductions (optional)
            pf_pct = Decimal(str(getattr(settings, "SALARY_PF_PCT", 0))) / 100
            tax_pct = Decimal(str(getattr(settings, "SALARY_TAX_PCT", 0))) / 100

            if pf_pct > 0:
                cleaned["pf"] = (basic * pf_pct).quantize(Decimal("0.01"))
            if tax_pct > 0:
                gross = basic + hra + allowances
                cleaned["tax"] = (gross * tax_pct).quantize(Decimal("0.01"))

        return cleaned
