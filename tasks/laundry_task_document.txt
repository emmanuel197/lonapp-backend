# Multi-Tenant Laundry Management System - Task Document

## Project Overview
Django REST Framework backend for a multi-tenant SaaS laundry management system with geospatial capabilities, role-based access control, and comprehensive workflow management.

---

## 1. DATABASE MODELS AND SCHEMA

### 1.1 Core Tenant Models
- **1.1.1** Create Organization (Tenant) model with fields: name, contact_info, subscription_tier, billing_status, unique_identifier
- **1.1.2** Implement multi-tenancy partition key strategy using Organization ID
- **1.1.3** Add Organization foreign key relationships to all tenant-scoped models

### 1.2 Geospatial Models
- **1.2.1** Enable PostGIS extension in PostgreSQL database
- **1.2.2** Configure django.contrib.gis.db backend
- **1.2.3** Create Outlet model with address fields and GeoDjango PointField for GPS coordinates
- **1.2.4** Add geospatial index on location field for efficient distance queries
- **1.2.5** Link Outlet model to Organization via foreign key

### 1.3 User Management Models
- **1.3.1** Implement custom User model (subclassing AbstractUser/AbstractBaseUser)
- **1.3.2** Add email/phone login capability
- **1.3.3** Create Organization relationship for staff users (null for customers)
- **1.3.4** Implement role field or many-to-many relation to Role model
- **1.3.5** Define user roles: attendant, dispatcher, washer, dryer, ironer, qc_packager, org_admin, customer, super_admin
- **1.3.6** Integrate custom user model with DRF authentication

### 1.4 Role Management Models
- **1.4.1** Create Role model with role name constants
- **1.4.2** Seed basic roles in database
- **1.4.3** Create user-role mapping functionality
- **1.4.4** Implement role-based access control integration

### 1.5 Order and Item Models
- **1.5.1** Create Order model with fields: customer, outlet, organization, order_status, timestamps, payment_status
- **1.5.2** Create LaundryItem model with fields: description, service_types, turnaround_time, current_stage
- **1.5.3** Link LaundryItem to Order and Organization
- **1.5.4** Implement item status tracking through washing/drying/ironing/QC stages
- **1.5.5** Create choices/enums for item status values

### 1.6 Service Configuration Models
- **1.6.1** Create ServiceType model/choices for service combinations
- **1.6.2** Define service types: Washing only, Drying only, Ironing only, Washing & Drying, Drying & Ironing, Full Service
- **1.6.3** Implement TAT (Turnaround Time) field/model for normal vs express service
- **1.6.4** Seed database with default service types and TAT options

### 1.7 Process and Logistics Models
- **1.7.1** Create Dispatch Request model with fields: source, destination, requested_by, assigned_dispatcher, status, timestamps
- **1.7.2** Implement Handover/Transfer model for team-to-team item transfers
- **1.7.3** Create Defect Report model with fields: item, reported_by, defect_type, resolved_flag, stage_found
- **1.7.4** Design Payment/Invoice model with order, amount, payment_method, payment_type fields

### 1.8 Subscription Management Models
- **1.8.1** Create Subscription model for organization plan management
- **1.8.2** Add fields: plan_type, billing_cycle, price, active_status, start/end_dates
- **1.8.3** Link Subscription to Organization model
- **1.8.4** Implement subscription tier enforcement logic

### 1.9 Database Setup and Migrations
- **1.9.1** Write initial migrations for all models
- **1.9.2** Create custom migration for PostGIS extension enablement
- **1.9.3** Prepare seed data script for roles, service types, and TAT entries
- **1.9.4** Create default Super Admin user setup
- **1.9.5** Verify geospatial indices creation on location fields

---

## 2. AUTHENTICATION AND AUTHORIZATION

### 2.1 DRF Authentication Setup
- **2.1.1** Configure Django REST Framework with token-based authentication
- **2.1.2** Implement JWT authentication using djangorestframework-simplejwt
- **2.1.3** Create customer registration endpoint (/api/auth/register/)
- **2.1.4** Create organization user registration flow
- **2.1.5** Implement login endpoint (/api/auth/login/) with token response
- **2.1.6** Integrate custom User model with DRF auth system

### 2.2 Permission Classes
- **2.2.1** Create IsOrganizationStaff custom permission class
- **2.2.2** Implement IsCustomer permission class
- **2.2.3** Create IsSuperAdmin permission class
- **2.2.4** Develop role-specific permission classes for each user type
- **2.2.5** Apply permission classes to viewsets and views

### 2.3 Multi-Tenant Security
- **2.3.1** Implement middleware for organization-based data filtering
- **2.3.2** Create automatic queryset filtering by user's organization
- **2.3.3** Enforce tenant isolation at application level
- **2.3.4** Implement organization context validation in requests
- **2.3.5** Add safety checks for cross-tenant data access prevention

### 2.4 JWT Configuration
- **2.4.1** Configure JWT token expiration and refresh mechanisms
- **2.4.2** Embed user roles and organization info in JWT claims
- **2.4.3** Implement stateless authentication for frontend integration
- **2.4.4** Set up JWT secret key management and rotation

---

## 3. API ENDPOINTS AND BUSINESS LOGIC

### 3.1 Customer-Facing APIs

#### 3.1.1 Customer Management
- **3.1.1.1** POST /api/customers/register - Customer registration
- **3.1.1.2** GET /api/customers/me - Customer profile retrieval
- **3.1.1.3** PUT /api/customers/me - Customer profile update
- **3.1.1.4** Implement email/phone validation and password hashing

#### 3.1.2 Laundry Discovery (Geolocation)
- **3.1.2.1** GET /api/outlets/nearby - Find nearby outlets with lat/lng parameters
- **3.1.2.2** Implement PostGIS distance queries via Django ORM
- **3.1.2.3** Return outlets ordered by distance with service details
- **3.1.2.4** Allow unauthenticated access for new customer searches

#### 3.1.3 Order Management
- **3.1.3.1** GET /api/orders/{id}/ - Order status and details retrieval
- **3.1.3.2** GET /api/orders/ - Customer order history
- **3.1.3.3** Filter orders by authenticated customer ID
- **3.1.3.4** Implement order tracking with current stage information

#### 3.1.4 Payment Integration
- **3.1.4.1** POST /api/orders/{id}/pay - Payment processing endpoint
- **3.1.4.2** Integrate with payment gateway (future scope)
- **3.1.4.3** Generate receipt notifications upon payment completion
- **3.1.4.4** Handle partial payment scenarios

### 3.2 Outlet Attendant APIs

#### 3.2.1 Order Intake
- **3.2.1.1** POST /api/org/{org_id}/orders/intake - Create new order on customer drop-off
- **3.2.1.2** Handle customer creation or guest marking
- **3.2.1.3** Process items list with descriptions, service types, and TAT
- **3.2.1.4** Calculate pricing and generate invoice
- **3.2.1.5** Generate unique item tags/QR codes
- **3.2.1.6** Record payment information and mark order status

#### 3.2.2 Dispatch Management
- **3.2.2.1** POST /api/org/{org_id}/dispatches/ - Create dispatch request to factory
- **3.2.2.2** Group orders/items into laundry bags for dispatch
- **3.2.2.3** Auto-select or manually assign dispatcher
- **3.2.2.4** Update item status to "Awaiting Pickup"
- **3.2.2.5** Create Dispatch record with "Pending Pickup" status

#### 3.2.3 Return Processing
- **3.2.3.1** POST /api/org/{org_id}/orders/{id}/ready - Mark order ready for customer pickup
- **3.2.3.2** POST /api/org/{org_id}/orders/{id}/complete - Confirm customer pickup
- **3.2.3.3** Trigger customer notification for pickup readiness
- **3.2.3.4** Require pickup code or signature confirmation

### 3.3 Dispatcher APIs

#### 3.3.1 Dispatch Assignment
- **3.3.1.1** GET /api/org/{org_id}/dispatches - View assigned pickup requests
- **3.3.1.2** Filter by assigned_to=me and status=pending
- **3.3.1.3** Enforce organization-specific dispatch visibility

#### 3.3.2 Dispatch Execution
- **3.3.2.1** POST /api/org/{org_id}/dispatches/{id}/accept - Accept dispatch assignment
- **3.3.2.2** POST /api/org/{org_id}/dispatches/{id}/complete - Confirm delivery
- **3.3.2.3** Update dispatch status and record timestamps
- **3.3.2.4** Trigger next-step notifications (factory received/outlet received)

### 3.4 Processing Team APIs

#### 3.4.1 Washing Team
- **3.4.1.1** POST /api/org/{org_id}/batches/{batch_id}/handover/accept - Accept incoming items
- **3.4.1.2** POST /api/org/{org_id}/items/{item_id}/washed - Mark washing complete
- **3.4.1.3** Trigger automatic handover to drying team
- **3.4.1.4** Update item status to appropriate next stage

#### 3.4.2 Drying Team
- **3.4.2.1** POST /api/org/{org_id}/items/{item_id}/accept_handover - Accept items for drying
- **3.4.2.2** POST /api/org/{org_id}/items/{item_id}/dried - Mark drying complete
- **3.4.2.3** Route to ironing or QC based on service requirements
- **3.4.2.4** Implement role-based access enforcement

#### 3.4.3 Ironing Team
- **3.4.3.1** POST /api/org/{org_id}/items/{item_id}/accept_handover - Accept items for ironing
- **3.4.3.2** POST /api/org/{org_id}/items/{item_id}/ironed - Mark ironing complete
- **3.4.3.3** Automatically trigger handover to QC team
- **3.4.3.4** Maintain status transition enforcement

#### 3.4.4 Defect Handling
- **3.4.4.1** POST /api/org/{org_id}/items/{id}/defect - Report defect with details
- **3.4.4.2** POST /api/org/{org_id}/items/{id}/return/accept - Accept returned items
- **3.4.4.3** Implement return-to-previous-stage workflow
- **3.4.4.4** Create defect logging and resolution tracking

### 3.5 Quality Control and Packaging APIs

#### 3.5.1 QC Processing
- **3.5.1.1** POST /api/org/{org_id}/batches/{batch_id}/qc/accept - Accept items for QC
- **3.5.1.2** Implement defect inspection and routing logic
- **3.5.1.3** Handle irreparable defects and damage recording
- **3.5.1.4** Process QC pass/fail determinations

#### 3.5.2 Packaging and Return Dispatch
- **3.5.2.1** POST /api/org/{org_id}/orders/{order_id}/packaged - Mark order packaged
- **3.5.2.2** POST /api/org/{org_id}/dispatches/return - Initiate return dispatch to outlet
- **3.5.2.3** Create factory-to-outlet dispatch requests
- **3.5.2.4** Update item status to "Out for Delivery"

### 3.6 Super-Admin APIs

#### 3.6.1 Organization Management
- **3.6.1.1** POST /api/admin/organizations/ - Create new tenant organization
- **3.6.1.2** PUT /api/admin/organizations/{id}/ - Update organization details
- **3.6.1.3** DELETE /api/admin/organizations/{id}/ - Deactivate organization
- **3.6.1.4** Implement super-admin role enforcement

#### 3.6.2 Subscription Management
- **3.6.2.1** POST /api/admin/organizations/{id}/assign_plan - Assign subscription tier
- **3.6.2.2** GET /api/admin/organizations/{id}/usage - Retrieve usage statistics
- **3.6.2.3** POST /api/admin/organizations/{id}/invoice - Record billing information
- **3.6.2.4** Implement subscription tier limit enforcement

#### 3.6.3 Global Configuration
- **3.6.3.1** Manage global service types and pricing rules
- **3.6.3.2** Configure notification templates and settings
- **3.6.3.3** Implement system-wide configuration management

---

## 4. ROLE-BASED ACCESS CONTROL

### 4.1 Role Definitions and Assignment
- **4.1.1** Define comprehensive role set: SuperAdmin, OrgAdmin, Attendant, Dispatcher, WashingTeam, DryingTeam, IroningTeam, QCTeam, Customer
- **4.1.2** Implement role seeding in database initialization
- **4.1.3** Create user-role assignment functionality
- **4.1.4** Handle multiple role assignments for admin users

### 4.2 DRF Permission Classes
- **4.2.1** Develop IsSuperAdmin permission class
- **4.2.2** Create IsOrgAdmin permission with organization context
- **4.2.3** Implement IsStaff(role_name) generic permission class
- **4.2.4** Design IsCustomer permission for customer-only endpoints

### 4.3 Organization Context Security
- **4.3.1** Implement org_id URL parameter validation
- **4.3.2** Verify user organization membership for all requests
- **4.3.3** Enforce tenant data isolation at view level
- **4.3.4** Create automatic queryset filtering by organization

### 4.4 Role Hierarchy and Restrictions
- **4.4.1** Define role hierarchy rules (OrgAdmin > Attendant, etc.)
- **4.4.2** Implement privilege escalation prevention
- **4.4.3** Map roles to Django permission sets if using built-in permissions
- **4.4.4** Document role-endpoint access matrix

### 4.5 Auditing and Access Logging
- **4.5.1** Implement created_by/updated_by fields on sensitive models
- **4.5.2** Create audit log for important actions
- **4.5.3** Record user access patterns and permission checks
- **4.5.4** Implement accountability tracking for multi-tenant operations

---

## 5. NOTIFICATION INTEGRATION

### 5.1 Notification Framework
- **5.1.1** Implement Django signals for automatic notification triggers
- **5.1.2** Create notification service layer for external integrations
- **5.1.3** Design notification templates for different event types
- **5.1.4** Implement asynchronous notification processing with Celery

### 5.2 Communication Channels
- **5.2.1** Integrate Twilio for SMS and WhatsApp messaging
- **5.2.2** Configure email service (SMTP or service API)
- **5.2.3** Implement multi-channel notification delivery
- **5.2.4** Create fallback mechanisms for failed notifications

### 5.3 Notification Events
- **5.3.1** Order creation and invoice generation notifications
- **5.3.2** Order status change notifications (in-progress, ready for pickup)
- **5.3.3** Payment confirmation and receipt delivery
- **5.3.4** Dispatch event notifications for stakeholders

### 5.4 User Preferences and Compliance
- **5.4.1** Implement customer notification preference settings
- **5.4.2** Create opt-in/opt-out compliance mechanisms
- **5.4.3** Implement notification delivery logging
- **5.4.4** Design notification audit trail for compliance

---

## 6. TESTING STRATEGY

### 6.1 Unit Testing
- **6.1.1** Write model method and property tests
- **6.1.2** Test multi-tenant relationship enforcement
- **6.1.3** Validate business logic calculations (pricing, status transitions)
- **6.1.4** Test helper functions and utilities

### 6.2 API Endpoint Testing
- **6.2.1** Implement APITestCase for all endpoints
- **6.2.2** Test authentication requirements (401/403 responses)
- **6.2.3** Validate role-based access control
- **6.2.4** Test happy path and edge case scenarios

### 6.3 Geolocation Testing
- **6.3.1** Create test data with known GPS coordinates
- **6.3.2** Test nearby outlet search functionality
- **6.3.3** Validate distance ordering and filtering
- **6.3.4** Verify PostGIS integration functionality

### 6.4 Integration Testing
- **6.4.1** Implement end-to-end order lifecycle simulation
- **6.4.2** Test multi-user role interactions
- **6.4.3** Validate status transitions and handover workflows
- **6.4.4** Test notification trigger chains

### 6.5 Multi-Tenant Security Testing
- **6.5.1** Create cross-tenant data access prevention tests
- **6.5.2** Validate organization isolation enforcement
- **6.5.3** Test role-based data filtering
- **6.5.4** Verify tenant context security

### 6.6 Performance Testing
- **6.6.1** Implement query optimization tests (N+1 prevention)
- **6.6.2** Test geospatial query performance with indices
- **6.6.3** Validate endpoint performance under load
- **6.6.4** Implement code coverage goals (>80%)

---

## 7. DEPLOYMENT AND DEVOPS

### 7.1 Environment Configuration
- **7.1.1** Set up development, staging, and production environments
- **7.1.2** Configure environment variables for sensitive data
- **7.1.3** Set up PostGIS-enabled PostgreSQL in all environments
- **7.1.4** Create Docker configuration for local development

### 7.2 Database Deployment
- **7.2.1** Automate Django migrations in deployment pipeline
- **7.2.2** Create seed data deployment scripts
- **7.2.3** Implement database backup and recovery procedures
- **7.2.4** Set up PostGIS extension automation

### 7.3 Application Deployment
- **7.3.1** Configure production web server (Gunicorn/Nginx)
- **7.3.2** Set up SSL termination and security headers
- **7.3.3** Configure CORS for frontend integration
- **7.3.4** Implement static file and media handling

### 7.4 Monitoring and Logging
- **7.4.1** Set up application logging and error tracking (Sentry)
- **7.4.2** Implement performance monitoring
- **7.4.3** Create health check endpoints
- **7.4.4** Set up alert systems for critical issues

### 7.5 CI/CD Pipeline
- **7.5.1** Create automated testing pipeline
- **7.5.2** Implement code quality checks and coverage reporting
- **7.5.3** Set up automated deployment procedures
- **7.5.4** Create rollback mechanisms for failed deployments

### 7.6 Documentation and Maintenance
- **7.6.1** Generate API documentation (Swagger/OpenAPI)
- **7.6.2** Create deployment and operational runbooks
- **7.6.3** Document role-endpoint access matrix
- **7.6.4** Set up post-deployment verification procedures

---

## Task Completion Checklist

### Phase 1: Foundation (Tasks 1.1-2.4)
- [ ] Database models and schema
- [ ] Authentication and authorization

### Phase 2: Core APIs (Tasks 3.1-3.6)
- [ ] Customer-facing APIs
- [ ] Staff operation APIs
- [ ] Admin management APIs

### Phase 3: Security and Access (Tasks 4.1-4.5)
- [ ] Role-based access control
- [ ] Multi-tenant security

### Phase 4: Integration (Tasks 5.1-5.4)
- [ ] Notification system
- [ ] External service integration

### Phase 5: Quality Assurance (Tasks 6.1-6.6)
- [ ] Comprehensive testing suite
- [ ] Performance validation

### Phase 6: Production (Tasks 7.1-7.6)
- [ ] Deployment infrastructure
- [ ] Monitoring and maintenance

---

**Total Tasks: 7 main categories, 28 subcategories, 150+ individual tasks**