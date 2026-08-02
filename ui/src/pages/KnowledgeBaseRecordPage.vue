<template>
	<div class="w-full flex items-center p-2 rounded-xl bg-white shadow-md mx-auto 2xl:max-w-[90%] sticky top-0 z-50">
		<Button
			label="Prev"
			icon="pi pi-arrow-left"
			icon-pos="left"
			severity="secondary"
			size="small"
			@click="goToPrevious"
			:disabled="currentIndex === 0"
		/>
		<Select
			v-model="currentRecord"
			class="ml-auto"
			size="small"
			:options="recordOptions"
			option-label="label"
			option-value="value"
			@change="onRecordSelected"
		/>
		<Button
			label="Next"
			icon="pi pi-arrow-right"
			icon-pos="right"
			severity="secondary"
			class="ml-auto"
			size="small"
			@click="goToNext"
			:disabled="currentIndex === records.length - 1"
		/>
	</div>

	<div class="w-full 2xl:mx-auto 2xl:max-w-[90%] mt-4">
		<div v-if="isLoadingRecord" class="p-4 text-center text-gray-500">Loading record...</div>
		<div v-else-if="recordData" class="bg-white rounded-lg shadow-md p-6">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-2xl font-bold">{{ recordData.source }}</h2>
				<div class="flex items-center gap-2">
					<Button label="Download" icon="pi pi-download" severity="secondary" outlined @click="onDownload" />
					<Button label="Save" icon="pi pi-save" :loading="saving" @click="onSave" />
				</div>
			</div>
			<div class="space-y-4">
				<MdEditor v-model="editorText" style="height: 75vh" />
			</div>
		</div>
	</div>

	<ReviewFindingsDialog
		v-model:visible="reviewDialogOpen"
		:findings="reviewFindings"
		:loading="checking"
		:error="hasReviewError"
		@submit-anyway="onSubmitAnyway"
	/>
</template>

<script setup lang="ts">
import { knowledgeBaseService, ReviewFinding, reviewService } from "@/api-service";
import ReviewFindingsDialog from "@/components/dialog/ReviewFindingsDialog.vue";
import { downloadMarkdown } from "@/utils/download-markdown";
import axios from "axios";
import { MdEditor } from "md-editor-v3";
import { Button, Select, useToast } from "primevue";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();
const toast = useToast();

const records = ref<any[]>([]);
const currentRecord = ref<string>("");
const recordData = ref<any>(null);
const isLoadingRecord = ref(false);
const saving = ref(false);
const editorText = ref("");

const checking = ref(false);
const reviewDialogOpen = ref(false);
const reviewFindings = ref<ReviewFinding[]>([]);
const hasReviewError = ref(false);

const recordOptions = computed(() =>
	records.value.map((record) => ({
		label: record,
		value: record,
	})),
);

const currentIndex = computed(() => records.value.indexOf(currentRecord.value));

const fetchRecord = async (recordName: string) => {
	if (!recordName) return;
	isLoadingRecord.value = true;
	try {
		const response = await knowledgeBaseService.getRawRecord(recordName);
		recordData.value = response.data;
	} catch (error) {
		console.error("Failed to fetch record:", error);
		recordData.value = null;
	} finally {
		isLoadingRecord.value = false;
	}
};

watch(currentRecord, (newRecord) => {
	if (newRecord) {
		fetchRecord(newRecord);
	}
});

watch(recordData, (newData) => {
	if (newData && newData.content) {
		editorText.value = newData.content;
	} else {
		editorText.value = "";
	}
});

onMounted(async () => {
	try {
		const response = await knowledgeBaseService.getAllRecords();
		records.value = response.data.records.map((r) => r.source);
		// Initialize to record from route param, or first record if not found
		const recordIdFromRoute = route.params.id as string;
		if (recordIdFromRoute && records.value.includes(recordIdFromRoute)) {
			currentRecord.value = recordIdFromRoute;
		} else if (records.value.length > 0) {
			currentRecord.value = records.value[0];
			onRecordSelected();
		}
	} catch (error) {
		console.error("Failed to fetch records:", error);
	}
});

const goToPrevious = () => {
	const idx = currentIndex.value;
	if (idx > 0) {
		currentRecord.value = records.value[idx - 1];
		onRecordSelected();
	}
};

const goToNext = () => {
	const idx = currentIndex.value;
	if (idx < records.value.length - 1) {
		currentRecord.value = records.value[idx + 1];
		onRecordSelected();
	}
};

const onRecordSelected = () => {
	if (currentRecord.value) {
		router.push(`/knowledge-base/${currentRecord.value}`);
	}
};

// Downloads what's currently in the editor, including unsaved edits — the user
// gets the document they can see, not the last indexed version.
const onDownload = () => {
	downloadMarkdown(currentRecord.value, editorText.value);
};

const hasAdrErrors = async () => {
	reviewFindings.value = [];
	hasReviewError.value = false;
	checking.value = true;
	try {
		reviewDialogOpen.value = true;
		const result = await reviewService.reviewDocument(editorText.value);
		const findings = result.data.findings;
		if (findings.length > 0) {
			reviewFindings.value = findings;
			return true;
		}
		return false;
	} catch (error) {
		hasReviewError.value = true;
		return true;
	} finally {
		checking.value = false;
	}
};

// Saves the editor buffer and follows a rename: editing the H1 moves the record to a new
// source key, so the list entry, selection and route all have to point at the new one.
const save = async () => {
	const previous = currentRecord.value;
	const { data } = await knowledgeBaseService.saveMarkdown(previous, editorText.value);

	if (data.source !== previous) {
		const index = records.value.indexOf(previous);
		if (index !== -1) {
			records.value[index] = data.source;
		}
		// Assigning currentRecord refetches via its watcher; `replace` so the back button
		// doesn't return to a key that no longer exists.
		currentRecord.value = data.source;
		router.replace(`/knowledge-base/${encodeURIComponent(data.source)}`);
	} else {
		// The server restamps the ADR id, so what's stored can differ from what was typed.
		// Pull it back so the editor shows the canonical version rather than a stale edit.
		await fetchRecord(previous);
	}

	toast.add({ severity: "success", summary: "Record reindexed", detail: data.source, life: 3000 });
};

const onSaveFailed = (error: unknown) => {
	console.error("Failed to reindex record:", error);
	const detail = axios.isAxiosError(error) ? error.response?.data?.detail : undefined;
	toast.add({ severity: "error", summary: "Failed to reindex record", detail, life: 4000 });
};

const onSave = async () => {
	saving.value = true;
	try {
		const needsAmendment = await hasAdrErrors();
		if (needsAmendment) return;
		reviewDialogOpen.value = false;

		await save();
	} catch (error) {
		onSaveFailed(error);
	} finally {
		saving.value = false;
	}
};

// User chose "Submit anyway" in the review dialog — save without re-reviewing.
const onSubmitAnyway = async () => {
	try {
		saving.value = true;
		await save();
	} catch (error) {
		onSaveFailed(error);
	} finally {
		saving.value = false;
	}
};
</script>
