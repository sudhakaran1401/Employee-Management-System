def _hr_or_admin(user):
     return user.is_superuser or user.groups.filter(name__in=["HR", "ADMIN"]).exists()
