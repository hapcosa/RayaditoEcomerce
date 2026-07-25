import Link from 'next/link';

interface AuthFormWrapperProps {
  title: string;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
}

export function AuthFormWrapper({ title, subtitle, children }: AuthFormWrapperProps) {
  return (
    <div className="mx-auto max-w-md px-6 py-16">
      <div className="mb-8 text-center">
        <Link href="/" className="font-manuscrita text-2xl text-tierra-600 hover:text-tierra-700">
          Piedras Rayadito
        </Link>
        <h1 className="mt-4 font-serif text-3xl font-medium text-piedra-900">{title}</h1>
        {subtitle && <div className="mt-2 text-sm text-piedra-500">{subtitle}</div>}
      </div>
      <div className="rounded-2xl border border-piedra-200 bg-white p-8 shadow-sm">
        {children}
      </div>
    </div>
  );
}

interface FieldProps {
  label: string;
  id: string;
  error?: string;
  children: React.ReactNode;
}

export function Field({ label, id, error, children }: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-piedra-700">
        {label}
      </label>
      {children}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

export const inputCls =
  'w-full rounded-lg border border-piedra-200 px-3 py-2.5 text-sm text-piedra-900 placeholder-piedra-400 focus:border-tierra-400 focus:outline-none focus:ring-1 focus:ring-tierra-300';

export const submitCls =
  'w-full rounded-full bg-tierra-500 py-3 text-sm font-medium uppercase tracking-wide text-white transition-colors hover:bg-tierra-600 disabled:bg-piedra-200 disabled:text-piedra-400';
