from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    DEPT_CHOICES = [
        ("", "Select"),
        ("HR", "HR"),
        ("IT", "IT"),
        ("FIN", "Finance"),
        ("SALES", "Sales"),
        ("MKT", "Marketing"),
        ("OPS", "Operations"),
        ("SUP", "Support"),
        ("ADM", "Admin"),
        ("QA", "QA"),
        ("R&D", "R&D")
    ]
     
    DESG_CHOICES = [
        ("", "Select"),
        ("Accountant", "Accountant"),
        ("Admin Executive", "Admin Executive"),
        ("Auditor", "Auditor"),
        ("Backend Developer", "Backend Developer"),
        ("Business Development Executive (BDE)", "Business Development Executive (BDE)"),
        ("Business Development Manager (BDM)", "Business Development Manager (BDM)"),
        ("CEO (Chief Executive Officer)", "CEO (Chief Executive Officer)"),
        ("CFO (Chief Financial Officer)", "CFO (Chief Financial Officer)"),
        ("COO (Chief Operating Officer)", "COO (Chief Operating Officer)"),
        ("CTO (Chief Technology Officer)", "CTO (Chief Technology Officer)"),
        ("Customer Service Representative", "Customer Service Representative"),
        ("Data Analyst", "Data Analyst"),
        ("Data Scientist", "Data Scientist"),
        ("DevOps Engineer", "DevOps Engineer"),
        ("Digital Marketing Executive", "Digital Marketing Executive"),
        ("Director", "Director"),
        ("Finance Executive", "Finance Executive"),
        ("Finance Manager", "Finance Manager"),
        ("Frontend Developer", "Frontend Developer"),
        ("Full Stack Developer", "Full Stack Developer"),
        ("General Manager", "General Manager"),
        ("Graphic Designer", "Graphic Designer"),
        ("HR Executive", "HR Executive"),
        ("HR Generalist", "HR Generalist"),
        ("HR Manager", "HR Manager"),
        ("Marketing Executive", "Marketing Executive"),
        ("Office Assistant", "Office Assistant"),
        ("Office Manager", "Office Manager"),
        ("Operations Executive", "Operations Executive"),
        ("Operations Manager", "Operations Manager"),
        ("Process Coordinator", "Process Coordinator"),
        ("Product Manager", "Product Manager"),
        ("Project Manager", "Project Manager"),
        ("Python Developer", "Python Developer"),
        ("QA Analyst", "QA Analyst"),
        ("QA Engineer", "QA Engineer"),
        ("Recruiter", "Recruiter"),
        ("Sales Executive", "Sales Executive"),
        ("Sales Manager", "Sales Manager"),
        ("SEO Specialist", "SEO Specialist"),
        ("Social Media Manager", "Social Media Manager"),
        ("Software Engineer", "Software Engineer"),
        ("Support Executive", "Support Executive"),
        ("System Administrator", "System Administrator"),
        ("Talent Acquisition Specialist", "Talent Acquisition Specialist"),
        ("Technical Support Engineer", "Technical Support Engineer"),
        ("UI/UX Designer", "UI/UX Designer")
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=120, choices=DESG_CHOICES, default="Select")
    department = models.CharField(max_length=20, choices=DEPT_CHOICES, default="Select")
    joining_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to="employees/photos/", blank=True, null=True)
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    #salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.department})"


class EmployeeProfile(models.Model):
    """
    Links Django auth User to Employee record.
    Used for employee self-dashboard.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile")
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="profile")

    def __str__(self):
        return f"{self.user.username} -> {self.employee.name}"
