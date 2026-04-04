from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.post_login_redirect, name='post_login_redirect'),
    path('home/', views.home, name='home'),

    # 👤 Employee Role
    path('me/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('me/profile/', views.my_profile, name='my_profile'),
    

    # 🏢 HR / Admin Role
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/employees/', views.employee_list, name='employee_list'),
    path('hr/employees/create/', views.employee_create, name='employee_create_canonical'),
    path('hr/employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('hr/employees/<int:employee_id>/update/', views.employee_update, name='employee_update'),
    path('hr/employees/<int:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    path("hr/employee-report/", views.employee_joining_report, name="employees_joining_report"),
    path("hr/employee-chart-api/", views.employee_chart_api, name="employee_chart_api"),
    path('hr/employees/report/csv/', views.employee_download_csv, name='employee_download_csv'),
    path('hr/employees/report/pdf/', views.employee_download_pdf, name='employee_download_pdf'),
    

]

