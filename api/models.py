from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser # Or AbstractBaseUser
from django.contrib.gis.db import models as gismodels # Use gismodels for geospatial fields
from django.core.exceptions import ValidationError

# 1.1.1 Create Organization (Tenant) model
# Incorporating fields from model-exam.txt LaundryOrganization and task document
class Organization(models.Model):
    name = models.CharField(max_length=255)
    contact_info = models.TextField(blank=True, null=True)
    # subscription_tier removed as it will be derived from the Subscription model
    billing_status = models.CharField(max_length=50, default='active') # e.g., 'active', 'trial', 'past_due'
    unique_identifier = models.CharField(max_length=100, unique=True) # e.g., subdomain or slug
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# 1.8.1 Create Subscription model for organization plan management
# 1.8.2 Add fields: plan_type, billing_cycle, price, active_status, start/end_dates
# 1.8.3 Link Subscription to Organization model
class Subscription(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='subscriptions')
    plan_type = models.CharField(max_length=100) # e.g., 'Basic', 'Premium', 'Enterprise'
    billing_cycle = models.CharField(max_length=50) # e.g., 'monthly', 'annually'
    price = models.DecimalField(max_digits=10, decimal_places=2)
    active_status = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organization.name} - {self.plan_type} ({'Active' if self.active_status else 'Inactive'})"

# 1.4.1 Create Role model with role name constants
class Role(models.Model):
    # 1.3.5 Define user roles
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('org_admin', 'Organization Admin'),
        ('attendant', 'Attendant'),
        ('dispatcher', 'Dispatcher'),
        ('washer', 'Washer'),
        ('dryer', 'Dryer'),
        ('ironer', 'Ironer'),
        ('qc_packager', 'QC Packager'),
        ('customer', 'Customer'),
    ]
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()

# 1.3.1 Implement custom User model (subclassing AbstractUser)
# 1.3.2 Add email/phone login capability (fields added, login logic in authentication)
# 1.3.3 Create Organization relationship for staff users (null for customers)
# 1.3.4 Implement role field or many-to-many relation to Role model
class User(AbstractUser):
    # Remove username field if using email/phone for login
    # username = None # Uncomment if using email/phone as primary identifier

    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True) # 1.3.2
    # 1.3.3 Link staff users to an Organization
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='staff_users',
        null=True, # Null for customers and super_admin
        blank=True
    )
    # 1.3.4 Link user to a Role
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL, # Or models.PROTECT depending on desired behavior
        null=True,
        blank=True
    )

    # Add fields from OrganizationOfficial if needed, or rely on User model fields
    # first_name and last_name are already in AbstractUser
    # title = models.CharField(max_length=100, blank=True, null=True) # Optional, if different from role
    # id_document = models.FileField(upload_to="organization_official_ids/", blank=True, null=True) # Optional

    # USERNAME_FIELD = 'email' # Uncomment if using email for login
    # REQUIRED_FIELDS = [] # Add fields required for createsuperuser if username is removed

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.role})"
        elif self.email:
            return f"{self.email} ({self.role})"
        elif self.phone_number:
            return f"{self.phone_number} ({self.role})"
        else:
            return f"User ID: {self.id} ({self.role})"

    class Meta:
        # Add constraints or indexes if needed
        pass

# 1.2.3 Create Outlet model with address fields and GeoDjango PointField
# 1.2.5 Link Outlet model to Organization via foreign key
# Incorporating fields from model-exam.txt Outlet
class Outlet(gismodels.Model): # Use gismodels for geospatial fields
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='outlets') # 1.1.3
    full_name = models.CharField(max_length=100, help_text="E.g. Pokosiai Laundry")
    abbreviated_name = models.CharField(max_length=20, help_text="E.g. PK")
    phone_number = models.CharField(max_length=20, help_text="Include country code")
    whatsapp_number = models.CharField(max_length=20, help_text="Include country code")
    physical_address = models.CharField(max_length=200)
    # 1.2.3 GeoDjango PointField for GPS coordinates
    # 1.2.4 Add geospatial index on location field (handled by GeoDjango)
    location = gismodels.PointField(srid=4326) # Use SRID 4326 for WGS84 (GPS coordinates)

    def __str__(self):
        return f"{self.abbreviated_name} – {self.full_name}"

# Model from model-exam.txt for Organization Registration Documents
class RegistrationDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ("sole_proprietor", "Sole Proprietor"),
        ("partnership",      "Partnership"),
        ("llc",              "Limited Liability Company"),
        ("unregistered",     "Unregistered"),
    ]

    DOCUMENT_NAME_CHOICES = [
        ("cert_registration",     "Certification of Registration"),
        ("form_a",                "Form A"),
        ("cert_incorporation",    "Certification of Incorporation"),
        ("form_3b",               "Form 3B"),
        ("partnership_deed",      "Partnership Deed (Optional)"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="registration_documents") # 1.1.3
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    document_name = models.CharField(max_length=30, choices=DOCUMENT_NAME_CHOICES)
    file = models.FileField(upload_to="registration_docs/", help_text="Max file size: 5 MB.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization.name} - {self.get_doc_type_display()} – {self.get_document_name_display()}"

# Model from model-exam.txt for Organization Payment Details
# 1.7.4 Design Payment/Invoice model (This is for the org receiving payment, not customer paying)
class PaymentDetail(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ("bank",        "Bank Account"),
        ("mobile_money","Mobile Money"),
    ]

    BANK_CHOICES = [
        ("calbank",     "CalBank"),
        ("gt_bank",     "GTBank"),
        ("stanbic",     "Stanbic"),
        # Add other banks
    ]

    MM_NETWORK_CHOICES = [
        ("mtn",       "MTN"),
        ("vodafone",  "Vodafone"),
        ("airtel_tigo","AirtelTigo"),
        # Add other networks
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="payment_details") # 1.1.3
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)

    bank_name = models.CharField(max_length=30, choices=BANK_CHOICES, blank=True, null=True, help_text="Select Bank (if payment_type is 'bank')")
    account_number = models.CharField(max_length=30, blank=True, null=True, help_text="Enter bank account number")
    branch = models.CharField(max_length=50, blank=True, null=True, help_text="Bank branch name")

    mobile_network = models.CharField(max_length=20, choices=MM_NETWORK_CHOICES, blank=True, null=True, help_text="Select Mobile Money network")
    merchant_number = models.CharField(max_length=30, blank=True, null=True, help_text="Mobile Money merchant number")
    merchant_id = models.CharField(max_length=50, blank=True, null=True, help_text="Mobile Money merchant ID")

    def clean(self):
        super().clean() # Call the parent clean method
        if self.payment_type == "bank":
            if not self.bank_name or not self.account_number or not self.branch:
                raise ValidationError("All bank account fields are required for a Bank payment mode.")
            # Ensure mobile money fields are null/empty
            if self.mobile_network or self.merchant_number or self.merchant_id:
                 raise ValidationError("Mobile Money fields must be empty for a Bank payment mode.")
        elif self.payment_type == "mobile_money":
            if not self.mobile_network or not self.merchant_number or not self.merchant_id:
                raise ValidationError("All Mobile Money fields are required for a Mobile Money payment mode.")
            # Ensure bank fields are null/empty
            if self.bank_name or self.account_number or self.branch:
                 raise ValidationError("Bank account fields must be empty for a Mobile Money payment mode.")
        # Add validation for other payment types if added

    def __str__(self):
        if self.payment_type == "bank":
            return f"Bank: {self.get_bank_name_display()} (account {self.account_number})"
        elif self.payment_type == "mobile_money":
            return f"Mobile Money: {self.get_mobile_network_display()} (Merchant {self.merchant_number})"
        else:
            return f"Payment Detail ID: {self.id}"

# Model from model-exam.txt for Organization Social Media
class SocialMedia(models.Model):
    PLATFORM_CHOICES = [
        ("facebook",  "Facebook"),
        ("instagram", "Instagram"),
        ("twitter",   "Twitter"),
        ("linkedin",  "LinkedIn"),
        ("tiktok",    "TikTok"),
        # Add others
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="social_media_accounts") # 1.1.3
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    account_handle = models.CharField(max_length=100, help_text="E.g. SunnyLaundry@1234")
    link = models.URLField(help_text="Full URL to the social page")

    class Meta:
        unique_together = ('organization', 'platform') # Ensure only one account per platform per organization

    def __str__(self):
        return f"{self.organization.name} - {self.get_platform_display()}: {self.account_handle}"

# --- Placeholder Models (To be expanded based on task document) ---

# 1.6.1 Create ServiceType model/choices
# 1.6.2 Define service types
class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True) # e.g., 'Washing only', 'Full Service'
    description = models.TextField(blank=True, null=True)
    # Add fields for pricing if pricing is service-based (per service type)
    # price_per_kg = models.DecimalField(...)
    # price_per_item = models.DecimalField(...)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='service_types', null=True, blank=True) # 1.1.3 - Can be global or org-specific

    def __str__(self):
        return self.name

# 1.6.3 Implement TAT (Turnaround Time) field/model
class TurnaroundTime(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g., 'Normal', 'Express'
    hours = models.IntegerField() # e.g., 24 for normal, 6 for express
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='turnaround_times', null=True, blank=True) # 1.1.3 - Can be global or org-specific

    def __str__(self):
        return f"{self.name} ({self.hours} hours)"

# 1.5.1 Create Order model
class Order(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='orders')
    # 1.5.1 Fields: customer, outlet, order_status, timestamps, payment_status
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='customer_orders', null=True, blank=True) # Link to the User model
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, related_name='outlet_orders', null=True, blank=True) # Outlet where order was dropped off/picked up

    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending Intake'), # Customer initiated online, awaiting drop-off
        ('received', 'Received at Outlet'), # Attendant created
        ('awaiting_pickup', 'Awaiting Dispatch Pickup'), # Ready to go to factory
        ('in_transit_to_factory', 'In Transit (to Factory)'),
        ('received_at_factory', 'Received at Factory'),
        ('in_processing', 'In Processing'), # Washing, Drying, Ironing stages
        ('qc_packaging', 'QC & Packaging'),
        ('awaiting_return_dispatch', 'Awaiting Return Dispatch'), # Ready to go back to outlet
        ('in_transit_to_outlet', 'In Transit (to Outlet)'),
        ('received_at_outlet', 'Received back at Outlet'), # Ready for customer pickup
        ('ready_for_pickup', 'Ready for Customer Pickup'),
        ('completed', 'Completed'), # Picked up by customer
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'), # e.g., due to defect
    ]
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default='received')

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Add fields for total amount, discount, etc.
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order #{self.id} for {self.organization.name} - Status: {self.get_order_status_display()}"

# 1.5.2 Create LaundryItem model
# 1.5.3 Link LaundryItem to Order and Organization
# 1.5.4 Implement item status tracking
class LaundryItem(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='laundry_items')
    # 1.5.3 Link to Order
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    # 1.5.2 Fields: description, service_types, turnaround_time, current_stage
    description = models.CharField(max_length=255) # e.g., "Blue shirt", "King size duvet"
    # Many-to-many relationship for multiple service types per item
    service_types = models.ManyToManyField(ServiceType, related_name='items')
    turnaround_time = models.ForeignKey(TurnaroundTime, on_delete=models.SET_NULL, null=True, blank=True)

    # 1.5.4 & 1.5.5 Implement item status tracking through stages
    ITEM_STATUS_CHOICES = [
        ('received', 'Received'), # Part of an order received at outlet/factory
        ('awaiting_wash', 'Awaiting Washing'),
        ('in_washing', 'In Washing'),
        ('washing_complete', 'Washing Complete'),
        ('awaiting_dry', 'Awaiting Drying'),
        ('in_drying', 'In Drying'),
        ('drying_complete', 'Drying Complete'),
        ('awaiting_iron', 'Awaiting Ironing'),
        ('in_ironing', 'In Ironing'),
        ('ironing_complete', 'Ironing Complete'),
        ('awaiting_qc', 'Awaiting QC'),
        ('in_qc', 'In QC'),
        ('qc_passed', 'QC Passed'),
        ('qc_failed', 'QC Failed'), # Needs re-processing or defect noted
        ('awaiting_package', 'Awaiting Packaging'),
        ('packaged', 'Packaged'),
        ('awaiting_dispatch_return', 'Awaiting Dispatch Return'), # Ready to go back to outlet
        ('in_transit_to_outlet', 'In Transit (to Outlet)'),
        ('received_at_outlet', 'Received back at Outlet'),
        ('ready_for_pickup', 'Ready for Pickup'), # Part of an order ready for customer
        ('picked_up', 'Picked Up'), # Part of a completed order
        ('returned_to_wash', 'Returned to Washing (Defect)'),
        ('returned_to_dry', 'Returned to Drying (Defect)'),
        ('returned_to_iron', 'Returned to Ironing (Defect)'),
        ('damaged', 'Damaged'), # Irreparable defect
    ]
    current_stage = models.CharField(max_length=50, choices=ITEM_STATUS_CHOICES, default='received')

    # Optional: fields for weight, quantity (if items are counted), notes
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True) # e.g., number of shirts
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Item #{self.id} ({self.description}) - Status: {self.get_current_stage_display()}"

# 1.7.1 Create Dispatch Request model
class DispatchRequest(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='dispatch_requests')

    # Source and destination can be Outlet or Factory (need a way to distinguish or use generic relations)
    # For simplicity, let's assume Source/Destination are Outlets or a conceptual 'Factory' location
    # A more robust approach might use GenericForeignKeys or separate fields for Outlet/Factory
    # Let's use ForeignKey to Outlet for now, assuming Factory is represented elsewhere or implicitly
    # Or, use two ForeignKey fields and check which one is populated
    source_outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, related_name='dispatches_sent', null=True, blank=True)
    destination_outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, related_name='dispatches_received', null=True, blank=True)
    # Need to represent Factory as source/destination - could use a boolean flag or a separate model
    is_to_factory = models.BooleanField(default=False) # True if destination is factory
    is_from_factory = models.BooleanField(default=False) # True if source is factory

    # Items/Orders included in this dispatch
    # Could link directly to Items or Orders, or use a ManyToMany field
    # Linking to items allows tracking specific items in a dispatch
    items = models.ManyToManyField(LaundryItem, related_name='dispatches')

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='dispatches_requested', null=True, blank=True)
    assigned_dispatcher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='dispatches_assigned', null=True, blank=True) # User with 'dispatcher' role

    STATUS_CHOICES = [
        ('pending', 'Pending Pickup'),
        ('accepted', 'Accepted by Dispatcher'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        source_desc = self.source_outlet.abbreviated_name if self.source_outlet else 'Factory'
        dest_desc = self.destination_outlet.abbreviated_name if self.destination_outlet else 'Factory'
        return f"Dispatch #{self.id} ({source_desc} to {dest_desc}) - Status: {self.get_status_display()}"

# 1.7.2 Implement Handover/Transfer model for team-to-team item transfers
# This could be implicitly handled by Item status changes and timestamps,
# or explicitly logged with a model:
class ItemHandover(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='item_handovers')
    item = models.ForeignKey(LaundryItem, on_delete=models.CASCADE, related_name='handovers')

    # Define stages for handover
    STAGE_CHOICES = [
        ('washing', 'Washing'),
        ('drying', 'Drying'),
        ('ironing', 'Ironing'),
        ('qc', 'QC'),
        ('packaging', 'Packaging'),
        ('outlet_return', 'Return to Outlet'), # Factory to Outlet handover
    ]
    from_stage = models.CharField(max_length=50, choices=STAGE_CHOICES, null=True, blank=True) # Null for initial factory receipt
    to_stage = models.CharField(max_length=50, choices=STAGE_CHOICES)

    handed_over_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='handovers_given', null=True, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='handovers_received', null=True, blank=True)

    handed_over_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Handover for Item {self.item.id}: {self.from_stage or 'Dispatch'} -> {self.to_stage}"

# 1.7.3 Create Defect Report model
class DefectReport(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='defect_reports')
    item = models.ForeignKey(LaundryItem, on_delete=models.CASCADE, related_name='defect_reports')

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='defects_reported', null=True, blank=True)

    DEFECT_TYPE_CHOICES = [
        ('stain_not_removed', 'Stain Not Removed'),
        ('damage', 'Damage'), # Tear, hole, etc.
        ('missing_button', 'Missing Button'),
        ('color_bleed', 'Color Bleed'),
        ('shrinkage', 'Shrinkage'),
        ('other', 'Other'),
    ]
    defect_type = models.CharField(max_length=50, choices=DEFECT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)

    stage_found = models.CharField(max_length=50, choices=ItemHandover.STAGE_CHOICES) # Stage where defect was found

    resolved_flag = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='defects_resolved', null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Defect on Item {self.item.id}: {self.get_defect_type_display()} (Found at {self.get_stage_found_display()})"

# 1.7.4 Design Payment/Invoice model (This is for customer payments for orders)
class OrderPayment(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='order_payments')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment Gateway'),
        ('other', 'Other'),
    ]
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True) # Transaction ID from payment gateway/system
    payment_date = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='payments_received', null=True, blank=True) # Staff member who recorded payment

    def __str__(self):
        return f"Payment of {self.amount} for Order #{self.order.id} via {self.get_payment_method_display()}"

# Note: Remember to configure settings.AUTH_USER_MODEL = 'api.User' in settings.py
# And run makemigrations and migrate after adding/modifying models.

