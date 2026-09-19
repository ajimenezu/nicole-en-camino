import { defineStore } from 'pinia'

const NOMBRE_DEFAULT = 'Nicole en Camino'

/** Campos del evento. Se editan desde Ajustes y se leen desde el
 *  endpoint de la invitación, contra su token — no desde /config, que es
 *  público y sin token. */
export interface CambiosConfig {
  nombre_app?: string
  evento_lugar?: string
  evento_fecha?: string
  evento_hora?: string
  evento_texto?: string
  evento_aviso?: string
}

export const useConfigStore = defineStore('config', {
  state: () => ({
    nombreApp: NOMBRE_DEFAULT,
    cargado: false,
  }),
  actions: {
    async fetch() {
      if (this.cargado) return
      try {
        const config = useRuntimeConfig()
        const data = await $fetch<{ nombre_app: string }>('/config', {
          baseURL: config.public.apiBase,
        })
        this.nombreApp = data.nombre_app
        this.cargado = true
      } catch {
        // Sin backend disponible se mantiene el default — la UI no se rompe.
      }
    },
    async guardar(cambios: CambiosConfig) {
      const api = useApi()
      const data = await api<{ nombre_app: string }>('/config', {
        method: 'PATCH',
        body: cambios,
      })
      this.nombreApp = data.nombre_app
      return data
    },
    setNombre(nombre: string) {
      this.nombreApp = nombre
    },
  },
})
