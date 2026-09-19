# Plan: Página pública de celebración

## Estado
Borrador. Deriva de [spec.md](./spec.md). Stack sin cambios.

## Backend

Un solo cambio: `GET /w/{share_token}` suma el muro de agradecimiento a
lo que ya devuelve.

```
GET /w/{share_token}
  nombre_app
  items      → lo que falta (ya existía)
  recibidos  → NUEVO: el muro
```

Cada entrada de `recibidos` lleva: nombre del objeto, persona, y una
foto (la de Nicole usando el regalo si existe; si no, la de referencia del
catálogo).

Reglas de qué entra al muro:

- Solo regalos con `origen = REGALO` y `persona` no vacía. Lo que
  compraron ellos no va: no hay a quién agradecer.
- Solo regalos **ya registrados**, que por definición son los recibidos.
  Las reservas pendientes no son regalos todavía, así que la sorpresa no
  corre riesgo — sale gratis por cómo quedó el modelo en el 003.
- Orden: más recientes primero.

Va en el mismo endpoint y no en uno nuevo porque es una sola página que
se pinta de una: dos requests para el mismo render no aportan nada.

## Frontend

### Paleta

Se reemplaza la rosa actual por la del diseño, **en toda la app**. Nuxt UI
usa `ui.primary` y `ui.gray`, así que alcanza con redefinir esas dos
escalas en `tailwind.config.ts` y todo lo existente las toma solo.

```
pink (primary — rosa vino)      neutral (superficies — crema y oscuros)
  50  #fbf5f4                     50  #fdf9f0   ← fondo de página
 100  #f7e9e8                    100  #f7f3ea
 200  #ecd2d1                    200  #ece8df
 300  #dfb3b3                    300  #dddad1
 400  #c98d8e                    400  #b5afa4
 500  #b06d6e                    500  #857372   ← outline
 600  #8c4c4d   ← primary        600  #6b5f5e
 700  #743f40                    700  #534343   ← texto secundario
 800  #5f3536                    800  #332b2b
 900  #4f2e2f                    900  #1c1c17   ← texto principal
 950  #2a1717                    950  #121210
```

Los fondos pasan de `bg-pink-*` a `bg-neutral-50/100`: el crema es la
superficie del diseño y el rosa queda para los acentos.

### Tipografía

Serif (Libre Caslon Text) solo en los títulos de la página pública. El
admin sigue con la sans: son tablas y datos, y ahí la serif estorba. Se
carga con `@nuxtjs/google-fonts` para no depender de un `<link>` externo
en runtime.

### La página

`pages/w/[token].vue` se reescribe con tres bloques:

1. **Hero** — nombre configurado, la frase "Florece donde estás plantada"
   (quitada después, en la 005)
   y la ilustración floral. Si la ilustración no está en
   `frontend/public/`, el bloque se degrada al ícono de Nicole sin romper.
2. **Regalos recibidos** — grilla de tarjetas con la foto, el objeto y de
   parte de quién. No aparece si todavía no hay ninguno.
3. **Lista de deseos** — lo que ya existe (agrupado por categoría,
   urgentes primero, reservar), con el estilo nuevo.

Se saca el RSVP del diseño de Stitch por decisión del spec.

## Qué no se toma del export de Stitch

Tailwind por CDN, Material Symbols, las imágenes de `googleusercontent`
(son temporales) y el markup crudo. Ver el detalle en el spec.

## Riesgo

El cambio de paleta toca **todas** las pantallas a la vez. No hay tests
visuales, así que hay que recorrer login, catálogo, regalos, ajustes y la
pública en el navegador, en claro y oscuro, antes de cerrar.
