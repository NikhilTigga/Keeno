from django.db import models
from django.utils import timezone

class AdminRoles(models.Model):
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name

class AdminLogin(models.Model):
    roles =models.ForeignKey(AdminRoles,on_delete = models.CASCADE , null = True , blank=True)
    email = models.EmailField(
        max_length=254,
        unique=True
    )
    password = models.CharField(
        max_length=128
    )
    def __str__(self):
        return self.email