from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Patient
from audit_logs.models import AuditLog

from .forms import PatientForm



@login_required
def create_patient(request):
    """Register a patient and automatically record the logged-in user."""
    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.save()

            return render(
                request,
                "patients/patient_detail.html",
                {"patient": patient},
            )

    else:
        form = PatientForm()

    return render(
        request,
        "patients/patient_form.html",
        {"form": form},
    )


@login_required
def patient_list(request):
    """Display patients and allow searching by key identifying details."""
    query = request.GET.get("q", "").strip()

    patients = Patient.objects.select_related(
        "created_by"
    )

    if query:
        patients = patients.filter(
            Q(patient_number__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone__icontains=query)
        )

    return render(
        request,
        "patients/patient_list.html",
        {
            "patients": patients,
            "query": query,
        },
    )



@login_required
def patient_detail(request, patient_id):
    """Display patient information together with their sales history."""
    patient = get_object_or_404(Patient, id=patient_id)

    sales = patient.sales.select_related(
        "pharmacist"
    ).prefetch_related(
        "items__drug"
    )

    # Record administrator access to patient clinical history.
    if request.user.role == "ADMIN":
        AuditLog.objects.create(
            user=request.user,
            action="VIEW",
            table_name="Patient",
            record_id=patient.id,
            description=(
                f"Administrator viewed clinical history "
                f"for patient {patient.patient_number}."
            ),
            ip_address=request.META.get("REMOTE_ADDR"),
        )

    return render(
        request,
        "patients/patient_detail.html",
        {
            "patient": patient,
            "sales": sales,
        },
    )
