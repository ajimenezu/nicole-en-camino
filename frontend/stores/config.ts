import { defineStore } from 'pinia'

const NOMBRE_DEFAULT = 'Nicole en Camino'

/** Lo que se edita desde Ajustes. `fecha_parto: null` borra la fecha y
 *  con eso apaga la cuenta regresiva. Los datos del evento (lugar, hora)
 *  no viven acá: son de cada invitación y se leen contra su token. */
export interface CambiosConfig {
  nombre_app?: string
  fecha_parto?: string | null
}

interface ConfigApi {
  nombre_app: string
  fecha_parto: string | null
}

export const useConfigStore = defineStore('config', {
  state: () => ({
    nombreApp: NOMBRE_DEFAULT,
    fechaParto: null as string | null,
    cargado: false,
  }),
  actions: {
    _aplicar(data: ConfigApi) {
      this.nombreApp = data.nombre_app
      this.fechaParto = data.fecha_parto
    },
    async fetch() {
      if (this.cargado) return
      try {
        const config = useRuntimeConfig()
        this._aplicar(
          await $fetch<ConfigApi>('/config', { baseURL: config.public.apiBase }),
        )
        this.cargado = true
      } catch {
        // Sin backend disponible se mantiene el default — la UI no se rompe.
      }
    },
    async guardar(cambios: CambiosConfig) {
      const api = useApi()
      const data = await api<ConfigApi>('/config', {
        method: 'PATCH',
        body: cambios,
      })
      this._aplicar(data)
      return data
    },
    setNombre(nombre: string) {
      this.nombreApp = nombre
    },
  },
})
