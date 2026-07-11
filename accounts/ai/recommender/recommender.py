from qdrant_client.models import PointStruct

from accounts.models import Job

from .embedding import get_embedding
from .vector_db import client, COLLECTION_NAME, ensure_collection


def job_to_text(job):
    return f"""
    Job Title: {job.title}
    Required Skills: {job.job_skills}
    Experience Level: {job.experience}
    Location: {job.location}
    Employment Type: {job.employment_type}
    Job Description: {job.description}
    Company: {job.company.company_name}
    """


def index_job(job):
    ensure_collection()
    text = job_to_text(job)
    vector = get_embedding(text)
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=job.id,
                vector=vector.tolist(),
                payload={
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company.company_name,
                    "location": job.location,
                },
            )
        ],
    )


def remove_job(job_id):
    ensure_collection()
    client.delete(collection_name=COLLECTION_NAME, points_selector=[job_id])


def reindex_all_jobs():
    count = 0
    for job in Job.objects.select_related("company").all():
        index_job(job)
        count += 1
    return count


def profile_to_text(profile):
    resume = getattr(profile, "resume", None)
    skills, education, experience = "", "", ""

    if resume:
        skills = ", ".join(resume.skills.values_list("skill_name", flat=True))
        education = " ".join(resume.educations.values_list("degree", flat=True))
        experience = " ".join(resume.experiences.values_list("job_title", flat=True))

    return f"""
    Skills: {skills}
    Summary: {profile.summary or ""}
    Education: {education}
    Experience: {experience}
    """


def recommend_jobs(profile_text, limit=10):
    if not profile_text or not profile_text.strip():
        return []

    ensure_collection()
    vector = get_embedding(profile_text)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector.tolist(),
        limit=limit,
        with_payload=True,
    )
    return results.points


def get_recommended_jobs(profile, applied_job_ids=None, limit=10):
    applied_job_ids = set(applied_job_ids or [])

    profile_text = profile_to_text(profile)

    # over-fetch so that after removing applied jobs we still have `limit` left
    results = recommend_jobs(profile_text, limit=limit * 3)

    job_ids = [
        p.payload["job_id"]
        for p in results
        if p.payload and "job_id" in p.payload
        and p.payload["job_id"] not in applied_job_ids
    ]

    if not job_ids:
        return Job.objects.none()

    job_ids = job_ids[:limit]

    job_scores = {
        p.payload["job_id"]: p.score
        for p in results
        if p.payload and "job_id" in p.payload
    }

    jobs = list(
        Job.objects.select_related("company").filter(id__in=job_ids, status="Open")
    )

    for job in jobs:
        job.match_score = normalize_score(job_scores.get(job.id, 0))

    jobs.sort(key=lambda x: job_ids.index(x.id))
    return jobs

def normalize_score(raw_score, floor=0.2, ceiling=0.75):
    """
    Cosine similarity from sentence embeddings rarely exceeds ~0.75
    even for excellent matches. Rescale the realistic range onto 0-100
    so the displayed percentage actually reflects match quality.
    """
    score = (raw_score - floor) / (ceiling - floor)
    score = max(0.0, min(1.0, score))  # clip to 0-1
    return round(score * 100, 1)