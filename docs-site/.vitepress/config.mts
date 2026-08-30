import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Patterngen Docs",
  description: "Documentation site for the setup and usage of Patterngen",
  // Served from https://at-low45.github.io/patterngen/ — assets need this base path.
  base: "/patterngen/",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/AT-LOW45/patterngen' }
    ]
  }
})
