import { mockNuxtImport } from '@nuxt/test-utils/runtime'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useRegalosStore } from '~/stores/regalos'
import type { Regalo } from '~/types/api'

const { apiMock, fetchMock } = vi.hoisted(() => ({
  apiMock: vi.fn(),
  fetchMock: vi.fn(),
}))
mockNuxtImport('useApi', () => () => apiMock)
vi.stubGlobal('$fetch', fetchMock)

function regalo(over: Partial<Regalo> = {}): Regalo {
  return {
    id: 1,
    item: { id: 10, nombre: 'Cuna', etapa: 'CUALQUIERA', fotos: [] },
    persona: 'Ana',
    origen: 'REGALO',
    cantidad: 1,
    fecha: '2026-08-15',
    nota: null,
    agradecido: false,
    devuelto_en: null,
    fotos: [],
    ...over,
  }
}

describe('store regalos', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    apiMock.mockReset()
    fetchMock.mockReset()
  })

  it('registrar sobre un item existente', async () => {
    const store = useRegalosStore()
    apiMock.mockResolvedValue(regalo())
    await store.registrar({ item_id: 10, persona: 'Ana' })
    expect(apiMock).toHaveBeenCalledWith(
      '/regalos',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(store.regalos).toHaveLength(1)
  })

  it('registrar creando el item al vuelo', async () => {
    const store = useRegalosStore()
    apiMock.mockResolvedValue(
      regalo({ item: { id: 99, nombre: 'Manta', etapa: 'RECIEN_NACIDO', fotos: [] } }),
    )
    await store.registrar({
      item_nuevo: { nombre: 'Manta', etapa: 'RECIEN_NACIDO' },
      persona: 'Vecina',
    })
    expect(store.regalos[0]!.item.nombre).toBe('Manta')
  })

  it('el registro nuevo queda primero en la lista', async () => {
    const store = useRegalosStore()
    store.regalos = [regalo({ id: 1, persona: 'Viejo' })]
    apiMock.mockResolvedValue(regalo({ id: 2, persona: 'Nuevo' }))
    await store.registrar({ item_id: 10, persona: 'Nuevo' })
    expect(store.regalos[0]!.persona).toBe('Nuevo')
  })

  it('marcarAgradecido actualiza el regalo en la lista', async () => {
    const store = useRegalosStore()
    store.regalos = [regalo({ id: 1, agradecido: false })]
    apiMock.mockResolvedValue(regalo({ id: 1, agradecido: true }))
    await store.marcarAgradecido(1, true)
    expect(store.regalos[0]!.agradecido).toBe(true)
  })

  it('marcarDevuelto postea la devolución sin mandar fecha', async () => {
    // La fecha la pone el backend: el caso normal es marcarlo el día que
    // se entrega el objeto.
    const store = useRegalosStore()
    store.regalos = [regalo({ id: 1, origen: 'PRESTADO', devuelto_en: null })]
    apiMock.mockResolvedValue(
      regalo({ id: 1, origen: 'PRESTADO', devuelto_en: '2026-09-15' }),
    )

    await store.marcarDevuelto(1, true)

    expect(apiMock).toHaveBeenCalledWith('/regalos/1/devolucion', {
      method: 'POST',
    })
    expect(store.regalos[0]!.devuelto_en).toBe('2026-09-15')
  })

  it('marcarDevuelto en false deshace la devolución', async () => {
    const store = useRegalosStore()
    store.regalos = [
      regalo({ id: 1, origen: 'PRESTADO', devuelto_en: '2026-09-15' }),
    ]
    apiMock.mockResolvedValue(
      regalo({ id: 1, origen: 'PRESTADO', devuelto_en: null }),
    )

    await store.marcarDevuelto(1, false)

    expect(apiMock).toHaveBeenCalledWith('/regalos/1/devolucion', {
      method: 'DELETE',
    })
    expect(store.regalos[0]!.devuelto_en).toBeNull()
  })

  it('pendientesDeAgradecer no cuenta las compras propias', () => {
    const store = useRegalosStore()
    store.regalos = [
      regalo({ id: 1, agradecido: false }),
      regalo({ id: 2, agradecido: true }),
      regalo({ id: 3, agradecido: false, persona: '', origen: 'NOSOTROS' }),
    ]
    expect(store.pendientesDeAgradecer).toBe(1)
  })

  it('fetchPersonas alimenta el autocompletado', async () => {
    const store = useRegalosStore()
    apiMock.mockResolvedValue(['Ana', 'Beto'])
    await store.fetchPersonas('an')
    expect(apiMock).toHaveBeenCalledWith('/regalos/personas', {
      query: { q: 'an' },
    })
    expect(store.personas).toEqual(['Ana', 'Beto'])
  })

  it('fetchAll filtra por pendientes', async () => {
    const store = useRegalosStore()
    apiMock.mockResolvedValue([regalo()])
    await store.fetchAll({ agradecido: false })
    expect(apiMock).toHaveBeenCalledWith('/regalos', {
      query: { agradecido: false },
    })
  })

  it('fetchPorPersona guarda los grupos', async () => {
    const store = useRegalosStore()
    apiMock.mockResolvedValue([
      {
        persona: 'Ana',
        total_regalos: 2,
        pendientes_de_agradecer: 1,
        regalos: [regalo()],
      },
    ])
    await store.fetchPorPersona()
    expect(store.porPersona[0]!.pendientes_de_agradecer).toBe(1)
  })

  it('eliminar saca el regalo de la lista', async () => {
    const store = useRegalosStore()
    store.regalos = [regalo({ id: 1 }), regalo({ id: 2 })]
    apiMock.mockResolvedValue(undefined)
    await store.eliminar(1)
    expect(store.regalos.map((r) => r.id)).toEqual([2])
  })

  it('subirFoto usa presign y sube directo a R2', async () => {
    const store = useRegalosStore()
    store.regalos = [regalo({ id: 1 })]
    const file = new File(['x'], 'nicole.jpg', { type: 'image/jpeg' })
    apiMock
      .mockResolvedValueOnce({
        upload_url: 'https://r2.fake/put/regalos/1/a.jpg',
        key: 'regalos/1/a.jpg',
      })
      .mockResolvedValueOnce({ id: 7, url: 'https://cdn.fake/regalos/1/a.jpg', orden: 0 })
    fetchMock.mockResolvedValue(undefined)

    await store.subirFoto(1, file)

    expect(fetchMock).toHaveBeenCalledWith(
      'https://r2.fake/put/regalos/1/a.jpg',
      expect.objectContaining({ method: 'PUT' }),
    )
    expect(store.regalos[0]!.fotos).toHaveLength(1)
  })

  it('eliminarFoto la saca del regalo', async () => {
    const store = useRegalosStore()
    store.regalos = [
      regalo({
        id: 1,
        fotos: [
          { id: 7, url: 'https://cdn.fake/a.jpg', orden: 0 },
          { id: 8, url: 'https://cdn.fake/b.jpg', orden: 1 },
        ],
      }),
    ]
    apiMock.mockResolvedValue(undefined)
    await store.eliminarFoto(1, 7)
    expect(store.regalos[0]!.fotos.map((f) => f.id)).toEqual([8])
  })
})
