from .embedding import get_embedding
from .vector_db import client, COLLECTION_NAME
from qdrant_client.models import PointStruct
from accounts.models import Job


# ----------------------------
# JOB → TEXT
# ----------------------------
def job_to_text(job):
    return f"""
    Job Title: {job.title}
    Required Skills: {job.skills}
    Experience Level: {job.experience}
    Location: {job.location}
    Employment Type: {job.employment_type}
    Job Description: {job.description}
    Company: {job.company.company_name}
    """


# ----------------------------
# INDEX JOB INTO QDRANT
# ----------------------------
def index_job(job):
    text = job_to_text(job)
    vector = get_embedding(text)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=job.id,
                vector=vector,
                payload={
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company.company_name,
                    "location": job.location,
                }
            )
        ]
    )


# ----------------------------
# PROFILE → TEXT
# ----------------------------
def profile_to_text(profile):
    education = " ".join(profile.educations.values_list("degree", flat=True))
    experience = " ".join(profile.experiences.values_list("job_title", flat=True))

    return f"""
    Skills: {profile.skills or ""}
    Summary: {profile.summary or ""}
    Education: {education}
    Experience: {experience}
    """


# ----------------------------
# VECTOR SEARCH (FIXED FOR NEW QDRANT)
# ----------------------------
def recommend_jobs(profile_text, limit=10):

    if not profile_text:
        return []

    vector = get_embedding(profile_text)

    # ✅ NEW QDRANT API (IMPORTANT FIX)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit,
        with_payload=True
    )

    return results.points


# ----------------------------
# FINAL OUTPUT (ORDER PRESERVED + SAFE + SCORE ADDED)
# ----------------------------
def get_recommended_jobs(profile):

    profile_text = profile_to_text(profile)

    results = recommend_jobs(profile_text)

    # store both order + score
    job_scores = {}

    job_ids = [
        point.payload["job_id"]
        for point in results
        if point.payload and "job_id" in point.payload
    ]

    # build score map
    for point in results:
        if point.payload and "job_id" in point.payload:
            job_scores[point.payload["job_id"]] = point.score

    if not job_ids:
        return Job.objects.none()

    jobs = list(Job.objects.filter(id__in=job_ids))

    # attach score to each job
    for job in jobs:
        job.match_score = job_scores.get(job.id, 0) * 100  # percentage

    # preserve ranking order (your original logic kept)
    jobs.sort(key=lambda x: job_ids.index(x.id))

    return jobs