from django.urls import path
from .views import *



urlpatterns = [
    
    path('userRegister',UserRegisterView.as_view(),name='userRegister'),
    path('userLoginAPI',UserLoginAPI.as_view(),name='userLoginAPI'),
    path('verifyUserOTP',VerifyUserOTP.as_view(),name='verifyUserOTP'),
    path('updateUserLocationView',UpdateUserLocationView.as_view(),name='updateUserLocationView'),
    path('exploreAPI',ExploreAPI.as_view(),name='exploreAPI'),
    
    path('getMenuByGlobalCategory',GetMenuByGlobalCategory.as_view(),name='getMenuByGlobalCategory'),

    path('restaurantByCategoryView',RestaurantByCategoryView.as_view(),name='restaurantByCategoryView'),
    
    path('restaurantDetailWithMenuView',RestaurantDetailWithMenuView.as_view(),name='restaurantDetailWithMenuView'),
    
    path('todaysSpecialMenuItemsView',TodaysSpecialMenuItemsView.as_view(),name='todaysSpecialMenuItemsView'),
    
    path('keenoPicksTodayMenuItemsView',KeenoPicksTodayMenuItemsView.as_view(),name='keenoPicksTodayMenuItemsView'),
    
    path('familyMealsMenuItemsView',FamilyMealsMenuItemsView.as_view(),name='familyMealsMenuItemsView'),
    
    path('spotlightListView',SpotlightListView.as_view(),name='spotlightListView'),
    
    path('highRatedNearbyMenuItemsView',HighRatedNearbyMenuItemsView.as_view(),name='highRatedNearbyMenuItemsView'),
    
    path('reorderNearbyMenuItemsView',PreviouslyOrderedOrNearbyMenuItemsView.as_view(),name='reorderNearbyMenuItemsView'),
    
    path('nearbyRestaurantsView',NearbyRestaurantsView.as_view(),name='nearbyRestaurantsView'),
    
    path('addToCartView',AddToCartView.as_view(),name='addToCartView'),
    
    path('viewCartAPI',ViewCartAPI.as_view(),name='viewCartAPI'),
    
    path('menuDetailByUserView',MenuDetailByUserView.as_view(),name='menuDetailByUserView'),
    
    path('updateCartItemQuantityActionView',UpdateCartItemQuantityView.as_view(),name='updateCartItemQuantityActionView'),
    
    path('userOrderDetailsAPI',UserOrderDetailsAPI.as_view(),name='userOrderDetailsAPI'),
    
    path('placeOrderView',PlaceOrderView.as_view(),name='placeOrderView'),
    
    path('userDashboardAPI',UserDashboardAPI.as_view(),name='userDashboardAPI'),
    
    path('helpSupportAPI',HelpSupportAPI.as_view(),name='helpSupportAPI'),
    
    path('toggleWishlistView',ToggleWishlistView.as_view(),name='toggleWishlistView'),
    
    path('simpleCartMenuListView',SimpleCartMenuListView.as_view(),name='simpleCartMenuListView'),
   
    path('addUpdateDeliveryPartnerRating',AddUpdateDeliveryPartnerRating.as_view(),name='addUpdateDeliveryPartnerRating'),
    
    path('addUpdateRestaurantRating',AddUpdateRestaurantRating.as_view(),name='addUpdateRestaurantRating'),
    
    path('deliveryPartnerFormAPI',DeliveryPartnerFormAPI.as_view(),name='deliveryPartnerFormAPI'),
    path('deliveryPartnerLoginAPI',DeliveryPartnerLoginAPI.as_view(),name='deliveryPartnerLoginAPI'),
    path('updateDeliveryPartnerAddressAPI',UpdateDeliveryPartnerAddressAPI.as_view(),name='updateDeliveryPartnerAddressAPI'),
    path('nearbyOrdersForDeliveryPartnerAPI',NearbyOrdersForDeliveryPartnerAPI.as_view(),name='NearbyOrdersForDeliveryPartnerAPI'),
    path('deliveryPartnerOrderActionAPI',DeliveryPartnerOrderActionAPI.as_view(),name='deliveryPartnerOrderActionAPI'),
    path('sendOrderOTPAPI',SendOrderOTPAPI.as_view(),name='sendOrderOTPAPI'),
    path('confirmOrderDeliveredAPI',ConfirmOrderDeliveredAPI.as_view(),name='confirmOrderDeliveredAPI'),
    
    path('deliveryPartnerRatingAPI',DeliveryPartnerRatingAPI.as_view(),name='DeliveryPartnerRatingAPI'),
    
    path('deliveryPartnerDashboardAPI',DeliveryPartnerDashboardAPI.as_view(),name='DeliveryPartnerDashboardAPI'),
    path('deliveryPartnerWeeklyStatsAPI',DeliveryPartnerWeeklyStatsAPI.as_view(),name='deliveryPartnerWeeklyStatsAPI'),
    path('deliveryHistoryAPI',DeliveryHistoryAPI.as_view(),name='deliveryHistoryAPI'),
    
    path('myEarningAPI',MyEarningAPI.as_view(),name='myEarningAPI'),
    
    path('deliveryPartnerProfileAPI',DeliveryPartnerProfileAPI.as_view(),name='deliveryPartnerProfileAPI'),
    
    path('deliveryPartnerPaymentHistoryAPI',DeliveryPartnerPaymentHistoryAPI.as_view(),name='deliveryPartnerPaymentHistoryAPI'),
    
    path('ordersListAcceptedByDeliveryPartnerAPI',OrdersListAcceptedByDeliveryPartnerAPI.as_view(),name='ordersListAcceptedByDeliveryPartnerAPI'),
    path('searchMenuAPI',SearchMenuAPI.as_view(),name='searchMenuAPI'),
    path('getNotificationReadAPI',GetNotificationReadAPI.as_view(),name='getNotificationReadAPI'),
    
    path('addMoneyToWalletView',AddMoneyToWalletView.as_view(),name='addMoneyToWalletView'),
    
    path('walletDetailsView',WalletDetailsView.as_view(),name='walletDetailsView'),
    
    path('restaurantList',RestaurantList.as_view(),name='restaurantList'),
    
    path('restaurantPartyBookingView',RestaurantPartyBookingView.as_view(),name='restaurantPartyBookingView'),
    
   
    
    path('editUserProfileView',EditUserProfileView.as_view(),name='editUserProfileView'),
    
    path('userWishlistView',UserWishlistView.as_view(),name='userWishlistView'),
    
 ]
