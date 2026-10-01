"""Publica en Instagram lo que la app dejo programado.

Pensado para correr cada 5 minutos desde un timer de systemd (ver
docs/DEPLOY.md), igual que `notify_pending_dispatch`: un comando idempotente
que se puede correr a mano, sin cola ni worker aparte.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from social import instagram
from social.services import BATCH_SIZE, due_posts, publish_post, recover_stuck_posts


class Command(BaseCommand):
    help = 'Publish the scheduled product posts to Instagram.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List the posts that are due, without publishing.',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        pending = list(due_posts(now)[:BATCH_SIZE])

        if options['dry_run']:
            for post in pending:
                self.stdout.write(
                    f'Post {post.pk}: {post.product} '
                    f'(scheduled for {post.scheduled_for:%Y-%m-%d %H:%M})')
            self.stdout.write(f'{len(pending)} post(s) are due.')
            return

        stuck = recover_stuck_posts(now)
        if stuck:
            self.stderr.write(f'{stuck} post(s) were left half-way and marked as failed.')

        if not pending:
            self.stdout.write('No posts are due.')
            return
        if not instagram.is_configured():
            # Se dejan programadas: apenas se carguen las credenciales salen.
            self.stderr.write(
                'INSTAGRAM_USER_ID / INSTAGRAM_ACCESS_TOKEN are not set; '
                f'{len(pending)} post(s) left waiting.')
            return

        published = 0
        for post in pending:
            if publish_post(post, now=now):
                published += 1
                self.stdout.write(f'Post {post.pk}: published.')
            else:
                post.refresh_from_db()
                self.stderr.write(f'Post {post.pk}: {post.last_error or "skipped"}')
        self.stdout.write(self.style.SUCCESS(f'Published {published} post(s).'))
