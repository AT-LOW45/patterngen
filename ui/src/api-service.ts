import axios, { CreateAxiosDefaults } from "axios";

const axiosConfig: CreateAxiosDefaults = {
	baseURL: import.meta.env.VITE_API_ENDPOINT,
};

const api = axios.create(axiosConfig);

export const knowledgeBaseService = {
	getAllRecords: () => api.get("/knowledge-base"),
} as const;
