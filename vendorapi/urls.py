from django.urls import path
from .views import *

urlpatterns = [
    
    path('vendor_register', VendorRegisterView.as_view(), name='vendor_register'),
    path('vendor_login', VendorLoginView.as_view(), name='vendor_login'),
    path('verify_otp', VerifyVendorOTPView.as_view(), name='verify_otp'),
    path('vendorRestaurantRegistrationForm',VendorRestaurantRegistrationForm.as_view(),name='vendorRestaurantRegistrationForm'),
    path('createCategory', CreateCategoryView.as_view(), name='createCategory'),
    path('CreateMenuItemView',CreateMenuItemView.as_view(),name='CreateMenuItemView'),
    path('GetGlobalCategoryView',GetGlobalCategoryView.as_view(),name='GetGlobalCategoryView'),
    path('categoryListByRestaurantView',CategoryListByRestaurantView.as_view(),name='categoryListByRestaurantView'),
    path('editCategoryView',EditCategoryView.as_view(),name='editCategoryView'),
    path('restaurantListByVendorView',RestaurantListByVendorView.as_view(),name='restaurantListByVendorView'),
    path('getRestaurantMenuAPI',GetRestaurantMenuAPI.as_view(),name='getRestaurantMenuAPI'),
    path('getRestaurantCategoryAPI',GetRestaurantCategoryAPI.as_view(),name='getRestaurantCategoryAPI'),
    path('createAddonMasterAPI',CreateAddonMasterAPI.as_view(),name='createAddonMasterAPI'),
    path('listAddonMasterAPI',ListAddonMasterAPI.as_view(),name='listAddonMasterAPI'),
    path('editAddonMasterAPI',EditAddonMasterAPI.as_view(),name='editAddonMasterAPI'),
    path('vendorOrderManagementAPI',VendorOrderManagementAPI.as_view(),name='vendorOrderManagementAPI'),
    path('updateOrderStatusAPI',UpdateOrderStatusAPI.as_view(),name='updateOrderStatusAPI'),
    path('generateOutForDeliveryOTPAPI',GenerateOutForDeliveryOTPAPI.as_view(),name='generateOutForDeliveryOTPAPI'),
    path('createStaffProfileAPI',CreateStaffProfileAPI.as_view(),name='createStaffProfileAPI'),
    path('getStaffListAPI',GetStaffListAPI.as_view(),name='getStaffListAPI'),
    path('restaurantDashboardAPI',RestaurantDashboardAPI.as_view(),name='restaurantDashboardAPI'),
    path('restaurantReportAPI',RestaurantReportAPI.as_view(),name='restaurantReportAPI'),
    path('verifyOTPForOutForDeliveryAPI',VerifyOTPForOutForDeliveryAPI.as_view(),name='verifyOTPForOutForDeliveryAPI'),
    path('createRestaurantTable',CreateRestaurantTable.as_view(),name='createRestaurantTable'),
    path('vendorviewRestaurantTableList',GetRestaurantTables.as_view(),name='vendorviewRestaurantTableList'),
    path('featuredCategoryListView',FeaturedCategoryListView.as_view(),name='featuredCategoryListView'),
    
    path('pendingOrderCountAPI',PendingOrderCountAPI.as_view(),name='pendingOrderCountAPI'),
    
    path('partyEnquiryByRestaurantView',PartyEnquiryByRestaurantView.as_view(),name='partyEnquiryByRestaurantView'),
    
    path('updatepartyEnquiryStatus',UpdatepartyEnquiryStatus.as_view(),name='updatepartyEnquiryStatus'),
    
    path('updateRestaurantisOpenStatus',UpdateRestaurantisOpenStatus.as_view(),name='updateRestaurantisOpenStatus'),
]
