<script setup lang="ts">
/** Cuánto falta para que llegue Nicole.
 *
 * Es la única página pública sin token: el link se comparte por chat y no
 * muestra nada privado — el nombre de la app y una fecha, que es lo mismo
 * que ya dice la invitación. La wishlist y las invitaciones siguen
 * detrás de su token.
 */
import { diasHasta, fechaLegible } from '~/utils/cuentaRegresiva'

definePageMeta({ layout: false })

const runtime = useRuntimeConfig()

const nombreApp = ref('Nicole en Camino')
const fecha = ref<string | null>(null)
const cargando = ref(true)
const error = ref(false)

const LOGO = '/logo-nicole.png'
const LOGO_DARK = '/logo-nicole-dark.png'
const logoOk = ref(true)

const dias = computed(() => (fecha.value ? diasHasta(fecha.value) : null))
const cuando = computed(() => (fecha.value ? fechaLegible(fecha.value) : ''))

onMounted(async () => {
  try {
    const data = await $fetch<{ nombre_app: string; fecha_parto: string | null }>(
      '/config',
      { baseURL: runtime.public.apiBase },
    )
    nombreApp.value = data.nombre_app
    fecha.value = data.fecha_parto
  } catch {
    error.value = true
  } finally {
    cargando.value = false
  }
})

useHead(() => ({ title: nombreApp.value }))
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-neutral-50 px-4 py-10 text-center dark:bg-neutral-950">
    <picture v-if="logoOk">
      <source :srcset="LOGO_DARK" media="(prefers-color-scheme: dark)">
      <img
        :src="LOGO"
        alt=""
        class="mx-auto h-40 w-40 sm:h-52 sm:w-52"
        aria-hidden="true"
        @error="logoOk = false"
      >
    </picture>
    <img v-else src="/icon.svg" alt="" class="mx-auto h-16 w-16" aria-hidden="true">

    <h1 class="mt-4 font-serif text-4xl italic text-pink-800 sm:text-5xl dark:text-pink-200">
      {{ nombreApp }}
    </h1>

    <div v-if="cargando" class="py-16">
      <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
    </div>

    <p
      v-else-if="error"
      class="mt-10 max-w-sm text-neutral-600 dark:text-neutral-400"
    >
      No pudimos cargar la cuenta regresiva. Probá de nuevo en un momento.
    </p>

    <!-- Con fecha por delante: el número es la página. -->
    <template v-else-if="dias !== null && dias > 0">
      <p class="mt-10 text-sm uppercase tracking-[0.3em] text-neutral-500 dark:text-neutral-400">
        Faltan
      </p>
      <p class="font-serif text-7xl leading-none text-pink-700 sm:text-8xl dark:text-pink-300">
        {{ dias }}
      </p>
      <p class="mt-2 text-2xl text-pink-800 dark:text-pink-200">
        {{ dias === 1 ? 'día' : 'días' }}
      </p>
      <p class="mt-6 text-neutral-600 dark:text-neutral-400">
        para conocer a Nicole — {{ cuando }}
      </p>
    </template>

    <p
      v-else-if="dias === 0"
      class="mt-10 font-serif text-4xl italic text-pink-700 dark:text-pink-300"
    >
      ¡Es hoy!
    </p>

    <!-- La fecha ya pasó: no se inventa nada, se deja de contar. -->
    <p
      v-else-if="dias !== null"
      class="mt-10 max-w-sm text-lg text-neutral-600 dark:text-neutral-400"
    >
      La fecha prevista era el {{ cuando }}.
    </p>

    <p v-else class="mt-10 max-w-sm text-neutral-600 dark:text-neutral-400">
      Todavía no hay una fecha para contar los días. ¡Pronto!
    </p>

    <p class="mt-12 text-2xl tracking-[0.6em] text-pink-400" aria-hidden="true">
      ❀
    </p>
  </div>
</template>
