<template>
	<div class="p-4">
		<h1 class="text-2xl font-bold mb-4">Knowledge Base</h1>
		<div v-if="error" class="text-red-600 mb-4">{{ error }}</div>
		<div class="rounded-md p-3 bg-white shadow-sm">
			<DataTable 
				:value="records" 
				:loading="loading" 
				row-hover
				@row-click="onRowClick"
			>
				<Column field="name" header="Record Name"></Column>
				<Column header="Actions">
					<template #body>
						<div class="flex items-center justify-start gap-2">
							<Button text severity="danger" icon="pi pi-trash" />
						</div>
					</template>
				</Column>
			</DataTable>
		</div>
		
		<Drawer 
			v-model:visible="drawerVisible" 
			header="Record Details" 
			position="right"
			:modal="true"
		>
			<div v-if="selectedRecord">
				<p><strong>Name:</strong> {{ selectedRecord.name }}</p>
			</div>
		</Drawer>
	</div>
</template>

<script setup lang="ts">
import { Column, DataTable, Button, Drawer } from "primevue";
import { onMounted, ref } from "vue";
import { knowledgeBaseService } from "../api-service";

interface KnowledgeBaseRecord {
	name: string;
}

const records = ref<KnowledgeBaseRecord[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const drawerVisible = ref(false);
const selectedRecord = ref<KnowledgeBaseRecord | null>(null);

const fetchRecords = async () => {
	loading.value = true;
	error.value = null;
	try {
		const response = await knowledgeBaseService.getAllRecords();
		records.value = response.data.sources.map((source: string) => ({
			name: source,
		}));
	} catch (err) {
		error.value = err instanceof Error ? err.message : "Failed to fetch records";
	} finally {
		loading.value = false;
	}
};

const onRowClick = (event: any) => {
	selectedRecord.value = event.data;
	drawerVisible.value = true;
};

onMounted(() => {
	fetchRecords();
});
</script>

<style scoped>
:deep(.p-datatable tbody > tr) {
	cursor: pointer;
}
</style>
