from django.urls import path
from . import views

urlpatterns = [
  
    path('me/my-attendance/', views.my_attendance, name='my_attendance'),
    path('me/calendar/', views.daily_calendar, name='attendance_calendar'),
    path('me/mark-attendance/', views.mark_attendance, name='mark_attendance_by_employee'),
    path('me/attendance-history/', views.attendance_list, name='attendance_history'),
    path('me/monthly-report/', views.attendance_report, name='attendance_report_employee'),
    path('me/calendar/events/', views.attendance_events, name='attendance_events'),

    # 🏢 HR / Admin
    path('hr/list/', views.attendance_list, name='attendance_list'),
    path('hr/mark/', views.mark_attendance, name='mark_attendance'),
    path('hr/employees/<int:employee_id>/mark/', views.mark_attendance, name='mark_attendance_by_hr'),
    path('hr/monthly-report/', views.attendance_report, name='attendance_report'),
    path("hr/monthly-report/download/csv/", views.attendance_download_csv, name="attendance_download_csv"),
    path("hr/monthly-report/download/pdf/", views.attendance_download_pdf, name="attendance_download_pdf"),
    path('hr/monthly-chart/', views.attendance_status_chart, name='attendance_status_chart'),
    
]
