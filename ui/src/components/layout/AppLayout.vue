<template>
	<div class="flex h-screen w-full">
		<Sidebar />
		<main class="flex-1 overflow-y-auto bg-slate-100 transition-all duration-300" :class="collapsed ? 'ml-16' : 'ml-64'">
			<div class="p-5 w-full">
				<router-view />
			</div>
		</main>
	</div>
</template>

<script setup lang="ts">
import Sidebar from "./Sidebar.vue";
import { useSidebar } from "@/composables/useSidebar";

const { collapsed } = useSidebar();
</script>
