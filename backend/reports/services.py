class ReportService:

    @staticmethod
    def daily_sales_report(report_date):
        return Sale.objects.filter(
            sale_date__date=report_date
        )

    @staticmethod
    def monthly_sales_report(year, month):
        return Sale.objects.filter(
            sale_date__year=year,
            sale_date__month=month
        )

    @staticmethod
    def inventory_report():
        return Drug.objects.all()

    @staticmethod
    def low_stock_report():
        return Drug.objects.filter(
            quantity_in_stock__lte=F("reorder_level")
        )

    @staticmethod
    def expired_drugs_report():
        return Drug.objects.filter(
            expiry_date__lt=date.today()
        )

    @staticmethod
    def patient_report():
        return Patient.objects.all()

    @staticmethod
    def purchase_report():
        return Purchase.objects.all()