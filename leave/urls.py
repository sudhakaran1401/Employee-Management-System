from django.urls import include, path
from . import views

urlpatterns = [

    path('me/apply/', views.apply_leave, name='apply_leave'),
    path('me/update/<int:leave_id>/', views.update_leave, name='update_leave'),
    path('me/my-requests/', views.my_leave_requests, name='my_leave_requests'),
    path('me/balance/', views.leave_balance, name='leave_balance'),
    path('me/leave-balance/', views.my_leave_balance, name='my_leave_balance'),
    # 🏢 HR / Admin
    path('hr/approve/<int:pk>/', views.approve_leave, name='approve_leave'),
    path('hr/reject/<int:pk>/', views.reject_leave, name='reject_leave'),
    path('hr/employees/<int:employee_id>/leave-requests/', views.pending_leave_requests, name='hr_employee_leave_requests'),
    path('hr/employees/<int:employee_id>/leave-balance/', views.leave_balance_by_employee, name='leave_balance_by_employee'),
    path('hr/all-leave-requests/', views.hr_all_leave_requests, name='hr_all_leave_requests'),
    path('hr/leave-report/', views.leave_report, name='leave_report'),
    path("hr/leave-report/download/csv/", views.leave_report_download_csv, name="leave_report_download_csv"),
    path("hr/leave-report/download/pdf/", views.leave_report_download_pdf, name="leave_report_download_pdf"),

   
]
      

