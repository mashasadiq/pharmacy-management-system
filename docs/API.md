# API Documentation

## 1. Overview

The Pharmacy Management System currently uses Django views and templates for its main user interface. A limited number of views return JSON responses to support asynchronous operations such as drug searches, sales processing and purchase recording.

Django REST Framework (DRF) is included in the project dependencies, but a complete REST API using DRF serializers, API views or viewsets has not yet been implemented.

This document describes the existing JSON endpoints and outlines the proposed API architecture for future development.

## 2. Current API Implementation

The existing JSON endpoints are implemented using Django's `JsonResponse`.

They are protected using Django authentication or the project's `admin_required` decorator. They are not currently a token-based API.

### 2.1 Inventory endpoints

| Endpoint | Method | Access | Description |
|---|---|---|---|
| `/inventory/search/` | GET | Authenticated users | Searches drugs by name, generic name, brand or barcode. |

**Search request**

```http
GET /inventory/search/?q=paracetamol
```

**Successful response**

```json
{
  "drugs": [
    {
      "id": 1,
      "name": "Paracetamol",
      "generic_name": "Paracetamol",
      "brand": "Example Brand",
      "barcode": "123456",
      "selling_price": "50.00",
      "stock": 100,
      "minimum_stock": 10
    }
  ]
}
```

An empty search query returns:

```json
{
  "drugs": []
}
```

### 2.2 Sales endpoints

| Endpoint | Method | Access | Description |
|---|---|---|---|
| `/sales/api/create/` | POST | Authenticated users | Creates a pending sale without deducting inventory stock. |
| `/sales/api/products/search/` | GET | Authenticated users | Searches in-stock drugs for the POS interface. |
| `/sales/<sale_id>/complete/` | POST | Authenticated users | Completes a pending sale and deducts inventory stock. |
| `/sales/<sale_id>/edit/` | POST | Authenticated users | Updates the items of a pending sale. |
| `/sales/<sale_id>/delete/` | POST | Administrators | Deletes a pending sale. |
| `/sales/<sale_id>/cancel/` | POST | Administrators | Cancels a completed sale and restores inventory stock. |

**Create sale request**

```http
POST /sales/api/create/
Content-Type: application/json
```

```json
{
  "patient": 1,
  "payment_method": "CASH",
  "items": [
    {
      "drug_id": 1,
      "quantity": 2
    }
  ]
}
```

The payment method must match one of the choices defined by the Sale model.

**Successful response**

```json
{
  "message": "Sale created successfully.",
  "sale_id": 1,
  "total_amount": "100.00"
}
```

Creating a sale records it as pending. Stock is not deducted until the sale is completed.

**Search POS products**

```http
GET /sales/api/products/search/?q=paracetamol
```

The endpoint searches in-stock drugs by name, generic name, brand or barcode. An exact barcode match is prioritised. Otherwise, the search returns up to 20 matching products.

**Successful response**

```json
{
  "products": [
    {
      "id": 1,
      "name": "Paracetamol",
      "price": "50.00",
      "stock": 100,
      "barcode": "123456"
    }
  ]
}
```

**Complete sale**

```http
POST /sales/<sale_id>/complete/
```

A successful response includes the generated invoice number:

```json
{
  "message": "Sale completed successfully.",
  "sale_id": 1,
  "invoice_number": "INV-20261022-000001"
}
```

Only pending sales can be completed. The operation validates the sale items, deducts stock and records an audit event.

**Edit pending sale request**

```http
POST /sales/<sale_id>/edit/
Content-Type: application/json
```

```json
{
  "items": [
    {
      "drug_id": 1,
      "quantity": 3
    }
  ]
}
```

The endpoint updates the items and recalculates the total of a pending sale without deducting inventory stock.

**Delete pending sale**

```http
POST /sales/<sale_id>/delete/
```

Only administrators can delete pending sales.

**Cancel completed sale**

```http
POST /sales/<sale_id>/cancel/
```

Only administrators can cancel completed sales. The cancellation operation restores the inventory stock and records an audit event.

### 2.3 Purchase endpoints

| Endpoint | Method | Access | Description |
|---|---|---|---|
| `/purchases/api/create/` | POST | Administrators | Records a purchase and updates inventory stock. |

**Create purchase request**

```http
POST /purchases/api/create/
Content-Type: application/json
```

```json
{
  "idempotency_key": "unique-request-identifier",
  "drug_id": 1,
  "supplier_id": 1,
  "quantity": 20,
  "cost_price": "35.50",
  "purchase_date": "2026-10-22",
  "invoice_number": "SUP-INV-001",
  "remarks": "Stock replenishment"
}
```

The `idempotency_key` is required to prevent duplicate purchase submissions.

**Successful response for a new purchase**

```json
{
  "message": "Purchase recorded successfully.",
  "purchase_id": 1,
  "purchase_reference": "PUR-20261022-000001",
  "supplier_invoice_number": "SUP-INV-001",
  "drug": "Paracetamol",
  "quantity": 20,
  "new_stock": 120,
  "created": true
}
```

If the same idempotency key is submitted again, the existing purchase is returned rather than recording another purchase. The response then indicates `"created": false`.

The endpoint validates the submitted data and delegates purchase creation to the purchase service, which handles the inventory update and related operations.

## 3. Authentication and Authorization

The existing JSON endpoints use Django's session-based authentication.

- `login_required` restricts access to authenticated users.
- `admin_required` restricts designated operations to administrators.
- Sale deletion and cancellation explicitly check that the logged-in user's role is `ADMIN`.
- Purchase creation is protected by `admin_required`.

The current implementation does not provide a separate token-based authentication mechanism for external API clients.

POST requests are subject to Django's CSRF protection. Clients using session authentication must provide the appropriate CSRF token.

## 4. Common Response and Error Handling

The existing endpoints return JSON responses for successful operations and errors.

Observed HTTP status codes include:

| Status code | Meaning in the current implementation |
|---|---|
| `200 OK` | Successful operation or repeated purchase submission. |
| `201 Created` | New purchase successfully recorded. |
| `400 Bad Request` | Invalid input or an operation that cannot be performed in the current state. |
| `403 Forbidden` | User is not authorized to perform an operation. |
| `405 Method Not Allowed` | Unsupported HTTP method. |
| `500 Internal Server Error` | Unexpected server-side error. |

Error responses generally use the following structure:

```json
{
  "error": "Description of the error."
}
```

The precise response structure depends on the endpoint.

## 5. Application URL Prefixes

The following application URL prefixes are configured in the main Django URL configuration:

| Application | URL prefix |
|---|---|
| Accounts | `/accounts/` |
| Patients | `/patients/` |
| Inventory | `/inventory/` |
| Dashboard | `/dashboard/` |
| Sales | `/sales/` |
| Purchases | `/purchases/` |
| Reports | `/reports/` |
| Notifications | `/notifications/` |
| Django Admin | `/admin/` |

These prefixes include both template-based pages and, where implemented, JSON endpoints.

## 6. Planned REST API Architecture

As the system evolves towards a React and Tailwind CSS frontend, Django REST Framework will provide a structured backend API.

The proposed architecture is:

```text
React + Tailwind CSS
          |
          | HTTP / JSON
          |
Django REST Framework
          |
          | Serializers and API Views
          |
Business Logic / Services
          |
          | ORM
          |
PostgreSQL Database
```

The existing Django business logic and services will be reused where appropriate rather than duplicating critical operations in API views.

### 6.1 Planned API resources

| Resource | Planned functionality |
|---|---|
| Authentication | Login, logout and user management. |
| Users | User profiles and role management. |
| Drugs | Drug creation, listing, updating and searching. |
| Suppliers | Supplier management. |
| Patients | Patient registration and management. |
| Sales | Sale creation, completion, editing and cancellation. |
| Purchases | Purchase recording and history. |
| Reports | Inventory, sales and purchase reports. |
| Notifications | Notification listing and read-status management. |
| Audit Logs | Tracking important system operations. |

These are proposed API resources, not a statement that all corresponding REST endpoints currently exist.

## 7. API Design Principles

Future API development should follow these principles:

- **RESTful resource design:** Use resource-oriented URLs and appropriate HTTP methods.
- **JSON communication:** Use JSON for request and response bodies.
- **Validation:** Validate incoming data before performing database operations.
- **Authentication:** Protect endpoints against unauthorized access.
- **Role-based permissions:** Enforce administrator and pharmacist permissions at the API level.
- **Business logic separation:** Keep complex operations in reusable service functions.
- **Error handling:** Return consistent and meaningful error responses.
- **Database integrity:** Use transactions and appropriate locking for stock-sensitive operations.
- **Documentation:** Document endpoint methods, request fields, response structures and permissions.

## 8. API Versioning

When the structured REST API is introduced, versioning will be used to support future changes without unnecessarily breaking existing clients.

The proposed base URL is:

```text
/api/v1/
```

Example:

```text
/api/v1/drugs/
/api/v1/patients/
/api/v1/sales/
/api/v1/purchases/
```

Versioning will be introduced as part of the future DRF implementation.

## 9. Future Security Considerations

Before exposing the API to external clients or deploying it to production:

- Enforce HTTPS.
- Use an appropriate authentication mechanism for the intended clients.
- Apply role-based permissions to sensitive operations.
- Retain CSRF protection when using session authentication.
- Validate and sanitize incoming data.
- Protect sensitive patient information.
- Apply request throttling where appropriate.
- Avoid exposing internal exception details in production responses.
- Test authentication, authorization and input validation.

## 10. Current Implementation Status

The project currently has a working Django template-based application with selected JSON endpoints for inventory searching, POS operations and purchase recording.

The complete REST API, including DRF serializers, API views, structured authentication and versioned endpoints, remains planned future work.
