def is_admin(user):
    return user.is_superuser or user.groups.filter(name="ADMIN").exists()

def is_hr(user):
    return user.groups.filter(name="HR").exists()

def is_employee(user):
    return user.groups.filter(name="EMPLOYEE").exists()
