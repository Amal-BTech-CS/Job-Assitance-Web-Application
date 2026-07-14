from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from accounts.ai.recommender.recommender import index_job, remove_job
from accounts.models import CompanyProfile, Job,Application
from accounts.ai.email_notify import send_status_email


@login_required
def create_job(request):

    company, created = CompanyProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        Job.objects.create(

            company=company,

            title=request.POST.get("title"),

            description=request.POST.get("description"),

            location=request.POST.get("location"),

            salary=request.POST.get("salary"),

            experience=request.POST.get("experience"),

            employment_type=request.POST.get("employment_type"),

            job_skills=request.POST.get("job_skills"),

            status=request.POST.get("status", "Open")
        )
        try:
            index_job(job)
        except Exception as e:
            print("Job indexing error:", e)
        return redirect(
            "manage_jobs"
        )

    return render(
        request,
        "accounts/create_job.html"
    )


@login_required
def manage_jobs(request):

    company, created = CompanyProfile.objects.get_or_create(
        user=request.user
    )

    jobs = (
        Job.objects
        .filter(company=company)
        .annotate(applicant_count=Count("applications"))
    )
    
    return render(

        request,

        "accounts/manage_jobs.html",

        {
            "jobs": jobs
        }

    )


@login_required
def edit_job(request, id):

    company = CompanyProfile.objects.get(
        user=request.user
    )

    job = Job.objects.get(
        id=id,
        company=company
    )

    if request.method == "POST":

        job.title = request.POST.get("title")

        job.description = request.POST.get("description")

        job.location = request.POST.get("location")

        job.salary = request.POST.get("salary")

        job.experience = request.POST.get("experience")

        job.employment_type = request.POST.get("employment_type")

        job.job_skills = request.POST.get("job_skills")
        job.status = request.POST.get("status")
        job.save()
        try:
            index_job(job)
        except Exception as e:
            print("Job indexing error:", e)
        return redirect(
            "manage_jobs"
        )

    return render(

        request,

        "accounts/edit_job.html",

        {

            "job": job

        }

    )


@login_required
def delete_job(request, id):

    company = CompanyProfile.objects.get(
        user=request.user
    )

    job = Job.objects.get(

        id=id,

        company=company

    )

    
    job_id = job.id
    job.delete()

    try:
        remove_job(job_id)
    except Exception as e:
        print("Job un-indexing error:", e)
    return redirect(
        "manage_jobs"
    )

from django.core.paginator import Paginator
from django.db.models import Q, Case, When, IntegerField, Value
from django.db.models.functions import Greatest
def browse_jobs(request):
    query = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    employment_type = request.GET.get("type", "").strip()

    jobs = Job.objects.filter(status="Open").select_related("company")

    if query:
        keywords = query.split()
        search_query = Q()
        relevance = Value(0, output_field=IntegerField())

        for keyword in keywords:
            search_query |= (
                Q(title__icontains=keyword) |
                Q(job_skills__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(company__company_name__icontains=keyword)
            )

            # Weight matches by field importance:
            # title match >> skills match >> company match >> description match.
            # Summed per keyword so multi-word queries reward jobs matching
            # more of the query, not just any single word.
            relevance = relevance + (
                Case(When(title__icontains=keyword, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                Case(When(job_skills__icontains=keyword, then=Value(6)), default=Value(0), output_field=IntegerField()) +
                Case(When(company__company_name__icontains=keyword, then=Value(3)), default=Value(0), output_field=IntegerField()) +
                Case(When(description__icontains=keyword, then=Value(1)), default=Value(0), output_field=IntegerField())
            )

        jobs = (
            jobs.filter(search_query)
            .annotate(relevance=relevance)
            .distinct()
            .order_by("-relevance", "-created_at")
        )
    else:
        jobs = jobs.order_by("-created_at")

    if location:
        jobs = jobs.filter(location__icontains=location)

    if employment_type:
        jobs = jobs.filter(employment_type__iexact=employment_type)

    paginator = Paginator(jobs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "jobs": page_obj,
        "page_obj": page_obj,
        "query": query,
        "location": location,
        "employment_type": employment_type,
    }

    return render(request, "accounts/browse_jobs.html", context)
@login_required
def job_detail(request, job_id):

    job = get_object_or_404(Job, id=job_id)

    already_applied = Application.objects.filter(
        applicant__user=request.user,
        job=job
    ).exists()

    return render(request, "accounts/job_detail.html", {
        "job": job,
        "already_applied": already_applied,
    })
