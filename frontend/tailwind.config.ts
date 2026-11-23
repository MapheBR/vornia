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
        "vornia-verde-suave": "var(--vornia-verde-suave)",
        "vornia-cinza-claro": "var(--vornia-cinza-claro)",
        "vornia-branco": "var(--vornia-branco)",
      },
    },
  },
  plugins: [],
};

export default config;
