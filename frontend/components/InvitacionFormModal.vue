<script setup lang="ts">
/** Editor de una invitación: sus datos y su lámina. */
import type { Invitacion } from '~/stores/invitaciones'

const props = defineProps<{ invitacion: Invitacion }>()
const emit = defineEmits<{ close: [] }>()

const invitaciones = useInvitacionesStore()
const toast = useToast()

const f = reactive({
  titulo: props.invitacion.titulo,
  lugar: props.invitacion.lugar ?? '',
  fecha: props.invitacion.fecha ?? '',
  hora: props.invitacion.hora ?? '',
  texto: props.invitacion.texto ?? '',
  aviso: props.invitacion.aviso ?? '',
  pideCantidad: props.invitacion.pide_cantidad,
})
const guardando = ref(false)
const subiendo = ref(false)

const imagen = computed(() => props.invitacion.imagen_url)

async function guardar() {
  guardando.value = true
  try {
    // Se mandan todos: vaciar un campo tiene que poder borrar ese
    // renglón de la invitación.
    await invitaciones.editar(props.invitacion.id, {
      titulo: f.titulo.trim(),
      lugar: f.lugar.trim(),
      fecha: f.fecha.trim(),
      hora: f.hora.trim(),
      texto: f.texto.trim(),
      aviso: f.aviso.trim(),
      pide_cantidad: f.pideCantidad,
    })
    toast.add({ title: 'Invitación actualizada', color: 'green' })
    emit('close')
  } catch {
    toast.add({ title: 'No se pudo guardar', color: 'red' })
  } finally {
    guardando.value = false
  }
}

async function onImagen(file: File) {
  subiendo.value = true
  try {
    await invitaciones.subirImagen(props.invitacion.id, file)
    toast.add({ title: 'Lámina actualizada', color: 'green' })
  } catch {
    toast.add({
      title: 'No se pudo subir la lámina',
      description: 'Solo jpeg/png/webp de hasta 5 MB.',
      color: 'red',
    })
  } finally {
    subiendo.value = false
  }
}

async function quitarImagen() {
  try {
    await invitaciones.quitarImagen(props.invitacion.id)
  } catch {
    toast.add({ title: 'No se pudo quitar', color: 'red' })
  }
}
</script>

<template>
  <UModal
    :model-value="true"
    :ui="{ height: 'max-h-[85vh]' }"
    @update:model-value="emit('close')"
  >
    <UCard
      :ui="{
        base: 'flex max-h-[85vh] flex-col',
        body: { base: 'min-h-0 flex-1 overflow-y-auto' },
      }"
    >
      <template #header>
        <h3 class="text-lg font-medium">Editar invitación</h3>
      </template>

      <form id="form-invitacion" class="space-y-3" @submit.prevent="guardar">
        <UFormGroup
          label="Título"
          required
          help="Solo para distinguirlas acá. No lo ve quien recibe el link."
        >
          <UInput v-model="f.titulo" required placeholder="Tanda de la familia" />
        </UFormGroup>

        <UFormGroup label="Texto de invitación">
          <UTextarea
            v-model="f.texto"
            :rows="2"
            placeholder="Acompañanos a celebrar la llegada de Nicole"
          />
        </UFormGroup>
        <UFormGroup label="Fecha">
          <UInput v-model="f.fecha" placeholder="Sábado 15 de noviembre" />
        </UFormGroup>
        <UFormGroup label="Hora">
          <UInput v-model="f.hora" placeholder="De 4 a 7 de la tarde" />
        </UFormGroup>
        <UFormGroup label="Lugar">
          <UInput v-model="f.lugar" placeholder="Salón El Jardín, Av. Central 450" />
        </UFormGroup>
        <UFormGroup
          label="Aviso sobre la confirmación"
          help="Va encima del formulario, no sobre la lámina."
        >
          <UTextarea
            v-model="f.aviso"
            :rows="2"
            placeholder="Confirmá tu asistencia antes del 7 de noviembre, en el siguiente formulario o con los papás de Nicole por WhatsApp"
          />
        </UFormGroup>

        <UCheckbox
          v-model="f.pideCantidad"
          label="Preguntar cuántos vienen"
          help="Para cuando se invita a familias. Es un campo de texto: «2 adultos y 1 bebé»."
        />

        <UFormGroup
          label="Lámina"
          help="Si no subís una, se usa la que viene con la app."
        >
          <div class="flex items-start gap-3">
            <img
              v-if="imagen"
              :src="imagen"
              alt=""
              class="h-24 w-16 shrink-0 rounded border border-neutral-200 object-cover dark:border-neutral-800"
            >
            <img
              v-else
              src="/invitacion-julia.webp"
              alt=""
              class="h-24 w-16 shrink-0 rounded border border-dashed border-neutral-300 object-cover opacity-60 dark:border-neutral-700"
            >
            <div class="space-y-1">
              <SelectorFoto
                size="xs"
                :cargando="subiendo"
                etiqueta="Subir lámina"
                @seleccion="onImagen"
              />
              <UButton
                v-if="imagen"
                variant="link"
                size="xs"
                class="px-0"
                @click="quitarImagen"
              >
                Usar la lámina por defecto
              </UButton>
            </div>
          </div>
        </UFormGroup>
      </form>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cancelar
          </UButton>
          <UButton type="submit" form="form-invitacion" :loading="guardando">
            Guardar
          </UButton>
        </div>
      </template>
    </UCard>
  </UModal>
</template>
