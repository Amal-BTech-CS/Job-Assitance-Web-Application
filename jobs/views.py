from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from accounts.ai.recommender.recommender import index_job, remove_job
from accounts.models import CompanyProfile, Job


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


def browse_jobs(request):

    query = request.GET.get("q", "")
    location = request.GET.get("location", "")
    employment_type = request.GET.get("type", "")

    jobs = Job.objects.filter(status="Open")

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(job_skills__icontains=query) |
            Q(description__icontains=query)
        )

    if location:
        jobs = jobs.filter(location__icontains=location)

    if employment_type:
        jobs = jobs.filter(employment_type__iexact=employment_type)

    return render(request, "accounts/browse_jobs.html", {
        "jobs": jobs,
        "query": query
    })
