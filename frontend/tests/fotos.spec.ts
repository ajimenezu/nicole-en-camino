import { mockNuxtImport } from '@nuxt/test-utils/runtime'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useItemsStore } from '~/stores/items'
import type { Item } from '~/types/api'

const { apiMock, fetchMock } = vi.hoisted(() => ({
  apiMock: vi.fn(),
  fetchMock: vi.fn(),
}))
mockNuxtImport('useApi', () => () => apiMock)
vi.stubGlobal('$fetch', fetchMock)

function item(over: Partial<Item> = {}): Item {
  return {
    id: 1,
    nombre: 'Cuna',
    descripcion: null,
    amazon_link: null,
    cantidad: 1,
    cantidad_recibida: 0,
    reservas_activas: 0,
    prioridad: 'NORMAL',
    rango_precio: null,
    categoria: null,
    estado: 'NECESITADO',
    origen_adquisicion: null,
    prestamos_pendientes: 0,
    personas: [],
    etapa: 'CUALQUIERA',
    caja: null,
    fotos: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...over,
  }
}

describe('fotos de items', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    apiMock.mockReset()
    fetchMock.mockReset()
  })

  it('subirFoto hace presign, sube al storage y confirma', async () => {
    const store = useItemsStore()
    store.items = [item({ id: 1 })]
    const file = new File(['x'], 'foto.png', { type: 'image/png' })

    apiMock
      .mockResolvedValueOnce({
        upload_url: 'https://r2.fake/put/items/1/abc.png',
        key: 'items/1/abc.png',
      })
      .mockResolvedValueOnce({
        id: 10,
        url: 'https://cdn.fake/items/1/abc.png',
        orden: 0,
      })
    fetchMock.mockResolvedValue(undefined)

    await store.subirFoto(1, file)

    // El PUT va directo al storage, no al backend.
    expect(fetchMock).toHaveBeenCalledWith(
      'https://r2.fake/put/items/1/abc.png',
      expect.objectContaining({ method: 'PUT' }),
    )
    expect(store.items[0]!.fotos).toHaveLength(1)
    expect(store.items[0]!.fotos[0]!.url).toBe('https://cdn.fake/items/1/abc.png')
  })

  it('el presign viaja con tipo y tamaño del archivo', async () => {
    const store = useItemsStore()
    store.items = [item({ id: 1 })]
    const file = new File(['contenido'], 'foto.webp', { type: 'image/webp' })

    apiMock
      .mockResolvedValueOnce({ upload_url: 'https://r2.fake/put/k', key: 'items/1/k.webp' })
      .mockResolvedValueOnce({ id: 11, url: 'https://cdn.fake/k', orden: 0 })
    fetchMock.mockResolvedValue(undefined)

    await store.subirFoto(1, file)

    expect(apiMock).toHaveBeenCalledWith(
      '/items/1/fotos/presign',
      expect.objectContaining({
        body: { content_type: 'image/webp', size_bytes: file.size },
      }),
    )
  })

  it('eliminarFoto la saca del item', async () => {
    const store = useItemsStore()
    store.items = [
      item({
        id: 1,
        fotos: [
          { id: 10, url: 'https://cdn.fake/a.png', orden: 0 },
          { id: 11, url: 'https://cdn.fake/b.png', orden: 1 },
        ],
      }),
    ]
    apiMock.mockResolvedValue(undefined)

    await store.eliminarFoto(1, 10)

    expect(store.items[0]!.fotos.map((f) => f.id)).toEqual([11])
  })
})
