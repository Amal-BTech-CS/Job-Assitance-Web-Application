from django.core.management.base import BaseCommand
from accounts.ai.recommender.recommender import reindex_all_jobs


class Command(BaseCommand):
    help = "Re-embeds every Job row into the Qdrant 'jobs' collection."

    def handle(self, *args, **options):
        count = reindex_all_jobs()
        self.stdout.write(self.style.SUCCESS(f"Indexed {count} job(s) into Qdrant."))