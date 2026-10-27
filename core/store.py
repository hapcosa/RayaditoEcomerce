"""Identidad de la tienda y sus catálogos, leídos de `store.json`.

`store.json` (raíz del repo) es lo único que cambia un fork para ser otra
tienda: nombre, dominio, textos de marca y qué catálogos públicos existen
(Rayadito: joyas y piedras; un fork textil: ropa). El backend lo carga en
`settings.STORE` y lo expone en `/api/store/`; la tienda Next.js lo importa
directo y la app admin lo pide a la API.

Se lee una vez al arrancar. El código lo consulta siempre vía `settings.STORE`
(nunca importando el archivo) para que los tests puedan reemplazarlo con
`override_settings` sin depender de la tienda concreta.
"""
import json
import re
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Tipo de los productos sin catálogo: existen pero no se listan en la tienda.
GENERAL_PRODUCT_TYPE = 'general'

SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
REQUIRED_TEXT = ('slug', 'name', 'short_name', 'description', 'domain')
REQUIRED_CATALOG_TEXT = ('slug', 'path', 'label', 'singular', 'category_type')


def _fail(path, problem):
    raise ImproperlyConfigured(f'{path}: {problem}')


def validate_store(data, path='store.json'):
    """Valida la estructura y devuelve el dict con los opcionales completados."""
    if not isinstance(data, dict):
        _fail(path, 'debe ser un objeto JSON')
    for key in REQUIRED_TEXT:
        if not isinstance(data.get(key), str) or not data[key].strip():
            _fail(path, f'falta "{key}" (texto)')
    if not SLUG_RE.match(data['slug']):
        _fail(path, '"slug" solo admite minúsculas, números y guiones')

    catalogs = data.get('catalogs')
    if not isinstance(catalogs, list) or not catalogs:
        _fail(path, '"catalogs" debe ser una lista con al menos un catálogo')
    seen_slugs, seen_paths = set(), set()
    for index, catalog in enumerate(catalogs):
        where = f'catalogs[{index}]'
        if not isinstance(catalog, dict):
            _fail(path, f'{where} debe ser un objeto')
        for key in REQUIRED_CATALOG_TEXT:
            if not isinstance(catalog.get(key), str) or not catalog[key].strip():
                _fail(path, f'{where} sin "{key}" (texto)')
        for key in ('slug', 'path'):
            if not SLUG_RE.match(catalog[key]):
                _fail(path, f'{where}.{key} solo admite minúsculas, números y guiones')
        if catalog['slug'] == GENERAL_PRODUCT_TYPE:
            _fail(path, f'{where}.slug "{GENERAL_PRODUCT_TYPE}" está reservado')
        if catalog['slug'] in seen_slugs:
            _fail(path, f'{where}.slug "{catalog["slug"]}" repetido')
        if catalog['path'] in seen_paths:
            _fail(path, f'{where}.path "{catalog["path"]}" repetido')
        seen_slugs.add(catalog['slug'])
        seen_paths.add(catalog['path'])
        catalog.setdefault('description', '')

    if 'rubro' in data and not (isinstance(data['rubro'], str) and SLUG_RE.match(data['rubro'])):
        _fail(path, '"rubro" (opcional) es un slug, ej. "joyeria" o "textil"')

    data.setdefault('tagline', '')
    data.setdefault('email_signature', data['name'])
    data.setdefault('email_from_name', data['name'])
    return data


def load_store(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        _fail(path, 'no existe; cada tienda necesita su store.json en la raíz del repo')
    except json.JSONDecodeError as error:
        _fail(path, f'JSON inválido ({error})')
    return validate_store(data, path)


def _store():
    from django.conf import settings
    return settings.STORE


def catalogs():
    return _store()['catalogs']


def catalog_by_slug(slug):
    return next((c for c in catalogs() if c['slug'] == slug), None)


def catalog_by_path(path):
    return next((c for c in catalogs() if c['path'] == path), None)


def catalog_choices():
    """`(slug, singular)` de cada catálogo, para campos de selección."""
    return [(c['slug'], c['singular']) for c in catalogs()]
