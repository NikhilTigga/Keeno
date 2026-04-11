from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views import View
from .models import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
import random
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
import uuid
from django.db import transaction
from django.db.models import Prefetch
from django.db.models import Sum
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncHour
from datetime import timedelta
import json
# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class VendorRegisterView(View):

    def post(self, request):

        name = request.POST.get('name')
        email = request.POST.get('email')
        phoneno = request.POST.get('phoneno')
        password = request.POST.get('password')
        image = request.FILES.get('image')  # image field

        # Validate required fields
        if not name or not email or not phoneno or not password:
            return JsonResponse({
                'status': False,
                'message': 'All fields are required'
            }, status=200)

        # Check duplicate email
        if VendorRegistration.objects.filter(email=email).exists():
            return JsonResponse({
                'status': False,
                'message': 'Email already exists'
            }, status=200)

        # Check duplicate phone
        if VendorRegistration.objects.filter(phoneno=phoneno).exists():
            return JsonResponse({
                'status': False,
                'message': 'Phone number already exists'
            }, status=200)

        # Hash password
        hashed_password = make_password(password)

        # Create vendor
        vendor = VendorRegistration.objects.create(
            name=name,
            email=email,
            phoneno=phoneno,
            password=hashed_password,
            profile_img=image   # Correct field name based on your model
        )

        # Return response
        return JsonResponse({
            'status': True,
            'message': 'Vendor registered successfully',
            'vendor': {
                'vendor_id': vendor.id,
                'name': vendor.name,
                'email': vendor.email,
                'phoneno': vendor.phoneno,
                'image': vendor.profile_img.url if vendor.profile_img else None
            }
        }, status=201)
        
@method_decorator(csrf_exempt, name='dispatch')        
class VendorLoginView(View):

    def post(self, request):

        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            return JsonResponse({
                "status": False,
                "message": "Email and password required"
            }, status=200)

        try:
            vendor = VendorRegistration.objects.get(email=email)

        except VendorRegistration.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Vendor not found"
            }, status=200)


        if not check_password(password, vendor.password):
            return JsonResponse({
                "status": False,
                "message": "Invalid password"
            }, status=200)


        # Generate OTP
        otp = str(random.randint(1000,9999))
        VendorOTP.objects.create(
            vendor=vendor,
            
            otp = otp,
        )

        # Send OTP (for testing print in console)
        print(f"OTP for {vendor.email} is {otp}")

        return JsonResponse({
            "status": True,
            "message": "OTP sent successfully",
            "vendor_id": vendor.id,
            "phone": vendor.phoneno,
            "otp":otp
        })
 
@method_decorator(csrf_exempt, name='dispatch')        
class VerifyVendorOTPView(View):

    def post(self, request):

        vendor_id = request.POST.get("vendor_id")
        otp = request.POST.get("otp")
        

        if not vendor_id or not otp:
            return JsonResponse({
                "status": False,
                "message": "vendor_id and otp required"
            }, status=200)

        try:
            vendor_otp = VendorOTP.objects.filter(
                vendor_id=vendor_id,
                otp=otp,
                is_verified=False
            ).latest('created_at')
            
            vendor= VendorRegistration.objects.get(id=vendor_id)

        except VendorOTP.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Invalid OTP"
            }, status=200)


        vendor_otp.is_verified = True
        vendor_otp.save()

        return JsonResponse({
            "status": True,
            "message": "Login successful",
            "vendor":{
                "vendor_id": vendor.id,
                "name": vendor.name,
                "email": vendor.email,
                "phoneno": vendor.phoneno
            }
        })
        
# @method_decorator(csrf_exempt, name='dispatch')
# class VendorRestaurantRegistrationForm(View):
#     def post(self, request):

#         try:
#             vendor_id = request.POST.get("vendor_id")
#             ownername = request.POST.get("ownername")
#             phone = request.POST.get("phone")
#             email = request.POST.get("email")
#             restaurantname = request.POST.get("restaurantname")
#             address = request.POST.get("address")
#             latitude = request.POST.get("latitude")
#             longitude = request.POST.get("longitude")

#             # validation
#             if not vendor_id:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "vendor_id required"
#                 }, status=200)

#             try:
#                 vendor = VendorRegistration.objects.get(id=vendor_id)
#             except VendorRegistration.DoesNotExist:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Vendor not found"
#                 }, status=200)

#             # handle multiple images
#             image_urls = []

#             if request.FILES.getlist("restaurantimage"):

#                 for image in request.FILES.getlist("restaurantimage"):

#                     # save file
#                     path = os.path.join("restaurant_images", image.name)
#                     full_path = os.path.join(settings.MEDIA_ROOT, path)

#                     os.makedirs(os.path.dirname(full_path), exist_ok=True)

#                     with open(full_path, "wb+") as destination:
#                         for chunk in image.chunks():
#                             destination.write(chunk)

#                     # store URL
#                     image_url = request.build_absolute_uri(
#                         settings.MEDIA_URL + path
#                     )

#                     image_urls.append(image_url)

#             # create restaurant
#             restaurant = Restaurant.objects.create(
#                 vendorid=vendor,
#                 ownername=ownername,
#                 phone=phone,
#                 email=email,
#                 restaurantname=restaurantname,
#                 adderess=address,
#                 latitude=latitude if latitude else None,
#                 longitude=longitude if longitude else None,
#                 restaurantimage=image_urls
#             )

#             return JsonResponse({
#                 "status": True,
#                 "message": "Restaurant registered successfully",
#                 "restaurant_id": restaurant.id,
#                 "images": image_urls
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             }, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class VendorRestaurantRegistrationForm(View):
    def post(self, request):

        try:
            vendor_id = request.POST.get("vendor_id")
            ownername = request.POST.get("ownername")
            phone = request.POST.get("phone")
            email = request.POST.get("email")
            restaurantname = request.POST.get("restaurantname")
            address = request.POST.get("address")
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")

            if not vendor_id:
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id required"
                })

            try:
                vendor = VendorRegistration.objects.get(id=vendor_id)
            except VendorRegistration.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                })

            image_urls = []

            if request.FILES.getlist("restaurantimage"):

                for image in request.FILES.getlist("restaurantimage"):

                    path = os.path.join("restaurant_images", image.name)
                    path = path.replace("\\", "/")  # ✅ fix Windows slash

                    full_path = os.path.join(settings.MEDIA_ROOT, path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)

                    with open(full_path, "wb+") as destination:
                        for chunk in image.chunks():
                            destination.write(chunk)

                    # ✅ Save only from /media/
                    image_url = settings.MEDIA_URL + path
                    image_urls.append(image_url)

            restaurant = Restaurant.objects.create(
                vendorid=vendor,
                ownername=ownername,
                phone=phone,
                email=email,
                restaurantname=restaurantname,
                adderess=address,
                latitude=latitude if latitude else None,
                longitude=longitude if longitude else None,
                restaurantimage=image_urls
            )

            return JsonResponse({
                "status": True,
                "message": "Restaurant registered successfully",
                "restaurant_id": restaurant.id,
                "images": image_urls
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class CreateCategoryView(View):
    def post(self, request):

        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            global_category_id = request.POST.get("global_category_id")
            categories_name = request.POST.get("categories_name")
            
            print('vendor_id',vendor_id)
            print('restaurant_id',restaurant_id)
            print('global_category_id',global_category_id)
            print('categories_name',categories_name)
            
            
            

            # Get multiple images
            images = request.FILES.getlist("category_images")
            print('category_images',images)

            # Validate fields
            if not all([vendor_id, restaurant_id, global_category_id, categories_name]):
                return JsonResponse({
                    "status": False,
                    "message": "All fields are required"
                }, status=400)

            # Check vendor
            vendor = VendorRegistration.objects.filter(id=vendor_id).first()
            if not vendor:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # Check restaurant belongs to vendor
            restaurant = Restaurant.objects.filter(
                id=restaurant_id,
                vendorid=vendor
            ).first()

            if not restaurant:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or not owned by vendor"
                }, status=404)
            
            # Check global category
            global_category = GlobalCategory.objects.filter(
                id=global_category_id
            ).first()

            if not global_category:
                return JsonResponse({
                    "status": False,
                    "message": "Global category not found"
                }, status=404)

            # Save images and store paths in list
            image_paths = []

            upload_dir = os.path.join(settings.MEDIA_ROOT, "categories")
            os.makedirs(upload_dir, exist_ok=True)

            for image in images:

                filename = f"{uuid.uuid4()}_{image.name}"

                file_path = os.path.join(upload_dir, filename)

                with open(file_path, "wb+") as destination:
                     for chunk in image.chunks():
                         destination.write(chunk)

                image_paths.append(f"{settings.MEDIA_URL}categories/{filename}")

            # Create category with images
            category = Categories.objects.create(
                categories_name=categories_name,
                restaurant=restaurant,
                GlobalCategory=global_category,
                category_images=image_paths
            )

            return JsonResponse({
                "status": True,
                "message": "Category created successfully",
                "data": {
                    "id": category.id,
                    "categories_name": category.categories_name,
                    "restaurant": restaurant.restaurantname,
                    "global_category": global_category.catgname,
                    "category_images": category.category_images,
                    "created_at": category.created_at.strftime("%d-%m-%Y %I:%M %p")
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
# @method_decorator(csrf_exempt, name='dispatch')
# class CreateMenuItemView(View):
#     def post(self, request):
#         try:
#             vendor_id = request.POST.get("vendor_id")
#             restaurant_id = request.POST.get("restaurant_id")
#             category_id = request.POST.get("category_id")
#             name = request.POST.get("name")
#             price = request.POST.get("price")
#             veg_nonveg = request.POST.get("VegNonVeg")
#             description = request.POST.get("description", "")
#             is_available = request.POST.get("is_available", True)
#             discount_details=request.POST.get("discount_details")

#             # Get images
#             images = request.FILES.getlist("menu_images")

#             # Validate required fields
#             if not all([
#                 vendor_id,
#                 restaurant_id,
#                 name,
#                 price,
#                 veg_nonveg
#             ]):
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Required fields missing"
#                 }, status=400)

#             # Validate Vendor
#             vendor = VendorRegistration.objects.filter(id=vendor_id).first()
#             if not vendor:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Vendor not found"
#                 }, status=404)
#             restaurant = Restaurant.objects.filter(
#                 id=restaurant_id,
#                 vendorid=vendor
#             ).first()

#             if not restaurant:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Restaurant not found or not owned by vendor"
#                 }, status=404)

#             category = None
#             if category_id:
#                 category = Categories.objects.filter(
#                     id=category_id,
#                     restaurant=restaurant
#                 ).first()

#                 if not category:
#                     return JsonResponse({
#                         "status": False,
#                         "message": "Category not found in this restaurant"
#                     }, status=404)
#             image_paths = []
#             upload_dir = os.path.join(settings.MEDIA_ROOT, "menu_items")
#             os.makedirs(upload_dir, exist_ok=True)
#             for image in images:

#                 filename = f"{uuid.uuid4()}_{image.name}"
#                 file_path = os.path.join(upload_dir, filename)

#                 with open(file_path, "wb+") as destination:
#                     for chunk in image.chunks():
#                         destination.write(chunk)

#                 image_paths.append(f"{settings.MEDIA_URL}menu_items/{filename}")
#             menu_item = MenuItems.objects.create(
#                 restaurant=restaurant,
#                 categories=category,
#                 name=name,
#                 price=price,
#                 VegNonVeg=veg_nonveg,
#                 description=description,
#                 is_available=is_available,
#                 menu_images=image_paths,
#                 discountdetails=discount_details,
#             )
#             return JsonResponse({
#                 "status": True,
#                 "message": "Menu item created successfully",
#                 "data": {
#                     "id": menu_item.id,
#                     "name": menu_item.name,
#                     "price": str(menu_item.price),
#                     "VegNonVeg": menu_item.VegNonVeg,
#                     "restaurant": restaurant.restaurantname,
#                     "category": category.categories_name if category else None,
#                     "menu_images": menu_item.menu_images,
#                     "created_at": menu_item.created_at.strftime("%d-%m-%Y %I:%M %p")
#                 }
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             }, status=500)




@method_decorator(csrf_exempt, name='dispatch')
class CreateMenuItemView(View):

    def post(self, request):
        try:
            
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            category_id = request.POST.get("category_id")
            featured_category_id = request.POST.get("featured_category_id")
            name = request.POST.get("name")
            price = request.POST.get("price")
            veg_nonveg = request.POST.get("VegNonVeg")

            description = request.POST.get("description", "")
            halal_attribute = request.POST.get("halal_attribute")
            spicy = request.POST.get("spicy", "false").lower() == "true"

            prep_time = request.POST.get("prep_time")
            discount = request.POST.get("discount")

            is_available = request.POST.get("is_available", "true").lower() == "true"

            addon_master_ids = request.POST.get("addon_master_ids")
            portions_data = request.POST.get("portions")

            images = request.FILES.getlist("menu_images")
            
            

            # =========================
            # ✅ VALIDATION
            # =========================
            if not all([vendor_id, restaurant_id, name, price, veg_nonveg]):
                return JsonResponse({
                    "status": False,
                    "message": "Required fields missing"
                }, status=400)

            vendor = VendorRegistration.objects.filter(id=vendor_id).first()
            if not vendor:
                return JsonResponse({"status": False, "message": "Vendor not found"}, status=404)

            restaurant = Restaurant.objects.filter(
                id=restaurant_id,
                vendorid=vendor
            ).first()

            if not restaurant:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or not owned by vendor"
                }, status=404)

            category = None
            if category_id:
                category = Categories.objects.filter(
                    id=category_id,
                    restaurant=restaurant
                ).first()
                
            featured_category = None
            if featured_category_id:
                featured_category = FeaturedCategory.objects.filter(
                    id=featured_category_id
                ).first()
                
           
                 

            # =========================
            # ✅ IMAGE UPLOAD
            # =========================
            image_paths = []
            upload_dir = os.path.join(settings.MEDIA_ROOT, "menu_items")
            os.makedirs(upload_dir, exist_ok=True)

            for image in images:
                filename = f"{uuid.uuid4()}_{image.name}"
                file_path = os.path.join(upload_dir, filename)

                with open(file_path, "wb+") as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)

                image_paths.append(f"{settings.MEDIA_URL}menu_items/{filename}")

            # =========================
            # ✅ CALCULATE DISCOUNT PRICE
            # =========================
            price = float(price)
            discount_value = int(discount) if discount else 0

            price_after_discount = price
            if discount_value > 0:
                price_after_discount = price - (price * discount_value / 100)

            # =========================
            # ✅ CREATE MENU ITEM
            # =========================
            menu_item = MenuItems.objects.create(
                restaurant=restaurant,
                categories=category,
                globalCategory= category.GlobalCategory if category.GlobalCategory else None,
                name=name,
                price=price,
                price_afterDesc=price_after_discount,
                VegNonVeg=veg_nonveg,
                description=description,
                featured_category=featured_category, 
                is_available=is_available,
                menu_images=image_paths,
                halal_attribute=halal_attribute,
                sypicy=spicy,
                prep_time=int(prep_time) if prep_time else None,
                discount=discount_value if discount else None
            )
            # if  featured_category_id:
            #     menu_item.featured_category = featured_category
            #     menu_item.save()

            # =========================
            # ✅ CREATE PORTIONS
            # =========================
            if portions_data:
                portions = json.loads(portions_data)

                for portion in portions:
                    MenuItemPortion.objects.create(
                        menu_item=menu_item,
                        portion_name=portion.get("portion_name"),
                        price=portion.get("price")
                    )

            # =========================
            # ✅ CREATE ADDONS
            # =========================
            if addon_master_ids:
                addon_ids = json.loads(addon_master_ids)

                addon_masters = AddonMaster.objects.filter(
                    id__in=addon_ids,
                    restaurant=restaurant
                )

                for addon_master in addon_masters:
                    AddOn.objects.create(
                        menu_item=menu_item,
                        name=addon_master.addon_name,
                        price=addon_master.price,
                        image=addon_master.addon_image,
                        is_available=addon_master.is_available
                    )

            return JsonResponse({
                "status": True,
                "message": "Menu item created successfully",
                "data": {
                    "id": menu_item.id,
                    "name": menu_item.name,
                    "price": str(menu_item.price),
                    "price_after_discount": str(menu_item.price_afterDesc),
                    "discount": menu_item.get_discount_display(),
                    "prep_time": menu_item.get_prep_time_display() if menu_item.prep_time else None,
                    "total_addons": menu_item.addons.count(),
                    "total_portions": menu_item.portions.count()
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            

@method_decorator(csrf_exempt, name='dispatch')
class GetGlobalCategoryView(View):
    def get(self, request):
        try:
            categories = GlobalCategory.objects.all()
            data = []
            for cat in categories:
                data.append({
                    "id": cat.id,
                    "catgname": cat.catgname,
                    "created_at": cat.created_at.strftime("%d-%m-%Y %I:%M %p")
                })
            return JsonResponse({
                "status": True,
                "message": "Global categories fetched successfully",
                "count": len(data),
                "data": data
            })
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CategoryListByRestaurantView(View):
    def post(self, request):
        try:
            restaurant_id = request.POST.get("restaurant_id")

            if not restaurant_id:
                return JsonResponse({
                    "status": False,
                    "message": "restaurant_id is required"
                }, status=400)

            # Check restaurant exists
            restaurant = Restaurant.objects.filter(id=restaurant_id).first()

            if not restaurant:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found"
                }, status=404)

            categories = Categories.objects.filter(
                restaurant=restaurant
            ).order_by("-created_at")

            data = []

            for cat in categories:

                # convert image paths to full media url
                images = []
                if cat.category_images:
                    for img in cat.category_images:
                        images.append(
                            request.build_absolute_uri(f"/media/{img}")
                        )

                data.append({
                    "category_id": cat.id,
                    "category_name": cat.categories_name,
                    "category_images": images
                })

            return JsonResponse({
                "status": True,
                "message": "Categories fetched successfully",
                "data": data
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class EditCategoryView(View):
    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            category_id = request.POST.get("category_id")
            categories_name = request.POST.get("categories_name")
            global_category_id = request.POST.get("global_category_id")
            new_images = request.FILES.getlist("category_images")

            # Required validation
            if not vendor_id or not restaurant_id or not category_id:
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id, restaurant_id and category_id are required"
                }, status=400)

            # Verify vendor exists
            vendor = VendorRegistration.objects.filter(
                id=vendor_id
            ).first()

            if not vendor:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # Verify restaurant belongs to vendor
            restaurant = Restaurant.objects.filter(
                id=restaurant_id,
                vendorid=vendor
            ).first()

            if not restaurant:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or unauthorized"
                }, status=403)

            # Verify category belongs to restaurant
            category = Categories.objects.filter(
                id=category_id,
                restaurant=restaurant
            ).first()

            if not category:
                return JsonResponse({
                    "status": False,
                    "message": "Category not found in this restaurant"
                }, status=404)

            # Update category name (optional)
            if categories_name:
                category.categories_name = categories_name

            # Update global category (optional)
            if global_category_id:

                global_category = GlobalCategory.objects.filter(
                    id=global_category_id
                ).first()

                if not global_category:
                    return JsonResponse({
                        "status": False,
                        "message": "Global category not found"
                    }, status=404)

                category.GlobalCategory = global_category

            # Update images (optional)
            if new_images:

                upload_dir = os.path.join(settings.MEDIA_ROOT, "categories")
                os.makedirs(upload_dir, exist_ok=True)

                image_paths = []

                for image in new_images:

                    file_path = os.path.join(upload_dir, image.name)

                    with open(file_path, "wb+") as f:
                        for chunk in image.chunks():
                            f.write(chunk)

                    image_paths.append(
                        f"{settings.MEDIA_URL}categories/{image.name}"
                    )

                category.category_images = image_paths

            category.save()

            return JsonResponse({
                "status": True,
                "message": "Category updated successfully",
                "data": {
                    "id": category.id,
                    "categories_name": category.categories_name,
                    "vendor_id": vendor.id,
                    "restaurant_id": restaurant.id,
                    "restaurant_name": restaurant.restaurantname,
                    "global_category": category.GlobalCategory.catgname,
                    "category_images": category.category_images,
                    "created_at": category.created_at.strftime("%d-%m-%Y %I:%M %p")
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
              
@method_decorator(csrf_exempt, name='dispatch')
class RestaurantListByVendorView(View):
    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")

            if not vendor_id:
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id is required"
                }, status=400)

            # Verify Vendor exists
            vendor = VendorRegistration.objects.filter(
                id=vendor_id
            ).first()

            if not vendor:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # Get restaurants of vendor
            restaurants = Restaurant.objects.filter(
                vendorid=vendor
            ).order_by("-created_at")

            restaurant_list = []

            for restaurant in restaurants:

                restaurant_list.append({
                    "restaurant_id": restaurant.id,
                    "restaurant_name": restaurant.restaurantname,
                    "owner_name": restaurant.ownername,
                    "phone": restaurant.phone,
                    "email": restaurant.email,
                    "address": restaurant.adderess,
                    "latitude": str(restaurant.latitude) if restaurant.latitude else None,
                    "longitude": str(restaurant.longitude) if restaurant.longitude else None,
                    "restaurant_images": restaurant.restaurantimage,
                    "is_active": restaurant.is_active,
                    "approve_status": restaurant.approveStatus,
                    "created_at": restaurant.created_at.strftime("%d-%m-%Y %I:%M %p")
                })
            return JsonResponse({
                "status": True,
                "message": "Restaurant list fetched successfully",
                "total_restaurants": len(restaurant_list),
                "data": restaurant_list
            })
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class GetRestaurantMenuAPI(View):

    def post(self, request):
        try:
            restaurant_id = request.POST.get("restaurant_id")

            if not restaurant_id:
                return JsonResponse({
                    "status": False,
                    "message": "restaurant_id is required"
                }, status=400)

            menu_items = MenuItems.objects.filter(
                restaurant_id=restaurant_id,
                is_available=True
            ).select_related("categories")

            if not menu_items.exists():
                return JsonResponse({
                    "status": False,
                    "message": "No menu items found"
                }, status=404)

            data = []

            for item in menu_items:
                data.append({
                    "menu_id": item.id,
                    "menu_name": item.name,
                    "price": float(item.price),
                    "category_name": item.categories.categories_name if item.categories else None,
                    "veg_nonveg": item.VegNonVeg,
                    "is_available": item.is_available,
                    "menu_images": item.menu_images,
                    "description": item.description,
                    "discountdetails": item.discount
                })

            return JsonResponse({
                "status": True,
                "restaurant_id": restaurant_id,
                "menu_items": data
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=400)
            
@method_decorator(csrf_exempt, name='dispatch')
class GetRestaurantCategoryAPI(View):

    def post(self, request):
        try:
            restaurant_id = request.POST.get("restaurant_id")

            if not restaurant_id:
                return JsonResponse({
                    "status": False,
                    "message": "restaurant_id is required"
                }, status=400)

            # Get restaurant object
            restaurant = Restaurant.objects.filter(id=restaurant_id).first()
            if not restaurant:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found"
                }, status=404)

            # Get categories having available menu items
            categories = Categories.objects.filter(
                restaurant_id=restaurant_id,
                
            ).distinct()

            if not categories.exists():
                return JsonResponse({
                    "status": False,
                    "message": "No categories found"
                }, status=404)

            data = []

            for category in categories:
                # Get veg/nonveg types inside this category
                

                data.append({
                    "category_id": category.id,
                    "category_name": category.categories_name,
                    "category_image": category.category_images,
                    "restaurant_name": restaurant.restaurantname,
                    
                })
            return JsonResponse({
                "status": True,
                "restaurant_id": restaurant_id,
                "restaurant_name": restaurant.restaurantname,
                "categories": data[::-1]
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=400)
            
@method_decorator(csrf_exempt, name='dispatch')
class CreateAddonMasterAPI(View):

    def post(self, request):
        try:
            
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            addon_name = request.POST.get("addon_name")
            price = request.POST.get("price")
            is_available = request.POST.get("is_available", True)
            addon_image = request.FILES.get("addon_image")

            # ✅ Validate required fields
            if not all([vendor_id, restaurant_id, addon_name, price]):
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id, restaurant_id, addon_name and price are required"
                }, status=400)

            # ✅ Check vendor exists
            try:
                vendor = VendorRegistration.objects.get(id=vendor_id)
            except VendorRegistration.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # ✅ Check restaurant exists and belongs to vendor
            try:
                restaurant = Restaurant.objects.get(
                    id=restaurant_id,
                    vendorid=vendor   # assuming Restaurant has FK to VendorRegistration
                )
            except Restaurant.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or does not belong to this vendor"
                }, status=404)

            # ✅ Create Addon
            addon = AddonMaster.objects.create(
                restaurant=restaurant,
                addon_name=addon_name,
                price=price,
                addon_image=addon_image,
                is_available=is_available
            )

            return JsonResponse({
                "status": True,
                "message": "Addon created successfully",
                "data": {
                    "addon_id": addon.id,
                    "addon_name": addon.addon_name,
                    "price": str(addon.price),
                    "image": addon.addon_image.url if addon.addon_image else None,
                    "is_available": addon.is_available
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
@method_decorator(csrf_exempt, name='dispatch')
class EditAddonMasterAPI(View):
    @transaction.atomic
    def post(self, request):  # you can change to put() if needed
        try:
            addon_id = request.POST.get("addon_id")
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")

            addon_name = request.POST.get("addon_name")
            price = request.POST.get("price")
            is_available = request.POST.get("is_available")
            addon_image = request.FILES.get("addon_image")

            # ✅ Required validation
            if not all([addon_id, vendor_id, restaurant_id]):
                return JsonResponse({
                    "status": False,
                    "message": "addon_id, vendor_id and restaurant_id are required"
                }, status=400)

            # ✅ Validate vendor
            try:
                vendor = VendorRegistration.objects.get(id=vendor_id)
            except VendorRegistration.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # ✅ Validate restaurant
            try:
                restaurant = Restaurant.objects.get(
                    id=restaurant_id,
                    vendorid=vendor
                )
            except Restaurant.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or not owned by vendor"
                }, status=404)

            # ✅ Validate addon exists
            try:
                addon = AddonMaster.objects.get(
                    id=addon_id,
                    restaurant=restaurant
                )
            except AddonMaster.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Addon not found for this restaurant"
                }, status=404)

            # =========================
            # UPDATE FIELDS (ONLY IF SENT)
            # =========================

            if addon_name:
                addon.addon_name = addon_name

            if price:
                addon.price = price

            if is_available is not None:
                addon.is_available = str(is_available).lower() in ["true", "1", "yes"]

            # ✅ If new image uploaded → replace old
            if addon_image:
                # delete old image file
                if addon.addon_image and os.path.isfile(addon.addon_image.path):
                    os.remove(addon.addon_image.path)

                addon.addon_image = addon_image

            addon.save()

            return JsonResponse({
                "status": True,
                "message": "Addon updated successfully",
                "data": {
                    "addon_id": addon.id,
                    "addon_name": addon.addon_name,
                    "price": str(addon.price),
                    "image": addon.addon_image.url if addon.addon_image else None,
                    "is_available": addon.is_available
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
                
@method_decorator(csrf_exempt, name='dispatch')
class ListAddonMasterAPI(View):

    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")

            # ✅ Validate required fields
            if not all([vendor_id, restaurant_id]):
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id and restaurant_id are required"
                }, status=400)

            # ✅ Check vendor exists
            try:
                vendor = VendorRegistration.objects.get(id=vendor_id)
            except VendorRegistration.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # ✅ Check restaurant belongs to vendor
            try:
                restaurant = Restaurant.objects.get(
                    id=restaurant_id,
                    vendorid=vendor
                )
            except Restaurant.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or does not belong to this vendor"
                }, status=404)

            # ✅ Get all addons for this restaurant
            addons = AddonMaster.objects.filter(
                restaurant=restaurant
            ).order_by("-created_at")

            addon_list = []

            for addon in addons:
                addon_list.append({
                    "addon_id": addon.id,
                    "addon_name": addon.addon_name,
                    "price": str(addon.price),
                    "image": request.build_absolute_uri(addon.addon_image.url) if addon.addon_image else None,
                    "is_available": addon.is_available,
                    "created_at": addon.created_at
                })

            return JsonResponse({
                "status": True,
                "message": "Addon list fetched successfully",
                "total_addons": len(addon_list),
                "data": addon_list
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class VendorOrderManagementAPI(View):

    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            status = request.POST.get("status")  # now optional

            if not all([vendor_id, restaurant_id]):
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id and restaurant_id are required"
                }, status=400)

            # ✅ Validate Vendor
            try:
                vendor = VendorRegistration.objects.get(id=vendor_id)
            except VendorRegistration.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # ✅ Validate Restaurant
            try:
                restaurant = Restaurant.objects.get(
                    id=restaurant_id,
                    vendorid=vendor
                )
            except Restaurant.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or not owned by vendor"
                }, status=404)

            # =========================
            # BUILD ORDER QUERY
            # =========================

            orders_queryset = Orders.objects.filter(
                items__restaurant=restaurant
            ).distinct()

            # ✅ Apply status filter only if provided
            if status:
                orders_queryset = orders_queryset.filter(status=status)

            orders = orders_queryset.prefetch_related(
                Prefetch(
                    "items",
                    queryset=CartItems.objects.filter(restaurant=restaurant)
                )
            ).select_related("user")

            response_data = []

            for order in orders:
                items_data = []
                total_amount = 0

                for item in order.items.all():
                    item_total = item.price_at_order_time * item.quantity
                    addon_total = sum(
                        addon.get("item_price", 0)
                        for addon in (item.addon or [])
                    )
                    total_amount += item_total
                    total_amount+=addon_total

                    items_data.append({
                        "menu_item_name": item.menu_item.name,
                        "quantity": item.quantity,
                        "price_at_order_time": str(item.price_at_order_time),
                        "selected_portion": item.selectportion,
                        "addons": item.addon,
                        "item_total": str(item_total+addon_total)
                    })

                response_data.append({
                    "order_id": order.id,
                    "order_uuid": str(order.order_uuid),
                    "customer_name": order.user.name,
                    "mobile_no": order.user.phone_no,
                    "delivery_address": order.delivery_address,
                    "order_time": order.created_at,
                    "order_status": order.status,
                    "total_amount": str(total_amount),
                    "items": items_data
                })

            return JsonResponse({
                "status": True,
                "message": "Orders fetched successfully",
                "total_orders": len(response_data),
                "data": response_data
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UpdateOrderStatusAPI(View):

    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            order_id = request.POST.get("order_id")
            new_status = request.POST.get("status")
            

            if not all([vendor_id, restaurant_id, order_id, new_status]):
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id, restaurant_id, order_id and status are required"
                }, status=400)

            # Validate Status
            valid_statuses = dict(Orders.STATUS_CHOICES).keys()
            if new_status not in valid_statuses:
                return JsonResponse({
                    "status": False,
                    "message": f"Invalid status. Allowed: {list(valid_statuses)}"
                }, status=400)

            # Validate Vendor
            try:
                vendor = VendorRegistration.objects.get(id=vendor_id)
            except VendorRegistration.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # Validate Restaurant
            try:
                restaurant = Restaurant.objects.get(
                    id=restaurant_id,
                    vendorid=vendor
                )
            except Restaurant.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or not owned by vendor"
                }, status=404)

            # ✅ Get Order ONLY by ID
            try:
                order = Orders.objects.get(id=order_id)
            except Orders.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Order not found"
                }, status=404)

            # ✅ Verify Order Belongs To This Restaurant
            if not order.items.filter(restaurant=restaurant).exists():
                return JsonResponse({
                    "status": False,
                    "message": "This order does not belong to this restaurant"
                }, status=403)

            # ✅ Update Status
            order.status = new_status
            order.save()

            return JsonResponse({
                "status": True,
                "message": "Order status updated successfully",
                "data": {
                    "order_id": order.id,
                    "order_uuid": str(order.order_uuid),
                    "new_status": order.status
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
@method_decorator(csrf_exempt, name='dispatch')
class CreateStaffProfileAPI(View):

    def post(self, request):
        try:
            restaurant_id = request.POST.get("restaurant_id")
            vendor_id = request.POST.get("vendor_id")
            staff_name = request.POST.get("staff_name")
            email = request.POST.get("email")
            phone_no = request.POST.get("phone_no")
            work_days = request.POST.get("work_days")
            work_time = request.POST.get("work_time")
            work_status = request.POST.get("work_status", "active")
            department = request.POST.get("department")
            role = request.POST.get("role")
            profile_photo = request.FILES.get("profile_photo")

            # ✅ Required field validation
            if not all([restaurant_id, vendor_id, staff_name, email, phone_no, department, role]):
                return JsonResponse({
                    "status": False,
                    "message": "Required fields are missing"
                }, status=400)

            # ✅ Check restaurant
            try:
                restaurant = Restaurant.objects.get(id=restaurant_id)
            except Restaurant.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found"
                }, status=404)

            # ✅ Check vendor
            try:
                vendor = VendorRegistration.objects.get(id=vendor_id)
            except VendorRegistration.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # ✅ Check duplicate email
            if StaffProfile.objects.filter(email=email).exists():
                return JsonResponse({
                    "status": False,
                    "message": "Email already exists"
                }, status=400)

            # ✅ Create staff profile
            staff = StaffProfile.objects.create(
                restaurant=restaurant,
                vendor=vendor,
                staff_name=staff_name,
                email=email,
                phone_no=phone_no,
                work_days=work_days,
                work_time=work_time,
                work_status=work_status,
                department=department,
                role=role,
                profile_photo=profile_photo
            )

            return JsonResponse({
                "status": True,
                "message": "Staff profile created successfully",
                "data": {
                    "id": staff.id,
                    "staff_name": staff.staff_name,
                    "email": staff.email,
                    "phone_no": staff.phone_no,
                    "profile_photo": staff.profile_photo.url if staff.profile_photo else None
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class GetStaffListAPI(View):

    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            department = request.POST.get("department", "all")

            # 🔹 Validation
            if not vendor_id or not restaurant_id:
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id and restaurant_id are required"
                }, status=400)

            # 🔹 Base Query
            staff_queryset = StaffProfile.objects.filter(
                vendor_id=vendor_id,
                restaurant_id=restaurant_id
            )

            # 🔹 Department Filter
            if department.lower() != "all":
                staff_queryset = staff_queryset.filter(
                    department__iexact=department
                )

            # 🔹 Response Data
            staff_list = []
            for staff in staff_queryset:

                # Profile Image URL
                if staff.profile_photo:
                    image_url = request.build_absolute_uri(
                        staff.profile_photo.url
                    )
                else:
                    image_url = None

                staff_list.append({
                    "id": staff.id,
                    "profile_image": image_url,
                    "staff_name": staff.staff_name,
                    "role": staff.role,
                    "email": staff.email,
                    "phone_no": staff.phone_no,
                    "work_days": staff.work_days,
                    "work_time": staff.work_time,
                    "joined_at": staff.joined_at,
                    "work_status": staff.work_status,
                    "department": staff.department
                })

            return JsonResponse({
                "status": True,
                "total_staff": staff_queryset.count(),
                "data": staff_list
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)   

@method_decorator(csrf_exempt, name='dispatch')
class RestaurantDashboardAPI(View):
    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")

            if not vendor_id or not restaurant_id:
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id and restaurant_id are required"
                }, status=400)

            today = timezone.now().date()

            # 🔹 Today's Orders
            today_orders = Orders.objects.filter(
                items__restaurant_id=restaurant_id,
                items__restaurant__vendorid_id=vendor_id,
                created_at__date=today
            ).distinct()

            total_orders_today = today_orders.count()

            # 🔹 Pending Orders Today
            pending_orders_today = today_orders.filter(
                status="pending"
            ).count()

            # 🔹 Today's Earnings
            todays_earning = today_orders.filter(
                payment__payment_status="success"
            ).aggregate(
                total=Sum("paid_amount")
            )["total"] or 0

            # 🔹 Total Menu Items
            total_menu_items = MenuItems.objects.filter(
                restaurant_id=restaurant_id
            ).count()

            return JsonResponse({
                "status": True,
                "data": {
                    "today_total_orders": total_orders_today,
                    "today_pending_orders": pending_orders_today,
                    "today_total_earning": todays_earning,
                    "total_menu_items": total_menu_items
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RestaurantReportAPI(View):
    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            filter_type = request.POST.get("filter", "today")

            now = timezone.now()

            # ------------------------
            # DATE FILTERS
            # ------------------------

            if filter_type == "today":
                start_date = now.replace(hour=0, minute=0, second=0)
                last_start = start_date - timedelta(days=1)

            elif filter_type == "week":
                start_date = now - timedelta(days=7)
                last_start = start_date - timedelta(days=7)

            elif filter_type == "month":
                start_date = now - timedelta(days=30)
                last_start = start_date - timedelta(days=30)

            elif filter_type == "year":
                start_date = now - timedelta(days=365)
                last_start = start_date - timedelta(days=365)

            else:
                start_date = now.replace(hour=0, minute=0, second=0)
                last_start = start_date - timedelta(days=1)

            # ------------------------
            # BASE QUERY
            # ------------------------

            orders = Orders.objects.filter(
                items__restaurant_id=restaurant_id,
                items__restaurant__vendorid_id=vendor_id,
                created_at__gte=start_date
            ).distinct()

            last_orders = Orders.objects.filter(
                items__restaurant_id=restaurant_id,
                items__restaurant__vendorid_id=vendor_id,
                created_at__gte=last_start,
                created_at__lt=start_date
            ).distinct()

            # ------------------------
            # EARNINGS
            # ------------------------

            total_earning = orders.aggregate(
                total=Sum("paid_amount")
            )["total"] or 0

            last_earning = last_orders.aggregate(
                total=Sum("paid_amount")
            )["total"] or 0

            if last_earning > 0:
                earning_percent = ((total_earning - last_earning) / last_earning) * 100
            else:
                earning_percent = 0

            total_orders = orders.count()

            avg_order_value = orders.aggregate(
                avg=Avg("paid_amount")
            )["avg"] or 0

            # ------------------------
            # ORDER SECTION
            # ------------------------

            completed_orders = orders.filter(status="delivered").count()

            cancelled_orders = orders.filter(status="cancelled").count()

            rejected_orders = orders.filter(status="rejected").count()

            # ------------------------
            # RECENT TRANSACTIONS
            # ------------------------

            recent_orders = orders.order_by("-created_at")[:5]

            transactions = []

            for order in recent_orders:

                first_item = order.items.first()

                image = None

                if first_item and first_item.menu_item.menu_images:
                    image = first_item.menu_item.menu_images[0]

                transactions.append({
                    "order_id": order.id,
                    "order_uuid": str(order.order_uuid),
                    "order_image": image,
                    "amount": order.paid_amount,
                    "customer_name": order.user.name if hasattr(order.user, "name") else "",
                    "date": order.created_at,
                    "status": order.status
                })

            # ------------------------
            # TOP SELLING ITEMS
            # ------------------------

            items = CartItems.objects.filter(
                restaurant_id=restaurant_id,
                order__created_at__gte=start_date
            )

            top_items = items.values(
                "menu_item__name",
                "menu_item__price"
            ).annotate(
                sold_count=Sum("quantity")
            ).order_by("-sold_count")[:5]

            total_items_sold = items.aggregate(
                total=Sum("quantity")
            )["total"] or 0

            # ------------------------
            # CUSTOMER SECTION
            # ------------------------

            users = orders.values("user").distinct()

            new_customers = UserRegister.objects.filter(
                orders__created_at__gte=start_date
            ).distinct().count()

            returning_customers = orders.values(
                "user"
            ).annotate(
                count=Count("id")
            ).filter(count__gt=1).count()

            if new_customers > 0:
                return_rate = (returning_customers / new_customers) * 100
            else:
                return_rate = 0

            # ------------------------
            # CUSTOMER INSIGHTS
            # ------------------------

            top_customer = orders.values(
                "user__name"
            ).annotate(
                total_orders=Count("id")
            ).order_by("-total_orders").first()

            peak_time = orders.annotate(
                hour=TruncHour("created_at")
            ).values("hour").annotate(
                count=Count("id")
            ).order_by("-count").first()

            # ------------------------
            # FINAL RESPONSE
            # ------------------------

            return JsonResponse({

                "status": True,

                "earnings": {
                    "total_earning": total_earning,
                    "percent_from_last": round(earning_percent, 2),
                    "total_orders": total_orders,
                    "avg_order_value": round(avg_order_value, 2)
                },

                "orders": {
                    "completed_orders": completed_orders,
                    "cancelled_orders": cancelled_orders,
                    "rejected_orders": rejected_orders
                },

                "recent_transactions": transactions,

                "item_section": {
                    "top_selling_items": list(top_items),
                    "total_items_sold": total_items_sold
                },

                "customers": {
                    "new_customers": new_customers,
                    "returning_customers": returning_customers,
                    "return_rate": round(return_rate, 2)
                },

                "customer_insights": {
                    "top_customer": top_customer,
                    "peak_order_time": peak_time
                }

            })

        except Exception as e:

            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            

@method_decorator(csrf_exempt, name='dispatch')
class GenerateOutForDeliveryOTPAPI(View):

    def post(self, request):
        try:
            order_id = request.POST.get("order_id")
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")

            if not order_id or not vendor_id or not restaurant_id:
                return JsonResponse({
                    "status": False,
                    "message": "order_id, vendor_id and restaurant_id are required"
                }, status=400)

            # Check vendor
            vendor = VendorRegistration.objects.filter(id=vendor_id).first()
            if not vendor:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # Check restaurant
            restaurant = Restaurant.objects.filter(
                id=restaurant_id,
                vendorid=vendor
            ).first()

            if not restaurant:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found for this vendor"
                }, status=404)

            # Check order
            order = Orders.objects.filter(id=order_id).first()
            if not order:
                return JsonResponse({
                    "status": False,
                    "message": "Order not found"
                }, status=404)

            # Generate 4 digit OTP
            otp = str(random.randint(1000, 9999))

            # Save OTP
            order.delivery_otp = otp
            order.save()

            return JsonResponse({
                "status": True,
                "message": "Delivery OTP generated successfully",
                "data": {
                    "order_id": order.id,
                    "delivery_otp": otp
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
    
            
@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPForOutForDeliveryAPI(View):

    def post(self, request):
        try:
            order_id = request.POST.get("order_id")
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")
            otp = request.POST.get("otp")

            if not order_id or not vendor_id or not restaurant_id or not otp:
                return JsonResponse({
                    "status": False,
                    "message": "order_id, vendor_id, restaurant_id and otp are required"
                }, status=400)

            # Check vendor
            vendor = VendorRegistration.objects.filter(id=vendor_id).first()
            if not vendor:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # Check restaurant
            restaurant = Restaurant.objects.filter(
                id=restaurant_id,
                vendorid=vendor
            ).first()

            if not restaurant:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found for this vendor"
                }, status=404)

            # Check order
            order = Orders.objects.filter(id=order_id).first()
            if not order:
                return JsonResponse({
                    "status": False,
                    "message": "Order not found"
                }, status=404)

            # Verify OTP
            if order.delivery_otp != otp:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid OTP"
                }, status=400)

            # Find delivery partner who accepted the order
            action = DeliveryPartnerOrderAction.objects.filter(
                order=order,
                action="accepted"
            ).select_related("delivery_partner").first()

            if not action:
                return JsonResponse({
                    "status": False,
                    "message": "No delivery partner accepted this order"
                }, status=400)

            # Assign delivery partner
            order.delivery_partner = action.delivery_partner
            order.status = "out_for_delivery"
            order.save()

            return JsonResponse({
                "status": True,
                "message": "OTP verified. Order is now out for delivery.",
                "data": {
                    "order_id": order.id,
                    "delivery_partner": action.delivery_partner.full_name,
                    "status": order.status
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)                 
            


@method_decorator(csrf_exempt, name='dispatch')            
class CreateRestaurantTable(View):
    
    def post(self, request):
        
        restaurant_id= request.POST.get("restraurant_id")
        seats=request.POST.get("seats")
        table_name = request.POST.get("table_name")
        price = request.POST.get("price")
        duration =request.POST.get("duration")
        description = request.POST.get("description")
        images = request.FILES.getlist("images")
        
        if not restaurant_id or not seats or not price or not duration:
            return JsonResponse({
                "status":False,
                "message": "restaurant_id, seats, price and duration are required"
                
            })
            
        restaurant = Restaurant.objects.filter(id=restaurant_id).first()
        
        if not restaurant:
            return JsonResponse({
                "status": False,
                "message": "Restaurant not found"
            })
            
        image_urls = []
        
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "table_images"))
        
        for image in images:
            filename = fs.save(image.name,image)
            file_url=settings.MEDIA_URL + "table_images/"+ filename
            image_urls.append(file_url)
            
            
        #create_table
        
        table = RestaurantTable.objects.create(
            restaurant =restaurant,
            seats = seats,
            table_name = table_name,
            price = price,
            duration = duration,
            description = description,
            images=image_urls,
            
            
        )
        
        return JsonResponse({
            "status":True,
            "message":"Table created Successfually",
            "table_id":table.id,
            "images":image_urls,
        })
            

@method_decorator(csrf_exempt, name='dispatch')
class GetRestaurantTables(View):

    def post(self, request):

        restaurant_id = request.POST.get("restaurant_id")

        if not restaurant_id: 
            return JsonResponse({
                "status": False,
                "message": "restaurant_id is required"
            })

        restaurant = Restaurant.objects.filter(id=restaurant_id).first()

        if not restaurant:
            return JsonResponse({
                "status": False,
                "message": "Restaurant not found"
            })

        tables = RestaurantTable.objects.filter(restaurant_id=restaurant_id)

        table_list = []

        for table in tables:
            table_list.append({
                "table_id": table.id,
                "table_name": table.table_name,
                "seats": table.seats,
                "price": str(table.price),
                "duration": table.duration,
                "description": table.description,
                "images": table.images,
                "status": table.status,
                "next_available_time": table.next_available_time,
                "created_at": table.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return JsonResponse({
            "status": True,
            "restaurant_id": restaurant_id,
            "tables": table_list
        })
        
        
class FeaturedCategoryListView(View):

    def get(self, request):
        try:
            categories = FeaturedCategory.objects.all()

            data = []
            for cat in categories:
                data.append({
                    "id": cat.id,
                    "category_name": cat.category_name,
                    "created_at": cat.created_at.strftime("%d %b %Y")  # formatted date
                })

            return JsonResponse({
                "status": True,
                "message": "Featured categories fetched successfully",
                "data": data
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            
            
@method_decorator(csrf_exempt, name='dispatch')
class PendingOrderCountAPI(View):

    def post(self, request):
        try:
            vendor_id = request.POST.get("vendor_id")
            restaurant_id = request.POST.get("restaurant_id")

            if not all([vendor_id, restaurant_id]):
                return JsonResponse({
                    "status": False,
                    "message": "vendor_id and restaurant_id are required"
                }, status=400)

            # ✅ Validate Vendor
            try:
                vendor = VendorRegistration.objects.get(id=vendor_id)
            except VendorRegistration.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Vendor not found"
                }, status=404)

            # ✅ Validate Restaurant
            try:
                restaurant = Restaurant.objects.get(
                    id=restaurant_id,
                    vendorid=vendor
                )
            except Restaurant.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found or not owned by vendor"
                }, status=404)

            # ✅ Count Pending Orders
            pending_orders_count = Orders.objects.filter(
                items__restaurant=restaurant,
                status="pending"   # 🔥 important
            ).distinct().count()

            return JsonResponse({
                "status": True,
                "message": "Pending orders count fetched successfully",
                "pending_orders_count": pending_orders_count
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            
