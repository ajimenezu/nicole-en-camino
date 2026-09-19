# Spec: Página pública de celebración

## Estado
Implementado. Se construyó después del
[003-registro-regalos](../003-registro-regalos/spec.md), del que toma los
datos. Este documento existe para no perder las decisiones ya tomadas.

## Motivación

Hoy hay dos superficies: la app de administración (densa, funcional) y la
wishlist pública (una grilla mínima). Falta la **cara linda del proyecto**:
la página que se comparte por mensaje, con la identidad visual de Nicole,
que sirve tanto para agradecer como para invitar a regalar.

El diseño de referencia se hizo en Google Stitch (ver
[`design/`](./design/)).

## Alcance

Una sola página pública que reemplaza a la wishlist actual como destino
del link compartido, con tres bloques:

1. **Hero** — nombre, la frase "Florece donde estás plantada" (quitada
   después, en la 005: no gustó) y la
   ilustración floral.
2. **Regalos recibidos** — muro de agradecimiento: qué recibieron y de
   parte de quién.
3. **Lista de deseos** — lo que falta, con la reserva que ya funciona.

## Decisiones tomadas

1. **El muro muestra los nombres.** "Cuna de madera — de la familia
   López". Es agradecer en público.
   - Solo aparecen regalos **ya recibidos**: las reservas pendientes
     siguen ocultas, así que la sorpresa no se ve afectada.
   - Los regalos cargados con `origen = NOSOTROS` no aparecen en el muro
     (no hay a quién agradecer).
2. **Sin RSVP.** El ítem del menú se saca. Si más adelante quieren
   confirmación de asistencia al baby shower, es un spec aparte.
3. **La página pública se hace después del 003**, porque el muro se
   alimenta de la entidad `Regalo`.

## Identidad visual (del diseño de Stitch)

Reemplaza a la paleta rosa actual **en toda la app**, no solo acá:

```
surface / fondo      #fdf9f0   crema cálido
primary              #8c4c4d   rosa vino
primary-container    #d88c8c   rosa medio
secondary            #605a7a   lavanda
tertiary             #895025   terracota
on-surface           #1c1c17   casi negro
on-surface-variant   #534343   marrón grisáceo
outline-variant      #d7c1c1   bordes
```

- **Tipografía**: serif (Libre Caslon Text o similar) para títulos de la
  página pública; la sans actual se mantiene en el admin, donde hay
  tablas y datos y se lee mejor.
- **Ilustración floral**: va en `frontend/public/hero-flores.png`.
  **Pendiente** de que el usuario guarde el archivo; mientras no esté, el
  hero se sostiene con el ícono y la tipografía.

## Qué NO se toma del HTML exportado

- **Tailwind por CDN**: no va en producción y Nuxt UI ya trae el suyo.
- **Material Symbols**: la app usa heroicons en todas partes.
- **Las imágenes de `googleusercontent`**: son temporales de Stitch y
  van a dejar de resolver.
- **El markup crudo**: se reconstruye con los componentes de Nuxt UI que
  ya existen, para no duplicar estilos ni romper la coherencia.
- Los textos del menú y el footer están en inglés en el export
  ("Gifts Received", "Privacy"); la app es en español.

## Pendiente de definir

- Si el muro se ordena por fecha, por persona, o agrupado.
- Si la ilustración del hero es fija o cambia.
- Los "addons" de la pantalla principal del admin, que quedaron como idea
  a futuro en el 003.
