<template>
	<div class="flex flex-col gap-5 text-base">
		<!-- Page header -->
		<div class="flex items-end justify-between gap-4">
			<div class="flex flex-col gap-1">
				<h1 class="text-xl font-medium text-slate-700 dark:text-surface-100">Create ADR</h1>
				<p class="text-sm text-slate-500 dark:text-surface-400">Fill in the decision record — the preview on the right updates as you type.</p>
			</div>
			<div class="flex items-center gap-2 shrink-0">
				<span class="font-mono text-sm text-slate-400">{{ form.id }}</span>
				<Tag v-if="form.status" :value="form.status" :severity="statusSeverity" />
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
			<!-- LEFT: form -->
			<div class="flex flex-col gap-7">
				<!-- Overview -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-info-circle text-xs" /> Overview
					</h2>

					<FormField label="Title" required>
						<InputText v-model="form.title" placeholder="e.g. API authentication strategy" fluid />
					</FormField>

					<div class="grid grid-cols-2 gap-3">
						<FormField label="Status" required>
							<Select v-model="form.status" :options="statusOptions" placeholder="Select status" fluid />
						</FormField>
						<FormField label="Scope" required :tip="{ message: 'The system or component boundary this applies to.' }">
							<InputText v-model="form.scope" placeholder="e.g. Backend API" fluid />
						</FormField>
					</div>

					<FormField label="Context">
						<Textarea v-model="form.context" placeholder="Describe the situation and why a decision was needed..." :auto-resize="true" rows="4" fluid />
					</FormField>
				</section>

				<!-- Decision -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-lightbulb text-xs" /> Decision
					</h2>

					<FormField label="Decision" required :tip="{ message: 'Supports code blocks — use the </> button for fenced code.' }">
						<MdEditor
							v-model="form.decision"
							:theme="isDark ? 'dark' : 'light'"
							:preview="false"
							:toolbars="mdToolbars"
							:footers="[]"
							language="en-US"
							placeholder="State the decision clearly. What was chosen and why?"
							style="height: 220px"
						/>
					</FormField>

					<FormField label="Alternatives considered">
						<div class="flex gap-2">
							<InputText v-model="alternativeInput" placeholder="Add an alternative..." class="flex-1" @keydown.enter.prevent="addAlternative" />
							<Button icon="pi pi-plus" severity="secondary" aria-label="Add alternative" @click="addAlternative" />
						</div>
						<div v-if="form.alternatives.length" class="flex flex-wrap gap-1.5 mt-2">
							<Chip v-for="(alt, i) in form.alternatives" :key="i" :label="alt" removable @remove="form.alternatives.splice(i, 1)" />
						</div>
					</FormField>

					<FormField label="Related ADRs" :tip="{ message: 'Comma-separated IDs of related decisions.' }">
						<InputText v-model="form.relatedAdrs" placeholder="e.g. ADR-001, ADR-002" fluid />
					</FormField>
				</section>

				<!-- Implementation -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-code text-xs" /> Implementation
					</h2>

					<FormField label="Implementation" :tip="{ message: 'Code examples, exception classes, response shapes. Use the </> button for fenced code blocks.' }">
						<MdEditor
							v-model="form.implementation"
							:theme="isDark ? 'dark' : 'light'"
							:preview="false"
							:toolbars="mdToolbars"
							:footers="[]"
							language="en-US"
							placeholder="Show how the decision is implemented — e.g. code examples, correct vs incorrect usage..."
							style="height: 340px"
						/>
					</FormField>
				</section>

				<!-- Consequences -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-arrows-h text-xs" /> Consequences
					</h2>

					<FormField label="Positive consequences">
						<Textarea v-model="form.positiveConsequences" placeholder="What improves as a result of this decision?" :auto-resize="true" rows="3" fluid />
					</FormField>

					<FormField label="Negative consequences / trade-offs">
						<Textarea v-model="form.negativeConsequences" placeholder="What gets harder, slower, or more complex?" :auto-resize="true" rows="3" fluid />
					</FormField>

					<FormField label="Notes" :tip="{ message: 'Supports code blocks — use the </> button for fenced code.' }">
						<MdEditor
							v-model="form.notes"
							:theme="isDark ? 'dark' : 'light'"
							:preview="false"
							:toolbars="mdToolbars"
							:footers="[]"
							language="en-US"
							placeholder="Implementation details, code snippets, links to docs..."
							style="height: 200px"
						/>
					</FormField>
				</section>
			</div>

			<!-- RIGHT: live preview (sticky) -->
			<div class="lg:sticky lg:top-0">
				<div class="rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-900 overflow-hidden">
					<div class="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800">
						<i class="pi pi-eye text-slate-400 text-sm" />
						<span class="text-sm font-medium text-slate-500 dark:text-surface-300">Live preview</span>
						<span class="ml-auto text-xs text-slate-400">{{ form.id }}.md</span>
					</div>
					<MdPreview
						:model-value="markdown"
						:theme="isDark ? 'dark' : 'light'"
						language="en-US"
						class="max-h-[calc(100vh-13rem)] overflow-y-auto px-5"
					/>
				</div>
			</div>
		</div>

		<!-- Actions -->
		<div class="flex items-center justify-end gap-2 pt-4 border-t border-slate-200 dark:border-surface-800">
			<Button label="Save draft" severity="secondary" icon="pi pi-save" @click="saveDraft" />
			<Button label="Create ADR" icon="pi pi-check" icon-pos="right" @click="submitAdr" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from "vue";
import { InputText, Textarea, Button, Tag, Chip, Select } from "primevue";
import { MdPreview, MdEditor } from "md-editor-v3";
import type { ToolbarNames } from "md-editor-v3";
import FormField from "@/components/form/FormField.vue";

interface AdrForm {
	id: string;
	status: string;
	title: string;
	scope: string;
	context: string;
	decision: string;
	alternatives: string[];
	relatedAdrs: string;
	implementation: string;
	positiveConsequences: string;
	negativeConsequences: string;
	notes: string;
}

// Focused toolbar for the code-capable sections (Decision, Implementation, Notes).
// The page's right-hand pane is the preview, so the editor's built-in preview is off.
const mdToolbars: ToolbarNames[] = [
	"bold",
	"italic",
	"strikeThrough",
	"title",
	"quote",
	"unorderedList",
	"orderedList",
	"-",
	"codeRow",
	"code",
	"link",
	"table",
	"-",
	"revoke",
	"next",
];

const statusOptions: string[] = ["Proposed", "Accepted", "Deprecated", "Superseded"];

const statusSeverityMap: Record<string, "success" | "info" | "warn" | "secondary"> = {
	Accepted: "success",
	Proposed: "info",
	Deprecated: "warn",
	Superseded: "secondary",
};

const alternativeInput = ref<string>("");

const form = ref<AdrForm>({
	id: "ADR-003",
	status: "",
	title: "",
	scope: "",
	context: "",
	decision: "",
	alternatives: [],
	relatedAdrs: "",
	implementation: "",
	positiveConsequences: "",
	negativeConsequences: "",
	notes: "",
});

const statusSeverity = computed(() => statusSeverityMap[form.value.status] ?? "secondary");

const addAlternative = (): void => {
	const val = alternativeInput.value.trim();
	if (val && !form.value.alternatives.includes(val)) {
		form.value.alternatives.push(val);
	}
	alternativeInput.value = "";
};

// Assemble the form into an ADR markdown document, mirroring the docs/adr/ format.
// Core sections always render (with a muted placeholder when empty) so the document
// structure is visible; optional sections appear only once filled in.
const markdown = computed<string>(() => {
	const f = form.value;
	const lines: string[] = [];

	lines.push(`# ${f.id}: ${f.title || "Untitled ADR"}`, "");
	lines.push("## Status", f.status || "_Not set_", "");
	lines.push("## Scope", f.scope || "_Not set_", "");
	lines.push("## Context", f.context || "_Describe the situation and why a decision was needed._", "");
	lines.push("## Decision", f.decision || "_State the decision clearly._");

	if (f.alternatives.length) {
		lines.push("", "### Alternatives Considered", ...f.alternatives.map((a) => `- ${a}`));
	}
	if (f.relatedAdrs.trim()) {
		lines.push("", "### Related ADRs", f.relatedAdrs.trim());
	}

	if (f.implementation.trim()) {
		lines.push("", "## Implementation", f.implementation.trim());
	}

	lines.push("", "## Consequences");
	if (f.positiveConsequences.trim()) {
		lines.push("", "### Positive", f.positiveConsequences.trim());
	}
	if (f.negativeConsequences.trim()) {
		lines.push("", "### Trade-offs", f.negativeConsequences.trim());
	}
	if (!f.positiveConsequences.trim() && !f.negativeConsequences.trim()) {
		lines.push("_What improves, and what gets harder as a result._");
	}
	if (f.notes.trim()) {
		lines.push("", "## Notes", f.notes.trim());
	}

	return lines.join("\n");
});

// Track the app's dark mode (PrimeVue toggles a `.app-dark` class) so the preview matches.
const hasDarkClass = (): boolean =>
	document.documentElement.classList.contains("app-dark") || document.body.classList.contains("app-dark");

const isDark = ref<boolean>(hasDarkClass());
const observer = new MutationObserver(() => {
	isDark.value = hasDarkClass();
});
observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });
onBeforeUnmount(() => observer.disconnect());

const saveDraft = (): void => {
	// TODO: persist draft (not yet wired to backend)
};

const submitAdr = (): void => {
	// TODO: POST assembled markdown to the backend index-document endpoint
};
</script>
