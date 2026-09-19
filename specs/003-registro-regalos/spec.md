# Spec: Registro de regalos

## Estado
Borrador — pendiente de revisión. Extiende
[001-baby-wishlist](../001-baby-wishlist/spec.md) y
[002-mejoras](../002-mejoras/spec.md).

## Motivación

La app se construyó con la wishlist como centro, pero el uso real es otro:
**el propósito principal es llevar el registro de qué recibimos, de parte
de quién, y dónde quedó guardado** — durante todo el proceso, no solo el
baby shower. La wishlist es un canal más por el que llegan regalos, no la
identidad de la app.

Tres huecos concretos que eso deja hoy:

1. **`gifter_name` es un string concatenado.** Si Ana regala dos bodies y
   Beto uno, queda `"Ana, Ana, Beto"`. No se puede responder "¿qué nos
   regaló Ana?", que es justo la pregunta para agradecer.
2. **Registrar un regalo que llegó en mano son tres pasos** (crear objeto,
   marcar adquirido, escribir nombre), y la mayoría de los regalos nunca
   pasan por la wishlist.
3. **No hay forma de agradecer con evidencia.** Queremos mandarle a cada
   persona una foto de Nicole usando lo que regaló.

## Historias de usuario

### Registrar lo que llega

1. **Anotar un regalo en un solo paso**
   Como admin, quiero registrar "recibimos X de parte de Y" sin pasos
   previos, para poder cargar varios regalos seguidos cuando llegan.
   - AC: si el objeto no existe en el catálogo, se crea en el mismo paso.
   - AC: si existe, se asocia al existente sin duplicarlo.
   - AC: el nombre de quien regala es texto libre, con autocompletado de
     los nombres ya usados, para que no queden variantes del mismo
     nombre.
   - AC: se puede indicar la fecha (por defecto hoy) y una nota.

2. **Registrar varias unidades del mismo objeto**
   Como admin, quiero registrar que una persona regaló varias unidades de
   lo mismo, sin cargar el regalo una vez por unidad.
   - AC: la cantidad regalada suma a `cantidad_recibida` del objeto.

3. **Registrar algo que compramos nosotros**
   Como admin, quiero anotar lo que compramos nosotros, para que el
   catálogo refleje lo que ya tenemos aunque no sea un regalo.

### Saber quién regaló qué

4. **Ver todo lo que regaló una persona**
   Como admin, quiero ver la lista de lo que nos regaló cada persona, para
   agradecer sin olvidarme de nada.
   - AC: los regalos se agrupan por nombre de persona.
   - AC: se ve qué regaló, cuándo, y si ya le agradecimos.

5. **Marcar que ya agradecimos**
   Como admin, quiero marcar un regalo como agradecido, para saber a quién
   me falta escribirle.
   - AC: se puede filtrar por "pendientes de agradecer".

6. **Guardar la foto de Nicole usando el regalo**
   Como admin, quiero subir una foto de Nicole usando lo que nos
   regalaron, para mandársela después a esa persona.
   - AC: la foto se asocia **al regalo**, no al objeto: si dos personas
     regalaron lo mismo, cada una tiene la suya.
   - AC: se pueden subir varias fotos por regalo.
   - AC: desde la app se puede ver y descargar la foto para compartirla a
     mano (mensaje, mail); la app no envía nada por su cuenta.

### Encontrar y organizar

7. **Clasificar por etapa**
   Como admin, quiero indicar para qué etapa sirve cada objeto, para saber
   qué usar en cada momento y qué todavía no hace falta.
   - AC: lista fija: recién nacido, 0-3 meses, 3-6 meses, 6-12 meses,
     1-2 años, más de 2 años, y "cualquier etapa".
   - AC: la etapa es independiente de la categoría (un body es categoría
     *ropa* y etapa *0-3 meses*).

8. **Filtrar el catálogo**
   Como admin, quiero filtrar por etapa y por estado (lo tenemos /
   pendiente), para ver rápido qué falta para la etapa que viene.

9. **Buscar y saber todo de un objeto**
   Como admin, quiero buscar un objeto y ver en un solo lugar **quién lo
   regaló, en qué caja está y para qué etapa es**.
   - AC: la búsqueda sigue siendo por texto parcial, sin distinguir
     mayúsculas ni acentos.

## Reglas de negocio

- `cantidad_recibida` de un objeto pasa a derivarse de la suma de sus
  regalos; deja de moverse a mano.
- Un regalo registrado a mano no tiene sorpresa que preservar: el nombre
  se ve de inmediato.
- Una reserva de la wishlist sigue oculta hasta marcarse recibida; al
  recibirla **se convierte en un regalo** con el nombre y el mensaje que
  había dejado la persona.
- Borrar un regalo devuelve el objeto al estado que corresponda.

## Fuera de alcance

- Enviar las fotos o los agradecimientos desde la app (se comparten a
  mano).
- Personas como entidad con datos de contacto: el nombre es texto libre
  con autocompletado.
- Widgets configurables en la pantalla principal ("addons"): idea
  registrada para más adelante.
- Integración con Google Photos.

## Decisiones confirmadas

1. **Persona como texto libre con autocompletado**, no entidad.
2. **Etapas de lista fija**, complementarias a las categorías.
3. **Fotos en Cloudflare R2**, colgando del regalo.
4. El registro cubre **todo el proceso**, no solo el baby shower.
