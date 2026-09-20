/** Achica una foto en el navegador antes de subirla al storage.
 *
 * Hace falta por tres motivos, todos del caso "sacar la foto con el
 * celular":
 *
 * 1. El backend rechaza archivos de más de 5 MB y una foto de cámara
 *    ronda los 3–12 MB, así que sin esto la subida falla seguido.
 * 2. El iPhone entrega HEIC, que no está entre los formatos aceptados.
 *    Al redibujar en un canvas y re-encodear, el formato se normaliza.
 * 3. La wishlist la abre la familia desde el celular, con datos: una
 *    foto de 200 KB en vez de 4 MB cambia por completo la carga.
 *
 * Si el navegador no sabe decodificar el archivo, se devuelve el
 * original y que decida el backend: es preferible un error claro suyo
 * a que acá se pierda la foto en silencio.
 */

export const LADO_MAXIMO = 1600
const CALIDAD = 0.82

/** Formatos que el backend acepta (ver storage.CONTENT_TYPES_PERMITIDOS). */
const PERMITIDOS = new Set(['image/jpeg', 'image/png', 'image/webp'])

/** Escala para que el lado más largo no pase de `maximo`, sin deformar.
 *
 * Nunca agranda: una imagen ya chica se devuelve tal cual.
 */
export function calcularMedidas(
  ancho: number,
  alto: number,
  maximo: number = LADO_MAXIMO,
): { ancho: number; alto: number } {
  const lado = Math.max(ancho, alto)
  if (lado <= maximo || lado === 0) return { ancho, alto }
  const factor = maximo / lado
  return { ancho: Math.round(ancho * factor), alto: Math.round(alto * factor) }
}

function nombreWebp(nombre: string): string {
  return `${nombre.replace(/\.[^.]+$/, '') || 'foto'}.webp`
}

export async function comprimirImagen(file: File): Promise<File> {
  if (!file.type.startsWith('image/')) return file

  try {
    const bitmap = await createImageBitmap(file)
    const { ancho, alto } = calcularMedidas(bitmap.width, bitmap.height)

    const canvas = document.createElement('canvas')
    canvas.width = ancho
    canvas.height = alto
    const ctx = canvas.getContext('2d')
    if (!ctx) return file
    ctx.drawImage(bitmap, 0, 0, ancho, alto)
    bitmap.close()

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, 'image/webp', CALIDAD),
    )
    if (!blob) return file

    // Si el archivo ya era válido y comprimirlo no ayudó (una imagen
    // chica y bien optimizada puede crecer al re-encodear), se deja el
    // original. Un HEIC en cambio hay que convertirlo aunque pese más.
    if (PERMITIDOS.has(file.type) && blob.size >= file.size) return file

    return new File([blob], nombreWebp(file.name), { type: 'image/webp' })
  } catch {
    return file
  }
}
