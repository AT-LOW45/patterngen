<template>
	<div class="w-full flex  items-center p-2 rounded-xl bg-white shadow-md mx-auto 2xl:max-w-[80%] sticky top-0">
		<Button label="Prev" icon="pi pi-arrow-left" icon-pos="left" severity="secondary" size="small" />
		<Select class="ml-auto" size="small" />
		<Button label="Prev" icon="pi pi-arrow-right" icon-pos="right" severity="secondary" class="ml-auto" size="small" />
	</div>
</template>

<script setup lang="ts">
import { Button, Select } from 'primevue';
</script>