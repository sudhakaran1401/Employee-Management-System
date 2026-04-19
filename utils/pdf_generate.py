from urllib import response

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import calendar


def render_pdf_report(response, title, month, year, employee_name, summary_labels, summary_values, table_title, table_headers, table_rows,):
    file_title = title.replace(" ", "_")

    if year:
        if month:
            month_name = calendar.month_name[int(month)]
            file_title += f"_{month_name}_{year}"
        else:
            file_title += f"_{year}"

    if employee_name:
        file_title += f"_{employee_name.replace(' ', '_')}"

    filename = f"{file_title}.pdf"

    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []

    # ================= TITLE =================
    final_title = title
    if year:
        if month:
            month_name = calendar.month_name[int(month)]
            final_title = f"{title} - {month_name} {year}"
        else:
            final_title = f"{title} - {year}"

    if employee_name:
        final_title += f" ({employee_name})"

    elements.append(Paragraph(f"<b>{final_title}</b>", styles['Title']))
    elements.append(Spacer(1, 15))

    # ================= SUMMARY =================
    elements.append(Paragraph("<b>Summary</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))

    summary_data = [
        [label, value] for label, value in zip(summary_labels, summary_values)
    ]

    table = Table(summary_data, colWidths=[150, 120])

    colors_list = [colors.green, colors.red, colors.blue, colors.orange]

    style = [
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
    ]

    for i in range(len(summary_data)):
        style.append(('BACKGROUND', (0,i), (0,i), colors_list[i % len(colors_list)]))
        style.append(('TEXTCOLOR', (0,i), (0,i), colors.white))

    table.setStyle(TableStyle(style))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # ================= PIE CHART =================
    elements.append(Paragraph("<b>Summary Chart</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))

    drawing = Drawing(400, 250)

    pie = Pie()
    pie.x = 80
    pie.y = 100
    pie.width = 140
    pie.height = 140

    pie.data = summary_values

    total = sum(summary_values) if sum(summary_values) > 0 else 1

    pie.labels = [
        f"{label} ({round((value / total) * 100, 1)}%)"
        for label, value in zip(summary_labels, summary_values)
    ]

    pie.sideLabels = True

    for i in range(len(summary_values)):
        pie.slices[i].fillColor = colors_list[i % len(colors_list)]

    drawing.add(pie)

    legend = Legend()
    legend.x = 320
    legend.y = 250

    legend.columnMaximum = 10

    legend.colorNamePairs = [
        (pie.slices[i].fillColor, summary_labels[i])
        for i in range(len(summary_labels))
    ]

    drawing.add(legend)

    elements.append(drawing)
    elements.append(Spacer(1, 0))

    # ================= TABLE =================
    elements.append(Paragraph(f"<b>{table_title}</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))

    data = [table_headers] + table_rows

    table = Table(data, repeatRows=1)

    table.setStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ])

    elements.append(table)

    doc.build(elements)
    return response