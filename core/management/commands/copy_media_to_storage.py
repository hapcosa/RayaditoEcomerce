"""Copia la media del disco del servidor al storage configurado (R2 / S3).

Es el paso de migracion de `MEDIA_STORAGE=local` a `MEDIA_STORAGE=s3`: las
rutas guardadas en la base son relativas (`photos/26/08/x.jpg`), asi que basta
con que cada archivo quede en el bucket con la misma clave.

Usa el mismo storage que Django (`default_storage`), no una herramienta
aparte: si el comando sube bien, el sitio lee bien, y no hay que configurar
credenciales dos veces. Es idempotente: lo que ya esta en el bucket se salta,
asi que se puede cortar y volver a correr.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Copy local media files (MEDIA_ROOT) into the configured default storage.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default=settings.MEDIA_ROOT,
            help='Directory to copy from (default: MEDIA_ROOT).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List what would be uploaded, without uploading.',
        )

    def handle(self, *args, **options):
        source = Path(options['source']).resolve()
        if not source.is_dir():
            raise CommandError(f'{source} no es un directorio.')
        if isinstance(default_storage, FileSystemStorage) and \
                Path(default_storage.location).resolve() == source:
            raise CommandError(
                'El storage configurado es el mismo directorio de origen. '
                'Pon MEDIA_STORAGE=s3 y las credenciales del bucket antes de copiar.')

        uploaded = skipped = 0
        for path in sorted(source.rglob('*')):
            if not path.is_file() or any(p.startswith('.') for p in path.relative_to(source).parts):
                continue
            name = path.relative_to(source).as_posix()
            if default_storage.exists(name):
                skipped += 1
                continue
            if options['dry_run']:
                self.stdout.write(f'subiria {name}')
                uploaded += 1
                continue
            with path.open('rb') as handle:
                saved = default_storage.save(name, File(handle))
            # Con file_overwrite=False un nombre ocupado se renombra en vez de
            # pisarse; aca no deberia pasar (se chequeo exists), pero si pasa la
            # base quedaria apuntando a otro archivo, asi que se corta.
            if saved != name:
                raise CommandError(
                    f'{name} se guardo como {saved}: la base apunta a {name}. '
                    'Revisa el bucket antes de seguir.')
            uploaded += 1
            self.stdout.write(f'subido {name}')

        verb = 'por subir' if options['dry_run'] else 'subidos'
        self.stdout.write(self.style.SUCCESS(
            f'{uploaded} archivo(s) {verb}, {skipped} ya estaban en el storage.'))
