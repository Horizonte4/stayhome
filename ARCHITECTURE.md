# StayHome Architecture

## 1. System Overview

StayHome is a Django-based platform for property rental and sale. The codebase is organized as a multi-app Django project with a shared PostgreSQL database, server-rendered templates, and a small set of service modules that centralize write-side business rules.

At a high level:

- `stayhome/` provides project settings, root URL routing, and the application entry point.
- Domain behavior is split across dedicated Django apps such as `users`, `properties`, `transactions`, `comunication`, and `aichat`.
- Shared templates live in the repository-level `templates/` directory, while static assets and media are served from `static/` and `media/`.
- The default runtime model is containerized through Docker and Docker Compose.

## 2. Technology Stack

### Framework and runtime

- Python 3.12 is the base runtime in `Dockerfile`.
- Django is the primary web framework.
- The project uses a custom Django user model declared as `AUTH_USER_MODEL = "users.User"` in `stayhome/settings.py`.
- Server-side templates are rendered with Django Templates, using `templates/` as a shared template directory and `APP_DIRS = True` for app template discovery.

### Persistence

- The default database engine is PostgreSQL via `django.db.backends.postgresql`.
- Database connection parameters are read from environment variables in `stayhome/settings.py`.
- PostgreSQL is provided in local development by the `db` service defined in `docker-compose.yml`, using the `postgres:16` image.

### Supporting libraries observed in the repository

- `psycopg2-binary` for PostgreSQL connectivity.
- `python-dotenv` for local environment loading.
- `Pillow` for image handling.
- `requests` for outbound HTTP access in the products integration.
- `google-genai` for the AI chat integration.
- `pytest-django` is listed in `requirements.txt`.

## 3. Container Architecture with Docker and Docker Compose

### Docker image

The application image is defined in `Dockerfile`:

- Base image: `python:3.12-slim`
- System packages: `gcc`, `libpq-dev`, and `gettext`
- Python dependencies are installed from `requirements.txt`
- The application code is copied into `/app`
- Port `8000` is exposed
- The default command runs Django's development server

### Compose services

`docker-compose.yml` defines two services:

- `db`
  - Uses `postgres:16`
  - Persists data in the `postgres_data` volume
  - Exposes PostgreSQL on host port `5433`
- `web`
  - Builds from the local `Dockerfile`
  - Mounts the repository into `/app`
  - Exposes Django on host port `8000`
  - Depends on `db`
  - Injects database, email, product API, and Gemini API settings through environment variables

The `web` service currently starts with:

```sh
sh -c "pip install -r requirements.txt && python manage.py runserver 0.0.0.0:8000"
```

This confirms that the default Compose workflow is aimed at development rather than production hardening.

## 4. Django Application Structure

### Installed apps

The project-level `INSTALLED_APPS` in `stayhome/settings.py` includes:

- Django built-ins such as `django.contrib.admin`, `auth`, `sessions`, `messages`, and `staticfiles`
- Project apps:
  - `stayhome`
  - `users`
  - `properties`
  - `core`
  - `transactions`
  - `comunication`
  - `aichat`

### URL composition

`stayhome/urls.py` acts as the root router:

- `/admin/` for Django admin
- `/users/` for user-related routes
- `/properties/` for property browsing and management
- `/transactions/` for bookings and purchases
- `/chat/` for direct communication
- `/ai/` for the AI assistant
- `/api/productos-aliados/` and `/productos-aliados/` for the products integration

The project also enables `i18n_patterns`, so most user-facing routes are language-aware.

### View organization

The codebase follows a practical layering pattern:

- `views.py` handles HTTP concerns such as request parsing, access control, redirects, and template rendering.
- `selectors.py` groups read-side query composition.
- `services.py` centralizes write-side business logic and orchestration.
- `models.py` owns persistence, domain state, and model-level helpers.

This is not a strict Clean Architecture implementation with separate packages for all use cases, but it does apply a clear boundary between HTTP handlers, queries, and mutation logic.

## 5. Domain Model

### Users and roles

`users/models.py` defines:

- `User`
  - Extends `AbstractUser`
  - Removes `username`
  - Uses `email` as the login identifier
- `Client`
  - One-to-one profile linked to `User`
- `Owner`
  - One-to-one profile linked to `User`

The `RoleCheckerMixin` adds role helpers such as `is_owner`, `is_client`, and `role`.

### Properties

`properties/models.py` defines:

- `Property`
  - Core listing aggregate for rental and sale
  - Supports `short_term`, `long_term`, and `sale` through `listing_type`
  - Stores pricing, capacity, location, media, and availability metadata
  - Implements helper methods such as `get_blocked_dates()`, `is_available()`, and overlap checks against approved bookings
- `SavedProperty`
  - Join entity between a user and a property
  - Used for favorites and wishlist behavior
  - Categorization depends on `listing_type`

`PropertyManager` and `PropertyQuerySet` in `properties/managers.py` provide query helpers for search, availability filtering, and sold-property exclusion.

### Transactions

`transactions/models.py` defines:

- `Booking`
  - Connects a user to a property and a date range
  - Tracks status through `pending`, `approved`, `rejected`, and `cancelled`
  - Computes duration and total price
- `Purchase`
  - Connects a buyer to a property purchase request
  - Tracks status through `pending`, `approved`, and `rejected`
  - Stores the captured `total_value`

### Shared model behavior

`core/models.py` provides `TimeStampedModel`, which supplies:

- `created_at`
- `updated_at`

Both `Booking` and `Purchase` inherit from this base model.

## 6. Service Layer in `services.py`

StayHome uses a service-layer style to keep non-trivial business logic out of HTTP views.

### `properties/services.py`

`PropertyService` and related helper functions encapsulate property-oriented business operations:

- Normalize and validate blocked availability dates
- Create a property and attach the current owner
- Update property data without losing the existing availability calendar
- Delete a property
- Update the availability calendar
- Toggle a property in the authenticated user's saved list
- Assemble the full property detail context, including saved state, purchase state, booking state, and calendar payload

This module also exposes helper functions for blocked and reserved date calculation, as well as availability filtering.

### `transactions/services.py`

This is the main transactional business module.

`BookingService` handles:

- Booking conflict detection
- Booking creation
- Booking approval, rejection, and cancellation
- Owner and client booking dashboard data

`PurchaseService` handles:

- Purchase request creation
- Purchase approval
- Purchase rejection

`ReportService` handles:

- Aggregated metrics for the Django admin reporting dashboard

### `reports/services.py`

This module defines a separate `ReportService` focused on exporting a JSON snapshot of selected system metrics. Its responsibility is different from the admin dashboard metrics in `transactions/services.py`.

### Other service modules observed

- `notifications/services.py` sends booking-related email notifications.
- `products/services.py` fetches partner products from an external API configured by `PRODUCT_API_URL`.
- `aichat/services.py` separates the Google Gemini SDK wrapper (`GeminiService`) from the application use-case orchestrator (`AssistantService`).

## 7. Transaction Boundaries and Data Integrity

The repository uses `transaction.atomic()` as a context manager, not as a decorator.

### Booking creation

`BookingService.create_booking()` wraps booking creation in:

```python
with transaction.atomic():
    booking = Booking.objects.create(...)
    NotificationService.send_booking_request_email(booking)
```

This means the booking insert and the owner notification attempt are treated as a single atomic unit from the service perspective. If the notification step raises an exception before the block completes, the database transaction is rolled back and the pending booking is not committed.

### Booking approval

`BookingService.change_status()` uses another atomic block when a booking is approved:

- The target booking is marked as `approved`
- Any overlapping pending bookings for the same property are loaded
- Each overlapping pending booking is marked as `rejected`

This is important because approval and overlap cleanup must succeed together. The code avoids a partial state where one booking becomes approved while conflicting pending requests remain unresolved.

### AI chat persistence

`aichat/services.py` also uses `transaction.atomic()` inside `AssistantService.process_message()` to persist the user message and assistant reply together. If one message cannot be saved, the conversation does not end up with an orphaned partial exchange.

## 8. Property, Booking, and Purchase Business Flows

### Property types and sale eligibility

The code does not define a real `is_purchasable` field. Purchase eligibility is derived from existing domain state:

- A property is treated as purchasable when `listing_type == "sale"`
- A property is no longer effectively available for sale once an approved `Purchase` exists

This rule appears in both the transaction service logic and the property-query filtering implemented in `properties/managers.py`.

### Availability model

Property availability is the combination of:

- Blocked dates stored in `Property.availability_dates`
- Approved booking overlaps

Blocked dates are stored as a comma-separated string and converted into date values by `Property.get_blocked_dates()`. Availability checks for rental listings use:

- `has_blocked_dates_overlap()`
- `has_approved_booking_overlap()`
- `is_available()`

For search results, `PropertyQuerySet.available()` and `filter_properties_by_availability()` work together to remove sold listings and rental date conflicts.

### Booking workflow

The booking flow is implemented through `transactions/views.py` and `BookingService`:

1. The user submits check-in and check-out dates.
2. The view validates the request shape and date parsing.
3. `BookingService.create_booking()` enforces domain rules:
   - owners cannot book their own properties
   - sale listings cannot receive bookings
   - long-term rentals require a minimum stay of 30 days
   - long-term rentals must be booked in full 30-day increments
   - unavailable dates are rejected
4. A new booking is created with `pending` status.
5. The property owner can later approve or reject the booking.
6. When approved, overlapping pending bookings are rejected automatically.
7. Clients can cancel only if the booking is still outside the configured cancellation limit (`BOOKING_CANCEL_DAYS_LIMIT`).

### Purchase workflow

The purchase flow is implemented through `transactions/views.py` and `PurchaseService`:

1. The buyer submits a purchase request from a property detail page.
2. `PurchaseService.request_purchase()` enforces domain rules:
   - only `sale` properties can be purchased
   - owners cannot buy their own properties
   - a property with an approved purchase cannot be purchased again
   - the same buyer cannot create duplicate requests for the same property
3. The service creates a `Purchase` with `pending` status and copies the current property price into `total_value`.
4. The property owner approves or rejects the request through `change_purchase_status`.
5. Once approved, the property becomes logically sold and is excluded from available property queries.

### Contact flow coupling

`PropertyService.build_property_detail_context()` exposes `can_contact_owner` based on real business rules:

- sale listings can trigger owner contact
- rental listings require an approved booking before contact is enabled

This ties communication access to transaction state rather than making chat universally available.

## 9. Reporting Services and JSON Output

StayHome has two reporting paths with different consumers.

### Admin dashboard reporting

`transactions/services.py` exposes `ReportService.get_admin_dashboard_data()`, which feeds the custom admin reporting dashboard defined in `transactions/admin.py`.

This service computes:

- total users, clients, owners, properties, bookings, and purchases
- booking counts by status
- purchase counts by status
- most booked property
- top booked properties
- top properties by approved sales
- latest booking
- latest confirmed sale

The dashboard is rendered through `templates/admin/transactions/reports_dashboard.html`.

### JSON report generation

`reports/services.py` exposes `ReportService.generate_system_report_json(output_path="system_report.json")`.

This method builds a payload with:

- `total_users_created`
- `most_booked_property`
- `last_booking`
- `last_confirmed_sale`

It serializes the payload to a JSON file using `json.dump(..., ensure_ascii=False, indent=2)` and returns both the output path and the in-memory report structure.

## 10. Current Constraints Observed in the Codebase

- `reports/` exists as a Python module with a reporting service, but it is not listed in `INSTALLED_APPS`.
- No versioned contributor instruction file such as `agent.md`, `AGENT.md`, or `CONTRIBUTING.md` was found in the repository root or `.github/`.
- Property blocked dates are stored as a comma-separated string in `Property.availability_dates`, which simplifies the schema but pushes parsing and validation into service and model helpers.
- Docker Compose currently runs Django's development server and installs dependencies at container startup, which is convenient for local development but not optimized for a production runtime.
