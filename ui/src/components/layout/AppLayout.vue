<template>
	<div class="flex h-screen w-full">
		<Sidebar />
		<main class="flex-1 ml-64 overflow-y-auto bg-slate-100">
			<div class="p-5 w-full">
				<router-view />
			</div>
		</main>
	</div>
</template>

<script setup lang="ts">
import Sidebar from "./Sidebar.vue";
</script>
