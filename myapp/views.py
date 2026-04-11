



# Create your views here.

import json
from django.shortcuts import render
from django.http import JsonResponse
from .models import *
from myapi.models import *
from django.views import View
from django.shortcuts import redirect
from vendorapi.models import GlobalCategory
from vendorapi.models import Restaurant,DeliveryPartnerForm,SetOrderIncentive,DeliveryPartnerWallet,WalletTransaction,OrderCompletion ,CommissionSetting , VendorPayout, Orders , Banner,VendorRegistration,  AboutUs ,HelpSupport , Spotlight
from django.db.models import Sum
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .serializers import *
from django.utils.decorators import method_decorator
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from datetime import timedelta, datetime
import os
from django.conf import settings
from django.db.models import Q
from django.utils.dateparse import parse_date

import uuid

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
class LoginView(View):
    def get(self, request):
     return render(request, 'login.html')
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not email or not password:
            return JsonResponse({
                'error': 'Email and password required'
            }, status=400)
        try:
            admin = AdminLogin.objects.get(
                email=email,
                password=password
            )
            request.session['admin_email'] = admin.email
            request.session['role']=admin.roles.name
            return JsonResponse({
                'message': 'Login successful'
            })
        except AdminLogin.DoesNotExist:
            return JsonResponse({
                'error': 'Invalid email or password'
            }, status=401)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):

    def post(self, request):
        try:
            # Remove specific session keys
            request.session.pop('admin_email', None)
            request.session.pop('role', None)

            # OR clear full session
            request.session.flush()

            return JsonResponse({
                "status": True,
                "message": "Logout successful"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

    # Optional (for browser logout via GET)
    def get(self, request):
        request.session.flush()
        return redirect('login') 
    
    
class AdminDashboardView(View):
    def get (self, request):
        if request.session.get('admin_email'):
            return render(request,'dash.html')
        else:
            return redirect('login')
        
        

class calculateTotalDashboard(View):
    def get (self ,request):

        total_users=UserRegister.objects.count()
        
        print('Total Users',total_users)
        total_vendors=VendorRegistration.objects.count()
        total_deliveryPatners=DeliveryPartnerForm.objects.count()
        total_comission =VendorPayout.objects.aggregate(total = Sum('commission_amount'))['total'] or 0
        print("Total Comission is ",total_comission)
        return JsonResponse({
            'status':True,
            'data':{
                'total_users':total_users,
                'total_vendors':total_vendors,
                'total_deliveryPatners':total_deliveryPatners,
                'total_comission': total_comission,
               

            }
            
        })



        
class CreateGlobalCategoryView(View):
    def post(self, request):
        if not request.session.get('admin_email'):
             return redirect('login')
        try:
            catgname = request.POST.get("catgname")
            # Check duplicate category (optional)
            if GlobalCategory.objects.filter(catgname__iexact=catgname).exists():
                return JsonResponse({
                    "status": False,
                    "message": "Global category already exists"
                }, status=400)
            # Create Global Category
            global_category = GlobalCategory.objects.create(
                catgname=catgname
            )
            return JsonResponse({
                "status": True,
                "message": "Global category created successfully",
                "data": {
                    "id": global_category.id,
                    "catgname": global_category.catgname,
                    "created_at": global_category.created_at
                }
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
class VerifyCreatorView(View):

    def get(self, request):

        # 🔐 Admin session check
        if not request.session.get('admin_email'):
            return redirect('login')

        # 🔎 Detect AJAX / API call
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':

            status_filter = request.GET.get("status")
            search = request.GET.get("search", "").lower()

            restaurants = Restaurant.objects.select_related("approvedby").all()

            # Status filter
            if status_filter and status_filter != "all":
                restaurants = restaurants.filter(approveStatus=status_filter)

            data = []

            for r in restaurants:

                # Search filter
                if search:
                    if search not in (
                        r.restaurantname.lower() +
                        r.ownername.lower() +
                        r.email.lower() +
                        r.phone.lower()
                    ):
                        continue

                data.append({
                    "id": r.id,
                    "restaurantname": r.restaurantname,
                    "ownername": r.ownername,
                    "phone": r.phone,
                    "email": r.email,
                    "adderess": r.adderess,
                    "approveStatus": r.approveStatus,
                    "approvedby": r.approvedby.username if r.approvedby else None,
                    "created_at": r.created_at.isoformat(),
                    "images": r.restaurantimage if r.restaurantimage else []
                })

            summary = {
                "total": Restaurant.objects.count(),
                "pending": Restaurant.objects.filter(approveStatus="pending").count(),
                "approved": Restaurant.objects.filter(approveStatus="approved").count(),
                "rejected": Restaurant.objects.filter(approveStatus="rejected").count(),
            }

            return JsonResponse({
                "status": True,
                "summary": summary,
                "restaurants": data
            })

        # 📄 Normal page load
        return render(request, 'sideBarPages/verifyVendor.html')
    
    

def verifyDeliveryPartnerView(request):
    """
    Serves both the page (GET) and the AJAX data-fetch (GET + XMLHttpRequest).
    """
    if not request.session.get('admin_email'):
            return redirect('login')
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        partners = DeliveryPartnerForm.objects.all()
        serializer = DeliveryPartnerSerializer(partners, many=True)
        return JsonResponse({"status": True, "partners": serializer.data})

    return render(request, 'sideBarPages/verifyDeliveryPatner.html')



@require_http_methods(["POST"])
def verifyDeliveryPartnerAction(request):
    
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    Approve or reject a single delivery partner.
    Called via AJAX from the table action buttons.
    """
    try:
        body   = json.loads(request.body)
        pid    = int(body.get("id", 0))
        action = body.get("action", "")
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"status": False, "message": "Invalid request body."}, status=400)

    if action not in ("approve", "reject"):
        return JsonResponse({"status": False, "message": "Invalid action."}, status=400)

    try:
        partner = DeliveryPartnerForm.objects.get(pk=pid)
    except DeliveryPartnerForm.DoesNotExist:
        return JsonResponse({"status": False, "message": "Partner not found."}, status=404)

    partner.approval_status = "approved" if action == "approve" else "rejected"
    partner.save(update_fields=["approval_status"])

    return JsonResponse({
        "status":  True,
        "message": f"Partner {partner.full_name} has been {partner.approval_status}.",
        "new_status": partner.approval_status,
    })
    

def setOrderIncentiveView(request):
    
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    GET  (normal)  → render the HTML template
    GET  (AJAX)    → return JSON list of all incentive rules
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        incentives = SetOrderIncentive.objects.all().order_by('more_than_order')
        
        serializer=IncentiveSerializer(incentives, many=True)
        return JsonResponse({
            "status":     True,
            "incentives": serializer.data,
        })
    return render(request, 'sideBarPages/setIncentive.html')


def setOrderIncentiveView(request):
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    GET  (normal)  → render the HTML template
    GET  (AJAX)    → return JSON list of all incentive rules
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        incentives = SetOrderIncentive.objects.all().order_by('more_than_order')
        serializer=IncentiveSerializer(incentives, many=True)
        return JsonResponse({
            "status":     True,
            "incentives": serializer.data,
        })
    return render(request, 'sideBarPages/setIncentive.html')


@require_http_methods(["POST"])
def setOrderIncentiveSave(request):
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    Body (JSON):
      { "more_than_order": <int>, "incentive_amount": <float> }          ← create
      { "id": <int>, "more_than_order": <int>, "incentive_amount": <float> } ← update
    """
    try:
        body   = json.loads(request.body)
        orders = int(body.get("more_than_order", 0))
        amount = float(body.get("incentive_amount", -1))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"status": False, "message": "Invalid data."}, status=400)

    if orders < 1:
        return JsonResponse({"status": False, "message": "Orders must be at least 1."})
    if amount < 0:
        return JsonResponse({"status": False, "message": "Amount cannot be negative."})

    inc_id = body.get("id")

    if inc_id:
        # ── Update ──
        try:
            inc = SetOrderIncentive.objects.get(pk=int(inc_id))
        except SetOrderIncentive.DoesNotExist:
            return JsonResponse({"status": False, "message": "Rule not found."}, status=404)
        inc.more_than_order  = orders
        inc.incentive_amount = amount
        inc.save(update_fields=["more_than_order", "incentive_amount"])
        serializer=IncentiveSerializer(inc)
        return JsonResponse({
            "status":  True,
            "message": "Incentive rule updated successfully.",
            "incentive":serializer.data,
        })
    else:
        # ── Create ──
        inc = SetOrderIncentive.objects.create(
            more_than_order=orders,
            incentive_amount=amount,
        )
        serializer = IncentiveSerializer(inc)
        return JsonResponse({
            "status":  True,
            "message": "Incentive rule created successfully.",
            "incentive": serializer.data,
        })
        
        
@require_http_methods(["POST"])
def setOrderIncentiveDelete(request):
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    Body (JSON): { "id": <int> }
    """
    try:
        body   = json.loads(request.body)
        inc_id = int(body.get("id", 0))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"status": False, "message": "Invalid request."}, status=400)

    try:
        inc = SetOrderIncentive.objects.get(pk=inc_id)
    except SetOrderIncentive.DoesNotExist:
        return JsonResponse({"status": False, "message": "Rule not found."}, status=404)

    inc.delete()
    return JsonResponse({"status": True, "message": "Incentive rule deleted successfully."})

def paydeliverypatner(request):
    if not request.session.get('admin_email'):
            return redirect('login')
    patner=DeliveryPartnerForm.objects.all()
    
    return render(request,'sideBarPages/payDeliveryPatner.html',{"deliveryPatner": patner})

@method_decorator(csrf_exempt, name='dispatch')
class PayDeliveryPartnerAPI(View):
    

    def post(self, request):
        if not request.session.get('admin_email'):
            return redirect('login')
        try:
            
            

            delivery_partner_id = request.POST.get("delivery_partner_id")
            to_date = request.POST.get("to_date")
            fixed_amount = request.POST.get("fixed_amount", 0)
            
            
            print('delivery_partner_id',delivery_partner_id)
            print('to_date',to_date)
            print('fixed_amount',fixed_amount)

            if not delivery_partner_id or not to_date:
                return JsonResponse({
                    "status": False,
                    "message": "delivery_partner_id and to_date required"
                })

            fixed_amount = float(fixed_amount)

            partner = DeliveryPartnerForm.objects.get(id=delivery_partner_id)

            wallet, created = DeliveryPartnerWallet.objects.get_or_create(
                delivery_partner=partner
            )

            to_date = datetime.strptime(to_date, "%Y-%m-%d")

            # Get earliest unpaid incentive date
            first_unpaid = OrderCompletion.objects.filter(
                delivery_partner=partner,
                incentive_paid_status="pending"
            ).order_by("created_at").first()

            if not first_unpaid:
                return JsonResponse({
                    "status": False,
                    "message": "No pending incentives"
                })

            from_date = first_unpaid.created_at.date()

            # Get incentives between dates
            pending_incentives = OrderCompletion.objects.filter(
                delivery_partner=partner,
                incentive_paid_status="pending",
                created_at__date__gte=from_date,
                created_at__date__lte=to_date
            )

            incentive_total = pending_incentives.aggregate(
                total=Sum("incentive_amount")
            )["total"] or 0

            total_paid = float(incentive_total) + fixed_amount

            if total_paid == 0:
                return JsonResponse({
                    "status": False,
                    "message": "No incentives found for this period"
                })

            # Create wallet transaction
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                fixedamount=fixed_amount,
                incentiveTotalAmount=incentive_total,
                TotalPaidAmount=total_paid,
                description=f"Payout from {from_date} to {to_date.date()}"
            )

            # Attach orders
            transaction.order_completions.set(pending_incentives)

            # Mark incentives paid
            pending_incentives.update(incentive_paid_status="paid")

            # Update wallet
            wallet.balance += total_paid
            wallet.total_earned += total_paid
            wallet.save()

            return JsonResponse({
                "status": True,
                "message": "Payment completed",
                "data": {
                    "from_date": str(from_date),
                    "to_date": str(to_date.date()),
                    "incentive_total": float(incentive_total),
                    "fixed_amount": fixed_amount,
                    "total_paid": total_paid,
                    "orders_paid": pending_incentives.count()
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
            
@csrf_exempt
def update_restaurant_status(request):

    if request.method == "POST":
        if not request.session.get('admin_email'):
            return redirect('login')
        try:
            data = json.loads(request.body)

            restaurant_id = data.get("restaurant_id")
            action = data.get("action")

            restaurant = Restaurant.objects.get(id=restaurant_id)

            if action == "approve":
                restaurant.approveStatus = "approved"
            else:
                restaurant.approveStatus = "rejected"

            restaurant.save()

            return JsonResponse({
                "status": True,
                "message": "Restaurant status updated"
            })

        except Restaurant.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Restaurant not found"
            })

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            })
            
def commission_to_dict(c: CommissionSetting) -> dict:
    """Serialise a CommissionSetting instance to a JSON-safe dict."""
    return {
        "id":               c.pk,
        "restaurant":       c.restaurant_id,
        "restaurant_name":  c.restaurant.restaurantname if c.restaurant else None,
        "commission_type":  c.commission_type,
        "commission_value": str(c.commission_value),
        "min_commission":   str(c.min_commission) if c.min_commission is not None else None,
        "max_commission":   str(c.max_commission) if c.max_commission is not None else None,
        "is_active":        c.is_active,
        "created_at":       c.created_at.isoformat() if c.created_at else None,
        "updated_at":       c.updated_at.isoformat() if c.updated_at else None,
    }


def setCommissionView(request):
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    GET (AJAX)  → returns JSON list of all CommissionSetting records
    GET (HTML)  → renders the commission settings page
    """
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        commissions = (
            CommissionSetting.objects
            .select_related("restaurant")
            .order_by("-created_at")
        )
        return JsonResponse({
            "status":      True,
            "commissions": [commission_to_dict(c) for c in commissions],
        })
 
    # HTML render – pass restaurants for the <select> dropdown
    restaurants = Restaurant.objects.filter(is_active=True).order_by("restaurantname")
    return render(request, "sideBarPages/setCommission.html", {"restaurants": restaurants})
 
 
@require_http_methods(["POST"])
def setCommissionSave(request):
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    POST (AJAX JSON)
    Body fields:
        id               – int, optional (present → update, absent → create)
        restaurant       – int | null
        commission_type  – "percentage" | "fixed"
        commission_value – float
        min_commission   – float | null
        max_commission   – float | null
        is_active        – bool
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"status": False, "message": "Invalid JSON payload."}, status=400)
 
    # ── Validate required fields ──────────────────────────────────────────
    commission_type  = data.get("commission_type", "").strip()
    commission_value = data.get("commission_value")
 
    if commission_type not in ("percentage", "fixed"):
        return JsonResponse({"status": False, "message": "Invalid commission type."}, status=400)
 
    try:
        commission_value = float(commission_value)
        if commission_value < 0:
            raise ValueError
        if commission_type == "percentage" and commission_value > 100:
            return JsonResponse({"status": False, "message": "Percentage cannot exceed 100."}, status=400)
    except (TypeError, ValueError):
        return JsonResponse({"status": False, "message": "Invalid commission value."}, status=400)
 
    # ── Optional numeric fields ───────────────────────────────────────────
    min_commission = data.get("min_commission")
    max_commission = data.get("max_commission")
    try:
        min_commission = float(min_commission) if min_commission is not None else None
        max_commission = float(max_commission) if max_commission is not None else None
    except (TypeError, ValueError):
        return JsonResponse({"status": False, "message": "Invalid min/max commission."}, status=400)
 
    if min_commission is not None and max_commission is not None:
        if min_commission > max_commission:
            return JsonResponse(
                {"status": False, "message": "Min commission cannot exceed Max commission."}, status=400
            )
 
    # ── Restaurant FK ─────────────────────────────────────────────────────
    restaurant_id = data.get("restaurant")
    restaurant    = None
    if restaurant_id:
        try:
            restaurant = Restaurant.objects.get(pk=int(restaurant_id))
        except (Restaurant.DoesNotExist, ValueError, TypeError):
            return JsonResponse({"status": False, "message": "Restaurant not found."}, status=404)
 
    is_active = bool(data.get("is_active", True))
    record_id = data.get("id")
 
    # ── Create or Update ──────────────────────────────────────────────────
    if record_id:
        # UPDATE
        try:
            obj = CommissionSetting.objects.get(pk=int(record_id))
        except CommissionSetting.DoesNotExist:
            return JsonResponse({"status": False, "message": "Commission rule not found."}, status=404)
 
        obj.restaurant       = restaurant
        obj.commission_type  = commission_type
        obj.commission_value = commission_value
        obj.min_commission   = min_commission
        obj.max_commission   = max_commission
        obj.is_active        = is_active
        obj.save()
        return JsonResponse({
            "status":  True,
            "message": "Commission rule updated successfully.",
            "commission": commission_to_dict(obj),
        })
    else:
        # CREATE
        obj = CommissionSetting.objects.create(
            restaurant       = restaurant,
            commission_type  = commission_type,
            commission_value = commission_value,
            min_commission   = min_commission,
            max_commission   = max_commission,
            is_active        = is_active,
        )
        return JsonResponse({
            "status":  True,
            "message": "Commission rule created successfully.",
            "commission": commission_to_dict(obj),
        }, status=201)
        

@require_http_methods(["POST"])
def setCommissionDelete(request):
    
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    POST (AJAX JSON)
    Body: { "id": <int> }
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"status": False, "message": "Invalid JSON payload."}, status=400)
 
    record_id = data.get("id")
    if not record_id:
        return JsonResponse({"status": False, "message": "ID is required."}, status=400)
 
    try:
        obj = CommissionSetting.objects.get(pk=int(record_id))
    except CommissionSetting.DoesNotExist:
        return JsonResponse({"status": False, "message": "Commission rule not found."}, status=404)
 
    obj.delete()
    return JsonResponse({"status": True, "message": "Commission rule deleted successfully."})












def payout_to_dict(p: VendorPayout) -> dict:
    return {
        "id":                p.pk,
        "order_id":          p.order_id,
        "order_uuid":        str(p.order.order_uuid) if p.order else None,
        # ✅ Include restaurant FK int so JS can match it against the dropdown value="{{ r.id }}"
        "restaurant":        p.restaurant_id,
        "restaurant_name":   p.restaurant.restaurantname if p.restaurant else None,
        "order_amount":      str(p.order_amount),
        "commission_amount": str(p.commission_amount),
        "vendor_earning":    str(p.vendor_earning),
        "payout_status":     p.payout_status,
        "payout_date":       p.payout_date.isoformat() if p.payout_date else None,
        "created_at":        p.created_at.isoformat() if p.created_at else None,
    }
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Commission helper
# ─────────────────────────────────────────────────────────────────────────────
 
def calculate_commission(order_amount: Decimal, restaurant: Restaurant) -> Decimal:
    """
    Look up the active CommissionSetting for this restaurant
    (falls back to global if no restaurant-specific rule exists).
    Returns the calculated commission amount.
    """
    setting = (
        CommissionSetting.objects.filter(restaurant=restaurant, is_active=True).first()
        or CommissionSetting.objects.filter(restaurant__isnull=True, is_active=True).first()
    )
 
    if not setting:
        return Decimal("0.00")
 
    if setting.commission_type == "percentage":
        commission = (order_amount * setting.commission_value / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if setting.min_commission is not None:
            commission = max(commission, setting.min_commission)
        if setting.max_commission is not None:
            commission = min(commission, setting.max_commission)
    else:
        commission = setting.commission_value
 
    return commission.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 1. List / Page Render
# ─────────────────────────────────────────────────────────────────────────────
 

def vendorPayoutView(request):
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    GET (AJAX)  → JSON list of all VendorPayout records.
    GET (HTML)  → renders vendor_payout.html.
 
    ✅ FIX: Always pass `restaurants` queryset to the template so the
    filter dropdown is populated even when no payout records exist yet.
    """
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        payouts = (
            VendorPayout.objects
            .select_related("restaurant", "order")
            .order_by("-created_at")
        )
        return JsonResponse({
            "status":  True,
            "payouts": [payout_to_dict(p) for p in payouts],
        })
 
    # HTML render — pass ALL active approved restaurants for the filter <select>
    restaurants = (
        Restaurant.objects
        .filter(is_active=True, approveStatus="approved")
        .order_by("restaurantname")
    )
    return render(request, "sideBarPages/vendorPayout.html", {"restaurants": restaurants})
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 2. Auto-create payout when an order is delivered
#    Call this from your order status-update view / signal.
# ─────────────────────────────────────────────────────────────────────────────
 
@transaction.atomic
def create_vendor_payout_for_order(order: Orders):
    """
    Creates a VendorPayout for a delivered order.
    Safe to call multiple times — skips if a payout already exists.
 
    Usage (inside your order delivered logic):
        from .vendor_payout_views import create_vendor_payout_for_order
        create_vendor_payout_for_order(order_instance)
    """
    if VendorPayout.objects.filter(order=order).exists():
        return None
 
    # Resolve restaurant from the first order item
    first_item = order.order_items.select_related("menuitem__restaurant").first()
    if not first_item:
        return None
    restaurant = first_item.menuitem.restaurant
 
    order_amount = order.paid_amount or Decimal("0.00")
    commission   = calculate_commission(order_amount, restaurant)
    vendor_earn  = (order_amount - commission).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
 
    return VendorPayout.objects.create(
        restaurant        = restaurant,
        order             = order,
        order_amount      = order_amount,
        commission_amount = commission,
        vendor_earning    = vendor_earn,
        payout_status     = "pending",
    )
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 3. Update single payout status
# ─────────────────────────────────────────────────────────────────────────────
 

@require_http_methods(["POST"])
def vendorPayoutUpdateStatus(request):
    
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    POST (AJAX JSON)
    Body: { "id": int, "payout_status": str, "payout_date": str|null }
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"status": False, "message": "Invalid JSON."}, status=400)
 
    record_id   = data.get("id")
    new_status  = data.get("payout_status", "").strip()
    payout_date = data.get("payout_date")
 
    if new_status not in ("pending", "processing", "paid"):
        return JsonResponse({"status": False, "message": "Invalid status value."}, status=400)
 
    if new_status == "paid" and not payout_date:
        return JsonResponse({"status": False, "message": "Payout date required when marking as Paid."}, status=400)
 
    try:
        obj = VendorPayout.objects.get(pk=int(record_id))
    except (VendorPayout.DoesNotExist, TypeError, ValueError):
        return JsonResponse({"status": False, "message": "Payout record not found."}, status=404)
 
    obj.payout_status = new_status
    if payout_date:
        obj.payout_date = parse_datetime(payout_date) or timezone.now()
    else:
        obj.payout_date = None
    obj.save()
 
    return JsonResponse({
        "status":  True,
        "message": "Payout status updated successfully.",
        "payout":  payout_to_dict(obj),
    })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 4. Bulk update status
# ─────────────────────────────────────────────────────────────────────────────
 

@require_http_methods(["POST"])
def vendorPayoutBulkUpdate(request):
    
    if not request.session.get('admin_email'):
            return redirect('login')
    """
    POST (AJAX JSON)
    Body: { "ids": [int, ...], "payout_status": str, "payout_date": str|null }
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"status": False, "message": "Invalid JSON."}, status=400)
 
    ids         = data.get("ids", [])
    new_status  = data.get("payout_status", "").strip()
    payout_date = data.get("payout_date")
 
    if not ids or not isinstance(ids, list):
        return JsonResponse({"status": False, "message": "No IDs provided."}, status=400)
 
    if new_status not in ("pending", "processing", "paid"):
        return JsonResponse({"status": False, "message": "Invalid status value."}, status=400)
 
    parsed_date = None
    if new_status == "paid":
        parsed_date = parse_datetime(payout_date) if payout_date else timezone.now()
 
    updated_qs = VendorPayout.objects.filter(pk__in=ids)
    count      = updated_qs.update(payout_status=new_status, payout_date=parsed_date)
 
    return JsonResponse({
        "status":        True,
        "message":       f"{count} payout(s) updated to '{new_status}'.",
        "updated_count": count,
    })
    
    
    
    
    
    
    
    
    
    
    
    
def calculate_commission(order_amount: Decimal, restaurant: Restaurant) -> Decimal:
    """
    Resolves: restaurant-specific rule → global rule → 0
    """
    setting = (
        CommissionSetting.objects.filter(restaurant=restaurant, is_active=True).first()
        or CommissionSetting.objects.filter(restaurant__isnull=True, is_active=True).first()
    )
    if not setting:
        return Decimal("0.00")
 
    if setting.commission_type == "percentage":
        commission = (order_amount * setting.commission_value / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if setting.min_commission is not None:
            commission = max(commission, setting.min_commission)
        if setting.max_commission is not None:
            commission = min(commission, setting.max_commission)
    else:
        commission = setting.commission_value
 
    return commission.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 1. Page render for "Create Payout" admin page
# ─────────────────────────────────────────────────────────────────────────────
 

def vendorPayoutCreatePage(request):
    """Renders the create-payout admin page."""
    restaurants = (
        Restaurant.objects
        .filter(is_active=True, approveStatus="approved")
        .order_by("restaurantname")
    )
    return render(request, "sideBarPages/makevendorPayout.html", {"restaurants": restaurants})
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 2. API: Fetch delivered orders that don't have a payout yet
# ─────────────────────────────────────────────────────────────────────────────
 


 
def vendorPayoutPendingOrders(request):
    """
    GET → returns delivered orders that do NOT yet have a VendorPayout.
    Also calculates estimated commission.
    """

    orders = (
        Orders.objects
        .filter(status="delivered")
        .exclude(vendor_payout__isnull=False)
        .select_related("user")
        .prefetch_related("items__menu_item__restaurant")   # FIXED
        .order_by("-created_at")
    )

    result = []

    for order in orders:

        first_item = (
            order.items
            .select_related("menu_item__restaurant")
            .first()
        )

        if not first_item:
            continue

        restaurant = first_item.menu_item.restaurant

        order_amount = order.paid_amount or Decimal("0.00")

        commission = calculate_commission(order_amount, restaurant)

        vendor_earn = max(order_amount - commission, Decimal("0.00"))

        result.append({
            "order_id": order.pk,
            "order_uuid": str(order.order_uuid),

            "restaurant_id": restaurant.pk,
            "restaurant_name": restaurant.restaurantname,

            "user_email": order.user.email if order.user else None,

            "paid_amount": str(order_amount),
            "estimated_commission": str(commission),
            "estimated_earning": str(vendor_earn),

            "delivered_time": order.delivered_time.isoformat() if order.delivered_time else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        })

    return JsonResponse({
        "status": True,
        "orders": result
    })
 
# ─────────────────────────────────────────────────────────────────────────────
# 3. API: Admin creates payout records for selected orders
# ─────────────────────────────────────────────────────────────────────────────
 



@require_http_methods(["POST"])
def vendorPayoutCreate(request):

    """
    POST JSON
    Body:
    {
        "order_ids": [1,2,3]
    }

    Creates VendorPayout records for delivered orders.
    Skips if payout already exists.
    """

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse(
            {"status": False, "message": "Invalid JSON payload"},
            status=400
        )

    order_ids = data.get("order_ids")

    if not order_ids or not isinstance(order_ids, list):
        return JsonResponse(
            {"status": False, "message": "order_ids must be a list"},
            status=400
        )

    created = 0
    skipped = 0
    created_order_ids = []
    errors = []

    with transaction.atomic():

        for order_id in order_ids:

            try:
                order = (
                    Orders.objects
                    .select_related("user")
                    .prefetch_related("items__menu_item__restaurant")   # ✅ FIXED
                    .get(id=int(order_id), status="delivered")
                )

            except Orders.DoesNotExist:
                errors.append(f"Order #{order_id} not found or not delivered")
                skipped += 1
                continue


            # Skip if payout already exists
            if VendorPayout.objects.filter(order=order).exists():
                skipped += 1
                continue


            # Get first order item
            first_item = (
                order.items                                   # ✅ FIXED
                .select_related("menu_item__restaurant")
                .first()
            )

            if not first_item:
                errors.append(f"Order #{order_id} has no order items")
                skipped += 1
                continue


            restaurant = first_item.menu_item.restaurant

            order_amount = order.paid_amount or Decimal("0.00")

            if order_amount <= Decimal("0.00"):
                errors.append(f"Order #{order_id} has zero paid amount")
                skipped += 1
                continue


            # Calculate commission
            commission = calculate_commission(order_amount, restaurant)

            vendor_earning = max(
                (order_amount - commission).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                Decimal("0.00")
            )


            VendorPayout.objects.create(
                restaurant=restaurant,
                order=order,
                order_amount=order_amount,
                commission_amount=commission,
                vendor_earning=vendor_earning,
                payout_status="pending"
            )

            created += 1
            created_order_ids.append(order_id)


    return JsonResponse({
        "status": True,
        "created": created,
        "skipped": skipped,
        "created_order_ids": created_order_ids,
        "errors": errors,
        "message": f"{created} payout(s) created, {skipped} skipped"
    })
  
  
  
    
class GetWalletHistoryAPI(View):

    def get(self, request):
        try:
            transactions = (
                WalletTransaction.objects
                .select_related("wallet")  # safer first
                .prefetch_related("order_completions")
                .order_by("-created_at")
            )

            data = []

            for t in transactions:
                # SAFE access
                wallet = t.wallet
                partner = getattr(wallet, "delivery_partner", None)

                partner_name = partner.full_name if partner else "Unknown"
                partner_id = partner.id if partner else None

                data.append({
                    "partner_name": partner_name,
                    "partner_id": partner_id,
                    "period": t.created_at.strftime("%d %b %Y"),
                    "incentive_total": float(t.incentiveTotalAmount or 0),
                    "fixed_amount": float(t.fixedamount or 0),
                    "total_paid": float(t.TotalPaidAmount or 0),
                    "orders_count": t.order_completions.count(),
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M")
                })

            return JsonResponse({
                "status": True,
                "data": data
            })

        except Exception as e:
            print("ERROR:", str(e))  # 🔥 IMPORTANT
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)
            
            
class DeliveryReportGetWalletHistoryAPI(View):
    

    def get(self, request):

        if not request.session.get('admin_email'):
            return redirect('login')
        try:
            # Get from/to dates from query params
            from_date = request.GET.get("from")
            to_date = request.GET.get("to")

            filters = Q()
            if from_date:
                filters &= Q(created_at__date__gte=parse_date(from_date))
            if to_date:
                filters &= Q(created_at__date__lte=parse_date(to_date))

            transactions = (
                WalletTransaction.objects
                .select_related("wallet")
                .prefetch_related("order_completions")
                .filter(filters)
                .order_by("-created_at")
            )

            data = []
            for t in transactions:
                wallet = t.wallet
                partner = getattr(wallet, "delivery_partner", None)
                partner_name = partner.full_name if partner else "Unknown"
                partner_id = partner.id if partner else None

                data.append({
                    "partner_name": partner_name,
                    "partner_id": partner_id,
                    "period": t.created_at.strftime("%d %b %Y"),
                    "incentive_total": float(t.incentiveTotalAmount or 0),
                    "fixed_amount": float(t.fixedamount or 0),
                    "total_paid": float(t.TotalPaidAmount or 0),
                    "orders_count": t.order_completions.count(),
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M")
                })

            return JsonResponse({
                "status": True,
                "data": data
            })

        except Exception as e:
            print("ERROR:", str(e))
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)


class PayoutReportView(View):
    
        
    def get(self, request):
        if not request.session.get('admin_email'):
           return redirect('login')
       
        return render(request, "sideBarPages/deliveryPatnerPayoutReport.html")  
    
    
    


def add_banner(request):

    if request.method == "POST":
        title = request.POST.get("title")
        is_active = request.POST.get("is_active") == "true"

        files = request.FILES.getlist("images")

        image_paths = []

        # ✅ Ensure directory exists
        upload_dir = os.path.join(settings.MEDIA_ROOT, "banners")
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            file_path = os.path.join(upload_dir, file.name)

            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            image_paths.append(f"/media/banners/{file.name}")

        Banner.objects.create(
            title=title,
            is_active=is_active,
            images=image_paths
        )

        return redirect("add_banner")

    banners = Banner.objects.all().order_by("-id")

    return render(request, "sideBarPages/banners.html", {
        "banners": banners
    })



def delete_banner_image(request, banner_id):
    if request.method == "POST":
        image_to_delete = request.POST.get("image")  # full path like "/media/banners/xyz.jpg"
        banner = Banner.objects.get(id=banner_id)

        if image_to_delete in banner.images:
            # Delete file from media folder
            file_path = os.path.join(settings.BASE_DIR, image_to_delete.lstrip("/"))
            if os.path.exists(file_path):
                os.remove(file_path)

            # Remove from images list
            banner.delete()
          

        return JsonResponse({"status": "success"})
    
    
    
    
    
    

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
 
def serialize_about(obj):
    """Return a JSON-safe dict for an AboutUs instance."""
    return {
        "id":            obj.pk,
        "title":         obj.title,
        "description":   obj.description,
        "mission":       obj.mission or "",
        "vision":        obj.vision or "",
        "contact_email": obj.contact_email or "",
        "contact_phone": obj.contact_phone or "",
        "address":       obj.address or "",
        "updated_at":    obj.updated_at.isoformat() if obj.updated_at else None,
    }
 
 
def serialize_support(obj):
    """Return a JSON-safe dict for a HelpSupport instance."""
    return {
        "id":            obj.pk,
        "title":         obj.title,
        "description":   obj.description,
        "contact_email": obj.contact_email,
        "contact_phone": obj.contact_phone,
        "address":       obj.address or "",
        "working_hours": obj.working_hours or "",
        "updated_at":    obj.updated_at.isoformat() if obj.updated_at else None,
    }
 
 
# ─────────────────────────────────────────────────────────────────────────────
# About Us
# ─────────────────────────────────────────────────────────────────────────────
 

def aboutUsPage(request):
    if not request.session.get('admin_email'):
           return redirect('login')
       
    """Render the About Us admin page."""
    return render(request, 'sideBarPages/aboutus.html')
 
 

def aboutUsView(request):
    """
    GET  → return the single AboutUs record (or empty status).
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': False, 'message': 'Invalid request.'}, status=400)
 
    obj = AboutUs.objects.first()
    if obj:
        return JsonResponse({'status': True, 'about': serialize_about(obj)})
    return JsonResponse({'status': False, 'about': None})
 
 

def aboutUsSave(request):
    """
    POST → create or update the AboutUs record.
    Expects JSON body:
        {
            "id":            <int|null>,
            "title":         <str>,
            "description":   <str>,
            "mission":       <str>,
            "vision":        <str>,
            "contact_email": <str>,
            "contact_phone": <str>,
            "address":       <str>
        }
    """
    if request.method != 'POST':
        return JsonResponse({'status': False, 'message': 'Method not allowed.'}, status=405)
 
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': False, 'message': 'Invalid request.'}, status=400)
 
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'status': False, 'message': 'Invalid JSON.'}, status=400)
 
    # Required field validation
    title       = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
 
    if not title:
        return JsonResponse({'status': False, 'message': 'Title is required.'})
    if not description:
        return JsonResponse({'status': False, 'message': 'Description is required.'})
 
    record_id = data.get('id')
 
    # Try to get by id; fallback to the first record; else create new
    if record_id:
        try:
            obj = AboutUs.objects.get(pk=record_id)
        except AboutUs.DoesNotExist:
            obj = AboutUs.objects.first() or AboutUs()
    else:
        obj = AboutUs.objects.first() or AboutUs()
 
    obj.title         = title
    obj.description   = description
    obj.mission       = (data.get('mission') or '').strip() or None
    obj.vision        = (data.get('vision') or '').strip() or None
    obj.contact_email = (data.get('contact_email') or '').strip() or None
    obj.contact_phone = (data.get('contact_phone') or '').strip() or None
    obj.address       = (data.get('address') or '').strip() or None
 
    obj.save()
 
    return JsonResponse({'status': True, 'message': 'Saved successfully.', 'about': serialize_about(obj)})
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Help & Support
# ─────────────────────────────────────────────────────────────────────────────
 

def helpSupportPage(request):
    
    if not request.session.get('admin_email'):
           return redirect('login')
    """Render the Help & Support admin page."""
    return render(request, 'sideBarPages/helpandSupport.html')
 
 

def helpSupportView(request):
    """
    GET → return the single HelpSupport record (or empty status).
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': False, 'message': 'Invalid request.'}, status=400)
 
    obj = HelpSupport.objects.first()
    if obj:
        return JsonResponse({'status': True, 'support': serialize_support(obj)})
    return JsonResponse({'status': False, 'support': None})
 
 

def helpSupportSave(request):
    """
    POST → create or update the HelpSupport record.
    Expects JSON body:
        {
            "id":            <int|null>,
            "title":         <str>,
            "description":   <str>,
            "contact_email": <str>,
            "contact_phone": <str>,
            "address":       <str>,
            "working_hours": <str>
        }
    """
    if request.method != 'POST':
        return JsonResponse({'status': False, 'message': 'Method not allowed.'}, status=405)
 
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': False, 'message': 'Invalid request.'}, status=400)
 
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'status': False, 'message': 'Invalid JSON.'}, status=400)
 
    # Required field validation
    title         = (data.get('title') or '').strip()
    description   = (data.get('description') or '').strip()
    contact_email = (data.get('contact_email') or '').strip()
    contact_phone = (data.get('contact_phone') or '').strip()
 
    errors = []
    if not title:         errors.append('Title')
    if not description:   errors.append('Description')
    if not contact_email: errors.append('Contact Email')
    if not contact_phone: errors.append('Contact Phone')
 
    if errors:
        return JsonResponse({'status': False, 'message': f"{', '.join(errors)} {'is' if len(errors)==1 else 'are'} required."})
 
    record_id = data.get('id')
 
    # Try to get by id; fallback to first; else create new
    if record_id:
        try:
            obj = HelpSupport.objects.get(pk=record_id)
        except HelpSupport.DoesNotExist:
            obj = HelpSupport.objects.first() or HelpSupport()
    else:
        obj = HelpSupport.objects.first() or HelpSupport()
 
    obj.title         = title
    obj.description   = description
    obj.contact_email = contact_email
    obj.contact_phone = contact_phone
    obj.address       = (data.get('address') or '').strip() or None
    obj.working_hours = (data.get('working_hours') or '').strip() or None
 
    obj.save()
 
    return JsonResponse({'status': True, 'message': 'Saved successfully.', 'support': serialize_support(obj)})
 
 
 
 
 

# ─────────────────────────────────────────────────────────────────────────────
# Helper: save an uploaded image file and return its public URL
# ─────────────────────────────────────────────────────────────────────────────
def _save_image(uploaded_file) -> str:
    """
    Saves an uploaded image to MEDIA_ROOT/global_categories/<uuid>.<ext>
    and returns the relative URL (e.g. /media/global_categories/abc.jpg).
    """
    ext      = os.path.splitext(uploaded_file.name)[1].lower()
    filename = f"global_categories/{uuid.uuid4().hex}{ext}"
    path     = default_storage.save(filename, ContentFile(uploaded_file.read()))
    return default_storage.url(path)          # returns e.g. /media/global_categories/abc.jpg
 
 
def _delete_image(url: str):
    """
    Deletes an image from storage given its URL.
    Gracefully ignores errors if the file no longer exists.
    """
    try:
        # Strip the leading /media/ prefix that default_storage.url() adds
        from django.conf import settings
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        if url.startswith(media_url):
            relative_path = url[len(media_url):]
            if default_storage.exists(relative_path):
                default_storage.delete(relative_path)
    except Exception:
        pass
 
 
def _category_to_dict(cat: GlobalCategory) -> dict:
    """Serialise a GlobalCategory instance to a JSON-safe dict."""
    return {
        "id":         cat.pk,
        "catgname":   cat.catgname,
        "images":     cat.images or [],
        "created_at": cat.created_at.isoformat(),
    }
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 1.  Page render  —  GET /admin/global-categories/
# ─────────────────────────────────────────────────────────────────────────────

def global_category_page(request):
    """Renders the Global Category management HTML page."""
    return render(request, "sideBarPages/createGlobalCategory.html")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 2.  List  —  GET /admin/global-categories/list/
# ─────────────────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def list_global_categories(request):
    """
    Returns all GlobalCategory records ordered by newest first.
 
    Response JSON:
    {
        "status": true,
        "categories": [ { id, catgname, images, created_at }, … ]
    }
    """
    categories = GlobalCategory.objects.all()
    return JsonResponse({
        "status":     True,
        "categories": [_category_to_dict(c) for c in categories],
    })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 3.  Create  —  POST /admin/global-categories/create/
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt                          # remove if you pass the CSRF token from JS
@require_http_methods(["POST"])
def create_global_category(request):
    """
    Creates a new GlobalCategory.
 
    Expected: multipart/form-data
        catgname  (str, required)
        images    (file, optional, multiple)
 
    Response JSON:
    {
        "status": true,
        "category": { id, catgname, images, created_at }
    }
    """
    catgname = request.POST.get("catgname", "").strip()
 
    if not catgname:
        return JsonResponse({"status": False, "message": "Category name is required."})
 
    # Check for duplicate name (case-insensitive)
    if GlobalCategory.objects.filter(catgname__iexact=catgname).exists():
        return JsonResponse({"status": False, "message": "A category with this name already exists."})
 
    # Save uploaded images
    image_urls = []
    for f in request.FILES.getlist("images"):
        try:
            url = _save_image(f)
            image_urls.append(url)
        except Exception as e:
            return JsonResponse({"status": False, "message": f"Image upload failed: {str(e)}"})
 
    category = GlobalCategory.objects.create(
        catgname   = catgname,
        images     = image_urls,
        created_at = timezone.now(),
    )
 
    return JsonResponse({
        "status":   True,
        "message":  "Category created successfully.",
        "category": _category_to_dict(category),
    })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 4.  Update  —  POST /admin/global-categories/update/
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def update_global_category(request):
    """
    Updates an existing GlobalCategory.
 
    Expected: multipart/form-data
        id              (int, required)
        catgname        (str, required)
        images          (file, optional, multiple  — NEW images to add)
        remove_images[] (str, optional, multiple   — URLs of images to delete)
 
    Response JSON:
    {
        "status": true,
        "category": { id, catgname, images, created_at }
    }
    """
    cat_id   = request.POST.get("id", "").strip()
    catgname = request.POST.get("catgname", "").strip()
 
    if not cat_id or not catgname:
        return JsonResponse({"status": False, "message": "ID and category name are required."})
 
    try:
        category = GlobalCategory.objects.get(pk=int(cat_id))
    except (GlobalCategory.DoesNotExist, ValueError):
        return JsonResponse({"status": False, "message": "Category not found."})
 
    # Duplicate name check (exclude self)
    if (GlobalCategory.objects
            .filter(catgname__iexact=catgname)
            .exclude(pk=category.pk)
            .exists()):
        return JsonResponse({"status": False, "message": "Another category with this name already exists."})
 
    # 1️⃣  Remove images the admin marked for deletion
    urls_to_remove = request.POST.getlist("remove_images[]")
    existing_images = list(category.images or [])
    for url in urls_to_remove:
        _delete_image(url)
        if url in existing_images:
            existing_images.remove(url)
 
    # 2️⃣  Add newly uploaded images
    for f in request.FILES.getlist("images"):
        try:
            url = _save_image(f)
            existing_images.append(url)
        except Exception as e:
            return JsonResponse({"status": False, "message": f"Image upload failed: {str(e)}"})
 
    category.catgname = catgname
    category.images   = existing_images
    category.save()
 
    return JsonResponse({
        "status":   True,
        "message":  "Category updated successfully.",
        "category": _category_to_dict(category),
    })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 5.  Delete  —  POST /admin/global-categories/delete/
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def delete_global_category(request):
    """
    Deletes a GlobalCategory and all its stored images.
 
    Expected: application/json  { "id": <int> }
 
    Response JSON:
    {
        "status": true,
        "message": "Category deleted successfully."
    }
    """
    try:
        body   = json.loads(request.body)
        cat_id = int(body.get("id", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"status": False, "message": "Invalid request body."})
 
    try:
        category = GlobalCategory.objects.get(pk=cat_id)
    except GlobalCategory.DoesNotExist:
        return JsonResponse({"status": False, "message": "Category not found."})
 
    # Delete all stored images from disk / cloud storage
    for url in (category.images or []):
        _delete_image(url)
 
    category.delete()
 
    return JsonResponse({"status": True, "message": "Category deleted successfully."})






# ── Helper: save uploaded image file ─────────────────────────────────────────
def _save_image(file_obj, folder="spotlights"):
    """Save an uploaded image to media/<folder>/ and return its URL path."""
    ext      = os.path.splitext(file_obj.name)[1].lower()
    filename = f"{folder}/{uuid.uuid4().hex}{ext}"
    path     = default_storage.save(filename, file_obj)
    return default_storage.url(path)
 
 
# ── Helper: serialise a Spotlight instance ────────────────────────────────────
def _spotlight_to_dict(spotlight):
    return {
        "id":             spotlight.id,
        "spotlight_name": spotlight.spotlight_name,
        "spotlight_img":  spotlight.spotlight_img or [],
        "created_at":     spotlight.created_at.isoformat(),
    }
 
 
# ── List all spotlights ───────────────────────────────────────────────────────

def spotlight_page(request):
    """Render the spotlight management page."""
    return render(request, "sideBarPages/spotlight.html")
 
 

def list_spotlights(request):
    """Return all spotlights as JSON."""
    spotlights = Spotlight.objects.all().order_by("-created_at")
    return JsonResponse({
        "status":     True,
        "spotlights": [_spotlight_to_dict(s) for s in spotlights],
    })
 
 
# ── Create spotlight ──────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def create_spotlight(request):
    name = request.POST.get("spotlight_name", "").strip()
    if not name:
        return JsonResponse({"status": False, "message": "Spotlight name is required."})
 
    images = request.FILES.getlist("images")
    image_urls = [_save_image(img) for img in images]
 
    spotlight = Spotlight.objects.create(
        spotlight_name=name,
        spotlight_img=image_urls,
    )
 
    return JsonResponse({
        "status":    True,
        "spotlight": _spotlight_to_dict(spotlight),
    })
 
 
# ── Update spotlight ──────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def update_spotlight(request):
    spotlight_id = request.POST.get("id", "").strip()
    name         = request.POST.get("spotlight_name", "").strip()
 
    if not spotlight_id or not name:
        return JsonResponse({"status": False, "message": "ID and spotlight name are required."})
 
    try:
        spotlight = Spotlight.objects.get(id=spotlight_id)
    except Spotlight.DoesNotExist:
        return JsonResponse({"status": False, "message": "Spotlight not found."})
 
    spotlight.spotlight_name = name
 
    # Remove images the user flagged for deletion
    remove_urls    = request.POST.getlist("remove_images[]")
    existing_imgs  = spotlight.spotlight_img or []
    kept_imgs      = [url for url in existing_imgs if url not in remove_urls]
 
    # Delete removed files from storage (optional – skip if you prefer soft-delete)
    for url in remove_urls:
        try:
            # Convert URL back to relative path understood by default_storage
            relative = url.lstrip("/").replace(
                default_storage.base_url.lstrip("/"), "", 1
            )
            if default_storage.exists(relative):
                default_storage.delete(relative)
        except Exception:
            pass  # Best-effort deletion
 
    # Add newly uploaded images
    new_images  = request.FILES.getlist("images")
    new_urls    = [_save_image(img) for img in new_images]
 
    spotlight.spotlight_img = kept_imgs + new_urls
    spotlight.save()
 
    return JsonResponse({
        "status":    True,
        "spotlight": _spotlight_to_dict(spotlight),
    })
 
 
# ── Delete spotlight ──────────────────────────────────────────────────────────

@csrf_exempt          # CSRF is handled by the fetch call sending the token via header if needed
@require_http_methods(["POST"])
def delete_spotlight(request):
    try:
        body = json.loads(request.body)
        spotlight_id = int(body.get("id", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"status": False, "message": "Invalid request body."})
 
    try:
        spotlight = Spotlight.objects.get(id=spotlight_id)
    except Spotlight.DoesNotExist:
        return JsonResponse({"status": False, "message": "Spotlight not found."})
 
    # Optionally delete associated image files from storage
    for url in (spotlight.spotlight_img or []):
        try:
            relative = url.lstrip("/").replace(
                default_storage.base_url.lstrip("/"), "", 1
            )
            if default_storage.exists(relative):
                default_storage.delete(relative)
        except Exception:
            pass
 
    spotlight.delete()
    return JsonResponse({"status": True, "message": "Spotlight deleted successfully."})