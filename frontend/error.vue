<script setup lang="ts">
/** Pantalla de error, sobre todo para links rotos.
 *
 * Los links de la wishlist y de las invitaciones llevan un UUID largo y
 * se pasan por chat, así que se cortan y se pegan mal: sin esto la
 * persona veía la pantalla cruda de Nuxt, en inglés. No ofrece "ir al
 * inicio" porque el inicio es el login del admin, que no le sirve a
 * quien recibió un link: lo útil es pedirlo de nuevo.
 */
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const LOGO = '/logo-nicole.png'
const LOGO_DARK = '/logo-nicole-dark.png'
const logoOk = ref(true)

const esNoEncontrado = computed(() => props.error?.statusCode === 404)

useHead({ title: esNoEncontrado.value ? 'Link no encontrado' : 'Algo salió mal' })
</script>

<template>
  <div
    class="flex min-h-screen flex-col items-center justify-center bg-neutral-50 px-4 text-center dark:bg-neutral-950"
  >
    <picture v-if="logoOk">
      <source :srcset="LOGO_DARK" media="(prefers-color-scheme: dark)">
      <img
        :src="LOGO"
        alt=""
        class="h-28 w-28 sm:h-32 sm:w-32"
        aria-hidden="true"
        @error="logoOk = false"
      >
    </picture>

    <h1
      class="mt-4 font-serif text-3xl italic text-pink-800 dark:text-pink-200"
    >
      {{ esNoEncontrado ? 'No encontramos esta página' : 'Algo salió mal' }}
    </h1>

    <p class="mt-3 max-w-sm text-neutral-600 dark:text-neutral-400">
      <template v-if="esNoEncontrado">
        Puede que el link esté incompleto: al pasarlo por chat a veces se
        corta. Pedíselo de nuevo a los papás de Nicole.
      </template>
      <template v-else>
        Fue un problema nuestro, no tuyo. Probá de nuevo en un momento.
      </template>
    </p>

    <UButton
      v-if="!esNoEncontrado"
      class="mt-6"
      icon="i-heroicons-arrow-path"
      @click="clearError({ redirect: '/' })"
    >
      Reintentar
    </UButton>

    <p class="mt-10 text-2xl tracking-[0.6em] text-pink-400" aria-hidden="true">
      ❀
    </p>
  </div>
</template>
