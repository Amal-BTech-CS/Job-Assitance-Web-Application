import logging

from qdrant_client.models import PointStruct

from accounts.models import Job

from .embedding import get_embedding
from .vector_db import client, COLLECTION_NAME, ensure_collection

logger = logging.getLogger(__name__)


def job_to_text(job):
    company_name = job.company.company_name if job.company_id else "Unknown"
    return f"""
    Job Title: {job.title}
    Required Skills: {job.job_skills}
    Experience Level: {job.experience}
    Location: {job.location}
    Employment Type: {job.employment_type}
    Job Description: {job.description}
    Company: {company_name}
    """


def index_job(job):
    """
    Embeds and upserts a single job into Qdrant.
    Never raises — indexing failures must not break Job save/create.
    """
    try:
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
                        "company": job.company.company_name if job.company_id else "",
                        "location": job.location,
                        "status": job.status,
                    },
                )
            ],
        )
    except Exception:
        logger.exception("Failed to index job %s into Qdrant", job.id)


def remove_job(job_id):
    try:
        ensure_collection()
        client.delete(collection_name=COLLECTION_NAME, points_selector=[job_id])
    except Exception:
        logger.exception("Failed to remove job %s from Qdrant", job_id)


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


MIN_RELEVANCE_SCORE = 0.2   # Qdrant-side floor — matches normalize_score's floor
MIN_MATCH_PERCENTAGE = 40.0  # only show jobs whose normalized match_score >= this


def recommend_jobs(profile_text, limit=10):
    if not profile_text or not profile_text.strip():
        return []

    ensure_collection()
    vector = get_embedding(profile_text)
    try:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector.tolist(),
            limit=limit,
            with_payload=True,
            score_threshold=MIN_RELEVANCE_SCORE,  # Qdrant filters weak matches server-side
        )
    except Exception:
        logger.exception("Qdrant query_points failed")
        return []
    return results.points


def get_recommended_jobs(profile, applied_job_ids=None, limit=10):
    applied_job_ids = set(applied_job_ids or [])
    profile_text = profile_to_text(profile)

    # Over-fetch generously — we still need to survive three filters
    # after this: applied-job removal, stale/closed-job removal,
    # and the 40%-match-score cutoff.
    results = recommend_jobs(profile_text, limit=limit * 5)

    # Preserve vector-search order + scores before any DB filtering
    ordered_candidates = [
        (p.payload["job_id"], p.score)
        for p in results
        if p.payload and "job_id" in p.payload
        and p.payload["job_id"] not in applied_job_ids
    ]

    if not ordered_candidates:
        return Job.objects.none()

    candidate_ids = [job_id for job_id, _ in ordered_candidates]
    score_by_id = dict(ordered_candidates)

    # Filter against live DB status first, so closed/stale-in-Qdrant
    # jobs don't silently eat into the result set.
    open_jobs = {
        job.id: job
        for job in Job.objects.select_related("company").filter(
            id__in=candidate_ids, status="Open"
        )
    }

    ranked_ids = [jid for jid in candidate_ids if jid in open_jobs]

    jobs = []
    for jid in ranked_ids:
        job = open_jobs[jid]
        score = normalize_score(score_by_id[jid])

        if score < MIN_MATCH_PERCENTAGE:
            continue  # below 40% — not a real match, don't show it

        job.match_score = score
        jobs.append(job)

        if len(jobs) >= limit:
            break

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