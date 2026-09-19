<script setup lang="ts">
/** La invitación al baby shower, con su propio link.
 *
 * Separada de la wishlist a propósito: esta se manda a todos los
 * convidados, mientras que la lista de regalos se pasa solo a quien
 * pregunta. Acá la invitación es lo único que hay.
 */
const route = useRoute()
const runtime = useRuntimeConfig()

const token = route.params.token as string

const LOGO = '/logo-nicole.png'
const LOGO_DARK = '/logo-nicole-dark.png'
const logoOk = ref(true)

interface InvitacionApi {
  nombre_app: string
  lugar: string | null
  fecha: string | null
  hora: string | null
  texto: string | null
  aviso: string | null
  imagen_url: string | null
  pide_cantidad: boolean
}

const datos = ref<InvitacionApi | null>(null)
const cargando = ref(true)
const error = ref(false)

onMounted(async () => {
  try {
    datos.value = await $fetch<InvitacionApi>(`/i/${token}`, {
      baseURL: runtime.public.apiBase,
    })
  } catch {
    error.value = true
  } finally {
    cargando.value = false
  }
})

useHead(() => ({ title: datos.value?.nombre_app ?? 'Nicole en Camino' }))
</script>

<template>
  <div class="min-h-screen bg-neutral-50 dark:bg-neutral-950">
    <header class="px-4 pb-4 pt-10 text-center">
      <picture v-if="logoOk">
        <source :srcset="LOGO_DARK" media="(prefers-color-scheme: dark)">
        <img
          :src="LOGO"
          alt=""
          class="mx-auto h-24 w-24 sm:h-28 sm:w-28"
          aria-hidden="true"
          @error="logoOk = false"
        >
      </picture>
      <h1
        class="mt-2 font-serif text-2xl italic text-pink-800 dark:text-pink-200"
      >
        {{ datos?.nombre_app ?? 'Nicole en Camino' }}
      </h1>
    </header>

    <main id="contenido" class="mx-auto max-w-2xl px-4 pb-16">
      <div v-if="cargando" class="py-16 text-center">
        <UIcon
          name="i-heroicons-heart"
          class="h-8 w-8 animate-pulse text-pink-400"
        />
      </div>

      <p
        v-else-if="error"
        class="py-16 text-center text-neutral-600 dark:text-neutral-400"
      >
        Este link no es válido o ya no está disponible.
      </p>

      <InvitacionRsvp
        v-else-if="datos"
        :token="token"
        :evento="datos"
        class="mt-0"
      />
    </main>
  </div>
</template>
