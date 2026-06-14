import * as vscode from "vscode";

export default function openKnowledgeBase() {
	const config = vscode.workspace.getConfiguration("patterngen");
	const ragBaseUrl = config.get<string>("ragEndpoint");

	if (!ragBaseUrl) {
		vscode.window.showErrorMessage("Rag endpoint not configured.");
		return;
	}

	const url = new URL(ragBaseUrl);

	vscode.env.openExternal(
		vscode.Uri.from({
			scheme: url.protocol.replace(":", ""),
			authority: url.host,
			path: url.pathname,
		}),
	);
}
