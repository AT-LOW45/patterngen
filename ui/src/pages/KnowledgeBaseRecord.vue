<template>
	<div class="w-full flex items-center p-2 rounded-xl bg-white shadow-md mx-auto 2xl:max-w-[80%] sticky top-0 z-50">
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

	<div class="w-full 2xl:mx-auto 2xl:max-w-[80%] mt-4">
		<div v-if="isLoadingRecord" class="p-4 text-center text-gray-500">Loading record...</div>
		<div v-else-if="recordData" class="bg-white rounded-lg shadow-md p-6">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-2xl font-bold">{{ recordData.source }}</h2>
				<Button label="Save" icon="pi pi-save" :loading="saving" @click="onSave" />
			</div>
			<div class="space-y-4">
				<MdEditor v-model="editorText" style="height: 75vh" />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { knowledgeBaseService } from "@/api-service";
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
		records.value = response.data.sources || [];
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

const onSave = async () => {
	saving.value = true;
	try {
		await knowledgeBaseService.reindexRecord(currentRecord.value, editorText.value);
		toast.add({ severity: "success", summary: "Record reindexed", life: 3000 });
	} catch (error) {
		console.error("Failed to reindex record:", error);
		toast.add({ severity: "error", summary: "Failed to reindex record", life: 3000 });
	} finally {
		saving.value = false;
	}
};
</script>
