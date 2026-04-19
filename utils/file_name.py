import calendar

def generate_filename(title, year=None, month=None, employee_name=None, ext="csv"):
    file_title = title.replace(" ", "_")

    if year:
        if month:
            month_name = calendar.month_abbr[int(month)]  # Apr
            file_title += f"_{month_name}_{year}"
        else:
            file_title += f"_{year}"

    if employee_name:
        file_title += f"_{employee_name.replace(' ', '_')}"

    return f"{file_title}.{ext}"