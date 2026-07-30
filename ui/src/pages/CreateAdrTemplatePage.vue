<template>
	<div class="flex flex-col gap-5 text-base">
		<!-- Page header -->
		<div class="flex items-end justify-between gap-4">
			<div class="flex flex-col gap-1">
				<h1 class="text-xl font-medium text-slate-700 dark:text-surface-100">Create ADR</h1>
				<p class="text-slate-500 dark:text-surface-400">Fill in the decision record — the preview on the right updates as you type.</p>
			</div>
			<div class="flex flex-col items-end gap-1 shrink-0">
				<div class="flex items-center gap-2">
					<span class="font-mono text-sm text-slate-400">{{ form.id || "Assigning ID…" }}</span>
					<Tag v-if="form.status" :value="form.status" :severity="statusSeverity" />
				</div>
				<!-- The server assigns the real id on create, so this one can shift if another
				     ADR lands first (or if this page/draft has been open a while). -->
				<div class="flex items-center gap-2">
					<Icon icon="material-symbols:info" />
					<span v-if="form.id" class="text-sm text-slate-400 dark:text-surface-400">
						Temporary — the final ID is assigned when you create the ADR.
					</span>
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
			<!-- LEFT: form -->
			<div class="flex flex-col gap-7">
				<!-- Overview -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-info-circle text-xs" />
						Overview
					</h2>

					<FormField label="Title" required :error-message="validationErrors?.properties?.title?.errors">
						<InputText v-model="form.title" placeholder="e.g. API authentication strategy" fluid />
					</FormField>

					<div class="grid grid-cols-2 gap-3">
						<FormField label="Status" required :error-message="validationErrors?.properties?.status?.errors">
							<Select v-model="form.status" :options="statusOptions" placeholder="Select status" fluid />
						</FormField>
						<FormField
							label="Scope"
							required
							:tip="{ message: 'The system or component boundary this applies to.' }"
							:error-message="validationErrors?.properties?.scope?.errors"
						>
							<InputText v-model="form.scope" placeholder="e.g. Backend API" fluid />
						</FormField>
					</div>

					<FormField label="Context">
						<Textarea
							v-model="form.context"
							placeholder="Describe the situation and why a decision was needed..."
							:auto-resize="true"
							rows="4"
							fluid
						/>
					</FormField>
				</section>

				<!-- Decision -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-lightbulb text-xs" />
						Decision
					</h2>

					<FormField
						label="Decision"
						required
						:tip="{ message: 'Supports code blocks — use the </> button for fenced code.' }"
						:error-message="validationErrors?.properties?.decision?.errors"
					>
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
							<InputText
								v-model="alternativeInput"
								placeholder="Add an alternative..."
								class="flex-1"
								@keydown.enter.prevent="addAlternative"
							/>
							<Button icon="pi pi-plus" severity="secondary" aria-label="Add alternative" @click="addAlternative" />
						</div>
						<div v-if="form.alternatives.length" class="flex flex-wrap gap-1.5 mt-2">
							<Chip v-for="(alt, i) in form.alternatives" :key="i" :label="alt" removable @remove="form.alternatives.splice(i, 1)" />
						</div>
					</FormField>

					<FormField label="Related ADRs" :tip="{ message: 'Existing records in the knowledge base that this decision relates to.' }">
						<MultiSelect
							v-model="form.relatedAdrs"
							:options="relatedAdrChoices"
							:loading="loadingRelatedAdrs"
							placeholder="Select related ADRs"
							display="chip"
							filter
							:show-toggle-all="false"
							empty-message="No other ADRs yet"
							empty-filter-message="No match"
							fluid
						/>
					</FormField>
				</section>

				<!-- Implementation -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-code text-xs" />
						Implementation
					</h2>

					<FormField
						label="Implementation"
						:tip="{ message: 'Code examples, exception classes, response shapes. Use the </> button for fenced code blocks.' }"
					>
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

				<!-- Custom sections -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-plus-circle text-xs" />
						Custom sections
					</h2>

					<div
						v-for="(section, i) in form.customSections"
						:key="i"
						class="flex flex-col gap-3 rounded-xl border border-slate-200 dark:border-surface-700 p-4 bg-white"
					>
						<div class="flex items-center gap-2">
							<InputText v-model="section.heading" placeholder="Section heading — e.g. Exception Classes" class="flex-1" />
							<SelectButton
								v-model="section.format"
								:options="formatOptions"
								option-label="label"
								option-value="value"
								:allow-empty="false"
								size="small"
							/>
							<Button icon="pi pi-trash" severity="danger" text aria-label="Remove section" @click="removeCustomSection(i)" />
						</div>

						<Textarea
							v-if="section.format === 'plain'"
							v-model="section.body"
							placeholder="Section content..."
							:auto-resize="true"
							rows="3"
							fluid
						/>
						<MdEditor
							v-else
							v-model="section.body"
							:theme="isDark ? 'dark' : 'light'"
							:preview="false"
							:toolbars="mdToolbars"
							:footers="[]"
							language="en-US"
							placeholder="Section content — supports code blocks via the </> button..."
							style="height: 260px"
						/>
					</div>

					<Button label="Add section" icon="pi pi-plus" severity="secondary" outlined class="self-start" @click="addCustomSection" />
				</section>

				<!-- Consequences -->
				<section class="flex flex-col gap-4">
					<h2 class="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-slate-400">
						<i class="pi pi-arrows-h text-xs" />
						Consequences
					</h2>

					<FormField label="Positive consequences">
						<Textarea
							v-model="form.positiveConsequences"
							placeholder="What improves as a result of this decision?"
							:auto-resize="true"
							rows="3"
							fluid
						/>
					</FormField>

					<FormField label="Negative consequences / trade-offs">
						<Textarea
							v-model="form.negativeConsequences"
							placeholder="What gets harder, slower, or more complex?"
							:auto-resize="true"
							rows="3"
							fluid
						/>
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
			<div class="lg:sticky lg:top-5">
				<div
					class="rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-900 overflow-hidden flex flex-col max-h-[calc(100vh-5.5rem)]"
				>
					<div
						class="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 shrink-0"
					>
						<i class="pi pi-eye text-slate-400 text-sm" />
						<span class="text-sm font-medium text-slate-500 dark:text-surface-300">Live preview</span>
						<span class="ml-auto text-xs text-slate-400">{{ form.id || "adr" }}.md</span>
					</div>
					<MdPreview
						:model-value="markdown"
						:theme="isDark ? 'dark' : 'light'"
						language="en-US"
						class="flex-1 min-h-0 overflow-y-auto px-5"
					/>
				</div>
			</div>
		</div>

		<!-- Actions (sticky so they're reachable without scrolling to the bottom) -->
		<div
			class="sticky bottom-0 z-10 -mx-5 flex items-center justify-end gap-2 border-t border-slate-200 bg-slate-100/95 px-5 py-3 backdrop-blur dark:border-surface-800 dark:bg-surface-900/95"
		>
			<Button label="Save draft" severity="secondary" icon="pi pi-save" :loading="savingDraft" :disabled="submitting" @click="saveDraft" />
			<Button label="Create ADR" icon="pi pi-check" icon-pos="right" :loading="submitting" :disabled="!form.id" @click="submitAdr" />
		</div>
	</div>

	<!-- Unsaved-changes warning shown when navigating away with unsaved progress -->
	<Dialog v-model:visible="showLeaveDialog" header="Unsaved changes" :modal="true" :closable="false" :style="{ width: '460px' }">
		<p class="text-slate-600 dark:text-surface-300">
			Leaving this page will discard your unsaved progress. Would you like to save it as a draft first?
		</p>
		<template #footer>
			<div class="flex w-full items-center justify-between">
				<Button label="Leave without saving" severity="danger" text @click="discardAndLeave" />
				<div class="flex gap-2">
					<Button label="Cancel" severity="secondary" text @click="cancelLeave" />
					<Button label="Save as draft" icon="pi pi-save" :loading="savingDraft" @click="saveDraftAndLeave" />
				</div>
			</div>
		</template>
	</Dialog>

	<ReviewFindingsDialog
		v-model:visible="showReviewDialog"
		:findings="reviewFindings"
		:loading="checking"
		:error="hasReviewError"
		@submit-anyway="submitAnyway"
	/>
</template>

<script setup lang="ts">
import ReviewFindingsDialog from "@/components/dialog/ReviewFindingsDialog.vue";
import FormField from "@/components/form/FormField.vue";
import { useCreateAdr } from "@/composables/useCreateAdr";
import { Icon } from '@iconify/vue';
import { MdEditor, MdPreview } from "md-editor-v3";
import { Button, Chip, Dialog, InputText, MultiSelect, Select, SelectButton, Tag, Textarea } from "primevue";

const {
	form,
	alternativeInput,
	submitting,
	savingDraft,
	validationErrors,
	statusSeverity,
	markdown,
	isDark,
	statusOptions,
	formatOptions,
	mdToolbars,
	relatedAdrChoices,
	loadingRelatedAdrs,
	addAlternative,
	addCustomSection,
	removeCustomSection,
	saveDraft,
	submitAdr,
	showLeaveDialog,
	cancelLeave,
	discardAndLeave,
	saveDraftAndLeave,
	reviewFindings,
	showReviewDialog,
	checking,
	hasReviewError,
	submitAnyway,
} = useCreateAdr();
</script>
