import { defineStore } from 'pinia'

export interface Invitacion {
  id: number
  token: string
  titulo: string
  lugar: string | null
  fecha: string | null
  hora: string | null
  texto: string | null
  aviso: string | null
  imagen_url: string | null
  pide_cantidad: boolean
  muestra_wishlist: boolean
  asisten: number
  no_asisten: number
  created_at: string
}

export type CamposInvitacion = Partial<
  Pick<
    Invitacion,
    | 'titulo'
    | 'lugar'
    | 'fecha'
    | 'hora'
    | 'texto'
    | 'aviso'
    | 'pide_cantidad'
    | 'muestra_wishlist'
  >
>

export const useInvitacionesStore = defineStore('invitaciones', {
  state: () => ({
    invitaciones: [] as Invitacion[],
    cargando: false,
  }),
  actions: {
    _reemplazar(inv: Invitacion) {
      const i = this.invitaciones.findIndex((x) => x.id === inv.id)
      if (i >= 0) this.invitaciones[i] = inv
    },
    async fetchAll() {
      const api = useApi()
      this.cargando = true
      try {
        this.invitaciones = await api<Invitacion[]>('/invitaciones')
      } finally {
        this.cargando = false
      }
    },
    async crear(titulo: string) {
      const api = useApi()
      const inv = await api<Invitacion>('/invitaciones', {
        method: 'POST',
        body: { titulo },
      })
      this.invitaciones.unshift(inv)
      return inv
    },
    async editar(id: number, cambios: CamposInvitacion) {
      const api = useApi()
      const inv = await api<Invitacion>(`/invitaciones/${id}`, {
        method: 'PATCH',
        body: cambios,
      })
      this._reemplazar(inv)
      return inv
    },
    async eliminar(id: number) {
      const api = useApi()
      await api(`/invitaciones/${id}`, { method: 'DELETE' })
      this.invitaciones = this.invitaciones.filter((i) => i.id !== id)
    },
    /** Sube una lámina propia para esa invitación. */
    async subirImagen(id: number, file: File) {
      const api = useApi()
      const presign = await api<{ upload_url: string; key: string }>(
        `/invitaciones/${id}/imagen/presign`,
        {
          method: 'POST',
          body: { content_type: file.type, size_bytes: file.size },
        },
      )
      await $fetch(presign.upload_url, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type },
      })
      const inv = await api<Invitacion>(`/invitaciones/${id}/imagen`, {
        method: 'POST',
        body: { key: presign.key, orden: 0 },
      })
      this._reemplazar(inv)
      return inv
    },
    async quitarImagen(id: number) {
      const api = useApi()
      const inv = await api<Invitacion>(`/invitaciones/${id}/imagen`, {
        method: 'DELETE',
      })
      this._reemplazar(inv)
      return inv
    },
  },
})
