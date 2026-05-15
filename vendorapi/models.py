from django.db import models
from django.utils import timezone
from myapp.models import AdminLogin
from myapi.models import *
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Create your models here.

class VendorRegistration(models.Model):
    name = models.CharField(max_length=255)
    profile_img = models.ImageField(upload_to='vendor_profile/', blank=True, null=True)

    email = models.EmailField(unique=True)

    phoneno = models.CharField(max_length=15, unique=True)

    password = models.CharField(max_length=255)

    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class VendorOTP(models.Model):

    vendor = models.ForeignKey(VendorRegistration, on_delete=models.CASCADE)

    otp = models.CharField(max_length=4)

    created_at = models.DateTimeField(default=timezone.now)

    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.vendor.email} - {self.otp}"
    
class Restaurant(models.Model):
    vendorid = models.ForeignKey(
        VendorRegistration,
        on_delete=models.CASCADE,
        related_name="restaurants"
    )
    ownername = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    restaurantname = models.CharField(max_length=255)
    # store multiple images in JSON format
    restaurantimage = models.JSONField(
        default=list,
        blank=True,
        null=True
    )
    adderess = models.TextField()
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    
    is_open = models.BooleanField(default=False)
    
    is_veg = models.BooleanField(default=False)
    approveStatus = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected")
        ],
        default="pending"
    )
    approvedby = models.ForeignKey(AdminLogin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NEW FIELD: Cuisine
    cuisine = models.JSONField(
        default=list,
        blank=True,
        help_text="Example: ['Indian', 'Chinese', 'Fast Food']"
    )
    
    # NEW FIELD: Restaurant Since
    since = models.DateField(
        null=True,
        blank=True,
        help_text="Restaurant establishment date"
    )
    
    # NEW FIELD: GST
    gst_number = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    
    # NEW FIELD: FSSAI
    fssai_license_no = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    
    # NEW FIELD: Business Hours (Monday–Sunday)
    business_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Example:
        {
            "monday": "9:00 AM - 10:00 PM",
            "tuesday": "9:00 AM - 10:00 PM",
            "wednesday": "9:00 AM - 10:00 PM",
            "thursday": "9:00 AM - 10:00 PM",
            "friday": "9:00 AM - 11:00 PM",
            "saturday": "9:00 AM - 11:00 PM",
            "sunday": "10:00 AM - 10:00 PM"
        }
        """
    )
    
    # NEW FIELD: Bank Details
    bank_name = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    account_number = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    ifsc_code = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    upi_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    

    def __str__(self):
        return self.restaurantname

class GlobalCategory(models.Model):

    catgname = models.CharField(max_length=255)

    created_at = models.DateTimeField(default=timezone.now)
    
    images = models.JSONField(   # 🔥 added field
        default=list,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.catgname

    class Meta:
        db_table = "globalCategory"
        ordering = ["-created_at"]
        
class Categories(models.Model):
    categories_name = models.CharField(max_length=255)
    restaurant=models.ForeignKey(Restaurant,on_delete=models.CASCADE,related_name="categories")
    GlobalCategory = models.ForeignKey(GlobalCategory,on_delete=models.CASCADE,related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True)
    category_images = models.JSONField(
        default=list,
        blank=True,
        null=True
    )
    
    def __str__(self):
        return self.categories_name
    
class Spotlight(models.Model):
    spotlight_name =models.CharField(max_length=255)
    spotlight_img = models.JSONField(
        
        default=list,
        blank=True,
        null=True,
    ) 
    
    created_at =models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.spotlight_name
    
    
class FeaturedCategory(models.Model):
    
    category_name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name

    class Meta:
        db_table = "featured_categories"
        ordering = ["-created_at"]
        

class MenuItems(models.Model):

    VEG_CHOICES = (
        ("Veg", "Veg"),
        ("NonVeg", "NonVeg"),
    )

    restaurant = models.ForeignKey(
        "Restaurant",   # your existing Restaurant model
        on_delete=models.CASCADE,
        related_name="menu_items"
    )
    
    categories =models.ForeignKey(
       Categories, on_delete=models.CASCADE, related_name="menu_items", null=True, blank=True
    )

    globalCategory = models.ForeignKey(
        GlobalCategory,
        on_delete=models.CASCADE,
        null=True,
        related_name="menu_items"
    )
    
    featured_category = models.ForeignKey(
        FeaturedCategory,
        on_delete=models.SET_NULL,   # better than CASCADE here
        null=True,
        blank=True,
        related_name="menu_items"
    )
    
    spotlight =models.ForeignKey(
        Spotlight,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spotlight"
    )

    name = models.CharField(max_length=255)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    
    price_afterDesc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True)
    
    menu_images = models.JSONField(
        default=list,
        blank=True,
        null=True
    )

    is_available = models.BooleanField(default=True)

    VegNonVeg = models.CharField(
        max_length=10,
        choices=VEG_CHOICES
    )
    halal_attribute = models.CharField(max_length=20, null=True)
    sypicy = models.BooleanField(default=False)
    prep_time = models.PositiveIntegerField(help_text="Time in minutes", null=True)
    
    discount = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Discount in percentage (e.g., 10 for 10%)"
    )

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    
    def get_prep_time_display(self):
        if self.prep_time < 60:
            return f"{self.prep_time} min"
        else:
            return f"{self.prep_time // 60} hr"

    def get_discount_display(self):
        if self.discount:
            return f"{self.discount}%"
        return "No Discount"

    def __str__(self):
        return self.name

    class Meta:
        db_table = "menu_items"
        ordering = ["-created_at"]
        
        
class MenuRating(models.Model):

    user = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name="menu_ratings"
    )

    menu_item = models.ForeignKey(
        MenuItems,
        on_delete=models.CASCADE,
        related_name="ratings"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "menu_rating"
        ordering = ["-created_at"]
        unique_together = ("user", "menu_item")  # 🚀 prevents duplicate rating

    def __str__(self):
        return f"{self.user.email} - {self.menu_item.name} ({self.rating})"
    
class RestaurantRating(models.Model):

    user = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name="restaurant_ratings"
    )

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="ratings"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "restaurant_rating"   # ✅ fixed
        ordering = ["-created_at"]
        unique_together = ("user", "restaurant")   # ✅ fixed

    def __str__(self):
        return f"{self.user.email} - {self.restaurant.name} ({self.rating})"  # ✅ fixed
    
    
class UserCart(models.Model):
    user = models.OneToOneField(
        UserRegister,
        on_delete=models.CASCADE,
        related_name="cart"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    def __str__(self):
        return f"{self.user.email}'s Cart"
    
    
class MenuItemPortion(models.Model):
    menu_item = models.ForeignKey(MenuItems, on_delete=models.CASCADE, related_name="portions")
    portion_name = models.CharField(max_length=50)  # Half / Full
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    
class AddOn(models.Model):
    menu_item = models.ForeignKey(MenuItems, on_delete=models.CASCADE, related_name="addons")
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="addons/", null=True, blank=True)
    is_available = models.BooleanField(default=True)
    
class DeliveryPartnerForm(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    VEHICLE_TYPE_CHOICES = (
        ("bike", "Bike"),
        ("scooter", "Scooter"),
        ("cycle", "Cycle"),
        ("car", "Car"),
    )

    # Personal Details
    full_name = models.CharField(max_length=150 , null=True)

    email = models.EmailField( null=True, unique=True)

    phone_number = models.CharField(max_length=15 , null=True)

    city = models.CharField(max_length=100, null=True)

    referral_code = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    # Documents
    profile_image = models.JSONField(
        
        null=True,
        blank=True
    )

    aadhar_card = models.JSONField(
        
        null=True,
        blank=True
    )

    driving_license = models.JSONField(
       
        null=True,
        blank=True
    )

    vehicle_rc_certificate = models.JSONField(
        
        null=True,
        blank=True
    )

    vehicle_image = models.JSONField(
        
        null=True,
        blank=True
    )

    # Vehicle Details
    vehicle_number = models.CharField(max_length=20)

    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES, null=True
    )

    vehicle_model = models.CharField(max_length=100 , null=True)

    vehicle_color = models.CharField(max_length=50 , null=True)

    manufacturing_year = models.IntegerField( null=True)

    # Bank Details
    account_holder_name = models.CharField(max_length=150 , null=True)

    account_number = models.CharField(max_length=30 , null=True)
    
    bank_name=models.CharField(max_length=100,null=True)
    
    branch_name=models.CharField(max_length=100,null=True)

    ifsc_code = models.CharField(max_length=20 , null=True)
    
    deliver_partnerid=models.CharField(max_length=100, unique=True,null=True)
    
    password = models.CharField(max_length=255, null=True)

    # Approval Status
    approval_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    
    # New Location Fields
    address = models.TextField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    WORK_STATUS_CHOICES = (
    ("offline", "Offline"),
    ("online", "Online"),
   
     )
    work_status = models.CharField(
    max_length=20,
    choices=WORK_STATUS_CHOICES,
    default="offline"
    )
    daily_order_target = models.IntegerField(
    default=10,
    
    help_text="Number of orders partner should complete per day"
     )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - Delivery Partner Form"

    class Meta:
        db_table = "delivery_partner_form"
        ordering = ["-created_at"]
        
            
class Orders(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("preparing", "Preparing"),
        ("out_for_delivery", "Out For Delivery"),
        ("delivered", "Delivered"),
        ("ready","Ready"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )
    
    delivery_partner = models.ForeignKey(
    DeliveryPartnerForm,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="assigned_orders"
    )
    
    order_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
       
    )
    # ⭐ NEW FIELD
    order_otp = models.CharField(
        max_length=4,
        null=True
    )
    
    delivery_otp = models.CharField(
        max_length=4,null=True
    )
    
    paid_amount = models.DecimalField(
    max_digits=10,
    decimal_places=2, null=True
      )
    delivery_address = models.TextField(
        null=True,
        blank=True
    )
    
    order_suggestion=models.TextField(blank=True)
    coupon_code = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    
    delivered_time = models.DateTimeField(
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"
    

    
class CartItems(models.Model):

    order = models.ForeignKey(
        Orders,
        on_delete=models.CASCADE,
        related_name="items",null=True
    )

    cart = models.ForeignKey(
        UserCart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    menu_item = models.ForeignKey(
        MenuItems,
        on_delete=models.CASCADE,
        related_name="order_items"
    )

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="order_items"
    )

    quantity = models.PositiveIntegerField(default=1)

    price_at_order_time = models.DecimalField(   # VERY IMPORTANT 🔥
        max_digits=10,
        decimal_places=2
    )
    
    selectportion = models.JSONField(
        null=True,
        blank=True,
        default=dict
    )
    
    addon = models.JSONField(
        null=True,
        blank=True,
        default=list
    )

    
    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
    
class Payment(models.Model):

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    PAYMENT_MODE_CHOICES = (
        ("razorpay", "Razorpay"),
        ("google_pay", "Google Pay"),
        ("phonepe", "PhonePe"),
        ("cod", "Cash On Delivery"),
    )

    order = models.OneToOneField(   # One order = one payment
        Orders,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    transaction_no = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODE_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} - Order {self.order.id}"
    

        
class DeliveryPartnerOrderAction(models.Model):

    ACTION_CHOICES = (
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    order = models.ForeignKey(
        Orders,
        on_delete=models.CASCADE,
        related_name="delivery_actions"
    )

    delivery_partner = models.ForeignKey(
        DeliveryPartnerForm,
        on_delete=models.CASCADE,
        related_name="order_actions"
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_partner_order_action"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.delivery_partner.full_name} - {self.action} - Order {self.order.id}"
    
class AddonMaster(models.Model):

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='addons'
    )

    addon_name = models.CharField(
        max_length=255
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    addon_image = models.ImageField(
        upload_to='addon__master_images/',
        null=True,
        blank=True
    )


    is_available = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.addon_name} - {self.restaurant.name}"


class StaffProfile(models.Model):

    WORK_STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("on_leave", "On Leave"),
    )

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="staff_profiles"
    )

    vendor = models.ForeignKey(
        VendorRegistration,
        on_delete=models.CASCADE,
        related_name="staff_profiles"
    )

    staff_name = models.CharField(
        max_length=150
    )

    email = models.EmailField(
        unique=True
    )

    phone_no = models.CharField(
        max_length=15
    )

    work_days = models.CharField(
        max_length=100,
        help_text="Example: Monday-Friday"
    )

    work_time = models.CharField(
        max_length=100,
        help_text="Example: 9:00 AM - 6:00 PM"
    )

    joined_at = models.DateField(
        auto_now_add=True
    )

    work_status = models.CharField(
        max_length=20,
        choices=WORK_STATUS_CHOICES,
        default="active"
    )

    department = models.CharField(
        max_length=100
    )

    role = models.CharField(
        max_length=100
    )
    
    profile_photo = models.ImageField(
        upload_to="staff_profiles/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.staff_name} - {self.restaurant.name}"
    
    

class DeliveryPartnerRating(models.Model):
    delivery_partner = models.ForeignKey(
       DeliveryPartnerForm,
        on_delete=models.CASCADE,
        related_name="ratings"
    )

    user = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name="delivery_partner_ratings"
    )

    user_rating_out_of_5 = models.DecimalField(
        max_digits=2,
        decimal_places=1
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} rated {self.delivery_partner} - {self.user_rating_out_of_5}"
    

class SetOrderIncentive(models.Model):

    more_than_order = models.IntegerField(help_text="km")

    incentive_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Orders > {self.more_than_order} : Incentive {self.incentive_amount}"
    
    
class RestaurantTable(models.Model):

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    seats = models.IntegerField()
    table_name = models.CharField(max_length=200 , blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in minutes")
    description = models.TextField(null=True, blank=True)

    status = models.BooleanField(default=True)
    
    images = models.JSONField(default=list, blank=True)

    next_available_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    
class TableBooking(models.Model):

    table = models.ForeignKey(RestaurantTable, on_delete=models.CASCADE)

    user = models.ForeignKey(UserRegister, on_delete=models.CASCADE)

    booking_start_time = models.DateTimeField()
    booking_end_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=[
            ("booked","Booked"),
            ("completed","Completed"),
            ("cancelled","Cancelled"),
            ("expired", "Expired")
        ],
        default="booked"
    )
    
    booking_price = models.DecimalField(max_digits=8, decimal_places=2, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    

class OrderCompletion(models.Model):

    order = models.ForeignKey(
        Orders,
        on_delete=models.CASCADE,
        related_name="order_completions"
    )
    
    INCENTIVE_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
    )

    delivery_partner = models.ForeignKey(
        DeliveryPartnerForm,
        on_delete=models.CASCADE,
        related_name="order_completions"
    )

    today_order_count = models.IntegerField(
        default=0,
        help_text="Total orders completed today by the partner"
    )

    incentive_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    incentive_paid_status = models.CharField(
        max_length=10,
        choices=INCENTIVE_STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order.id} - Partner {self.delivery_partner.id}"

    class Meta:
        
        ordering = ["-created_at"]
        

class DeliveryPartnerWallet(models.Model):

    delivery_partner = models.OneToOneField(
        DeliveryPartnerForm,
        on_delete=models.CASCADE,
        related_name="wallet"
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_earned = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_withdrawn = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet - {self.delivery_partner.full_name}"
    

class WalletTransaction(models.Model):
    
    order_completions = models.ManyToManyField(
        OrderCompletion,
        related_name="wallet_transactions"
    )

    wallet = models.ForeignKey(
        DeliveryPartnerWallet,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    
    fixedamount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    

    incentiveTotalAmount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    
    TotalPaidAmount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    

    description = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"
    
    
    
class Notifications(models.Model):

    user = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    
    
    
class CommissionSetting(models.Model):

    COMMISSION_TYPE_CHOICES = (
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    )

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="commissions",
        null=True,
        blank=True
    )

    commission_type = models.CharField(
        max_length=20,
        choices=COMMISSION_TYPE_CHOICES,
        default="percentage"
    )

    commission_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Example: 25 means 25% commission"
    )

    min_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    max_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.restaurant:
            return f"{self.restaurant.restaurantname} - {self.commission_value}%"
        return f"Global Commission - {self.commission_value}%"
    
    

class VendorPayout(models.Model):

    PAYOUT_STATUS = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("paid", "Paid"),
    )

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="vendor_payouts"
    )

    order = models.OneToOneField(
        Orders,
        on_delete=models.CASCADE,
        related_name="vendor_payout"
    )

    order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
    )

    vendor_earning = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
    )

    payout_status = models.CharField(
        max_length=20,
        choices=PAYOUT_STATUS,
        default="pending"
    )

    payout_date = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vendor_payouts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payout - Order {self.order.id} - {self.restaurant.restaurantname}"
    
    

class BookingTransaction(models.Model):

    PAYMENT_MODE_CHOICES = (
        ("upi", "UPI"),
        ("card", "Card"),
        ("cash", "Cash"),
        ("net_banking", "Net Banking"),
        ("razorpay", "Razorpay"),
        ("google_pay", "Google Pay"),
        ("phonepe", "PhonePe"),
        ("cod", "Cash On Delivery"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name="booking_transactions"
    )

    booking = models.ForeignKey(
        TableBooking,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODE_CHOICES
    )

    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    transaction_no = models.CharField(
        max_length=100,
        unique=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_no} - {self.user}"
    
    

class Banner(models.Model):
    title = models.CharField(max_length=255)
    
    # store multiple image URLs / paths as JSON list
    images = models.JSONField(default=list, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class AboutUs(models.Model):

    title = models.CharField(max_length=255, default="About Us")
    description = models.TextField()

    # Optional fields
    mission = models.TextField(blank=True, null=True)
    vision = models.TextField(blank=True, null=True)

    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)

    address = models.TextField(blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    

class HelpSupport(models.Model):

    title = models.CharField(max_length=255, default="Help & Support")
    description = models.TextField()

    # Contact Information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)

    # Optional fields
    address = models.TextField(blank=True, null=True)
    working_hours = models.CharField(max_length=255, blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    

class Wishlist(models.Model):

    user = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    menu_item = models.ForeignKey(
        MenuItems,
        on_delete=models.CASCADE,
        related_name="wishlisted_by"
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )

    def __str__(self):
        return f"{self.user.email} ❤️ {self.menu_item.name}"

    class Meta:
        db_table = "wishlist"
        unique_together = ("user", "menu_item")  # 🔥 Prevent duplicates
        ordering = ["-created_at"]
        


class UserWallet(models.Model):
    user = models.OneToOneField(UserRegister, on_delete=models.CASCADE)

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.balance}"
    
class UserWalletTransaction(models.Model):
    
    DONE_BY_CHOICES = (
        ('user', 'User'),
        ('admin', 'Keeno Admin'),
        
    )

    TRANSACTION_TYPE_CHOICES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Wallet'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    done_by = models.CharField(max_length=20, choices=DONE_BY_CHOICES ,null=True, blank=True)
    transaction_id = models.UUIDField(
    default=uuid.uuid4,
    unique=True,
    editable=False,
    null=True,
    blank=True
)
    
    def __str__(self):
        return f"{self.wallet} - {self.amount} ({self.transaction_type})"
    
    


class RestaurantPartyBooking(models.Model):
    
    APPROVE_STATUS = [
        ('pending','Pending'),
        ('approved','Approved')
    ]
    
    ENQUIRY_STATUS =[
        ('pending','Pending'),
        ('cancel','Cancel'),
        ('completed','Completed')
    ]
    
    PARTY_CHOICE =[
        
        ('biryaniparty','Biryani Party'),
        ('birthdayparty','Birthday Party'),
        ('hostalparty','Hostal Party')
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete= models.CASCADE, related_name="pary_bookings")
    user = models.ForeignKey(UserRegister, on_delete = models.CASCADE, related_name="party_bookings" )
    partytype = models.CharField(max_length=100, choices=PARTY_CHOICE , null=True , blank=True)
    
    partydatetime = models.DateTimeField( null=True , blank=True)
    
    approvestatus = models.CharField(max_length=100, choices=APPROVE_STATUS , default='pending')
    enquirystatus = models.CharField(max_length=100, choices=ENQUIRY_STATUS , default='pending')
    
    name = models.CharField(max_length=255)
    Mobileno = models.CharField(max_length=15)
    order_details = models.TextField()
    
    deliveryAdddress = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} - {self.restaurant.restaurantname}"
    
    