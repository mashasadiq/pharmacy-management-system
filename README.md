# Pharmacy Management System

A Django-based web application for managing day-to-day operations in a **single pharmacy**. The system provides tools for managing medicines, inventory, suppliers, patients, purchases, sales, notifications, and operational reports.

The current MVP uses Django's server-rendered templates, PostgreSQL, HTML, CSS, and JavaScript.

> **Project status:** MVP development and deployment preparation. The current application is a Django-based system. A separate React frontend and fully integrated REST API are planned improvements, not requirements for running the current MVP.

## Current capabilities

- User authentication with Admin and Pharmacist roles
- Role-based access to pharmacy operations
- Drug and inventory management
- Supplier management
- Patient registration and records
- Point of Sale (POS) and sales processing
- Purchase recording and stock receiving
- Low-stock notifications
- Sales and operational reports
- Audit logging for selected system activities
- Role-specific dashboards

The current feature set focuses on the operational needs of a single pharmacy. It does not yet represent a complete hospital pharmacy management system.

## Technology stack

| Area | Technology |
|---|---|
| Backend and web framework | Python, Django |
| Database | PostgreSQL |
| Database driver | psycopg |
| User interface | Django templates, HTML, CSS, JavaScript |
| Development environment | Python virtual environment |

Django REST Framework is included as a project dependency, but a fully integrated REST API is not yet part of the current application. React and Tailwind CSS are also planned rather than implemented.

See `backend/requirements.txt` for the pinned Python dependencies.

## Repository structure

```text
pharmacy-management-system/
├── backend/
│   ├── accounts/
│   ├── audit_logs/
│   ├── config/
│   ├── dashboard/
│   ├── fixtures/
│   ├── inventory/
│   ├── notifications/
│   ├── patients/
│   ├── prescriptions/
│   ├── purchases/
│   ├── reports/
│   ├── sales/
│   ├── suppliers/
│   ├── templates/
│   ├── tests/
│   ├── manage.py
│   └── requirements.txt
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── ERD.md
│   ├── PRD.md
│   └── SETUP.md
├── frontend/
├── .gitignore
└── README.md
```

The `frontend/` directory currently contains preliminary scaffolding. It is not yet a completed React application. The main user interface is served by Django templates.

## Getting started

For environment preparation, database configuration, and instructions for running the application locally, see the [Local Setup Guide](docs/SETUP.md).

## Documentation

- [Product Requirements Document](docs/PRD.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [Entity Relationship Diagram](docs/ERD.md)
- [Local Setup Guide](docs/SETUP.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [API Documentation and Planned Integration](docs/API.md)

## Planned direction

The project will evolve beyond its current single-pharmacy MVP toward a more comprehensive hospital pharmacy management system.

Planned areas of development include:

1. **Deployment and reliability:** Deploy and validate the current MVP, improve production configuration, strengthen security, and establish reliable backup and recovery procedures.
2. **Frontend development:** Build a separate React frontend using Tailwind CSS.
3. **API integration:** Develop documented Django REST Framework endpoints to support frontend integration and future external integrations.
4. **Clinical records:** Extend patient management to support appropriate clinical notes and health records, with strict access controls and privacy safeguards.
5. **RAG-supported clinical decision support:** Explore retrieval-augmented generation using expert-reviewed medical and pharmaceutical knowledge to assist healthcare professionals. This is intended to support, not replace, professional clinical judgment.
6. **Machine-learning inventory intelligence:** Develop demand forecasting and replenishment recommendations to help reduce medicine stock-outs, wastage, and overstocking, particularly for slow-moving medicines.

These are planned improvements and should not be interpreted as features already available in the current MVP.

## Important data and deployment notice

This project is under development and should not be treated as a production-ready system for managing real patient or pharmacy operations.

Before production use, the system requires appropriate access controls, privacy and data-protection safeguards, secure and durable database storage, tested backups and recovery procedures, monitoring, and compliance with applicable Kenyan laws and regulations. An experimental or free-tier deployment should not be used as the sole system for critical pharmacy operations.
