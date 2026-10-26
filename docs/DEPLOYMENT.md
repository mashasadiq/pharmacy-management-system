# Deployment Guide — Render

## 1. Deployment objective

The deployment objective is to host the existing Django pharmacy management system on Render as a single web service connected to PostgreSQL.

The initial deployment will use the existing Django application, which serves its HTML templates and static assets. The future React frontend is outside the scope of this deployment and will be integrated separately when developed.

The deployment is intended initially for demonstration and testing. It must not be treated as production-ready for real patient or pharmacy business data until the required security, reliability, backup, and privacy controls are implemented and verified.

## 2. Current deployment readiness

The project currently has a local PostgreSQL configuration and environment-based settings, but Render-specific production configuration has not yet been implemented.

| Component | Current state |
|---|---|
| Django application | Implemented |
| PostgreSQL | Configured for local development |
| Environment variables | Used for secret key, debug mode, and database credentials |
| `ALLOWED_HOSTS` | Currently empty |
| `CSRF_TRUSTED_ORIGINS` | Not configured |
| Static files | `STATIC_URL` configured; production collection and serving not configured |
| Gunicorn | Not yet included in requirements |
| Render configuration | Not yet created |
| Production database connection | Not yet configured |
| HTTPS and secure cookie settings | Not yet configured |

These items must be addressed before the first deployment.

## 3. Hosting considerations and free-tier limitations

Render free services may be useful for demonstrations and testing, but they are not an appropriate sole hosting arrangement for a pharmacy handling real patient or business data.

Potential limitations include:

- Free web services may spin down after inactivity.
- Free PostgreSQL plans have storage and retention limitations.
- The application filesystem should be treated as ephemeral.
- Service availability and performance may be limited by the selected plan.

Before operational use, the project requires:

- Durable database storage.
- Automated database backups.
- A tested database recovery procedure.
- Persistent media storage if uploaded files are introduced.
- Application monitoring and error logging.
- Appropriate security and privacy controls.
- A hosting plan suitable for the application's operational requirements.

Render pricing and plan conditions may change. Consult the official documentation before selecting a hosting plan.

## 4. Pre-deployment requirements

Before deploying, complete the following checklist.

### Code and repository

- [ ] Use a dedicated deployment branch.
- [ ] Confirm that the working tree contains only intended changes.
- [ ] Commit the required application code and migrations.
- [ ] Confirm that `.env` files and secret values are excluded from Git.
- [ ] Run the full Django test suite.
- [ ] Confirm that the project starts successfully in a clean environment.

### Django production configuration

- [ ] Install and configure Gunicorn.
- [ ] Generate a strong production `SECRET_KEY`.
- [ ] Set `DEBUG=False`.
- [ ] Configure `ALLOWED_HOSTS` with the Render hostname.
- [ ] Configure `CSRF_TRUSTED_ORIGINS` with the hosted HTTPS origin.
- [ ] Configure production PostgreSQL credentials.
- [ ] Configure `STATIC_ROOT`.
- [ ] Implement a production static-file serving strategy.
- [ ] Review HTTPS proxy and secure cookie settings.
- [ ] Run Django's deployment security checks.

### Database and data protection

- [ ] Create the Render PostgreSQL database.
- [ ] Confirm the application can connect to it.
- [ ] Apply migrations in a controlled deployment step.
- [ ] Create the initial administrator securely.
- [ ] Confirm backup and recovery arrangements before handling operational data.

## 5. Production configuration requirements

The current local settings require additional production configuration.

### 5.1 Secret key and debug mode

The project already reads `SECRET_KEY` and `DEBUG` from environment variables.

For the hosted environment:

- Set `SECRET_KEY` to a strong, private value.
- Set `DEBUG=False`.
- Never commit production secrets to the repository.

### 5.2 Allowed hosts and CSRF protection

The current `ALLOWED_HOSTS` setting is empty.

It must be configured to accept the actual Render hostname. `CSRF_TRUSTED_ORIGINS` must include the hosted HTTPS origin.

These settings should be environment-aware so that local development and production can use different host configurations.

### 5.3 PostgreSQL

The current project uses individual environment variables:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

The production configuration must map the credentials supplied by Render to these variables.

If the project is later changed to use a `DATABASE_URL` connection string, update Django settings and this documentation together.

### 5.4 Static files

The project currently defines:

```python
STATIC_URL = "static/"
```

This is not sufficient by itself for production static-file deployment.

Before deployment:

- Configure `STATIC_ROOT`.
- Add an appropriate production static-file serving solution.
- Run `python manage.py collectstatic` during the build or release process.
- Verify that CSS, JavaScript, and other static assets load correctly on the hosted application.

### 5.5 Application server

Django's development server must not be used to serve the hosted application.

Add and configure Gunicorn as the production WSGI server. The start command must reference the project's actual WSGI module:

```text
config.wsgi:application
```

The final Render start command should be documented after Gunicorn has been installed and tested locally.

## 6. Render deployment procedure

Once the production requirements have been implemented and tested, follow these steps.

### Step 1: Prepare the repository

- Push the deployment branch to GitHub.
- Confirm that required migrations and application code are committed.
- Verify that no secrets or local environment files are tracked.

### Step 2: Create the PostgreSQL database

1. Sign in to Render.
2. Create a PostgreSQL database.
3. Select an appropriate region and plan.
4. Obtain the database connection details.
5. Keep credentials private.

Use the database connection information to configure the Django environment variables.

### Step 3: Create the web service

1. Create a new Render Web Service.
2. Connect the GitHub repository.
3. Select the deployment branch.
4. Set the root directory to `backend` if the build and start commands are written relative to that directory.
5. Configure the build command and start command after they have been finalized and tested.

### Step 4: Configure environment variables

Add the required production variables through the Render dashboard.

At minimum, configure:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django production secret |
| `DEBUG` | Must be `False` |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port |

Also configure the host and CSRF settings according to the production settings implementation.

Do not place secret values in GitHub or deployment documentation.

### Step 5: Build and deploy

- Trigger the initial deployment.
- Inspect the build logs.
- Confirm dependencies install successfully.
- Confirm static files are collected successfully.
- Confirm the application starts without errors.

### Step 6: Apply database migrations

Apply migrations to the intended production database using the planned release or deployment procedure.

Do not assume that deploying new code automatically applies database migrations.

### Step 7: Create the initial administrator

Create the initial administrator securely using Django's `createsuperuser` command or another documented administrative provisioning procedure.

Verify that the account has the intended application role and administrative permissions.

### Step 8: Verify the hosted application

Perform the post-deployment smoke tests described in Section 9.

## 7. Database migration procedure after deployment

Every database schema change must follow a controlled process.

1. Modify the relevant model locally.
2. Generate migrations using `makemigrations`.
3. Inspect the generated migration files.
4. Apply migrations locally.
5. Run relevant application tests.
6. Run the full test suite.
7. Commit model and migration changes together.
8. Back up production data when appropriate and supported by the hosting plan.
9. Deploy the updated application.
10. Apply production migrations in the planned release sequence.
11. Verify the affected workflow on the hosted application.

Example local commands:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py makemigrations --check --dry-run
```

For production, run migration commands only against the intended production database.

Avoid combining unrelated model changes into unreviewed migrations.

## 8. Rollback and recovery

Rolling back application code does not automatically reverse database migrations.

A database rollback may result in data loss or incompatibility with the previous application version.

The project should follow these practices:

- Maintain database backups appropriate to the hosting plan.
- Test the database restoration procedure.
- Prefer backward-compatible schema changes.
- Avoid destructive migrations without a reviewed recovery plan.
- Keep deployment and migration history available.
- Verify application behaviour after recovery.

The actual backup and restoration commands must be documented after the hosting plan and database configuration have been selected.

## 9. Post-deployment smoke tests

After each deployment, verify the following:

### Application access

- [ ] Login page loads over HTTPS.
- [ ] Static CSS and JavaScript assets load correctly.
- [ ] Users can sign in and sign out.
- [ ] Invalid login attempts are handled correctly.

### Authentication and permissions

- [ ] Administrator can access permitted administrative functions.
- [ ] Pharmacist can access permitted pharmacy workflows.
- [ ] Pharmacist is denied restricted administrator actions.
- [ ] Unauthorized users cannot access protected pages or endpoints.

### Inventory and purchases

- [ ] Drug inventory pages load.
- [ ] Stock values are correct.
- [ ] Purchase creation updates stock correctly.
- [ ] Repeated purchase requests do not create duplicate records.

### Sales

- [ ] Sales can be created.
- [ ] Sale completion deducts stock correctly.
- [ ] Sale cancellation restores stock according to the business rules.
- [ ] Invoice information is generated and displayed correctly.

### Notifications and reports

- [ ] Low-stock notifications appear for intended users.
- [ ] Notification read status works correctly.
- [ ] Inventory reports return expected values.
- [ ] Purchase and sales reports return expected values.

### Operational checks

- [ ] Application logs contain no unhandled errors.
- [ ] No secret values are exposed in logs or error pages.
- [ ] Database records persist across application restarts.
- [ ] Database backup and recovery arrangements are confirmed.

## 10. Production readiness and maintenance

A successful deployment does not automatically make the system suitable for real pharmacy operations.

Before operational use, assess:

- Data privacy and access controls for patient information.
- Database backup frequency and recovery objectives.
- Monitoring and alerting for application and database failures.
- Secure handling of credentials and other secrets.
- Database and application performance.
- Availability requirements and hosting capacity.
- Audit-log retention and access restrictions.
- Procedures for updates, incidents, and recovery.

The initial Render deployment should be treated as a controlled demonstration environment until these requirements have been addressed and verified.

## 11. Future deployment improvements

The following improvements are planned as the project evolves:

- Separate React and Tailwind frontend deployment.
- Django REST Framework API integration.
- More comprehensive automated deployment and release processes.
- Improved application monitoring and error reporting.
- Persistent media storage if required.
- AI-assisted pharmacy inventory analysis and demand forecasting.
- RAG-based clinical decision support using reviewed knowledge sources, with professional oversight.

These are future enhancements and should not be interpreted as currently deployed capabilities.
