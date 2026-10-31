"""Achica las fotos ya subidas que pasan de `core.images.MAX_SIDE` px.

Las fotos nuevas se achican al subirse (ver `core.images`); esto es para las
que ya estaban. Cada archivo se reescribe en el mismo lugar y con el mismo
nombre, así que las URLs no cambian y la base no se toca.

Reescribir pisa el original: haz un respaldo de la media antes (ver
docs/DEPLOY.md). Es idempotente: una foto ya achicada se salta.
"""
from django.core.management.base import BaseCommand

from core.images import shrink_stored
from homepage.models import HeroImage
from product.models import GalleryProduct, Product

SOURCES = (
    (Product, 'photo'),
    (GalleryProduct, 'photos'),
    (HeroImage, 'image'),
)


class Command(BaseCommand):
    help = 'Shrink stored product, gallery and hero photos larger than MAX_SIDE.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List what would be shrunk, without touching files.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        changed = skipped = failed = 0
        for model, field in SOURCES:
            for obj in model.objects.exclude(**{field: ''}).iterator():
                field_file = getattr(obj, field)
                try:
                    did = shrink_stored(field_file, dry_run=dry_run)
                except Exception as e:  # una foto rota no corta el resto
                    failed += 1
                    self.stderr.write(f'error {field_file.name}: {e}')
                    continue
                if did:
                    changed += 1
                    verb = 'achicaria' if dry_run else 'achicada'
                    self.stdout.write(f'{verb} {field_file.name}')
                else:
                    skipped += 1

        verb = 'por achicar' if dry_run else 'achicadas'
        self.stdout.write(self.style.SUCCESS(
            f'{changed} foto(s) {verb}, {skipped} ya estaban bien, {failed} con error.'))
