<template>
	<div class="flex flex-col gap-6 text-base px-5 py-2">
		<!-- Step indicator -->
		<div class="flex items-center">
			<template v-for="(step, i) in steps" :key="i">
				<div class="flex items-center gap-2">
					<div
						class="w-7 h-7 rounded-full flex items-center justify-center text-base font-medium shrink-0 transition-colors"
						:class="{
							'bg-green-50 text-green-700 border border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800':
								i < currentStep,
							'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800': i === currentStep,
							'bg-surface-100 text-surface-400 border border-surface-200 dark:bg-surface-800 dark:text-surface-500 dark:border-surface-700':
								i > currentStep,
						}"
					>
						<i v-if="i < currentStep" class="pi pi-check text-sm" />
						<span v-else>{{ i + 1 }}</span>
					</div>
					<span
						class="text-sm whitespace-nowrap"
						:class="{
							'text-green-600 dark:text-green-400': i < currentStep,
							'text-blue-600 font-medium dark:text-blue-400': i === currentStep,
							'text-surface-400 dark:text-surface-500': i > currentStep,
						}"
					>
						{{ step.label }}
					</span>
				</div>
				<div
					v-if="i < steps.length - 1"
					class="flex-1 h-px mx-2 transition-colors"
					:class="i < currentStep ? 'bg-green-200 dark:bg-green-800' : 'bg-surface-200 dark:bg-surface-700'"
				/>
			</template>
		</div>

		<!-- Step 1: Overview -->
		<template v-if="currentStep === 0">
			<div class="grid grid-cols-2 gap-3">
				<div class="flex flex-col gap-1.5">
					<label class="text-base font-medium text-surface-500 dark:text-surface-400">ADR ID</label>
					<InputText
						:value="form.id"
						readonly
						class="font-mono text-sm text-surface-400 dark:text-surface-500 bg-surface-50 dark:bg-surface-800"
					/>
					<span class="text-sm text-surface-400">Auto-assigned.</span>
				</div>
				<div class="flex flex-col gap-1.5">
					<label class="text-base font-medium text-surface-500 dark:text-surface-400">
						Status
						<span class="text-red-400">*</span>
					</label>
					<Select v-model="form.status" :options="statusOptions" placeholder="Select status" />
				</div>
			</div>

			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">
					Title
					<span class="text-red-400">*</span>
				</label>
				<InputText v-model="form.title" placeholder="e.g. API authentication strategy" />
			</div>

			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">
					Scope
					<span class="text-red-400">*</span>
				</label>
				<InputText v-model="form.scope" placeholder="e.g. Backend API, Frontend Web Application" />
				<span class="text-sm text-surface-400">The system or component boundary this decision applies to.</span>
			</div>

			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">Context</label>
				<Textarea
					v-model="form.context"
					placeholder="Describe the situation and why a decision was needed..."
					:auto-resize="true"
					rows="4"
				/>
			</div>
		</template>

		<!-- Step 2: Decision -->
		<template v-if="currentStep === 1">
			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">
					Decision
					<span class="text-red-400">*</span>
				</label>
				<Textarea v-model="form.decision" placeholder="State the decision clearly. What was chosen and why?" :auto-resize="true" rows="5" />
			</div>

			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">Alternatives considered</label>
				<div class="flex gap-2">
					<InputText
						v-model="alternativeInput"
						placeholder="Add an alternative..."
						class="flex-1"
						@keydown.enter.prevent="addAlternative"
					/>
					<Button icon="pi pi-plus" severity="secondary" @click="addAlternative" />
				</div>
				<div v-if="form.alternatives.length" class="flex flex-wrap gap-1.5 mt-1">
					<Chip v-for="(alt, i) in form.alternatives" :key="i" :label="alt" removable @remove="form.alternatives.splice(i, 1)" />
				</div>
			</div>

			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">Related ADRs</label>
				<InputText v-model="form.relatedAdrs" placeholder="e.g. ADR-001, ADR-002" />
				<span class="text-sm text-surface-400">Comma-separated IDs of related decisions.</span>
			</div>
		</template>

		<!-- Step 3: Consequences -->
		<template v-if="currentStep === 2">
			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">Positive consequences</label>
				<Textarea
					v-model="form.positiveConsequences"
					placeholder="What improves as a result of this decision?"
					:auto-resize="true"
					rows="4"
				/>
			</div>

			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">Negative consequences / trade-offs</label>
				<Textarea
					v-model="form.negativeConsequences"
					placeholder="What gets harder, slower, or more complex?"
					:auto-resize="true"
					rows="4"
				/>
			</div>

			<div class="flex flex-col gap-1.5">
				<label class="text-base font-medium text-surface-500 dark:text-surface-400">Notes</label>
				<Textarea v-model="form.notes" placeholder="Implementation details, code snippets, links to docs..." :auto-resize="true" rows="3" />
			</div>
		</template>

		<!-- Step 4: Review -->
		<template v-if="currentStep === 3">
			<div
				v-for="section in reviewSections"
				:key="section.title"
				class="rounded-xl border border-slate-300 dark:border-surface-700 bg-white dark:bg-surface-800 overflow-hidden"
			>
				<div class="flex items-center gap-2 px-4 py-3 border-b border-slate-500 dark:border-surface-700">
					<i :class="['pi', section.icon, 'text-surface-400 text-sm']" />
					<span class="text-base font-medium text-slate-500 dark:text-surface-400">{{ section.title }}</span>
				</div>
				<div class="divide-y divide-slate-200 dark:divide-surface-700">
					<div v-for="row in section.rows" :key="row.key" class="flex gap-4 px-4 py-3">
						<span class="text-sm text-slate-400 w-28 shrink-0 pt-0.5">{{ row.key }}</span>
						<span class="text-sm text-slate-700 dark:text-surface-200 flex-1">
							<Tag v-if="row.tag" :value="row.value" :severity="row.tagSeverity" class="text-sm" />
							<div v-else-if="row.chips" class="flex flex-wrap gap-1.5">
								<Chip v-for="c in row.chips" :key="c" :label="c" class="text-sm" />
							</div>
							<span v-else class="text-slate-500 dark:text-surface-400 leading-relaxed">{{ row.value || "—" }}</span>
						</span>
					</div>
				</div>
			</div>
		</template>

		<!-- Navigation -->
		<div class="flex items-center justify-between pt-4 border-t border-slate-300 dark:border-surface-800">
			<Button
				label="Back"
				severity="secondary"
				text
				icon="pi pi-arrow-left"
				:class="{ invisible: currentStep === 0 }"
				@click="currentStep--"
			/>
			<div class="flex gap-2">
				<Button label="Save draft" severity="secondary" @click="saveDraft" />
				<Button
					:label="currentStep === steps.length - 1 ? 'Submit ADR' : 'Continue'"
					:icon="currentStep === steps.length - 1 ? 'pi pi-check' : 'pi pi-arrow-right'"
					icon-pos="right"
					@click="handleNext"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { InputText, Textarea, Button, Tag, Chip, Select } from "primevue";

interface Step {
	label: string;
}

interface ReviewRow {
	key: string;
	value?: string;
	tag?: boolean;
	tagSeverity?: "success" | "info" | "warn" | "danger" | "secondary" | "contrast";
	chips?: string[];
}

interface ReviewSection {
	title: string;
	icon: string;
	rows: ReviewRow[];
}

interface AdrForm {
	id: string;
	status: string;
	title: string;
	scope: string;
	context: string;
	decision: string;
	alternatives: string[];
	relatedAdrs: string;
	positiveConsequences: string;
	negativeConsequences: string;
	notes: string;
}

const steps: Step[] = [{ label: "Overview" }, { label: "Decision" }, { label: "Consequences" }, { label: "Review" }];

const currentStep = ref<number>(0);
const alternativeInput = ref<string>("");

const statusOptions: string[] = ["Proposed", "Accepted", "Deprecated", "Superseded"];

const form = ref<AdrForm>({
	id: "ADR-003",
	status: "",
	title: "",
	scope: "",
	context: "",
	decision: "",
	alternatives: [],
	relatedAdrs: "",
	positiveConsequences: "",
	negativeConsequences: "",
	notes: "",
});

const addAlternative = (): void => {
	const val = alternativeInput.value.trim();
	if (val && !form.value.alternatives.includes(val)) {
		form.value.alternatives.push(val);
	}
	alternativeInput.value = "";
};

const reviewSections = computed<ReviewSection[]>(() => [
	{
		title: "Overview",
		icon: "pi-info-circle",
		rows: [
			{ key: "ID", value: form.value.id },
			{ key: "Title", value: form.value.title },
			{ key: "Status", value: form.value.status, tag: true, tagSeverity: "warn" },
			{ key: "Scope", value: form.value.scope },
			{ key: "Context", value: form.value.context },
		],
	},
	{
		title: "Decision",
		icon: "pi-lightbulb",
		rows: [
			{ key: "Decision", value: form.value.decision },
			{ key: "Alternatives", chips: form.value.alternatives },
			{ key: "Related ADRs", value: form.value.relatedAdrs },
		],
	},
	{
		title: "Consequences",
		icon: "pi-arrows-h",
		rows: [
			{ key: "Positive", value: form.value.positiveConsequences },
			{ key: "Trade-offs", value: form.value.negativeConsequences },
			{ key: "Notes", value: form.value.notes },
		],
	},
]);

const handleNext = (): void => {
	if (currentStep.value < steps.length - 1) {
		currentStep.value++;
	} else {
		submitAdr();
	}
};

const saveDraft = (): void => {
	// emit or call your save API
};

const submitAdr = (): void => {
	// emit or call your submit API
};
</script>
