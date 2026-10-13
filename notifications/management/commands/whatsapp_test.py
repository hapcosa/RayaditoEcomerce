"""Manda una plantilla de prueba para revisar credenciales y plantillas.

Por defecto usa `hello_world` (en_US), la plantilla de ejemplo que Meta crea en
toda cuenta nueva de WhatsApp Business, asi que sirve antes de tener aprobadas
las propias. No exige WHATSAPP_ENABLED: es justo lo que se corre antes de
prenderlo.
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from notifications.whatsapp import WhatsAppError, normalize_phone, send_template


class Command(BaseCommand):
    help = 'Send a WhatsApp template to a phone number to check the setup.'

    def add_arguments(self, parser):
        parser.add_argument('phone', help='Chilean mobile, e.g. +56912345678.')
        parser.add_argument('--template', default='hello_world')
        parser.add_argument('--language', default='en_US')
        parser.add_argument(
            '--params', default='{}',
            help='Named body parameters as JSON, e.g. \'{"nombre": "Ana"}\'.',
        )

    def handle(self, *args, **options):
        if not (settings.WHATSAPP_PHONE_NUMBER_ID and settings.WHATSAPP_ACCESS_TOKEN):
            raise CommandError(
                'Faltan WHATSAPP_PHONE_NUMBER_ID o WHATSAPP_ACCESS_TOKEN en el .env.')
        phone = normalize_phone(options['phone'])
        if not phone:
            raise CommandError(f'{options["phone"]!r} no es un celular chileno.')
        try:
            params = json.loads(options['params'])
        except ValueError as exc:
            raise CommandError(f'--params no es JSON valido: {exc}') from None

        try:
            wamid = send_template(phone, options['template'], params,
                                  language=options['language'])
        except WhatsAppError as exc:
            raise CommandError(str(exc)) from None
        self.stdout.write(self.style.SUCCESS(f'Enviado a +{phone}: {wamid}'))
