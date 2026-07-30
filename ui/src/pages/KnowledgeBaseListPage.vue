<template>
	<div class="p-4">
		<div class="flex items-center justify-between w-full">
			<h1 class="text-2xl font-semibold mb-4">Knowledge Base</h1>
			<Button label="Create ADR" aria-controls="create-adr-menu" aria-haspopup="true" @click="toggle" />
		</div>
		<div v-if="error && !uploadError" class="text-red-600 mb-4">{{ error }}</div>
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
			:dismissable-mask="!uploading && !reviewing"
		>
			<div class="space-y-4">
				<div class="flex flex-col gap-5 pt-3">
					<Message severity="info">
						Only markdown and plain text files are supported. The record's ID is derived from the document's title, or from the filename if
						it has none.
					</Message>
					<div class="flex flex-col gap-2">
						<FileUpload
							ref="fileUploadRef"
							name="file"
							:auto="false"
							choose-label="Choose File"
							:show-upload-button="false"
							:show-cancel-button="false"
							@select="onFileSelect"
							@clear="((error = null), (uploadError = false))"
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

				<!-- Quality review, rendered inline rather than in ReviewFindingsDialog so the
				     user keeps the source/file inputs in view while fixing the file. Advisory:
				     every state leaves "Upload anyway" available. -->
				<div v-if="reviewing" class="flex items-center gap-2 text-sm text-slate-500 dark:text-surface-400">
					<i class="pi pi-spin pi-spinner" />
					<span>Reviewing ADR quality…</span>
				</div>

				<Message v-else-if="reviewError" severity="warn" :closable="false">
					Quality review unavailable — you can upload anyway and review later.
				</Message>

				<div v-else-if="reviewFindings.length" class="flex flex-col gap-2">
					<span class="text-sm font-medium text-slate-600 dark:text-surface-300">Quality review found {{ reviewSummary }}</span>
					<ul class="flex max-h-56 flex-col gap-2 overflow-y-auto pr-1">
						<li
							v-for="(finding, i) in reviewFindings"
							:key="i"
							class="flex gap-2 rounded-lg border border-l-4 border-slate-200 p-3 dark:border-surface-700"
							:class="severityConfig(finding.severity).spine"
						>
							<i :class="[severityConfig(finding.severity).icon, severityConfig(finding.severity).fg, 'mt-0.5 shrink-0']" />
							<div class="flex min-w-0 flex-col gap-0.5">
								<span class="text-xs font-semibold uppercase tracking-wide" :class="severityConfig(finding.severity).fg">
									{{ severityConfig(finding.severity).label }} · {{ finding.section }}
								</span>
								<p class="text-sm leading-relaxed text-slate-700 dark:text-surface-200">{{ finding.message }}</p>
							</div>
						</li>
					</ul>
				</div>

				<div v-else-if="uploadError && error" class="text-red-500">
					{{ error }}
				</div>
				<div v-else-if="reviewRan" class="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
					<i class="pi pi-check-circle" />
					<span>No issues found</span>
				</div>
			</div>
			<template #footer>
				<Button
					label="Cancel"
					severity="secondary"
					icon="pi pi-times"
					text
					@click="dialogVisible = false"
					:disabled="uploading || reviewing"
				/>
				<Button :label="uploadLabel" icon="pi pi-upload" :loading="uploading || reviewing" @click="onUpload" />
			</template>
		</Dialog>
	</div>
</template>

<script setup lang="ts">
import { knowledgeBaseService, draftService, reviewService, ReviewFinding } from "@/api-service";
import ROUTES from "@/router/routes";
import { downloadMarkdown } from "@/utils/download-markdown";
import axios from "axios";
import { Button, Column, DataTable, Dialog, FileUpload, Menu, Message, Tag, useConfirm, useToast } from "primevue";
import { MenuItem } from "primevue/menuitem";
import { computed, onMounted, ref, watch } from "vue";
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
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
// Source name currently being fetched for download, so only that row spins.
const downloading = ref<string | null>(null);
const fileUploadRef = ref();
const uploadError = ref(false);

// Upload-dialog quality review. `reviewRan` distinguishes "not reviewed yet" from
// "reviewed and clean", which is what turns the Upload button into "Upload anyway".
const reviewing = ref(false);
const reviewFindings = ref<ReviewFinding[]>([]);
const reviewError = ref(false);
const reviewRan = ref(false);

const SEVERITY = {
	error: {
		label: "Error",
		icon: "pi pi-times-circle",
		fg: "text-rose-600 dark:text-rose-400",
		spine: "border-l-rose-500",
	},
	warning: {
		label: "Warning",
		icon: "pi pi-exclamation-triangle",
		fg: "text-amber-600 dark:text-amber-400",
		spine: "border-l-amber-500",
	},
} as const;

const severityConfig = (severity: ReviewFinding["severity"]) => SEVERITY[severity];

const reviewSummary = computed<string>(() => {
	const errors = reviewFindings.value.filter((f) => f.severity === "error").length;
	const warnings = reviewFindings.value.filter((f) => f.severity === "warning").length;
	const parts: string[] = [];
	if (errors) parts.push(`${errors} error${errors > 1 ? "s" : ""}`);
	if (warnings) parts.push(`${warnings} warning${warnings > 1 ? "s" : ""}`);
	return parts.join(" · ");
});

// Once the review has flagged something (or couldn't run), the next click is the
// user deliberately overriding it.
const uploadLabel = computed<string>(() =>
	reviewRan.value && (reviewFindings.value.length > 0 || reviewError.value) ? "Upload anyway" : "Upload",
);

const resetReview = () => {
	reviewFindings.value = [];
	reviewError.value = false;
	reviewRan.value = false;
};

// A fresh dialog session starts unreviewed.
watch(dialogVisible, () => resetReview());
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
		// Findings belong to the previous file's content.
		resetReview();
	}
};

const clearFile = () => {
	selectedFile.value = null;
	fileUploadRef.value?.clear();
	resetReview();
};

const formatFileSize = (bytes: number): string => {
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Reads the selected file and reviews its markdown. Returns true when it's clear to
// upload without asking. Fail-safe: an unreadable file or a review outage sets
// `reviewError` rather than blocking, mirroring the create/edit gates.
const runReview = async (file: File): Promise<boolean> => {
	reviewing.value = true;
	try {
		const content = await file.text();
		const result = await reviewService.reviewDocument(content);
		reviewFindings.value = result.data.findings;
		return result.data.findings.length === 0;
	} catch (err) {
		console.error("ADR review failed:", err);
		reviewError.value = true;
		return false;
	} finally {
		reviewing.value = false;
		reviewRan.value = true;
	}
};

const doUpload = async (file: File) => {
	uploadError.value = false;
	uploading.value = true;
	error.value = null;
	try {
		// The backend derives and returns the source key — nothing is sent for it.
		const { data } = await knowledgeBaseService.indexDocument(file);
		selectedFile.value = null;
		if (fileUploadRef.value) {
			fileUploadRef.value.clear();
		}
		resetReview();
		fetchRecords();
		dialogVisible.value = false;
		toast.add({ severity: "success", summary: "Uploaded record", detail: data.source, life: 3000 });
	} catch (err) {
		// A derivation failure (400) or an existing record (409) explains itself in `detail`.
		const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined;
		error.value = detail ?? (err instanceof Error ? err.message : "Failed to upload file");
		uploadError.value = true;
	} finally {
		uploading.value = false;
	}
};

const onUpload = async () => {
	if (!selectedFile.value) {
		error.value = "Please select a file to upload.";
		return;
	}

	const file = selectedFile.value;

	// Second click on "Upload anyway" — the user has seen the findings and chose to proceed.
	if (reviewRan.value) {
		await doUpload(file);
		return;
	}

	error.value = null;
	const clean = await runReview(file);
	// Not clean: findings (or the unavailable notice) render inline and the button
	// becomes "Upload anyway". Nothing is uploaded yet.
	if (!clean) return;

	await doUpload(file);
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
