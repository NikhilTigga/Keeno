from django.urls import path
from .views import *
urlpatterns = [
    
    path('login/',  LoginView.as_view(),name='login'),
    path('',AdminDashboardView.as_view(),name='AdminDashboard'),
    
    
    path('create-global-category/', CreateGlobalCategoryView.as_view(), name='create_global_category'),
    path('verifyCreatorView',VerifyCreatorView.as_view(),name='verifyCreatorView'),
    path('verifyDeliveryPartnerView',verifyDeliveryPartnerView,name='verifyDeliveryPartnerView'),
    path('verifyDeliveryPartnerAction',verifyDeliveryPartnerAction,name='verifyDeliveryPartnerAction'),
    path('setOrderIncentiveView',setOrderIncentiveView, name='setOrderIncentiveView'),
    path('setOrderIncentiveView',setOrderIncentiveView,name='setOrderIncentiveView'),
    path('setOrderIncentiveSave',setOrderIncentiveSave,name='setOrderIncentiveSave'),
    path('setOrderIncentiveDelete',setOrderIncentiveDelete,name='setOrderIncentiveDelete'),
    
    path('paydeliverypatner',paydeliverypatner,name='paydeliverypatner'),
    
    path('payDeliveryPartnerAPI', PayDeliveryPartnerAPI.as_view(),name='payDeliveryPartnerAPI'),
    
    path('update_restaurant_status',update_restaurant_status,name='update_restaurant_status'),
    path('commission/',        setCommissionView,   name='setCommissionView'),
    path('commission/save/',   setCommissionSave,   name='setCommissionSave'),
    path('commission/delete/', setCommissionDelete, name='setCommissionDelete'),
    
    path('vendor-payouts/',vendorPayoutView,name='vendorPayoutView'),
    path('vendor-payouts/update-status/',vendorPayoutUpdateStatus,name='vendorPayoutUpdateStatus'),
    path('vendor-payouts/bulk-update/',vendorPayoutBulkUpdate,name='vendorPayoutBulkUpdate'),
    
    
    
    
    path('vendor-payouts/create/',vendorPayoutCreatePage,name='vendorPayoutCreatePage'),
    path('vendor-payouts/pending-orders/',vendorPayoutPendingOrders, name='vendorPayoutPendingOrders'),
    path('vendor-payouts/create-records/',vendorPayoutCreate,name='vendorPayoutCreate'),
    path("wallet-history/", GetWalletHistoryAPI.as_view(), name="walletHistoryAPI"),
    path("deliveryReportGetWalletHistoryAPI",DeliveryReportGetWalletHistoryAPI.as_view(),name="deliveryReportGetWalletHistoryAPI"),
    path("payoutReportView",PayoutReportView.as_view(),name='payoutReportView'),
    path("add_banner",add_banner,name="add_banner"),
    path("banner/<int:banner_id>/delete_image/", delete_banner_image, name="delete_banner_image"),
    path("calculateTotalDashboard",calculateTotalDashboard.as_view(),name="calculateTotalDashboard"),
    
    
    
     # ── About Us ──────────────────────────────────────────────────────────────
    path('about-us/',aboutUsPage,  name='aboutUsPage'),
    path('about-us/get/',aboutUsView,  name='aboutUsView'),
    path('about-us/save/',aboutUsSave,  name='aboutUsSave'),

    # ── Help & Support ────────────────────────────────────────────────────────
    path('help-support/',helpSupportPage,  name='helpSupportPage'),
    path('help-support/get/',helpSupportView,  name='helpSupportView'),
    path('help-support/save/',helpSupportSave,  name='helpSupportSave'),
    
    path('logout/', LogoutView.as_view(), name='logout'),
    
    
     # ── Page ──────────────────────────────────────────────────────────────────
    path(
        "global-categories/",
        global_category_page,
        name="global_category_page",
    ),
 
    # ── AJAX API ──────────────────────────────────────────────────────────────
    path(
        "global-categories/list/",
        list_global_categories,
        name="list_global_categories",
    ),
    path(
        "global-categories/create/",
        create_global_category,
        name="create_global_category",
    ),
    path(
        "global-categories/update/",
        update_global_category,
        name="update_global_category",
    ),
    path(
        "global-categories/delete/",
        delete_global_category,
        name="delete_global_category",
    ),
    
    path('spotlights/',spotlight_page,    name='spotlight_page'),
    path('spotlights/list/',list_spotlights,   name='list_spotlights'),
    path('spotlights/create/',create_spotlight,  name='create_spotlight'),
    path('spotlights/update/',update_spotlight,  name='update_spotlight'),
    path('spotlights/delete/',delete_spotlight,  name='delete_spotlight'),
    
    path('party-bookings/',partyBookingListView,  name='partyBookingListView'),
    path('party-bookings/action/',partyBookingAction,  name='partyBookingAction'),
    
]
