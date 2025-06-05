from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser # Or AbstractBaseUser
from django.contrib.gis.db import models as gismodels # Use gismodels for geospatial fields
from django.core.exceptions import ValidationError
from django.utils import timezone # Import timezone for default values
from django.utils.translation import gettext_lazy as _ # Import for validation messages

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
# Using the existing Role model which aligns with task 1.3.5
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
        # Roles from laundry-exam3.txt Role model (if different from above, add here or clarify)
        # ('manager', 'Manager'), # Example if needed
        # ('clerk', 'Clerk'),     # Example if needed
    ]
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()

# Model from laundry-exam3.txt for Departments within an Organization
class Department(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('organization', 'name') # Department names unique per organization

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

# Model from laundry-exam3.txt for System Modules/Permissions
class Module(models.Model):
    name = models.CharField(max_length=100, unique=True) # Modules are likely global, not per organization

    def __str__(self):
        return self.name

# 1.3.1 Implement custom User model (subclassing AbstractUser)
# 1.3.2 Add email/phone login capability (fields added, login logic in authentication)
# 1.3.3 Create Organization relationship for staff users (null for customers)
# 1.3.4 Implement role field or many-to-many relation to Role model
# Incorporating address field from model-exam2.txt Customer model
# Note: The Employee model in laundry-exam3.txt contains many HR-specific fields.
# We will keep the User model focused on authentication and core identity,
# and potentially link it to an Employee profile if detailed HR data is needed separately.
# For now, we'll add some key fields from Employee to User if they are relevant for login/basic profile.
class User(AbstractUser):
    # Remove username field if using email/phone for login
    # username = None # Uncomment if using email/phone as primary identifier

    email = models.EmailField(unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True) # 1.3.2
    # 1.3.3 Link staff users to an Organization
    # Note: This field is for staff users. Customer organization link is in CustomerProfile.
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

    # Add address field from model-exam2.txt Customer - Used for general user address
    address = models.TextField(blank=True, null=True) # e.g. neighborhood/town

    # Add fields from laundry-exam3.txt Employee if needed in User model
    # employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True) # Keep separate in Employee model?
    # profile_image = models.ImageField(upload_to="user_profiles/", blank=True, null=True) # Can add to User
    # gender = models.CharField(max_length=10, choices=[("male", "Male"), ("female", "Female"), ("other", "Other")], blank=True, null=True) # Can add to User
    # date_of_birth = models.DateField(blank=True, null=True) # Can add to User
    # residential_addr = models.TextField(blank=True, null=True) # Already have 'address'

    # USERNAME_FIELD = 'email' # Uncomment if using email for login
    # REQUIRED_FIELDS = [] # Add fields required for createsuperuser if username is removed

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.role or 'No Role'})"
        elif self.email:
            return f"{self.email} ({self.role or 'No Role'})"
        elif self.phone_number:
            return f"{self.phone_number} ({self.role or 'No Role'})"
        else:
            return f"User ID: {self.id} ({self.role or 'No Role'})"

    class Meta:
        # Add constraints or indexes if needed
        pass

# Model from laundry-exam4.txt for detailed Customer information
# This model holds customer-specific data and links to the core User model.
class CustomerProfile(models.Model):
    GENDER_CHOICES = [
        ("male",   "Male"),
        ("female", "Female"),
        ("other",  "Other"),
    ]

    ACCOUNT_STATUS_CHOICES = [
        ("active",    "Active"),
        ("suspended", "Suspended"),
        ("inactive",  "Inactive"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("card",         "Card"),
        ("mobile_money", "Mobile Money"),
        ("cash",         "Physical Cash"),
    ]

    SUBSCRIPTION_STATUS_CHOICES = [
        ("subscribed",    "Subscribed"),
        ("unsubscribed",  "Unsubscribed"),
        ("trial",         "Trial"),
        # …add more as needed
    ]

    COMMUNICATION_CHANNEL_CHOICES = [
        ("in_notification", "In‐Notification"),
        ("email",           "Email"),
        ("sms",             "SMS"),
        ("whatsapp",        "WhatsApp"),
        # …etc.
    ]

    # Link to the core User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile"
    )

    # Link to the Organization the customer belongs to
    organization      = models.ForeignKey(
        Organization, # Link to our main Organization model
        on_delete=models.CASCADE,
        related_name="customers",
        help_text="Which laundry company this customer belongs to."
    )

    customer_id       = models.CharField(
        max_length=20,
        unique=True, # Unique across the system, or per organization? Assuming system-wide for now.
        help_text="Unique Customer Code (e.g. '0001', '0002', etc.)"
    )
    profile_image     = models.ImageField(
        upload_to="customer_profiles/",
        blank=True,
        null=True,
        help_text="Optional profile photo"
    )

    # ─────────── Personal Information (Some overlap with User, but keeping here for customer context) ───────────
    # first_name        = models.CharField(max_length=50) # Available on User
    middle_name       = models.CharField(max_length=50, blank=True, null=True)
    # last_name         = models.CharField(max_length=50) # Available on User
    gender            = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True) # Added blank/null
    date_of_birth     = models.DateField(blank=True, null=True)

    # ─────────── Contact Information (Some overlap with User) ───────────
    # phone_number      = models.CharField(max_length=20, help_text="Primary phone (include country code, eg. +233…)") # Available on User
    whatsapp_number   = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="(Optional) Include country code"
    )
    # email             = models.EmailField(unique=True) # Available on User
    # physical_address  = models.TextField(help_text="Full mailing/delivery address") # Available on User as 'address'
    delivery_address   = models.TextField(
        blank=True,
        null=True,
        help_text="Address where we deliver (often same as physical_address)."
    )


    # ─────────── Account Information ───────────
    # username          = models.CharField(max_length=50, unique=True) # Handled by User model
    # password          = models.CharField(max_length=128, help_text="Default password (you might choose to hash this or link to Django User instead)") # Handled by User model
    account_status    = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default="active",
        help_text="Is the customer active, suspended, etc.?"
    )

    # ─────────── Billing Information ───────────
    payment_method    = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True) # Added blank/null
    # – Card details (only if payment_method == "card")
    card_number       = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="e.g. 'XXXX-XXXX-XXXX-XXXX' (only if payment_method='card')"
    )
    expiry_date       = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="MM/YY (only if payment_method='card')"
    )
    cvc               = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        help_text="CVC (only if payment_method='card')"
    )
    # – Mobile Money details (only if payment_method == "mobile_money")
    mobile_money_network = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="(Only if payment_method='mobile_money') e.g. 'MTN', 'Vodafone', etc."
    )
    mobile_money_number  = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Mobile Money number (if that is the payment method)"
    )
    # – Physical Cash requires no extra fields beyond choosing the method.


    # ─────────── Preferences ───────────
    preferred_pickup_days = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=(
            "Comma‐separated weekdays, e.g. 'Mon,Tue,Fri' to indicate preferred pickup/delivery days."
        )
    )
    days_per_week       = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of pickup/delivery days per week (e.g. 1, 2, 3…)."
    )
    special_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Any special delivery/pickup instructions."
    )

    # ─────────── Subscription / Loyalty ───────────
    subscription_status  = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="Is the customer on a subscription plan, trial, or unsubscribed?"
    )
    loyalty_points       = models.PositiveIntegerField(
        default=0,
        help_text="Total loyalty points accrued"
    )

    # ─────────── Communication Preferences ───────────
    communication_channels = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=(
            "Comma‐separated communication channels the customer prefers. "
            "Possible values: " + ", ".join([c[0] for c in COMMUNICATION_CHANNEL_CHOICES])
        )
    )
    # Store as e.g. "in_notification,email" if they pick those two.

    # ─────────── Comments ───────────
    comments           = models.TextField(blank=True, null=True)

    # ─────────── Audit Fields ───────────
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean() # Call the parent clean method
        # Enforce that card_... fields are only provided when payment_method == "card",
        # and mobile_money_... fields only when payment_method == "mobile_money".
        errors = {}

        if self.payment_method == "card":
            if not (self.card_number and self.expiry_date and self.cvc):
                errors["card_number"] = _("All card fields are required when payment_method is 'card'.")
            # Ensure mobile money fields are null/empty
            if self.mobile_money_network or self.mobile_money_number:
                 errors["mobile_money_network"] = _("Mobile Money fields must be empty for a Card payment method.")

        elif self.payment_method == "mobile_money":
            if not (self.mobile_money_network and self.mobile_money_number):
                errors["mobile_money_network"] = _(
                    "Mobile Money fields are required when payment_method is 'mobile_money'."
                )
            # Ensure card fields are null/empty
            if self.card_number or self.expiry_date or self.cvc:
                 errors["card_number"] = _("Card fields must be empty for a Mobile Money payment method.")

        # If method is 'cash' or 'bank_transfer' or 'online' or 'other', no extra fields are required.
        # Add validation for other payment types if added to choices

        if errors:
            raise ValidationError(errors)

    @property
    def pickup_days_list(self):
        """
        Returns the preferred_pickup_days as a Python list.
        e.g. "Mon,Tue,Fri" -> ["Mon", "Tue", "Fri"].
        """
        if self.preferred_pickup_days:
            return [day.strip() for day in self.preferred_pickup_days.split(",")]
        return []

    @property
    def communication_channel_list(self):
        """
        Returns the communication_channels as a Python list.
        e.g. "in_notification,email" -> ["in_notification", "email"].
        """
        if self.communication_channels:
            return [ch.strip() for ch in self.communication_channels.split(",")]
        return []


    def __str__(self):
        # Use user's name if available, otherwise fallback to customer_id
        user_name = self.user.get_full_name() or self.user.email or self.user.phone_number
        return f"{user_name} (Customer ID: {self.customer_id})"


# Model from laundry-exam3.txt for detailed Employee information
# This model holds HR-specific data and links to the core User model.
class Employee(models.Model):
    GENDER_CHOICES = [
        ("male",   "Male"),
        ("female", "Female"),
        ("other",  "Other"),
    ]

    # 1.1.3 Add Organization foreign key
    organization   = models.ForeignKey(
        Organization, # Link to our main Organization model
        on_delete=models.CASCADE,
        related_name="employees"
    )

    # Link to the core User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile"
    )

    # Identification
    employee_id    = models.CharField(max_length=20, unique=True) # Unique across the system, or per organization? Let's assume system-wide for now.
    profile_image  = models.ImageField(upload_to="employee_profiles/", blank=True, null=True)

    # Personal Information (Some might overlap with User, decide which model is source of truth)
    # first_name     = models.CharField(max_length=50) # Already in User
    # middle_name    = models.CharField(max_length=50, blank=True, null=True)
    # last_name      = models.CharField(max_length=50) # Already in User
    # personal_phone = models.CharField(max_length=20, help_text="Include country code, eg. +233245224993") # Could use User phone_number
    date_of_birth  = models.DateField(blank=True, null=True)
    gender         = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True) # Added blank/null

    # Contact Information (Some might overlap with User)
    contact_phone    = models.CharField(max_length=20, blank=True, null=True, help_text="Alternate phone number") # Added blank/null
    whatsapp_number  = models.CharField(max_length=20, blank=True, null=True, help_text="(Optional)")
    # email            = models.EmailField(unique=True) # Already in User
    residential_addr = models.TextField(blank=True, null=True, help_text="Full mailing/residential address") # Added blank/null, could use User address

    # Employment Information
    job_title         = models.CharField(max_length=100, blank=True, null=True) # Added blank/null
    department        = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True)
    employment_status = models.CharField(max_length=50, blank=True, null=True, help_text="E.g. 'Full‐Time', 'Contractor', etc.") # Added blank/null
    supervisor        = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subordinates"
    )
    hire_date         = models.DateField(blank=True, null=True)

    # Attendance & Schedule
    start_shift   = models.TimeField(blank=True, null=True)
    break_time    = models.TimeField(blank=True, null=True)
    end_shift     = models.TimeField(blank=True, null=True)
    work_days     = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Comma‐separated days, e.g. 'Mon,Tue,Thu,Fri'"
    )
    days_per_week = models.PositiveSmallIntegerField(default=5)

    # Leave & Time Off
    vacation_days        = models.PositiveSmallIntegerField(default=0)
    sick_leave_days      = models.PositiveSmallIntegerField(default=0)
    compassionate_days   = models.PositiveSmallIntegerField(default=0)
    maternity_leave_days = models.PositiveSmallIntegerField(default=0)

    # Qualifications
    qualification_name = models.CharField(max_length=100, blank=True, null=True)
    year_attained      = models.DateField(blank=True, null=True)

    # HR Notes
    hr_notes = models.TextField(blank=True, null=True)

    # Module Permissions & Role - Role is already on User model. Modules could be M2M here or on User.
    # Let's keep Modules M2M on Employee profile for HR/permission management context.
    modules = models.ManyToManyField(Module, blank=True, related_name="employees")
    # role    = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True) # Role is on User model

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Ensure end_shift > start_shift if both are set
        if self.start_shift and self.end_shift:
            # Convert time objects to datetime objects for comparison, using a dummy date
            dummy_date = timezone.now().date()
            start_dt = timezone.datetime.combine(dummy_date, self.start_shift)
            end_dt = timezone.datetime.combine(dummy_date, self.end_shift)

            if end_dt <= start_dt:
                raise ValidationError(_("End shift must be after start shift."))

    @property
    def total_hours_per_day(self):
        """
        Calculates total work hours per day based on start, end, and break duration.
        """
        if self.start_shift and self.end_shift:
            # Convert time objects to minutes from midnight
            start_minutes = self.start_shift.hour * 60 + self.start_shift.minute
            end_minutes   = self.end_shift.hour * 60 + self.end_shift.minute

            # Handle shifts crossing midnight
            if end_minutes <= start_minutes:
                total_shift_minutes = (24 * 60 - start_minutes) + end_minutes
            else:
                total_shift_minutes = end_minutes - start_minutes

            break_minutes = self.break_duration_minutes if self.break_duration_minutes is not None else 0

            work_duration_minutes = total_shift_minutes - break_minutes

            if work_duration_minutes < 0:
                work_duration_minutes = 0 # Should not be negative

            hours = work_duration_minutes // 60
            mins  = work_duration_minutes % 60
            return f"{hours}h {mins}m"

        return None # Return None if shifts are not fully defined

# Add break_duration_minutes field to Employee model
Employee.add_to_class('break_duration_minutes', models.PositiveSmallIntegerField(default=30, help_text="Break duration in minutes", blank=True, null=True)) # Added blank/null

# Update total_hours_per_day property to use break_duration_minutes
# Replace the old property with the new one
del Employee.total_hours_per_day
@property
def total_hours_per_day(self):
    """
    Calculates total work hours per day based on start, end, and break duration.
    """
    if self.start_shift and self.end_shift:
        # Convert time objects to minutes from midnight
        start_minutes = self.start_shift.hour * 60 + self.start_shift.minute
        end_minutes   = self.end_shift.hour * 60 + self.end_shift.minute

        # Handle shifts crossing midnight
        if end_minutes <= start_minutes:
            total_shift_minutes = (24 * 60 - start_minutes) + end_minutes
        else:
            total_shift_minutes = end_minutes - start_minutes

        break_minutes = self.break_duration_minutes if self.break_duration_minutes is not None else 0

        work_duration_minutes = total_shift_minutes - break_minutes

        if work_duration_minutes < 0:
            work_duration_minutes = 0 # Should not be negative

        hours = work_duration_minutes // 60
        mins  = work_duration_minutes % 60
        return f"{hours}h {mins}m"

    return None # Return None if shifts are not fully defined
Employee.add_to_class('total_hours_per_day', total_hours_per_day)


# Model from laundry-exam3.txt for Emergency Contacts
class EmergencyContact(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='emergency_contacts')
    employee        = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="emergency_contacts")
    first_name      = models.CharField(max_length=50)
    middle_name     = models.CharField(max_length=50, blank=True, null=True)
    last_name       = models.CharField(max_length=50)
    phone_number    = models.CharField(max_length=20, help_text="Include country code")
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    gender          = models.CharField(max_length=10, choices=Employee.GENDER_CHOICES, blank=True, null=True) # Added blank/null
    residential_addr= models.TextField(blank=True, null=True, help_text="Address of this emergency contact") # Added blank/null

    def __str__(self):
        return f"{self.first_name} {self.last_name} – Emergency contact for {self.employee.user.get_full_name() or self.employee.employee_id}"


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

# 4) FULL ITEM DESCRIPTION / CARE DETAILS (OPTIONAL) from model-exam2.txt
class ItemDetail(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='item_details') # 1.1.3

    # Basic Identification
    item_type    = models.CharField(max_length=50, blank=True, null=True)
    material     = models.CharField(max_length=50, blank=True, null=True)
    color        = models.CharField(max_length=30, blank=True, null=True)
    size         = models.CharField(max_length=20, blank=True, null=True)
    quantity     = models.PositiveIntegerField(default=1)
    tag_number   = models.CharField(max_length=30, blank=True, null=True)

    # Condition & Care
    condition    = models.CharField(max_length=30, blank=True, null=True)
    age          = models.CharField(max_length=30, blank=True, null=True, help_text="Approximate age (e.g. '1 year')")
    embellishments = models.CharField(max_length=100, blank=True, null=True)
    care_label_instructions = models.TextField(blank=True, null=True)
    special_handling = models.TextField(blank=True, null=True)

    # Details
    weight       = models.CharField(max_length=30, blank=True, null=True, help_text="e.g. '1.2 kg'")
    pattern_design = models.CharField(max_length=50, blank=True, null=True)
    dimensions     = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. '50×30 cm'")
    category       = models.CharField(max_length=50, blank=True, null=True)

    # Image (upload to media/…)
    image = models.ImageField(
        upload_to='item_images/',
        blank=True,
        null=True,
        help_text="Optional: photo of item (max 5 MB)"
    )

    def __str__(self):
        parts = [self.item_type or '', self.color or '', self.size or '']
        return " ".join([p for p in parts if p])


# 1.5.1 Create Order model (Based on LaundryBag from model-exam2.txt and existing Order)
class Order(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='orders')
    # 1.5.1 Fields: customer, outlet, order_status, timestamps, payment_status
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='customer_orders', null=True, blank=True) # Link to the User model
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, related_name='outlet_orders', null=True, blank=True) # Outlet where order was dropped off/picked up

    # Fields from model-exam2.txt LaundryBag
    COLLECTION_METHOD_CHOICES = [
        ('customer_dropoff', 'Customer Drop-off'),
        ('company_pickup',   'Laundry Company Pick-Up'),
    ]
    collection_method = models.CharField(
        max_length=20,
        choices=COLLECTION_METHOD_CHOICES,
        default='customer_dropoff'
    )
    pickup_location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="If company pick-up, store pickup address/branch/etc."
    )

    DELIVERY_METHOD_CHOICES = [
        ('pick_up',  'Pick Up'),
        ('delivery', 'Delivery'),
    ]
    delivery_method   = models.CharField(
        max_length=10,
        choices=DELIVERY_METHOD_CHOICES,
        default='pick_up'
    )
    delivery_location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Address where laundry should be delivered"
    )

    # Auto-generated invoice/bag numbers (unique per organization)
    bag_number     = models.CharField(max_length=20) # Unique per organization
    invoice_number = models.CharField(max_length=20) # Unique per organization

    # Service Type (standard, express, etc.) – can also be a FK to a ServiceType model
    # Keeping the link via LaundryItem for flexibility, but a general service type could be here too
    # service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True) # Optional: if an order has one primary service type

    # Duration (in days) and expected delivery date
    duration_days  = models.PositiveIntegerField(default=0)
    delivery_date  = models.DateField(blank=True, null=True)

    # Status fields (from existing Order model)
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

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Totals and payment info
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Default to 0.00 as per model-exam2.txt
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Default to 0.00
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # From model-exam2.txt

    # Special instructions
    special_instructions = models.TextField(blank=True, null=True) # From model-exam2.txt

    @property
    def amount_outstanding(self):
        return self.total_amount - self.amount_paid

    def __str__(self):
        return f"Order #{self.id} ({self.bag_number}) for {self.organization.name} - Status: {self.get_order_status_display()}"

    class Meta:
        # Ensure bag_number and invoice_number are unique per organization
        unique_together = (('organization', 'bag_number'), ('organization', 'invoice_number'))


# 1.5.2 Create LaundryItem model (Based on model-exam2.txt LaundryItem and existing LaundryItem)
# 1.5.3 Link LaundryItem to Order and Organization
# 1.5.4 Implement item status tracking
class LaundryItem(models.Model):
    # 1.1.3 Add Organization foreign key
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='laundry_items')
    # 1.5.3 Link to Order (renamed from 'bag' in model-exam2.txt)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    # Fields from model-exam2.txt LaundryItem
    # Using description for item name, category could be added if needed
    description = models.CharField(max_length=255) # e.g., "Blue shirt", "King size duvet"
    # category = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 'Ladies', 'Gents'") # Optional category field

    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Increased max_digits slightly
    quantity = models.PositiveIntegerField(default=1) # Default to 1

    # Computed: unit_price * quantity, but stored for easy queries (as per model-exam2.txt)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Increased max_digits slightly

    # Preferences: Wash / Dry / Iron (booleans) - Replaced by ManyToMany to ServiceType for flexibility
    # wash = models.BooleanField(default=True)
    # dry  = models.BooleanField(default=False)
    # iron = models.BooleanField(default=False)

    # 1.5.2 Fields: service_types, turnaround_time, current_stage (from existing)
    # Many-to-many relationship for multiple service types per item
    service_types = models.ManyToManyField(ServiceType, related_name='items')
    turnaround_time = models.ForeignKey(TurnaroundTime, on_delete=models.SET_NULL, null=True, blank=True)

    # 1.5.4 & 1.5.5 Implement item status tracking through stages (from existing)
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

    # Optional: fields for weight, notes (from existing)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    # Optionally link to the detailed item description (from model-exam2.txt)
    detail = models.OneToOneField(
        'ItemDetail',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='laundry_item', # Added related_name
        help_text="Complete item description/care info"
    )

    def save(self, *args, **kwargs):
        # Auto-compute `amount` before saving
        self.amount = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        # Consider adding logic here or in a signal to update Order total_amount

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
        source_desc = self.source_outlet.abbreviated_name if self.source_outlet else ('Factory' if self.is_from_factory else 'Unknown Source')
        dest_desc = self.destination_outlet.abbreviated_name if self.destination_outlet else ('Factory' if self.is_to_factory else 'Unknown Destination')
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
        ('factory_intake', 'Factory Intake'), # Initial handover from Dispatch to Factory
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