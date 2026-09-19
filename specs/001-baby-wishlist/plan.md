# Plan: Catálogo y Wishlist para Bebé

## Estado
Borrador — pendiente de revisión con el usuario. Deriva de
[spec.md](./spec.md).

## Stack (reutilizado de FinTrack)

- **Backend**: FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL
- **Auth admin**: JWT con PyJWT[crypto], mismo patrón que FinTrack
  (`sub=str(user.id)`, claim mínimo, `check_acceso_*` centralizado en
  `deps.py`)
- **Frontend**: Nuxt 3 + TypeScript + Nuxt UI v2 + Pinia
- **Deploy backend**: Railway (Nixpacks, `alembic upgrade head` como
  pre-deploy, `railway.json` igual al de FinTrack)
- **Deploy frontend**: Vercel
- **DB local dev**: Postgres 16 vía `docker-compose.yml` (mismo patrón que
  FinTrack)
- **Storage de fotos**: Cloudflare R2 (S3-compatible) — nuevo respecto a
  FinTrack, ver sección dedicada.
- **Notificación de actividad**: contador in-app (sin servicio de email;
  no se reutiliza el Resend de FinTrack porque el usuario eligió esta
  opción).

## Modelo de datos

```
admins
  id, email, password_hash, created_at

items
  id, nombre, descripcion (nullable), amazon_link (nullable)
  estado: enum('necesitado', 'reservado', 'adquirido')
  origen_adquisicion: enum('nosotros', 'regalo') (nullable, solo si adquirido)
  gifter_name (nullable — ver reglas de visibilidad)
  caja_id (FK -> cajas_almacenamiento, nullable, solo si adquirido)
  created_at, updated_at

fotos_item
  id, item_id (FK), url, orden

cajas_almacenamiento
  id, etiqueta, descripcion (nullable)

reservas
  id, item_id (FK, único mientras esté activa)
  nombre_reservante
  token_deshacer (UUID, único)
  revelado: bool (default false)
  created_at, released_at (nullable)

wishlist_config
  id (fila única), share_token (UUID/slug público)
  nombre_app (default 'Nicole en Camino')
```

**Unicidad de reserva activa**: índice único parcial en Postgres —
`CREATE UNIQUE INDEX ... ON reservas (item_id) WHERE released_at IS NULL`
— garantiza a nivel de base de datos que dos invitados no puedan reservar
el mismo item en simultáneo (condición de carrera). El endpoint de
reservar captura la violación de unicidad y responde 409.

**Seed de `wishlist_config`**: la migración que crea la tabla inserta
también la fila única con `nombre_app = 'Nicole en Camino'` y un
`share_token` generado, para que `GET /config` funcione desde el primer
arranque sin pasos manuales.

**Nota de visibilidad**: `items.gifter_name` solo se popula en el momento
en que el admin marca el item como adquirido. Mientras el item está en
estado `reservado`, el nombre vive únicamente en `reservas.nombre_reservante`
y ningún endpoint de admin lo expone — así se garantiza la sorpresa real
(historia 6 del spec), sin necesidad de lógica de "ocultar campo", el dato
simplemente no está accesible hasta ese momento.

## Endpoints

### Admin (JWT requerido)
- `POST /auth/login`, `GET /auth/me`
- `GET /items` — listado completo con estado, fotos, caja
- `POST /items` — crear (nombre, descripcion?, amazon_link?)
- `PATCH /items/{id}` — editar datos generales
- `POST /items/{id}/fotos/presign` — URL firmada de subida a R2
- `POST /items/{id}/fotos` — confirmar foto subida (guarda url + orden)
- `DELETE /items/{id}/fotos/{foto_id}`
- `PATCH /items/{id}/adquirir` — `{origen, gifter_name?}`. Si el item
  estaba `reservado`, ignora `gifter_name` del body y lo toma de la
  reserva asociada (revelándolo recién ahí). Con `origen = nosotros`
  sobre un item `reservado` responde 409: hay que liberar la reserva
  primero. Sobre un item ya `adquirido` responde 409 (no re-adquirible).
- `DELETE /items/{id}` — elimina el item y sus fotos (en DB y en R2).
  Responde 409 si el item está `reservado` (liberar la reserva primero).
- `POST /items/{id}/liberar-reserva` — descarta la reserva activa
  (`released_at = now()`) y devuelve el item a `necesitado`. La respuesta
  NUNCA incluye `nombre_reservante` — la sorpresa se preserva incluso al
  liberar.
- `POST /cajas`, `GET /cajas`
- `PATCH /items/{id}/caja` — `{caja_id}`
- `GET /reservas/pendientes/count` — contador para el aviso in-app
- `GET /wishlist/link` — obtiene (o genera si no existe) el `share_token`
- `PATCH /config` — actualizar `nombre_app`

### Público (sin auth)
- `GET /config` — `nombre_app` actual, para el header de login
- `GET /w/{share_token}` — items en estado `necesitado` con fotos y
  link. Incluye `nombre_app` en la respuesta para que la wishlist
  pública no necesite una llamada extra a `/config`.
- `POST /w/{share_token}/items/{item_id}/reservar` — `{nombre}` → crea
  reserva, devuelve `token_deshacer` (se muestra una sola vez al
  invitado; el frontend lo guarda en localStorage además)
- `POST /w/reservas/{token_deshacer}/deshacer` — libera la reserva, el
  item vuelve a `necesitado`

## Storage de fotos (Cloudflare R2)

Flujo de subida directa (evita pasar binarios por el backend):
1. Frontend pide `POST /items/{id}/fotos/presign` → backend genera URL
   firmada de PUT contra R2 (boto3 con endpoint S3-compatible de R2).
2. Frontend sube el archivo directo a esa URL.
3. Frontend confirma con `POST /items/{id}/fotos` pasando la key/URL
   final, que el backend guarda en `fotos_item`.

Requiere cuenta de Cloudflare R2 + bucket público (o CDN en frente) para
servir las imágenes. Variables de entorno nuevas: `R2_ACCOUNT_ID`,
`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_URL`.

**Validación en el presign**: la URL firmada se genera restringida a
`Content-Type` de imagen (`image/jpeg`, `image/png`, `image/webp`) y con
`Content-Length` máximo de 5 MB. El endpoint de confirmación rechaza
keys que no correspondan a un presign emitido para ese item.

Al eliminar una foto (o un item con fotos), el backend borra también el
objeto en R2 — no se dejan huérfanos.

## Protecciones de los endpoints públicos

- **Rate limiting** con `slowapi==0.1.9` (mismo patrón que FinTrack)
  sobre todos los endpoints `/w/*`: límites conservadores (ej.
  10/minuto por IP en `reservar` y `deshacer`, 30/minuto en lectura)
  — suficiente para uso familiar y frena spam de cualquiera que
  obtenga el link.
- **CORS**: variable `CORS_ORIGINS` (URL del frontend en Vercel), mismo
  patrón que el `.env.example` de FinTrack.

## Identidad visual

### Ícono
Diseño aprobado en `specs/001-baby-wishlist/design/icon.svg`: insignia
circular, "J" trazada a mano + destello decorativo, con variante oscura
automática vía `prefers-color-scheme` embebido en el propio SVG. Se
copia a `frontend/public/` como favicon (y se generan los PNG derivados
que requiera Nuxt para `apple-touch-icon`, etc.).

### Paleta de colores
Basada en la imagen de referencia del usuario. Escala tipo Tailwind para
`app.config.ts` de Nuxt UI v2:

```
pink (primary)
  50:  #fff5fa
  100: #ffe5f0   (dado)
  200: #fdcae1   (dado)
  300: #f5b3d1
  400: #dba3bd
  500: #c594aa   (dado — primary)
  600: #a97a8f
  700: #8c6274
  800: #6f4c5b
  900: #523845

neutral (dark mode)
  900: #131313   (dado)
  950: #050505   (dado)
```

- **Modo claro**: fondo `pink.100` (`#ffe5f0`), superficies/cards
  `pink.200` (`#fdcae1`) o blanco, acentos/botones `pink.500` (`#c594aa`).
- **Modo oscuro**: fondo `neutral.950` (`#050505`), superficies
  `neutral.900` (`#131313`), acentos siguen en la rama `pink` (más clara,
  ej. `pink.300`/`pink.200` para contraste sobre fondo oscuro).
- Nuxt UI v2 se configura con `ui.primary = 'pink'` (paleta custom de
  arriba) y `ui.gray` apuntando a la escala `neutral` para los fondos
  oscuros.

## Autenticación de admins

Una sola cuenta compartida entre ambos (un único email/password) para
la v1. La tabla `admins` queda igual (soporta múltiples filas) para no
bloquear agregar una segunda cuenta más adelante sin migrar el modelo.

## Estructura de carpetas (espejo de FinTrack)

```
backend/
  app/
    models/        (admin.py, item.py, foto_item.py, caja.py, reserva.py, wishlist_config.py)
    schemas/
    routers/        (auth.py, items.py, cajas.py, wishlist.py)
    core/            (deps.py, security.py, storage_r2.py)
    alembic/
  main.py
  railway.json

frontend/
  pages/            (login.vue, admin/items/index.vue, w/[token].vue, ...)
  stores/           (auth.ts, items.ts)
  components/
  composables/
```

## Calidad

Nivel "completo" (equivalente a lo que FinTrack aspira a tener, no
necesariamente lo que ya tiene hoy):

- **Backend**: `ruff` para lint + format (`ruff check`, `ruff format
  --check`). Tests con pytest + savepoint rollback (patrón FinTrack).
  Coverage mínimo **80%**, verificado en CI.
- **Frontend**: `vue-tsc --noEmit` para typecheck. ESLint (módulo de
  Nuxt) para lint. Tests con Vitest + `@vue/test-utils` sobre stores
  (Pinia) y flujos críticos (reserva/deshacer). Coverage mínimo **70%**
  (más bajo que backend porque testear UI de Nuxt tiene más fricción
  y el proyecto es chico).
- **CI**: dos workflows de GitHub Actions, `ci-backend.yml` y
  `ci-frontend.yml`, corriendo en cada push/PR contra `main`:
  - Backend: `ruff check`, `ruff format --check`, `pytest --cov` con gate
    de 80%.
  - Frontend: `vue-tsc --noEmit`, `eslint .`, `vitest run --coverage` con
    gate de 70%.
  - Un PR no se mergea si el workflow correspondiente falla (branch
    protection en GitHub, a configurar manualmente por el usuario — no
    es algo que un agente pueda hacer vía código).

### Convención de commits

Todos los commits usan **Conventional Commits** (mismo estilo que
FinTrack):

- Formato: `tipo(scope): descripción en minúsculas`
- Tipos permitidos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`,
  `ci`, `style`
- Scopes sugeridos: `items`, `reservas`, `cajas`, `fotos`, `auth`,
  `config`, `wishlist`, `frontend`, `backend`, `deploy`
- Ejemplos: `feat(reservas): liberar reserva sin revelar nombre`,
  `test(items): 409 al eliminar item reservado`, `ci: workflow backend
  con gate de coverage`
- Aplica a todos los commits, humanos o generados por agentes. Un commit
  por tarea de tasks.md como regla general (tareas `[P]` chicas pueden
  agruparse si comparten scope).
- **Validación automática** en dos capas:
  - Local: hook `commit-msg` gestionado con `husky` + `@commitlint/cli`
    y `@commitlint/config-conventional` (en el `package.json` raíz del
    repo), que rechaza el commit si el mensaje no cumple el formato.
  - CI: workflow `ci-commits.yml` que corre commitlint sobre todos los
    mensajes del rango del PR (`--from origin/main --to HEAD`), para
    cubrir commits hechos sin los hooks instalados.

## Decisiones técnicas heredadas de FinTrack a reutilizar tal cual

- `bcrypt==4.2.1` pineado (evita incompatibilidad con passlib)
- `PyJWT[crypto]` en vez de python-jose
- JWT claim mínimo (`sub` + rol), sin datos sensibles
- FKs explícitas en SQLAlchemy cuando haya ambigüedad
- Tests backend con pytest + savepoint rollback por test

## Decisiones confirmadas

1. **Login admin**: una sola cuenta compartida (no dos separadas) para
   la v1.
2. **Storage de fotos**: Cloudflare R2, confirmado.
3. **Link único de wishlist**: confirmado que un solo `share_token` para
   toda la lista es aceptable (el link no debe filtrarse fuera del
   círculo familiar — responsabilidad de quien lo comparte, no de la
   app).
