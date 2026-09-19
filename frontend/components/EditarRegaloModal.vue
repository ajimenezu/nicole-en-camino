<script setup lang="ts">
/** Corrige un regalo ya registrado.
 *
 * Existe porque anotar un regalo es justo el momento en el que se
 * confunde un nombre: pasa en medio del festejo, con la caja en la mano.
 * Hasta ahora la única salida era borrar y volver a cargar, lo que se
 * llevaba puestas también las fotos de Nicole usando ese regalo.
 *
 * El objeto no se cambia acá: mover un regalo de un item a otro
 * recalcula las cantidades de los dos y es una operación distinta. Para
 * eso sigue estando borrar y registrar de nuevo.
 */
import type { Regalo } from '~/types/api'

const props = defineProps<{ regalo: Regalo }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const regalos = useRegalosStore()
const toast = useToast()

const persona = ref(props.regalo.persona)
const cantidad = ref(props.regalo.cantidad)
const fecha = ref(props.regalo.fecha)
const nota = ref(props.regalo.nota ?? '')
const guardando = ref(false)

const esRegalo = computed(() => props.regalo.origen === 'REGALO')

onMounted(() => regalos.fetchPersonas())

const sugerencias = computed(() => {
  const q = persona.value.trim().toLowerCase()
  if (!q) return regalos.personas.slice(0, 6)
  return regalos.personas
    .filter((p) => p.toLowerCase().includes(q) && p.toLowerCase() !== q)
    .slice(0, 6)
})

// El backend rechaza un regalo sin persona, así que se corta acá antes
// de mandarlo y se muestra el motivo en el propio campo.
const puedeGuardar = computed(
  () => !esRegalo.value || !!persona.value.trim(),
)

async function guardar() {
  if (!puedeGuardar.value) return
  guardando.value = true
  try {
    await regalos.editar(props.regalo.id, {
      persona: persona.value.trim(),
      cantidad: cantidad.value,
      fecha: fecha.value,
      nota: nota.value.trim() || null,
    })
    toast.add({ title: 'Regalo actualizado', color: 'green' })
    emit('saved')
    emit('close')
  } catch {
    toast.add({ title: 'No se pudo guardar el cambio', color: 'red' })
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <UModal :model-value="true" @update:model-value="emit('close')">
    <UCard>
      <template #header>
        <h3 class="text-lg font-medium">Corregir regalo</h3>
        <p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
          {{ props.regalo.item.nombre }}
        </p>
      </template>

      <form class="space-y-4" @submit.prevent="guardar">
        <UFormGroup
          v-if="esRegalo"
          label="¿Quién lo regaló?"
          required
          :error="!puedeGuardar && 'Un regalo necesita el nombre de quien lo dio'"
        >
          <UInput v-model="persona" placeholder="Nombre de la persona" />
          <div v-if="sugerencias.length > 0" class="mt-2 flex flex-wrap gap-1">
            <UButton
              v-for="s in sugerencias"
              :key="s"
              size="xs"
              variant="soft"
              color="pink"
              @click="persona = s"
            >
              {{ s }}
            </UButton>
          </div>
        </UFormGroup>
        <p v-else class="text-sm text-gray-500 dark:text-gray-400">
          Está anotado como comprado por ustedes.
        </p>

        <!-- Apilados en celular: ver la nota en RegistrarRegaloModal
             sobre el ancho mínimo del input de fecha en iOS. -->
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <UFormGroup label="¿Cuántos?">
            <UInput v-model.number="cantidad" type="number" min="1" max="99" />
          </UFormGroup>
          <UFormGroup label="¿Cuándo?">
            <UInput v-model="fecha" type="date" />
          </UFormGroup>
        </div>

        <UFormGroup label="Nota (opcional)">
          <UTextarea v-model="nota" :rows="2" placeholder="Algo para recordar…" />
        </UFormGroup>

        <div class="flex justify-end gap-2">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cancelar
          </UButton>
          <UButton type="submit" :loading="guardando" :disabled="!puedeGuardar">
            Guardar
          </UButton>
        </div>
      </form>
    </UCard>
  </UModal>
</template>
