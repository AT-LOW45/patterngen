import axios, { CreateAxiosDefaults } from "axios";

const axiosConfig: CreateAxiosDefaults = {
	baseURL: import.meta.env.VITE_API_ENDPOINT,
};

const api = axios.create(axiosConfig);

export const knowledgeBaseService = {
	getAllRecords: () => api.get("/knowledge-base"),
	getRecord: (source: string) => api.get(`knowledge-base/${source}`),
	deleteRecord: (source: string) => api.delete(`/knowledge-base/${source}`),

	// POST /index-document?source=<source> with multipart form data containing file
	indexDocument: (source: string, file: File) => {
		const form = new FormData();
		form.append("file", file);
		return api.post(`/index-document?source=${encodeURIComponent(source)}`, form, {
			headers: { "Content-Type": "multipart/form-data" },
		});
	},
} as const;
