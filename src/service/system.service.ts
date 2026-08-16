import ragApi from "../config/api-config";
import * as vscode from "vscode";

const systemService = {
	checkLiveliness: () => ragApi.post("/health"),
};

type BackendStatus = "checking" | "up" | "down";
let status: BackendStatus = "checking";
let probe: Promise<void> | null = null;

export const startLivelinessCheck = () => {
	console.log(`[patterngen] liveliness check started at ${new Date().toISOString()}`);
	status = "checking";
	probe = systemService
		.checkLiveliness()
		.then(() => {
			status = "up";
			console.log(`[patterngen] liveliness check resolved UP at ${new Date().toISOString()}`);
		})
		.catch(() => {
			status = "down";
			console.log(`[patterngen] liveliness check resolved DOWN at ${new Date().toISOString()}`);
		});
};

const ensureBackendReady = async () => {
	// still in flight — tell the user, wait for it to settle, then re-check below
	if (status === "checking") {
		vscode.window.showInformationMessage("Patterngen is still checking the backend - one moment...");
		await probe;
	}
	if (status === "down") {
		vscode.window.showWarningMessage("Patterngen backend is not reachable now. Please check the configuration");
		return false;
	}
	return true;
};

export const withBackendReady = (run: () => unknown) => {
	return async () => {
		if (!(await ensureBackendReady())) {
			return;
		}
		return await run();
	};
};

export default systemService;
