# Spec: Catálogo y Wishlist para Bebé

## Estado
Confirmado con el usuario (ver decisiones en "Supuestos confirmados").

## Visión
Una app para que una pareja que espera un bebé lleve el catálogo de todo lo
que necesita comprar (o le pueden regalar), sepa qué ya tiene y dónde está
guardado, y pueda compartir una wishlist con familiares/amigos para evitar
regalos duplicados — preservando la sorpresa de quién regaló qué hasta que
el regalo llega físicamente.

## Problema
Sin esto, la pareja maneja el registro de cosas por comprar en la cabeza o
en notas sueltas, no tiene forma fácil de coordinar con la familia para
evitar duplicados, y una vez que el bebé nace, no recuerdan en qué caja
guardaron cada cosa.

## Usuarios
- **Admin (la pareja)**: los únicos que agregan/editan items, marcan
  adquisición y asignan cajas de almacenamiento. Login compartido entre
  ambos, sin roles diferenciados.
- **Invitado (familiar/amigo)**: accede sin cuenta vía un link compartido,
  puede reservar un item indicando su nombre. No tiene ninguna otra acción
  disponible.

## Historias de usuario

### Admin

1. **Agregar item al catálogo**
   Como admin, quiero crear un item con nombre y, opcionalmente, un link de
   Amazon y/o fotos de referencia.
   - AC: nombre es obligatorio; link y fotos son opcionales; se pueden
     adjuntar varias fotos por item.

2. **Marcar item como adquirido**
   Como admin, quiero marcar un item como adquirido e indicar si lo
   compramos nosotros o fue un regalo.
   - AC: si elijo "regalo" y el item nunca fue reservado desde la wishlist
     compartida, puedo escribir el nombre de quien regaló directamente (no
     hay sorpresa que preservar, porque yo mismo lo estoy cargando).
   - AC: si el item **sí** fue reservado desde la wishlist compartida, el
     nombre del reservante se revela automáticamente recién en este paso
     (ver historia 6).

3. **Asignar caja de almacenamiento**
   Como admin, quiero asociar un item adquirido a una caja de
   almacenamiento (identificador + descripción/ubicación opcional), para
   encontrarlo rápido después.
   - AC: las cajas se pueden crear al vuelo o reutilizar una existente.
   - AC: el campo de caja solo aplica a items ya adquiridos.

4. **Compartir la wishlist**
   Como admin, quiero generar un link público para compartir el catálogo
   con familiares y amigos.
   - AC: el link muestra únicamente los items en estado "necesitado" (no
     reservados ni adquiridos).

5. **Ver estado general sin espoilear sorpresas**
   Como admin, quiero ver cuántos items están reservados (aunque no sepa
   por quién todavía), para tener una idea de cobertura sin arruinar la
   sorpresa.
   - AC: la vista admin muestra el item en estado "reservado" pero el
     campo de nombre permanece oculto hasta marcarlo como recibido.

6. **Revelar quién regaló al marcar recibido**
   Como admin, al marcar un item reservado como "recibido", quiero que se
   revele el nombre de quien lo reservó originalmente.
   - AC: la revelación ocurre automáticamente en el mismo paso que marcar
     "adquirido" para un item que estaba en estado "reservado".
   - AC: hasta ese momento, ningún admin puede ver el nombre por ningún
     medio — la sorpresa es real también para la pareja.

7. **Enterarse de que hubo actividad, sin espoiler**
   Como admin, quiero recibir un aviso simple (ej. email o contador en la
   app) cuando alguien reserva un item, sin que se revele el nombre del
   reservante ni necesariamente qué item fue, para saber que hay
   actividad sin arruinar la sorpresa.
   - AC: el aviso no incluye el nombre del reservante.
   - AC: mecanismo exacto (email puntual, resumen, o contador in-app) se
     define en la fase de plan.

### Invitado

8. **Ver la wishlist compartida**
   Como invitado con el link, quiero ver los items disponibles (con foto o
   link de Amazon si existen) para elegir qué regalar.

9. **Reservar un item**
   Como invitado, quiero indicar que voy a regalar un item ingresando mi
   nombre, para que se quite de la lista pública y nadie más lo duplique.
   - AC: al reservar, el item desaparece inmediatamente de la vista
     pública para otros invitados.
   - AC: mi nombre no se muestra a nadie (ni admin ni otros invitados)
     hasta que el admin marque el item como recibido.
   - AC: no requiero cuenta ni login para reservar.

10. **Deshacer mi propia reserva**
   Como invitado, quiero poder liberar un item que reservé si me
   arrepiento, para que vuelva a estar disponible para otros.
   - AC: como no hay cuentas, al reservar recibo un link/código privado
     de "deshacer" que debo conservar (ej. guardado en el navegador o
     mostrado una sola vez al confirmar la reserva).
   - AC: al deshacer, el item vuelve a aparecer en la wishlist pública y
     pierde cualquier nombre asociado.

11. **Configurar el nombre de la app**
    Como admin, quiero poder cambiar el nombre que se muestra en la app
    desde una pantalla de configuración.
    - AC: el valor por defecto es "Nicole en Camino".
    - AC: el nombre configurado se muestra en el header tanto de la vista
      admin como de la wishlist pública.

12. **Eliminar un item**
    Como admin, quiero poder eliminar un item que agregamos por error o
    que ya no queremos, para mantener el catálogo limpio.
    - AC: eliminar pide confirmación.
    - AC: si el item está `reservado`, no se puede eliminar directamente:
      primero hay que liberar la reserva (historia 13). Esto evita borrar
      un regalo que alguien ya se comprometió a traer sin darse cuenta.
    - AC: al eliminar se borran también sus fotos asociadas.

13. **Liberar una reserva sin arruinar la sorpresa**
    Como admin, quiero poder liberar la reserva de un item (por ejemplo,
    si pasó mucho tiempo y el regalo nunca llegó, o si necesitamos
    comprarlo nosotros con urgencia), sin que se me revele quién lo había
    reservado.
    - AC: el item vuelve al estado `necesitado` y reaparece en la
      wishlist pública.
    - AC: el nombre del reservante NUNCA se muestra al liberar — la
      reserva se descarta sin revelarse.
    - AC: la acción pide confirmación explicando la consecuencia (la
      persona que reservó no será notificada).

## Identidad visual

- **Nombre por defecto**: "Nicole en Camino" (editable, ver historia 11).
- **Ícono**: insignia circular con una "J" trazada a mano y un pequeño
  destello decorativo; cambia automáticamente a la variante oscura según
  el modo del sistema.
- **Paleta de colores**: tonos rosados para modo claro (mauve `#c594aa`
  como color primario, rosas claros `#fdcae1` y `#ffe5f0` para fondos/
  superficies) y tonos casi negros para modo oscuro (`#131313`,
  `#050505`). Detalle técnico de la paleta en plan.md.

## Modelo conceptual (entidades, sin implementación aún)

- **Item**: nombre, descripción, link de Amazon (opcional), fotos
  (opcional, múltiples), estado (`necesitado` / `reservado` / `adquirido`),
  origen de adquisición (`nosotros` / `regalo`, solo si adquirido), nombre
  de quien regaló (opcional, con visibilidad condicionada — ver reglas de
  revelación), caja de almacenamiento asociada (opcional, solo si
  adquirido).
- **Caja de almacenamiento**: identificador/etiqueta, descripción o
  ubicación opcional.
- **Reserva**: item asociado, nombre de quien reserva, fecha de reserva,
  bandera de "revelado" (se activa cuando el admin marca el item como
  recibido).

## Reglas de negocio clave

- Un item reservado desaparece de la wishlist pública inmediatamente.
- El nombre de quien reserva un item vía wishlist está oculto **para
  todos, incluido el admin**, hasta que el admin marca el item como
  recibido — esto preserva la sorpresa de quién trajo cada regalo.
- Si el admin carga un regalo manualmente (sin pasar por reserva online),
  no hay ocultamiento: el nombre se guarda y muestra de inmediato.
- La caja de almacenamiento solo tiene sentido para items ya adquiridos.
- Un item `reservado` no puede marcarse como adquirido con origen
  "nosotros" ni eliminarse directamente: primero se libera la reserva
  (sin revelar el nombre). Marcarlo adquirido como "regalo recibido" sí
  procede directo, revelando el nombre (historia 6).
- Solo puede existir una reserva activa por item; dos invitados no pueden
  reservar el mismo item aunque lo intenten al mismo tiempo.

## Fuera de alcance (por ahora)

- Pagos o integración con la API de Amazon (precio, stock) — el link es
  solo una referencia.
- Múltiples wishlists o múltiples bebés.
- Roles diferenciados entre los dos admins (comparten el mismo acceso).
- App nativa mobile — solo web responsive.

## Criterios de éxito

- La pareja puede administrar el catálogo sin fricción desde el celular.
- Un invitado puede reservar un item en menos de un minuto, sin crear
  cuenta.
- Cero regalos duplicados una vez que la wishlist está en uso activo.
- Después de nacer el bebé, cualquier item adquirido se puede ubicar por
  su caja de almacenamiento.

## Supuestos confirmados

1. El ocultamiento del nombre del regalador aplica también para el admin
   — sorpresa real para la pareja, no solo para otros invitados.
2. Los admins reciben un aviso simple (sin nombre) cuando alguien reserva
   un item; el mecanismo exacto se decide en la fase de plan.
3. El invitado puede liberar su propia reserva mediante un link/código
   privado entregado al momento de reservar (no hay cuentas de usuario).
