# Multi-Tenant Laundry Management System – Backend Development Task Plan

## Django Backend (Python + Django REST Framework)

This section outlines the tasks to implement the laundry management system backend using Django, PostgreSQL/PostGIS, and Django REST Framework (DRF). The solution will use a custom User model and follow a multi-tenant SaaS architecture where a single application instance serves multiple laundry businesses (tenants). Data for each tenant will be isolated via an Organization ID partition key (table-based multi-tenancy). PostGIS will be enabled in PostgreSQL to support geospatial queries for finding nearby outlets. We will organize the development tasks into categories: Models, Authentication, API Endpoints, Role Logic, Testing, and Deployment.

## Models and Database

### Organization (Tenant) Model
Create an Organization model to represent each laundry business (tenant). Include fields like name, contact info, subscription tier, billing status, and a unique identifier or subdomain. This model serves as the tenant key for multi-tenancy, with other models linking to it to isolate data per client.

### Outlet Model (Geolocation)
Define an Outlet model for physical laundry outlet locations. Fields: address details and a location field (GeoDjango PointField) for GPS coordinates. Enable the PostGIS extension in the PostgreSQL database and use the django.contrib.gis.db backend. A geospatial index should be added on the location field to allow efficient distance queries (find nearest outlets). Each Outlet links to an Organization (foreign key).

### Custom User Model
Implement a custom user model (subclassing AbstractUser or AbstractBaseUser) to support both staff and customers. Include fields for email/phone login, and a relation to Organization for staff users (null for customers). Add a role field or a many-to-many relation to a Role model to distinguish user roles (e.g. 'attendant', 'dispatcher', 'washer', 'dryer', 'ironer', 'qc_packager', 'org_admin', 'customer', 'super_admin'). Alternatively, use Django Groups/Permissions to represent these roles. Ensure the custom user model is integrated with DRF authentication.

### Role Model (Optional)
If using a separate model for roles, define a Role model with role name constants. Seed the basic roles and create a mapping between users and roles. This will facilitate role-based access (e.g. only users with the "dispatcher" role can accept dispatch jobs).

### Laundry Order and Item Models
Create an Order model to represent a laundry drop-off order. Fields: customer (ForeignKey to User), outlet (ForeignKey), organization (ForeignKey for quick tenant filtering), order status, timestamps (created, completed), and payment status (partial/paid). Each Order can have multiple LaundryItem entries: define a LaundryItem model with fields like description (e.g. "blue shirt"), service type(s) requested, turnaround time (TAT), and current stage/status (e.g. pending, washing, drying, etc.). Link LaundryItem to its Order and Organization. Use choices or a small related model for item status to track progress through washing/drying/ironing/QC stages.

### ServiceType and TAT
Define representations for service options and turnaround times. For example, create a ServiceType model or choices enumerating the possible services (washing, drying, ironing combinations) and a field or model for TAT (normal vs express). Seed the database with these values on initialization – e.g. service types "Washing only", "Drying only", "Ironing only", "Washing & Drying", "Drying & Ironing", "Washing, Drying & Ironing" as described, and TAT options "normal" or "express".

### Process and Logistics Models
Implement models to track logistics of laundry movement:

#### Dispatch Request
Model a dispatch of laundry bags between locations. Fields: source (outlet or factory), destination, requested by (user), assigned dispatcher (user), status (requested, accepted, in-transit, completed), timestamps. This helps manage "dispatch to factory" and "dispatch to outlet" events.

#### Handover/Transfer
For handovers between teams (washing -> drying -> ironing -> QC), you may use status updates on LaundryItem or a small Handover model to log each transfer. Each handover record can log from_stage, to_stage, item or batch, requested_by, accepted_by, timestamps. This is useful for auditing the chain of custody for items.

#### Defect Report
Optionally, create a model to record defects discovered (e.g. missing button, stain not removed). Fields: item, reported_by (QC), defect_type/notes, resolved flag, and stage at which it was found. This ties into the return-to-previous-stage flow.

#### Payment/Invoice
Model invoices or payments for orders. Fields might include order, amount, payment method, and whether it's full or partial. Alternatively, store payment info in Order if simple. These records will be used to send receipts/invoices via notifications.

### Super Admin & Subscription Models
For the platform owner (super-admin), create a model (or extend Organization) for subscription details. Include fields like plan type (tier), billing cycle, price, active/inactive status. This allows the super-admin to manage laundry organizations' subscriptions and enforce limits (e.g. max outlets or users for a basic tier). Possibly include a Subscription model related to Organization, with fields for plan name, start/end dates, and payment status.

### Database Migrations & Seed Data
Write migrations for all the above models. After defining models, create an initial migration to set up the schema (including enabling PostGIS extension via a custom migration step). Prepare a seed script or fixture to populate essential reference data: default Roles, ServiceType entries, TAT entries, and maybe a default Super Admin user. This ensures the system has required values (roles, service options) from the start. Use Django's loaddata or a migration to insert these. Verify that geospatial indices are created on location fields.

## Authentication & Authorization

### DRF Authentication Setup
Configure Django REST Framework authentication. Enable token-based auth (e.g. using DRF's built-in TokenAuthentication or JSON Web Tokens via libraries like djangorestframework-simplejwt). The custom User model should work with DRF's auth system. Implement endpoints for user registration and login for both customers and organization users. For example, a /api/auth/register/ for customer signup (with email/phone, password), and a separate flow for organization user creation (likely done by an org admin or super-admin). Provide a /api/auth/login/ that returns a token for subsequent requests.

### Permission Classes
Use DRF permission classes or custom permissions to enforce access rules. For instance, create a custom permission that checks the user's role and organization. Example: IsOrganizationStaff permission to allow access only to users associated with an organization (and possibly matching the organization context of the request), and IsCustomer or IsAuthenticated for customer endpoints. Also implement IsSuperAdmin for super-admin specific APIs. These will be applied on viewsets or views to enforce role-based access control in addition to simple authentication.

### Multi-Tenant Enforcement
Implement middleware or hooks to always filter data by the user's organization (for org staff). For example, when an outlet attendant queries orders, the API should automatically filter Order.objects.filter(organization=user.organization). You can integrate this logic in the view (queryset filtering) or use Django's capability like global filters. The goal is to ensure one tenant cannot access another tenant's data. Use the Organization foreign keys on each model to scope queries. For extra safety, consider using Django's object-level permissions or even row-level security in Postgres, but application-level filtering is usually sufficient.

### JWT for Organization Users (Optional)
Although not strictly required by DRF (which can use session or token auth), you might align with modern practices and use JWT for both types of users. If so, configure the JWT authentication classes and issue role-embedded JWTs (include user's roles and org in the token claims). This can simplify stateless auth and allow frontends to show/hide features based on token info. Make sure to set appropriate expiration and refresh mechanisms.

## API Endpoints and Business Logic

Design a comprehensive set of RESTful API endpoints to cover all core functionalities. Use DRF viewsets or class-based views for clean implementations, grouping related functionality. Below is a breakdown of required API areas:

### Customer-Facing APIs

#### Customer Registration & Profile
Endpoints for customers to register an account and manage profile info. (e.g. POST /api/customers/register, GET/PUT /api/customers/me). Basic validation (unique email/phone) and secure password hashing via Django's auth system.

#### Laundry Discovery (Geolocation Search)
Provide an endpoint for customers to find nearby laundry outlets. For example, GET /api/outlets/nearby?lat=<>&lng=<> which queries the Outlet model using a geospatial filter. Utilize PostGIS functions (via Django ORM GeoQueries) to find outlets within a radius or ordered by distance from the provided coordinates. The view should not require auth (or optional auth) since new customers might search before signing up. Return a list of outlets with details (name, distance, services offered, etc.).

#### Create Laundry Order (Drop-off)
Allow a customer to initiate a laundry order. This could be a POST /api/orders/ where the customer selects an outlet (if scheduling a drop-off or pickup request). However, in the typical flow, an outlet attendant creates the order when the customer physically drops off laundry. If we allow online order creation, implement it carefully: the order would be in a pending state awaiting drop-off. For simplicity, this API could be limited or omitted in favor of attendant-created orders.

#### Order Tracking & Notifications
Provide GET /api/orders/<id>/ for a customer to view the status and details of their order (items, services, current stage, expected ready time). Also, GET /api/orders/ list for their order history. These should filter by the authenticated customer's ID. As part of the order status updates (processed via staff APIs), trigger notifications to the customer: for example, when an order is ready for pickup, send a WhatsApp/SMS or email notification with the pickup code or invoice. (The actual sending is handled via integration tasks described later.)

#### Payment
If online payment is in scope, expose an endpoint for making payments (or recording that payment was made). E.g. POST /api/orders/<id>/pay to mark an order as paid (this could integrate with a payment gateway). Otherwise, payments may be recorded by staff at drop-off/pickup. Ensure that when an order is marked paid, a receipt notification can be sent (email/WhatsApp with invoice).

### Laundry Staff & Operations APIs
(These are secured for organization users and require role-based permissions)

#### Outlet Attendant APIs

##### Order Intake
Endpoint for attendants to create a new Order when a customer drops off laundry. For example, POST /api/org/<org_id>/orders/intake with payload of customer info (if new customer, create user or mark as guest), items list (each with description, service type, TAT). The server calculates pricing (if pricing rules exist) and generates an invoice. It should respond with an order ID and invoice details. The attendant may take payment on the spot: include payment info in the request or have a separate call. If partial payment is made, record that. Mark order status as "Received" or "Processing". Generate unique item tags (IDs or QR codes) for each item – possibly returned in the response for printing tags.

##### Dispatch to Factory
Since some laundries have off-site processing, attendants need to dispatch accumulated items to the central factory. Implement an endpoint like POST /api/org/<org_id>/dispatches/ to create a dispatch request when a batch of items (one or multiple orders, grouped as "laundry bags") is ready to go. The request includes which orders/items are in the dispatch and which dispatcher (driver) is requested. Mark those items as "Awaiting Pickup". Optionally, allow the system to auto-select an available dispatcher. This will create a Dispatch record with status "Pending Pickup". If the outlet has an on-site processing (no factory dispatch needed), this step can be skipped (the system might be configurable per org).

##### Receive Returned Laundry
When finished laundry comes back from the factory, provide an endpoint for attendants to mark orders as returned and ready for customer pickup. For example, POST /api/org/<org_id>/orders/<id>/ready to mark an order ready for pickup (triggering a notification to the customer). Also, an endpoint to confirm customer pickup: POST /api/org/<org_id>/orders/<id>/complete which finalizes the order, maybe requiring a pickup code or signature confirmation. This will mark order status "Completed".

#### Dispatcher (Driver) APIs

##### View Assigned Pickups
A dispatcher user should fetch pending dispatch requests assigned to them. Endpoint: GET /api/org/<org_id>/dispatches?assigned_to=me&status=pending. They should only see dispatches for their organization and that are either unassigned or assigned to them.

##### Accept Dispatch Request
Endpoint for driver to accept a pickup assignment, e.g. POST /api/org/<org_id>/dispatches/<id>/accept. This changes the dispatch status to "In Transit" and records the driver's acceptance (and timestamp). Notify the outlet that pickup is en route, if needed.

##### Confirm Delivery
Once the dispatcher delivers laundry bags to the factory (for outlet->factory dispatch) or to the outlet (for factory->outlet return), they use an endpoint to mark the dispatch complete. E.g. POST /api/org/<org_id>/dispatches/<id>/complete with info like delivered_at time. This will update the dispatch status and trigger the next step (factory received or outlet received). Possibly, include capturing a signature or photo proof (out of scope for now).

The dispatch endpoints should enforce that only users with the dispatcher role can accept/complete dispatches, and they can only act on dispatches for their own organization.

#### Processing Team APIs (Washing, Drying, Ironing)
At the factory side, each team member should use the app (or an internal interface) to claim and update work on laundry items:

##### Accept Handover
When a dispatch arrives at the factory, the Washing Team should be notified of incoming items. Provide an endpoint for a washing team member to acknowledge receipt of a batch (handover from dispatcher). E.g. POST /api/org/<org_id>/batches/<batch_id>/handover/accept or similarly at item level. This will mark those items as in "Washing" stage. Only washing team role can do this.

##### Mark Washing Complete
Endpoint: POST /api/org/<org_id>/items/<item_id>/washed (could be bulk or per item). Marks item status as washed. If the item's requested services include drying or ironing, automatically trigger the next stage handover request. For instance, once washed, if drying is needed, create a handover task assigned to the Drying Team. This could be represented by updating item status to "Awaiting Drying" and maybe notifying drying team. The washing team's interface could have an action "handover to drying" which effectively flags items for the next team.

##### Drying Team
Similar endpoints: accept handover for drying, mark items dried (POST .../items/<id>/dried), then trigger handover to ironing if ironing is requested. If ironing is not needed for certain items, trigger handover directly to QC for those.

##### Ironing Team
Endpoints to accept handover of items needing ironing, mark items ironed (POST .../items/<id>/ironed), then send to QC.

For each stage, ensure the user has the correct role to perform the action, and that the item's current status matches the stage (e.g. a drying team member shouldn't mark an item washed). Status transitions should be enforced in business logic.

##### Defect Handling
At any stage, if a team member finds an issue (e.g. stain not removed after washing), they should flag it. Provide an endpoint like POST /api/org/<org_id>/items/<id>/defect with details. This will mark the item with a defect and create a Defect record. The system should then allow a return to previous stage: e.g. a drying team member finds a washing defect (clothes still dirty) – they trigger a return to washing. In practice, that could mean updating item status back to "Washing" and notifying the washing team. Implement endpoints for accepting these returns: e.g. POST /api/org/<org_id>/items/<id>/return/accept by a washing team member to acknowledge reprocessing. Similar flows for drying defects (return to drying) and ironing defects. Each defect resolution should be logged. If a defect is not tied to a previous stage (like a tear or missing button discovered at QC), the QC team may resolve it directly or mark it as irreparable.

Throughout these processes, update the LaundryItem status accordingly: e.g., "In Washing", "Washing Complete", "Returned to Washing due to defect", etc. Maintain a history of status changes (could simply rely on timestamps in Defect or Handover models).

#### Quality Control (QC) & Packaging APIs

##### Accept Items for QC
Once ironing (or earlier if no ironing) is done, the QC and Packaging team receives the items. Endpoint for QC to accept the handover: e.g. POST /api/org/<org_id>/batches/<batch_id>/qc/accept marking items as "In QC". Only users with QC role can do this.

##### Inspect & Mark QC Status
For each item or order, QC can mark it as passed or note defects. If defects are found in final QC, use the defect endpoints described to route items back to the appropriate team (washing, drying, or ironing). If an "other defect" (like damage) that cannot be fixed by prior stages, record it and possibly adjust the order (maybe issue a refund or note for customer).

##### Packaging
Once items pass QC, the packaging step can be integrated: QC team packs the items (perhaps grouping by order or destination outlet). Provide an endpoint to mark an order as "Packaged and Ready". E.g. POST /api/org/<org_id>/orders/<order_id>/packaged. This triggers the final dispatch back to the outlet. The system creates a dispatch request (factory -> outlet) similar to the initial dispatch.

##### Dispatch to Outlet
QC/Packaging can call an endpoint to initiate a return dispatch: POST /api/org/<org_id>/dispatches/return with details of which orders/bags to send and which dispatcher is assigned. This creates a Dispatch record for the return trip, notifies the dispatcher, and marks items as "Out for Delivery". The dispatcher flow for pickup and delivery back to outlet is as described before (they accept and complete the trip).

### Super-Admin APIs
(for platform administrators managing all tenant organizations)

#### Organization Management
Endpoints to create and manage tenant organizations. For example, POST /api/admin/organizations/ to register a new laundry business (with details like name, plan, etc.), PUT /api/admin/organizations/<id>/ to update subscription info, and possibly deactivate or delete. Only the super-admin role can access these.

#### Subscription Tier Management
If multiple subscription tiers exist (e.g., Basic, Premium), provide APIs to define and modify these plans. Alternatively, treat plans as code constants. At minimum, the super-admin should be able to assign a tier to an Organization and set billing parameters. E.g. POST /api/admin/organizations/<id>/assign_plan with plan details.

#### Billing and Invoices
While actual payment processing might be external, provide an endpoint to view usage or send billing info. For instance, GET /api/admin/organizations/<id>/usage to retrieve that org's monthly order count, etc., and POST /api/admin/organizations/<id>/invoice to record or send an invoice for subscription fees. Integration with a payment gateway or accounting system can be planned as a future task.

#### Global Settings
Possibly APIs to manage global lists like service types or default pricing. If the service types and TAT are mostly fixed as per the domain, this may not require frequent change via API (they were seeded). But if needed, allow super-admin to add new service types or adjust configurations (e.g., enabling new notification templates).

### Notification Integration
(cross-cutting concern, implemented via service modules or signals)

Although not a REST endpoint for external use, design internal hooks to send notifications for key events: order created (send invoice link via email/SMS), order status changes (in-progress, ready for pickup notifications), order completed (thank you and receipt), and dispatch events (perhaps notify destination on dispatch initiation). Use Django's signal framework or call notification functions in the views.

#### WhatsApp/SMS/Email
Integrate with a service like Twilio for SMS/WhatsApp and an email service (SMTP or service API). For example, when an invoice is generated, trigger a WhatsApp message with a short link to the invoice PDF, or send an SMS and email with the invoice attached. Use templated messages for consistency. Ensure these operations are done asynchronously (via Celery or Django Q) to not block request-response cycle.

Provide configuration for notification preferences (customers might choose WhatsApp vs email). Ensure opt-in/opt-out compliance where applicable. Logging of notifications (e.g., store in a Notification model or log) is useful for audit.

**Note:** All API endpoints must enforce proper permission checks. For example, an outlet attendant should not be able to call admin or other teams' endpoints, and users can only access data for their organization. Use DRF's @action or separate viewsets for role-specific actions to clearly segregate logic. Also, utilize HTTP response codes properly (201 for created, 200 for success, 400/403 for errors or forbidden actions, etc.).

## Role-Based Access Control Logic

Implement role-based access control (RBAC) so that each API route only allows permitted roles. Key tasks:

### Role Definitions & Assignment
As mentioned in Models, have a clear set of roles. The system roles include: SuperAdmin (platform owner), OrgAdmin/Manager (owner of a laundry org), Attendant, Dispatcher, WashingTeam, DryingTeam, IroningTeam, QCTeam, and Customer. Each user will be assigned one or more roles. Seed the standard roles in the database so they can be referenced. For organization staff, roles are typically singular (an employee's function), but an admin could have multiple (e.g., OrgAdmin might also act as Attendant).

### DRF Permission Classes
Develop custom DRF permission classes for each major role or group of roles. For example:
- **IsSuperAdmin**: user.is_superuser or role == SuperAdmin.
- **IsOrgAdmin**: user.role == OrgAdmin and user.organization matches the context of the request (e.g., if an OrgAdmin is accessing staff creation for their org).
- **IsStaff(role_name)**: a generic class that checks user.role == given role and ensures user.organization context where needed.
- **IsCustomer**: perhaps simply IsAuthenticated but also not staff (or a separate flag).

Use these in combination on viewsets. For instance, the Order intake endpoint might allow OrgAdmin or Attendant roles; a dispatch accept endpoint allows only Dispatcher role, etc. Document these permissions clearly in the code and possibly API docs.

### Organization Context in Requests
Many URLs include an <org_id> or such to indicate the organization context. We must ensure the authenticated user actually belongs to that org (except for SuperAdmin who can access all). Implement checks comparing request.user.organization.id to the <org_id> in the URL (or the organization of the object being accessed). This can be done in the view's get_queryset() or a custom permission. This guarantees tenant isolation at the application level (each tenant's data is private).

### Role Hierarchy and Restrictions
Define any role hierarchy if needed (e.g., OrgAdmin can do everything Attendant can, plus more). Enforce that lower roles cannot escalate privileges. For example, an Attendant shouldn't be able to create new users or change org settings – those actions are reserved for OrgAdmin or SuperAdmin. If using Django's built-in permissions, map these roles to permission sets. Otherwise, simply hard-code logic in views (simpler for a small system).

### Testing Role Access
As part of RBAC logic, plan tests to verify that each endpoint rejects unauthorized roles (covered in Testing section). For development, use dummy accounts for each role to manually test via the browsable API or CLI.

### Auditing and Logging
Consider recording who performed important actions (the user id, timestamp on status changes, etc.). This could be done via model created_by/updated_by fields or explicit log entries. This is not strictly RBAC, but it's related to accountability for multi-tenant systems.

## Testing (Unit & Integration Tests)

A thorough testing approach will ensure reliability of such a complex system:

### Unit Tests for Models
Write tests for model methods and properties. For instance, if there are helper methods (e.g., to compute order price or to check if order is complete), test them with various scenarios. Also test that multi-tenant relationships are correctly set (e.g., creating an Order automatically associates the organization from the outlet or user). Use Django's test framework with an in-memory or test database.

### API Endpoint Tests
Utilize Django's APITestCase or APIClient to simulate requests to each endpoint. Test authentication requirements (endpoints should return 401 for no token, 403 for wrong role). For example, verify that an Attendant account can create an order (201 Created) but a Customer account cannot call the attendant-specific endpoint (should get 403 Forbidden). Test happy paths and edge cases (e.g., cannot mark an item as ironed if it wasn't requested, cannot accept a dispatch that's already accepted, etc.).

### Geolocation Query Test
Populate some Outlet data with known coordinates and use the nearby search API. Assert that the results are ordered by distance and filtered correctly (maybe add a couple of outlets and ensure the one closest to a target point comes first). This will also indirectly test that PostGIS integration and geodjango are working.

### Lifecycle Simulation Tests
Simulate an end-to-end laundry order in a test:
1. Customer signup (or use an existing customer).
2. Attendant creates an order with 2 items (one requiring full service, one only wash & dry).
3. Attendant triggers dispatch to factory.
4. Dispatcher accepts and completes dispatch.
5. Washing team accepts, marks one item washed, intentionally flags a defect on the other, etc. Drying, Ironing, QC steps...
6. Finally, items are marked ready, dispatched back, and picked up by customer.

Throughout this flow, assert that each step's status is updated and only the correct role can perform the action. This integration test ensures all pieces work together.

### Multi-Tenant Data Isolation Test
Create two Organizations in test, each with some data. Use users from one org to attempt access of the other org's data (e.g., an attendant from Org A trying to fetch an order from Org B via API). Confirm the response is 404 (not found) or 403, and that no cross-org data leak is possible.

### Performance and Load Testing
Although unit tests might not cover this, plan to use tools like Django's assertNumQueries to ensure queries per request are reasonable (especially on listing endpoints – e.g., ensure N+1 queries are avoided via select_related/prefetch as needed). For geospatial queries, ensure adding an index makes the query fast. Optionally, use a test dataset to simulate a tenant with many orders to see that endpoints remain performant.

### Continuous Integration
If using CI/CD, configure the test suite to run on each commit. All tests should pass before deployment. Consider code coverage goals (e.g., > 80%).

## Deployment and DevOps

Outline tasks for deploying the Django backend in a production environment and managing the development workflow:

### Environment Configuration
Set up separate settings for development and production. Use environment variables for sensitive info (DB credentials, secret key, JWT secret, third-party API keys for notifications). Ensure the PostGIS-enabled PostgreSQL is available in each environment. For local dev, use Docker (e.g., the Kartoza PostGIS image) or install PostGIS locally. Document the required DB setup (enabling the postgis extension in the database).

### Migrations & Seed in Deployment
Automate running of Django migrations on deploy (to create/update the DB schema). Also include a step to run the initial seeding of data (roles, service types, etc.) in new environments. This could be in a Django data migration or a custom management command executed during release.

### Static Files & Media
If the app will serve media (e.g., invoice PDFs or images of items), set up an S3 bucket or use Django's Media settings accordingly. Collectstatic for admin or browsable API if needed. Not a primary concern for the API, but mention for completeness.

### Scaling Multi-Tenancy Considerations
In a multi-tenant SaaS, you might eventually separate tenants by schema or DB if needed. For now, the single-db approach with organization keys is used. Ensure that as new tenants are added, their data stays isolated. If very high data volume per tenant is expected, plan a sharding strategy (not in initial scope).

### Web Server & WSGI
Configure a production web server (Gunicorn/UWSGI with Nginx or Heroku setup). Make sure to use environment settings that enable allowed hosts, secure proxy SSL header, etc. Also, configure CORS in Django if the frontends (mobile/web) are on different domains.

### Monitoring & Logging
Plan to set up logging for important events (especially any security-related events or errors). Use Django's logging configuration to output to console or a file. Set up an error monitoring service (Sentry or similar) to catch exceptions in production.

### Documentation & Deployment Scripts
Write API documentation (e.g., using DRF's Swagger or API docs) so that front-end and testers understand how to use the endpoints. Include details about required roles for each endpoint. For deployment, write scripts or CI steps to build the Docker image (if containerized), run migrations, and start the application. Perhaps use Docker Compose for local dev (with a PostGIS service) and a similar approach for staging/production.

### Post-Deployment Verification
After deployment, always test key functionalities (auth, a sample order flow) on the live system with a test tenant. Also verify that notification integrations (Twilio email/SMS) are correctly configured with live credentials in prod environment (possibly using sandbox/test modes first).