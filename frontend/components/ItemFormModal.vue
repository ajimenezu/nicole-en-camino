<script setup lang="ts">
import type { Etapa, Item, RangoPrecio } from '~/types/api'
import { ETAPAS, ETAPA_LABEL } from '~/types/api'

const props = defineProps<{ item?: Item | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const items = useItemsStore()
const categorias = useCategoriasStore()
const toast = useToast()

// -1 y no 0: USelectMenu resuelve la etiqueta con `if (!modelValue)`
// (SelectMenu.vue:402), así que con 0 el campo se veía vacío en lugar
// de "Sin categoría".
const SIN_CATEGORIA = -1

const nombre = ref(props.item?.nombre ?? '')
const descripcion = ref(props.item?.descripcion ?? '')
const amazonLink = ref(props.item?.amazon_link ?? '')
const cantidad = ref(props.item?.cantidad ?? 1)
const rangoPrecio = ref<RangoPrecio | ''>(props.item?.rango_precio ?? '')
const categoriaId = ref<number>(props.item?.categoria?.id ?? SIN_CATEGORIA)
const etapa = ref<Etapa>(props.item?.etapa ?? 'CUALQUIERA')
const nuevaCategoria = ref('')
const creandoCategoria = ref(false)
const guardando = ref(false)
const subiendoFoto = ref(false)

/** Fotos elegidas antes de que el item exista, con su preview local. */
const fotosPendientes = ref<{ file: File; url: string }[]>([])

const trayendoDelLink = ref(false)
/** Al crear no hay id contra el cual importar: se deja marcado y se
 *  resuelve junto con las fotos pendientes. */
const linkPendiente = ref(false)

const esEdicion = computed(() => !!props.item)

onMounted(() => categorias.fetchAll())

onUnmounted(() => {
  fotosPendientes.value.forEach((p) => URL.revokeObjectURL(p.url))
})

function quitarPendiente(indice: number) {
  const [quitada] = fotosPendientes.value.splice(indice, 1)
  if (quitada) URL.revokeObjectURL(quitada.url)
}

/** Sube lo que quedó esperando, ya con el id del item recién creado.
 *
 * No propaga el error: si el item se creó, cerrar el modal con un aviso
 * es mejor que hacer parecer que falló todo y tentar a crearlo de nuevo.
 */
/** Trae la imagen del producto desde el link de la tienda.
 *
 * El aviso de error usa el detail del backend porque ahí está lo útil:
 * distingue "esa página no declara imagen" de "la tienda respondió 503",
 * y sin eso el usuario no sabe si reintentar o copiar la imagen a mano.
 */
async function traerDelLink(itemId: number) {
  trayendoDelLink.value = true
  try {
    await items.fotoDesdeUrl(itemId, amazonLink.value.trim())
    toast.add({ title: 'Imagen importada del link', color: 'green' })
    return true
  } catch (e: unknown) {
    const detalle = (e as { data?: { detail?: string } }).data?.detail
    toast.add({
      title: 'No pude traer la imagen',
      description: detalle ?? 'Probá copiando la dirección de la imagen.',
      color: 'red',
    })
    return false
  } finally {
    trayendoDelLink.value = false
  }
}

async function onTraerDelLink() {
  if (!props.item) {
    linkPendiente.value = true
    return
  }
  await traerDelLink(props.item.id)
}

async function subirPendientes(itemId: number) {
  if (linkPendiente.value) await traerDelLink(itemId)

  const fallidas: string[] = []
  for (const pendiente of fotosPendientes.value) {
    try {
      await items.subirFoto(itemId, pendiente.file)
    } catch {
      fallidas.push(pendiente.file.name)
    }
  }
  if (fallidas.length > 0) {
    toast.add({
      title: 'El item se creó, pero faltaron fotos',
      description: `No se pudieron subir ${fallidas.length} de ${fotosPendientes.value.length}. Podés agregarlas editando el item.`,
      color: 'amber',
    })
  }
}

const opcionesCategoria = computed(() => [
  { value: SIN_CATEGORIA, label: 'Sin categoría' },
  ...categorias.categorias.map((c) => ({ value: c.id, label: c.nombre })),
])

async function guardar() {
  guardando.value = true
  try {
    let catId: number | null =
      categoriaId.value === SIN_CATEGORIA ? null : categoriaId.value
    if (creandoCategoria.value && nuevaCategoria.value.trim()) {
      const creada = await categorias.crear(nuevaCategoria.value.trim())
      catId = creada.id
    }
    const body = {
      nombre: nombre.value.trim(),
      descripcion: descripcion.value.trim() || null,
      amazon_link: amazonLink.value.trim() || null,
      cantidad: cantidad.value,
      // prioridad no se manda a proposito: sigue existiendo en el backend
      // (ordena la wishlist publica) pero ya no se edita desde acá. Al
      // omitirla, ItemUpdate la deja como está en vez de pisarla.
      rango_precio: rangoPrecio.value || null,
      categoria_id: catId,
      etapa: etapa.value,
    }
    if (props.item) {
      await items.editar(props.item.id, body)
    } else {
      const creado = await items.crear(body)
      await subirPendientes(creado.id)
    }
    emit('saved')
    emit('close')
  } catch (e: unknown) {
    const status = (e as { statusCode?: number }).statusCode
    toast.add({
      title: 'No se pudo guardar',
      description:
        status === 409
          ? 'No podés bajar la cantidad por debajo de lo ya reservado o recibido.'
          : 'Revisá los datos (el link debe ser una URL válida).',
      color: 'red',
    })
  } finally {
    guardando.value = false
  }
}

async function onFotoSeleccionada(file: File) {
  // Al crear todavía no hay id contra el cual firmar la subida (la key
  // en el storage es items/{id}/… y el backend valida esa pertenencia). Se
  // retiene el archivo y se sube apenas el item exista.
  if (!props.item) {
    fotosPendientes.value.push({ file, url: URL.createObjectURL(file) })
    return
  }
  subiendoFoto.value = true
  try {
    await items.subirFoto(props.item.id, file)
    toast.add({ title: 'Foto subida', color: 'green' })
  } catch {
    toast.add({
      title: 'No se pudo subir la foto',
      description:
        'Solo imágenes jpeg/png/webp de hasta 5 MB (requiere el storage de fotos configurado).',
      color: 'red',
    })
  } finally {
    subiendoFoto.value = false
  }
}

async function quitarFoto(fotoId: number) {
  if (!props.item) return
  try {
    await items.eliminarFoto(props.item.id, fotoId)
  } catch {
    toast.add({ title: 'No se pudo eliminar la foto', color: 'red' })
  }
}
</script>

<template>
  <UModal :model-value="true" @update:model-value="emit('close')">
    <UCard>
      <template #header>
        <h3 class="text-lg font-medium">
          {{ esEdicion ? 'Editar item' : 'Nuevo item' }}
        </h3>
      </template>

      <form class="space-y-4" @submit.prevent="guardar">
        <UFormGroup label="Nombre" required>
          <UInput v-model="nombre" required placeholder="Cuna, pañalera, monitor…" />
        </UFormGroup>

        <UFormGroup label="Descripción">
          <UTextarea v-model="descripcion" :rows="2" placeholder="Color, talla, referencia…" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="¿Cuántos necesitan?">
            <UInput v-model.number="cantidad" type="number" min="1" max="99" />
          </UFormGroup>

          <UFormGroup label="Rango de precio">
            <USelect
              v-model="rangoPrecio"
              :options="[
                { value: '', label: 'Sin indicar' },
                { value: 'BAJO', label: '$ — económico' },
                { value: 'MEDIO', label: '$$ — medio' },
                { value: 'ALTO', label: '$$$ — caro' },
              ]"
            />
          </UFormGroup>
        </div>

        <UFormGroup label="¿Para qué etapa es?">
          <USelect
            v-model="etapa"
            :options="ETAPAS.map((e) => ({ value: e, label: ETAPA_LABEL[e] }))"
          />
        </UFormGroup>

        <UFormGroup label="Categoría">
          <template v-if="!creandoCategoria">
            <USelectMenu
              v-model="categoriaId"
              :options="opcionesCategoria"
              value-attribute="value"
              option-attribute="label"
            />
            <UButton
              variant="link"
              size="xs"
              icon="i-heroicons-plus"
              class="mt-1"
              @click="creandoCategoria = true"
            >
              Crear categoría nueva
            </UButton>
          </template>
          <template v-else>
            <UInput v-model="nuevaCategoria" placeholder="Ropa, higiene, paseo…" />
            <UButton variant="link" size="xs" class="mt-1" @click="creandoCategoria = false">
              Usar una existente
            </UButton>
          </template>
        </UFormGroup>

        <UFormGroup label="Link de Amazon (o tienda)">
          <UInput v-model="amazonLink" type="url" placeholder="https://amazon.com/…" />
          <div v-if="amazonLink.trim()" class="mt-1 flex items-center gap-2">
            <UButton
              variant="link"
              size="xs"
              icon="i-heroicons-arrow-down-tray"
              :loading="trayendoDelLink"
              :disabled="linkPendiente"
              @click="onTraerDelLink"
            >
              Usar la imagen del link
            </UButton>
            <span
              v-if="linkPendiente"
              class="text-xs text-gray-500 dark:text-gray-400"
            >
              Se trae cuando guardes.
            </span>
          </div>
        </UFormGroup>

        <div class="space-y-2">
          <p class="text-sm font-medium">Fotos de referencia</p>
          <div class="flex flex-wrap items-center gap-2">
            <div
              v-for="foto in props.item?.fotos"
              :key="foto.id"
              class="group relative h-16 w-16 overflow-hidden rounded-lg border border-neutral-200 dark:border-neutral-800"
            >
              <img :src="foto.url" alt="" class="h-full w-full object-cover">
              <button
                type="button"
                class="absolute inset-0 hidden items-center justify-center bg-black/50 text-white group-hover:flex"
                :aria-label="`Eliminar foto ${foto.id}`"
                @click="quitarFoto(foto.id)"
              >
                <UIcon name="i-heroicons-trash" class="h-5 w-5" />
              </button>
            </div>

            <div
              v-for="(pendiente, i) in fotosPendientes"
              :key="pendiente.url"
              class="group relative h-16 w-16 overflow-hidden rounded-lg border border-dashed border-pink-300 dark:border-pink-800"
            >
              <img :src="pendiente.url" alt="" class="h-full w-full object-cover">
              <button
                type="button"
                class="absolute inset-0 hidden items-center justify-center bg-black/50 text-white group-hover:flex"
                :aria-label="`Quitar foto ${pendiente.file.name}`"
                @click="quitarPendiente(i)"
              >
                <UIcon name="i-heroicons-x-mark" class="h-5 w-5" />
              </button>
            </div>

            <SelectorFoto
              :cargando="subiendoFoto"
              etiqueta="Agregar foto"
              @seleccion="onFotoSeleccionada"
            />
          </div>
          <p
            v-if="!esEdicion && fotosPendientes.length > 0"
            class="text-xs text-gray-500 dark:text-gray-400"
          >
            Se suben cuando guardes el item.
          </p>
        </div>

        <div class="flex justify-end gap-2">
          <UButton variant="ghost" color="gray" @click="emit('close')">
            Cancelar
          </UButton>
          <UButton type="submit" :loading="guardando">
            {{ esEdicion ? 'Guardar' : 'Crear' }}
          </UButton>
        </div>
      </form>
    </UCard>
  </UModal>
</template>
