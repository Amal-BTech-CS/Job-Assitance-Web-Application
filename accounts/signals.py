from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from accounts.models import Job
from accounts.ai.recommender.recommender import index_job, remove_job


@receiver(post_save, sender=Job)
def sync_job_to_qdrant(sender, instance, created, **kwargs):
    """
    Fires after every Job.save().
    `created=True` only on the first save (i.e. brand new job) —
    we only want to index on creation, not on every field update.
    """
    if created:
        index_job(instance)


@receiver(post_delete, sender=Job)
def remove_job_from_qdrant(sender, instance, **kwargs):
    """
    Fires after a Job row is deleted from Postgres.
    Removes the matching point from Qdrant so it can't
    still surface in recommendations.
    """
    remove_job(instance.id)