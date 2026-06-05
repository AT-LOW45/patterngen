<template>
	<div class="p-4">
		<h1 class="text-2xl font-bold mb-4">Knowledge Base</h1>
		<div v-if="error" class="text-red-600 mb-4">{{ error }}</div>
		<div class="rounded-md p-3 bg-white shadow-sm">
			<div class="mb-4">
				<Button label="Upload Document" icon="pi pi-upload" @click="dialogVisible = true" />
			</div>
			<DataTable :value="records" :loading="loading" row-hover @row-click="onRowClick">
				<Column field="name" header="Record Name"></Column>
				<Column header="Actions">
					<template #body="{ data }">
						<div class="flex items-center justify-start gap-2">
							<Button text severity="danger" icon="pi pi-trash" @click="onDelete(data)" />
						</div>
					</template>
				</Column>
			</DataTable>
		</div>

		<Drawer v-model:visible="drawerVisible" header="Record Details" position="right" :modal="true">
			<div v-if="selectedRecord">
				<p>
					<strong>Name:</strong>
					{{ selectedRecord.name }}
				</p>
			</div>
		</Drawer>

		<Dialog v-model:visible="dialogVisible" header="Upload Document" :modal="true" class="w-full md:w-96">
			<div class="space-y-4">
				<div>
					<label for="source" class="block text-sm font-medium mb-2">Source Query String</label>
					<InputText id="source" v-model="sourceInput" placeholder="Enter source" class="w-full" />
				</div>
				<div>
					<label for="file" class="block text-sm font-medium mb-2">Select File</label>
					<input id="file" type="file" @change="onFileChange" class="w-full" />
					<div v-if="selectedFile" class="mt-2 text-sm text-gray-600">Selected: {{ selectedFile.name }}</div>
				</div>
			</div>
			<template #footer>
				<Button label="Cancel" icon="pi pi-times" text @click="dialogVisible = false" />
				<Button label="Upload" icon="pi pi-upload" :loading="uploading" @click="onUpload" />
			</template>
		</Dialog>
	</div>
</template>

<script setup lang="ts">
import { Column, DataTable, Button, Drawer, Dialog, InputText, useConfirm, useToast } from "primevue";
import { onMounted, ref } from "vue";
import { knowledgeBaseService } from "../api-service";

interface KnowledgeBaseRecord {
	name: string;
}

const confirm = useConfirm();
const toast = useToast();

const records = ref<KnowledgeBaseRecord[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const drawerVisible = ref(false);
const selectedRecord = ref<KnowledgeBaseRecord | null>(null);
const dialogVisible = ref(false);
const sourceInput = ref("");
const selectedFile = ref<File | null>(null);
const uploading = ref(false);

const fetchRecords = async () => {
	loading.value = true;
	error.value = null;
	try {
		const response = await knowledgeBaseService.getAllRecords();
		console.log(response.data)
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

const onDelete = (record: KnowledgeBaseRecord) => {
	confirm.require({
		group: "resets",
		message: `Delete "${record.name}"? This action cannot be undone.`,
		header: "Confirm Deletion",
		icon: "pi pi-exclamation-triangle",
		rejectProps: {
			severity: "secondary",
		},
		accept: async () => {
			loading.value = true;
			error.value = null;
			try {
				await knowledgeBaseService.deleteRecord(record.name);
				fetchRecords();
			} catch (err) {
				error.value = err instanceof Error ? err.message : "Failed to delete record";
			} finally {
				loading.value = false;
			}
		},
	});
};

const onFileChange = (e: Event) => {
	const target = e.target as HTMLInputElement;
	selectedFile.value = target.files?.[0] ?? null;
};

const onUpload = async () => {
	if (!sourceInput.value) {
		error.value = "Please enter a source query string.";
		return;
	}
	if (!selectedFile.value) {
		error.value = "Please select a file to upload.";
		return;
	}
	uploading.value = true;
	error.value = null;
	try {
		await knowledgeBaseService.indexDocument(sourceInput.value, selectedFile.value);
		sourceInput.value = "";
		const fileInput = document.getElementById("kb-file-input") as HTMLInputElement | null;
		if (fileInput) fileInput.value = "";
		selectedFile.value = null;
		fetchRecords();
		dialogVisible.value = false;
		toast.add({ severity: "success", summary: "Uploaded record", life: 3000 });
	} catch (err) {
		error.value = err instanceof Error ? err.message : "Failed to upload file";
	} finally {
		uploading.value = false;
	}
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
