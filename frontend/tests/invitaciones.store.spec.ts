import { mockNuxtImport } from '@nuxt/test-utils/runtime'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Invitacion } from '~/stores/invitaciones'
import { useInvitacionesStore } from '~/stores/invitaciones'

const { apiMock, fetchMock } = vi.hoisted(() => ({
  apiMock: vi.fn(),
  fetchMock: vi.fn(),
}))
mockNuxtImport('useApi', () => () => apiMock)
vi.stubGlobal('$fetch', fetchMock)

function invitacion(over: Partial<Invitacion> = {}): Invitacion {
  return {
    id: 1,
    token: 'tok-1',
    titulo: 'Tanda de la familia',
    lugar: null,
    fecha: null,
    hora: null,
    texto: null,
    aviso: null,
    imagen_url: null,
    pide_cantidad: false,
    muestra_wishlist: true,
    asisten: 0,
    no_asisten: 0,
    created_at: '2026-09-01T12:00:00Z',
    ...over,
  }
}

describe('store invitaciones', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    apiMock.mockReset()
    fetchMock.mockReset()
  })

  it('fetchAll trae la lista', async () => {
    const store = useInvitacionesStore()
    apiMock.mockResolvedValue([invitacion(), invitacion({ id: 2 })])
    await store.fetchAll()

    expect(apiMock).toHaveBeenCalledWith('/invitaciones')
    expect(store.invitaciones).toHaveLength(2)
    expect(store.cargando).toBe(false)
  })

  it('cargando vuelve a false aunque falle', async () => {
    const store = useInvitacionesStore()
    apiMock.mockRejectedValue(new Error('sin red'))

    await expect(store.fetchAll()).rejects.toThrow()
    expect(store.cargando).toBe(false)
  })

  it('crear pone la nueva primero', async () => {
    const store = useInvitacionesStore()
    store.invitaciones = [invitacion({ id: 1 })]
    apiMock.mockResolvedValue(invitacion({ id: 9, titulo: 'Amigas' }))

    await store.crear('Amigas')

    expect(apiMock).toHaveBeenCalledWith('/invitaciones', {
      method: 'POST',
      body: { titulo: 'Amigas' },
    })
    expect(store.invitaciones[0]!.id).toBe(9)
  })

  it('editar reemplaza la que ya estaba', async () => {
    const store = useInvitacionesStore()
    store.invitaciones = [invitacion({ id: 1 }), invitacion({ id: 2 })]
    apiMock.mockResolvedValue(invitacion({ id: 2, titulo: 'Corregido' }))

    await store.editar(2, { titulo: 'Corregido' })

    expect(store.invitaciones[1]!.titulo).toBe('Corregido')
    expect(store.invitaciones).toHaveLength(2)
  })

  it('eliminar la saca del listado', async () => {
    const store = useInvitacionesStore()
    store.invitaciones = [invitacion({ id: 1 }), invitacion({ id: 2 })]
    apiMock.mockResolvedValue(undefined)

    await store.eliminar(1)

    expect(store.invitaciones.map((i) => i.id)).toEqual([2])
  })

  it('subirImagen firma, sube y confirma', async () => {
    const store = useInvitacionesStore()
    store.invitaciones = [invitacion({ id: 1 })]
    apiMock
      .mockResolvedValueOnce({ upload_url: 'https://r2/put', key: 'k1' })
      .mockResolvedValueOnce(invitacion({ id: 1, imagen_url: 'https://r2/k1' }))
    fetchMock.mockResolvedValue(undefined)

    const file = new File(['x'], 'lamina.webp', { type: 'image/webp' })
    await store.subirImagen(1, file)

    expect(apiMock).toHaveBeenNthCalledWith(1, '/invitaciones/1/imagen/presign', {
      method: 'POST',
      body: { content_type: 'image/webp', size_bytes: file.size },
    })
    expect(fetchMock).toHaveBeenCalledWith('https://r2/put', {
      method: 'PUT',
      body: file,
      headers: { 'Content-Type': 'image/webp' },
    })
    expect(store.invitaciones[0]!.imagen_url).toBe('https://r2/k1')
  })

  it('quitarImagen vuelve a la lamina por defecto', async () => {
    const store = useInvitacionesStore()
    store.invitaciones = [invitacion({ id: 1, imagen_url: 'https://r2/k1' })]
    apiMock.mockResolvedValue(invitacion({ id: 1, imagen_url: null }))

    await store.quitarImagen(1)

    expect(apiMock).toHaveBeenCalledWith('/invitaciones/1/imagen', {
      method: 'DELETE',
    })
    expect(store.invitaciones[0]!.imagen_url).toBeNull()
  })
})
