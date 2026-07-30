import type { AdrForm } from "@/composables/useCreateAdr";
import axios, { CreateAxiosDefaults } from "axios";

const axiosConfig: CreateAxiosDefaults = {
	baseURL: import.meta.env.VITE_API_ENDPOINT,
};

const api = axios.create(axiosConfig);

export const knowledgeBaseService = {
	getAllRecords: () => api.get("/knowledge-base"),
	getRecord: (source: string) => api.get(`knowledge-base/${source}`),
	getRawRecord: (source: string) => api.get(`/knowledge-base/${encodeURIComponent(source)}/raw`),
	deleteRecord: (source: string) => api.delete(`/knowledge-base/${source}`),

	// Create a record from an uploaded file. No `source` is sent — the backend derives it
	// (H1 if the document has one, else the filename plus a fresh ADR id) and 409s rather
	// than overwriting an existing record. Returns the key it settled on.
	indexDocument: (file: File) => {
		const form = new FormData();
		form.append("file", file);
		return api.post<{ source: string }>("/knowledge-base/index-document", form, {
			headers: { "Content-Type": "multipart/form-data" },
		});
	},

	// Next sequential ADR id to pre-fill the create form (e.g. "ADR-004").
	getNextId: () => api.get<{ id: string }>("/knowledge-base/next-id"),

	// Create a new record from markdown. The backend derives the source key from
	// the document's H1 title and returns it, then writes to blob + indexes.
	createDocument: (content: string) => api.post<{ source: string }>("/knowledge-base", { content }),

	// Save an edit to a known record. The backend treats the document's H1 as
	// authoritative, so changing the title renames the record — the returned `source` is
	// the key it now lives under and may differ from the one passed in.
	saveMarkdown: (source: string, content: string) => {
		const blob = new Blob([content], { type: "text/markdown" });
		const file = new File([blob], source, { type: "text/markdown" });
		const form = new FormData();
		form.append("file", file);
		return api.post<{ source: string }>(`/knowledge-base/index-document?source=${encodeURIComponent(source)}`, form, {
			headers: { "Content-Type": "multipart/form-data" },
		});
	},
} as const;

// Drafts — in-progress ADRs stored as the form object (JSON), never indexed.
// Kept separate from knowledgeBaseService, mirroring the backend's dedicated draft service.
export const draftService = {
	listDrafts: () => api.get<{ drafts: { id: string; draft: AdrForm }[] }>("/knowledge-base/drafts"),
	getDraft: (id: string) => api.get<{ id: string; draft: AdrForm }>(`/knowledge-base/drafts/${encodeURIComponent(id)}`),
	saveDraft: (id: string, draft: AdrForm) => api.put(`/knowledge-base/drafts/${encodeURIComponent(id)}`, draft),
	deleteDraft: (id: string) => api.delete(`/knowledge-base/drafts/${encodeURIComponent(id)}`),
} as const;

export type ReviewFinding = { severity: "warning" | "error"; section: string; message: string };

export const reviewService = {
	reviewDocument: (content: string) => api.post<{ findings: ReviewFinding[] }>("/knowledge-base/adr-review", { content }),
};
