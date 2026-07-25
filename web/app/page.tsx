export default function HomePage() {
  return (
    <main className="min-h-screen">
      <section className="mx-auto flex max-w-prosa flex-col items-center gap-8 px-6 py-24 text-center">
        <p className="font-manuscrita text-2xl text-tierra-600">desde Chiloé</p>

        <h1 className="text-balance font-serif text-5xl font-medium leading-tight text-piedra-900 sm:text-6xl">
          Piedras Rayadito
        </h1>

        <p className="max-w-prosa text-lg leading-relaxed text-piedra-700">
          Joyería y lapidación de piedras del sur de Chile. Cada pieza es única,
          trabajada a mano con ágatas y minerales recogidos en las playas de la
          isla.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <a
            href="/joyas"
            className="rounded-full bg-tierra-500 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-50 transition-colors hover:bg-tierra-600"
          >
            Ver joyas
          </a>
          <a
            href="/piedras"
            className="rounded-full border border-piedra-300 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-800 transition-colors hover:border-agata-500 hover:text-agata-600"
          >
            Piedras
          </a>
        </div>

        {/* Muestra de tokens de color — se reemplaza al portar la portada real (ROADMAP Fase 4). */}
        <div className="mt-8 flex items-center gap-3" aria-hidden="true">
          <span className="h-8 w-8 rounded-full bg-piedra-300" />
          <span className="h-8 w-8 rounded-full bg-tierra-500" />
          <span className="h-8 w-8 rounded-full bg-agata-500" />
          <span className="h-8 w-8 rounded-full bg-piedra-800" />
        </div>
      </section>
    </main>
  );
}
