<script setup lang="ts">
import type { ItemPublico, WishlistPublica } from '~/types/api'
import { RANGO_PRECIO_LABEL } from '~/types/api'

definePageMeta({ layout: false })

const route = useRoute()
const runtime = useRuntimeConfig()
const toast = useToast()
const { reservas, cargar, guardar, olvidar } = useReservasLocales()

const token = computed(() => String(route.params.token))
const nombreApp = ref('Nicole en Camino')
const items = ref<ItemPublico[]>([])
const cargando = ref(true)
const error = ref(false)

const itemReservando = ref<ItemPublico | null>(null)
const nombreInvitado = ref('')
const mensajeInvitado = ref('')
const enviando = ref(false)
// Se ata en runtime y no como src estático: si el archivo todavía no está
// en public/, Vite fallaría al resolver el import en build.
const LOGO = '/logo-nicole.png'
const LOGO_DARK = '/logo-nicole-dark.png'
const logoOk = ref(true)

// Botón de volver arriba: aparece recién cuando el hero salió de vista.
const heroRef = ref<HTMLElement>()
const { y } = useWindowScroll()
const mostrarSubir = computed(
  () => y.value > (heroRef.value?.offsetHeight ?? 400) * 0.8,
)

function volverArriba() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Los items que aparté ya no vienen en la lista pública, así que se
// muestran aparte —con su nombre— para poder deshacerlos.
const misReservas = computed(() =>
  Object.entries(reservas.value).map(([id, r]) => ({
    itemId: Number(id),
    // Las reservas hechas antes de guardar el nombre no lo tienen.
    nombre: r.nombre || 'Un regalo apartado',
  })),
)

/** Agrupa por categoría preservando el orden por prioridad del backend. */
const grupos = computed(() => {
  const mapa = new Map<string, ItemPublico[]>()
  for (const item of items.value) {
    const clave = item.categoria ?? ''
    if (!mapa.has(clave)) mapa.set(clave, [])
    mapa.get(clave)!.push(item)
  }
  // Los items sin categoría van al final.
  return [...mapa.entries()].sort(([a], [b]) => {
    if (a === '') return 1
    if (b === '') return -1
    return a.localeCompare(b)
  })
})

async function fetchWishlist() {
  cargando.value = true
  try {
    const data = await $fetch<WishlistPublica>(`/w/${token.value}`, {
      baseURL: runtime.public.apiBase,
    })
    nombreApp.value = data.nombre_app
    items.value = data.items
    error.value = false
  } catch {
    error.value = true
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargar()
  fetchWishlist()
})

useHead(() => ({ title: nombreApp.value }))

async function reservar() {
  if (!itemReservando.value || !nombreInvitado.value.trim()) return
  enviando.value = true
  const item = itemReservando.value
  try {
    const data = await $fetch<{ token_deshacer: string; unidad: number }>(
      `/w/${token.value}/items/${item.id}/reservar`,
      {
        method: 'POST',
        baseURL: runtime.public.apiBase,
        body: {
          nombre: nombreInvitado.value.trim(),
          mensaje: mensajeInvitado.value.trim() || null,
        },
      },
    )
    guardar(item.id, data.token_deshacer, item.nombre)
    // Con varias unidades el item sigue disponible para otros.
    await fetchWishlist()
    itemReservando.value = null
    nombreInvitado.value = ''
    mensajeInvitado.value = ''
    toast.add({
      title: '¡Gracias! 🎁',
      description: `Anotamos que vos traés «${item.nombre}». Tu nombre queda en secreto hasta que lo reciban.`,
      color: 'pink',
      timeout: 7000,
    })
  } catch (e: unknown) {
    const status = (e as { statusCode?: number }).statusCode
    toast.add({
      title: status === 409 ? 'Alguien se adelantó' : 'No se pudo reservar',
      description:
        status === 409
          ? 'Ya no quedan unidades de este regalo. Elegí otro de la lista.'
          : 'Intentá de nuevo en un momento.',
      color: 'red',
    })
    if (status === 409) await fetchWishlist()
  } finally {
    enviando.value = false
  }
}

async function deshacer(itemId: number) {
  const tokenDeshacer = reservas.value[itemId]?.token
  if (!tokenDeshacer) return
  try {
    await $fetch(`/w/reservas/${tokenDeshacer}/deshacer`, {
      method: 'POST',
      baseURL: runtime.public.apiBase,
    })
    olvidar(itemId)
    await fetchWishlist()
    toast.add({ title: 'Reserva liberada', color: 'green' })
  } catch {
    olvidar(itemId)
    toast.add({
      title: 'Esa reserva ya no está activa',
      color: 'amber',
    })
    await fetchWishlist()
  }
}
</script>

<template>
  <div class="min-h-screen bg-neutral-50 dark:bg-neutral-950">
    <header ref="heroRef" class="px-4 pb-8 pt-10 text-center sm:pt-16">
      <!-- El logo con la guirnalda es la pieza principal. <picture> elige
           la variante clara u oscura sin JavaScript, así no parpadea al
           cargar. Si el archivo todavía no está, cae al ícono simple. -->
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
      <img
        v-else
        src="/icon.svg"
        alt=""
        class="mx-auto h-16 w-16"
        aria-hidden="true"
      >
      <h1
        class="mt-4 font-serif text-4xl italic text-pink-800 sm:text-5xl dark:text-pink-200"
      >
        {{ nombreApp }}
      </h1>
      <p class="mt-6 text-2xl tracking-[0.6em] text-pink-400" aria-hidden="true">
        ❀
      </p>
    </header>

    <main id="contenido" class="mx-auto max-w-5xl p-4 sm:p-6">
      <div v-if="cargando" class="py-20 text-center">
        <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
      </div>

      <UCard v-else-if="error">
        <p class="py-6 text-center text-sm text-gray-600 dark:text-gray-300">
          Este link no es válido o ya no está disponible.
        </p>
      </UCard>

      <template v-else>
        <h2
          v-if="items.length > 0"
          class="mb-1 text-center font-serif text-2xl text-pink-800 dark:text-pink-200"
        >
          Lista de deseos
        </h2>
        <p class="mb-4 text-sm text-gray-600 dark:text-gray-300">
          Si querés regalar algo de esta lista, tocá «Yo lo regalo» y escribí
          tu nombre. Se aparta esa unidad para que nadie la repita, y tu
          nombre queda en secreto hasta que reciban el regalo.
        </p>

        <div v-if="misReservas.length > 0" class="mb-6">
          <h2 class="mb-2 text-sm font-medium text-pink-800 dark:text-pink-200">
            Lo que vas a regalar
          </h2>
          <div class="flex flex-wrap gap-2">
            <UCard
              v-for="mia in misReservas"
              :key="mia.itemId"
              class="flex-1 sm:max-w-xs"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="min-w-0 truncate text-sm">🎁 {{ mia.nombre }}</span>
                <UButton
                  size="xs"
                  variant="ghost"
                  color="gray"
                  class="shrink-0"
                  @click="deshacer(mia.itemId)"
                >
                  Ya no puedo
                </UButton>
              </div>
            </UCard>
          </div>
        </div>

        <UCard v-if="items.length === 0">
          <p class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
            Por ahora no queda nada por regalar. ¡Gracias! 💕
          </p>
        </UCard>

        <section v-for="[categoria, deCategoria] in grupos" :key="categoria" class="mb-6">
          <h2
            v-if="categoria"
            class="mb-2 text-sm font-medium text-pink-800 dark:text-pink-200"
          >
            {{ categoria }}
          </h2>
          <h2
            v-else-if="grupos.length > 1"
            class="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400"
          >
            Otros
          </h2>

          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <UCard v-for="item in deCategoria" :key="item.id">
              <!-- lazy: la lista puede tener decenas de fotos y la mayoría
                   queda lejos de la primera pantalla. Quien abre el link en
                   el celular no tiene por qué bajarlas todas de entrada. La
                   altura fija (h-40) reserva el lugar, así que la página no
                   salta cuando llegan. -->
              <img
                v-if="item.fotos.length > 0"
                :src="item.fotos[0]!.url"
                alt=""
                loading="lazy"
                decoding="async"
                class="mb-3 h-40 w-full rounded-lg object-cover"
              >
              <FotoPlaceholder v-else alto="h-40" class="mb-3" />
              <p class="font-medium">{{ item.nombre }}</p>
              <p
                v-if="item.descripcion"
                class="mt-1 text-sm text-gray-500 dark:text-gray-400"
              >
                {{ item.descripcion }}
              </p>

              <div class="mt-2 flex flex-wrap items-center gap-2">
                <UBadge v-if="item.cantidad > 1" color="blue" variant="subtle" size="xs">
                  Quedan {{ item.disponibles }} de {{ item.cantidad }}
                </UBadge>
                <UBadge v-if="item.rango_precio" color="gray" variant="subtle" size="xs">
                  {{ RANGO_PRECIO_LABEL[item.rango_precio] }}
                </UBadge>
              </div>

              <div class="mt-3 flex items-center gap-2">
                <UButton size="sm" @click="itemReservando = item">
                  Yo lo regalo
                </UButton>
                <!-- La tienda es un dominio ajeno: noopener le niega el
                     acceso a window.opener y noreferrer evita mandarle de
                     dónde viene la visita, que acá es la URL con el token
                     de la lista. Los navegadores actuales ya hacen las dos
                     cosas por default, pero esto no depende del default. -->
                <ULink
                  v-if="item.amazon_link"
                  :to="item.amazon_link"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-xs text-pink-600 underline dark:text-pink-300"
                >
                  Ver en tienda
                </ULink>
              </div>
            </UCard>
          </div>
        </section>
      </template>
    </main>

    <Transition name="subir">
      <button
        v-if="mostrarSubir"
        type="button"
        class="fixed bottom-6 left-1/2 z-40 flex -translate-x-1/2 items-center gap-2 rounded-full border border-neutral-200 bg-neutral-50/90 py-2 pl-2 pr-4 shadow-lg backdrop-blur transition-transform hover:-translate-y-0.5 dark:border-neutral-800 dark:bg-neutral-900/90"
        aria-label="Volver al inicio de la página"
        @click="volverArriba"
      >
        <img src="/icon.svg" alt="" class="h-9 w-9" aria-hidden="true">
        <UIcon
          name="i-heroicons-arrow-up"
          class="flecha h-4 w-4 text-pink-700 dark:text-pink-300"
        />
      </button>
    </Transition>

    <UModal
      v-if="itemReservando"
      :model-value="true"
      @update:model-value="itemReservando = null"
    >
      <UCard>
        <template #header>
          <h3 class="text-lg font-medium">Vas a regalar</h3>
        </template>
        <form class="space-y-4" @submit.prevent="reservar">
          <p class="text-sm text-gray-600 dark:text-gray-300">
            <span class="font-medium">{{ itemReservando.nombre }}</span>
            <span v-if="itemReservando.cantidad > 1">
              — reservás una unidad de {{ itemReservando.cantidad }}
            </span>
          </p>
          <UFormGroup label="Tu nombre" required>
            <UInput
              v-model="nombreInvitado"
              required
              autofocus
              placeholder="¿Cómo te llamás?"
            />
          </UFormGroup>
          <UFormGroup label="Mensaje (opcional)">
            <UTextarea
              v-model="mensajeInvitado"
              :rows="2"
              maxlength="500"
              placeholder="Unas palabras para acompañar el regalo…"
            />
          </UFormGroup>
          <UAlert
            color="pink"
            variant="subtle"
            icon="i-heroicons-sparkles"
            title="Tu nombre y tu mensaje quedan en secreto"
            description="No los verán hasta que marquen el regalo como recibido."
          />
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" color="gray" @click="itemReservando = null">
              Cancelar
            </UButton>
            <UButton type="submit" :loading="enviando">
              Confirmar
            </UButton>
          </div>
        </form>
      </UCard>
    </UModal>
  </div>
</template>

<style scoped>
/* Entrada y salida del botón */
.subir-enter-active,
.subir-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.subir-enter-from,
.subir-leave-to {
  opacity: 0;
  transform: translate(-50%, 0.75rem);
}

/* La flecha late apenas, para invitar al click sin distraer */
@keyframes flotar {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}
.flecha {
  animation: flotar 2s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .subir-enter-active,
  .subir-leave-active,
  .flecha {
    transition: none;
    animation: none;
  }
}
</style>
