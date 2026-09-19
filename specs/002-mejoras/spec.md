# Spec: Mejoras al catálogo y wishlist

## Estado
Confirmado con el usuario. Extiende
[001-baby-wishlist](../001-baby-wishlist/spec.md), que se mantiene como
base — nada de lo especificado allí se reemplaza.

## Motivación

Con la v1 en uso aparecen tres huecos concretos:

1. Muchos items se necesitan **de a varios** (bodies, pañales, biberones)
   y hoy cada item es una sola unidad: la primera persona que reserva se
   lleva el item entero de la lista.
2. Cuando el catálogo crece, el invitado **no sabe qué hace falta de
   verdad** ni cuánto se espera que gaste.
3. Después de que nazca Nicole, ubicar algo exige recorrer el catálogo,
   aunque el dato de la caja ya esté guardado.

## Historias de usuario

### Cantidad por item

1. **Pedir varias unidades de un item**
   Como admin, quiero indicar cuántas unidades necesitamos de un item,
   para que varias personas puedan regalar una cada una.
   - AC: la cantidad es un entero ≥ 1; por defecto 1 (los items
     existentes no cambian de comportamiento).
   - AC: no se puede bajar la cantidad por debajo de las unidades ya
     reservadas o recibidas.

2. **Ver cuántas unidades faltan**
   Como invitado, quiero ver cuántas unidades quedan disponibles, para
   saber si todavía puedo aportar una.
   - AC: la wishlist pública muestra el remanente (ej. "quedan 3 de 5")
     solo cuando la cantidad es mayor a 1.
   - AC: el item desaparece de la lista pública cuando no quedan unidades
     disponibles (reservadas + recibidas = cantidad).

3. **Reservar una unidad**
   Como invitado, quiero reservar una unidad de un item, sin bloquear las
   demás para otras personas.
   - AC: dos invitados pueden reservar unidades distintas del mismo item
     al mismo tiempo sin pisarse.
   - AC: si dos intentan tomar la última unidad simultáneamente, solo uno
     lo logra y el otro recibe un aviso claro.

4. **Recibir de a poco**
   Como admin, quiero marcar unidades recibidas una por una, y que el
   item siga en la lista mientras falten.
   - AC: al recibir una unidad reservada se revela el nombre de quien la
     regaló (misma regla de sorpresa que en la v1, ahora por unidad).
   - AC: el item queda `ADQUIRIDO` recién cuando se recibieron todas las
     unidades.
   - AC: el admin ve el detalle: cuántas recibidas, cuántas reservadas y
     de quiénes fueron las ya reveladas.

### Organización del catálogo

5. **Clasificar por categoría**
   Como admin, quiero asignarle una categoría a cada item, creándolas yo
   mismo a medida que las necesito.
   - AC: las categorías son de texto libre, reutilizables (mismo patrón
     que las cajas de almacenamiento): se elige una existente o se crea al
     vuelo.
   - AC: un item puede no tener categoría.
   - AC: la wishlist pública agrupa los items por categoría, y los que no
     tienen quedan al final.

6. **Marcar prioridad**
   Como admin, quiero señalar qué items son urgentes, para que los
   invitados sepan qué hace más falta.
   - AC: tres niveles — `URGENTE`, `NORMAL` (por defecto), `PUEDE_ESPERAR`.
   - AC: la wishlist pública destaca los urgentes y los ordena primero
     dentro de su categoría.

7. **Indicar rango de precio**
   Como admin, quiero indicar un nivel de gasto aproximado, para que cada
   invitado elija algo acorde a su presupuesto.
   - AC: tres niveles opcionales — `$`, `$$`, `$$$` — sin montos exactos,
     porque el precio real lo ve en el link de la tienda.
   - AC: se muestra tanto en el admin como en la wishlist pública.

### Encontrar las cosas

8. **Buscar dónde guardamos algo**
   Como admin, quiero buscar un item por nombre y ver en qué caja está,
   para encontrarlo rápido cuando lo necesitemos.
   - AC: la búsqueda es por texto parcial sobre nombre y descripción, sin
     distinguir mayúsculas ni acentos.
   - AC: el resultado muestra la caja y su ubicación.
   - AC: es accesible desde el catálogo sin pasos intermedios.

### Detalles que suman

9. **Dejar un mensaje con el regalo**
   Como invitado, quiero poder dejar un mensaje junto a mi reserva, para
   acompañar el regalo con unas palabras.
   - AC: el mensaje es opcional.
   - AC: queda oculto exactamente igual que el nombre, y se revela junto
     con él al marcar la unidad como recibida.

10. **Saber hace cuánto está reservado**
    Como admin, quiero ver hace cuánto se reservó una unidad, para decidir
    si conviene liberarla porque el regalo nunca llegó.
    - AC: se muestra la antigüedad en lenguaje natural (ej. "hace 3
      meses"), nunca el nombre de quien reservó.
    - AC: las reservas de más de 60 días se destacan visualmente.

11. **Instalar la app en el celular**
    Como admin, quiero poder instalar la app en el teléfono, para
    entrar de una sin abrir el navegador.
    - AC: instalable (PWA) con el ícono de Nicole y el nombre configurado.
    - AC: la wishlist pública también es instalable para los invitados.

## Reglas de negocio nuevas

- `cantidad_recibida + unidades_reservadas_activas ≤ cantidad` siempre.
- Un item desaparece de la wishlist pública cuando no quedan unidades
  disponibles, aunque no esté completamente recibido.
- La sorpresa ahora es **por unidad**: recibir una unidad revela solo el
  nombre (y mensaje) de esa reserva; las demás siguen ocultas.
- Liberar una unidad por parte del admin sigue sin revelar nada.
- Bajar la cantidad de un item nunca puede dejar unidades reservadas o
  recibidas "huérfanas".

## Fuera de alcance

- Montos exactos de precio y cualquier conversión de moneda.
- Notificaciones por email (se mantiene el contador in-app de la v1).
- Reordenar items manualmente (el orden lo dan prioridad y categoría).
- Categorías anidadas.

## Decisiones confirmadas

1. **Cantidad**: se recibe por unidad, con contador; el item sigue visible
   hasta completarse.
2. **Categorías**: de texto libre creadas por la pareja, no una lista
   fija.
3. **Precio**: rango aproximado (`$` / `$$` / `$$$`), sin montos exactos.
