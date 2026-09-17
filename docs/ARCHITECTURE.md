# System architecture



dashboard/

├── views.py
├── urls.py
├── services.py #Instead of putting all business logic in views, create a service.
├── serializers.py
└── tests.py


reports/

├── views.py
├── urls.py
├── serializers.py
├── services.py #Create one service responsible for generating report data.
├── exports.py  
└── tests.py

<!-- Export Layer

A dedicated exports.py module can later handle:

PDF generation
Excel (.xlsx) exports
CSV exports

Separating export code from querying logic keeps the application easier to maintain. -->