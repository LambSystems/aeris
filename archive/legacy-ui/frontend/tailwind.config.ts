import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        aeris: {
          background: "#101614",
          panel: "#eef6ee12",
          context: "#d5f56d",
          priority: "#f1b84a",
          scan: "#5ec6ef",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;

