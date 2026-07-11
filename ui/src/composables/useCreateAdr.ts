import { knowledgeBaseService, draftService } from "@/api-service";
import { adrSchema } from "@/schemas/adrSchema";
import useZodValidation from "@/composables/useZodValidation";
import ROUTES from "@/router/routes";
import type { ToolbarNames } from "md-editor-v3";
import { useToast } from "primevue";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

export type SectionFormat = "plain" | "rich";

export interface CustomSection {
	heading: string;
	body: string;
	format: SectionFormat;
}

export interface AdrForm {
	id: string;
	status: string;
	title: string;
	scope: string;
	context: string;
	decision: string;
	alternatives: string[];
	relatedAdrs: string;
	implementation: string;
	customSections: CustomSection[];
	positiveConsequences: string;
	negativeConsequences: string;
	notes: string;
}

const statusOptions: string[] = ["Proposed", "Accepted", "Deprecated", "Superseded"];

const formatOptions: { label: string; value: SectionFormat }[] = [
	{ label: "Plain text", value: "plain" },
	{ label: "Rich text", value: "rich" },
];

const statusSeverityMap: Record<string, "success" | "info" | "warn" | "secondary"> = {
	Accepted: "success",
	Proposed: "info",
	Deprecated: "warn",
	Superseded: "secondary",
};

// Focused toolbar for the code-capable sections (Decision, Implementation, Notes, rich
// custom sections). The page has its own preview pane, so the editor's is turned off.
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

function emptyForm(): AdrForm {
	return {
		id: "",
		status: "",
		title: "",
		scope: "",
		context: "",
		decision: "",
		alternatives: [],
		relatedAdrs: "",
		implementation: "",
		customSections: [],
		positiveConsequences: "",
		negativeConsequences: "",
		notes: "",
	};
}

/**
 * All state and behaviour for the Create ADR page. The component is left as pure
 * template + this hook call.
 */
export function useCreateAdr() {
	const router = useRouter();
	const route = useRoute();
	const toast = useToast();

	const form = ref<AdrForm>(emptyForm());
	const alternativeInput = ref<string>("");
	const submitting = ref<boolean>(false);
	const savingDraft = ref<boolean>(false);
	// The draft this session maps to. Null until the first save; set when resuming an existing draft.
	const draftId = ref<string | null>(null);

	const { validate, simpleValidate, validationErrors } = useZodValidation(adrSchema, {
		errorToast: { summary: "Missing required fields", detail: "Please complete the highlighted fields." },
	});

	const statusSeverity = computed(() => statusSeverityMap[form.value.status] ?? "secondary");

	const addAlternative = (): void => {
		const val = alternativeInput.value.trim();
		if (val && !form.value.alternatives.includes(val)) {
			form.value.alternatives.push(val);
		}
		alternativeInput.value = "";
	};

	const addCustomSection = (): void => {
		form.value.customSections.push({ heading: "", body: "", format: "plain" });
	};

	const removeCustomSection = (index: number): void => {
		form.value.customSections.splice(index, 1);
	};

	// Assemble the form into an ADR markdown document, mirroring the docs/adr/ format.
	// Core sections always render (with a muted placeholder when empty) so the document
	// structure is visible; optional sections appear only once filled in.
	const markdown = computed<string>(() => {
		const f = form.value;
		const lines: string[] = [];

		const title = f.title || "Untitled ADR";
		lines.push(f.id ? `# ${f.id}: ${title}` : `# ${title}`, "");
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

		for (const s of f.customSections) {
			if (!s.heading.trim() && !s.body.trim()) continue;
			lines.push("", `## ${s.heading.trim() || "Untitled Section"}`, s.body.trim());
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

	// Track the app's dark mode (PrimeVue toggles a `.app-dark` class) so editors/preview match.
	const hasDarkClass = (): boolean =>
		document.documentElement.classList.contains("app-dark") || document.body.classList.contains("app-dark");

	const isDark = ref<boolean>(hasDarkClass());
	const observer = new MutationObserver(() => {
		isDark.value = hasDarkClass();
	});
	observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
	observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });
	onBeforeUnmount(() => observer.disconnect());

	// Resume an existing draft when ?draft=<id> is present; otherwise start fresh with
	// a backend-assigned next id.
	onMounted(async () => {
		const resumeId = typeof route.query.draft === "string" ? route.query.draft : null;
		if (resumeId) {
			try {
				const { data } = await draftService.getDraft(resumeId);
				form.value = { ...emptyForm(), ...data.draft };
				draftId.value = resumeId;
				return;
			} catch (error) {
				console.error("Failed to load draft:", error);
				toast.add({ severity: "error", summary: "Couldn't load draft", detail: "Starting a new ADR instead.", life: 4000 });
				// fall through to a fresh id so the page stays usable
			}
		}

		try {
			const { data } = await knowledgeBaseService.getNextId();
			form.value.id = data.id;
		} catch (error) {
			console.error("Failed to fetch next ADR id:", error);
			toast.add({ severity: "error", summary: "Couldn't assign an ADR id", detail: "Reload to try again.", life: 4000 });
		}
	});

	// After the first failed submit, re-validate live so errors clear as fields are fixed.
	watch(form, () => simpleValidate(form.value), { deep: true });

	const saveDraft = async (): Promise<void> => {
		// New drafts get a stable id on first save (independent of the ADR id);
		// saving again overwrites the same draft.
		if (!draftId.value) {
			draftId.value = crypto.randomUUID();
		}
		savingDraft.value = true;
		try {
			await draftService.saveDraft(draftId.value, form.value);
			toast.add({ severity: "success", summary: "Draft saved", life: 2000 });
		} catch (error) {
			console.error("Failed to save draft:", error);
			toast.add({ severity: "error", summary: "Failed to save draft", life: 3000 });
		} finally {
			savingDraft.value = false;
		}
	};

	const submitAdr = async (): Promise<void> => {
		if (!validate(form.value)) return;

		submitting.value = true;
		try {
			const { data } = await knowledgeBaseService.createDocument(markdown.value);

			// Publishing consumes the draft — remove it so it no longer shows in the list.
			// Best-effort: the ADR is already created, so a cleanup failure shouldn't fail the publish.
			if (draftId.value) {
				try {
					await draftService.deleteDraft(draftId.value);
				} catch (error) {
					console.error("Failed to remove draft after publish:", error);
				}
				draftId.value = null;
			}

			toast.add({ severity: "success", summary: "ADR created", detail: data.source, life: 3000 });
			router.push(ROUTES.knowledgeBase);
		} catch (error) {
			console.error("Failed to create ADR:", error);
			toast.add({ severity: "error", summary: "Failed to create ADR", life: 3000 });
		} finally {
			submitting.value = false;
		}
	};

	return {
		// state
		form,
		alternativeInput,
		submitting,
		savingDraft,
		validationErrors,
		// derived
		statusSeverity,
		markdown,
		isDark,
		// static UI config
		statusOptions,
		formatOptions,
		mdToolbars,
		// actions
		addAlternative,
		addCustomSection,
		removeCustomSection,
		saveDraft,
		submitAdr,
	};
}
