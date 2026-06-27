<template>
	<aside class="fixed left-0 top-0 w-64 h-screen bg-slate-50 overflow-y-auto shadow">
		<div class="border-b border-slate-200 px-5 py-5">
			<h1 class="m-0 text-2xl font-semibold">Patterngen</h1>
		</div>
		<nav class="py-5">
			<ul class="list-none p-0 m-0">
				<li>
					<router-link
						:to="ROUTES.default"
						class="flex items-center gap-3 px-5 py-3  no-underline hover:bg-slate-100 transition-colors duration-300"
						active-class="bg-slate-200 text-slate-900 font-semibold"
					>
						<Icon icon="mdi:book-open-variant" width="20" height="20" />
						Knowledge Base
					</router-link>
				</li>
			</ul>
		</nav>
	</aside>
</template>

<script setup lang="ts">
import ROUTES from "@/router/routes";
import { Icon } from "@iconify/vue";
</script>
