# Product Requirements Document

## 1. Product summary

The Pharmacy Management System is a web application designed to support common pharmacy operations, including medicine inventory management, supplier records, patient registration, purchases, sales, notifications, and operational reporting.

The current implementation is a single-pharmacy Django-based MVP using PostgreSQL and Django templates.

This document distinguishes existing capabilities from planned enhancements so that future requirements are not mistaken for delivered functionality.

## 2. Problem statement

Manual or fragmented pharmacy processes can make it difficult to maintain accurate stock records, trace transactions, identify low-stock medicines, and review sales activity.

The system aims to centralize these workflows, improve the consistency of operational records, and support more efficient pharmacy management.

## 3. Users and roles

### Admin

A privileged user responsible for administrative operations, oversight, and restricted management functions.

### Pharmacist

A staff user responsible for permitted day-to-day pharmacy operations, including viewing inventory, registering patients, and processing sales.

Permissions must be enforced on the server side and tested for both authorized and unauthorized actions.

## 4. Current MVP scope

| Area | Requirement | Status |
|---|---|---|
| Authentication | Users can sign in and sign out | Implemented |
| Role access | Admin and Pharmacist roles have different permissions | Implemented; continue reviewing as features grow |
| Inventory | Maintain drug records and stock information | Implemented |
| Suppliers | Maintain supplier records through Django Admin for purchasing workflows | Implemented |
| Patients | Register, list, search, and view individual patient records | Implemented |
| Sales / POS | Record sales and sale items | Implemented |
| Stock deduction | Deduct stock when a sale is completed | Implemented |
| Sale cancellation | Restore stock according to cancellation rules | Implemented with role restrictions |
| Purchases | Record received stock and purchase details | Implemented |
| Duplicate purchase protection | Prevent duplicate processing of retried purchase submissions | Implemented |
| Notifications | Display user notifications, including low-stock alerts | Implemented |
| Audit logging | Record selected important operations, with records accessible through Django Admin | Implemented |
| Reports | Provide inventory, low-stock, expired-drug, patient, purchase, daily sales, and monthly sales reporting | Implemented routes; individual report behaviour should be maintained and tested |
| Prescriptions | Manage prescription lifecycle and dispensing | Not complete; paused/future scope |

## 5. Quality requirements

- **Security:** Authenticate users, enforce role permissions server-side, protect state-changing requests against CSRF, and keep secrets outside source control.
- **Data integrity:** Validate quantities and prices, use database transactions for stock-changing operations, and prevent duplicate purchase submissions.
- **Usability:** Provide clear navigation, useful validation messages, and understandable access-denied responses.
- **Maintainability:** Keep business rules testable, use migrations for schema changes, and maintain accurate setup and deployment documentation.
- **Reliability:** Run automated tests before deployment and maintain a tested database backup and recovery process before production use.
- **Privacy:** Restrict access to patient information to authorized users and minimize exposure of personal data.

## 6. Out of scope for the current MVP

- A completed React/Tailwind frontend.
- A complete and stable REST API covering all application workflows.
- Production-grade AI/ML forecasting or RAG recommendations.
- A complete prescription and dispensing workflow.
- Advanced clinical history and clinical decision-support functionality.
- Claims of regulatory certification or suitability for autonomous clinical decision-making.

## 7. Future enhancements

1. **Deployment and reliability:** Deploy and stabilize the existing Django application, improving security, monitoring, backups, and operational documentation.
2. **Frontend development:** Develop a separate React and Tailwind frontend.
3. **API integration:** Build and test Django REST Framework endpoints to support frontend communication.
4. **Clinical records:** Introduce patient clinical notes and history with strict authorization and privacy controls.
5. **RAG-based clinical decision support:** Explore retrieval-augmented assistance using reliable, expert-reviewed medical and pharmaceutical knowledge to support healthcare professionals, not replace their judgment.
6. **Machine learning for inventory management:** Develop demand forecasting, stock-out risk prediction, and replenishment recommendations to help reduce medicine shortages, overstocking, expiry, and wastage.

## 8. Acceptance principles

A feature is considered complete only when:

- Its expected behaviour is implemented.
- Appropriate access controls are enforced.
- Relevant automated tests pass.
- Its documentation accurately reflects the implemented behaviour.

The existence of a model, URL, template, or application module alone does not establish that a complete user-facing workflow is available.
