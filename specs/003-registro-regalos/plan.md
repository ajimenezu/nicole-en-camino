# Plan: Registro de regalos

## Estado
Borrador. Deriva de [spec.md](./spec.md). Stack y convenciones sin
cambios respecto de las tandas anteriores.

## Cambios al modelo

```
regalos (nueva) — el hecho: "recibimos X de parte de Y"
  id
  item_id            FK -> items (CASCADE)
  persona            text          — nombre libre, '' si lo compramos nosotros
  origen             enum('REGALO','NOSOTROS')
  cantidad           int, default 1, CHECK >= 1
  fecha              date, default hoy
  nota               text, nullable
  agradecido         bool, default false
  reserva_id         FK -> reservas, nullable, único
                     — solo si vino por la wishlist
  created_at

fotos_regalo (nueva) — Nicole usando el regalo
  id, regalo_id (FK, CASCADE), url, orden

items (cambios)
  etapa              enum(...), default CUALQUIERA
  cantidad_recibida  pasa a derivarse de sum(regalos.cantidad)
  gifter_name        SE ELIMINA (lo reemplazan los regalos)
```

`fotos_item` se mantiene para las fotos de referencia (las de la tienda).
Las fotos de Nicole son otra cosa y viven en `fotos_regalo`.

### Etapas

`RECIEN_NACIDO`, `M0_3`, `M3_6`, `M6_12`, `A1_2`, `A2_MAS`, `CUALQUIERA`
(default). Lista fija por decisión del spec.

### Por qué `cantidad_recibida` deja de ser un contador propio

Hoy se incrementa a mano en varios lugares y es fácil que se desincronice.
Pasa a ser `sum(regalos.cantidad)` recalculado tras cada alta/baja de
regalo, junto con `recalcular_estado()`. Un solo lugar de verdad.

## Migración

Una sola, con estos pasos:

1. Crear `regalos` y `fotos_regalo`; agregar `items.etapa`.
2. **Backfill**: por cada item con `cantidad_recibida > 0`, crear un
   regalo. `gifter_name` no se puede partir de forma confiable (es un
   string concatenado con comas, y un nombre puede llevar coma), así que
   se vuelca **entero en `persona`** de un único regalo con
   `cantidad = cantidad_recibida`. Si `gifter_name` es NULL, el regalo
   queda con `origen = NOSOTROS`.
   Los datos actuales son de prueba, pero la migración se escribe para no
   perder nada igual.
3. Vincular los regalos que vienen de reservas ya reveladas
   (`reservas.revelado = true`) con su `reserva_id`, tomando el nombre de
   `reservas.nombre_reservante` — ahí sí el dato está limpio.
4. Eliminar `items.gifter_name`.
5. `downgrade` reconstruye `gifter_name` concatenando las personas y
   elimina los ENUM nuevos (misma lección de las tandas anteriores).

## Endpoints

### Nuevos
- `POST /regalos` — registra un regalo. Body: `item_id` **o**
  `item_nuevo` (nombre + campos opcionales), `persona`, `origen`,
  `cantidad`, `fecha`, `nota`. Crea el objeto si vino `item_nuevo`.
- `GET /regalos` — listado con filtros: `persona`, `agradecido`,
  `desde`/`hasta`.
- `GET /regalos/por-persona` — agrupado por persona, con lo que regaló
  cada una y cuántos agradecimientos faltan.
- `GET /regalos/personas` — nombres ya usados, para el autocompletado.
- `PATCH /regalos/{id}` — editar persona, cantidad, fecha, nota,
  `agradecido`.
- `DELETE /regalos/{id}` — borra el regalo y recalcula el objeto.
- `POST /regalos/{id}/fotos/presign` + `POST /regalos/{id}/fotos` +
  `DELETE /regalos/{id}/fotos/{foto_id}` — mismo flujo de R2 que las
  fotos de referencia, reutilizando `core/storage_r2.py` con el prefijo
  `regalos/{id}/`.

### Modificados
- `POST /items/{id}/reservas/{reserva_id}/recibir`: además de revelar,
  **crea el regalo** con `persona = nombre_reservante`, `nota = mensaje`
  y `reserva_id`.
- `PATCH /items/{id}/adquirir`: crea un regalo con `origen` según el
  body en vez de tocar `gifter_name`.
- `GET /items` y `GET /items/buscar`: devuelven `etapa` y la lista de
  personas que regalaron ese objeto (derivada de sus regalos).
- Crear/editar item aceptan `etapa`.

## Frontend

- **Botón principal "Registrar regalo"** en el catálogo: modal con
  buscador de objeto existente o alta al vuelo, campo de persona con
  autocompletado (`/regalos/personas`), cantidad, fecha y nota.
- **Sección "Regalos"** nueva: lista con filtros por persona, por
  pendientes de agradecer y por fecha; y una vista agrupada por persona
  para agradecer de a uno.
- **Fotos de Nicole** en el detalle de cada regalo, con subida por presign
  y opción de descargar para compartir a mano.
- **Filtro por etapa** en el catálogo, junto a los de estado.
- **Búsqueda ampliada**: cada resultado muestra caja, etapa y quién lo
  regaló.

## Riesgos

1. **Se elimina `gifter_name`**, que hoy usan el listado admin y sus
   tests. Hay que revisarlos uno por uno, igual que en la tanda anterior
   con `/adquirir`.
2. **El backfill del string concatenado es imperfecto** por diseño: no
   hay forma segura de partirlo. Queda como un regalo con el string
   entero, para revisar a mano si hiciera falta.
3. **Las fotos de Nicole requieren R2 configurado.** Sin credenciales la
   sección queda visible pero los endpoints responden 503, igual que las
   fotos de referencia hoy.
