# Plan: Mejoras al catálogo y wishlist

## Estado
Borrador. Deriva de [spec.md](./spec.md). El stack y las convenciones son
los de [001-baby-wishlist/plan.md](../001-baby-wishlist/plan.md) y no
cambian.

## Cambios al modelo de datos

```
items (campos nuevos)
  cantidad              int, default 1, CHECK >= 1
  cantidad_recibida     int, default 0, CHECK >= 0
  categoria_id          FK -> categorias, nullable
  prioridad             enum('URGENTE','NORMAL','PUEDE_ESPERAR') default NORMAL
  rango_precio          enum('BAJO','MEDIO','ALTO'), nullable

categorias (nueva)
  id, nombre (único)

reservas (campos nuevos)
  unidad                int    — número de slot dentro del item
  mensaje               text, nullable
```

### Índice de unicidad

El índice parcial de la v1 (`item_id WHERE released_at IS NULL`) permitía
una sola reserva activa por item. Se reemplaza por:

```sql
CREATE UNIQUE INDEX uq_reservas_item_unidad
  ON reservas (item_id, unidad) WHERE released_at IS NULL
```

Para `cantidad = 1` el comportamiento es idéntico al de la v1 (solo puede
existir la unidad 1).

### Estado derivado

`items.estado` se mantiene (filtros y vistas de la v1 siguen andando)
pero pasa a recalcularse tras cada cambio:

| Condición | Estado |
|---|---|
| `cantidad_recibida == cantidad` | `ADQUIRIDO` |
| `cantidad_recibida + reservas_activas == cantidad` | `RESERVADO` |
| resto | `NECESITADO` |

## Concurrencia: cómo se protege la última unidad

El índice único por sí solo **no** alcanza: dos reservas concurrentes
podrían tomar números de unidad distintos y superar la cantidad. La
protección real es un lock de fila sobre el item:

```python
item = db.query(Item).filter(Item.id == item_id).with_for_update().first()
```

`SELECT ... FOR UPDATE` serializa las reservas del mismo item, de modo que
el chequeo de disponibilidad y la asignación del número de unidad ocurren
sin carreras. El índice único queda como segunda línea de defensa.

La unidad asignada es el menor entero positivo libre entre las reservas
activas (los números de unidades ya recibidas se reciclan; la capacidad la
controla `cantidad_recibida + activas < cantidad`).

## Endpoints

### Nuevos
- `GET /categorias`, `POST /categorias` — mismo patrón que cajas.
- `GET /items/{id}/reservas` — admin. Lista las reservas activas con `id`
  y `dias_desde_reserva`. **Nunca** incluye nombre ni mensaje.
- `POST /items/{id}/reservas/{reserva_id}/recibir` — marca esa unidad como
  recibida y devuelve el nombre y mensaje revelados.
- `POST /items/{id}/reservas/{reserva_id}/liberar` — libera esa unidad sin
  revelar nada. **Reemplaza** a `POST /items/{id}/liberar-reserva` de la
  v1.
- `GET /items/buscar?q=` — admin. Busca por nombre y descripción,
  insensible a mayúsculas y acentos, y devuelve el item con su caja.

### Modificados
- `PATCH /items` (crear/editar): aceptan `cantidad`, `categoria_id`,
  `prioridad`, `rango_precio`. Bajar `cantidad` por debajo de
  `cantidad_recibida + activas` responde 409.
- `PATCH /items/{id}/adquirir`: pasa a recibir **todas las unidades
  restantes** como compra propia o regalo cargado a mano. Sigue
  respondiendo 409 si hay reservas activas (hay que resolverlas primero).
  Para `cantidad = 1` se comporta igual que en la v1.
- `POST /w/{token}/items/{id}/reservar`: acepta `mensaje` opcional y
  devuelve también la `unidad` asignada.
- `GET /w/{share_token}`: incluye `cantidad`, `disponibles`, `categoria`,
  `prioridad` y `rango_precio`; ordena por prioridad y agrupa por
  categoría.

### Búsqueda sin acentos

Sin extensiones de Postgres (`unaccent` no está garantizado en todos los
hosts), se normaliza en SQL:

```sql
translate(lower(nombre), 'áéíóúüñ', 'aeiouun') LIKE :q
```

Suficiente para español y portable.

## Frontend

- **Admin**: campo de cantidad, selector de categoría (con creación al
  vuelo, igual que cajas), prioridad y rango de precio en el formulario.
  La tarjeta muestra `recibidas/cantidad`. Un panel por item lista las
  reservas activas con su antigüedad ("hace 3 meses", destacando >60 días)
  y botones de recibir/liberar por unidad.
- **Buscador**: campo en el catálogo que filtra contra `/items/buscar` y
  muestra la caja de cada resultado.
- **Wishlist pública**: badges de prioridad y rango de precio, contador
  "quedan N de M", agrupación por categoría con los urgentes primero, y
  campo de mensaje opcional en el modal de reserva.
- **PWA**: `@vite-pwa/nuxt` con el ícono de Nicole y el nombre configurado,
  mismo patrón que FinTrack.

## Migraciones

Una sola migración con todo el bloque de cambios. Puntos de cuidado:

1. Backfill: `cantidad = 1`, `cantidad_recibida = 1` para los items ya
   `ADQUIRIDO` y `0` para el resto; `prioridad = NORMAL`.
2. Backfill de `reservas.unidad = 1` (en la v1 solo había una activa por
   item).
3. Drop del índice viejo y creación del nuevo.
4. El `downgrade` debe eliminar los tipos ENUM nuevos (misma lección que
   la migración de items en la v1).

## Riesgo conocido

`PATCH /items/{id}/adquirir` cambia de semántica: pasa de "marcar el item"
a "recibir las unidades restantes". Es compatible para `cantidad = 1`,
que es el 100% de los datos actuales, pero los tests de la v1 que cubren
ese endpoint hay que revisarlos uno por uno.
