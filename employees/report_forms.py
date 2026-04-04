from django import forms
from datetime import date

class MonthlyReportFilterForm(forms.Form):
    employee_id = forms.IntegerField(required=False)
    month = forms.IntegerField(min_value=1, max_value=12, required=False)
    year = forms.IntegerField(required=False)

    def clean(self):
        cleaned = super().clean()
        today = date.today()
        cleaned["month"] = cleaned.get("month") or today.month
        cleaned["year"] = cleaned.get("year") or today.year
        return cleaned
