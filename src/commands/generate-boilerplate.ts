// src/commands/generate-boilerplate.ts
import boilerplateService from "../service/boilerplate.service";
import codeActions from "../constants/code-actions";
import * as vscode from "vscode";

async function requestCodeActions(
	document: vscode.TextDocument,
	range: vscode.Range,
	kind?: string,
): Promise<vscode.CodeAction[]> {
	return (
		(await vscode.commands.executeCommand<vscode.CodeAction[]>(
			"vscode.executeCodeActionProvider",
			document.uri,
			range,
			kind,
			// itemResolveCount: force the provider to resolve each action's edit.
			// Without it, action.edit comes back undefined and there's nothing to apply.
			50,
		)) ?? []
	);
}

// The generated code deliberately omits imports, so ask the language server to add
// them. TS/JS expose a dedicated `source.addMissingImports` action; Vue/Volar only
// surface a titled action, so we fall back to that. The server needs a beat to
// analyse the freshly inserted code, hence the short retry loop.
async function applyAddMissingImports(document: vscode.TextDocument): Promise<boolean> {
	const fullRange = new vscode.Range(
		document.positionAt(0),
		document.positionAt(document.getText().length),
	);

	// Retry until we find an action that actually carries an edit/command — the
	// language server needs a beat to analyse the inserted code and offer it.
	for (let attempt = 0; attempt < 6; attempt++) {
		const bySource = await requestCodeActions(document, fullRange, codeActions.addMissingImports);
		const candidates = bySource.length > 0 ? bySource : await requestCodeActions(document, fullRange);
		const action = candidates.find(
			(a) => a.kind?.value === codeActions.addMissingImports || /add all missing imports/i.test(a.title),
		);

		if (action?.edit) {
			await vscode.workspace.applyEdit(action.edit);
			return true;
		}
		if (action?.command) {
			await vscode.commands.executeCommand(action.command.command, ...(action.command.arguments ?? []));
			return true;
		}

		await new Promise((resolve) => setTimeout(resolve, 400));
	}

	return false;
}

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
				const selectedText = editor.document.getText(editor.selection);
				const response = await boilerplateService.generateBoilerplate(input, language, selectedText);
				return response.data.code;
			},
		);

		const inserted = await editor.edit((editBuilder) => {
			editBuilder.insert(editor.selection.active, code);
		});

		// generated code omits imports by design — let the editor add the correct ones
		if (inserted) {
			await applyAddMissingImports(editor.document);
		}
	} catch (error) {
		console.error("generateBoilerplate error:", error); // full error in Debug Console
		vscode.window.showErrorMessage(`Error: ${error instanceof Error ? error.message : String(error)}`);
	}
}
