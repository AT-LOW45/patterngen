// tailwind styles
import "@/styles/tailwind.css";
import "primeicons/primeicons.css";

// other imports
import { definePreset } from "@primevue/themes";
import Aura from "@primevue/themes/aura";
import { ConfirmationService, ToastService, Tooltip } from "primevue";
import PrimeVue from "primevue/config";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router/router";

const init = async () => {
	const app = createApp(App);

	const Presets = definePreset(Aura, {
		semantic: {
			primary: {
				50: "#E6F3F2",
				100: "#CCEBE8",
				200: "#99D6D1",
				300: "#66C1BB",
				400: "#33ACA4",
				500: "#098e87",
				600: "#087F78",
				700: "#076F68",
				800: "#065F59",
				900: "#054F49",
				950: "#033B35",
			},
		},
	});

	app.use(PrimeVue, {
		theme: {
			preset: Presets,
			options: {
				darkModeSelector: ".app-dark",
			},
		},
	});

	app.use(router);
	app.use(ConfirmationService);
	app.use(ToastService);

	app.directive("tooltip", Tooltip);

	app.mount("#app");
};

init();
