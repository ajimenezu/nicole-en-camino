<script setup lang="ts">
import type { Etapa, Item, ItemBusqueda } from '~/types/api'
import { ETAPAS, ETAPA_LABEL, RANGO_PRECIO_LABEL } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const auth = useAuthStore()
const items = useItemsStore()
const categorias = useCategoriasStore()
const regalos = useRegalosStore()
const router = useRouter()
const toast = useToast()

const modalForm = ref(false)
const itemEditando = ref<Item | null>(null)
const itemAdquirir = ref<Item | null>(null)
const itemReservas = ref<Item | null>(null)
const itemCaja = ref<Item | null>(null)
const itemEliminar = ref<Item | null>(null)
const filtro = ref<'TODOS' | 'NECESITADO' | 'RESERVADO' | 'ADQUIRIDO'>('TODOS')
const filtroEtapa = ref<Etapa | 'TODAS'>('TODAS')
/** Id de categoría como texto, o 'TODAS' / 'SIN'.
 *
 * Va como string a propósito: USelect monta un `<select>` nativo y el
 * DOM devuelve siempre texto, así que guardar el id numérico haría que
 * la comparación estricta fallara sin dar señal — el filtro se vería
 * bien y no devolvería ningún item. 'SIN' es para los que quedaron sin
 * categoría, que de otro modo no habría forma de encontrar.
 */
const filtroCategoria = ref<string>('TODAS')
/** Origen es un eje distinto del estado: algo puede estar adquirido y
 *  además ser prestado. Por eso va en su propio control y no como una
 *  opción más de la fila de estados, que es excluyente.
 *
 *  'PRESTADO_PENDIENTE' es el caso que de verdad importa revisar: lo que
 *  todavía hay que devolver. */
const filtroOrigen = ref<
  'TODOS' | 'PRESTADO' | 'PRESTADO_PENDIENTE' | 'REGALO' | 'NOSOTROS'
>('TODOS')
const modalRegistrar = ref(false)

const busqueda = ref('')
const resultados = ref<ItemBusqueda[] | null>(null)
const buscando = ref(false)

onMounted(async () => {
  auth.fetchMe()
  await Promise.all([
    items.fetchAll(),
    items.fetchPendientes(),
    categorias.fetchAll(),
    // Solo para el contador de "sin agradecer" del resumen: ese dato
    // vive en la otra pantalla y es justo el más fácil de olvidar.
    regalos.fetchAll(),
  ])
})

/** Qué se está buscando: texto libre o «From: nombre». */
const criterio = computed(() => interpretarBusqueda(busqueda.value))

watchDebounced(
  busqueda,
  async () => {
    if (!criterio.value) {
      resultados.value = null
      return
    }
    buscando.value = true
    try {
      resultados.value = await items.buscar(criterio.value)
    } finally {
      buscando.value = false
    }
  },
  { debounce: 300 },
)

function coincideCategoria(item: Item): boolean {
  if (filtroCategoria.value === 'TODAS') return true
  if (filtroCategoria.value === 'SIN') return !item.categoria
  return String(item.categoria?.id) === filtroCategoria.value
}

function coincideOrigen(item: Item): boolean {
  if (filtroOrigen.value === 'TODOS') return true
  if (filtroOrigen.value === 'PRESTADO_PENDIENTE') {
    return item.prestamos_pendientes > 0
  }
  return item.origen_adquisicion === filtroOrigen.value
}

const itemsFiltrados = computed(() =>
  items.items.filter(
    (i) =>
      (filtro.value === 'TODOS' || i.estado === filtro.value) &&
      (filtroEtapa.value === 'TODAS' || i.etapa === filtroEtapa.value) &&
      coincideCategoria(i) &&
      coincideOrigen(i),
  ),
)

const hayFiltrosActivos = computed(
  () =>
    filtro.value !== 'TODOS' ||
    filtroEtapa.value !== 'TODAS' ||
    filtroCategoria.value !== 'TODAS' ||
    filtroOrigen.value !== 'TODOS',
)

const opcionesFiltroCategoria = computed(() => [
  { value: 'TODAS', label: 'Todas las categorías' },
  ...categorias.categorias.map((c) => ({
    value: String(c.id),
    label: c.nombre,
  })),
  { value: 'SIN', label: 'Sin categoría' },
])

function limpiarFiltros() {
  filtro.value = 'TODOS'
  filtroEtapa.value = 'TODAS'
  filtroCategoria.value = 'TODAS'
  filtroOrigen.value = 'TODOS'
}

const badge = {
  NECESITADO: { color: 'gray' as const, label: 'Por comprar' },
  RESERVADO: { color: 'amber' as const, label: 'Reservado 🎁' },
  ADQUIRIDO: { color: 'green' as const, label: 'Lo tenemos' },
}

function editarItem(item: Item) {
  itemEditando.value = item
  modalForm.value = true
}

/** El resultado de búsqueda es una vista reducida del item; el editor
 *  necesita el completo, que ya vino en el listado del catálogo. */
function editarDesdeBusqueda(id: number) {
  const item = items.items.find((i) => i.id === id)
  if (!item) {
    toast.add({ title: 'No pude abrir ese item', color: 'red' })
    return
  }
  editarItem(item)
}

const subiendoFotoDe = ref<number | null>(null)
const fotoAmpliada = ref<{ url: string; alt: string } | null>(null)

/** Sube una foto sin pasar por el editor.
 *
 * `items.subirFoto` la agrega al item del store, así que la tarjeta
 * cambia sola de placeholder a foto.
 */
async function subirFotoDeTarjeta(item: Item, file: File) {
  subiendoFotoDe.value = item.id
  try {
    await items.subirFoto(item.id, file)
    toast.add({ title: 'Foto agregada', color: 'green' })
  } catch {
    toast.add({
      title: 'No se pudo subir la foto',
      description: 'Solo jpeg/png/webp de hasta 5 MB.',
      color: 'red',
    })
  } finally {
    subiendoFotoDe.value = null
  }
}

function acciones(item: Item) {
  // Editar sigue acá aunque ahora el título también abra el editor: la
  // redundancia no molesta en un menú plegado, y quien no descubra que
  // el título es clickeable igual encuentra por dónde.
  const editar = {
    label: 'Editar',
    icon: 'i-heroicons-pencil',
    click: () => editarItem(item),
  }
  const grupos = [[editar]]

  // "Ya llegó" no vive acá: es la acción principal y va como botón
  // visible en la tarjeta.
  if (item.estado !== 'ADQUIRIDO' && item.reservas_activas === 0) {
    grupos.push([
      {
        label: 'Marcar adquirido',
        icon: 'i-heroicons-check-circle',
        click: () => (itemAdquirir.value = item),
      },
    ])
  }

  if (item.estado === 'ADQUIRIDO') {
    grupos.push([
      {
        label: item.caja ? 'Cambiar caja' : 'Asignar caja',
        icon: 'i-heroicons-archive-box',
        click: () => (itemCaja.value = item),
      },
    ])
  }

  // Con unidades reservadas no se puede eliminar: hay que resolverlas.
  if (item.reservas_activas === 0) {
    grupos.push([
      {
        label: 'Eliminar',
        icon: 'i-heroicons-trash',
        click: () => (itemEliminar.value = item),
      },
    ])
  }

  return grupos
}

const recibiendo = ref<number | null>(null)

/** Con una sola reserva no hay nada que elegir, así que se marca de una.
 *  Con varias se abre el panel para decidir cuál. */
async function yaLlego(item: Item) {
  if (item.reservas_activas > 1) {
    itemReservas.value = item
    return
  }
  recibiendo.value = item.id
  try {
    const revelada = await items.recibirLaUnica(item.id)
    toast.add({
      title: '¡Sorpresa revelada! 🎁',
      description: revelada.mensaje
        ? `De ${revelada.nombre}: «${revelada.mensaje}»`
        : `Este regalo era de: ${revelada.nombre}`,
      color: 'pink',
      timeout: 10000,
    })
  } catch {
    toast.add({ title: 'No se pudo marcar como recibido', color: 'red' })
  } finally {
    recibiendo.value = null
  }
}

async function confirmarEliminar() {
  if (!itemEliminar.value) return
  try {
    await items.eliminar(itemEliminar.value.id)
    toast.add({ title: 'Item eliminado', color: 'green' })
  } catch {
    toast.add({ title: 'No se pudo eliminar', color: 'red' })
  } finally {
    itemEliminar.value = null
  }
}

function salir() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <!-- Lo de "en camino" se movió al resumen, que es donde conviven
           los números; acá quedaba suelto al lado del título. -->
      <h2 class="text-xl font-medium text-pink-800 dark:text-pink-200">
        Catálogo
      </h2>
      <div class="flex items-center gap-2">
        <UButton icon="i-heroicons-gift" @click="modalRegistrar = true">
          Registrar regalo
        </UButton>
        <UButton
          variant="outline"
          icon="i-heroicons-plus"
          @click="itemEditando = null; modalForm = true"
        >
          Nuevo item
        </UButton>
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-heart"
          to="/admin/regalos"
          aria-label="Ver regalos recibidos"
        />
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-envelope-open"
          to="/admin/eventos"
          aria-label="Ver los eventos y quién viene"
        />
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-cog-6-tooth"
          to="/admin/ajustes"
          aria-label="Ajustes"
        />
        <UButton
          variant="ghost"
          color="gray"
          icon="i-heroicons-arrow-right-on-rectangle"
          aria-label="Salir"
          @click="salir"
        />
      </div>
    </div>

    <ResumenCatalogo
      :items="items.items"
      :en-camino="items.pendientes"
      :sin-agradecer="regalos.pendientesDeAgradecer"
    />

    <UInput
      v-model="busqueda"
      icon="i-heroicons-magnifying-glass"
      placeholder="Buscar algo, o «From: nombre» para ver qué regaló alguien"
      :loading="buscando"
      aria-label="Buscar items"
    />

    <UCard v-if="resultados !== null">
      <template #header>
        <h3 class="text-sm font-medium">
          {{ resultados.length }} resultado{{ resultados.length === 1 ? '' : 's' }}
          <span v-if="criterio?.persona" class="text-pink-700 dark:text-pink-300">
            de «{{ criterio.persona }}»
          </span>
        </h3>
      </template>
      <p v-if="resultados.length === 0" class="text-sm text-gray-500 dark:text-gray-400">
        {{
          criterio?.persona
            ? `No hay regalos registrados de «${criterio.persona}».`
            : `No encontramos nada con «${busqueda}».`
        }}
      </p>
      <ul v-else class="divide-y divide-neutral-200 dark:divide-neutral-800">
        <li
          v-for="r in resultados"
          :key="r.id"
          class="flex flex-wrap items-center justify-between gap-2 py-2"
        >
          <!-- Miniatura y nombre abren el editor: encontrar algo casi
               siempre es el paso previo a corregirlo, y desde acá había
               que salir a buscarlo de nuevo en la grilla. -->
          <button
            type="button"
            class="group flex min-w-0 items-center gap-2 text-left"
            :aria-label="`Editar ${r.nombre}`"
            @click="editarDesdeBusqueda(r.id)"
          >
            <img
              v-if="r.fotos.length > 0"
              :src="r.fotos[0]!.url"
              alt=""
              loading="lazy"
              decoding="async"
              class="h-10 w-10 shrink-0 rounded-md object-cover"
            >
            <!-- En un envoltorio y no con la clase suelta: FotoPlaceholder
                 ya trae w-full, que competiría con un w-10 encima. -->
            <div v-else class="h-10 w-10 shrink-0">
              <FotoPlaceholder alto="h-10" />
            </div>
            <span
              class="truncate text-sm font-medium group-hover:text-pink-700 dark:group-hover:text-pink-300"
            >
              {{ r.nombre }}
            </span>
          </button>
          <UBadge color="gray" variant="subtle">
            {{ ETAPA_LABEL[r.etapa] }}
          </UBadge>
          <UBadge
            v-if="r.personas.length > 0"
            color="pink"
            variant="subtle"
          >
            🎁 {{ r.personas.join(', ') }}
          </UBadge>
          <UBadge v-if="r.caja" color="gray" variant="subtle">
            📦 {{ r.caja.etiqueta }}
            <span v-if="r.caja.descripcion" class="ml-1 opacity-75">
              — {{ r.caja.descripcion }}
            </span>
          </UBadge>
          <span v-else class="text-xs text-gray-500 dark:text-gray-400">
            Sin caja asignada
          </span>
        </li>
      </ul>
    </UCard>

    <div class="space-y-2">
      <div class="flex flex-wrap gap-2">
        <UButton
          v-for="f in (['TODOS', 'NECESITADO', 'RESERVADO', 'ADQUIRIDO'] as const)"
          :key="f"
          size="xs"
          :variant="filtro === f ? 'solid' : 'outline'"
          @click="filtro = f"
        >
          {{ f === 'TODOS' ? 'Todos' : badge[f].label }}
        </UButton>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <USelect
          v-model="filtroCategoria"
          size="xs"
          class="w-48"
          aria-label="Filtrar por categoría"
          :options="opcionesFiltroCategoria"
        />
        <USelect
          v-model="filtroEtapa"
          size="xs"
          class="w-44"
          aria-label="Filtrar por etapa"
          :options="[
            { value: 'TODAS', label: 'Todas las etapas' },
            ...ETAPAS.map((e) => ({ value: e, label: ETAPA_LABEL[e] })),
          ]"
        />
        <USelect
          v-model="filtroOrigen"
          size="xs"
          class="w-52"
          aria-label="Filtrar por origen"
          :options="[
            { value: 'TODOS', label: 'Cualquier origen' },
            { value: 'PRESTADO', label: 'Prestado' },
            { value: 'PRESTADO_PENDIENTE', label: 'Prestado sin devolver' },
            { value: 'REGALO', label: 'Nos lo regalaron' },
            { value: 'NOSOTROS', label: 'Lo compramos' },
          ]"
        />
        <UButton
          v-if="hayFiltrosActivos"
          variant="link"
          size="xs"
          icon="i-heroicons-x-mark"
          @click="limpiarFiltros"
        >
          Limpiar
        </UButton>
        <span
          v-if="hayFiltrosActivos"
          class="ml-auto text-xs text-gray-500 dark:text-gray-400"
        >
          {{ itemsFiltrados.length }} de {{ items.items.length }}
        </span>
      </div>
    </div>

    <div v-if="items.cargando" class="py-10 text-center">
      <UIcon name="i-heroicons-heart" class="h-8 w-8 animate-pulse text-pink-400" />
    </div>

    <UCard v-else-if="itemsFiltrados.length === 0">
      <div class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
        <template v-if="hayFiltrosActivos">
          <p>Ningún item coincide con estos filtros.</p>
          <UButton variant="link" size="xs" class="mt-1" @click="limpiarFiltros">
            Ver todos
          </UButton>
        </template>
        <p v-else>No hay items aquí todavía. ¡Agregá el primero con "Nuevo item"!</p>
      </div>
    </UCard>

    <!-- Dos columnas ya en celular. A una sola, la tarjeta medía 358px de
         ancho y la foto quedaba fijada en 128px de alto: se veía apenas
         el 39% de una imagen cuadrada, o sea una tira muy apaisada. -->
    <div v-else class="grid grid-cols-2 gap-3 lg:grid-cols-3">
      <UCard
        v-for="item in itemsFiltrados"
        :key="item.id"
        :ui="{ body: { padding: 'p-3 sm:p-6' } }"
      >
        <div class="flex items-start justify-between gap-2">
          <!-- El título abre el editor: es la acción más frecuente y
               antes estaba a dos clicks, dentro del menú. Se usa un
               <button> y no la tarjeta entera porque acá adentro ya hay
               otros elementos clickeables. -->
          <button
            type="button"
            class="group min-w-0 text-left"
            :aria-label="`Editar ${item.nombre}`"
            @click="editarItem(item)"
          >
            <span class="flex min-w-0 items-center gap-1">
              <!-- Dos líneas y no una: a dos columnas la tarjeta mide
                   173px y con truncate el nombre quedaba en "Body man…" -->
              <span
                class="line-clamp-2 font-medium group-hover:text-pink-700 dark:group-hover:text-pink-300"
              >
                {{ item.nombre }}
              </span>
              <UIcon
                name="i-heroicons-pencil"
                class="h-3.5 w-3.5 shrink-0 text-pink-600 opacity-0 transition-opacity group-hover:opacity-100 dark:text-pink-300"
              />
            </span>
            <span
              v-if="item.descripcion"
              class="mt-0.5 line-clamp-2 text-sm text-gray-500 dark:text-gray-400"
            >
              {{ item.descripcion }}
            </span>
          </button>
          <UDropdown :items="acciones(item)">
            <UButton
              variant="ghost"
              color="gray"
              icon="i-heroicons-ellipsis-vertical"
              :aria-label="`Acciones para ${item.nombre}`"
            />
          </UDropdown>
        </div>

        <!-- La foto es tambien la zona para subirla: antes el placeholder
             era decoracion muerta y agregar una imagen obligaba a entrar
             al editor. Los botones quedan siempre visibles y no al pasar
             el mouse, porque en el celular no hay hover. -->
        <div class="relative mt-2">
          <button
            v-if="item.fotos.length > 0"
            type="button"
            class="block w-full"
            :aria-label="`Ver la foto de ${item.nombre} en grande`"
            @click="fotoAmpliada = { url: item.fotos[0]!.url, alt: item.nombre }"
          >
            <img
              :src="item.fotos[0]!.url"
              alt=""
              loading="lazy"
              decoding="async"
              class="h-40 w-full rounded-lg object-cover sm:h-32"
            >
          </button>
          <FotoPlaceholder v-else alto="h-40 sm:h-32" />
          <div class="absolute bottom-1.5 right-1.5">
            <SelectorFoto
              size="xs"
              compacto
              :cargando="subiendoFotoDe === item.id"
              :etiqueta="`Agregar foto a ${item.nombre}`"
              @seleccion="(file: File) => subirFotoDeTarjeta(item, file)"
            />
          </div>
        </div>

        <UButton
          v-if="item.reservas_activas > 0"
          class="mt-3 w-full justify-center"
          icon="i-heroicons-gift"
          :loading="recibiendo === item.id"
          @click="yaLlego(item)"
        >
          Ya llegó{{ item.reservas_activas > 1 ? ` (${item.reservas_activas})` : '' }}
        </UButton>

        <div class="mt-3 flex flex-wrap items-center gap-2">
          <UBadge :color="badge[item.estado].color" variant="subtle">
            {{ badge[item.estado].label }}
          </UBadge>
          <UBadge v-if="item.cantidad > 1" color="blue" variant="subtle">
            {{ item.cantidad_recibida }}/{{ item.cantidad }} recibidos
          </UBadge>
          <!-- Lo prestado se avisa solo mientras siga en casa: una vez
               devuelto deja de ser algo pendiente de hacer. -->
          <UBadge
            v-if="item.prestamos_pendientes > 0"
            color="blue"
            variant="subtle"
          >
            Falta devolver
          </UBadge>
          <UBadge v-if="item.rango_precio" color="gray" variant="subtle">
            {{ RANGO_PRECIO_LABEL[item.rango_precio] }}
          </UBadge>
          <UBadge v-if="item.categoria" color="gray" variant="subtle">
            {{ item.categoria.nombre }}
          </UBadge>
          <UBadge v-if="item.etapa !== 'CUALQUIERA'" color="gray" variant="subtle">
            {{ ETAPA_LABEL[item.etapa] }}
          </UBadge>
          <UBadge v-if="item.personas.length > 0" color="pink" variant="subtle">
            🎁 {{ item.personas.join(', ') }}
          </UBadge>
          <UBadge v-if="item.caja" color="gray" variant="subtle">
            📦 {{ item.caja.etiqueta }}
          </UBadge>
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

    <RegistrarRegaloModal
      v-if="modalRegistrar"
      @close="modalRegistrar = false"
      @done="items.fetchAll()"
    />
    <ItemFormModal v-if="modalForm" :item="itemEditando" @close="modalForm = false" />
    <FotoModal
      v-if="fotoAmpliada"
      :url="fotoAmpliada.url"
      :alt="fotoAmpliada.alt"
      @close="fotoAmpliada = null"
    />
    <AdquirirModal
      v-if="itemAdquirir"
      :item="itemAdquirir"
      @close="itemAdquirir = null"
    />
    <ReservasModal
      v-if="itemReservas"
      :item="itemReservas"
      @close="itemReservas = null"
    />
    <CajaModal v-if="itemCaja" :item="itemCaja" @close="itemCaja = null" />
    <ConfirmModal
      v-if="itemEliminar"
      titulo="Eliminar item"
      :descripcion="`Se eliminará «${itemEliminar.nombre}» y sus fotos. Esta acción no se puede deshacer.`"
      confirm-label="Eliminar"
      @close="itemEliminar = null"
      @confirm="confirmarEliminar"
    />
  </div>
</template>
