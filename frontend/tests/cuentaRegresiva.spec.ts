import { describe, expect, it } from 'vitest'
import { diasHasta, fechaLegible } from '~/utils/cuentaRegresiva'

describe('diasHasta', () => {
  it('cuenta los días que faltan', () => {
    expect(diasHasta('2027-03-15', new Date(2027, 2, 1, 10, 0))).toBe(14)
  })

  it('el mismo día es cero', () => {
    expect(diasHasta('2027-03-15', new Date(2027, 2, 15, 8, 0))).toBe(0)
  })

  it('la noche anterior todavía falta un día', () => {
    // El caso que rompe si se cuenta por horas en vez de por días.
    expect(diasHasta('2027-03-15', new Date(2027, 2, 14, 23, 30))).toBe(1)
  })

  it('una fecha pasada da negativo', () => {
    expect(diasHasta('2027-03-15', new Date(2027, 2, 20, 9, 0))).toBe(-5)
  })

  it('cruza fin de mes y año bisiesto', () => {
    expect(diasHasta('2028-03-01', new Date(2028, 1, 28, 12, 0))).toBe(2)
  })

  it('no se corre un día por la zona horaria', () => {
    // new Date('2027-03-15') sería medianoche UTC, que en América es el
    // día anterior: la cuenta daría 15 en vez de 14.
    expect(diasHasta('2027-03-15', new Date(2027, 2, 1, 23, 59))).toBe(14)
  })

  it('devuelve null si la fecha no tiene el formato esperado', () => {
    expect(diasHasta('15/03/2027')).toBeNull()
    expect(diasHasta('')).toBeNull()
  })
})

describe('fechaLegible', () => {
  it('escribe la fecha en español', () => {
    expect(fechaLegible('2027-03-15')).toBe('15 de marzo de 2027')
  })

  it('devuelve el texto original si no puede interpretarlo', () => {
    expect(fechaLegible('cualquier cosa')).toBe('cualquier cosa')
  })
})
