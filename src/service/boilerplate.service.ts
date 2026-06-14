import ragApi from "../config/api-config";

const boilerplateService = {
	generateBoilerplate: (query: string, language: string, selection_context: string) =>
		ragApi.post("/boilerplate/generate-boilerplate", { query, language, selection_context }),
} as const;

export default boilerplateService;
