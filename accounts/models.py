from django.db import models
# Change import to AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings # Import settings to reference AUTH_USER_MODEL

# Assuming Organization and Role models are in the 'api' app
# You might need to import them directly if not using string references
# from api.models import Organization, Role


class UserManager(BaseUserManager):
    # Modify create_user to match AbstractUser's expected fields
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # Modify create_superuser to set is_staff and is_superuser
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Superuser should be active

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


# Change base class to AbstractUser
class User(AbstractUser):
    # AbstractUser already provides:
    # username, first_name, last_name, email, is_staff, is_active,
    # date_joined, last_login, groups, user_permissions

    # Keep custom email field if you need specific attributes like unique=True
    # AbstractUser already has an email field, but we can redefine it for unique=True
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)

    # Keep custom username field if you need specific attributes like unique=True and default
    # AbstractUser already has a username field
    username = models.CharField(max_length=150, unique=True, default="JohnDoe123") # Increased max_length for compatibility

    # Keep custom first_name and last_name if you need defaults
    # AbstractUser already has these fields
    first_name = models.CharField(max_length=150, blank=True, default='John') # AbstractUser default is blank=True
    last_name = models.CharField(max_length=150, blank=True, default='Doe') # AbstractUser default is blank=True


    # Remove is_active and is_admin as AbstractUser provides is_active and is_superuser/is_staff
    # is_active = models.BooleanField(default=True)
    # is_admin = models.BooleanField(default=False) # Use is_superuser/is_staff instead

    # Add fields from the api.User model
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True) # From api.User

    # Link staff users to an Organization (From api.User)
    # Note: This field is for staff users. Customer organization link is in CustomerProfile.
    organization = models.ForeignKey(
        'api.Organization', # Reference the model using a string 'app_label.ModelName'
        on_delete=models.CASCADE,
        related_name='staff_users',
        null=True, # Null for customers and super_admin
        blank=True
    )

    # Link user to a Role (From api.User)
    role = models.ForeignKey(
        'api.Role', # Reference the model using a string 'app_label.ModelName'
        on_delete=models.SET_NULL, # Or models.PROTECT depending on desired behavior
        null=True,
        blank=True
    )

    # Add address field (From api.User)
    address = models.TextField(blank=True, null=True) # e.g. neighborhood/town


    objects = UserManager()

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS should list fields prompted for by createsuperuser *in addition* to USERNAME_FIELD and password
    # Since username, first_name, last_name are now standard fields on AbstractUser,
    # and we want them required for superuser creation, keep them here.
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    # Remove explicit groups and user_permissions fields as AbstractUser provides them.
    # The related_name clashes will be resolved because there's only one User model.
    # groups = models.ManyToManyField(...)
    # user_permissions = models.ManyToManyField(...)

    # Remove custom properties/methods that overlap with AbstractUser
    # @property
    # def is_superuser(self):
    #     return self.is_admin
    #
    # @is_superuser.setter
    # def is_superuser(self, value):
    #     self.is_admin = value
    #
    # @property
    # def is_staff(self):
    #     return self.is_admin

    # Review and potentially remove or modify has_perm if AbstractUser's default is sufficient
    # def has_perm(self, perm, obj=None):
    #     # print(f"User Permissions: {self.get_all_permissions()}")
    #     # Check if the user has the required permission to view a custom user
    #     required_permission = "accounts.view_user" # This permission might need to be defined
    #     return self.is_active or self.user_permissions.filter(codename=required_permission).exists()
    # AbstractUser's has_perm checks superuser, active status, group, and user permissions.
    # The default is usually sufficient.

    def __str__(self):
        # Update __str__ to use available fields
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.role or 'No Role'})"
        elif self.email:
            return f"{self.email} ({self.role or 'No Role'})"
        elif self.phone_number:
            return f"{self.phone_number} ({self.role or 'No Role'})"
        else:
            return f"User ID: {self.id} ({self.role or 'No Role'})"

    class Meta(AbstractUser.Meta): # Inherit Meta options from AbstractUser
        # Add custom meta options if needed
        pass
