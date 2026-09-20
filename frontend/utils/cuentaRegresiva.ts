/** Cuántos días faltan para la fecha probable de parto.
 *
 * Se cuenta en días de calendario y en la hora local de quien mira, no en
 * horas: a las 23:00 de la noche anterior tiene que decir "falta 1 día",
 * no "faltan 0". Por eso las dos fechas se llevan a medianoche local
 * antes de restar.
 *
 * La fecha llega como 'YYYY-MM-DD' y se arma por partes a propósito:
 * `new Date('2027-03-15')` la interpreta en UTC, y al oeste de Greenwich
 * eso cae el día anterior, así que la cuenta daría un día de más.
 */

export function diasHasta(fechaIso: string, hoy: Date = new Date()): number | null {
  const partes = /^(\d{4})-(\d{2})-(\d{2})$/.exec(fechaIso)
  if (!partes) return null

  const [, anio, mes, dia] = partes
  const objetivo = new Date(Number(anio), Number(mes) - 1, Number(dia))
  if (Number.isNaN(objetivo.getTime())) return null

  const desde = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())
  const MS_POR_DIA = 24 * 60 * 60 * 1000
  return Math.round((objetivo.getTime() - desde.getTime()) / MS_POR_DIA)
}

/** La fecha escrita como se lee: "15 de marzo de 2027". */
export function fechaLegible(fechaIso: string): string {
  const partes = /^(\d{4})-(\d{2})-(\d{2})$/.exec(fechaIso)
  if (!partes) return fechaIso
  const [, anio, mes, dia] = partes
  return new Date(Number(anio), Number(mes) - 1, Number(dia)).toLocaleDateString(
    'es',
    { day: 'numeric', month: 'long', year: 'numeric' },
  )
}
