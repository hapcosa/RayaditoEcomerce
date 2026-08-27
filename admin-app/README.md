# Rayadito Admin (Expo)

App móvil nativa para que el staff de **Piedras Rayadito** cargue productos y
gestione pedidos desde el celular. Consume la misma API DRF del backend Django
(endpoints `/api/admin/`, solo `is_staff`).

Parte de la **Fase 5** del [ROADMAP](../docs/ROADMAP.md).

## Stack
- Expo SDK 57 + Expo Router (TS).
- Auth JWT (djoser + simplejwt) con header `Authorization: JWT <access>` (¡no Bearer!).
- Tokens en `expo-secure-store` (Keychain/Keystore).

## Setup

```bash
cd admin-app
npm install
cp .env.example .env      # y ajustá EXPO_PUBLIC_API_URL a la IP LAN del backend
npx expo start
```

### Probar en un teléfono físico
El teléfono y la máquina con Django deben estar en la **misma red**. `localhost`
en el teléfono es el propio teléfono, así que `EXPO_PUBLIC_API_URL` debe apuntar
a la IP LAN de la máquina (p. ej. `http://192.168.1.50:8000`), y Django debe
correr con `ALLOWED_HOSTS` incluyendo esa IP y escuchando en `0.0.0.0`:

```bash
python manage.py runserver 0.0.0.0:8000
```

- **Expo Go**: escaneá el QR de `npx expo start`.
- **Android por adb** (device ya conectado): `npx expo start --android`.

## Scripts
- `npm start` — dev server (Metro).
- `npm run android` / `npm run ios` / `npm run web`.
- `npm run typecheck` — `tsc --noEmit`.
- `npm run lint` — `expo lint`.

## Estructura
```
src/
  api/        cliente HTTP (JWT + refresh) y almacenamiento de tokens
  auth/       AuthProvider + useAuth (login staff, verificación is_staff)
  app/        rutas (expo-router)
    login.tsx        pantalla de login
    (app)/           pantallas protegidas (dashboard; productos/pedidos en PR4/5)
```
