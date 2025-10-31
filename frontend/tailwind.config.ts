import type { Config } from "tailwindcss";

export default {
    content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: "#667eea",
                    dark: "#764ba2",
                },
            },
            animation: {
                "fade-in": "fadeIn 0.3s ease",
                "slide-up": "slideUp 0.3s ease",
            },
            keyframes: {
                fadeIn: {
                    from: { opacity: "0" },
                    to: { opacity: "1" },
                },
                slideUp: {
                    from: { transform: "translateY(50px)", opacity: "0" },
                    to: { transform: "translateY(0)", opacity: "1" },
                },
            },
        },
    },
    plugins: [],
} satisfies Config;
