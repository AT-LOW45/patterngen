import ragApi from "../config/api-config";

const boilerplateService = {
	generateBoilerplate: (query: string, language: string, selection_context: string) => ragApi.post("/generate-boilerplate", { query, language }),
} as const;

export default boilerplateService;
