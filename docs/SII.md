# Boletas y facturas (SII)

La tienda tiene preparada la parte tributaria, pero **está apagada**
(`BILLING_MODE=off`) hasta que haya inicio de actividades. Este documento dice
qué hacer ese día.

> Esto no reemplaza a un contador. Antes de activarlo, revisa con uno el
> régimen tributario, si las ventas están afectas a IVA y el punto de "boleta y
> factura en la misma venta" de más abajo.

## Lo importante: probablemente no necesitas emitir boletas

Desde 2021, el **comprobante de pago electrónico** (el "voucher") de una venta
pagada con tarjeta u otro medio electrónico **vale como boleta**
(Res. Ex. SII N° 176 de 2020). Todas las ventas de la tienda se pagan con
MercadoPago, así que su comprobante cumple ese rol y no hace falta emitir una
boleta aparte por cada venta.

Lo que sí hay que emitir son las **facturas**, cuando un cliente con RUT de
empresa las pide. Para pocas facturas basta con el sistema gratuito del SII.

## El día que tengas inicio de actividades

1. **Inicio de actividades** en sii.cl, con el giro que corresponda (venta de
   joyería y artesanía). El contador define el régimen.
2. **Declara el modelo de emisión** en el SII
   (<https://www4.sii.cl/actatributointernetui>) indicando que los
   comprobantes de pago electrónico valen como boleta. Si no declaras nada, el
   SII asume que sí valen. Lee bien el texto de cada opción: elegir la
   equivocada puede hacer que el SII cuente dos veces la misma venta.
3. En el `.env` del servidor:

   ```env
   BILLING_MODE=voucher
   ```

   Reinicia `rayadito-api`. Desde ahí cada venta aprobada deja registrado su
   comprobante en el admin, en **Documentos tributarios**, con el número de
   pago de MercadoPago.
4. **Facturas.** Inscríbete en el *Sistema de Facturación Gratuito* del SII y,
   cuando quieras empezar a emitirlas, activa la opción en el checkout:

   ```env
   BILLING_INVOICES_ENABLED=true
   ```

   El checkout muestra "Necesito factura" y pide RUT (se valida el dígito
   verificador), razón social, giro, dirección y comuna. Cuando entra una venta
   con factura te llega un correo con esos datos. Emítela en el portal del SII
   y después, en el admin, carga el folio en el documento y pásalo a "Emitido".

**Boleta y factura en la misma venta:** si una venta pagada con MercadoPago
lleva factura, el comprobante de pago no debería contarse además como boleta.
Consulta con el contador cómo se informa ese caso en tu modelo de emisión.

## Cuando convenga automatizar (`BILLING_MODE=provider`)

Hay que pasar a un proveedor si quieres que las facturas se emitan solas, o si
algún día aceptas pagos que no dan comprobante electrónico (efectivo o
transferencia, que siempre requieren boleta). Opciones conocidas: OpenFactura
(Haulmer), SimpleAPI, Bsale, o LibreDTE si prefieres alojarlo tú. En todos los
casos se necesita **certificado digital** de una entidad acreditada y **folios
(CAF)** del SII; algunos proveedores los gestionan por ti.

Para conectarlo:

1. Escribe una subclase de `billing.providers.BillingProvider` con el método
   `issue()`, siguiendo la API del proveedor elegido. Tiene que ser
   idempotente: reintentar un documento ya emitido devuelve el mismo folio.
2. En el `.env`:

   ```env
   BILLING_MODE=provider
   BILLING_PROVIDER=billing.providers_openfactura.OpenFacturaProvider  # ejemplo
   ```

3. Agrega un timer que reintente los documentos fallidos. Las boletas deben
   llegar al SII dentro de la hora siguiente a la venta:

   ```ini
   # /etc/systemd/system/rayadito-billing.service
   [Service]
   Type=oneshot
   User=donaldchavez
   WorkingDirectory=/home/donaldchavez/servicios/RayaditoEcomerce
   EnvironmentFile=/home/donaldchavez/servicios/RayaditoEcomerce/.env
   ExecStart=/home/donaldchavez/servicios/RayaditoEcomerce/.venv/bin/python manage.py issue_tax_documents

   # /etc/systemd/system/rayadito-billing.timer
   [Timer]
   OnCalendar=*:0/10
   Persistent=true
   [Install]
   WantedBy=timers.target
   ```

Un fallo del proveedor nunca tumba la venta. El documento queda como "Falló"
con el error a la vista en el admin, y el timer lo reintenta.

## Qué hay en el código

| Pieza | Dónde |
|---|---|
| Modos y registro por venta | `billing/services.py` (`on_order_paid`, después del commit del pago) |
| Documento por venta | `billing.models.TaxDocument`: comprobante, boleta o factura; pendiente, emitido o falló |
| Datos de factura del cliente | `billing.models.InvoiceRequest`, que se llena desde el checkout |
| Validación de RUT | `billing/rut.py` (módulo 11) |
| Interfaz de proveedor | `billing/providers.py` |
| ¿Se ofrece factura? | `GET /api/billing/config`, lo consulta el checkout |
