// Permite el import con efecto lateral de hojas de estilo (global.css).
// Normalmente lo cubre el expo-env.d.ts autogenerado por `expo start`, que está
// gitignoreado; esta declaración mantiene el typecheck verde en CI sin ese paso.
declare module '*.css';
