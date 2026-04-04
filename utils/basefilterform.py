import calendar
from django import forms
from datetime import datetime

class BaseReportFilterForm(forms.Form):

    MONTH_CHOICES = [
        ("", "-------")
    ] + [(i, calendar.month_name[i]) for i in range(1, 13)]

    CURRENT_YEAR = datetime.now().year

    YEAR_CHOICES = [
        ("", "-------")
    ] + [(y, y) for y in range(2020, CURRENT_YEAR + 2)]

    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )