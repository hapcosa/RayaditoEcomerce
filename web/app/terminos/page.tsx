import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Términos y condiciones',
  description:
    'Términos y condiciones de uso y compra en la tienda Piedras Rayadito.',
};

export default function TerminosPage() {
  return (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-serif text-4xl font-medium text-piedra-900">
        Términos y condiciones
      </h1>
      <p className="mt-2 text-sm text-piedra-500">
        Documento en borrador — pendiente de revisión legal antes de la puesta en producción.
      </p>

      <div className="mt-8 flex flex-col gap-6 text-sm leading-relaxed text-piedra-700">
        <section>
          <h2 className="font-serif text-xl text-piedra-900">1. Sobre la tienda</h2>
          <p className="mt-2">
            Piedras Rayadito comercializa joyería artesanal y piedras lapidadas de
            Chiloé. Al realizar una compra aceptas estos términos.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-xl text-piedra-900">2. Precios y pagos</h2>
          <p className="mt-2">
            Todos los precios se expresan en pesos chilenos (CLP). Los pagos se
            procesan a través de MercadoPago.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-xl text-piedra-900">3. Envíos</h2>
          <p className="mt-2">
            Los despachos se realizan mediante Starken u otras opciones informadas
            durante el checkout. Los plazos dependen del destino.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-xl text-piedra-900">4. Piezas únicas</h2>
          <p className="mt-2">
            Al tratarse de trabajo artesanal, cada pieza puede presentar pequeñas
            variaciones respecto de las fotografías. Esto es parte de su carácter
            hecho a mano.
          </p>
        </section>
        <section>
          <h2 className="font-serif text-xl text-piedra-900">5. Contacto</h2>
          <p className="mt-2">
            Ante cualquier duda escríbenos a través del buzón de sugerencias o al
            correo de contacto del pie de página.
          </p>
        </section>
      </div>
    </article>
  );
}
