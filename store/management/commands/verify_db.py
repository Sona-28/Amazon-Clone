from django.core.management.base import BaseCommand

from store.models import Category


class Command(BaseCommand):
    help = "Write a category row, read it back, then delete it."

    def handle(self, *args, **options):
        slug = "db-connection-probe"
        Category.objects.filter(slug=slug).delete()
        created = Category.objects.create(
            name="DB Connection Probe",
            slug=slug,
            description="Temporary row used to confirm PostgreSQL read and write.",
        )
        loaded = Category.objects.get(pk=created.pk)
        loaded.delete()
        remaining = Category.objects.filter(slug=slug).count()
        if remaining != 0 or loaded.name != "DB Connection Probe":
            raise SystemExit("PostgreSQL read/write check failed.")
        self.stdout.write(self.style.SUCCESS("PostgreSQL read/write check passed."))
