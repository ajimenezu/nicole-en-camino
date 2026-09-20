<div align="center">
  <img src="frontend/public/icon.svg" width="96" alt="">
  <h1>Nicole en Camino</h1>
  <p>Catálogo y wishlist para la llegada de un bebé.</p>
</div>

Una app para llevar el registro de **qué recibieron, de parte de quién y
dónde quedó guardado** durante todo el proceso de la llegada de un bebé.
Incluye una wishlist compartible para coordinar con la familia y evitar
regalos duplicados, preservando la sorpresa de quién regaló qué hasta que
el regalo llega.

## Cómo funciona

**Registrar lo que llega:** un botón anota "recibimos X de parte de Y" en
un solo paso — si el objeto no estaba en el catálogo se crea ahí mismo, y
el nombre de la persona se autocompleta con los que ya usaron para que no
queden variantes del mismo nombre. Se le puede sumar una foto de Nicole
usando el regalo, para mandársela después a quien lo dio.

**Agradecer sin olvidarse de nadie:** una vista agrupa todo lo que regaló
cada persona y marca a quién falta agradecer.

**Encontrar las cosas:** cada objeto lleva su etapa (recién nacido, 0-3
meses…) y su caja de almacenamiento. El buscador responde "¿dónde
guardamos el termómetro?" mostrando caja, etapa y quién lo regaló.

**Para los invitados:** entran con un link, sin crear cuenta, y marcan qué
van a regalar, con un mensaje opcional. De los items que se necesitan de a
varios (bodies, pañales) cada uno aparta una unidad y el resto sigue
disponible.

**La sorpresa:** cuando alguien reserva, su nombre y su mensaje quedan
guardados pero **nadie puede verlos — ni la pareja**. Se revelan recién al
marcar ese regalo como recibido, y de a uno: recibir una unidad no delata
a quienes reservaron las otras. Esto no es una regla de UI — el schema de
la API simplemente no expone esos campos, y hay tests que verifican que el
nombre no aparece en ningún byte de ninguna respuesta de admin.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL 16 |
| Frontend | Nuxt 3 · TypeScript · Nuxt UI v2 · Pinia |
| Auth | JWT (PyJWT) · bcrypt |
| Fotos | Supabase Storage vía su API S3 (subida directa con presign) |
| Deploy | Vercel (web y API) · Supabase (Postgres y fotos) |

## Setup local

Requiere Docker, Python 3.13 y Node 22.

### 1. Base de datos

```bash
docker compose up -d
```

Levanta Postgres 16 en el puerto **5433** (no 5432, para no chocar con
otros proyectos).

### 2. Backend

```bash
cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt
```

Los comandos usan las rutas de Windows; en macOS y Linux son `.venv/bin/`.
`requirements-dev.txt` suma pytest y ruff a lo de `requirements.txt`, que
es lo único que se instala en producción.

Copiá `.env.example` a `.env` y ajustá lo que necesites. Después aplicá
las migraciones y creá la cuenta admin:

```bash
.venv/Scripts/alembic upgrade head
```

```bash
ADMIN_EMAIL=vos@ejemplo.com ADMIN_PASSWORD=tu-clave-segura .venv/Scripts/python seed_admin.py
```

Arrancá la API:

```bash
.venv/Scripts/uvicorn main:app --reload
```

Queda en http://localhost:8000 — con Swagger en `/docs`.

### 3. Frontend

```bash
cd frontend && npm install && npm run dev
```

Queda en http://localhost:3000.

## Tests y calidad

```bash
cd backend && .venv/Scripts/python -m pytest --cov=app --cov=main
```

```bash
cd frontend && npx vitest run --coverage
```

También corren `ruff check .` y `ruff format --check .` en el backend, y
`npx eslint .` más `npx vue-tsc --noEmit` en el frontend. Todo esto se
valida en CI (GitHub Actions) en cada PR contra `main`, junto con la
convención de [Conventional Commits](https://www.conventionalcommits.org/).

Los commits se validan también localmente con un hook de husky, que se
instala solo al correr `npm install` en la raíz del repo.

## Fotos

Las fotos son opcionales: sin storage configurado la app funciona completa
y los endpoints de foto responden 503 con un mensaje claro.

Sirve cualquier storage S3-compatible; en producción es Supabase Storage.
Se configura con las variables `STORAGE_*` del `.env` (ver
`.env.example`). El backend solo firma URLs — el archivo viaja directo
del navegador al storage, restringido a jpeg/png/webp de hasta 5 MB.

## Deploy

Dos proyectos de Vercel sobre este mismo repo, más un proyecto de
Supabase.

### Supabase

1. Un proyecto **solo para esta app**, en la misma región que las
   funciones de Vercel (por defecto Vercel usa `iad1`, que es US East).
2. **Data API apagada** (Project Settings → Data API). La app no la usa,
   y aunque la migración `c9d0e1f2a3b4` activa RLS en todas las tablas,
   apagarla deja una sola puerta de entrada a los datos.
3. Storage: un bucket **público**, con límite de 5 MB y tipos
   `image/jpeg, image/png, image/webp`. Supabase aplica esos límites en
   la subida misma.
4. Storage → S3: una access key. De ahí salen el endpoint y la región.

### API en Vercel

Root Directory `backend`. Vercel detecta FastAPI solo (`main.py` →
`app`). En cada deploy de producción corre `build_vercel.py`: aplica las
migraciones y, si están definidas, crea o actualiza la cuenta admin. Los
deploys de preview se saltean (`backend/vercel.json`), porque migrarían
la base real con código sin aprobar.

| Variable | Notas |
|---|---|
| `DATABASE_URL` | Supabase → Connect → **Transaction pooler** (puerto 6543), con la contraseña de la base |
| `JWT_SECRET` | 32+ caracteres. Generalo con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `CORS_ORIGINS` | La URL del frontend, sin barra final |
| `STORAGE_ENDPOINT_URL` | `https://<ref>.storage.supabase.co/storage/v1/s3` |
| `STORAGE_REGION` | La región del proyecto de Supabase, por ejemplo `us-east-1` |
| `STORAGE_ACCESS_KEY_ID`, `STORAGE_SECRET_ACCESS_KEY` | La access key de S3 |
| `STORAGE_BUCKET` | El nombre del bucket |
| `STORAGE_PUBLIC_URL` | `https://<ref>.supabase.co/storage/v1/object/public/<bucket>` |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Solo para el primer deploy: crean la cuenta admin. Borralas después, o cada deploy vuelve a poner esa contraseña |

`DEBUG` no se define: por defecto es `false`, que oculta `/docs` y exige
un `JWT_SECRET` seguro.

### Frontend en Vercel

Root Directory `frontend`, framework Nuxt (autodetectado).

| Variable | Notas |
|---|---|
| `NUXT_PUBLIC_API_BASE` | La URL de la API |
| `NUXT_PUBLIC_SITE_URL` | La URL del frontend. La usa el preview de WhatsApp para armar la imagen |

## Documentación del diseño

El proyecto se construyó con spec-driven development, en tandas:

- [`001-baby-wishlist/`](specs/001-baby-wishlist/) — la app base.
- [`002-mejoras/`](specs/002-mejoras/) — cantidad, categorías, prioridad,
  precio, buscador, mensaje y PWA.
- [`003-registro-regalos/`](specs/003-registro-regalos/) — el registro de
  regalos, agradecimientos, etapas y las fotos de Nicole.
- [`004-pagina-publica/`](specs/004-pagina-publica/) — la página de
  celebración. **Pendiente**, solo las decisiones tomadas.

Cada tanda tiene los mismos tres documentos:

- [`spec.md`](specs/001-baby-wishlist/spec.md) — el qué y el por qué:
  historias de usuario y reglas de negocio.
- [`plan.md`](specs/001-baby-wishlist/plan.md) — el cómo: arquitectura,
  modelo de datos, endpoints, paleta y criterios de calidad.
- [`tasks.md`](specs/001-baby-wishlist/tasks.md) — el desglose en tareas,
  con su estado.
