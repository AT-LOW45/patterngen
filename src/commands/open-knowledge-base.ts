import * as vscode from "vscode";

export default function openKnowledgeBase() {
	const config = vscode.workspace.getConfiguration("patterngen");
	const ragBaseUrl = config.get<string>("ragEndpoint");

	if (!ragBaseUrl) {
		vscode.window.showErrorMessage("Rag endpoint not configured.");
		return;
	}

	// Open the configured endpoint as-is. Decomposing it into scheme/authority/path
	// and rebuilding via Uri.from was dropping the :8000 port, so it opened
	// http://127.0.0.1 (port 80) and failed with a network error.
	vscode.env.openExternal(vscode.Uri.parse(ragBaseUrl));
}
