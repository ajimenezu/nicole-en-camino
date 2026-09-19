<script setup lang="ts">
import type { Regalo } from '~/types/api'
import { ETAPA_LABEL } from '~/types/api'

// withDefaults es necesario: Vue castea los props booleanos ausentes a
// false, así que sin esto el nombre nunca se mostraría.
const props = withDefaults(
  defineProps<{ regalo: Regalo; mostrarPersona?: boolean }>(),
  { mostrarPersona: true },
)
const emit = defineEmits<{ cambio: [] }>()

const regalos = useRegalosStore()
const toast = useToast()

const subiendo = ref(false)
const trabajando = ref(false)
const confirmarBorrado = ref(false)
const editando = ref(false)

function legible(fecha: string) {
  return new Date(`${fecha}T00:00:00`).toLocaleDateString('es', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

const fechaLegible = computed(() => legible(props.regalo.fecha))

const esPrestamo = computed(() => props.regalo.origen === 'PRESTADO')
const devuelto = computed(() => props.regalo.devuelto_en !== null)

async function alternarAgradecido() {
  trabajando.value = true
  try {
    await regalos.marcarAgradecido(props.regalo.id, !props.regalo.agradecido)
    emit('cambio')
  } catch {
    toast.add({ title: 'No se pudo actualizar', color: 'red' })
  } finally {
    trabajando.value = false
  }
}

async function alternarDevuelto() {
  trabajando.value = true
  try {
    await regalos.marcarDevuelto(props.regalo.id, !devuelto.value)
    emit('cambio')
  } catch {
    toast.add({ title: 'No se pudo actualizar', color: 'red' })
  } finally {
    trabajando.value = false
  }
}

async function onFoto(file: File) {
  subiendo.value = true
  try {
    await regalos.subirFoto(props.regalo.id, file)
    toast.add({ title: 'Foto guardada', color: 'green' })
    emit('cambio')
  } catch {
    toast.add({
      title: 'No se pudo subir la foto',
      description: 'Solo jpeg/png/webp de hasta 5 MB (requiere R2 configurado).',
      color: 'red',
    })
  } finally {
    subiendo.value = false
  }
}

async function quitarFoto(fotoId: number) {
  try {
    await regalos.eliminarFoto(props.regalo.id, fotoId)
    emit('cambio')
  } catch {
    toast.add({ title: 'No se pudo eliminar la foto', color: 'red' })
  }
}

async function borrar() {
  try {
    await regalos.eliminar(props.regalo.id)
    toast.add({ title: 'Regalo eliminado', color: 'green' })
    emit('cambio')
  } catch {
    toast.add({ title: 'No se pudo eliminar', color: 'red' })
  } finally {
    confirmarBorrado.value = false
  }
}
</script>

<template>
  <UCard>
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0">
        <p class="truncate font-medium">
          {{ props.regalo.item.nombre }}
          <span v-if="props.regalo.cantidad > 1" class="text-sm text-gray-500">
            ×{{ props.regalo.cantidad }}
          </span>
        </p>
        <p
          v-if="props.mostrarPersona !== false && props.regalo.persona"
          class="text-sm text-pink-700 dark:text-pink-300"
        >
          {{ props.regalo.origen === 'PRESTADO' ? 'prestado por' : 'de' }}
          {{ props.regalo.persona }}
        </p>
        <p v-else-if="!props.regalo.persona" class="text-sm text-gray-500">
          Lo compramos nosotros
        </p>
        <p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
          {{ fechaLegible }}
        </p>
      </div>
      <div class="flex shrink-0 items-center">
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-pencil"
          size="xs"
          :aria-label="`Corregir regalo ${props.regalo.item.nombre}`"
          @click="editando = true"
        />
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-trash"
          size="xs"
          :aria-label="`Eliminar regalo ${props.regalo.item.nombre}`"
          @click="confirmarBorrado = true"
        />
      </div>
    </div>

    <p
      v-if="props.regalo.nota"
      class="mt-2 rounded-lg bg-neutral-100 p-2 text-sm italic text-gray-600 dark:bg-neutral-900 dark:text-gray-300"
    >
      «{{ props.regalo.nota }}»
    </p>

    <div class="mt-3 flex flex-wrap items-center gap-2">
      <UBadge color="gray" variant="subtle" size="xs">
        {{ ETAPA_LABEL[props.regalo.item.etapa] }}
      </UBadge>
      <UBadge
        v-if="props.regalo.persona"
        :color="props.regalo.agradecido ? 'green' : 'amber'"
        variant="subtle"
        size="xs"
      >
        {{ props.regalo.agradecido ? 'Agradecido' : 'Falta agradecer' }}
      </UBadge>
      <UBadge
        v-if="esPrestamo"
        :color="devuelto ? 'gray' : 'blue'"
        variant="subtle"
        size="xs"
      >
        {{
          devuelto
            ? `Devuelto el ${legible(props.regalo.devuelto_en!)}`
            : 'Sin devolver'
        }}
      </UBadge>
    </div>

    <!-- Fotos de Nicole usando el regalo, para mandarle a quien lo dio -->
    <div class="mt-3 flex flex-wrap items-center gap-2">
      <a
        v-for="foto in props.regalo.fotos"
        :key="foto.id"
        :href="foto.url"
        target="_blank"
        rel="noopener noreferrer"
        class="group relative h-16 w-16 overflow-hidden rounded-lg border border-neutral-200 dark:border-neutral-800"
      >
        <img
          :src="foto.url"
          alt=""
          loading="lazy"
          decoding="async"
          class="h-full w-full object-cover"
        >
        <button
          type="button"
          class="absolute inset-0 hidden items-center justify-center bg-black/50 text-white group-hover:flex"
          :aria-label="`Eliminar foto ${foto.id}`"
          @click.prevent="quitarFoto(foto.id)"
        >
          <UIcon name="i-heroicons-trash" class="h-4 w-4" />
        </button>
      </a>
      <SelectorFoto
        :cargando="subiendo"
        etiqueta="Foto de Nicole"
        size="xs"
        @seleccion="onFoto"
      />
      <UButton
        v-if="props.regalo.persona"
        size="xs"
        :variant="props.regalo.agradecido ? 'ghost' : 'solid'"
        :color="props.regalo.agradecido ? 'gray' : 'pink'"
        :loading="trabajando"
        @click="alternarAgradecido"
      >
        {{ props.regalo.agradecido ? 'Desmarcar' : 'Ya agradecí' }}
      </UButton>
      <UButton
        v-if="esPrestamo"
        size="xs"
        :variant="devuelto ? 'ghost' : 'solid'"
        :color="devuelto ? 'gray' : 'blue'"
        :loading="trabajando"
        @click="alternarDevuelto"
      >
        {{ devuelto ? 'Aún no lo devolvimos' : 'Ya lo devolvimos' }}
      </UButton>
    </div>

    <EditarRegaloModal
      v-if="editando"
      :regalo="props.regalo"
      @close="editando = false"
      @saved="emit('cambio')"
    />

    <ConfirmModal
      v-if="confirmarBorrado"
      titulo="Eliminar regalo"
      :descripcion="`Se borra el registro de «${props.regalo.item.nombre}» y sus fotos. El objeto queda en el catálogo.`"
      confirm-label="Eliminar"
      @close="confirmarBorrado = false"
      @confirm="borrar"
    />
  </UCard>
</template>
