# Envíos con Starken

Estado al 2026-10-02: **integración lista y apagada** (`STARKEN_ENABLED=false`).
Mientras siga apagada, el checkout ofrece solo las opciones de precio fijo de
`/admin/shipping/shipping/`, igual que antes.

## Qué hace

| Pieza | Qué hace | Endpoint oficial |
|---|---|---|
| Cotización | Opciones de Starken con precio real por comuna y paquete | `consultarTarifas` |
| Comunas | Traduce la comuna del cliente al código de ciudad de Starken (caché de 24 h) | `listarCiudadesDestino` |
| Emisión | `manage.py starken_emit <pedido>` crea la orden de flete (OF) y guarda su número en el pedido | Web Service EMISION Host 2 Host |
| Seguimiento | `manage.py starken_tracking` actualiza el estado de los pedidos enviados | `getDetalleSeguimientoNuevo` |

- **El precio lo calcula el servidor.** La misma función arma las opciones del
  checkout y el monto que se cobra al crear la orden. Si Starken no responde al
  pagar, la orden no se crea (503) y el cliente puede elegir otra opción. Nunca
  se cobra un precio de respaldo inventado.
- **Si Starken se cae, el checkout no.** Las opciones de Starken desaparecen y
  quedan las de precio fijo (retiro en taller, "por pagar").
- **Emitir no es despachar.** `starken_emit` no cambia el estado del pedido: la
  dueña lo sigue pasando a "enviado" desde la app cuando entrega el paquete. El
  número de OF queda en `Order.deliveryNumber`, que es el que ya muestran la
  app y la página del pedido.
- **El seguimiento también toma números cargados a mano.** Si la dueña emite la
  OF en la web de Starken y escribe el número en la app, `starken_tracking` lo
  sigue igual. El estado queda en `/admin/shipping/shipment/`.
- La librería `django-starken` se sacó de `requirements.txt`: nadie la usaba,
  solo emite (no cotiza ni sigue envíos) y en su versión 1.0.7
  `import starken.handler` revienta con `KeyError: 'CTA_CTE_NUMBER'`.

## Qué hay que pedirle a Starken

El portal oficial dice que las credenciales productivas las entrega el
**ejecutivo comercial**. Pide:

1. **Cuenta corriente de empresa** con el servicio de emisión activo: número,
   dígito verificador y centro de costo. Sin cuenta corriente se puede cotizar
   la tarifa de lista, pero no emitir con `tipoPago=2`.
2. **Credenciales productivas de cotización y seguimiento**: el par `Rut` /
   `Clave` que va en los headers, y la URL productiva de los servicios REST (en
   QA es `https://restservices-qa.starken.cl/apiqa/starkenservices/rest`).
3. **Credenciales productivas de emisión H2H**: `rutEmpresaEmisora`,
   `rutUsuarioEmisor`, `claveUsuarioEmisor` y la URL productiva del servlet (en
   QA es `https://emisionh2h-qa.starken.cl/starkenh2h/servlet/aemisionh2hremrest`).
4. **Habilitar la IP del servidor**: para el QA de emisión Starken pide la IP
   desde la que se va a llamar. Pregunta si producción lo exige también y da la
   IP pública de salida del PC de prod.
5. **Confirmar la ciudad de origen** (código de `listarCiudadesOrigen`: Castro
   388, Ancud 389, Dalcahue 385, Quellón 1063) y cómo se entregan los paquetes:
   en agencia o con retiro a domicilio.
6. **Tarifa negociada**: con la cuenta corriente, la cotización devuelve su
   tarifa en vez de la de lista. Conviene confirmar que sea así en su ambiente.

## Configuración

En el `.env` (todas las variables están en `.env.example`):

```bash
STARKEN_ENABLED=true
STARKEN_API_URL=<url productiva de los servicios REST>
STARKEN_RUT=<rut del header>
STARKEN_CLAVE=<clave del header>
STARKEN_ORIGIN_CITY=388              # Castro; confirmar con Starken
STARKEN_CTA_CTE=<numero>             # sin DV
STARKEN_CTA_CTE_DV=<dv>
STARKEN_CENTRO_COSTO=0
STARKEN_PARCEL_KG=1                  # paquete estándar de un pedido
STARKEN_PARCEL_CM=20,15,10           # alto, ancho, largo

# Solo para emitir OF:
STARKEN_EMISSION_URL=<url productiva H2H>
STARKEN_EMITTER_COMPANY_RUT=<rut empresa, sin DV>
STARKEN_EMITTER_USER_RUT=<rut usuario, sin DV>
STARKEN_EMITTER_PASSWORD=<clave>
STARKEN_SENDER_RUT=12345678-9
STARKEN_SENDER_NAME=Piedras Rayadito
STARKEN_SENDER_STREET=<calle>
STARKEN_SENDER_NUMBER=<numero>
STARKEN_SENDER_COMMUNE=Castro
STARKEN_SENDER_PHONE=+56 9 ...
STARKEN_SENDER_EMAIL=contacto@piedrasdelrayadito.cl
```

Después, en `/admin/shipping/shipping/`, crea las opciones de Starken con
**Carrier = Starken (cotizado)** y el tipo de entrega (a domicilio o retiro en
agencia). Su campo `price` no se usa mientras la integración esté activa.

**Paquete.** El catálogo no guarda peso ni medidas, así que todo pedido se
cotiza y se emite como un bulto de `STARKEN_PARCEL_KG` y `STARKEN_PARCEL_CM`.
Para joyería alcanza; un fork con productos grandes necesitaría peso por
producto.

### Probar en QA antes de producción

Starken publica credenciales de prueba en
[developers.starken.cl](https://developers.starken.cl/) (sección *Cotiza tus
envíos*). Con ellas y las URL de QA (las default) se puede probar la cotización
y el seguimiento sin cuenta propia:

```bash
STARKEN_ENABLED=true STARKEN_RUT=<rut de prueba> STARKEN_CLAVE=<clave de prueba> \
STARKEN_ORIGIN_CITY=388 .venv/bin/python manage.py shell -c \
  "from shipping import starken; print(starken.quote('Ñuñoa', 2))"
```

El 2026-10-02 eso respondió `9520` (domicilio) y `9040` (agencia) para Castro →
Ñuñoa, y el seguimiento de una OF de ejemplo devolvió su estado. La emisión de QA
no se probó: exige que Starken habilite la IP.

## Emitir una OF

```bash
.venv/bin/python manage.py starken_emit 123 --dry-run      # revisa el payload (sin la clave)
.venv/bin/python manage.py starken_emit 123
.venv/bin/python manage.py starken_emit 124 --agencia 1467 # retiro en agencia: código de destino
.venv/bin/python manage.py starken_emit 125 --boleta 4567  # valor declarado > $50.000
```

- **Revisa el `--dry-run`.** La tienda guarda la dirección en una sola línea y
  Starken pide calle y número por separado; la separación es una heurística.
- **Retiro en agencia:** Starken exige el código de la agencia de destino
  (`@1467`). El checkout todavía no deja elegir agencia, así que hay que pasarlo
  a mano.
- **Más de $50.000 declarados:** Starken exige un documento de referencia. Se
  manda la boleta (tipo 28) con `--boleta`.
- La etiqueta se imprime desde Emisión Web de Starken (reimpresión unitaria o
  masiva), como indica su documentación.

## Seguimiento automático

`/etc/systemd/system/rayadito-starken-tracking.service`:

```ini
[Unit]
Description=Seguimiento de envíos Starken de Piedras Rayadito
After=network-online.target compose-rayadito.service

[Service]
Type=oneshot
User=donaldchavez
WorkingDirectory=/home/donaldchavez/servicios/RayaditoEcomerce
ExecStart=/home/donaldchavez/servicios/RayaditoEcomerce/.venv/bin/python manage.py starken_tracking
```

`/etc/systemd/system/rayadito-starken-tracking.timer`:

```ini
[Unit]
Description=Seguimiento de envíos Starken cada 2 horas

[Timer]
OnCalendar=0/2:15
Persistent=true

[Install]
WantedBy=timers.target
```

Solo consulta pedidos en "enviado" con opción de Starken y sin estado terminal
(entregado, devuelto, anulado...). Llegado a uno de esos, deja de preguntar,
como recomienda Starken.

## Comunas

Starken nombra algunas comunas distinto (Natales → PUERTO NATALES, Cabo de
Hornos → PUERTO WILLIAMS). `shipping/starken.py` tiene la tabla de alias,
verificada contra `listarCiudadesDestino` el 2026-10-02. Sin cotización quedan
Ollagüe, Juan Fernández, Antártica, Chillán Viejo y Tirúa (no aparecen), y
Olivar, Palmilla, Placilla y El Carmen, que son ambiguas. En esas comunas solo
se ofrecen las opciones de precio fijo.

En el carrito todavía no se conoce la comuna, así que ahí solo aparecen las
opciones de precio fijo. Las de Starken aparecen en el checkout al escribir la
dirección.

## Fuentes

- Portal oficial: <https://developers.starken.cl/> (secciones *Crea tu envío*,
  *Cotiza tus envíos* y *Opciones de seguimiento*).
- Diccionarios oficiales:
  [entrada de cotización](https://starken-developer.s3.us-west-2.amazonaws.com/cotizatusenvios/Diccionario_Entrada_Consulta_Tarifa.xlsx),
  [salida de cotización](https://starken-developer.s3.us-west-2.amazonaws.com/cotizatusenvios/Diccionario_Salida_Consulta_Tarifa.xlsx),
  [entrada de emisión H2H](https://starken-developer.s3.us-west-2.amazonaws.com/vendeconnosotros/Diccionario_H2H_Parametros_de_Entrada.xlsx),
  [salida de emisión H2H](https://starken-developer.s3.us-west-2.amazonaws.com/Diccionario_H2H_Parametros_de_Salida.xlsx),
  [seguimiento unitario](https://starken-developer.s3.us-west-2.amazonaws.com/opcionesdeseguimiento/Diccionario_Salida_Tracking_Unitario.xlsx)
  y [estados operacionales](https://starken-developer.s3.us-west-2.amazonaws.com/opcionesdeseguimiento/Estado_operacionales.xlsx).
