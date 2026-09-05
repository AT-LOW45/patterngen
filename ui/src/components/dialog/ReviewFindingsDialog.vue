<template>
	<Dialog
		v-model:visible="visible"
		modal
		dismissable-mask
		:draggable="false"
		style="z-index: 100000 !important"
		:style="{ width: '540px' }"
	>
		<template #header>
			<div class="flex items-center gap-3">
				<span class="flex h-11 w-11 items-center justify-center rounded-full" :class="badge.wrap">
					<Icon :icon="badge.icon" class="text-2xl" :class="[badge.fg, { 'animate-spin': loading }]" />
				</span>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-semibold text-slate-700 dark:text-surface-100">Quality review</span>
					<span class="text-sm text-slate-500 dark:text-surface-400">{{ summary }}</span>
				</div>
			</div>
		</template>

		<!-- Loading state -->
		<div v-if="loading" class="flex flex-col items-center gap-3 py-12 text-center">
			<Icon icon="mdi:loading" class="animate-spin text-4xl text-slate-400 dark:text-surface-400" />
			<p class="text-lg font-medium text-slate-700 dark:text-surface-200">Reviewing your ADR…</p>
			<p class="text-sm text-slate-500 dark:text-surface-400">Checking structure and content.</p>
		</div>

		<!-- Review service error state -->
		<div v-else-if="error" class="flex flex-col items-center gap-3 py-10 text-center">
			<Icon icon="mdi:cloud-off-outline" class="text-5xl text-slate-400 dark:text-surface-400" />
			<p class="text-lg font-medium text-slate-700 dark:text-surface-200">Review service unavailable</p>
			<p class="text-sm text-slate-500 dark:text-surface-400">
				We couldn't check this ADR right now. You can save it anyway and review later.
			</p>
		</div>

		<!-- Empty / all-clear state -->
		<div v-else-if="!findings.length" class="flex flex-col items-center gap-1 py-10 text-center">
			<Icon icon="lets-icons:check-fill" class="text-emerald-500 text-[4.5rem]" />
			<!-- <i class="pi pi-check-circle text-emerald-500" /> -->
			<p class="text-lg font-medium text-slate-700 dark:text-surface-200">No issues found</p>
			<p class="text-slate-500 dark:text-surface-400">This ADR looks good to submit.</p>
		</div>

		<!-- Findings list -->
		<ul v-else class="flex max-h-[55vh] flex-col gap-3 overflow-y-auto pr-1">
			<li
				v-for="(finding, i) in findings"
				:key="i"
				class="flex items-start gap-3 rounded-xl border border-l-4 border-slate-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800/40"
				:class="[
					config(finding.severity).spine,
					finding.navigable ? 'cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-surface-800' : '',
				]"
				@click="finding.navigable && onNavigate(finding)"
			>
				<Icon :icon="config(finding.severity).icon" class="mt-0.5 shrink-0 text-lg" :class="config(finding.severity).fg" />
				<div class="flex min-w-0 flex-1 flex-col gap-1">
					<span class="text-xs font-semibold uppercase tracking-wide" :class="config(finding.severity).fg">
						{{ config(finding.severity).label }} · {{ finding.section }}
					</span>
					<p class="text-base leading-relaxed text-slate-700 dark:text-surface-200">{{ finding.message }}</p>
				</div>
				<Icon
					v-if="finding.navigable"
					icon="mdi:arrow-right"
					class="shrink-0 self-center text-lg text-slate-400 dark:text-surface-400"
				/>
			</li>
		</ul>

		<template #footer>
			<Button :label="secondaryLabel" severity="secondary" text :disabled="loading" @click="visible = false" />
			<Button :label="primaryLabel" :disabled="loading" @click="onSubmitAnyway">
				<template #icon>
					<Icon icon="mdi:check" class="mr-2 text-base" />
				</template>
			</Button>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import type { ReviewFinding } from "@/api-service";
import { Button, Dialog } from "primevue";
import { computed } from "vue";
import { Icon } from "@iconify/vue";

// `navigable` is added by the create page for findings whose section maps to a form
// field; the edit page passes plain findings (undefined → not clickable).
type DisplayFinding = ReviewFinding & { navigable?: boolean };

const props = defineProps<{ findings: DisplayFinding[]; loading?: boolean; error?: boolean }>();
const visible = defineModel<boolean>("visible");

const emit = defineEmits<{ (e: "submit-anyway"): void; (e: "navigate", finding: DisplayFinding): void }>();

const onNavigate = (finding: DisplayFinding): void => {
	emit("navigate", finding);
};

const SEVERITY = {
	error: {
		label: "Error",
		icon: "mdi:close-circle",
		fg: "text-rose-600 dark:text-rose-400",
		spine: "border-l-rose-500",
	},
	warning: {
		label: "Warning",
		icon: "mdi:alert",
		fg: "text-amber-600 dark:text-amber-400",
		spine: "border-l-amber-500",
	},
} as const;

const config = (severity: ReviewFinding["severity"]) => SEVERITY[severity];

const errorCount = computed(() => props.findings.filter((f) => f.severity === "error").length);
const warningCount = computed(() => props.findings.filter((f) => f.severity === "warning").length);

const summary = computed<string>(() => {
	if (props.loading) {
		return "Reviewing your ADR…";
	}
	if (props.error) {
		return "Review unavailable";
	}
	if (!props.findings.length) {
		return "No issues found";
	}
	const parts: string[] = [];
	if (errorCount.value) {
		parts.push(`${errorCount.value} error${errorCount.value > 1 ? "s" : ""}`);
	}
	if (warningCount.value) {
		parts.push(`${warningCount.value} warning${warningCount.value > 1 ? "s" : ""}`);
	}
	return parts.join(" · ");
});

// Header badge reflects the worst severity present.
const badge = computed(() => {
	if (props.loading) {
		return { wrap: "bg-slate-100 dark:bg-surface-800", fg: "text-slate-400 dark:text-surface-400", icon: "mdi:loading" };
	}
	if (props.error) {
		return { wrap: "bg-slate-100 dark:bg-surface-800", fg: "text-slate-400 dark:text-surface-400", icon: "mdi:cloud-off-outline" };
	}
	if (!props.findings.length) {
		return { wrap: "bg-emerald-50 dark:bg-emerald-950", fg: "text-emerald-600 dark:text-emerald-400", icon: "mdi:check-circle" };
	}
	if (errorCount.value) {
		return { wrap: "bg-rose-50 dark:bg-rose-950", fg: "text-rose-600 dark:text-rose-400", icon: "mdi:close-circle" };
	}
	return { wrap: "bg-amber-50 dark:bg-amber-950", fg: "text-amber-600 dark:text-amber-400", icon: "mdi:alert" };
});

const secondaryLabel = computed<string>(() => (props.error ? "Cancel" : props.findings.length ? "Fix issues" : "Close"));
const primaryLabel = computed<string>(() => (props.error ? "Save anyway" : props.findings.length ? "Submit anyway" : "Submit"));

const onSubmitAnyway = (): void => {
	emit("submit-anyway");
	visible.value = false;
};
</script>
