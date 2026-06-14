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

	// POST /index-document?source=<source> with multipart form data containing file
	indexDocument: (source: string, file: File) => {
		const form = new FormData();
		form.append("file", file);
		return api.post(`/knowledge-base/index-document?source=${encodeURIComponent(source)}`, form, {
			headers: { "Content-Type": "multipart/form-data" },
		});
	},

	reindexRecord: (source: string, content: string) => {
		const blob = new Blob([content], { type: "text/markdown" });
		const file = new File([blob], source, { type: "text/markdown" });
		const form = new FormData();
		form.append("file", file);
		return api.post(`/knowledge-base/index-document?source=${encodeURIComponent(source)}`, form, {
			headers: { "Content-Type": "multipart/form-data" },
		});
	},
} as const;
