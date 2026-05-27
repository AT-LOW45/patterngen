// src/commands/generate-boilerplate.ts
import boilerplateService from "../service/boilerplate.service";
import * as vscode from "vscode";

export default async function generateBoilerplate(context: vscode.ExtensionContext) {
	try {
		// capture editor first, before any dialogs
		const editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showWarningMessage("No active editor found");
			return;
		}

		const input = await vscode.window.showInputBox({
			prompt: "What do you want to generate?",
			placeHolder: "e.g. express route handler for user authentication",
		});

		if (!input || input.trim().length === 0) {
			return;
		}

		const code = await vscode.window.withProgress(
			{
				location: vscode.ProgressLocation.Notification,
				title: "Patterngen: generating boilerplate...",
				cancellable: false,
			},
			async () => {
				const language = editor.document.languageId;
				const response = await boilerplateService.generateBoilerplate(input, language);
				return response.data.code;
			},
		);

		await editor.edit((editBuilder) => {
			editBuilder.insert(editor.selection.active, code);
		});
	} catch (error) {
		console.error("generateBoilerplate error:", error); // full error in Debug Console
		vscode.window.showErrorMessage(`Error: ${error instanceof Error ? error.message : String(error)}`);
	}
}
