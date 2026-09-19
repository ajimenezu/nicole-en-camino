<script setup lang="ts">
const config = useConfigStore()
onMounted(() => config.fetch())

// El mismo logo de la guirnalda que usa la página pública. <picture>
// elige la variante clara u oscura sin JavaScript, así no parpadea al
// cargar. Si el archivo no está, cae al ícono simple.
const LOGO = '/logo-nicole.png'
const LOGO_DARK = '/logo-nicole-dark.png'
const logoOk = ref(true)
</script>

<template>
  <div class="min-h-screen bg-neutral-50 dark:bg-neutral-950">
    <header
      class="border-b border-neutral-200 bg-neutral-100/80 backdrop-blur dark:border-neutral-900 dark:bg-neutral-950/80"
    >
      <div class="mx-auto flex max-w-5xl items-center gap-3 px-4 py-3">
        <picture v-if="logoOk">
          <source :srcset="LOGO_DARK" media="(prefers-color-scheme: dark)">
          <img
            :src="LOGO"
            alt=""
            class="h-12 w-12 shrink-0 sm:h-14 sm:w-14"
            aria-hidden="true"
            @error="logoOk = false"
          >
        </picture>
        <img
          v-else
          src="/icon.svg"
          alt=""
          class="h-9 w-9 shrink-0"
          aria-hidden="true"
        >
        <h1
          class="min-w-0 truncate font-serif text-xl italic text-pink-800 dark:text-pink-200"
        >
          {{ config.nombreApp }}
        </h1>
        <slot name="header-extra" />
      </div>
    </header>
    <main id="contenido" class="mx-auto max-w-5xl p-4 sm:p-6">
      <slot />
    </main>
  </div>
</template>
