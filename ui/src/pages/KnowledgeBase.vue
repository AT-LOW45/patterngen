<template>
	<div class="p-4">
		<h1 class="text-2xl font-bold mb-4">Knowledge Base</h1>
		<div v-if="error" class="text-red-600 mb-4">{{ error }}</div>
		<div class="rounded-md p-5 bg-white shadow-sm">
			<div class="mb-4">
				<Button label="Upload Document" icon="pi pi-upload" @click="dialogVisible = true" />
			</div>
			<DataTable :value="records" :loading="loading" row-hover @row-click="onRowClick">
				<template #empty>
					<span class="text-slate-500">No records yet</span>
				</template>

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

		<Dialog
			v-model:visible="dialogVisible"
			header="Upload Document"
			:modal="true"
			class="w-full"
			style="width: 500px"
			:dismissable-mask="!uploading"
		>
			<div class="space-y-4">
				<div>
					<FormField label="Source Query String" :tip="{ message: 'the vector db will use this to index documents' }">
						<InputText id="source" v-model="sourceInput" placeholder="Enter source" class="w-full" />
					</FormField>
				</div>
				<div class="flex flex-col gap-5">
					<Message severity="info">Only markdown and plain text files are supported</Message>
					<FileUpload
						ref="fileUploadRef"
						name="file"
						:auto="false"
						choose-label="Choose File"
						:show-upload-button="false"
						:show-cancel-button="false"
						@select="onFileSelect"
						accept="*"
						:max-file-size="104857600"
					/>
					<div v-if="selectedFile" class="mt-2 text-sm text-gray-600">Selected: {{ selectedFile.name }}</div>
				</div>
			</div>
			<template #footer>
				<Button label="Cancel" severity="secondary" icon="pi pi-times" text @click="dialogVisible = false" :disabled="uploading" />
				<Button label="Upload" icon="pi pi-upload" :loading="uploading" @click="onUpload" />
			</template>
		</Dialog>
	</div>
</template>

<script setup lang="ts">
import { Column, DataTable, Button, Drawer, Dialog, InputText, FileUpload, useConfirm, useToast, Message } from "primevue";
import { onMounted, ref } from "vue";
import { knowledgeBaseService } from "@/api-service";
import { useRouter } from "vue-router";
import FormField from "@/components/form/FormField.vue";

interface KnowledgeBaseRecord {
	name: string;
}

const confirm = useConfirm();
const toast = useToast();
const router = useRouter();

const records = ref<KnowledgeBaseRecord[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const drawerVisible = ref(false);
const selectedRecord = ref<KnowledgeBaseRecord | null>(null);
const dialogVisible = ref(false);
const sourceInput = ref("");
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const fileUploadRef = ref();

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
	router.push({ name: "KnowledgeBaseRecord", params: { id: event.data.name } });
	// drawerVisible.value = true;
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

const onFileSelect = (event: any) => {
	if (event.files && event.files.length > 0) {
		selectedFile.value = event.files[0];
	}
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
		selectedFile.value = null;
		if (fileUploadRef.value) {
			fileUploadRef.value.clear();
		}
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
