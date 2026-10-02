"""Cliente de la API oficial de Starken (developers.starken.cl).

Cubre lo que usa la tienda: listar ciudades de destino, cotizar, emitir la
orden de flete (OF) y consultar su estado. Los contratos salen de la
documentacion oficial (diccionarios de entrada y salida publicados en el
portal); ver docs/STARKEN.md.

Todo pasa por `settings.STARKEN`. Con la integracion apagada nada de esto se
llama: las vistas y el checkout lo consultan con `is_enabled()` antes.
"""
import logging
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CITIES_CACHE_KEY = 'starken:destination-cities'
CITIES_CACHE_SECONDS = 24 * 60 * 60
QUOTE_CACHE_SECONDS = 60 * 60

# Estados operacionales terminales (Estado_operacionales.xlsx del portal):
# llegado a uno de estos, Starken dice que no hace falta seguir consultando.
FINAL_STATUSES = {
    'CARGA DECOMISADA POR INCUMPLIMIENTO DE REGLAMENTO',
    'CARGA REMATADA POR ABANDONO',
    'CERRADO CON PROBLEMA CONTACTAR CON EJECUTIVO',
    'DEVUELTO AL CLIENTE',
    'ENTREGADO',
    'ENVIO ANULADO',
    'REDESTINADA POR SOLICITUD DEL CLIENTE',
}

# Tipos de documento de referencia de la OF.
DOCUMENT_BOLETA = 28
# Sobre este valor declarado Starken exige un documento de referencia.
DECLARED_VALUE_NEEDS_DOCUMENT = 50000
# tipoEncargo: 29 = bulto en kilogramos.
PARCEL_KIND = 29
# tipoPago: 2 = cargado a la cuenta corriente.
PAYMENT_CTA_CTE = 2


class StarkenError(Exception):
    """La API respondio con error, no respondio o falta configuracion."""


def config():
    return settings.STARKEN


def is_enabled():
    return bool(config()['ENABLED'])


def normalize(name):
    """`Ñuñoa` y `NUNOA` son la misma comuna: sin tildes, sin eñe, mayusculas."""
    text = unicodedata.normalize('NFKD', str(name or ''))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', text).strip().upper()


def to_clp(value):
    """Monto de Starken (viene como float: 6650.0) a entero CLP."""
    try:
        return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, TypeError, ValueError):
        raise StarkenError(f'monto invalido: {value!r}') from None


def _headers():
    cfg = config()
    if not cfg['RUT'] or not cfg['CLAVE']:
        raise StarkenError('faltan STARKEN_RUT / STARKEN_CLAVE')
    return {'Rut': cfg['RUT'], 'Clave': cfg['CLAVE'], 'Content-Type': 'application/json'}


def _request(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=config()['TIMEOUT'], **kwargs)
    except requests.RequestException as exc:
        raise StarkenError(f'sin respuesta de Starken: {exc.__class__.__name__}') from None
    if response.status_code != 200:
        raise StarkenError(f'Starken respondio HTTP {response.status_code}')
    try:
        return response.json()
    except ValueError:
        raise StarkenError('Starken respondio algo que no es JSON') from None


def _api(path):
    return f"{config()['API_URL'].rstrip('/')}/{path}"


def destination_cities():
    """{comuna normalizada: codigoCiudad} de todas las comunas de destino."""
    cached = cache.get(CITIES_CACHE_KEY)
    if cached is not None:
        return cached
    payload = _request('GET', _api('listarCiudadesDestino'), headers=_headers())
    if payload.get('codigoRespuesta') != 1:
        raise StarkenError(f"listarCiudadesDestino: {payload.get('mensajeRespuesta')}")
    mapping = {}
    for city in payload.get('listaCiudadesDestino') or []:
        for commune in city.get('listaComunas') or []:
            mapping.setdefault(normalize(commune.get('nombreComuna')), city['codigoCiudad'])
    cache.set(CITIES_CACHE_KEY, mapping, CITIES_CACHE_SECONDS)
    return mapping


# Comunas (nombre oficial, el de shipping/locations.py) que Starken lista con
# otro nombre. Verificado contra listarCiudadesDestino el 2026-10-02. Quedan
# afuera las ambiguas (Palmilla, Placilla, Olivar, El Carmen: Starken tiene
# varias localidades con ese nombre) y las que no aparecen (Ollagüe, Juan
# Fernandez, Antartica, Chillan Viejo, Tirua): ahi solo se ofrecen las opciones
# de precio fijo.
COMMUNE_ALIASES = {
    'PAIGUANO': 'PAIHUANO',
    'MOSTAZAL': 'SAN FRANCISCO DE MOSTAZAL',
    'SAN VICENTE': 'SAN VICENTE DE TAGUATAGUA',
    'SAN FABIAN': 'SAN FABIAN DE ALICO',
    'TREGUACO': 'TREHUACO',
    'ALTO BIOBIO': 'ALTO BIO BIO',
    'SAAVEDRA': 'PUERTO SAAVEDRA',
    'MARIQUINA': 'SAN JOSE DE LA MARIQUINA',
    'AYSEN': 'PUERTO AYSEN',
    'CISNES': 'PUERTO CISNES',
    "O'HIGGINS": 'VILLA OHIGGINS',
    'CABO DE HORNOS': 'PUERTO WILLIAMS',
    'NATALES': 'PUERTO NATALES',
    'SANTO DOMINGO': 'ROCAS DE SANTO DOMINGO',
}


def city_code_for(commune):
    """Codigo de ciudad de Starken para una comuna, o None si no llega ahi."""
    name = normalize(commune)
    cities = destination_cities()
    return cities.get(name, cities.get(COMMUNE_ALIASES.get(name, '')))


def _parcel():
    cfg = config()
    alto, ancho, largo = (list(cfg['PARCEL_CM']) + [10.0, 10.0, 10.0])[:3]
    return {'kilos': cfg['PARCEL_KG'], 'alto': alto, 'ancho': ancho, 'largo': largo}


def quote(commune, delivery_type, service_type=0):
    """Precio en entero CLP (IVA incluido) para enviar un paquete a `commune`.

    Lanza StarkenError si la comuna no esta en la cobertura o si Starken no
    ofrece esa combinacion de entrega y servicio.
    """
    cfg = config()
    if not cfg['ORIGIN_CITY']:
        raise StarkenError('falta STARKEN_ORIGIN_CITY')
    city = city_code_for(commune)
    if city is None:
        raise StarkenError(f'Starken no llega a la comuna {commune!r}')

    parcel = _parcel()
    key = f"starken:quote:{cfg['ORIGIN_CITY']}:{city}:{delivery_type}:{service_type}:" \
          f"{parcel['kilos']}:{parcel['alto']}:{parcel['ancho']}:{parcel['largo']}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    body = {
        'codigoCiudadOrigen': cfg['ORIGIN_CITY'],
        'codigoCiudadDestino': city,
        'codigoAgenciaOrigen': 0,
        'codigoAgenciaDestino': 0,
        **parcel,
        # Con cuenta corriente se cotiza su tarifa; sin ella, la de lista.
        'cuentaCorriente': cfg['CTA_CTE'],
        'cuentaCorrienteDV': cfg['CTA_CTE_DV'] if cfg['CTA_CTE'] else '',
        'rutCliente': '' if cfg['CTA_CTE'] else '1',
    }
    payload = _request('POST', _api('consultarTarifas'), headers=_headers(), json=body)
    if payload.get('codigoRespuesta') != 1:
        raise StarkenError(f"consultarTarifas: {payload.get('mensajeRespuesta')}")
    for rate in payload.get('listaTarifas') or []:
        entrega = (rate.get('tipoEntrega') or {}).get('codigoTipoEntrega')
        servicio = (rate.get('tipoServicio') or {}).get('codigoTipoServicio')
        if entrega == delivery_type and servicio == service_type:
            price = to_clp(rate.get('costoTotal'))
            cache.set(key, price, QUOTE_CACHE_SECONDS)
            return price
    raise StarkenError(
        f'Starken no ofrece entrega {delivery_type} / servicio {service_type} a {commune!r}')


def tracking_status(tracking_number):
    """Estado de una OF: (estadoFlete, es_terminal)."""
    payload = _request(
        'POST', _api('getDetalleSeguimientoNuevo'), headers=_headers(),
        json={'ordenFlete': int(tracking_number)})
    status = (payload.get('estadoFlete') or '').strip()
    if not status:
        raise StarkenError(f'seguimiento sin estado para la OF {tracking_number}')
    return status, normalize(status) in FINAL_STATUSES


def split_rut(rut):
    """'12.345.678-9' -> ('12345678', '9')."""
    clean = re.sub(r'[^0-9kK-]', '', str(rut or ''))
    if '-' not in clean:
        raise StarkenError(f'RUT sin digito verificador: {rut!r}')
    number, dv = clean.rsplit('-', 1)
    return number, dv.upper()


def split_street(address):
    """'Los Carrera 1234 depto 5' -> ('Los Carrera', '1234', 'depto 5').

    La tienda guarda la direccion en una sola linea; Starken pide calle y
    numero por separado. Toma el primer numero despues de la calle, asi que
    una calle con numero en el nombre ('Pasaje 3 45') queda mal partida:
    `starken_emit --dry-run` muestra el resultado antes de emitir. Sin numero
    reconocible va 'S/N'.
    """
    match = re.match(r'^\s*(.*?)[\s,#]+(\d+[A-Za-z]?)\b[\s,]*(.*)$', address or '')
    if not match or not match.group(1):
        return (address or '').strip(), 'S/N', ''
    return match.group(1).strip(), match.group(2), match.group(3).strip()


def _missing_emission_settings():
    cfg = config()
    keys = ('EMITTER_COMPANY_RUT', 'EMITTER_USER_RUT', 'EMITTER_PASSWORD', 'CTA_CTE',
            'CTA_CTE_DV', 'SENDER_RUT', 'SENDER_NAME', 'SENDER_STREET',
            'SENDER_NUMBER', 'SENDER_COMMUNE', 'SENDER_PHONE')
    return [f'STARKEN_{k}' for k in keys if not cfg[k]]


def emission_payload(order, *, agency_code=None, document_number=None):
    """Cuerpo de la emision H2H para un pedido.

    `agency_code`: codigo de agencia de destino, obligatorio para retiro en
    agencia. `document_number`: numero de boleta, obligatorio si el valor
    declarado supera los $50.000.
    """
    missing = _missing_emission_settings()
    if missing:
        raise StarkenError('falta configurar ' + ', '.join(missing))
    shipping = order.shipping_id
    if shipping is None or not shipping.is_starken or not shipping.starken_delivery_type:
        raise StarkenError('el pedido no usa una opcion de envio de Starken')

    cfg = config()
    delivery_type = shipping.starken_delivery_type
    if delivery_type == 1:
        if not agency_code:
            raise StarkenError('el retiro en agencia necesita el codigo de agencia de destino')
        commune = f'@{agency_code}'
    else:
        commune = normalize(order.city)
        if not commune:
            raise StarkenError('el pedido no tiene comuna')

    declared = int(order.amount or 0) - int(order.shipping_price or 0)
    if declared > DECLARED_VALUE_NEEDS_DOCUMENT and not document_number:
        raise StarkenError(
            f'el valor declarado (${declared}) supera los $50.000: Starken exige '
            'el numero de boleta (--boleta)')

    sender_rut, sender_dv = split_rut(cfg['SENDER_RUT'])
    names = (order.full_name or '').split()
    street, number, unit = split_street(order.address_line_1)
    email = order.email or (order.user.email if order.user_id else '')
    parcel = _parcel()

    payload = {
        'rutEmpresaEmisora': cfg['EMITTER_COMPANY_RUT'],
        'rutUsuarioEmisor': cfg['EMITTER_USER_RUT'],
        'claveUsuarioEmisor': cfg['EMITTER_PASSWORD'],
        'rutRemitente': sender_rut,
        'dvRemitente': sender_dv,
        'nombreRazonSocialRemitente': cfg['SENDER_NAME'][:60],
        'apellidoPaternoRemitente': '',
        'apellidoMaternoRemitente': '',
        'direccionRemitente': cfg['SENDER_STREET'][:50],
        'numeracionDireccionRemitente': cfg['SENDER_NUMBER'][:10],
        'departamentoRemitente': '',
        'emailRemitente': cfg['SENDER_EMAIL'][:50],
        'telefonoRemitente': cfg['SENDER_PHONE'][:20],
        'comunaRemitente': normalize(cfg['SENDER_COMMUNE'])[:30],
        'rutDestinatario': '',
        'dvRutDestinatario': '',
        'nombreRazonSocialDestinatario': (names[0] if names else '.')[:40],
        'apellidoPaternoDestinatario': (' '.join(names[1:2]) or '.')[:20],
        'apellidoMaternoDestinatario': (' '.join(names[2:]) or '.')[:20],
        'direccionDestinatario': street[:80],
        'numeracionDireccionDestinatario': number[:10],
        'departamentoDireccionDestinatario': unit[:10],
        'comunaDestino': commune[:30],
        'telefonoDestinatario': (order.telephone_number or '')[:20],
        'emailDestinatario': (email or '')[:50],
        'nombreContactoDestinatario': (order.full_name or '')[:40],
        'tipoEntrega': delivery_type,
        'tipoPago': PAYMENT_CTA_CTE,
        'numeroCtaCte': cfg['CTA_CTE'],
        'dvNumeroCtaCte': cfg['CTA_CTE_DV'],
        'centroCostoCtaCte': cfg['CENTRO_COSTO'],
        'valorDeclarado': declared,
        'contenido': cfg['CONTENT'][:50],
        'kilosTotal': parcel['kilos'],
        'alto': parcel['alto'],
        'ancho': parcel['ancho'],
        'largo': parcel['largo'],
        'tipoServicio': shipping.starken_service_type,
        'tipoDocumento1': DOCUMENT_BOLETA if document_number else '',
        'numeroDocumento1': document_number or '',
        'generaEtiquetaDocumento1': 'N' if document_number else '',
        'tipoEncargo1': PARCEL_KIND,
        'cantidadEncargo1': 1,
        'observacion': f'Pedido {order.id}',
    }
    return payload


def parse_freight_number(value):
    """nroOrdenFlete llega en notacion cientifica ('2.22746632E8')."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise StarkenError(f'numero de OF invalido: {value!r}') from None
    if number <= 0 or number != number.to_integral_value():
        raise StarkenError(f'numero de OF invalido: {value!r}')
    return str(int(number))


def create_freight_order(payload):
    """Emite la OF y devuelve su numero de seguimiento."""
    response = _request(
        'POST', config()['EMISSION_URL'], json=payload,
        headers={'Content-Type': 'application/json'})
    code = response.get('codigoError')
    if code != 0:
        description = response.get('DescripcionError') or response.get('descripcionError')
        raise StarkenError(f'emision rechazada ({code}): {description}')
    return parse_freight_number(response.get('nroOrdenFlete'))
