import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Política de privacidad',
  description:
    'Cómo Piedras Rayadito recopila y usa tus datos personales.',
};

export default function PrivacidadPage() {
  return (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-serif text-4xl font-medium text-piedra-900">
        Política de privacidad
      </h1>
      <p className="mt-2 text-sm text-piedra-500">
        Documento en borrador — pendiente de revisión legal antes de la puesta en producción.
      </p>

      <div className="mt-8 flex flex-col gap-6 text-sm leading-relaxed text-piedra-700">
        <section>
          <h2 className="font-serif text-xl text-piedra-900">1. Datos que recopilamos</h2>
          <p className="mt-2">
            Recopilamos los datos que nos entregas al crear una cuenta, realizar una
            compra o escribirnos por el buzón de sugerencias: nombre, correo,
            dirección de despacho y detalle del pedido.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-xl text-piedra-900">2. Uso de los datos</h2>
          <p className="mt-2">
            Usamos tus datos únicamente para procesar pedidos, gestionar envíos y
            responder tus mensajes. No los vendemos ni compartimos con terceros
            ajenos a estos fines.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-xl text-piedra-900">3. Pagos y envíos</h2>
          <p className="mt-2">
            Los datos de pago los procesa MercadoPago y los de despacho, la empresa
            de envíos, cada uno bajo sus propias políticas.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-xl text-piedra-900">4. Tus derechos</h2>
          <p className="mt-2">
            Puedes solicitar acceso, corrección o eliminación de tus datos
            escribiéndonos al correo de contacto del pie de página.
          </p>
        </section>
      </div>
    </article>
  );
}
