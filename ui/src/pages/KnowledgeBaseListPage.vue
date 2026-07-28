<template>
	<div class="p-4">
		<div class="flex items-center justify-between w-full">
			<h1 class="text-2xl font-semibold mb-4">Knowledge Base</h1>
			<Button label="Create ADR" aria-controls="create-adr-menu" aria-haspopup="true" @click="toggle" />
		</div>
		<div v-if="error" class="text-red-600 mb-4">{{ error }}</div>
		<div class="rounded-md p-5 bg-white shadow-sm mt-3">
			<DataTable :value="records" :loading="loading" row-hover @row-click="onRowClick">
				<template #empty>
					<span class="text-slate-500">No records yet</span>
				</template>

				<Column field="name" header="Record Name"></Column>
				<Column header="Type">
					<template #body="{ data }">
						<Tag v-if="data.isDraft" value="Draft" severity="warn" />
						<span v-else class="text-sm text-slate-400">Published</span>
					</template>
				</Column>
				<Column header="Actions">
					<template #body="{ data }">
						<div class="flex items-center justify-start gap-2">
							<!-- Drafts are stored as the form object, not markdown, so there's nothing to download yet. -->
							<Button
								v-if="!data.isDraft"
								text
								severity="secondary"
								icon="pi pi-download"
								v-tooltip.top="'Download as markdown'"
								:loading="downloading === data.name"
								@click.stop="onDownload(data)"
							/>
							<Button text severity="danger" icon="pi pi-trash" @click="onDelete(data)" />
						</div>
					</template>
				</Column>
			</DataTable>
		</div>

		<Menu ref="menu" popup :model="menuItems" id="create-adr-menu"></Menu>

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
					<div class="flex flex-col gap-2">
						<FileUpload
							ref="fileUploadRef"
							name="file"
							:auto="false"
							choose-label="Choose File"
							:show-upload-button="false"
							:show-cancel-button="false"
							@select="onFileSelect"
							:multiple="false"
							accept=".md,text/markdown,text/plain"
							:max-file-size="104857600"
						>
							<template #content>
								<div
									v-if="selectedFile"
									class="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-50 dark:border-surface-700 bg-slate-100 dark:bg-surface-800 w-full"
								>
									<i class="pi pi-file text-surface-500 dark:text-surface-400 shrink-0" />
									<span class="flex-1 text-sm text-surface-700 dark:text-surface-200 truncate min-w-0" :title="selectedFile.name">
										{{ selectedFile.name }}
									</span>
									<span class="text-xs text-surface-400 dark:text-surface-500 shrink-0 whitespace-nowrap">
										{{ formatFileSize(selectedFile.size) }}
									</span>
									<Button text size="small" icon="pi pi-times" severity="secondary" rounded @click="clearFile" />
								</div>
							</template>
						</FileUpload>
					</div>
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
import { knowledgeBaseService, draftService } from "@/api-service";
import FormField from "@/components/form/FormField.vue";
import ROUTES from "@/router/routes";
import { downloadMarkdown } from "@/utils/download-markdown";
import { Button, Column, DataTable, Dialog, FileUpload, InputText, Menu, Message, Tag, useConfirm, useToast } from "primevue";
import { MenuItem } from "primevue/menuitem";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

interface KnowledgeBaseRecord {
	name: string;
	isDraft: boolean;
	draftId?: string;
}

const confirm = useConfirm();
const toast = useToast();
const router = useRouter();

const records = ref<KnowledgeBaseRecord[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const selectedRecord = ref<KnowledgeBaseRecord | null>(null);
const dialogVisible = ref(false);
const sourceInput = ref("");
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
// Source name currently being fetched for download, so only that row spins.
const downloading = ref<string | null>(null);
const fileUploadRef = ref();
const menu = ref();
const menuItems = ref<MenuItem[]>([
	{
		label: "Choose method to create ADR",
		items: [
			{
				label: "Upload Document",
				icon: "pi pi-upload",
				command: () => (dialogVisible.value = true),
			},
			{
				label: "Create with Template",
				icon: "pi pi-pen-to-square",
				command: () => router.push(ROUTES.knowledgeBaseCreate),
			},
		],
	},
]);

const toggle = (event: PointerEvent) => {
	menu.value?.toggle(event);
};

const fetchRecords = async () => {
	loading.value = true;
	error.value = null;
	try {
		const [published, drafts] = await Promise.all([knowledgeBaseService.getAllRecords(), draftService.listDrafts()]);

		const draftRows: KnowledgeBaseRecord[] = drafts.data.drafts.map((d) => ({
			name: d.draft.title?.trim() || d.id,
			isDraft: true,
			draftId: d.id,
		}));
		const publishedRows: KnowledgeBaseRecord[] = published.data.sources.map((source: string) => ({
			name: source,
			isDraft: false,
		}));

		records.value = [...draftRows, ...publishedRows];
	} catch (err) {
		error.value = err instanceof Error ? err.message : "Failed to fetch records";
	} finally {
		loading.value = false;
	}
};

const onRowClick = (event: any) => {
	const row = event.data as KnowledgeBaseRecord;
	selectedRecord.value = row;
	if (row.isDraft && row.draftId) {
		// resume the draft in the create page
		router.push({ path: ROUTES.knowledgeBaseCreate, query: { draft: row.draftId } });
	} else {
		router.push({ name: "KnowledgeBaseRecord", params: { id: row.name } });
	}
};

// The list only holds source names, so fetch the raw markdown before handing it
// to the browser. `@click.stop` on the button keeps the row-click navigation from
// firing alongside the download.
const onDownload = async (record: KnowledgeBaseRecord) => {
	downloading.value = record.name;
	try {
		const { data } = await knowledgeBaseService.getRawRecord(record.name);
		downloadMarkdown(record.name, data.content);
	} catch (err) {
		toast.add({ severity: "error", summary: "Failed to download record", detail: record.name, life: 3000 });
	} finally {
		downloading.value = null;
	}
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
				if (record.isDraft && record.draftId) {
					await draftService.deleteDraft(record.draftId);
				} else {
					await knowledgeBaseService.deleteRecord(record.name);
				}
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

const clearFile = () => {
	selectedFile.value = null;
	fileUploadRef.value?.clear();
};

const formatFileSize = (bytes: number): string => {
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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
