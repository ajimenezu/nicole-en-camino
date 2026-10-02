<script setup lang="ts">
import type { Invitacion } from '~/stores/invitaciones'

definePageMeta({ middleware: 'auth' })

const invitaciones = useInvitacionesStore()
const rsvps = useRsvpsStore()
const toast = useToast()

const nuevaTitulo = ref('')
const creando = ref(false)
const editando = ref<Invitacion | null>(null)
const aBorrarInv = ref<Invitacion | null>(null)
const aBorrarRsvp = ref<{ id: number; nombre: string } | null>(null)
const copiado = ref<number | null>(null)
/** Qué invitación está desplegada. Con varias, mostrarlas todas
 *  abiertas convierte la pantalla en una lista interminable. */
const abierta = ref<number | null>(null)

onMounted(async () => {
  await Promise.all([invitaciones.fetchAll(), rsvps.fetchAll()])
  abierta.value = invitaciones.invitaciones[0]?.id ?? null
})

function linkDe(inv: Invitacion) {
  return `${location.origin}/i/${inv.token}`
}

async function copiar(inv: Invitacion) {
  await navigator.clipboard.writeText(linkDe(inv))
  copiado.value = inv.id
  setTimeout(() => (copiado.value = null), 2000)
}

async function crear() {
  if (!nuevaTitulo.value.trim()) return
  creando.value = true
  try {
    const inv = await invitaciones.crear(nuevaTitulo.value.trim())
    nuevaTitulo.value = ''
    abierta.value = inv.id
    editando.value = inv
  } catch {
    toast.add({ title: 'No se pudo crear', color: 'red' })
  } finally {
    creando.value = false
  }
}

async function borrarInvitacion() {
  if (!aBorrarInv.value) return
  try {
    await invitaciones.eliminar(aBorrarInv.value.id)
    await rsvps.fetchAll()
    toast.add({ title: 'Invitación eliminada', color: 'green' })
  } catch {
    toast.add({ title: 'No se pudo eliminar', color: 'red' })
  } finally {
    aBorrarInv.value = null
  }
}

async function borrarRsvp() {
  if (!aBorrarRsvp.value) return
  try {
    await rsvps.eliminar(aBorrarRsvp.value.id)
    await invitaciones.fetchAll()
    toast.add({ title: 'Respuesta eliminada', color: 'green' })
  } catch {
    toast.add({ title: 'No se pudo eliminar', color: 'red' })
  } finally {
    aBorrarRsvp.value = null
  }
}

function respuestasDe(id: number) {
  return rsvps.respuestas.filter((r) => r.invitacion_id === id)
}

function cuando(iso: string) {
  return new Date(iso).toLocaleDateString('es', { day: 'numeric', month: 'long' })
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h2 class="text-xl font-medium text-pink-800 dark:text-pink-200">
        Eventos
      </h2>
      <UButton
        variant="ghost"
        color="gray"
        icon="i-heroicons-arrow-left"
        to="/admin"
      >
        Volver al catálogo
      </UButton>
    </div>

    <UCard>
      <form class="flex flex-wrap gap-2" @submit.prevent="crear">
        <UInput
          v-model="nuevaTitulo"
          class="min-w-0 flex-1"
          placeholder="Nombre del evento — ej. «Tanda de la familia»"
          aria-label="Título de la invitación nueva"
        />
        <UButton
          type="submit"
          icon="i-heroicons-plus"
          :loading="creando"
          :disabled="!nuevaTitulo.trim()"
        >
          Crear invitación
        </UButton>
      </form>
    </UCard>

    <div v-if="invitaciones.cargando" class="py-10 text-center">
      <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
    </div>

    <UCard v-else-if="invitaciones.invitaciones.length === 0">
      <p class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
        Todavía no hay eventos. Creá el primero con el campo de arriba.
      </p>
    </UCard>

    <UCard v-for="inv in invitaciones.invitaciones" v-else :key="inv.id">
      <template #header>
        <!-- Apilado en celular: título y acciones no entran en un renglón
             de 390px sin que el nombre choque con los botones. -->
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
          <button
            type="button"
            class="min-w-0 flex-1 text-left"
            @click="abierta = abierta === inv.id ? null : inv.id"
          >
            <span class="block truncate font-medium">{{ inv.titulo }}</span>
            <span class="text-xs text-neutral-500 dark:text-neutral-400">
              {{ inv.asisten }} {{ inv.asisten === 1 ? 'confirmado' : 'confirmados' }}
              <template v-if="inv.no_asisten > 0">
                · {{ inv.no_asisten }} no
              </template>
            </span>
          </button>
          <div class="flex shrink-0 items-center gap-2">
          <UButton
            :icon="copiado === inv.id ? 'i-heroicons-check' : 'i-heroicons-clipboard'"
            :color="copiado === inv.id ? 'green' : 'pink'"
            size="xs"
            @click="copiar(inv)"
          >
            {{ copiado === inv.id ? 'Copiado' : 'Copiar link' }}
          </UButton>
          <UButton
            variant="ghost"
            color="gray"
            icon="i-heroicons-pencil"
            size="xs"
            :aria-label="`Editar ${inv.titulo}`"
            @click="editando = inv"
          />
          <UButton
            variant="ghost"
            color="gray"
            icon="i-heroicons-trash"
            size="xs"
            :aria-label="`Eliminar ${inv.titulo}`"
            @click="aBorrarInv = inv"
          />
          </div>
        </div>
      </template>

      <template v-if="abierta === inv.id">
        <p
          v-if="respuestasDe(inv.id).length === 0"
          class="py-4 text-center text-sm text-gray-500 dark:text-gray-400"
        >
          Todavía nadie respondió esta invitación.
        </p>
        <ul v-else class="divide-y divide-neutral-200 dark:divide-neutral-800">
          <li v-for="r in respuestasDe(inv.id)" :key="r.id" class="py-2">
            <div class="flex items-center gap-2">
              <UIcon
                :name="r.asistira ? 'i-heroicons-check-circle' : 'i-heroicons-x-circle'"
                :class="r.asistira ? 'text-green-600' : 'text-neutral-400'"
                class="h-4 w-4 shrink-0"
              />
              <span class="min-w-0 truncate text-sm font-medium">{{ r.nombre }}</span>
              <span class="ml-auto shrink-0 text-xs text-gray-500 dark:text-gray-400">
                {{ cuando(r.created_at) }}
              </span>
              <UButton
                variant="ghost"
                color="gray"
                icon="i-heroicons-trash"
                size="xs"
                :aria-label="`Eliminar la respuesta de ${r.nombre}`"
                @click="aBorrarRsvp = { id: r.id, nombre: r.nombre }"
              />
            </div>
            <p
              v-if="r.cantidad"
              class="mt-1 text-xs text-neutral-500 dark:text-neutral-400"
            >
              Vienen: {{ r.cantidad }}
            </p>
            <p
              v-if="r.comentario"
              class="mt-1 rounded-lg bg-pink-50 p-2 text-sm italic text-neutral-700 dark:bg-neutral-900 dark:text-neutral-300"
            >
              «{{ r.comentario }}»
            </p>
          </li>
        </ul>
      </template>
    </UCard>

    <InvitacionFormModal
      v-if="editando"
      :invitacion="editando"
      @close="editando = null"
    />

    <ConfirmModal
      v-if="aBorrarInv"
      titulo="Eliminar evento"
      :descripcion="`Se borra «${aBorrarInv.titulo}» y sus ${respuestasDe(aBorrarInv.id).length} respuestas. El link deja de funcionar.`"
      confirm-label="Eliminar"
      @close="aBorrarInv = null"
      @confirm="borrarInvitacion"
    />

    <ConfirmModal
      v-if="aBorrarRsvp"
      titulo="Eliminar respuesta"
      :descripcion="`Se borra la respuesta de «${aBorrarRsvp.nombre}». Si vuelve a confirmar, entra de nuevo.`"
      confirm-label="Eliminar"
      @close="aBorrarRsvp = null"
      @confirm="borrarRsvp"
    />
  </div>
</template>
