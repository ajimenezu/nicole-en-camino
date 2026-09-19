# Tasks: Página pública de celebración

Deriva de [plan.md](./plan.md). Conventional Commits, un commit por tarea.

## Fase 1 — Backend

- [x] P001 `RegaloPublicoOut` y `recibidos` en `GET /w/{share_token}`
      (solo `origen = REGALO` con persona, foto de Nicole o de referencia,
      más recientes primero)
- [x] P002 Tests: el muro lista los recibidos, excluye compras propias, y
      una reserva pendiente no aparece ni filtra el nombre

## Fase 2 — Identidad visual

- [x] P003 Paleta nueva en `tailwind.config.ts` (escalas `pink` y
      `neutral` del plan)
- [x] P004 Fondos de `bg-pink-*` a `bg-neutral-*` en layout y páginas
- [x] P005 [P] Fuente serif para los títulos de la página pública

## Fase 3 — La página

- [x] P006 Hero con nombre, frase e ilustración (degrada al ícono si el
      archivo no está)
- [x] P007 Muro de regalos recibidos
- [x] P008 Wishlist con el estilo nuevo, sin RSVP

## Fase 4 — Cierre

- [x] P009 Verificación en navegador: login, catálogo, regalos, ajustes y
      pública, en claro y oscuro
- [x] P010 [P] Tests frontend afectados por el cambio
- [x] P011 README y specs actualizados
