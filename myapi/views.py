
from collections import defaultdict
from decimal import Decimal
import json
# from turtle import radians
from math import radians, sin, cos, sqrt, asin
from datetime import date, timedelta
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.views import View
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from myapi.models import *
from vendorapi.models import *
import random
from django.db.models import Avg, Sum
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.core.files.storage import FileSystemStorage
@method_decorator(csrf_exempt, name='dispatch')
class UserRegisterView(View):
    def post(self,request):
        try:
            name=request.POST.get("name")
            profile_image=request.POST.get("profile_image")
            email =request.POST.get("email")
            phone_no=request.POST.get("phone_no")
            password =request.POST.get("password")
            if not name or not email or not phone_no or not password:
                return JsonResponse({
                    "status":False,
                    "message":"Name email phone_no and password is required "
                    
                }, status=400)
                
            if UserRegister.objects.filter(email=email).exists():
                return JsonResponse({
                    "status":False,
                    "message":"Email already exists"
                },status=400)
            
            if UserRegister.objects.filter(phone_no=phone_no).exists():
                return JsonResponse({
                    "status":False,
                    "message":"Phone no already Exists"
                })
            
            #Create User 
            user =UserRegister.objects.create(
                name = name,
                email =email,
                phone_no=phone_no,
                password = make_password(password),
                profile_image = profile_image,
                
            )
            
            UserCart.objects.create(user=user)
            
            UserWallet.objects.get_or_create(user=user)
            return JsonResponse(
                {
                    "status":True,
                    "message":"User registered successfully",
                    "user_id":user.id,
                    "profile_img":user.profile_image if user.profile_image else None,
                    
                } ,status=201)
            
        except Exception as e:
            return JsonResponse({
                "status":False,
                "message":str(e),
                
            }, status=500)
            
            
@method_decorator(csrf_exempt, name='dispatch')             
class UserLoginAPI(View):
    def post(self, request):
        email = request.POST.get('email')
        # mobile= request.POST.get('mobile_no')
        password= request.POST.get('password')
        if  not password:
            return JsonResponse({
                "status":False,
                "message":"Password is required",
            },status=200)       
        if not email:
            return JsonResponse({
                "status": False,
                "message": "Enter the field",
            }, status=400)
        try:
            if email.isdigit():
             user=UserRegister.objects.get(phone_no=email)
            else:
                user=UserRegister.objects.get(email=email)
        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status":False,
                "message":"User not Found",
            },status=200)
        if not check_password(password, user.password):
            return JsonResponse({
                "status":False,
                "message":"Invalid Password",
            })
        otp = str(random.randint(1000,9999))
        
        userOTP.objects.create(
            user=user,
            otp=otp,
        )
        return JsonResponse({
            "status":True,
            "message":"OTP sent successfully",
            "user_id":user.id,
            "phone":user.phone_no,
            "OTP":otp,
        })
        
        
@method_decorator(csrf_exempt, name='dispatch')       
class VerifyUserOTP(View):
    def post(self, request):
        
        user_id = request.POST.get("user_id")
        otp = request.POST.get("otp")
        
        if not user_id or not otp:
            return JsonResponse({
                "status":False,
                "message":"user id and otp is required",
            },status=200)
        
        try:
            user_otp=userOTP.objects.filter(user_id=user_id, otp=otp, is_verified=False).latest('created_at')
            user =UserRegister.objects.get(id=user_id)
        except userOTP.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Invalid OTP"
            }, status=200)
        user_otp.is_verified = True
        user_otp.save()
        return JsonResponse({
            "status": True,
            "message": "Login successful",
            "user":{
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "phone_no": user.phone_no
            }
        })
        
        
@method_decorator(csrf_exempt, name='dispatch')
class UpdateUserLocationView(View):

    def post(self, request):

        user_id = request.POST.get("user_id")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        # ✅ Check required fields
        if not user_id or not latitude or not longitude:
            return JsonResponse({
                "status": False,
                "message": "user_id, latitude and longitude required"
            }, status=200)

        try:
            user = UserRegister.objects.get(id=user_id)
        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            }, status=200)

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return JsonResponse({
                "status": False,
                "message": "Invalid latitude or longitude format"
            }, status=200)

        # ✅ Validate range
        if latitude < -90 or latitude > 90:
            return JsonResponse({
                "status": False,
                "message": "Latitude must be between -90 and 90"
            }, status=200)

        if longitude < -180 or longitude > 180:
            return JsonResponse({
                "status": False,
                "message": "Longitude must be between -180 and 180"
            }, status=200)

        # ✅ Update location
        user.latitude = latitude
        user.longitude = longitude
        user.save()

        return JsonResponse({
            "status": True,
            "message": "Location updated successfully",
            "data": {
                "user_id": user.id,
                "latitude": str(user.latitude),
                "longitude": str(user.longitude)
            }
        }, status=200)
        
        


@method_decorator(csrf_exempt, name='dispatch')
class ExploreAPI(View):
    def get(self, request):

        # ✅ 1. Global Categories
        categories = GlobalCategory.objects.all()

        category_list = []
        for cat in categories:
            category_list.append({
                "id": cat.id,
                "name": cat.catgname,
                "category_images":cat.images,
            })

        # ✅ 2. Popular Menu Items
        popular_items = (
            MenuItems.objects
            .filter(is_available=True)
            .annotate(
                avg_rating=Avg("restaurant__ratings__rating"),
                total_ratings=Count("ratings")
            )
            .order_by("-avg_rating", "-total_ratings")[:10]   # top 10
        )

        popular_list = []

        for item in popular_items:
            popular_list.append({
                "menu_id": item.id,
                "name": item.name,
                "price": str(item.price),
                "images": item.menu_images,
                "veg_nonveg": item.VegNonVeg,
                "restaurant_id": item.restaurant.id,
                "restaurant_name": item.restaurant.restaurantname,
                "avg_rating": round(item.avg_rating, 1) if item.avg_rating else 0,
                "total_ratings": item.total_ratings
            })

        return JsonResponse({
            "status": True,
            "categories": category_list[::-1],
            "popular_items": popular_list
        })
        
        
        
# @method_decorator(csrf_exempt, name='dispatch')
# class GetMenuByGlobalCategory(View):

#     def post(self, request):

#         category_id = request.POST.get("category_id")

#         if not category_id:
#             return JsonResponse({
#                 "status": False,
#                 "message": "category_id is required"
#             }, status=400)

#         try:
#             category = GlobalCategory.objects.get(id=category_id)
#         except GlobalCategory.DoesNotExist:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Invalid category"
#             }, status=404)

#         # ✅ Fetch menu items under this category
#         menu_items = (
#             MenuItems.objects
#             .filter(globalCategory_id=category_id, is_available=True)
#             .select_related("restaurant")
#             .annotate(
#                 avg_rating=Avg("restaurant__ratings__rating"),
#                 total_ratings=Count("ratings")
#             )
#             .order_by("-avg_rating", "-total_ratings")
#         )

#         items_list = []

#         for item in menu_items:
#             items_list.append({
#                 "menu_id": item.id,
#                 "name": item.name,
#                 "price": str(item.price),
#                 "images": item.menu_images,
#                 "veg_nonveg": item.VegNonVeg,
#                 "description": item.description,

#                 "restaurant_id": item.restaurant.id,
#                 "restaurant_name": item.restaurant.restaurantname,

#                 "avg_rating": round(item.avg_rating, 1) if item.avg_rating else 0,
#                 "total_ratings": item.total_ratings,

#                 "discount": item.discountdetails
#             })

#         return JsonResponse({
#             "status": True,
#             "category": {
#                 "id": category.id,
#                 "name": category.catgname
#             },
#             "total_items": len(items_list),
#             "items": items_list
#         })

        
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c  # distance in KM

@method_decorator(csrf_exempt, name='dispatch')
class RestaurantByCategoryView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")
            global_category_id = request.POST.get("global_category_id")

            search = request.POST.get("search", "").strip().lower()
            filter_type = request.POST.get("filter_type", "all")  # all / high_rated / open_now
            veg_filter = request.POST.get("veg", "all")  # all / veg

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            if not user.latitude or not user.longitude:
                return JsonResponse({
                    "status": False,
                    "message": "User location not found"
                })

            user_lat = user.latitude
            user_lon = user.longitude

            # ✅ Base queryset
            restaurants = Restaurant.objects.filter(
                menu_items__globalCategory_id=global_category_id
            ).distinct()

            # ✅ Search filter
            if search:
                restaurants = restaurants.filter(
                    restaurantname__icontains=search
                )

            # ✅ Veg filter
            if veg_filter == "veg":
                restaurants = restaurants.filter(
                    menu_items__VegNonVeg="Veg"
                ).distinct()

            response_data = []

            for restaurant in restaurants:

                if not restaurant.latitude or not restaurant.longitude:
                    continue

                # ✅ Distance
                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    restaurant.latitude,
                    restaurant.longitude
                )

                if distance > 20:
                    continue

                # ✅ Rating
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg_rating=Avg("rating"))["avg_rating"] or 0

                # ✅ Delivery Time
                time_minutes = int((distance / 40) * 60)

                data = {
                    "restaurant_id": restaurant.id,
                    "restaurant_name": restaurant.restaurantname,
                    "restaurantImage": restaurant.restaurantimage,
                    "rating": round(rating, 1),
                    "is_open": restaurant.is_open,
                    "distance_km": round(distance, 2),
                    "delivery_time_minutes": time_minutes
                }

                # ✅ Open Now filter
                if filter_type == "open_now" and not restaurant.is_open:
                    continue

                response_data.append(data)

            # ✅ Sorting
            if filter_type == "high_rated":
                response_data.sort(key=lambda x: x["rating"], reverse=True)
            else:
                response_data.sort(key=lambda x: x["distance_km"])

            return JsonResponse({
                "status": True,
                "data": response_data
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })



# @method_decorator(csrf_exempt, name='dispatch')
# class RestaurantDetailWithMenuView(View):

#     def post(self, request):
#         try:
#             restaurant_id = request.POST.get("restaurant_id")
#             user_id = request.POST.get("user_id")
#             search_name = request.POST.get("search", "").strip().lower()

#             # ✅ Validate required fields
#             if not restaurant_id or not user_id:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "restaurant_id and user_id are required"
#                 })

#             # ✅ Get restaurant
#             restaurant = Restaurant.objects.get(id=restaurant_id)

#             # ✅ Get user location ONLY from DB
#             try:
#                 user = UserRegister.objects.get(id=user_id)
#                 user_lat = user.latitude
#                 user_lng = user.longitude
#             except UserRegister.DoesNotExist:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "User not found"
#                 })

#             # ✅ Distance Calculation
#             distance_km = None
#             distance_minutes = None

#             if user_lat and user_lng and restaurant.latitude and restaurant.longitude:

#                 distance_km = round(
#                     calculate_distance(
#                         user_lat,
#                         user_lng,
#                         restaurant.latitude,
#                         restaurant.longitude
#                     ), 2
#                 )

#                 # realistic delivery time
#                 distance_minutes = max(5, round((distance_km / 30) * 60))

#             # ✅ Categories
#             categories = Categories.objects.filter(restaurant=restaurant)

#             category_list = []
#             for cat in categories:
#                 category_list.append({
#                     "id": cat.id,
#                     "name": cat.categories_name,
#                     "image": cat.category_images
#                 })

#             # ✅ Menu Items
#             menu_items = MenuItems.objects.filter(
#                 restaurant=restaurant,
#                 is_available=True
#             ).select_related("categories")

#             matched_items = []
#             other_items = []

#             for item in menu_items:
#                 item_data = {
#                     "id": item.id,
#                     "name": item.name,
#                     "price": str(item.price),
#                     "price_afterDesc": str(item.price_afterDesc) if item.price_afterDesc else None,
#                     "images": item.menu_images,
#                     "veg_nonveg": item.VegNonVeg,
#                     "description": item.description,
#                     "discount": item.get_discount_display(),
#                     "prep_time": item.get_prep_time_display() if item.prep_time else None,
#                     "category": item.categories.categories_name if item.categories else None
#                 }

#                 if search_name and search_name in item.name.lower():
#                     matched_items.append(item_data)
#                 else:
#                     other_items.append(item_data)

#             final_menu = matched_items + other_items if search_name else other_items

#             # ✅ Final Response
#             return JsonResponse({
#                 "status": True,
#                 "data": {
#                     "restaurant": {
#                         "id": restaurant.id,
#                         "name": restaurant.restaurantname,
#                         "images": restaurant.restaurantimage,
#                         "distance_km": distance_km,
#                         "distance_minutes": distance_minutes
#                     },
#                     "categories": category_list,
#                     "menu": final_menu
#                 }
#             })

#         except Restaurant.DoesNotExist:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Restaurant not found"
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             })


@method_decorator(csrf_exempt, name='dispatch')
class RestaurantDetailWithMenuView(View):

    def post(self, request):
        try:
            restaurant_id = request.POST.get("restaurant_id")
            user_id = request.POST.get("user_id")
            search_name = request.POST.get("search", "").strip().lower()

            if not restaurant_id or not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "restaurant_id and user_id are required"
                })

            # ✅ Get restaurant & user
            restaurant = Restaurant.objects.get(id=restaurant_id)
            user = UserRegister.objects.get(id=user_id)

            user_lat = user.latitude
            user_lon = user.longitude

            # ✅ Distance
            distance_km = None
            distance_minutes = None

            if user_lat and user_lon and restaurant.latitude and restaurant.longitude:
                distance_km = round(
                    calculate_distance(
                        user_lat,
                        user_lon,
                        restaurant.latitude,
                        restaurant.longitude
                    ), 2
                )
                distance_minutes = max(5, round((distance_km / 30) * 60))

            # ✅ Wishlist
            wishlist_ids = set(
                Wishlist.objects.filter(user_id=user_id)
                .values_list("menu_item_id", flat=True)
            )

            # ✅ Cart mapping
            cart_items_map = {}
            try:
                cart = user.cart
                cart_items = CartItems.objects.filter(
                    cart=cart,
                    order__isnull=True
                )
                cart_items_map = {
                    item.menu_item_id: item.quantity
                    for item in cart_items
                }
            except UserCart.DoesNotExist:
                pass

            # ✅ Categories
            categories = Categories.objects.filter(restaurant=restaurant)
            category_list = [{
                "id": cat.id,
                "name": cat.categories_name,
                "image": cat.category_images
            } for cat in categories]

            # ✅ Menu Items (optimized like first API)
            menu_items = MenuItems.objects.filter(
                restaurant=restaurant,
                is_available=True
            ).annotate(
                total_orders=Count("order_items")
            ).select_related("restaurant", "categories")

            matched_items = []
            other_items = []

            # ✅ Restaurant rating (single query ⚡)
            restaurant_rating = RestaurantRating.objects.filter(
                restaurant=restaurant
            ).aggregate(avg=Avg("rating"))["avg"] or 0

            for item in menu_items:

                is_wishlisted = item.id in wishlist_ids
                cart_qty = cart_items_map.get(item.id, 0)

                total_orders = item.total_orders or 0
                highly_ordered_percent = min(total_orders * 2, 100)

                has_addons = item.addons.filter(is_available=True).exists()

                item_data = {
                    "menu_id": item.id,
                    "restaurant_id": restaurant.id,
                    "menu_name": item.name,
                    "description": item.description,
                    "menu_image": item.menu_images,
                    "discount_percent": item.discount,
                    "halal": item.halal_attribute,
                    "veg_nonveg": item.VegNonVeg,
                    "spicy": item.sypicy,
                    "prep_time": item.get_prep_time_display() if item.prep_time else None,

                    "actual_price": str(item.price),
                    "price_after_discount": str(item.price_afterDesc) if item.price_afterDesc else None,

                    "restaurant_name": restaurant.restaurantname,
                    "distance_km": distance_km,
                    "restaurant_rating": round(restaurant_rating, 1),

                    "total_orders": total_orders,
                    "highly_ordered_percent": highly_ordered_percent,
                    "consumables": has_addons,
                    "free_delivery": False,
                    "is_wishlisted": is_wishlisted,
                    "cart_quantity": cart_qty,

                    "category": item.categories.categories_name if item.categories else None
                }

                # ✅ Search priority logic
                if search_name and search_name in item.name.lower():
                    matched_items.append(item_data)
                else:
                    other_items.append(item_data)

            final_menu = matched_items + other_items if search_name else other_items

            # ✅ Sort like first API
            final_menu.sort(
                key=lambda x: (-x["highly_ordered_percent"], x["distance_km"] or 0)
            )

            return JsonResponse({
                "status": True,
                "data": {
                    "restaurant": {
                        "id": restaurant.id,
                        "name": restaurant.restaurantname,
                        "images": restaurant.restaurantimage,
                        "distance_km": distance_km,
                        "distance_minutes": distance_minutes,
                        "rating": round(restaurant_rating, 1)
                    },
                    "categories": category_list,
                    "menu": final_menu
                }
            })

        except Restaurant.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Restaurant not found"
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class TodaysSpecialMenuItemsView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            if not user.latitude or not user.longitude:
                return JsonResponse({
                    "status": False,
                    "message": "User location not found"
                })

            user_lat = user.latitude
            user_lon = user.longitude 
            
            featured = FeaturedCategory.objects.filter(
            category_name__iexact="Today's Special"
            ).first()
            
            print(featured.id)

            # ✅ Filter ONLY "Today's Special" menu items
            menu_items = MenuItems.objects.select_related(
            "restaurant", "featured_category"
             ).filter(
             featured_category=featured,
             
             ).annotate(
             total_orders=Count("order_items")
             )
             
            print(menu_items)

            response_data = []
            
            cart = None
            cart_items_map = {}

            try:
              cart = user.cart  # OneToOneField
              cart_items = CartItems.objects.filter(
              cart=cart,
              order__isnull=True
              )

              # ✅ Create map for fast lookup (IMPORTANT ⚡)
              cart_items_map = {
              item.menu_item_id: item.quantity
              for item in cart_items
              }

            except UserCart.DoesNotExist:
               cart_items_map = {}
               
            wishlist_ids = set()

            wishlist_ids = set(
            Wishlist.objects.filter(user_id=user_id)
            .values_list("menu_item_id", flat=True)
            )

               
               

            for item in menu_items:
                
                print(item.name)

                restaurant = item.restaurant
                
                is_wishlisted = item.id in wishlist_ids
                
                cart_qty = cart_items_map.get(item.id, 0)

                # skip invalid restaurant
                if not restaurant.latitude or not restaurant.longitude:
                    print(f"Skipping {restaurant.restaurantname} due to missing location")
                    continue

                if not restaurant.is_active or restaurant.approveStatus != "approved":
                    print(f"Skipping {restaurant.restaurantname} as it's not active or approved")
                    continue

                # ✅ Distance
                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    restaurant.latitude,
                    restaurant.longitude
                )

                if distance > 20:
                    continue

                # ✅ Rating (optimized per restaurant)
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg=Avg("rating"))["avg"] or 0

                # ✅ Orders
                total_orders = item.total_orders or 0

                # ✅ Popularity %
                highly_ordered_percent = min(total_orders * 2, 100)
                
                has_addons = item.addons.filter(is_available=True).exists()

                data = {
                    "menu_id": item.id,
                    "restaurant_id":item.restaurant.id,
                    "menu_name": item.name,
                    "description": item.description,
                    "menu_image": item.menu_images,
                    "discount_percent": item.discount,
                    "halal": item.halal_attribute,
                    "veg_nonveg": item.VegNonVeg,
                    "spicy": item.sypicy,
                    "prep_time": item.get_prep_time_display() if item.prep_time else None,

                    "actual_price": str(item.price),
                    "price_after_discount": str(item.price_afterDesc) if item.price_afterDesc else None,

                    "restaurant_name": restaurant.restaurantname,
                    "distance_km": round(distance, 2),
                    "restaurant_rating": round(rating, 1),

                    "total_orders": total_orders,
                    "highly_ordered_percent": highly_ordered_percent,
                    "consumables": has_addons,
                    "free_delivery":False,
                    "is_wishlisted": is_wishlisted,
                    "cart_quantity": cart_qty
                }

                response_data.append(data)

            # ✅ Sort: popular first, then nearest
            response_data.sort(
                key=lambda x: (-x["highly_ordered_percent"], x["distance_km"])
            )

            return JsonResponse({
                "status": True,
                "data": response_data
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class KeenoPicksTodayMenuItemsView(View):
    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            if not user.latitude or not user.longitude:
                return JsonResponse({
                    "status": False,
                    "message": "User location not found"
                })

            user_lat = user.latitude
            user_lon = user.longitude 
            
            featured = FeaturedCategory.objects.filter(
            category_name__iexact="Keeno Picks Today"
            ).first()
            
            print(featured.id)

            # ✅ Filter ONLY "Today's Special" menu items
            menu_items = MenuItems.objects.select_related(
            "restaurant", "featured_category"
             ).filter(
             featured_category=featured,
             
             ).annotate(
             total_orders=Count("order_items")
             )
             
            print(menu_items)

            response_data = []
            
            cart = None
            cart_items_map = {}

            try:
             cart = user.cart  # OneToOneField
             cart_items = CartItems.objects.filter(
             cart=cart,
             order__isnull=True
              )

            # ✅ Create map for fast lookup (IMPORTANT ⚡)
             cart_items_map = {
             item.menu_item_id: item.quantity
             for item in cart_items
             }

            except UserCart.DoesNotExist:
                 cart_items_map = {}
                 
            wishlist_ids = set()

            wishlist_ids = set(
            Wishlist.objects.filter(user_id=user_id)
            .values_list("menu_item_id", flat=True)
            )

            for item in menu_items:
                
                print(item.name)
                cart_qty = cart_items_map.get(item.id, 0)
                is_wishlisted = item.id in wishlist_ids

                restaurant = item.restaurant

                # skip invalid restaurant
                if not restaurant.latitude or not restaurant.longitude:
                    print(f"Skipping {restaurant.restaurantname} due to missing location")
                    continue

                if not restaurant.is_active or restaurant.approveStatus != "approved":
                    print(f"Skipping {restaurant.restaurantname} as it's not active or approved")
                    continue

                # ✅ Distance
                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    restaurant.latitude,
                    restaurant.longitude
                )

                if distance > 20:
                    continue

                # ✅ Rating (optimized per restaurant)
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg=Avg("rating"))["avg"] or 0

                # ✅ Orders
                total_orders = item.total_orders or 0

                # ✅ Popularity %
                highly_ordered_percent = min(total_orders * 2, 100)
                has_addons = item.addons.filter(is_available=True).exists()
                data = {
                    "menu_id": item.id,
                    "restaurant_id":item.restaurant.id,
                    "menu_name": item.name,
                    "description": item.description,
                    "menu_image": item.menu_images,
                    "discount_percent": item.discount,
                    "halal": item.halal_attribute,
                    "veg_nonveg": item.VegNonVeg,
                    "spicy": item.sypicy,
                    "prep_time": item.get_prep_time_display() if item.prep_time else None,

                    "actual_price": str(item.price),
                    "price_after_discount": str(item.price_afterDesc) if item.price_afterDesc else None,

                    "restaurant_name": restaurant.restaurantname,
                    "distance_km": round(distance, 2),
                    "restaurant_rating": round(rating, 1),

                    "total_orders": total_orders,
                    "highly_ordered_percent": highly_ordered_percent,
                    "consumables": has_addons,
                    "free_delivery":True,
                    "cart_quantity": cart_qty,
                    "is_wishlisted": is_wishlisted
                }

                response_data.append(data)

            # ✅ Sort: popular first, then nearest
            response_data.sort(
                key=lambda x: (-x["highly_ordered_percent"], x["distance_km"])
            )

            return JsonResponse({
                "status": True,
                "data": response_data
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class FamilyMealsMenuItemsView(View):
    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            if not user.latitude or not user.longitude:
                return JsonResponse({
                    "status": False,
                    "message": "User location not found"
                })

            user_lat = user.latitude
            user_lon = user.longitude 
            
            featured = FeaturedCategory.objects.filter(
            category_name__iexact="Family Meals"
            ).first()
            
            print(featured.id)

            # ✅ Filter ONLY "Today's Special" menu items
            menu_items = MenuItems.objects.select_related(
            "restaurant", "featured_category"
             ).filter(
             featured_category=featured,
             
             ).annotate(
             total_orders=Count("order_items")
             )
             
            print(menu_items)

            response_data = []
            
            cart = None
            cart_items_map = {}

            try:
             cart = user.cart  # OneToOneField
             cart_items = CartItems.objects.filter(
             cart=cart,
             order__isnull=True
             )

            # ✅ Create map for fast lookup (IMPORTANT ⚡)
             cart_items_map = {
               item.menu_item_id: item.quantity
             for item in cart_items
              }

            except UserCart.DoesNotExist:
              cart_items_map = {}
              
            wishlist_ids = set()

            wishlist_ids = set(
            Wishlist.objects.filter(user_id=user_id)
            .values_list("menu_item_id", flat=True)
             )

            for item in menu_items:
                
                print(item.name)
                
                cart_qty = cart_items_map.get(item.id, 0)
                is_wishlisted = item.id in wishlist_ids
                restaurant = item.restaurant

                # skip invalid restaurant
                if not restaurant.latitude or not restaurant.longitude:
                    print(f"Skipping {restaurant.restaurantname} due to missing location")
                    continue

                if not restaurant.is_active or restaurant.approveStatus != "approved":
                    print(f"Skipping {restaurant.restaurantname} as it's not active or approved")
                    continue
                # ✅ Distance
                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    restaurant.latitude,
                    restaurant.longitude
                )
                if distance > 20:
                    continue

                # ✅ Rating (optimized per restaurant)
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg=Avg("rating"))["avg"] or 0

                # ✅ Orders
                total_orders = item.total_orders or 0

                # ✅ Popularity %
                highly_ordered_percent = min(total_orders * 2, 100)
                has_addons = item.addons.filter(is_available=True).exists()
                data = {
                    "menu_id": item.id,
                    "restaurant_id":item.restaurant.id,
                    "menu_name": item.name,
                    "description": item.description,
                    "menu_image": item.menu_images,
                    "discount_percent": item.discount,
                    "halal": item.halal_attribute,
                    "veg_nonveg": item.VegNonVeg,
                    "spicy": item.sypicy,
                    "prep_time": item.get_prep_time_display() if item.prep_time else None,

                    "actual_price": str(item.price),
                    "price_after_discount": str(item.price_afterDesc) if item.price_afterDesc else None,

                    "restaurant_name": restaurant.restaurantname,
                    "distance_km": round(distance, 2),
                    "restaurant_rating": round(rating, 1),

                    "total_orders": total_orders,
                    "highly_ordered_percent": highly_ordered_percent,
                    "consumables": has_addons,
                    "free_delivery":False,
                    "cart_quantity": cart_qty,
                    "is_wishlisted": is_wishlisted
                    
                }

                response_data.append(data)

            # ✅ Sort: popular first, then nearest
            response_data.sort(
                key=lambda x: (-x["highly_ordered_percent"], x["distance_km"])
            )

            return JsonResponse({
                "status": True,
                "data": response_data
            })
        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
@method_decorator(csrf_exempt, name='dispatch')
class SpotlightListView(View):

    def get(self, request):
        try:
            spotlights = Spotlight.objects.all().order_by('-created_at')

            data = []

            for s in spotlights:
                data.append({
                    "id": s.id,
                    "spotlight_name": s.spotlight_name,
                    "spotlight_img": s.spotlight_img,
                    "created_at": s.created_at
                })

            return JsonResponse({
                "status": True,
                "data": data
            })
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class HighRatedNearbyMenuItemsView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            if not user.latitude or not user.longitude:
                return JsonResponse({
                    "status": False,
                    "message": "User location not found"
                })

            user_lat = user.latitude
            user_lon = user.longitude

            # ✅ Get all menu items
            menu_items = MenuItems.objects.select_related(
                "restaurant"
            ).annotate(
                total_orders=Count("order_items")
            )

            response_data = []
            
            cart = None
            cart_items_map = {}

            try:
             cart = user.cart  # OneToOneField
             cart_items = CartItems.objects.filter(
             cart=cart,
             order__isnull=True
              )

            # ✅ Create map for fast lookup (IMPORTANT ⚡)
             cart_items_map = {
             item.menu_item_id: item.quantity
             for item in cart_items
              }

            except UserCart.DoesNotExist:
              cart_items_map = {}
              
            wishlist_ids = set()

            wishlist_ids = set(
            Wishlist.objects.filter(user_id=user_id)
            .values_list("menu_item_id", flat=True)
            )

            for item in menu_items:

                restaurant = item.restaurant
                print(f"Evaluating {item.name} from {restaurant.restaurantname}")
                cart_qty = cart_items_map.get(item.id, 0)
                is_wishlisted = item.id in wishlist_ids
                # ❌ Skip invalid restaurant
                if not restaurant.latitude or not restaurant.longitude:
                    print(f"Skipping {restaurant.restaurantname} due to missing location")
                    continue

                if not restaurant.is_active or restaurant.approveStatus != "approved":
                    print(f"Skipping {restaurant.restaurantname} as it's not active or approved")
                    continue

                # ✅ Distance check
                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    restaurant.latitude,
                    restaurant.longitude
                )

                if distance > 20:
                    continue

                #  Rating
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg=Avg("rating"))["avg"] or 0

                #  Only HIGH RATED (>= 4)
                if rating > 4:
                    print(f"Skipping {item.name} as restaurant rating {rating} is below 4")
                    continue

                #  Orders
                total_orders = item.total_orders or 0

                #  Popularity %
                highly_ordered_percent = min(total_orders * 2, 100)

                #  Addons check
                has_addons = item.addons.filter(is_available=True).exists()

                data = {
                    "menu_id": item.id,
                    "restaurant_id":item.restaurant.id,
                    "menu_name": item.name,
                    "description": item.description,
                    "menu_image": item.menu_images,
                    "discount_percent": item.discount,
                    "halal": item.halal_attribute,
                    "veg_nonveg": item.VegNonVeg,
                    "spicy": item.sypicy,
                    "prep_time": item.get_prep_time_display() if item.prep_time else None,

                    "actual_price": str(item.price),
                    "price_after_discount": str(item.price_afterDesc) if item.price_afterDesc else None,

                    "restaurant_name": restaurant.restaurantname,
                    "distance_km": round(distance, 2),
                    "restaurant_rating": round(rating, 1),
                    "total_orders": total_orders,
                    "highly_ordered_percent": highly_ordered_percent,
                    "consumables": has_addons,
                    "free_delivery": True,
                    "cart_quantity": cart_qty,
                    "is_wishlisted": is_wishlisted
                }

                response_data.append(data)

            # ✅ Sort: highest rating first, then nearest
            response_data.sort(
                key=lambda x: (-x["restaurant_rating"], x["distance_km"])
            )

            return JsonResponse({
                "status": True,
                "data": response_data
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
            
@method_decorator(csrf_exempt, name='dispatch')
class PreviouslyOrderedOrNearbyMenuItemsView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            if not user.latitude or not user.longitude:
                return JsonResponse({
                    "status": False,
                    "message": "User location not found"
                })

            user_lat = user.latitude
            user_lon = user.longitude

            # ✅ Step 1: Get previously ordered menu items
            ordered_items_ids = CartItems.objects.filter(
                order__user=user
            ).values_list("menu_item_id", flat=True).distinct()

            if ordered_items_ids:
                print("Showing previously ordered items")

                menu_items = MenuItems.objects.select_related(
                    "restaurant"
                ).filter(
                    id__in=ordered_items_ids
                ).annotate(
                    total_orders=Count("order_items")
                )

            else:
                print("No previous orders → showing nearby items")

                menu_items = MenuItems.objects.select_related(
                    "restaurant"
                ).annotate(
                    total_orders=Count("order_items")
                )
            response_data = []
            
            
            cart = None
            cart_items_map = {}

            try:
              cart = user.cart  # OneToOneField
              cart_items = CartItems.objects.filter(
              cart=cart,
              order__isnull=True
              )

              # ✅ Create map for fast lookup (IMPORTANT ⚡)
              cart_items_map = {
              item.menu_item_id: item.quantity
              for item in cart_items
              }

            except UserCart.DoesNotExist:
               cart_items_map = {}
               
            wishlist_ids = set()

            wishlist_ids = set(
            Wishlist.objects.filter(user_id=user_id)
            .values_list("menu_item_id", flat=True)
            )

            for item in menu_items:

                restaurant = item.restaurant

                # ❌ Skip invalid restaurant
                if not restaurant.latitude or not restaurant.longitude:
                    continue

                if not restaurant.is_active or restaurant.approveStatus != "approved":
                    continue
                
                is_wishlisted = item.id in wishlist_ids
                
                cart_qty = cart_items_map.get(item.id, 0)

                # ✅ Distance
                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    restaurant.latitude,
                    restaurant.longitude
                )

                if distance > 20:
                    continue

                # ✅ Rating
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg=Avg("rating"))["avg"] or 0

                # ✅ Orders
                total_orders = item.total_orders or 0

                # ✅ Popularity %
                highly_ordered_percent = min(total_orders * 2, 100)

                # ✅ Addons
                has_addons = item.addons.filter(is_available=True).exists()

                data = {
                    "menu_id": item.id,
                    "menu_name": item.name,
                    "restaurant_id":item.restaurant.id,
                    "menu_image": item.menu_images,
                    "discount_percent": item.discount,
                    "halal": item.halal_attribute,
                    "veg_nonveg": item.VegNonVeg,
                    "spicy": item.sypicy,
                    "prep_time": item.get_prep_time_display() if item.prep_time else None,

                    "actual_price": str(item.price),
                    "price_after_discount": str(item.price_afterDesc) if item.price_afterDesc else None,

                    "restaurant_name": restaurant.restaurantname,
                    "distance_km": round(distance, 2),
                    "restaurant_rating": round(rating, 1),

                    "total_orders": total_orders,
                    "highly_ordered_percent": highly_ordered_percent,
                    "consumables": has_addons,
                    "free_delivery": True,
                    "cart_quantity": cart_qty,
                    "is_wishlisted": is_wishlisted,
                }

                response_data.append(data)

            # ✅ Sort
            response_data.sort(
                key=lambda x: (-x["highly_ordered_percent"], x["distance_km"])
            )

            return JsonResponse({
                "status": True,
                "data": response_data
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
            
@method_decorator(csrf_exempt, name='dispatch')
class NearbyRestaurantsView(View):
    def post(self, request):
        try:
            user_id = request.POST.get("user_id")
            filter_type = request.POST.get("filter_type", "all")  # all / high_rated / newly_join / take_away

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            if not user.latitude or not user.longitude:
                return JsonResponse({
                    "status": False,
                    "message": "User location not found"
                })

            user_lat = user.latitude
            user_lon = user.longitude

            restaurants = Restaurant.objects.filter(
                is_active=True,
                approveStatus="approved"
            )

            response_data = []

            for restaurant in restaurants:

                # ❌ Skip invalid location
                if not restaurant.latitude or not restaurant.longitude:
                    continue

                # ✅ Distance
                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    restaurant.latitude,
                    restaurant.longitude
                )
                if distance > 20:
                    continue

                # ✅ Rating
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg=Avg("rating"))["avg"] or 0

                # ✅ Filter Logic
                if filter_type == "high_rated" and rating < 4:
                    continue

                if filter_type == "take_away" and not restaurant.is_open:
                    continue

                # ✅ Menu items
                menu_items = restaurant.menu_items.all()
                total_menu_items = menu_items.count()

                menu_names = list(
                    menu_items.values_list("name", flat=True)[:3]
                )

                data = {
                    "restaurant_id": restaurant.id,
                    "restaurant_name": restaurant.restaurantname,
                    "restaurant_image": restaurant.restaurantimage,
                    "address": restaurant.adderess,
                    "distance_km": round(distance, 2),
                    "rating": round(rating, 1),

                    "menu_preview": menu_names,
                    "total_menu_items": total_menu_items,

                    "is_open": restaurant.is_open,
                    "created_at": restaurant.created_at
                }

                response_data.append(data)

            # ✅ Sorting
            if filter_type == "newly_join":
                response_data.sort(key=lambda x: x["created_at"], reverse=True)
            elif filter_type == "high_rated":
                response_data.sort(key=lambda x: -x["rating"])
            else:
                response_data.sort(key=lambda x: x["distance_km"])

            return JsonResponse({
                "status": True,
                "data": response_data
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })



@method_decorator(csrf_exempt, name='dispatch')
class AddToCartView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            user_id = data.get("user_id")
            menu_item_id = data.get("menu_item_id")
            restaurant_id = data.get("restaurant_id")
            quantity = int(data.get("quantity", 1))
            selectportion = data.get("selectportion", {}) or {}
            addon = data.get("addon", []) or []
            print(user_id)
            print(menu_item_id)
            print(restaurant_id)
            print("quanitty is:",quantity)
            print(selectportion)
            print(addon)
            if not user_id or not menu_item_id or not restaurant_id:
                return JsonResponse({
                    "status": False,
                    "message": "Required fields missing"
                }, status=400)

            # Get user
            user = UserRegister.objects.get(id=user_id)

            # Get or create cart
            cart, created = UserCart.objects.get_or_create(user=user)

            # Get menu item
            menu_item = MenuItems.objects.get(id=menu_item_id)

            # Get restaurant
            restaurant = Restaurant.objects.get(id=restaurant_id)

            # 🔥 Calculate price
            base_price = 0
            portion_price = Decimal(selectportion.get("item_price", 0))
            addon_total = sum(
                Decimal(item.get("item_price", 0)) for item in addon
            )
            final_price = (portion_price + addon_total)
            if not selectportion and not addon:
               final_price=0
               final_price = menu_item.price
            # Check if item already in cart (same menu + portion + addon)
            cart_item = CartItems.objects.filter(
                cart=cart,
                menu_item=menu_item,
                selectportion=selectportion,
                addon=addon,
                order__isnull=True
            ).first()
            if cart_item:
                cart_item.quantity += quantity
                cart_item.save()
            else:
                cart_item = CartItems.objects.create(
                    cart=cart,
                    menu_item=menu_item,
                    restaurant=restaurant,
                    quantity=quantity,
                    price_at_order_time=final_price,
                    selectportion=selectportion,
                    addon=addon
                )
            return JsonResponse({
                "status": True,
                "message": "Item added to cart",
                "cart_item_id": cart_item.id,
                "itemqty": cart_item.quantity
            })
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

            
@method_decorator(csrf_exempt, name='dispatch')
class ViewCartAPI(View):
    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id required"
                }, status=400)

            try:
                user = UserRegister.objects.get(id=user_id)
            except UserRegister.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "User not found"
                }, status=404)

            try:
                cart = user.cart
                print('Cart id is ',user.cart.id)
            except UserCart.DoesNotExist:
                return JsonResponse({
                    "status": True,
                    "message": "Cart is empty",
                    "restaurants": [],
                    "total_amount": "0.00"
                })

            cart_items = CartItems.objects.select_related(
                "menu_item",
                "restaurant"
            ).filter(
                cart=cart,
                order__isnull=True
            )

            if not cart_items.exists():
                return JsonResponse({
                    "status": True,
                    "restaurants": [],
                    "total_amount": "0.00"
                })

            restaurant_dict = defaultdict(lambda: {
                "restaurant_details": {},
                "items": [],
                "restaurant_total": Decimal("0.00")
            })

            grand_total = Decimal("0.00")

            for item in cart_items:
                restaurant = item.restaurant
                item_total = item.price_at_order_time * item.quantity
                grand_total += item_total

                if not restaurant_dict[restaurant.id]["restaurant_details"]:
                     avg_rating = RestaurantRating.objects.filter(
                     restaurant=restaurant
                     ).aggregate(avg=Avg("rating"))["avg"]

                     avg_rating = round(avg_rating, 1) if avg_rating else 0
                     restaurant_dict[restaurant.id]["restaurant_details"] = {
                        "restaurant_id": restaurant.id,
                        "cart_id":cart.id,
                        "restaurant_rating":avg_rating,
                        "restaurant_name": restaurant.restaurantname,
                        "restaurant_image": (
                            restaurant.restaurantimage[0]
                            if restaurant.restaurantimage
                            else None
                        ),
                        "address": restaurant.adderess
                    }

                restaurant_dict[restaurant.id]["items"].append({
                    "cart_item_id": item.id,
                    "menu_item_id": item.menu_item.id,
                    "menu_item_name": item.menu_item.name,
                    "quantity": item.quantity,
                    "price_per_item": str(item.price_at_order_time),
                    "item_total": str(item_total),
                    "selectportion": item.selectportion,
                    "addon": item.addon,
                    "menu_image": (
                        item.menu_item.menu_images[0]
                        if item.menu_item.menu_images
                        else None
                    )
                })

                restaurant_dict[restaurant.id]["restaurant_total"] += item_total

            # Convert Decimal to string
            response_data = []
            for data in restaurant_dict.values():
                data["restaurant_total"] = str(data["restaurant_total"])
                response_data.append(data)

            return JsonResponse({
                "status": True,
                "restaurant_count": len(response_data),
                "total_amount": str(grand_total),
                "cart_id":cart.id,
                "restaurants": response_data
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            
            
@method_decorator(csrf_exempt, name='dispatch')
class MenuDetailByUserView(View):

    def post(self, request):

        menu_id = request.POST.get("menu_id")
        user_id = request.POST.get("user_id")

        #  Check required field
        if not menu_id:
            return JsonResponse({
                "status": False,
                "message": "menu_id is required"
            }, status=200)

        #  Get Menu
        try:
            menu = MenuItems.objects.select_related("restaurant").get(
                id=menu_id,
                is_available=True
            )
        except MenuItems.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Menu not found"
            }, status=200)

        # ✅ Get Portions
        portions_qs = MenuItemPortion.objects.filter(menu_item=menu)
        portions = []
        for p in portions_qs:
            portions.append({
                "id": p.id,
                "portion_name": p.portion_name,
                "price": str(p.price)
            })

        # ✅ Get AddOns
        addons_qs = AddOn.objects.filter(menu_item=menu, is_available=True)
        addons = []
        for a in addons_qs:
            image_url = None
            if a.image:
                image_url = request.build_absolute_uri(a.image.url)

            addons.append({
                "id": a.id,
                "name": a.name,
                "price": str(a.price),
                "image": image_url,
                "is_available": a.is_available
            })

        # ✅ Distance Calculation (Optional)
        distance_km = None
        if user_id:
            try:
                user = UserRegister.objects.get(id=user_id)

                if (
                    user.latitude and user.longitude and
                    menu.restaurant.latitude and menu.restaurant.longitude
                ):
                    lat1 = float(user.latitude)
                    lon1 = float(user.longitude)
                    lat2 = float(menu.restaurant.latitude)
                    lon2 = float(menu.restaurant.longitude)

                    r = 6371
                    dlat = radians(lat2 - lat1)
                    dlon = radians(lon2 - lon1)

                    a_val = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a_val))
                    distance_km = round(r * c, 2)

            except UserRegister.DoesNotExist:
                pass

        # ✅ Final Response
        return JsonResponse({
            "status": True,
            "message": "Menu details fetched successfully",
            "data": {
                "id": menu.id,
                "name": menu.name,
                "price": str(menu.price),
                "menu_images": menu.menu_images,
                "VegNonVeg": menu.VegNonVeg,
                "description": menu.description,
                "discount": menu.discount,
                "restaurant": {
                    "id": menu.restaurant.id,
                    "restaurantname": menu.restaurant.restaurantname,
                    "restaurantimage": menu.restaurant.restaurantimage,
                    "latitude": str(menu.restaurant.latitude) if menu.restaurant.latitude else None,
                    "longitude": str(menu.restaurant.longitude) if menu.restaurant.longitude else None,
                },
                "portions": portions,
                "addons": addons,
                "distance_km": distance_km
            }
        }, status=200)
        
        
@method_decorator(csrf_exempt, name='dispatch')
class UpdateCartItemQuantityView(View):

    def post(self, request):
        menu_item_id = request.POST.get("menu_item_id")
        user_id = request.POST.get("user_id")
        quantity = request.POST.get("quantity")

        # ✅ Validate
        if not menu_item_id or not user_id or not quantity:
            return JsonResponse({
                "status": False,
                "message": "menu_item_id, user_id and quantity are required"
            })

        try:
            quantity = int(quantity)
        except ValueError:
            return JsonResponse({
                "status": False,
                "message": "Invalid quantity"
            })

        try:
            # ✅ Get user's cart
            cart = UserCart.objects.get(user__id=user_id)

            # ✅ Find cart item using menu_item_id
            cart_item = CartItems.objects.filter(
                cart=cart,
                menu_item_id=menu_item_id,
                order__isnull=True
            ).first()

            if not cart_item:
                return JsonResponse({
                    "status": False,
                    "message": "Cart item not found"
                })

            # ✅ If quantity = 0 → delete
            if quantity <= 0:
                cart_item.delete()
                return JsonResponse({
                    "status": True,
                    "message": "Item removed from cart",
                    "data": {
                        "menu_item_id": int(menu_item_id),
                        "quantity": 0
                    }
                })

            # ✅ Update quantity
            cart_item.quantity = quantity
            cart_item.save()

            # ✅ Total price
            total_price = cart_item.quantity * float(cart_item.price_at_order_time)

            return JsonResponse({
                "status": True,
                "message": "Quantity updated successfully",
                "data": {
                    "cart_item_id": cart_item.id,
                    "menu_item_id": int(menu_item_id),
                    "quantity": cart_item.quantity,
                    "total_price": round(total_price, 2)
                }
            })

        except UserCart.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Cart not found for this user"
            })
            
            
            
@method_decorator(csrf_exempt, name='dispatch')
class PlaceOrderView(View):
    @transaction.atomic
    def post(self, request):

        try:
            user_id = request.POST.get("user_id")
            cart_id = request.POST.get("cart_id")
            couponecode =request.POST.get("coupone_code","")
            delivery_address = request.POST.get("delivery_address")
            payment_mode = request.POST.get("payment_mode")
            restaurant_id =request.POST.get("restaurant_id")
            order_suggestion=request.POST.get("order_suggestion")
            paid_amount=request.POST.get("paid_amount")
            transaction_no = request.POST.get("transaction_no")  # optional
            
            
            
            # ===============================
            # VALIDATION
            # ===============================
            if not user_id or not cart_id or not delivery_address or not payment_mode:
                return JsonResponse({
                    "status": False,
                    "message": "user_id, cart_id, delivery_address and payment_mode are required"
                }, status=400)
                
            if not restaurant_id:
               return JsonResponse({
               "status": False,
               "message": "restaurant_id is required"
                }, status=400)

            if payment_mode not in ["razorpay", "google_pay", "phonepe", "cod"]:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid payment mode"
                }, status=400)

            # ===============================
            # GET USER & CART
            # ===============================
            try:
                user = UserRegister.objects.get(id=user_id)
                cart = UserCart.objects.get(id=cart_id, user=user)
            except:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid user or cart"
                }, status=404)

            # cart_items = CartItems.objects.filter(cart=cart, order__isnull=True)
            cart_items = CartItems.objects.filter(
             cart=cart,
             order__isnull=True,
              menu_item__restaurant_id=restaurant_id
              )

            if not cart_items.exists():
                return JsonResponse({
                    "status": False,
                    "message": "Cart is empty"
                }, status=400)

            # ===============================
            # CREATE ORDER
            # ===============================
            order = Orders.objects.create(
                user=user,
                status="pending",
                coupon_code=couponecode,
                # restaurant_id=restaurant_id,
                order_suggestion=order_suggestion,
                paid_amount=paid_amount,
                delivery_address=delivery_address
            )

            total_amount = Decimal("0.00")

            # ===============================
            # MOVE CART ITEMS TO ORDER
            # ===============================
            for item in cart_items:
                item_total_price = item.menu_item.price * item.quantity
                total_amount += item_total_price

                CartItems.objects.create(
                    order=order,
                    cart=None,
                    menu_item=item.menu_item,
                    restaurant=item.menu_item.restaurant,
                    quantity=item.quantity,
                    price_at_order_time=item.menu_item.price,
                    selectportion=item.selectportion,
                    addon=item.addon
                )

            # ===============================
            # CREATE PAYMENT ENTRY
            # ===============================

            payment_status = "pending"

            if payment_mode == "cod":
                payment_status = "pending"  # COD will be marked success after delivery
            else:
                # For online payments you can verify transaction_no here
                payment_status = "success" if transaction_no else "pending"

            Payment.objects.create(
                order=order,
                transaction_no=transaction_no,
                payment_status=payment_status,
                payment_mode=payment_mode
            )

            # ===============================
            # CLEAR CART
            # ===============================
            cart_items.delete()

            return JsonResponse({
                "status": True,
                "message": "Order placed successfully",
                "order_id": order.id,
                "order_uuid": str(order.order_uuid),
                "total_amount": str(total_amount),
                "order_status": order.status,
                "payment_mode": payment_mode,
                "payment_status": payment_status
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            
            
@method_decorator(csrf_exempt, name='dispatch')
class UserOrderDetailsAPI(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")
            print("user id is", user_id)

            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id is required"
                }, status=400)

            orders = Orders.objects.filter(user_id=user_id).order_by("-created_at")

            if not orders.exists():
                return JsonResponse({
                    "status": False,
                    "message": "No orders found"
                }, status=404)

            order_list = []

            for order in orders:

                payment = getattr(order, "payment", None)
                delivery_time = order.created_at + timedelta(minutes=40)

                restaurant_data = {}
                grand_total = 0

                for item in order.items.all():

                    restaurant_name = item.restaurant.restaurantname
                    restaurbt_id=item.restaurant.id

                    if restaurant_name not in restaurant_data:
                        restaurant_data[restaurant_name] = {
                            "menu_items": [],
                            "restaurant_total": 0
                        }

                    # Base item price
                    item_total = item.quantity * float(item.price_at_order_time)

                    # Calculate addon price
                    addon_total = sum(
                        addon.get("item_price", 0)
                        for addon in (item.addon or [])
                    )

                    # Add addon price to item total
                    item_total += addon_total

                    # Add to grand total
                    grand_total += item_total

                    restaurant_data[restaurant_name]["menu_items"].append({
                        "restaurant_images":item.restaurant.restaurantimage,
                        "restaurbt_id":restaurbt_id,
                        "name": item.menu_item.name,
                        "quantity": item.quantity,
                        "price": float(item.price_at_order_time),
                        "portion": item.selectportion,
                        "addon": item.addon,
                        "addon_total": addon_total,
                        "total": float(item_total),
                    })

                    restaurant_data[restaurant_name]["restaurant_total"] += float(item_total)

                order_list.append({
                    "order_number": str(order.order_uuid),
                    "delivery_partner":order.delivery_partner if order.delivery_partner else None,
                    "order_status": order.status,
                    "delivery_address": order.delivery_address,
                    "created_at": order.created_at,
                    "estimated_delivery_time": delivery_time,
                    "grand_total": float(grand_total),
                    "paid_amount": float(order.paid_amount) if order.paid_amount else 0,
                    "coupon_code": order.coupon_code,
                    "order_suggestion": order.order_suggestion,
                    "payment": {
                        "transaction_no": payment.transaction_no if payment else None,
                        "payment_status": payment.payment_status if payment else None,
                        "payment_mode": payment.payment_mode if payment else None,
                    },
                    
                    "restaurants": restaurant_data
                })

            return JsonResponse({
                "status": True,
                "orders": order_list
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=400)
            
            
@method_decorator(csrf_exempt, name='dispatch')
class UserDashboardAPI(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id is required"
                }, status=400)

            # Get user
            user = UserRegister.objects.get(id=user_id)

            # ✅ Total Orders
            total_orders = Orders.objects.filter(user=user).count()

            # ✅ Total Table Bookings
            total_bookings = TableBooking.objects.filter(user=user).count()

            # ✅ Cancelled Bookings
            cancelled_bookings = TableBooking.objects.filter(
                user=user,
                status="cancelled"
            ).count()

            # ✅ Profile Image URL
            profile_img = (
                request.build_absolute_uri(user.profile_image.url)
                if user.profile_image else None
            )

            return JsonResponse({
                "status": True,
                "data": {
                    "user_name": user.name,
                    "mobile_no": user.phone_no,
                    "profile_image": profile_img,

                    # "total_orders": total_orders,
                    # "total_bookings": total_bookings,
                    # "cancelled_bookings": cancelled_bookings
                }
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            }, status=404)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class HelpSupportAPI(View):

    def get(self, request):
        try:
            support = HelpSupport.objects.last()

            if not support:
                return JsonResponse({
                    "status": False,
                    "message": "No Help & Support data found"
                }, status=404)

            return JsonResponse({
                "status": True,
                "data": {
                    "title": support.title,
                    "description": support.description,
                    "contact_email": support.contact_email,
                    "contact_phone": support.contact_phone,
                    "address": support.address,
                    "working_hours": support.working_hours,
                    "updated_at": support.updated_at
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)



@method_decorator(csrf_exempt, name='dispatch')
class ToggleWishlistView(View):

    def post(self, request):
        user_id = request.POST.get("user_id")
        menu_item_id = request.POST.get("menu_item_id")

        # ✅ Validate
        if not user_id or not menu_item_id:
            return JsonResponse({
                "status": False,
                "message": "user_id and menu_item_id are required"
            })

        try:
            user = UserRegister.objects.get(id=user_id)
            menu_item = MenuItems.objects.get(id=menu_item_id)

            # ✅ Check if already exists
            wishlist_item = Wishlist.objects.filter(
                user=user,
                menu_item=menu_item
            ).first()

            # ❌ If exists → REMOVE
            if wishlist_item:
                wishlist_item.delete()
                return JsonResponse({
                    "status": True,
                    "message": "Removed from wishlist",
                    "is_wishlisted": False
                })

            # ✅ Else → ADD
            Wishlist.objects.create(
                user=user,
                menu_item=menu_item
            )

            return JsonResponse({
                "status": True,
                "message": "Added to wishlist",
                "is_wishlisted": True
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except MenuItems.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Menu item not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
            
@method_decorator(csrf_exempt, name='dispatch')
class SimpleCartMenuListView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id required"
                }, status=400)

            # ✅ Get user
            try:
                user = UserRegister.objects.get(id=user_id)
            except UserRegister.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "User not found"
                }, status=404)

            # ✅ Get cart
            try:
                cart = user.cart
            except UserCart.DoesNotExist:
                return JsonResponse({
                    "status": True,
                    "menu_items": [],
                    "total_amount": "0.00",
                    "total_items": 0
                })

            # ✅ Get cart items
            cart_items = CartItems.objects.select_related("menu_item").filter(
                cart=cart,
                order__isnull=True
            )

            if not cart_items.exists():
                return JsonResponse({
                    "status": True,
                    "menu_items": [],
                    "total_amount": "0.00",
                    "total_items": 0
                })

            menu_list = []
            grand_total = Decimal("0.00")
            total_items = 0

            for item in cart_items:
                item_total = item.price_at_order_time * item.quantity
                grand_total += item_total
                total_items += item.quantity

                menu_list.append({
                    "cart_item_id": item.id,
                    "menu_item_id": item.menu_item.id,
                    "menu_item_name": item.menu_item.name,
                    "quantity": item.quantity,
                    "price_per_item": str(item.price_at_order_time),
                    "item_total": str(item_total),
                    "menu_image": (
                        item.menu_item.menu_images[0]
                        if item.menu_item.menu_images
                        else None
                    )
                })

            return JsonResponse({
                "status": True,
                "cart_id": cart.id,
                "total_items": total_items,
                "total_amount": str(grand_total),
                "menu_items": menu_list
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            
            
@method_decorator(csrf_exempt, name='dispatch')
class AddUpdateDeliveryPartnerRating(View):

    def post(self, request):
        user_id = request.POST.get("user_id")
        partner_id = request.POST.get("delivery_partner_id")
        rating = request.POST.get("rating")

        # ✅ Validation
        if not user_id or not partner_id or not rating:
            return JsonResponse({
                "status": False,
                "message": "user_id, delivery_partner_id and rating are required"
            }, status=400)

        try:
            rating = float(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except:
            return JsonResponse({
                "status": False,
                "message": "rating must be between 1.0 to 5.0"
            }, status=400)

        try:
            user = UserRegister.objects.get(id=user_id)
            partner = DeliveryPartnerForm.objects.get(id=partner_id)
        except:
            return JsonResponse({
                "status": False,
                "message": "Invalid user or delivery partner"
            }, status=404)

        # 🚀 Update or Create
        obj, created = DeliveryPartnerRating.objects.update_or_create(
            user=user,
            delivery_partner=partner,
            defaults={
                "user_rating_out_of_5": rating
            }
        )

        return JsonResponse({
            "status": True,
            "message": "Rating added" if created else "Rating updated",
            "data": {
                "id": obj.id,
                "rating": float(obj.user_rating_out_of_5)
            }
        })
        
@method_decorator(csrf_exempt, name='dispatch')
class AddUpdateRestaurantRating(View):

    def post(self, request):
        user_id = request.POST.get("user_id")
        restaurant_id = request.POST.get("restaurant_id")
        rating = request.POST.get("rating")
        description = request.POST.get("description", "")

        # ✅ Validation
        if not user_id or not restaurant_id or not rating:
            return JsonResponse({
                "status": False,
                "message": "user_id, restaurant_id and rating are required"
            }, status=400)

        # ✅ Rating validation
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            return JsonResponse({
                "status": False,
                "message": "rating must be between 1 to 5"
            }, status=400)

        # ✅ Fetch objects safely
        try:
            user = UserRegister.objects.get(id=user_id)
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            }, status=404)
        except Restaurant.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Restaurant not found"
            }, status=404)

        # 🚀 Update or Create (FIXED FIELD)
        obj, created = RestaurantRating.objects.update_or_create(
            user=user,
            restaurant=restaurant,   # ✅ FIXED
            defaults={
                "rating": rating,
                "description": description
            }
        )

        return JsonResponse({
            "status": True,
            "message": "Rating added" if created else "Rating updated",
            "data": {
                "id": obj.id,
                "rating": obj.rating,
                "description": obj.description
            }
        })
        
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryPartnerFormAPI(View):

    def post(self, request):
        try:
            # Personal Details
            full_name = request.POST.get("full_name")
            email = request.POST.get("email")
            phone_number = request.POST.get("phone_number")
            city = request.POST.get("city")
            referral_code = request.POST.get("referral_code")
            password = request.POST.get("password")

            if not password:
                return JsonResponse({
                    "status": False,
                    "message": "Password is required"
                })

            # Vehicle
            vehicle_number = request.POST.get("vehicle_number")
            vehicle_type = request.POST.get("vehicle_type")
            vehicle_model = request.POST.get("vehicle_model")
            vehicle_color = request.POST.get("vehicle_color")
            manufacturing_year = request.POST.get("manufacturing_year")

            # Bank
            account_holder_name = request.POST.get("account_holder_name")
            account_number = request.POST.get("account_number")
            bank_name = request.POST.get("bank_name")
            branch_name = request.POST.get("branch_name")
            ifsc_code = request.POST.get("ifsc_code")

            fs = FileSystemStorage()

            def save_multiple_images(files):
                urls = []
                for file in files:
                    filename = fs.save(f"delivery_docs/{file.name}", file)
                    file_url = fs.url(filename)
                    urls.append(file_url)
                return urls

            # Upload Files
            profile_images = save_multiple_images(request.FILES.getlist("profile_image"))
            aadhar_cards = save_multiple_images(request.FILES.getlist("aadhar_card"))
            driving_licenses = save_multiple_images(request.FILES.getlist("driving_license"))
            vehicle_rcs = save_multiple_images(request.FILES.getlist("vehicle_rc_certificate"))
            vehicle_images = save_multiple_images(request.FILES.getlist("vehicle_image"))
            
            print('profile_images',profile_images)
            print('aadhar_cards',aadhar_cards)
            print('driving_licenses',driving_licenses)
            print('vehicle_rcs',vehicle_rcs)
            print('vehicle_images',vehicle_images)

            # Save Partner
            delivery_partner = DeliveryPartnerForm.objects.create(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                city=city,
                referral_code=referral_code,
                password=make_password(password),

                vehicle_number=vehicle_number,
                vehicle_type=vehicle_type,
                vehicle_model=vehicle_model,
                vehicle_color=vehicle_color,
                manufacturing_year=manufacturing_year,

                account_holder_name=account_holder_name,
                account_number=account_number,
                bank_name=bank_name,
                branch_name=branch_name,
                ifsc_code=ifsc_code,

                # Save JSON image lists
                profile_image=profile_images,
                aadhar_card=aadhar_cards,
                driving_license=driving_licenses,
                vehicle_rc_certificate=vehicle_rcs,
                vehicle_image=vehicle_images,
            )
            delivery_partner.deliver_partnerid = "DEMPCODE/" + str(delivery_partner.id)
            delivery_partner.save()
            

            return JsonResponse({
                "status": True,
                "message": "Delivery Partner Form Submitted Successfully",
                "partner_id": delivery_partner.id
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)


        
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryPartnerLoginAPI(View):

    def post(self, request):
        try:
            email = request.POST.get("email")
            password = request.POST.get("password")

            if not email or not password:
                return JsonResponse({
                    "status": False,
                    "message": "Email and Password are required"
                }, status=400)

            try:
                partner = DeliveryPartnerForm.objects.filter(email=email).first()
            except DeliveryPartnerForm.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid email"
                }, status=404)

            # Check password
            if not check_password(password, partner.password):
                return JsonResponse({
                    "status": False,
                    "message": "Invalid password"
                }, status=401)
                
            if partner.approval_status=="pending":
                return JsonResponse({
                    "ststus":True,
                    "message":"You are not authorized by the admin"
                })
                

            return JsonResponse({
                "status": True,
                "message": "Login successful",
                "data": {
                    "partner_id": partner.id,
                    "full_name": partner.full_name,
                    "email": partner.email,
                    "phone_number": partner.phone_number,
                    "approval_status": partner.approval_status,
                    "deliveryPatnerCode":partner.deliver_partnerid,
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UpdateDeliveryPartnerAddressAPI(View):

    def post(self, request):
        try:
            partner_id = request.POST.get("partner_id")
            address = request.POST.get("address")
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")
            work_ststus=request.POST.get("work_status")
            
            if not work_ststus:
                return JsonResponse({
                    "status": False,
                    "message": "Work status is required"
                }, status=400)
                

            if not partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "partner_id is required"
                }, status=400)

            partner = DeliveryPartnerForm.objects.filter(id=partner_id).first()

            if not partner:
                return JsonResponse({
                    "status": False,
                    "message": "Delivery partner not found"
                }, status=404)

            # Update fields
            if address:
                partner.address = address

            if latitude:
                partner.latitude = latitude

            if longitude:
                partner.longitude = longitude
                
            if work_ststus:
                partner.work_status=work_ststus

            partner.save()

            return JsonResponse({
                "status": True,
                "message": "Address updated successfully",
                "data": {
                    "partner_id": partner.id,
                    "address": partner.address,
                    "latitude": partner.latitude,
                    "longitude": partner.longitude,
                    "work_status":partner.work_status,
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            

@method_decorator(csrf_exempt, name='dispatch')
class NearbyOrdersForDeliveryPartnerAPI(View):

    def post(self, request):
        try:
            partner_id = request.POST.get("partner_id")

            partner = DeliveryPartnerForm.objects.filter(id=partner_id).first()
 
            if not partner:
                return JsonResponse({"status": False, "message": "Partner not found"})

            if partner.work_status != "online":
                return JsonResponse({"status": False, "message": "Partner offline"})

            if not partner.latitude or not partner.longitude:
                return JsonResponse({"status": False, "message": "Location not available"})

            partner_lat = float(partner.latitude)
            partner_lon = float(partner.longitude)

            # Get orders with related data
            orders = Orders.objects.filter(status="ready") \
                .select_related("user") \
                .prefetch_related("items__menu_item", "items__restaurant")

            nearby_orders = []

            for order in orders:

                # Skip if already accepted
                if DeliveryPartnerOrderAction.objects.filter(
                        order=order,
                        action="accepted"
                ).exists():
                    continue

                cart_items = order.items.all()

                if not cart_items:
                    continue

                restaurant = cart_items[0].restaurant

                if not restaurant.latitude or not restaurant.longitude:
                    continue

                distance = calculate_distance(
                    partner_lat,
                    partner_lon,
                    float(restaurant.latitude),
                    float(restaurant.longitude)
                )

                if distance > 20:
                    continue

                payment = getattr(order, "payment", None)

                items = []
                total_items = 0

                for item in cart_items:
                    total_items += item.quantity
                    items.append({
                        "item_name": item.menu_item.name,
                        "quantity": item.quantity,
                        "price": item.price_at_order_time
                    })

                nearby_orders.append({
                    "order_id": order.id,
                    "order_uuid": str(order.order_uuid),
                    "order_status":order.status,

                    "restaurant_name": restaurant.restaurantname,
                    "restaurant_mobile": restaurant.phone,
                    "pickup_address": restaurant.adderess,

                    "distance_km": round(distance, 2),
                    "estimated_time": int(distance * 3),

                    "customer_details": {
                        "name": order.user.name,
                        "email": order.user.email,
                        "customer_mo":order.user.phone_no,
                        "deliveryAddress":order.delivery_address,
                    },

                    "payment_status": payment.payment_status if payment else "pending",

                    "items": items,

                    "payment_summary": {
                        "total_items": total_items,
                        "total_amount": order.paid_amount,
                        "coupon_code": order.coupon_code,
                        "payment_mode":order.payment.payment_mode if hasattr(order, "payment") else None,
                    }
                })

            return JsonResponse({
                "status": True,
                "total_orders": len(nearby_orders),
                "orders": nearby_orders
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })

            
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryPartnerOrderActionAPI(View):

    def post(self, request):
        try:
            order_id = request.POST.get("order_id")
            partner_id = request.POST.get("partner_id")
            action = request.POST.get("action")  # accepted / rejected

            if not order_id or not partner_id or not action:
                return JsonResponse({
                    "status": False,
                    "message": "order_id, partner_id and action are required"
                })

            if action not in ["accepted", "rejected"]:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid action"
                })

            order = Orders.objects.filter(id=order_id).first()
            partner = DeliveryPartnerForm.objects.filter(id=partner_id).first()

            if not order:
                return JsonResponse({
                    "status": False,
                    "message": "Order not found"
                })

            if not partner:
                return JsonResponse({
                    "status": False,
                    "message": "Delivery partner not found"
                })

            # Check if order already accepted by another partner
            already_accepted = DeliveryPartnerOrderAction.objects.filter(
                order=order,
                action="accepted"
            ).exclude(delivery_partner=partner).exists()

            if already_accepted:
                return JsonResponse({
                    "status": False,
                    "message": "Order already accepted by another partner"
                })

            # Save action
            DeliveryPartnerOrderAction.objects.create(
                order=order,
                delivery_partner=partner,
                action=action
            )

            # Update order status only if accepted
            if action == "accepted":
                order.delivery_partner = partner
                order.save()

            return JsonResponse({
                "status": True,
                "message": f"Order {action} successfully",
                "order_id": order.id,
                "action": action
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })


def generate_otp():
    return str(random.randint(1000, 9999))


@method_decorator(csrf_exempt, name='dispatch')
class SendOrderOTPAPI(View):
    def post(self, request):
        try:
            partner_id = request.POST.get("delivery_partner_id")
            order_id = request.POST.get("order_id")

            if not partner_id or not order_id:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id and order_id are required"
                })

            partner = DeliveryPartnerForm.objects.filter(id=partner_id).first()
            order = Orders.objects.filter(id=order_id).first()

            if not partner:
                return JsonResponse({
                    "status": False,
                    "message": "Delivery partner not found"
                })

            if not order:
                return JsonResponse({
                    "status": False,
                    "message": "Order not found"
                })

            # Check if this partner is assigned to the order
            if order.delivery_partner != partner:
                return JsonResponse({
                    "status": False,
                    "message": "This order is not assigned to this delivery partner"
                })

            # Generate OTP
            otp = generate_otp()

            # Update OTP in order
            order.order_otp = otp
            order.save()
            
            # Create Notification
            Notifications.objects.create(
                user=order.user,
                order=order,
                title="Delivery OTP Generated",
                message=f"Your delivery OTP for order {order.order_uuid} placed on {order.created_at.strftime('%d-%m-%Y')} is {otp}."
            )

            # Here you can integrate SMS service
            # send_sms(order.user.phone, f"Your delivery OTP is {otp}")

            return JsonResponse({
                "status": True,
                "message": "OTP generated successfully",
                "order_id": order.id,
                "otp": otp  # remove in production if sending via SMS
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })

        
# @method_decorator(csrf_exempt, name='dispatch')
# class ConfirmOrderDeliveredAPI(View):

#     def post(self, request):
#         try:
#             partner_id = request.POST.get("delivery_partner_id")
#             order_id = request.POST.get("order_id")
#             otp = request.POST.get("otp")

#             if not partner_id or not order_id or not otp:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "delivery_partner_id, order_id and otp are required"
#                 })

#             partner = DeliveryPartnerForm.objects.filter(id=partner_id).first()
#             order = Orders.objects.filter(id=order_id).first()

#             if not partner:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Delivery partner not found"
#                 })

#             if not order:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Order not found"
#                 })

#             # Check partner assignment
#             if order.delivery_partner != partner:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "This order is not assigned to this delivery partner"
#                 })

#             # Check OTP
#             if str(order.order_otp) != str(otp):
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Invalid OTP"
#                 })

#             # Update order status
#             order.status = "delivered"
#             order.delivered_time = timezone.now()
#             order.save()

#             return JsonResponse({
#                 "status": True,
#                 "message": "Order delivered successfully",
#                 "order_id": order.id
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             })
            
@method_decorator(csrf_exempt, name='dispatch')
class ConfirmOrderDeliveredAPI(View):

    def post(self, request):
        try:
            partner_id = request.POST.get("delivery_partner_id")
            order_id = request.POST.get("order_id")
            otp = request.POST.get("otp")

            if not partner_id or not order_id or not otp:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id, order_id and otp are required"
                })

            partner = DeliveryPartnerForm.objects.filter(id=partner_id).first()
            order = Orders.objects.filter(id=order_id).first()

            if not partner:
                return JsonResponse({
                    "status": False,
                    "message": "Delivery partner not found"
                })

            if not order:
                return JsonResponse({
                    "status": False,
                    "message": "Order not found"
                })

            # Check assignment
            if order.delivery_partner != partner:
                return JsonResponse({
                    "status": False,
                    "message": "This order is not assigned to this delivery partner"
                })

            # Check OTP
            if str(order.order_otp) != str(otp):
                return JsonResponse({
                    "status": False,
                    "message": "Invalid OTP"
                })

            # Update order
            order.status = "delivered"
            order.delivered_time = timezone.now()
            order.save()

            # -----------------------------
            # Calculate today's order count
            # -----------------------------

            today = timezone.now().date()

            today_order_count = Orders.objects.filter(
                delivery_partner=partner,
                status="delivered",
                delivered_time__date=today
            ).count()

            # -----------------------------
            # Calculate incentive
            # -----------------------------

            incentive_rules = SetOrderIncentive.objects.order_by("more_than_order")

            incentive_amount = 0

            for rule in incentive_rules:
                if today_order_count > rule.more_than_order:
                    incentive_amount = rule.incentive_amount

            # -----------------------------
            # Save order completion record
            # -----------------------------

            OrderCompletion.objects.create(
                order=order,
                delivery_partner=partner,
                today_order_count=today_order_count,
                incentive_amount=incentive_amount
            )

            return JsonResponse({
                "status": True,
                "message": "Order delivered successfully",
                "order_id": order.id,
                "today_orders": today_order_count,
                "incentive": float(incentive_amount)
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })            
            
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryPartnerRatingAPI(View):

    def post(self, request):
        try:
            delivery_partner_id = request.POST.get("delivery_partner_id")
            user_id = request.POST.get("user_id")
            rating = request.POST.get("rating")

            if not delivery_partner_id or not user_id or not rating:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id, user_id and rating are required"
                })

            if float(rating) > 5 or float(rating) < 0:
                return JsonResponse({
                    "status": False,
                    "message": "Rating must be between 0 and 5"
                })

            delivery_partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)
            user = UserRegister.objects.get(id=user_id)

            rating_obj = DeliveryPartnerRating.objects.create(
                delivery_partner=delivery_partner,
                user=user,
                user_rating_out_of_5=rating
            )

            return JsonResponse({
                "status": True,
                "message": "Rating submitted successfully",
                "data": {
                    "rating_id": rating_obj.id,
                    "delivery_partner_id": delivery_partner.id,
                    "user_id": user.id,
                    "rating": str(rating_obj.user_rating_out_of_5),
                    "created_at": rating_obj.created_at
                }
            })

        except DeliveryPartnerForm.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Delivery partner not found"
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
# @method_decorator(csrf_exempt, name='dispatch')            
# class DeliveryPartnerDashboardAPI(View):

#     def post(self, request):
#         try:

#             delivery_partner_id = request.POST.get("delivery_partner_id")

#             if not delivery_partner_id:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "delivery_partner_id is required"
#                 })

#             partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

#             today = date.today()

#             # Today's completed orders
#             today_orders = Orders.objects.filter(
#                 delivery_partner=partner,
#                 delivered_time__date=today
#             )

#             today_completed_orders_count = today_orders.count()

#             # Total completed orders
#             total_orders = Orders.objects.filter(
#                 delivery_partner=partner,
#                 delivered_time__isnull=False
#             ).count()

#             # Average rating
#             avg_rating = DeliveryPartnerRating.objects.filter(
#                 delivery_partner=partner
#             ).aggregate(avg=Avg("user_rating_out_of_5"))["avg"]

#             if not avg_rating:
#                 avg_rating = 0

#             # Incentive Calculation
#             incentive_rules = SetOrderIncentive.objects.order_by("more_than_order")

#             today_incentive = 0

#             for rule in incentive_rules:
#                 if today_completed_orders_count > rule.more_than_order:
#                     today_incentive = rule.incentive_amount

#             # Average Delivery Time
#             total_minutes = 0
#             count = 0

#             delivered_orders = Orders.objects.filter(
#                 delivery_partner=partner,
#                 delivered_time__isnull=False
#             )

#             for order in delivered_orders:
#                 if order.delivered_time and order.created_at:
#                     diff = order.delivered_time - order.created_at
#                     minutes = diff.total_seconds() / 60
#                     total_minutes += minutes
#                     count += 1

#             avg_delivery_time = 0
#             if count > 0:
#                 avg_delivery_time = round(total_minutes / count, 2)

#             return JsonResponse({
#                 "status": True,
#                 "data": {
#                     "today_completed_orders": today_completed_orders_count,
#                     "today_incentive": float(today_incentive),
#                     "average_rating": round(float(avg_rating), 2),
#                     "total_completed_orders": total_orders,
#                     "average_delivery_time_minutes": avg_delivery_time
#                 }
#             })

#         except DeliveryPartnerForm.DoesNotExist:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Delivery partner not found"
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             })

@method_decorator(csrf_exempt, name='dispatch')
class DeliveryPartnerDashboardAPI(View):

    def post(self, request):
        try:
            delivery_partner_id = request.POST.get("delivery_partner_id")

            if not delivery_partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id is required"
                })

            partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

            today = date.today()

            # ----------------------------
            # Today's completed orders
            # ----------------------------
            today_completions = OrderCompletion.objects.filter(
                delivery_partner=partner,
                created_at__date=today
            )

            today_completed_orders_count = today_completions.count()

            # ----------------------------
            # Today's incentive
            # ----------------------------
            today_incentive = today_completions.aggregate(
                total=Avg("incentive_amount")
            )["total"]

            if not today_incentive:
                today_incentive = 0

            # ----------------------------
            # Total completed orders
            # ----------------------------
            total_orders = OrderCompletion.objects.filter(
                delivery_partner=partner
            ).count()

            # ----------------------------
            # Average rating
            # ----------------------------
            avg_rating = DeliveryPartnerRating.objects.filter(
                delivery_partner=partner
            ).aggregate(avg=Avg("user_rating_out_of_5"))["avg"]

            if not avg_rating:
                avg_rating = 0

            # ----------------------------
            # Average delivery time
            # ----------------------------
            delivered_orders = Orders.objects.filter(
                delivery_partner=partner,
                delivered_time__isnull=False
            )

            total_minutes = 0
            count = 0

            for order in delivered_orders:
                if order.delivered_time and order.created_at:
                    diff = order.delivered_time - order.created_at
                    minutes = diff.total_seconds() / 60
                    total_minutes += minutes
                    count += 1

            avg_delivery_time = 0
            if count > 0:
                avg_delivery_time = round(total_minutes / count, 2)

            return JsonResponse({
                "status": True,
                "data": {
                    "today_completed_orders": today_completed_orders_count,
                    "today_incentive": float(today_incentive),
                    "average_rating": round(float(avg_rating), 2),
                    "total_completed_orders": total_orders,
                    "average_delivery_time_minutes": avg_delivery_time
                }
            })

        except DeliveryPartnerForm.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Delivery partner not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })


# @method_decorator(csrf_exempt, name='dispatch')
# class DeliveryPartnerWeeklyStatsAPI(View):

#     def post(self, request):
#         try:
#             delivery_partner_id = request.POST.get("delivery_partner_id")

#             if not delivery_partner_id:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "delivery_partner_id is required"
#                 })

#             partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

#             today = timezone.now().date()
#             last_7_days = today - timedelta(days=6)

#             incentive_rules = SetOrderIncentive.objects.order_by("more_than_order")

#             weekly_deliveries = 0
#             weekly_incentive = 0

#             daily_data = []

#             for i in range(7):

#                 day = last_7_days + timedelta(days=i)

#                 day_orders = Orders.objects.filter(
#                     delivery_partner=partner,
#                     delivered_time__date=day
#                 )

#                 deliveries = day_orders.count()

#                 weekly_deliveries += deliveries

#                 # calculate incentive for that day
#                 day_incentive = 0
#                 for rule in incentive_rules:
#                     if deliveries > rule.more_than_order:
#                         day_incentive = rule.incentive_amount

#                 weekly_incentive += day_incentive

#                 daily_data.append({
#                     "date": str(day),
#                     "deliveries": deliveries,
#                     "earned": float(day_incentive),
#                     "completionPercent":"90",
#                     "onTimePercent":"90"
#                 })

#             # Average Rating
#             avg_rating = DeliveryPartnerRating.objects.filter(
#                 delivery_partner=partner
#             ).aggregate(avg=Avg("user_rating_out_of_5"))["avg"]

#             if not avg_rating:
#                 avg_rating = 0

#             return JsonResponse({
#                 "status": True,
#                 "data": {
#                     "week_earned": float(weekly_incentive),
#                     "deliveries": weekly_deliveries,
#                     "rating": round(float(avg_rating), 2),
#                     "last_7_days": daily_data
#                 }
#             })

#         except DeliveryPartnerForm.DoesNotExist:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Delivery partner not found"
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             })
# @method_decorator(csrf_exempt, name='dispatch')
# class DeliveryPartnerWeeklyStatsAPI(View):

#     def post(self, request):
#         try:
#             delivery_partner_id = request.POST.get("delivery_partner_id")

#             if not delivery_partner_id:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "delivery_partner_id is required"
#                 })

#             partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

#             today = timezone.now().date()
#             last_7_days = today - timedelta(days=6)

#             incentive_rules = SetOrderIncentive.objects.order_by("more_than_order")

#             weekly_deliveries = 0
#             weekly_incentive = 0

#             daily_data = []

#             for i in range(7):

#                 day = last_7_days + timedelta(days=i)

#                 day_orders = Orders.objects.filter(
#                     delivery_partner=partner,
#                     delivered_time__date=day
#                 )

#                 deliveries = day_orders.count()
#                 weekly_deliveries += deliveries

#                 # calculate incentive for that day
#                 day_incentive = 0
#                 for rule in incentive_rules:
#                     if deliveries > rule.more_than_order:
#                         day_incentive = rule.incentive_amount

#                 weekly_incentive += day_incentive

#                 # -------------------------------
#                 # Completion Percent
#                 # -------------------------------

#                 target = partner.daily_order_target or 0

#                 if target > 0:
#                     completion_percent = round((deliveries / target) * 100, 2)
#                 else:
#                     completion_percent = 0

#                 # -------------------------------
#                 # On-Time Delivery Percent
#                 # -------------------------------

#                 on_time_deliveries = 0

#                 for order in day_orders:
#                     if order.delivered_time and order.created_at:
#                         delivery_time = order.delivered_time - order.created_at

#                         if delivery_time <= timedelta(minutes=45):
#                             on_time_deliveries += 1

#                 if deliveries > 0:
#                     on_time_percent = round((on_time_deliveries / deliveries) * 100, 2)
#                 else:
#                     on_time_percent = 0

#                 daily_data.append({
#                     "date": str(day),
#                     "deliveries": deliveries,
#                     "earned": float(day_incentive),
#                     "completionPercent": completion_percent,
#                     "onTimePercent": on_time_percent
#                 })

#             # -------------------------------
#             # Average Rating
#             # -------------------------------

#             avg_rating = DeliveryPartnerRating.objects.filter(
#                 delivery_partner=partner
#             ).aggregate(avg=Avg("user_rating_out_of_5"))["avg"]

#             if not avg_rating:
#                 avg_rating = 0

#             return JsonResponse({
#                 "status": True,
#                 "data": {
#                     "week_earned": float(weekly_incentive),
#                     "deliveries": weekly_deliveries,
#                     "rating": round(float(avg_rating), 2),
#                     "last_7_days": daily_data
#                 }
#             })

#         except DeliveryPartnerForm.DoesNotExist:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Delivery partner not found"
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             })

@method_decorator(csrf_exempt, name='dispatch')
class DeliveryPartnerWeeklyStatsAPI(View):

    def post(self, request):
        try:
            delivery_partner_id = request.POST.get("delivery_partner_id")

            if not delivery_partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id is required"
                })

            partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

            today = timezone.now().date()
            last_7_days = today - timedelta(days=6)

            weekly_deliveries = 0
            weekly_incentive = 0

            daily_data = []

            for i in range(7):

                day = last_7_days + timedelta(days=i)

                # -----------------------------
                # Get completions from OrderCompletion
                # -----------------------------
                day_completions = OrderCompletion.objects.filter(
                    delivery_partner=partner,
                    created_at__date=day
                )

                deliveries = day_completions.count()
                weekly_deliveries += deliveries

                # incentive earned that day
                day_incentive = day_completions.aggregate(
                    total=Sum("incentive_amount")
                )["total"] or 0

                weekly_incentive += day_incentive

                # -----------------------------
                # Completion Percent
                # -----------------------------
                target = partner.daily_order_target or 0

                if target > 0:
                    completion_percent = round((deliveries / target) * 100, 2)
                else:
                    completion_percent = 0

                # -----------------------------
                # On-Time Delivery Percent
                # -----------------------------
                day_orders = Orders.objects.filter(
                    delivery_partner=partner,
                    delivered_time__date=day
                )

                on_time_deliveries = 0

                for order in day_orders:
                    if order.delivered_time and order.created_at:
                        delivery_time = order.delivered_time - order.created_at

                        if delivery_time <= timedelta(minutes=45):
                            on_time_deliveries += 1

                if deliveries > 0:
                    on_time_percent = round((on_time_deliveries / deliveries) * 100, 2)
                else:
                    on_time_percent = 0

                daily_data.append({
                    "date": str(day),
                    "deliveries": deliveries,
                    "earned": float(day_incentive),
                    "completionPercent": completion_percent,
                    "onTimePercent": on_time_percent
                })

            # -----------------------------
            # Average Rating
            # -----------------------------
            avg_rating = DeliveryPartnerRating.objects.filter(
                delivery_partner=partner
            ).aggregate(avg=Avg("user_rating_out_of_5"))["avg"]

            if not avg_rating:
                avg_rating = 0

            return JsonResponse({
                "status": True,
                "data": {
                    "week_earned": float(weekly_incentive),
                    "deliveries": weekly_deliveries,
                    "rating": round(float(avg_rating), 2),
                    "last_7_days": daily_data[::-1]
                }
            })
        except DeliveryPartnerForm.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Delivery partner not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })

            
# @method_decorator(csrf_exempt, name='dispatch')            
# class DeliveryHistoryAPI(View):

#     def post(self, request):
#         try:
#             delivery_partner_id = request.POST.get("delivery_partner_id")
#             filter_type = request.POST.get("filter", "all")  

#             if not delivery_partner_id:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "delivery_partner_id is required"
#                 })

#             partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

#             today = timezone.now().date()

#             orders = Orders.objects.filter(
#                 delivery_partner=partner,
#                 status="delivered"
#             )

#             if filter_type == "today":
#                 orders = orders.filter(delivered_time__date=today)

#             elif filter_type == "week":
#                 week_start = today - timedelta(days=7)
#                 orders = orders.filter(delivered_time__date__gte=week_start)

#             elif filter_type == "month":
#                 orders = orders.filter(
#                     delivered_time__month=today.month,
#                     delivered_time__year=today.year
#                 )

#             total_deliveries = orders.count()

#             total_earnings = orders.aggregate(
#                 total=Sum("paid_amount")
#             )["total"] or 0

#             avg_rating = DeliveryPartnerRating.objects.filter(
#                 delivery_partner=partner
#             ).aggregate(avg=Avg("user_rating_out_of_5"))["avg"] or 0

#             delivery_list = []

#             for order in orders:

#                 restaurant = getattr(order, "restaurant", None)

#                 restaurant_name = restaurant.restaurantname if restaurant else "N/A"

#                 customer = order.user.name if order.user else "N/A"

#                 delivery_distance = 0

#                 if restaurant and restaurant.latitude and restaurant.longitude and order.user.latitude and order.user.longitude:
#                    try:
#                     delivery_distance = calculate_distance(
#                          restaurant.latitude,
#                          restaurant.longitude,
#                          order.user.latitude,
#                          order.user.longitude
#                          )
#                    except Exception:
#                      delivery_distance = 0

#                 delivery_list.append({
#                     "order_id": order.id,
#                     "restaurant_name": restaurant_name,
#                     "customer_name": customer,
#                     "delivery_address": order.delivery_address,
#                     "delivery_distance_km": delivery_distance,
#                     "delivered_time": order.delivered_time,
#                     "order_status": order.status
#                 })

#             return JsonResponse({
#                 "status": True,
#                 "data": {
#                     "summary": {
#                         "total_deliveries": total_deliveries,
#                         "total_earnings": float(total_earnings),
#                         "avg_rating": round(float(avg_rating), 2)
#                     },
#                     "delivery_details": delivery_list
#                 }
#             })

#         except DeliveryPartnerForm.DoesNotExist:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Delivery partner not found"
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             })
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryHistoryAPI(View):

    def post(self, request):
        try:
            delivery_partner_id = request.POST.get("delivery_partner_id")
            filter_type = request.POST.get("filter", "all")

            if not delivery_partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id is required"
                })

            partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

            today = timezone.now().date()

            completions = OrderCompletion.objects.filter(
               delivery_partner=partner
               ).select_related(
               "order",
                "order__user",
                "order__delivery_partner"
                )

            # -------------------------
            # Apply Filters
            # -------------------------
            if filter_type == "today":
                completions = completions.filter(created_at__date=today)

            elif filter_type == "week":
                week_start = today - timedelta(days=7)
                completions = completions.filter(created_at__date__gte=week_start)

            elif filter_type == "month":
                completions = completions.filter(
                    created_at__month=today.month,
                    created_at__year=today.year
                )

            total_deliveries = completions.count()

            total_earnings = completions.aggregate(
                total=Sum("order__paid_amount")
            )["total"] or 0

            avg_rating = DeliveryPartnerRating.objects.filter(
                delivery_partner=partner
            ).aggregate(avg=Avg("user_rating_out_of_5"))["avg"] or 0

            delivery_list = []

            for completion in completions:

                order = completion.order
                cart_item = order.items.select_related("restaurant").first()

                restaurant_name = cart_item.restaurant.restaurantname if cart_item else "N/A"
                

                customer = order.user.name if order.user else "N/A"

                delivery_distance = 0

                if cart_item.restaurant and cart_item.restaurant.latitude and cart_item.restaurant.longitude and order.user.latitude and order.user.longitude:
                    try:
                        delivery_distance = calculate_distance(
                            cart_item.restaurant.latitude,
                            cart_item.restaurant.longitude,
                            order.user.latitude,
                            order.user.longitude
                        )
                    except Exception:
                        delivery_distance = 0

                delivery_list.append({
                    "order_id": order.id,
                    "uid":order.order_uuid,
                    "restaurant_name": restaurant_name,
                    "customer_name": customer,
                    "delivery_address": order.delivery_address,
                    "delivery_distance_km": delivery_distance,
                    "delivered_time": order.delivered_time,
                    "order_status": order.status,
                    "incentive_earned": float(completion.incentive_amount)
                })

            return JsonResponse({
                "status": True,
                "data": {
                    "summary": {
                        "total_deliveries": total_deliveries,
                        "total_earnings": float(total_earnings),
                        "avg_rating": round(float(avg_rating), 2)
                    },
                    "delivery_details": delivery_list
                }
            })

        except DeliveryPartnerForm.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Delivery partner not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })

# @method_decorator(csrf_exempt, name='dispatch')            
# class MyEarningAPI(View):

#     def post(self, request):
#         try:
#             delivery_partner_id = request.POST.get("delivery_partner_id")
#             filter_type = request.POST.get("filter")  # weekly / monthly / yearly

#             if not delivery_partner_id:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "delivery_partner_id is required"
#                 })

#             partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

#             today = timezone.now().date()

#             orders = Orders.objects.filter(
#                 delivery_partner=partner,
#                 status="delivered"
#             )

#             breakdown = []

#             # ---------------- WEEKLY ----------------
#             if filter_type == "weekly":

#                 start_date = today - timedelta(days=6)

#                 week_orders = orders.filter(delivered_time__date__gte=start_date)

#                 for i in range(7):
#                     day = start_date + timedelta(days=i)

#                     day_orders = week_orders.filter(delivered_time__date=day)

#                     breakdown.append({
#                         "date": str(day),
#                         "earning": float(day_orders.aggregate(
#                             total=Sum("paid_amount"))["total"] or 0),
#                         "deliveries": day_orders.count()
#                     })

#                 total_earning = sum(x["earning"] for x in breakdown)
#                 total_deliveries = sum(x["deliveries"] for x in breakdown)

#             # ---------------- MONTHLY ----------------
#             elif filter_type == "monthly":

#                 start_date = today.replace(day=1)

#                 month_orders = orders.filter(delivered_time__date__gte=start_date)

#                 days = defaultdict(lambda: {"earning": 0, "deliveries": 0})

#                 for order in month_orders:
#                     day = order.delivered_time.date()

#                     days[str(day)]["earning"] += float(order.paid_amount or 0)
#                     days[str(day)]["deliveries"] += 1

#                 breakdown = [
#                     {"date": d, **data}
#                     for d, data in sorted(days.items())
#                 ]

#                 total_earning = sum(x["earning"] for x in breakdown)
#                 total_deliveries = sum(x["deliveries"] for x in breakdown)

#             # ---------------- YEARLY ----------------
#             elif filter_type == "yearly":

#                 start_date = today.replace(month=1, day=1)

#                 year_orders = orders.filter(delivered_time__date__gte=start_date)

#                 months = defaultdict(lambda: {"earning": 0, "deliveries": 0})

#                 for order in year_orders:
#                     month = order.delivered_time.strftime("%Y-%m")

#                     months[month]["earning"] += float(order.paid_amount or 0)
#                     months[month]["deliveries"] += 1

#                 breakdown = [
#                     {"month": m, **data}
#                     for m, data in sorted(months.items())
#                 ]

#                 total_earning = sum(x["earning"] for x in breakdown)
#                 total_deliveries = sum(x["deliveries"] for x in breakdown)

#             else:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Invalid filter. Use weekly, monthly, or yearly"
#                 })

#             return JsonResponse({
#                 "status": True,
#                 "filter": filter_type,
#                 "summary": {
#                     "total_earning": total_earning,
#                     "total_deliveries": total_deliveries,
#                     "AvgOrder":"20",
#                 },
#                 "breakdown": breakdown
#             })

#         except DeliveryPartnerForm.DoesNotExist:
#             return JsonResponse({
#                 "status": False,
#                 "message": "Delivery partner not found"
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             })
            
@method_decorator(csrf_exempt, name='dispatch')
class MyEarningAPI(View):

    def post(self, request):
        try:
            delivery_partner_id = request.POST.get("delivery_partner_id")
            filter_type = request.POST.get("filter")

            if not delivery_partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id is required"
                })

            partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

            today = timezone.now().date()

            completions = OrderCompletion.objects.filter(
                delivery_partner=partner
            ).select_related("order")

            breakdown = []

            # ---------------- WEEKLY ----------------
            if filter_type == "weekly":

                start_date = today - timedelta(days=6)

                week_data = completions.filter(
                    created_at__date__gte=start_date
                )

                for i in range(7):

                    day = start_date + timedelta(days=i)

                    day_orders = week_data.filter(
                        created_at__date=day
                    )

                    earning = sum([
                        float(c.order.paid_amount or 0)
                        for c in day_orders
                    ])

                    breakdown.append({
                        "date": str(day),
                        "earning": earning,
                        "deliveries": day_orders.count()
                    })

                total_earning = sum(x["earning"] for x in breakdown)
                total_deliveries = sum(x["deliveries"] for x in breakdown)

            # ---------------- MONTHLY ----------------
            elif filter_type == "monthly":

                start_date = today.replace(day=1)

                month_data = completions.filter(
                    created_at__date__gte=start_date
                )

                days = defaultdict(lambda: {"earning": 0, "deliveries": 0})

                for c in month_data:

                    day = c.created_at.date()

                    days[str(day)]["earning"] += float(c.order.paid_amount or 0)
                    days[str(day)]["deliveries"] += 1

                breakdown = [
                    {"date": d, **data}
                    for d, data in sorted(days.items())
                ]

                total_earning = sum(x["earning"] for x in breakdown)
                total_deliveries = sum(x["deliveries"] for x in breakdown)

            # ---------------- YEARLY ----------------
            elif filter_type == "yearly":

                start_date = today.replace(month=1, day=1)

                year_data = completions.filter(
                    created_at__date__gte=start_date
                )

                months = defaultdict(lambda: {"earning": 0, "deliveries": 0})

                for c in year_data:

                    month = c.created_at.strftime("%Y-%m")

                    months[month]["earning"] += float(c.order.paid_amount or 0)
                    months[month]["deliveries"] += 1

                breakdown = [
                    {"month": m, **data}
                    for m, data in sorted(months.items())
                ]

                total_earning = sum(x["earning"] for x in breakdown)
                total_deliveries = sum(x["deliveries"] for x in breakdown)

            else:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid filter. Use weekly, monthly, or yearly"
                })

            avg_order = 0
            if total_deliveries > 0:
                avg_order = round(total_earning / total_deliveries, 2)

            return JsonResponse({
                "status": True,
                "filter": filter_type,
                "summary": {
                    "total_earning": total_earning,
                    "total_deliveries": total_deliveries,
                    "AvgOrder": avg_order
                },
                "breakdown": breakdown
            })

        except DeliveryPartnerForm.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Delivery partner not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryPartnerProfileAPI(View):

    def post(self, request):
        try:
            delivery_partner_id = request.POST.get("delivery_partner_id")

            if not delivery_partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id is required"
                })

            partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

            # -----------------------------
            # Orders Statistics
            # -----------------------------

            completed_orders = Orders.objects.filter(
                delivery_partner=partner,
                status="delivered"
            )

            total_deliveries = completed_orders.count()

            total_orders = Orders.objects.filter(
                delivery_partner=partner
            ).count()

            success_percent = 0
            if total_orders > 0:
                success_percent = round((total_deliveries / total_orders) * 100, 2)

            # -----------------------------
            # Average Delivery Time
            # -----------------------------

            total_minutes = 0
            count = 0

            for order in completed_orders:

                if order.delivered_time and order.created_at:

                    time_taken = order.delivered_time - order.created_at
                    minutes = time_taken.total_seconds() / 60

                    total_minutes += minutes
                    count += 1

            avg_time = round(total_minutes / count, 2) if count > 0 else 0

            # -----------------------------
            # Total Earnings
            # -----------------------------

            total_earnings = completed_orders.aggregate(
                total=Sum("paid_amount")
            )["total"] or 0

            incentive_total = OrderCompletion.objects.filter(
                delivery_partner=partner
            ).aggregate(
                total=Sum("incentive_amount")
            )["total"] or 0

            total_earnings = float(total_earnings) + float(incentive_total)

            # -----------------------------
            # Personal Information
            # -----------------------------

            personal_info = {
                "full_name": partner.full_name,
                "email": partner.email,
                "phone_number": partner.phone_number,
                "city": partner.city,
                "emp_id": partner.deliver_partnerid,
                "vehicle_number": partner.vehicle_number,
                "vehicle_type": partner.vehicle_type,
                "vehicle_model": partner.vehicle_model,
                "vehicle_color": partner.vehicle_color,
                "manufacturing_year": partner.manufacturing_year,
                "address": partner.address,
                "work_status": partner.work_status
            }

            # -----------------------------
            # Documents
            # -----------------------------

            documents = {
                "profile_image": partner.profile_image,
                "aadhar_card": partner.aadhar_card,
                "driving_license": partner.driving_license,
                "vehicle_rc_certificate": partner.vehicle_rc_certificate,
                "vehicle_image": partner.vehicle_image
            }

            # -----------------------------
            # Rating
            # -----------------------------

            rating = DeliveryPartnerRating.objects.filter(
                delivery_partner=partner
            ).aggregate(avg=models.Avg("user_rating_out_of_5"))["avg"] or 0

            return JsonResponse({
                "status": True,
                "data": {
                    "profile": {
                        "profile_image": partner.profile_image,
                        "name": partner.full_name,
                        "emp_id": partner.deliver_partnerid,
                        "rating": round(float(rating), 2)
                    },
                    "stats": {
                        "total_deliveries": total_deliveries,
                        "success_percent": success_percent,
                        "avg_delivery_time_minutes": avg_time,
                        "total_earning": total_earnings
                    },
                    "personal_information": personal_info,
                    "documents": documents
                }
            })

        except DeliveryPartnerForm.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Delivery partner not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryPartnerPaymentHistoryAPI(View):

    def post(self, request):
        try:

            delivery_partner_id = request.POST.get("delivery_partner_id")

            if not delivery_partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id required"
                })

            partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

            # Wallet
            wallet, _ = DeliveryPartnerWallet.objects.get_or_create(
                delivery_partner=partner
            )

            # Total Earned
            total_earned = wallet.total_earned

            # Pending Incentive
            pending_incentive = OrderCompletion.objects.filter(
                delivery_partner=partner,
                incentive_paid_status="pending"
            ).aggregate(total=Sum("incentive_amount"))["total"] or 0

            # Monthly Transactions
            transactions = WalletTransaction.objects.filter(
                wallet=wallet
            ).annotate(
                month=TruncMonth("created_at")
            ).order_by("-created_at")

            history = []

            for t in transactions:
                history.append({
                    "month": t.month.strftime("%B %Y"),
                    "fixed_amount": float(t.fixedamount),
                    "incentive_amount": float(t.incentiveTotalAmount),
                    "total_paid": float(t.TotalPaidAmount),
                    "date": t.created_at.strftime("%Y-%m-%d"),
                    "status": "paid"
                })

            return JsonResponse({
                "status": True,
                "data": {
                    "total_earned": float(total_earned),
                    "pending_incentive": float(pending_incentive),
                    "transaction_history": history
                }
            })

        except DeliveryPartnerForm.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Delivery partner not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
            


            
# @method_decorator(csrf_exempt, name='dispatch')
# class VerifyOTPForOutForDeliveryAPI(View):

#     def post(self, request):
#         try:
#             order_id = request.POST.get("order_id")
#             vendor_id = request.POST.get("vendor_id")
#             restaurant_id = request.POST.get("restaurant_id")
#             otp = request.POST.get("otp")

#             if not order_id or not vendor_id or not restaurant_id or not otp:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "order_id, vendor_id, restaurant_id and otp are required"
#                 }, status=400)

#             # Check vendor
#             vendor = VendorRegistration.objects.filter(id=vendor_id).first()
#             if not vendor:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Vendor not found"
#                 }, status=404)

#             # Check restaurant
#             restaurant = Restaurant.objects.filter(
#                 id=restaurant_id,
#                 vendorid=vendor
#             ).first()

#             if not restaurant:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Restaurant not found for this vendor"
#                 }, status=404)

#             # Check order
#             order = Orders.objects.filter(id=order_id).first()
#             if not order:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Order not found"
#                 }, status=404)

#             # Verify OTP
#             if order.delivery_otp != otp:
#                 return JsonResponse({
#                     "status": False,
#                     "message": "Invalid OTP"
#                 }, status=400)
                
            

#             # OTP verified
#             return JsonResponse({
#                 "status": True,
#                 "message": "OTP verified successfully",
#                 "data": {
#                     "order_id": order.id,
#                     "delivery_otp": order.delivery_otp
#                 }
#             })

#         except Exception as e:
#             return JsonResponse({
#                 "status": False,
#                 "message": str(e)
#             }, status=500)

      
            
@method_decorator(csrf_exempt, name='dispatch')
class ViewOTPByDeliveryPartnerAPI(View):

    def post(self, request):
        try:
            delivery_partner_id = request.POST.get("delivery_partner_id")
            order_id = request.POST.get("order_id")

            if not delivery_partner_id or not order_id:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id and order_id are required"
                }, status=400)

            # Check delivery partner
            partner = DeliveryPartnerForm.objects.filter(id=delivery_partner_id).first()
            if not partner:
                return JsonResponse({
                    "status": False,
                    "message": "Delivery partner not found"
                }, status=404)

            # Check order assigned to delivery partner
            order = Orders.objects.filter(
                id=order_id,
                delivery_partner=partner
            ).first()

            if not order:
                return JsonResponse({
                    "status": False,
                    "message": "Order not found or not assigned to this delivery partner"
                }, status=404)

            if not order.delivery_otp:
                return JsonResponse({
                    "status": False,
                    "message": "OTP not generated yet"
                }, status=400)

            return JsonResponse({
                "status": True,
                "message": "Delivery OTP fetched successfully",
                "data": {
                    "order_id": order.id,
                    "delivery_partner_id": partner.id,
                    "delivery_otp": order.delivery_otp
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class OrdersListAcceptedByDeliveryPartnerAPI(View):
    def post(self, request):
        try:
            partner_id = request.POST.get("partner_id")

            if not partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "partner_id is required"
                })

            partner = DeliveryPartnerForm.objects.filter(id=partner_id).first()

            if not partner:
                return JsonResponse({
                    "status": False,
                    "message": "Partner not found"
                })

            # Get accepted orders for this delivery partner
            accepted_actions = DeliveryPartnerOrderAction.objects.filter(
                delivery_partner=partner,
               
            ).select_related("order")

            orders = Orders.objects.filter(
                id__in=accepted_actions.values_list("order_id", flat=True)
            ).select_related("user").prefetch_related(
                "items__menu_item",
                "items__restaurant"
            )

            order_list = []

            for order in orders:

                cart_items = order.items.all()

                if not cart_items:
                    continue

                restaurant = cart_items[0].restaurant

                payment = getattr(order, "payment", None)

                items = []
                total_items = 0

                for item in cart_items:
                    total_items += item.quantity
                    items.append({
                        "item_name": item.menu_item.name,
                        "quantity": item.quantity,
                        "price": item.price_at_order_time
                    })

                order_list.append({
                    "order_id": order.id,
                    "order_uuid": str(order.order_uuid),
                    "order_status": order.status,
                    "otp":order.delivery_otp,

                    "restaurant_name": restaurant.restaurantname,
                    "restaurant_mobile": restaurant.phone,
                    "pickup_address": restaurant.adderess,

                    "customer_details": {
                        "name": order.user.name,
                        "email": order.user.email,
                        "customer_mo": order.user.phone_no,
                        "deliveryAddress": order.delivery_address,
                    },

                    "payment_status": payment.payment_status if payment else "pending",

                    "items": items,

                    "payment_summary": {
                        "total_items": total_items,
                        "total_amount": order.paid_amount,
                        "coupon_code": order.coupon_code,
                        "payment_mode": order.payment.payment_mode if hasattr(order, "payment") else None,
                    }
                })

            return JsonResponse({
                "status": True,
                "total_orders": len(order_list),
                "orders": order_list
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
@method_decorator(csrf_exempt, name='dispatch')
class GetNotificationReadAPI(View):

    def post(self, request):

        user_id = request.POST.get("user_id")

        if not user_id:
            return JsonResponse({
                "status": False,
                "message": "user_id is required"
            })

        notifications = Notifications.objects.filter(
            user_id=user_id,
            is_read=False
        )

        if not notifications.exists():
            return JsonResponse({
                "status": False,
                "message": "No unread notifications found"
            })
           
        message =[]
        for notification in notifications:
            message.append({
                
                "messageid":notification.id,
                "title":notification.title,
                "message":notification.message,
                "is_read":notification.is_read,
                "created_at":notification.created_at.strftime("%d-%m-%Y %H:%M")
                
            })

        return JsonResponse({
            "status": True,
            "message": "All notifications marked as read",
            "data":message,
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
        

@method_decorator(csrf_exempt, name='dispatch')
class RestaurantDetailsView(View):

    def post(self, request):

        try:
            restaurant_id = request.POST.get("restaurant_id")

            if not restaurant_id:
                return JsonResponse({
                    "status": False,
                    "message": "restaurant_id required"
                })

            try:
                restaurant = Restaurant.objects.get(
                    id=restaurant_id,
                    is_active=True,
                    approveStatus="approved"
                )
            except Restaurant.DoesNotExist:
                return JsonResponse({
                    "status": False,
                    "message": "Restaurant not found"
                })

            # ------------------------------------
            # Average Restaurant Rating
            # ------------------------------------
            avg_rating = RestaurantRating.objects.filter(
                restaurant=restaurant
            ).aggregate(avg=Avg("rating"))["avg"]

            avg_rating = round(avg_rating, 1) if avg_rating else 0

            # ------------------------------------
            # Menu List
            # ------------------------------------
            menu_items = MenuItems.objects.filter(
                restaurant=restaurant,
                is_available=True
            )

            menu_data = []

            for item in menu_items:
                menu_rating = RestaurantRating.objects.filter(
                    menu_item=item
                ).aggregate(avg=Avg("rating"))["avg"]

                menu_data.append({
                    "menu_id": item.id,
                    "name": item.name,
                    "price": str(item.price),
                    "veg_nonveg": item.VegNonVeg,
                    "description": item.description,
                    "discount_details": item.discountdetails,
                    "avg_rating": round(menu_rating,1) if menu_rating else 0,
                    "images": item.menu_images
                })

            # ------------------------------------
            # Reviews Section
            # ------------------------------------
            # reviews = MenuRating.objects.filter(
            #     menu_item__restaurant=restaurant
            # ).select_related("user","menu_item").order_by("-created_at")[:10]

            reviews = RestaurantRating.objects.filter(
              restaurant=restaurant
              ).select_related("user").order_by("-created_at")[:10]

            review_data = []

            for r in reviews:
                review_data.append({
                    "user_name": r.user.name if hasattr(r.user,"name") else r.user.email,
                    "menu_item": r.menu_item.name,
                    "rating": r.rating,
                    "review": r.description,
                    "date": r.created_at.strftime("%Y-%m-%d")
                })

            # ------------------------------------
            # Photo List (Menu + Restaurant)
            # ------------------------------------
            photos = []

            if restaurant.restaurantimage:
                photos.extend(restaurant.restaurantimage)

            for m in menu_items:
                if m.menu_images:
                    photos.extend(m.menu_images)

            # ------------------------------------
            # About Section
            # ------------------------------------
            about_data = {
                "owner_name": restaurant.ownername,
                "cuisine": restaurant.cuisine,
                "since": restaurant.since,
                "gst_number": restaurant.gst_number,
                "fssai_license": restaurant.fssai_license_no
            }

            # ------------------------------------
            # Final Response
            # ------------------------------------
            data = {
                "restaurant_id": restaurant.id,
                "restaurant_name": restaurant.restaurantname,
                "address": restaurant.adderess,
                "latitude":restaurant.latitude,
                "longitude":restaurant.longitude,
                
                "phone": restaurant.phone,
                "images": restaurant.restaurantimage,
                "opening_hours": restaurant.business_hours,
                "avg_rating": avg_rating,
                "menu_list": menu_data,
                "photo_list": photos,
                "reviews": review_data,
                "about": about_data
            }

            return JsonResponse({
                "status": True,
                "data": data
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            
@method_decorator(csrf_exempt, name='dispatch')
class BookTableAPI(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")
            table_id = request.POST.get("table_id")
            booking_start_time = request.POST.get("booking_start_time")
            booking_end_time = request.POST.get("booking_end_time")

            if not user_id or not table_id or not booking_start_time or not booking_end_time:
                return JsonResponse({
                    "status": False,
                    "message": "All fields are required"
                })

            start_time = parse_datetime(booking_start_time)
            end_time = parse_datetime(booking_end_time)

            if start_time is None or end_time is None:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS"
                })

            if start_time >= end_time:
                return JsonResponse({
                    "status": False,
                    "message": "End time must be greater than start time"
                })

            user = UserRegister.objects.get(id=user_id)
            table = RestaurantTable.objects.get(id=table_id)

            if not table.status:
                return JsonResponse({
                    "status": False,
                    "message": "Table is currently unavailable"
                })

            # Check overlapping booking
            existing_booking = TableBooking.objects.filter(
                table=table,
                status="booked"
            ).filter(
                Q(booking_start_time__lt=end_time) &
                Q(booking_end_time__gt=start_time)
            ).exists()

            if existing_booking:
                return JsonResponse({
                    "status": False,
                    "message": "Table already booked for this time slot"
                })

            # Calculate booking minutes
            total_minutes = (end_time - start_time).total_seconds() / 60

            # Calculate number of slots
            slots = math.ceil(total_minutes / table.duration)

            # Calculate total price
            total_price = slots * float(table.price)

            # Create booking
            booking = TableBooking.objects.create(
                table=table,
                user=user,
                booking_start_time=start_time,
                booking_end_time=end_time,
                booking_price=total_price,
                status="booked"
            )

            return JsonResponse({
                "status": True,
                "message": "Table booked successfully",
                "data": {
                    "booking_id": booking.id,
                    "table_name": table.table_name,
                    "seats": table.seats,
                    "start_time": start_time,
                    "end_time": end_time,
                    "total_price": total_price
                }
            })

        except RestaurantTable.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Table not found"
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
 
 
        
@method_decorator(csrf_exempt, name='dispatch')
class GetUserTableBookings(View):
    
    def post(self, request):

        user_id = request.POST.get("user_id")

        if not user_id:
            return JsonResponse({
                "status": False,
                "message": "user_id is required"
            }, status=400)

        bookings = (
            TableBooking.objects
            .filter(user_id=user_id)
            .select_related("table__restaurant")
            .prefetch_related("transactions")   # 🔥 important
            .order_by("-created_at")
        )

        result = []
        now = timezone.now()

        for booking in bookings:

            # 🔥 Expiry logic
            if booking.booking_end_time and booking.booking_end_time < now and booking.status == "booked":
                booking.status = "expired"
                booking.save(update_fields=["status"])

            # 🔥 Payment Status Logic
            transaction = booking.transactions.first()  # get latest/first transaction

            if transaction:
                payment_status = transaction.payment_status
            else:
                payment_status = "pending"

            table = booking.table
            restaurant = table.restaurant

            result.append({

                "booking_id": booking.id,

                "payment_status": payment_status,  # ✅ dynamic

                "restaurant_id": restaurant.id,
                "restaurant_name": restaurant.restaurantname,

                "table_id": table.id,
                "table_name": table.table_name,
                "seats": table.seats,

                "booking_price": str(booking.booking_price),

                "booking_start_time": booking.booking_start_time.isoformat() if booking.booking_start_time else None,
                "booking_end_time": booking.booking_end_time.isoformat() if booking.booking_end_time else None,

                "status": booking.status,

                "images": table.images,

                "created_at": booking.created_at.isoformat() if booking.created_at else None
            })

        return JsonResponse({
            "status": True,
            "total_bookings": len(result),
            "bookings": result
        })



@method_decorator(csrf_exempt, name='dispatch')
class CancelTableBooking(View):

    def post(self, request):

        booking_id = request.POST.get("booking_id")
        user_id = request.POST.get("user_id")

        if not booking_id or not user_id:
            return JsonResponse({
                "status": False,
                "message": "booking_id and user_id are required"
            }, status=400)

        try:
            booking = TableBooking.objects.get(id=booking_id, user_id=user_id)
        except TableBooking.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Booking not found"
            }, status=404)

        now = timezone.now()

        # ❌ Already cancelled / completed
        if booking.status in ["cancelled", "completed", "expired"]:
            return JsonResponse({
                "status": False,
                "message": f"Booking already {booking.status}"
            })

        # ❌ Cannot cancel after start time
        if booking.booking_start_time <= now:
            return JsonResponse({
                "status": False,
                "message": "Cannot cancel booking after start time"
            })

        # ✅ Cancel booking
        booking.status = "cancelled"
        booking.save(update_fields=["status"])

        return JsonResponse({
            "status": True,
            "message": "Booking cancelled successfully",
            "booking_id": booking.id
        })
        
        
@method_decorator(csrf_exempt, name='dispatch')
class CreateBookingTransaction(View):

    def post(self, request):

        user_id = request.POST.get("user_id")
        booking_id = request.POST.get("booking_id")
        payment_mode = request.POST.get("payment_mode")
        paid_amount = request.POST.get("paid_amount")
        transaction_no =request.POST.get("transaction_no")
        payment_status =request.POST.get("payment_status")
        
        # ✅ Validation
        if not all([user_id, booking_id, payment_mode, paid_amount]):
            return JsonResponse({
                "status": False,
                "message": "user_id, booking_id, payment_mode, paid_amount required"
            }, status=400)

        try:
            booking = TableBooking.objects.get(id=booking_id, user_id=user_id)
        except TableBooking.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Invalid booking"
            }, status=404)

        # ❌ Prevent duplicate successful payment
        existing_success = booking.transactions.filter(payment_status="success").exists()
        if existing_success:
            return JsonResponse({
                "status": False,
                "message": "Payment already completed for this booking"
            })

        # ✅ Generate transaction number
        # transaction_no = "TXN" + str(uuid.uuid4()).replace("-", "")[:10]

        # ✅ Create transaction (initially pending)
        transaction = BookingTransaction.objects.create(
            user_id=user_id,
            booking=booking,
            payment_mode=payment_mode,
            paid_amount=paid_amount,
            transaction_no=transaction_no,
            payment_status=payment_status
        )

        return JsonResponse({
            "status": True,
            "message": "Transaction created",
            "transaction": {
                "transaction_id": transaction.id,
                "transaction_no": transaction.transaction_no,
                "payment_status": transaction.payment_status
            }
        })
        
        
@method_decorator(csrf_exempt, name='dispatch')
class ExploreAPI(View):

    def get(self, request):

        # ✅ 1. Global Categories
        categories = GlobalCategory.objects.all()

        category_list = []
        for cat in categories:
            category_list.append({
                "id": cat.id,
                "name": cat.catgname,
                "category_images":cat.images,
            })

        # ✅ 2. Popular Menu Items
        popular_items = (
            MenuItems.objects
            .filter(is_available=True)
            .annotate(
                avg_rating=Avg("restaurant__ratings__rating"),
                total_ratings=Count("ratings")
            )
            .order_by("-avg_rating", "-total_ratings")[:10]   # top 10
        )

        popular_list = []

        for item in popular_items:
            popular_list.append({
                "menu_id": item.id,
                "name": item.name,
                "price": str(item.price),
                "images": item.menu_images,
                "veg_nonveg": item.VegNonVeg,
                "restaurant_id": item.restaurant.id,
                "restaurant_name": item.restaurant.restaurantname,
                "avg_rating": round(item.avg_rating, 1) if item.avg_rating else 0,
                "total_ratings": item.total_ratings
            })

        return JsonResponse({
            "status": True,
            "categories": category_list[::-1],
            "popular_items": popular_list
        })
            
            
@method_decorator(csrf_exempt, name='dispatch')
class GetMenuByGlobalCategory(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")
            category_id = request.POST.get("category_id")

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            if not user.latitude or not user.longitude:
                return JsonResponse({
                    "status": False,
                    "message": "User location not found"
                })

            user_lat = user.latitude
            user_lon = user.longitude

            # ✅ If category_id is provided
            if category_id:
                try:
                    category = GlobalCategory.objects.get(id=category_id)
                except GlobalCategory.DoesNotExist:
                    return JsonResponse({
                        "status": False,
                        "message": "Invalid category"
                    })

                menu_items = MenuItems.objects.filter(
                    categories__GlobalCategory_id=category_id,
                    is_available=True
                )

            else:
                # ✅ No category → random items
                menu_items = MenuItems.objects.filter(
                    is_available=True
                ).order_by("?")[:20]   # random 20 items

            # ✅ Optimize query
            menu_items = menu_items.select_related(
                "restaurant"
            ).annotate(
                total_orders=Count("order_items")
            )

            response_data = []

            # ✅ Cart Mapping
            cart_items_map = {}
            try:
                cart = user.cart
                cart_items = CartItems.objects.filter(
                    cart=cart,
                    order__isnull=True
                )

                cart_items_map = {
                    item.menu_item_id: item.quantity
                    for item in cart_items
                }

            except UserCart.DoesNotExist:
                pass

            # ✅ Wishlist
            wishlist_ids = set(
                Wishlist.objects.filter(user_id=user_id)
                .values_list("menu_item_id", flat=True)
            )

            for item in menu_items:
                restaurant = item.restaurant

                # ❌ Skip invalid restaurant
                if not restaurant.latitude or not restaurant.longitude:
                    continue

                if not restaurant.is_active or restaurant.approveStatus != "approved":
                    continue

                # ✅ Distance
                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    restaurant.latitude,
                    restaurant.longitude
                )

                if distance > 20:
                    continue

                # ✅ Rating
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg=Avg("rating"))["avg"] or 0

                # ✅ Orders & popularity
                total_orders = item.total_orders or 0
                highly_ordered_percent = min(total_orders * 2, 100)

                # ✅ Cart & Wishlist
                cart_qty = cart_items_map.get(item.id, 0)
                is_wishlisted = item.id in wishlist_ids

                has_addons = item.addons.filter(is_available=True).exists()

                data = {
                    "menu_id": item.id,
                    "restaurant_id": restaurant.id,
                    "menu_name": item.name,
                    "description": item.description,
                    "menu_image": item.menu_images,
                    "discount_percent": item.discount,
                    "halal": item.halal_attribute,
                    "veg_nonveg": item.VegNonVeg,
                    "spicy": item.sypicy,
                    "prep_time": item.get_prep_time_display() if item.prep_time else None,

                    "actual_price": str(item.price),
                    "price_after_discount": str(item.price_afterDesc) if item.price_afterDesc else None,

                    "restaurant_name": restaurant.restaurantname,
                    "distance_km": round(distance, 2),
                    "restaurant_rating": round(rating, 1),

                    "total_orders": total_orders,
                    "highly_ordered_percent": highly_ordered_percent,
                    "consumables": has_addons,
                    "free_delivery": True,

                    "cart_quantity": cart_qty,
                    "is_wishlisted": is_wishlisted
                }

                response_data.append(data)

            # ✅ Sorting
            response_data.sort(
                key=lambda x: (-x["highly_ordered_percent"], x["distance_km"])
            )

            return JsonResponse({
                "status": True,
                "category_id": category_id if category_id else None,
                "data": response_data
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })



def searchcalculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM

    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


@method_decorator(csrf_exempt, name='dispatch')
class SearchMenuAPI(View):

    def post(self, request):

        menu_name = request.POST.get("menu_name")
        user_id = request.POST.get("user_id")

        # if not menu_name:
        #     return JsonResponse({
        #         "status": False,
        #         "message": "menu_name is required"
        #     }, status=400)

        # ✅ Get user location (if exists)
        user_lat, user_lon = None, None

        if user_id:
            try:
                user = UserRegister.objects.get(id=user_id)
                user_lat = user.latitude
                user_lon = user.longitude
            except UserRegister.DoesNotExist:
                pass
        if not menu_name:
            menu_items = (
            MenuItems.objects
            .filter(is_available=True)
            .select_related("restaurant")
            .annotate(avg_rating=Avg("restaurant__ratings__rating"))
        )
        else:
            menu_items = (
            MenuItems.objects
            .filter(name__icontains=menu_name, is_available=True)
            .select_related("restaurant")
            .annotate(avg_rating=Avg("restaurant__ratings__rating"))
        )
            

        # ✅ Search menu items
        

        result = []

        for item in menu_items:

            restaurant = item.restaurant

            # ❌ skip inactive/unapproved restaurants
            if not restaurant.is_active or restaurant.approveStatus != "approved":
                continue

            distance = None

            # ✅ Apply distance filter (if user location exists)
            if user_lat and user_lon and restaurant.latitude and restaurant.longitude:

                distance = searchcalculate_distance(
                    user_lat, user_lon,
                    restaurant.latitude, restaurant.longitude
                )

                # ❌ skip if > 20 km
                if distance > 20:
                    continue

            result.append({
                "restaurant_id": restaurant.id,
                "restaurant_name": restaurant.restaurantname,
                "restaurant_image": restaurant.restaurantimage,

                "menu_id": item.id,
                "menu_name": item.name,
                "price": str(item.price),
                "offer": item.discount,

                "rating": round(item.avg_rating, 1) if item.avg_rating else 0,

                "distance_km": round(distance, 2) if distance else None
            })

        return JsonResponse({
            "status": True,
            "total_results": len(result),
            "data": result
        })



@method_decorator(csrf_exempt, name='dispatch')
class UserDashboardAPI(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id is required"
                }, status=400)

            # Get user
            user = UserRegister.objects.get(id=user_id)

            # ✅ Total Orders
            total_orders = Orders.objects.filter(user=user).count()

            # ✅ Total Table Bookings
            total_bookings = TableBooking.objects.filter(user=user).count()

            # ✅ Cancelled Bookings
            cancelled_bookings = TableBooking.objects.filter(
                user=user,
                status="cancelled"
            ).count()

            # ✅ Profile Image URL
            # profile_img = (
            #     request.user.profile_image.url
            #     if user.profile_img else None
            # )

            return JsonResponse({
                "status": True,
                "data": {
                    "user_name": user.name,
                    "mobile_no": user.phone_no,
                    "profile_image": user.profile_image.url if user.profile_image else None,
                    "email":user.email,

                    "total_orders": total_orders,
                    "total_bookings": total_bookings,
                    "cancelled_bookings": cancelled_bookings
                }
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            }, status=404)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)





@method_decorator(csrf_exempt, name='dispatch')
class AboutUsAPI(View):

    def get(self, request):
        try:
            about = AboutUs.objects.last()

            if not about:
                return JsonResponse({
                    "status": False,
                    "message": "No About Us data found"
                }, status=404)

            return JsonResponse({
                "status": True,
                "data": {
                    "title": about.title,
                    "description": about.description,
                    "mission": about.mission,
                    "vision": about.vision,
                    "contact_email": about.contact_email,
                    "contact_phone": about.contact_phone,
                    "address": about.address,
                    "updated_at": about.updated_at
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            


@method_decorator(csrf_exempt, name='dispatch')
class HelpSupportAPI(View):

    def get(self, request):
        try:
            support = HelpSupport.objects.last()

            if not support:
                return JsonResponse({
                    "status": False,
                    "message": "No Help & Support data found"
                }, status=404)

            return JsonResponse({
                "status": True,
                "data": {
                    "title": support.title,
                    "description": support.description,
                    "contact_email": support.contact_email,
                    "contact_phone": support.contact_phone,
                    "address": support.address,
                    "working_hours": support.working_hours,
                    "updated_at": support.updated_at
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)



@method_decorator(csrf_exempt, name='dispatch')
class AddUpdateRestaurantRating(View):

    def post(self, request):
        user_id = request.POST.get("user_id")
        restaurant_id = request.POST.get("restaurant_id")
        rating = request.POST.get("rating")
        description = request.POST.get("description", "")

        # ✅ Validation
        if not user_id or not restaurant_id or not rating:
            return JsonResponse({
                "status": False,
                "message": "user_id, restaurant_id and rating are required"
            }, status=400)

        # ✅ Rating validation
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            return JsonResponse({
                "status": False,
                "message": "rating must be between 1 to 5"
            }, status=400)

        # ✅ Fetch objects safely
        try:
            user = UserRegister.objects.get(id=user_id)
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            }, status=404)
        except Restaurant.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Restaurant not found"
            }, status=404)

        # 🚀 Update or Create (FIXED FIELD)
        obj, created = RestaurantRating.objects.update_or_create(
            user=user,
            restaurant=restaurant,   # ✅ FIXED
            defaults={
                "rating": rating,
                "description": description
            }
        )

        return JsonResponse({
            "status": True,
            "message": "Rating added" if created else "Rating updated",
            "data": {
                "id": obj.id,
                "rating": obj.rating,
                "description": obj.description
            }
        })
        
@method_decorator(csrf_exempt, name='dispatch')
class AddUpdateDeliveryPartnerRating(View):

    def post(self, request):
        user_id = request.POST.get("user_id")
        partner_id = request.POST.get("delivery_partner_id")
        rating = request.POST.get("rating")

        # ✅ Validation
        if not user_id or not partner_id or not rating:
            return JsonResponse({
                "status": False,
                "message": "user_id, delivery_partner_id and rating are required"
            }, status=400)

        try:
            rating = float(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except:
            return JsonResponse({
                "status": False,
                "message": "rating must be between 1.0 to 5.0"
            }, status=400)

        try:
            user = UserRegister.objects.get(id=user_id)
            partner = DeliveryPartnerForm.objects.get(id=partner_id)
        except:
            return JsonResponse({
                "status": False,
                "message": "Invalid user or delivery partner"
            }, status=404)

        # 🚀 Update or Create
        obj, created = DeliveryPartnerRating.objects.update_or_create(
            user=user,
            delivery_partner=partner,
            defaults={
                "user_rating_out_of_5": rating
            }
        )

        return JsonResponse({
            "status": True,
            "message": "Rating added" if created else "Rating updated",
            "data": {
                "id": obj.id,
                "rating": float(obj.user_rating_out_of_5)
            }
        })
        
    
@method_decorator(csrf_exempt, name='dispatch')
class OrdersListAcceptedByDeliveryPartnerAPI(View):
    def post(self, request):
        try:
            partner_id = request.POST.get("partner_id")

            if not partner_id:
                return JsonResponse({
                    "status": False,
                    "message": "partner_id is required"
                })

            partner = DeliveryPartnerForm.objects.filter(id=partner_id).first()

            if not partner:
                return JsonResponse({
                    "status": False,
                    "message": "Partner not found"
                })

            # Get accepted orders for this delivery partner
            accepted_actions = DeliveryPartnerOrderAction.objects.filter(
                delivery_partner=partner,
               
            ).select_related("order")

            orders = Orders.objects.filter(
                id__in=accepted_actions.values_list("order_id", flat=True)
            ).select_related("user").prefetch_related(
                "items__menu_item",
                "items__restaurant"
            )

            order_list = []

            for order in orders:

                cart_items = order.items.all()

                if not cart_items:
                    continue

                restaurant = cart_items[0].restaurant

                payment = getattr(order, "payment", None)

                items = []
                total_items = 0

                for item in cart_items:
                    total_items += item.quantity
                    items.append({
                        "item_name": item.menu_item.name,
                        "quantity": item.quantity,
                        "price": item.price_at_order_time
                    })

                order_list.append({
                    "order_id": order.id,
                    "order_uuid": str(order.order_uuid),
                    "order_status": order.status,
                    "otp":order.delivery_otp,

                    "restaurant_name": restaurant.restaurantname,
                    "restaurant_mobile": restaurant.phone,
                    "pickup_address": restaurant.adderess,

                    "customer_details": {
                        "name": order.user.name,
                        "email": order.user.email,
                        "customer_mo": order.user.phone_no,
                        "deliveryAddress": order.delivery_address,
                    },

                    "payment_status": payment.payment_status if payment else "pending",

                    "items": items,

                    "payment_summary": {
                        "total_items": total_items,
                        "total_amount": order.paid_amount,
                        "coupon_code": order.coupon_code,
                        "payment_mode": order.payment.payment_mode if hasattr(order, "payment") else None,
                    }
                })

            return JsonResponse({
                "status": True,
                "total_orders": len(order_list),
                "orders": order_list
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
@method_decorator(csrf_exempt, name='dispatch')
class GetNotificationReadAPI(View):

    def post(self, request):

        user_id = request.POST.get("user_id")

        if not user_id:
            return JsonResponse({
                "status": False,
                "message": "user_id is required"
            })

        notifications = Notifications.objects.filter(
            user_id=user_id,
            is_read=False
        )

        if not notifications.exists():
            return JsonResponse({
                "status": False,
                "message": "No unread notifications found"
            })
           
        message =[]
        for notification in notifications:
            message.append({
                
                "messageid":notification.id,
                "title":notification.title,
                "message":notification.message,
                "is_read":notification.is_read,
                "created_at":notification.created_at.strftime("%d-%m-%Y %H:%M")
                
            })

        return JsonResponse({
            "status": True,
            "message": "All notifications marked as read",
            "data":message,
        })
        
        
@method_decorator(csrf_exempt, name='dispatch')
class AddMoneyToWalletView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")
            amount = request.POST.get("amount")
            payment_method = request.POST.get("payment_method")

            # ✅ Validation
            if not user_id or not amount or not payment_method:
                return JsonResponse({
                    "status": False,
                    "message": "user_id, amount and payment_method are required"
                }, status=400)

            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValueError
            except:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid amount"
                }, status=400)

            if payment_method not in dict(UserWalletTransaction.PAYMENT_METHOD_CHOICES):
                return JsonResponse({
                    "status": False,
                    "message": "Invalid payment method"
                }, status=400)

            # ✅ Get User
            user = UserRegister.objects.get(id=user_id)

            # ✅ Get or Create Wallet
            wallet, created = UserWallet.objects.get_or_create(user=user)

            # ✅ Create Transaction (initially pending)
            transaction = UserWalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='credit',
                payment_method=payment_method,
                status='pending',
                done_by='user'
            )

            # 🔥 Simulate Payment Success (replace with real gateway later)
            transaction.status = 'success'
            transaction.save()

            # ✅ Update Wallet Balance ONLY if success
            if transaction.status == 'success':
                wallet.balance += amount
                wallet.save()

            return JsonResponse({
                "status": True,
                "message": "Money added successfully",
                "wallet_balance": str(wallet.balance),
                "transaction_id": str(transaction.transaction_id),
                "payment_method": payment_method
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            }, status=404)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class WalletDetailsView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id is required"
                }, status=400)

            # ✅ Get User
            user = UserRegister.objects.get(id=user_id)

            # ✅ Get or Create Wallet
            wallet, created = UserWallet.objects.get_or_create(user=user)

            # ✅ Get Transactions (latest first)
            transactions = UserWalletTransaction.objects.filter(
                wallet=wallet
            ).order_by("-created_at")

            transaction_list = []

            for txn in transactions:
                transaction_list.append({
                    "transaction_id": str(txn.transaction_id),
                    "amount": str(txn.amount),
                    "transaction_type": txn.transaction_type,
                    "payment_method": txn.payment_method,
                    "status": txn.status,
                    "done_by": txn.done_by,
                    "date": txn.created_at.strftime("%Y-%m-%d %H:%M:%S")
                })

            return JsonResponse({
                "status": True,
                "wallet_balance": str(wallet.balance),
                "total_transactions": len(transaction_list),
                "transactions": transaction_list
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            }, status=404)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            
@method_decorator(csrf_exempt, name='dispatch')
class RestaurantList(View):
    def get(self , request):
        restaurants = Restaurant.objects.filter(is_active=True, approveStatus="approved")

        result = []
        for restaurant in restaurants:
            result.append({
                "id": restaurant.id,
                "name": restaurant.restaurantname,
               
            })

        return JsonResponse({
            "status": True,
            "total_restaurants": len(result),
            "restaurants": result
        })
        
        
@method_decorator(csrf_exempt, name='dispatch')
class RestaurantPartyBookingView(View):

    def post(self, request):
        try:
            restaurant_id = request.POST.get("restaurantid")
            user_id = request.POST.get("user_id")
            name = request.POST.get("name")
            mobileno = request.POST.get("mobileno")
            order_details = request.POST.get("order_details")
            deliveryaddress = request.POST.get("deliveryaddress")

            # ✅ Validation
            if not all([restaurant_id, user_id, name, mobileno, order_details, deliveryaddress]):
                return JsonResponse({
                    "status": "error",
                    "message": "All fields are required"
                }, status=400)

            # ✅ Fetch related objects
            restaurant = get_object_or_404(Restaurant, id=restaurant_id)
            user = get_object_or_404(UserRegister, id=user_id)

            # ✅ Create booking
            booking = RestaurantPartyBooking.objects.create(
                restaurant=restaurant,
                user=user,
                name=name,
                Mobileno=mobileno,
                order_details=order_details,
                deliveryAdddress=deliveryaddress
            )

            return JsonResponse({
                "status": "success",
                "message": "Party booking created successfully",
                "booking_id": booking.id
            }, status=201)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
            
            
            

            

@method_decorator(csrf_exempt, name='dispatch')
class EditUserProfileView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id is required"
                })

            user = UserRegister.objects.get(id=user_id)

            # ✅ Get fields (optional update)
            name = request.POST.get("name")
            email = request.POST.get("email")
            phone_no = request.POST.get("phone_no")
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")

            # ✅ Update only if provided
            if name:
                user.name = name

            if email:
                # Check duplicate email
                if UserRegister.objects.exclude(id=user_id).filter(email=email).exists():
                    return JsonResponse({
                        "status": False,
                        "message": "Email already exists"
                    })
                user.email = email

            if phone_no:
                # Check duplicate phone
                if UserRegister.objects.exclude(id=user_id).filter(phone_no=phone_no).exists():
                    return JsonResponse({
                        "status": False,
                        "message": "Phone number already exists"
                    })
                user.phone_no = phone_no

            if latitude:
                user.latitude = latitude

            if longitude:
                user.longitude = longitude

            # ✅ Profile Image (file upload)
            if 'profile_image' in request.FILES:
                user.profile_image = request.FILES['profile_image']

            user.save()

            return JsonResponse({
                "status": True,
                "message": "Profile updated successfully"
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
@method_decorator(csrf_exempt, name='dispatch')
class UserWishlistView(View):

    def post(self, request):
        try:
            user_id = request.POST.get("user_id")

            if not user_id:
                return JsonResponse({
                    "status": False,
                    "message": "user_id is required"
                }, status=400)

            # ✅ Get user
            user = UserRegister.objects.get(id=user_id)

            # ✅ Get wishlist items
            wishlist_items = Wishlist.objects.select_related(
                "menu_item__restaurant"
            ).filter(user=user)

            response_data = []

            for wish in wishlist_items:
                item = wish.menu_item
                restaurant = item.restaurant

                # ✅ Skip invalid restaurant
                if not restaurant.is_active or restaurant.approveStatus != "approved":
                    continue

                # ✅ Rating
                rating = RestaurantRating.objects.filter(
                    restaurant=restaurant
                ).aggregate(avg=Avg("rating"))["avg"] or 0

                # ✅ Addons
                has_addons = item.addons.filter(is_available=True).exists()

                data = {
                    "wishlist_id": wish.id,
                    "menu_id": item.id,
                    "restaurant_id": restaurant.id,

                    "menu_name": item.name,
                    "description": item.description,
                    "menu_image": item.menu_images,

                    "veg_nonveg": item.VegNonVeg,
                    "halal": item.halal_attribute,
                    "spicy": item.sypicy,

                    "actual_price": str(item.price),
                    "price_after_discount": str(item.price_afterDesc) if item.price_afterDesc else None,
                    "discount_percent": item.discount,

                    "prep_time": item.get_prep_time_display() if item.prep_time else None,

                    "restaurant_name": restaurant.restaurantname,
                    "restaurant_rating": round(rating, 1),

                    "consumables": has_addons,
                    "is_wishlisted": True
                }

                response_data.append(data)

            return JsonResponse({
                "status": True,
                "count": len(response_data),
                "data": response_data
            })

        except UserRegister.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "User not found"
            }, status=404)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)