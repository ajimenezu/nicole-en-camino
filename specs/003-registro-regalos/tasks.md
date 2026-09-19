# Tasks: Registro de regalos

Deriva de [plan.md](./plan.md). Orden = dependencia. `[P]` = paralelizable
dentro de su bloque. Conventional Commits, un commit por tarea.

## Fase 1 — Modelo y migración

- [x] R001 Modelos `Regalo` y `FotoRegalo` + enum `Etapa`
- [x] R002 Campo `items.etapa`
- [x] R003 Migración: tablas nuevas, backfill de `gifter_name` y de las
      reservas reveladas, drop de `gifter_name`, downgrade que
      reconstruye y borra los ENUM
- [x] R004 `cantidad_recibida` derivado de los regalos en
      `services/items.py`

## Fase 2 — Backend: registro

- [x] R005 `POST /regalos` con alta de objeto al vuelo
- [x] R006 `GET /regalos` con filtros
- [x] R007 [P] `GET /regalos/personas` (autocompletado)
- [x] R008 [P] `GET /regalos/por-persona` (agrupado, con pendientes de
      agradecer)
- [x] R009 `PATCH /regalos/{id}` — incluye marcar agradecido
- [x] R010 `DELETE /regalos/{id}` con recálculo del objeto
- [x] R011 `recibir` de una reserva crea el regalo con nombre y mensaje
- [x] R012 `/adquirir` crea el regalo en vez de tocar `gifter_name`

## Fase 3 — Backend: fotos y etapas

- [x] R013 Fotos de regalo en R2 (presign, confirmar, borrar) reusando
      `storage_r2` con prefijo `regalos/`
- [x] R014 [P] `etapa` en crear/editar item y en las salidas
- [x] R015 Búsqueda devuelve caja, etapa y quiénes regalaron

## Fase 4 — Tests backend

- [x] R016 Tests de registro: objeto existente, alta al vuelo, varias
      unidades, compra propia
- [x] R017 [P] Tests de agrupación por persona y agradecimientos
- [x] R018 [P] Tests de que recibir una reserva crea el regalo y respeta
      la sorpresa hasta ese momento
- [x] R019 [P] Tests de fotos de regalo (R2 mockeado)
- [x] R020 Tests de `cantidad_recibida` derivado (alta y baja de regalos)
- [x] R021 Adaptar los tests afectados por la baja de `gifter_name`

## Fase 5 — Frontend

- [x] R022 Tipos y store de regalos
- [x] R023 Modal "Registrar regalo" con autocompletado de persona y alta
      de objeto al vuelo
- [x] R024 Sección "Regalos": lista con filtros
- [x] R025 Vista agrupada por persona con marcar agradecido
- [x] R026 Fotos de Nicole por regalo (subida y descarga)
- [x] R027 Filtro por etapa en el catálogo
- [x] R028 Búsqueda con caja, etapa y personas

## Fase 6 — Cierre

- [x] R029 [P] Tests frontend del store de regalos
- [x] R030 [P] Verificación en navegador de los flujos nuevos
- [x] R031 README y specs actualizados
