<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const config = useConfigStore()
const toast = useToast()

const shareToken = ref('')
const nombre = ref('')
const guardando = ref(false)
const copiado = ref(false)

// Fecha probable de parto, para la cuenta regresiva. Vacío = sin fecha,
// que es como se apaga la página pública.
const fechaParto = ref('')
const guardandoFecha = ref(false)
const copiadoCuenta = ref(false)

const shareUrl = computed(() =>
  shareToken.value ? `${location.origin}/w/${shareToken.value}` : '',
)
const cuentaUrl = computed(() =>
  import.meta.client ? `${location.origin}/cuenta-regresiva` : '',
)
const diasQueFaltan = computed(() =>
  fechaParto.value ? diasHasta(fechaParto.value) : null,
)

onMounted(async () => {
  // Los dos pedidos no dependen uno del otro, así que salen juntos.
  // En fila, el link esperaba a que terminara la config sin necesitarla.
  const api = useApi()
  const [, data] = await Promise.all([
    config.fetch(),
    api<{ share_token: string }>('/wishlist/link'),
  ])
  nombre.value = config.nombreApp
  fechaParto.value = config.fechaParto ?? ''
  shareToken.value = data.share_token
})

async function copiarLink() {
  await navigator.clipboard.writeText(shareUrl.value)
  copiado.value = true
  setTimeout(() => (copiado.value = false), 2000)
}

async function copiarCuenta() {
  await navigator.clipboard.writeText(cuentaUrl.value)
  copiadoCuenta.value = true
  setTimeout(() => (copiadoCuenta.value = false), 2000)
}

async function guardarFecha() {
  guardandoFecha.value = true
  try {
    // Vacío se manda como null: así se borra la fecha y la página
    // pública vuelve a decir que todavía no hay.
    await config.guardar({ fecha_parto: fechaParto.value || null })
    toast.add({
      title: fechaParto.value ? 'Fecha guardada' : 'Fecha borrada',
      color: 'green',
    })
  } catch {
    toast.add({ title: 'No se pudo guardar la fecha', color: 'red' })
  } finally {
    guardandoFecha.value = false
  }
}


async function guardarNombre() {
  guardando.value = true
  try {
    await config.guardar({ nombre_app: nombre.value.trim() })
    toast.add({ title: 'Nombre actualizado', color: 'green' })
  } catch {
    toast.add({ title: 'No se pudo actualizar el nombre', color: 'red' })
  } finally {
    guardando.value = false
  }
}

</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center gap-2">
      <UButton
        variant="ghost"
        color="gray"
        icon="i-heroicons-arrow-left"
        to="/admin"
        aria-label="Volver al catálogo"
      />
      <h2 class="text-xl font-medium text-pink-800 dark:text-pink-200">
        Ajustes
      </h2>
    </div>


    <UCard>
      <template #header>
        <h3 class="font-medium">Compartir la wishlist</h3>
      </template>
      <div class="space-y-3">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          Para quien pregunte qué hace falta. Verán solo los items por
          comprar y podrán reservar qué regalar — sin crear cuenta. Las
          invitaciones al baby shower tienen su propio link, en Invitaciones.
        </p>
        <div class="flex gap-2">
          <UInput :model-value="shareUrl" readonly class="flex-1" aria-label="Link de la wishlist" />
          <UButton
            :icon="copiado ? 'i-heroicons-check' : 'i-heroicons-clipboard'"
            :color="copiado ? 'green' : 'pink'"
            @click="copiarLink"
          >
            {{ copiado ? 'Copiado' : 'Copiar' }}
          </UButton>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Cualquiera con el link puede ver y reservar — compártelo solo con
          el círculo cercano.
        </p>
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="font-medium">Cuenta regresiva</h3>
      </template>
      <div class="space-y-3">
        <p class="text-sm text-gray-600 dark:text-gray-300">
          La fecha probable de parto. Con una fecha cargada, la página de
          la cuenta regresiva muestra cuánto falta; sin fecha, avisa que
          todavía no hay.
        </p>
        <form class="flex flex-wrap items-end gap-2" @submit.prevent="guardarFecha">
          <UFormGroup label="Fecha probable" class="flex-1">
            <UInput v-model="fechaParto" type="date" aria-label="Fecha probable de parto" />
          </UFormGroup>
          <UButton type="submit" :loading="guardandoFecha">Guardar</UButton>
        </form>
        <p
          v-if="diasQueFaltan !== null && diasQueFaltan >= 0"
          class="text-sm text-pink-800 dark:text-pink-200"
        >
          Faltan {{ diasQueFaltan }} {{ diasQueFaltan === 1 ? 'día' : 'días' }}.
        </p>
        <div class="flex gap-2">
          <UInput
            :model-value="cuentaUrl"
            readonly
            class="flex-1"
            aria-label="Link de la cuenta regresiva"
          />
          <UButton
            :icon="copiadoCuenta ? 'i-heroicons-check' : 'i-heroicons-clipboard'"
            :color="copiadoCuenta ? 'green' : 'pink'"
            @click="copiarCuenta"
          >
            {{ copiadoCuenta ? 'Copiado' : 'Copiar' }}
          </UButton>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Este link es público y no lleva token: cualquiera que lo reciba ve
          la cuenta regresiva.
        </p>
      </div>
    </UCard>

    <UCard>
      <template #header>
        <h3 class="font-medium">Nombre de la app</h3>
      </template>
      <form class="flex gap-2" @submit.prevent="guardarNombre">
        <UInput v-model="nombre" required class="flex-1" aria-label="Nombre de la app" />
        <UButton type="submit" :loading="guardando">Guardar</UButton>
      </form>
    </UCard>

  </div>
</template>
