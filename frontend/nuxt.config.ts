// El módulo virtual de vite-plugin-pwa no resuelve dentro del entorno de
// Vitest, así que se excluye al correr los tests.
const enTests = !!process.env.VITEST

// El preview de los links necesita URLs absolutas: las relativas no las
// resuelve el robot de WhatsApp.
const SEO = {
  sitio: process.env.NUXT_PUBLIC_SITE_URL || 'https://nicole-en-camino.vercel.app',
  titulo: 'Nicole en Camino',
  descripcion: 'Estamos esperando a Nicole. Acá está lo que nos hace falta.',
}

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: [
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/eslint',
    '@nuxtjs/google-fonts',
    ...(enTests ? [] : ['@vite-pwa/nuxt']),
  ],

  css: ['~/assets/css/main.css'],

  googleFonts: {
    families: { 'Libre Caslon Text': [400, 700] },
    display: 'swap',
    download: true,
  },

  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'Nicole en Camino',
      short_name: 'Nicole',
      description: 'Catálogo y wishlist para la llegada de Nicole',
      theme_color: '#8c4c4d',
      background_color: '#fdf9f0',
      display: 'standalone',
      start_url: '/',
      lang: 'es',
      icons: [
        { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
      ],
    },
    workbox: {
      navigateFallback: null,
      globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
    },
    devOptions: { enabled: false },
  },

  components: {
    dirs: [{ path: '~/components', pathPrefix: false }],
  },

  app: {
    head: {
      htmlAttrs: { lang: 'es' },
      // Los links se comparten por WhatsApp, así que el preview importa
      // tanto como la página. Van fijos y no derivados de lo que se
      // carga en el cliente: el robot que arma el preview no ejecuta JS,
      // solo lee el HTML que sale del servidor.
      meta: [
        { name: 'description', content: SEO.descripcion },
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: SEO.titulo },
        { property: 'og:title', content: SEO.titulo },
        { property: 'og:description', content: SEO.descripcion },
        { property: 'og:image', content: `${SEO.sitio}/og-nicole.jpg` },
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
        { property: 'og:image:alt', content: 'El monograma de Nicole entre flores' },
        { property: 'og:locale', content: 'es_ES' },
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:title', content: SEO.titulo },
        { name: 'twitter:description', content: SEO.descripcion },
        { name: 'twitter:image', content: `${SEO.sitio}/og-nicole.jpg` },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/icon.svg' },
        { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' },
      ],
    },
  },

  // Cabeceras defensivas en todas las rutas.
  //
  // No hay CSP acá a propósito: Nuxt inyecta el payload de hidratación
  // como script inline, así que una CSP sin nonces dejaría la app en
  // blanco. Agregarla requiere configurarlos y probarlo, no una línea.
  //
  // Referrer-Policy importa más que de costumbre en este proyecto: el
  // token de la wishlist va en la ruta (/w/<token>) y desde ahí se sale a
  // la tienda. El default de los navegadores actuales ya manda solo el
  // origen, pero acá queda explícito y no a merced del default.
  routeRules: {
    '/**': {
      headers: {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), interest-cohort=()',
      },
    },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      siteUrl: SEO.sitio,
    },
  },

  typescript: {
    strict: true,
  },
})
