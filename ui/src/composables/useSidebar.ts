import { ref } from "vue";

// Module-level ref => shared singleton across every component that imports it,
// so the Sidebar and AppLayout stay in sync. Collapsed by default.
const collapsed = ref<boolean>(true);

export function useSidebar() {
	const toggle = (): void => {
		collapsed.value = !collapsed.value;
	};

	return { collapsed, toggle };
}
