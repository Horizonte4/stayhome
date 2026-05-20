# StayHome Onboarding

## 1. Purpose of This Guide

This document helps a new contributor start working on StayHome using only the repository's current implementation. It focuses on local setup, project navigation, and the code organization patterns that appear throughout the Django apps.

## 2. Prerequisites

The current repository implies the following local requirements:

- Git
- Docker
- Docker Compose

Because the default workflow is containerized, no host-level Python virtual environment is required for basic startup.

## 3. Local Setup with Docker Compose

### Clone the repository

```bash
git clone https://github.com/Horizonte4/stayhome.git
cd stayhome
```

### Review environment configuration

The repository includes `.env.example`. Review it before startup if you need to provide values for:

- database settings
- email delivery settings
- `PRODUCT_API_URL`
- `GEMINI_API_KEY`

The Django settings file also provides defaults for several local development variables.

### Build and start the containers

```bash
docker compose up --build
```

This starts:

- `db`: PostgreSQL 16
- `web`: the Django application

The application becomes available at:

- `http://localhost:8000`

## 4. Database Migrations and Initial Access

### Apply migrations

Open a second terminal after the containers are running and execute:

```bash
docker compose exec web python manage.py migrate
```

### Create a superuser

This step is optional, but useful if you need access to Django admin:

```bash
docker compose exec web python manage.py createsuperuser
```

### Access points

- Main application: `http://localhost:8000`
- Django admin: `http://localhost:8000/admin`

## 5. Project Folder Map

The most important folders for day-to-day development are:

### Project and configuration

- `stayhome/`
  - `settings.py`
  - `urls.py`
  - project-level configuration and entry points
- `manage.py`
  - Django management entry point

### Domain apps

- `users/`
  - custom user model and role profiles
- `properties/`
  - property listings, favorites, wishlist, availability, and property search
- `transactions/`
  - bookings, purchases, owner/client transaction flows, and admin reporting
- `comunication/`
  - direct messaging flows between users
- `aichat/`
  - AI assistant session and message orchestration
- `core/`
  - shared abstract models

### Supporting modules

- `reports/`
  - JSON reporting service
- `products/`
  - partner-products integration
- `notifications/`
  - outbound booking email notifications

### Presentation and assets

- `templates/`
  - shared templates
  - feature templates grouped by app
  - admin templates under `templates/admin/...`
- `static/`
  - static CSS and other front-end assets
- `media/`
  - uploaded files
- `locale/`
  - translation resources

### Automation

- `.github/workflows/`
  - CI definitions

## 6. Where to Find Models, Services, Selectors, Views, and Templates

The repository follows a repeated structure across its Django apps.

### `models.py`

Use `models.py` when you need to understand:

- persistent entities
- field definitions
- status enums
- model-level helper methods
- custom managers and querysets linked from the model

Examples:

- `users/models.py` defines `User`, `Client`, and `Owner`
- `properties/models.py` defines `Property` and `SavedProperty`
- `transactions/models.py` defines `Booking` and `Purchase`

### `services.py`

Use `services.py` when you need to understand write-side behavior and business rules.

Examples:

- `properties/services.py`
  - property creation and update
  - availability-date normalization
  - saved-property toggling
  - property detail context composition
- `transactions/services.py`
  - booking creation and status transitions
  - purchase request and approval flow
  - reporting metrics for admin
- `reports/services.py`
  - JSON report generation

### `selectors.py`

Use `selectors.py` when you need to understand read-side query composition.

Examples:

- `properties/selectors.py`
  - property detail lookup
  - saved-property lookups
  - available-property search entry point
- `transactions/selectors.py`
  - client booking context aggregation

### `views.py`

Use `views.py` when you need to understand:

- request validation
- redirects and messaging
- access control checks
- template rendering
- the point where services are invoked from HTTP routes

The codebase generally keeps views lightweight and pushes business rules into services.

### `urls.py`

Each app exposes its HTTP surface through `urls.py`. Start there when tracing a feature from route to view.

Key examples:

- `stayhome/urls.py` for project-level routing
- `properties/urls.py` for property pages
- `transactions/urls.py` for bookings and purchases

### Templates

Templates are grouped by feature area inside `templates/`:

- `templates/properties/`
- `templates/transactions/`
- `templates/users/`
- `templates/comunication/`
- `templates/aichat/`
- `templates/admin/transactions/`

Password-reset templates also exist under `templates/auth/` and `templates/registration/`, but they are separate from the business workflows documented here.

## 7. Development Workflow Based on the Current Repository

### Read the full feature slice before changing behavior

For any non-trivial change, review the relevant feature across:

1. `models.py`
2. `selectors.py`
3. `services.py`
4. `views.py`
5. `urls.py`
6. related templates

This matters because the repository often splits a single feature across these layers.

### Preserve the current separation of responsibilities

The current codebase is easier to reason about when these boundaries stay intact:

- keep HTTP parsing and response handling in views
- keep read-side query composition in selectors
- keep mutation and business orchestration in services
- keep state and domain helpers in models

### Check the user-facing templates for workflow impact

Many business rules surface directly in templates, especially in:

- property detail pages
- booking dashboards
- owner action screens
- admin reports

If a service or view changes, confirm whether the rendered UI also needs to change.

### Pay attention to role-based behavior

Several workflows differ for:

- anonymous users
- clients
- owners
- admin users

Before changing a route or service, verify which role is expected to trigger it.

### Follow the runtime assumptions already in the repo

The repository currently assumes:

- local development through Docker Compose
- PostgreSQL as the database backend
- email configuration through environment variables
- server-rendered Django templates rather than a separate front-end application

## 8. Common Entry Points for New Contributors

If you are new to the project, these are the most useful starting points:

- `stayhome/settings.py`
  - confirms installed apps, database settings, templates, static/media paths, and the custom user model
- `stayhome/urls.py`
  - shows the top-level feature map
- `properties/models.py` and `transactions/models.py`
  - explain the core domain
- `properties/services.py` and `transactions/services.py`
  - explain most of the business rules
- `templates/properties/detail.html`
  - shows how property availability, booking, and purchase flows are exposed to the user
- `transactions/admin.py`
  - shows how admin reporting is wired into Django admin

With those files, a contributor can usually trace a feature end to end before making changes.
