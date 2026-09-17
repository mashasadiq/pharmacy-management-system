# Database design
Pharmacy Management System Database Schema
1. accounts (Authentication)

Purpose: Who logs into the system.

User
User
----
id (PK)
username
password
first_name
last_name
email
phone_number
role (Administrator | Pharmacist)
is_active
date_joined
created_at
updated_at
Relationships
One User
    │
    ├── records many Purchases
    ├── records many Sales
    ├── creates many Patients
    └── creates many Prescriptions
2. suppliers

Purpose: Drug suppliers.

Supplier
Supplier
---------
id (PK)
company_name
contact_person
phone
email
address
city
country
is_active
created_at
updated_at

Relationship

One Supplier
      │
      ▼
Many Drugs
3. inventory

This is the heart of the system.

Drug
Drug
----
id (PK)
supplier (FK)

name
generic_name
brand

barcode
batch_number

category

unit

cost_price
selling_price

quantity_in_stock

minimum_stock

expiry_date

description

created_at
updated_at

Relationship

Supplier
      │
      ▼
Drug
4. purchases

Whenever new stock arrives.

Purchase
Purchase
---------
id (PK)

drug (FK)

supplier (FK)

received_by (FK User)

quantity

cost_price

purchase_date

invoice_number

remarks

created_at

Relationship

User
   │
   ▼
Purchase
      │
      ▼
Drug
5. patients

Patient records.

Patient
Patient
--------
id (PK)

patient_number

first_name

last_name

gender

date_of_birth

phone

email

address

created_by (FK User)

created_at
updated_at
6. prescriptions

Doctor prescriptions dispensed by the pharmacy.

Prescription
Prescription
------------
id (PK)

patient (FK)

pharmacist (FK User)

prescription_number

doctor_name

notes

status

created_at
PrescriptionItem

One prescription can contain many drugs.

PrescriptionItem
----------------

id (PK)

prescription (FK)

drug (FK)

quantity

dosage

duration

Relationship

Prescription
      │
      ▼
PrescriptionItem
      │
      ▼
Drug
7. sales
Sale
Sale
----

id (PK)

patient (FK)

pharmacist (FK User)

sale_date

total_amount

payment_method

status
SaleItem
SaleItem
--------

id (PK)

sale (FK)

drug (FK)

quantity

unit_price

subtotal

Relationship

Sale
   │
   ▼
SaleItem
   │
   ▼
Drug
8. reports

No database model needed.

Reason:

Reports are generated from:

Sales
Purchases
Drugs
Patients

They are queries, not stored data.

9. dashboard

No model needed.

Dashboard displays statistics.

Example

Today's Sales

Monthly Revenue

Low Stock

Expired Drugs

Number of Patients

These are calculated from existing tables.

10. notifications
Notification
Notification
------------

id (PK)

title

message

type

is_read

user (FK)

created_at

Examples

Drug expiring

Low stock

Purchase received

New prescription
11. audit_logs
AuditLog
AuditLog
--------

id (PK)

user (FK)

action

table_name

record_id

description

ip_address

timestamp

Example

Admin deleted Drug A

Pharmacist sold Amoxicillin

Admin updated Supplier
Complete Relationship Diagram
                 User
                  │
      ┌───────────┼────────────┐
      │           │            │
      ▼           ▼            ▼
 Purchase     Prescription    Sale
      │             │           │
      │             ▼           ▼
      │      PrescriptionItem  SaleItem
      │             │           │
      └─────────────┼───────────┘
                    │
                    ▼
                  Drug
                    ▲
                    │
                Supplier

Patient
   │
   ├────────────► Prescription
   │
   └────────────► Sale

Notification ─────► User

AuditLog ─────────► User
Which apps actually have models?
App	Model(s)
✅ accounts	User
✅ suppliers	Supplier
✅ inventory	Drug
✅ purchases	Purchase
✅ patients	Patient
✅ prescriptions	Prescription, PrescriptionItem
✅ sales	Sale, SaleItem
❌ dashboard	No models
❌ reports	No models
✅ notifications	Notification
✅ audit_logs	AuditLog