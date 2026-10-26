# Local Development Setup

This guide explains how to set up and run the Pharmacy Management System locally for development.

## 1. Prerequisites

Install the following:

- Git
- Python 3.12
- PostgreSQL
- A terminal and code editor

## 2. Clone the repository

```bash
git clone https://github.com/mashasadiq/pharmacy-management-system.git
cd pharmacy-management-system
```

## 3. Create and activate a virtual environment

Navigate to the backend directory:

```bash
cd backend
```

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install dependencies

Upgrade pip and install the project's pinned dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Configure environment variables

Create a `.env` file inside the `backend/` directory.

Add the following variables, replacing the placeholders with your local configuration:

```dotenv
SECRET_KEY=your-local-secret-key
DEBUG=True

DB_NAME=your_local_database_name
DB_USER=your_local_database_user
DB_PASSWORD=your_local_database_password
DB_HOST=localhost
DB_PORT=5432
```

The application loads these variables using `python-dotenv`.

**Important:**
- Never commit `.env` to version control.
- Never share production credentials.
- Use a dedicated local development database.
- Keep `DEBUG=False` in production.

## 6. Configure PostgreSQL

Ensure PostgreSQL is installed and running.

Create a PostgreSQL database and database user matching the values configured in your `.env` file.

The Django application connects to PostgreSQL using the `psycopg` driver.

## 7. Apply database migrations

With the virtual environment active and PostgreSQL configured, run:

```bash
python manage.py check
python manage.py showmigrations
python manage.py migrate
```

## 8. Create an administrator account

Create a Django superuser:

```bash
python manage.py createsuperuser
```

The custom user model defaults to the `PHARMACIST` application role. Creating a superuser does not automatically assign the `ADMIN` application role.

After creating the account:

1. Start the development server.
2. Open `/admin/` and log in using the superuser credentials.
3. Locate the account under Users.
4. Change its application role to `ADMIN`.
5. Save the changes.

## 9. Run automated tests

Run the full test suite:

```bash
python manage.py test
```

You can also run tests for an individual application:

```bash
python manage.py test inventory
```

Resolve test failures before considering the changes ready for integration or deployment.

## 10. Start the development server

```bash
python manage.py runserver
```

Open the application at:

http://127.0.0.1:8000/

## 11. Static files and deployment checks

For production-oriented static file preparation and configuration checks, run:

```bash
python manage.py collectstatic --noinput
python manage.py check --deploy
```

These commands are primarily relevant when preparing the application for deployment. The deployment check may report warnings until production settings are configured.

Review each warning rather than suppressing it blindly.

## Troubleshooting

- **Database connection error:** Confirm PostgreSQL is running and that the database name, username, password, host and port match your `.env` configuration.
- **Missing environment variables:** Confirm `backend/.env` exists and contains the required variable names.
- **Migration errors:** Inspect migration status using `python manage.py showmigrations`. Do not delete migration files as a shortcut.
- **Static files missing:** Check `STATIC_URL`, static file configuration and the deployment static-file serving setup.
- **Disallowed host error:** Check `ALLOWED_HOSTS` in `config/settings.py` and ensure the host being used is allowed. Avoid permissive wildcard settings in production.
- **Permission errors:** Verify the user's application role as well as their Django staff and superuser permissions.
