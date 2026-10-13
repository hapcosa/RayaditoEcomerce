# Avisos al cliente por WhatsApp (Cloud API)

Usa solo la **WhatsApp Cloud API oficial de Meta**. No usa scraping ni
WhatsApp Web automatizado. Está **apagado** (`WHATSAPP_ENABLED=false`) hasta
cargar las credenciales y tener las plantillas aprobadas.

## Qué hace hoy

| Aviso | Cuándo sale | Plantilla |
|---|---|---|
| Pedido pagado | Cuando MercadoPago aprueba el pago (una sola vez, aunque el webhook se repita) | `pedido_confirmado` |
| Pedido despachado | Cuando el pedido pasa a *enviado* con su número de seguimiento (app admin o `/api/orders/dispatch/`) | `pedido_despachado` |

Solo se le escribe a quien aceptó recibir avisos por WhatsApp en el checkout
(`WhatsAppOptIn`). Cada envío queda en `WhatsAppMessage` (admin de Django →
*Mensajes de WhatsApp*), con el `wamid` de Meta o el error.

**Pendiente** (segundo PR, cuando entren #94, #95 y #98, que tocan los mismos
archivos): la casilla de consentimiento en el checkout y el aviso de estado del
retracto. Mientras tanto ningún pedido tiene opt-in y no sale ningún mensaje,
aunque el flag esté encendido.

Un fallo de WhatsApp nunca tumba el pago ni el despacho: se registra y se
sigue.

## Qué tienes que crear en Meta

1. **Cuenta de WhatsApp Business (WABA) y número.** En
   [Meta for Developers](https://developers.facebook.com/apps) crea una app de
   tipo *Business*, agrégale el producto *WhatsApp* y asóciala al portafolio
   comercial de la tienda. Registra un número propio que reciba SMS o llamada
   para el código de verificación. Según Meta, un número **en uso en WhatsApp
   (la app personal) no se puede registrar sin borrar antes esa cuenta**. Un
   número de la app *WhatsApp Business* puede convivir con la API
   ("Coexistence"), pero solo con el flujo *Embedded Signup* de un proveedor
   tecnológico. Para esta tienda lo simple es usar un número aparte.
   Fuentes: [Get started](https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started),
   [Business phone numbers](https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/phone-numbers)
   y [Onboard WhatsApp Business app users](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users).
   El **Phone number ID** (no el número) va a `WHATSAPP_PHONE_NUMBER_ID`.
2. **Token de usuario del sistema.** En *Configuración del negocio → Usuarios
   del sistema*: crea uno (rol *Admin*), asígnale la app con control total y la
   cuenta de WhatsApp, y genera un token con los permisos `business_management`,
   `whatsapp_business_management` y `whatsapp_business_messaging`. Los tokens de
   usuario normales caducan en horas; los del sistema son de larga duración.
   Fuente: [Access tokens](https://developers.facebook.com/documentation/business-messaging/whatsapp/access-tokens).
   Va a `WHATSAPP_ACCESS_TOKEN` (solo en el `.env` de prod).
3. **Método de pago** en la cuenta de WhatsApp Business: las plantillas
   `utility` fuera de una conversación abierta se cobran.
4. **Dos plantillas**, categoría **Utility**, idioma **Spanish (CHL) — `es_CL`**,
   con parámetros **con nombre** (*named*). Los nombres y los parámetros tienen
   que ser exactamente estos, porque el código los manda así:

   **`pedido_confirmado`**, con los parámetros `nombre`, `pedido` y `total`:
   > Hola {{nombre}}, recibimos el pago de tu pedido #{{pedido}} por {{total}} en Piedras Rayadito. Te avisaremos por aquí cuando lo despachemos.

   **`pedido_despachado`**, con los parámetros `nombre`, `pedido`, `envio` y `seguimiento`:
   > Hola {{nombre}}, tu pedido #{{pedido}} de Piedras Rayadito ya va en camino por {{envio}}. Tu número de seguimiento es {{seguimiento}}. ¡Gracias por tu compra!

   Pie de página sugerido para las dos: *"¿No quieres más avisos? Escríbenos a
   contacto@piedrasdelrayadito.cl"*. Meta pide valores de ejemplo para cada
   parámetro al crear la plantilla (ej. `Ana`, `1234567890`, `$54.500`,
   `Starken`, `OF-998877`).

   No agregues ofertas, descuentos ni "mira nuestros productos": con contenido
   promocional Meta reclasifica la plantilla como *marketing* (más cara). Desde
   el 2025-04-09 lo hace automáticamente al aprobarla.
   Fuente: [Template categorization](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-categorization)
   (los ejemplos de *Order Management* son justo estos dos avisos) y
   [Utility templates](https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/utility-templates/utility-templates).

## Encender

```bash
# .env de prod
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
# Probar credenciales con la plantilla de ejemplo que Meta crea en toda cuenta:
python manage.py whatsapp_test +569XXXXXXXX
# Probar una plantilla propia ya aprobada:
python manage.py whatsapp_test +569XXXXXXXX --template pedido_despachado --language es_CL \
  --params '{"nombre": "Ana", "pedido": "123", "envio": "Starken", "seguimiento": "OF-1"}'
# Si llegan bien:
WHATSAPP_ENABLED=true
```

`whatsapp_test` no exige el flag, justamente para probar antes de encenderlo.

## Consentimiento (opt-in)

Política de Meta ([Get opt-in](https://developers.facebook.com/docs/whatsapp/overview/getting-opt-in)):

- Hay que tener el número del cliente **y** su consentimiento para recibir
  mensajes de la empresa.
- El texto debe decir claramente que acepta recibir mensajes y **nombrar a la
  empresa**. El método lo elige la empresa; un sitio web es uno de los válidos.
- Meta recomienda explicar cómo darse de baja y respetarlo.

Texto previsto para la casilla del checkout (desmarcada por defecto):
> Quiero recibir por WhatsApp los avisos de este pedido de Piedras Rayadito (pago, despacho y retracto).

Se guarda el texto exacto aceptado junto al teléfono. La baja se registra en el
admin de Django (*Consentimientos de WhatsApp* → `revoked_at`); con la baja
puesta, no sale ningún aviso más para ese pedido. Todavía no hay webhook para
procesar un "BAJA" respondido por WhatsApp.

## Precios

Según [Pricing](https://developers.facebook.com/docs/whatsapp/pricing), revisado el 2026-10-12:

- Desde el **2025-07-01** Meta cobra **por mensaje entregado**, no por
  conversación. El modelo por conversación quedó obsoleto.
- Se cobran solo las plantillas, según categoría (*marketing*, *utility*,
  *authentication*) y el país del destinatario. Los mensajes que no son
  plantilla son gratis.
- Una plantilla *utility* enviada **dentro de una ventana de atención abierta**
  (el cliente escribió en las últimas 24 h) es **gratis**. Fuera de esa ventana
  se cobra. Los avisos de esta tienda casi siempre caen fuera.
- Chile es un mercado propio en la tabla de tarifas, y desde el 2026-04-01 se
  puede facturar en **CLP**. Las tarifas vigentes rigen desde el 2026-07-01, y
  Meta solo las cambia el primer día de cada trimestre.
- **No pude leer la tarifa exacta de Chile.** Está en los CSV/PDF de *Rate
  cards* de esa página y en el selector de
  [whatsappbusiness.com/products/platform-pricing](https://whatsappbusiness.com/es-la/products/platform-pricing/),
  que se carga con JavaScript. Revísala ahí, mercado *Chile*, categoría *Utility*.

Con dos avisos por pedido, el costo es 2 × la tarifa *utility* de Chile por
cada venta con opt-in.

## API

`POST https://graph.facebook.com/{WHATSAPP_GRAPH_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages`
con `Authorization: Bearer <token>` y cuerpo `type: template` con parámetros
`parameter_name`. Ver `notifications/whatsapp.py`. La versión por defecto es
`v23.0`, la misma que usa la doc de ejemplo y la integración de Instagram.
