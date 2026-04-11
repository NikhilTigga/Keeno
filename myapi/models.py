from django.db import models
from django.utils import timezone
# Create your models here.



class UserRegister(models.Model):
    name =models.CharField(max_length=150)
    profile_image=models.ImageField(upload_to='user_profile/',blank=True,null=True)
    email =models.EmailField(max_length=254, unique=True)
    phone_no =models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=128)
    latitude=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    longitude=models.DecimalField(max_digits=9,decimal_places=6, null=True,blank=True)
    createdAt=models.DateTimeField(auto_now_add=True,null=True,blank=True)
    
    def __str__(self):
        return self.email
    
# class UserCart(models.Model):
#     user = models.OneToOneField(
#         UserRegister,
#         on_delete=models.CASCADE,
#         related_name="cart"
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )
#     def __str__(self):
#         return f"{self.user.email}'s Cart"
    

class userOTP(models.Model):
    user=models.ForeignKey(UserRegister,on_delete=models.CASCADE)
    otp=models.CharField(max_length=4)
    created_at=models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    
    def __str__ (self):
        return f"{self.user.email}-{self.otp}"
    


