# Tasks: Catálogo y Wishlist para Bebé

Deriva de [plan.md](./plan.md). Orden = dependencia. `[P]` = se puede
hacer en paralelo con las otras tareas `[P]` de su mismo bloque.

Todos los commits siguen **Conventional Commits** (ver "Convención de
commits" en plan.md). Regla general: un commit por tarea.

## Fase 0 — Scaffolding

- [x] T001 Estructura backend FastAPI (`main.py`, `app/core/config.py`,
      `requirements.txt`, `.env.example`) espejando FinTrack
- [x] T002 `docker-compose.yml` con Postgres 16 para dev local
- [x] T003 Alembic inicializado (`alembic init`, `env.py` leyendo
      `DATABASE_URL`)
- [x] T004 [P] Estructura frontend Nuxt 3 + TS + Nuxt UI v2 + Pinia
      (`nuxt.config.ts`, `package.json`, layout base)
- [x] T004a [P] Commitlint local: `husky` + `@commitlint/cli` +
      `@commitlint/config-conventional` en el `package.json` raíz, hook
      `commit-msg` — desde el primer commit del proyecto

## Fase 1 — Modelo de datos (cada uno con su migración Alembic)

Depende de Fase 0 (T001, T003).

- [x] T005 Modelo `Admin` + migración
- [x] T006 Modelo `Item` (enums `estado`, `origen_adquisicion`) +
      migración
- [x] T007 Modelo `FotoItem` (FK a `Item`) + migración
- [x] T008 [P] Modelo `CajaAlmacenamiento` + migración
- [x] T009 Modelo `Reserva` (FK a `Item`, `token_deshacer` único) +
      migración con índice único parcial `(item_id) WHERE released_at
      IS NULL`
- [x] T010 [P] Modelo `WishlistConfig` (fila única, `share_token`,
      `nombre_app`) + migración que inserta la fila seed ("Nicole en
      Camino" + `share_token` generado)

## Fase 2 — Auth admin

Depende de T005.

- [x] T011 `core/security.py` — hash/verify password (bcrypt==4.2.1
      pineado)
- [x] T012 `core/security.py` — JWT create/decode con PyJWT[crypto]
- [x] T013 `core/deps.py` — dependency de autenticación admin
- [x] T014 `POST /auth/login`
- [x] T015 `GET /auth/me`
- [x] T016 Comando/script de seed para crear la única cuenta admin
      inicial desde variables de entorno

## Fase 3 — CRUD Items (admin)

Depende de T006, Fase 2.

- [x] T017 Schemas Pydantic (`ItemCreate`, `ItemUpdate`, `ItemOut` — sin
      exponer `gifter_name` si `estado == reservado`)
- [x] T018 `POST /items`
- [x] T019 `GET /items` (listado admin)
- [x] T020 `PATCH /items/{id}` (datos generales)
- [x] T021 `PATCH /items/{id}/adquirir` — incluye la lógica de revelar
      `gifter_name` desde la `Reserva` asociada si el item estaba
      `reservado`; 409 si `origen=nosotros` sobre item `reservado` o si
      ya estaba `adquirido`
- [x] T021a `DELETE /items/{id}` — con borrado de fotos en DB y R2; 409
      si el item está `reservado`

## Fase 4 — Cajas de almacenamiento

Depende de T008.

- [x] T022 [P] `POST /cajas`
- [x] T023 [P] `GET /cajas`
- [x] T024 `PATCH /items/{id}/caja`

## Fase 5 — Fotos + R2

Depende de T007.

- [x] T025 `core/storage_r2.py` — cliente boto3 S3-compatible + generar
      URL presignada
- [x] T026 `POST /items/{id}/fotos/presign` — restringido a
      `Content-Type` de imagen (jpeg/png/webp) y máx. 5 MB
- [x] T027 `POST /items/{id}/fotos` (confirmar subida; rechaza keys no
      emitidas para ese item)
- [x] T028 `DELETE /items/{id}/fotos/{foto_id}` — borra también el
      objeto en R2

## Fase 6 — Wishlist pública + reservas

Depende de T009, T010, Fase 3.

- [x] T029 `GET /wishlist/link` (admin: obtiene o genera `share_token`)
- [x] T029a `PATCH /config` (admin: actualizar `nombre_app`)
- [x] T029b [P] `GET /config` (público: `nombre_app` actual, default
      "Nicole en Camino")
- [x] T030 `GET /w/{share_token}` (público, solo items `necesitado`;
      incluye `nombre_app` en la respuesta)
- [x] T031 `POST /w/{share_token}/items/{item_id}/reservar` (crea
      `Reserva`, devuelve `token_deshacer` una sola vez; 409 si ya hay
      reserva activa — respaldado por el índice único parcial de T009)
- [x] T032 `POST /w/reservas/{token_deshacer}/deshacer` (libera reserva,
      item vuelve a `necesitado`)
- [x] T032a `POST /items/{id}/liberar-reserva` (admin descarta la reserva
      activa sin que la respuesta exponga `nombre_reservante`)
- [x] T033 `GET /reservas/pendientes/count` (contador admin, sin nombres)
- [x] T033a Rate limiting con `slowapi` en endpoints `/w/*` (límites del
      plan.md) + `CORS_ORIGINS` configurado en `main.py`

## Fase 7 — Tests backend

Depende de Fases 2–6.

- [x] T034 Setup pytest + fixtures con savepoint rollback (patrón
      FinTrack)
- [x] T035 [P] Tests auth (login, /me, credenciales inválidas)
- [x] T036 [P] Tests items CRUD + flujo `adquirir` con revelación de
      nombre + 409 de `adquirir`/`eliminar` sobre item `reservado` +
      delete con limpieza de fotos
- [x] T037 [P] Tests reservas: reservar, deshacer, liberar por admin sin
      exponer nombre, nombre oculto en todos los endpoints admin
      mientras no esté revelado, doble reserva bloqueada (concurrencia
      contra el índice parcial)
- [x] T038 [P] Tests wishlist pública: solo se listan items `necesitado`
- [x] T038a [P] Tests `/config`: default "Nicole en Camino", update solo
      admin

## Fase 8 — Frontend base

Depende de T004.

- [x] T039 Layout + tema Nuxt UI v2 (`app.config.ts` con paleta `pink` /
      `neutral` definida en plan.md)
- [x] T039a [P] Favicon/ícono: copiar
      `specs/001-baby-wishlist/design/icon.svg` a `frontend/public/` +
      generar PNGs derivados (`apple-touch-icon`, etc.)
- [x] T039b Store `config` (Pinia) — fetch de `GET /config`
      (`nombre_app`), usado en el header de todas las páginas
- [x] T040 Store `auth` (Pinia) + middleware de rutas protegidas
- [x] T041 Página `login.vue` (usa `nombre_app` de T039b en el header)

## Fase 9 — Frontend admin

Depende de Fase 3–6 (API lista), T039–T041.

- [x] T042 Store `items` (Pinia)
- [x] T043 Página listado de items (badges de estado + contador de
      reservas pendientes de T033)
- [x] T044 Formulario crear/editar item, con upload de foto (flujo
      presign de T026–T027)
- [x] T045 Modal "marcar adquirido" (origen + nombre si aplica)
- [x] T045a Acciones "eliminar item" y "liberar reserva" con modales de
      confirmación (la de liberar explica que no se notifica al
      reservante y que el nombre no se revela)
- [x] T046 Gestión de cajas (crear/asignar, usa T022–T024)
- [x] T047 Página "link de wishlist" (mostrar/copiar URL de T029)
- [x] T047a Página "configuración" (editar `nombre_app` vía T029a/T039b)

## Fase 10 — Frontend wishlist pública

Depende de T030–T032, T039.

- [x] T048 Página pública `w/[token].vue` (grid de items disponibles,
      header con `nombre_app` de T039b)
- [x] T049 Flujo de reserva (modal pedir nombre, guardar
      `token_deshacer` en localStorage)
- [x] T050 Acción "deshacer mi reserva" (usa `token_deshacer` guardado)

## Fase 11 — Calidad y CI

Depende de Fase 7 (tests backend) y Fase 10 (frontend completo).

- [x] T051 [P] `ruff` config backend (`pyproject.toml`, reglas lint +
      format)
- [x] T052 [P] ESLint config frontend (módulo de Nuxt)
- [x] T053 Setup Vitest + `@vue/test-utils` (config, primer test smoke)
- [x] T054 [P] Tests frontend: store `auth` (login, logout, persistencia
      de sesión)
- [x] T055 [P] Tests frontend: store `items` (altas, cambios de estado)
- [x] T056 [P] Tests frontend: flujo de reserva/deshacer en la wishlist
      pública (componente)
- [x] T057 `ci-backend.yml` — GitHub Actions: `ruff check`, `ruff format
      --check`, `pytest --cov` con gate de 80%
- [x] T058 `ci-frontend.yml` — GitHub Actions: `vue-tsc --noEmit`,
      `eslint .`, `vitest run --coverage` con gate de 70%
- [x] T058a [P] `ci-commits.yml` — GitHub Actions: commitlint sobre los
      mensajes del rango del PR (`--from origin/main --to HEAD`)

## Fase 12 — Deploy

Depende de todas las anteriores funcionando localmente.

- [ ] T059 `railway.json` backend + variables de entorno (`DATABASE_URL`,
      `JWT_SECRET`, `CORS_ORIGINS`, `R2_*`) en Railway
- [ ] T060 Config Vercel frontend + variable `API_BASE_URL`
- [ ] T061 Verificar `alembic upgrade head` corre como pre-deploy en
      Railway

## Fase 13 — Polish

- [x] T062 [P] Revisión responsive/mobile-first en todas las páginas
- [x] T063 [P] README con instrucciones de setup local y deploy
