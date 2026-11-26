import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "vornia-azul-profundo": "var(--vornia-azul-profundo)",
        "vornia-azul-claro": "var(--vornia-azul-claro)",
        "vornia-verde-suave": "var(--vornia-verde-suave)",
        "vornia-verde-escuro": "var(--vornia-verde-escuro)",
        "vornia-cinza-claro": "var(--vornia-cinza-claro)",
        "vornia-branco": "var(--vornia-branco)",
        "vornia-borda": "var(--vornia-borda)",
        "vornia-sombra": "var(--vornia-sombra)",
      },
    },
  },
  plugins: [],
};

export default config;
