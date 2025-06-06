from django.contrib import admin
from .models import (
    Organization, Subscription, Role, Department, Module,
    CustomerProfile, Employee, EmergencyContact, RegistrationDocument,
    PaymentDetail, SocialMedia, Outlet, ServiceType, TurnaroundTime,
    ItemDetail, LaundryItem, Order,
    DispatchRequest, ItemHandover,
    DefectReport, OrderPayment
)
# Remove the import for User from accounts.models here, as it's registered in accounts/admin.py
# from accounts.models import User
from django.contrib.gis.admin import OSMGeoAdmin

# Register models from api.models
# Remove the registration for User here, it should be registered in accounts/admin.py
# admin.site.register(User)

# Change admin.register(Model) to admin.site.register(Model) for basic registration
admin.site.register(Organization)
admin.site.register(Subscription)
admin.site.register(Role)
admin.site.register(Department)
admin.site.register(Module)
admin.site.register(CustomerProfile)
admin.site.register(Employee)
admin.site.register(EmergencyContact)
admin.site.register(RegistrationDocument)
admin.site.register(PaymentDetail)
admin.site.register(SocialMedia)

# Use OSMGeoAdmin for the Outlet model
@admin.register(Outlet)
class OutletAdmin(OSMGeoAdmin):
    list_display = ('full_name', 'abbreviated_name', 'organization', 'location')
    search_fields = ('full_name', 'abbreviated_name', 'organization__name')

admin.site.register(ServiceType)
admin.site.register(TurnaroundTime)
admin.site.register(ItemDetail)
admin.site.register(LaundryItem)
admin.site.register(Order)
admin.site.register(DispatchRequest)
admin.site.register(ItemHandover)
admin.site.register(DefectReport)
admin.site.register(OrderPayment)

# Remove commented out registrations for models not in api.models
# Remove OrderItemAdmin registration as the model is not defined in api.models
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'service_type', 'quantity', 'price')
#     list_filter = ('service_type',)
#     search_fields = ('order__order_number',)

# Remove OrderServiceAdmin registration as the model is not defined in api.models
# @admin.register(OrderService)
# class OrderServiceAdmin(admin.ModelAdmin):
#     list_display = ('order_item', 'service_type', 'price')
#     list_filter = ('service_type',)

# @admin.register(OrderStatus)
# class OrderStatusAdmin(admin.ModelAdmin):
#     list_display = ('order', 'status', 'timestamp')
#     list_filter = ('status',)
#     search_fields = ('order__order_number',)

# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('order', 'payment_method', 'amount', 'status', 'timestamp')
#     list_filter = ('payment_method', 'status')
#     search_fields = ('order__order_number', 'transaction_id')

# @admin.register(PickupLocation)
# class PickupLocationAdmin(OSMGeoAdmin):
#     list_display = ('order', 'address', 'location')
#     search_fields = ('order__order_number', 'address')

# @admin.register(DeliveryLocation)
# class DeliveryLocationAdmin(OSMGeoAdmin):
#     list_display = ('order', 'address', 'location')
#     search_fields = ('order__order_number', 'address')

# Remove commented out registrations for models not in api.models
# @admin.register(Brand)
# class BrandAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ('name',)

# Add other models as they are created and defined in models.py
# admin.site.register(Size)
# admin.site.register(ProductSize)
# admin.site.register(ProductImage)
# admin.site.register(Vehicle)
# admin.site.register(Driver) # Driver might be linked to Employee/User
# admin.site.register(Notification)
# admin.site.register(Feedback)
# admin.site.register(Report)
# admin.site.register(Coupon)
# admin.site.register(Discount)
# admin.site.register(Tax)
# admin.site.register(Setting)