import { mockNuxtImport } from '@nuxt/test-utils/runtime'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useCajasStore } from '~/stores/cajas'
import { useConfigStore } from '~/stores/config'

const { fetchMock, apiMock } = vi.hoisted(() => ({
  fetchMock: vi.fn(),
  apiMock: vi.fn(),
}))
vi.stubGlobal('$fetch', fetchMock)
mockNuxtImport('useApi', () => () => apiMock)

describe('store config', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    fetchMock.mockReset()
  })

  it('usa "Nicole en Camino" como default', () => {
    expect(useConfigStore().nombreApp).toBe('Nicole en Camino')
  })

  it('fetch trae el nombre configurado', async () => {
    fetchMock.mockResolvedValue({ nombre_app: 'Esperando a Nicole' })
    const store = useConfigStore()
    await store.fetch()
    expect(store.nombreApp).toBe('Esperando a Nicole')
    expect(store.cargado).toBe(true)
  })

  it('no vuelve a pedir el nombre si ya se cargó', async () => {
    fetchMock.mockResolvedValue({ nombre_app: 'Uno' })
    const store = useConfigStore()
    await store.fetch()
    await store.fetch()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('si la API falla mantiene el default y no rompe', async () => {
    fetchMock.mockRejectedValue(new Error('sin backend'))
    const store = useConfigStore()
    await store.fetch()
    expect(store.nombreApp).toBe('Nicole en Camino')
    expect(store.cargado).toBe(false)
  })

  it('setNombre actualiza el nombre en memoria', () => {
    const store = useConfigStore()
    store.setNombre('Nicole ya llegó')
    expect(store.nombreApp).toBe('Nicole ya llegó')
  })
})

describe('store cajas', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    apiMock.mockReset()
  })

  it('fetchAll carga las cajas', async () => {
    apiMock.mockResolvedValue([
      { id: 1, etiqueta: 'Caja A', descripcion: null },
    ])
    const store = useCajasStore()
    await store.fetchAll()
    expect(store.cajas).toHaveLength(1)
  })

  it('crear agrega la caja y las mantiene ordenadas', async () => {
    const store = useCajasStore()
    store.cajas = [{ id: 1, etiqueta: 'Caja B', descripcion: null }]
    apiMock.mockResolvedValue({ id: 2, etiqueta: 'Caja A', descripcion: 'Closet' })
    await store.crear('Caja A', 'Closet')
    expect(store.cajas.map((c) => c.etiqueta)).toEqual(['Caja A', 'Caja B'])
  })
})
