// src/commands/generate-boilerplate.ts
import * as vscode from "vscode";

export default async function generateBoilerplate(context: vscode.ExtensionContext) {
	const input = await vscode.window.showInputBox({
		prompt: "What do you want to generate?",
		placeHolder: "e.g. express route handler for user authentication",
	});

	if (!input || input.trim().length === 0) {
		return;
	}

	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		vscode.window.showWarningMessage("No active editor found");
		return;
	}

	// hardcoded for now, replace with RAG call later
	const generated = `// generated for: ${input}\nconst example = () => {};`;

	await editor.edit((editBuilder) => {
		editBuilder.insert(editor.selection.active, generated);
	});
}
