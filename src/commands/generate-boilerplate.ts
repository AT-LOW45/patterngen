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

interface BoilerplateEdit {
	search: string;
	replace: string;
}

// Apply the model's edit. Prefer its `search` anchor — locate that exact text in the
// file and replace it — then fall back to the user's selection, then the cursor.
async function applyBoilerplateEdit(
	editor: vscode.TextEditor,
	selection: vscode.Selection,
	edit: BoilerplateEdit,
): Promise<boolean> {
	const document = editor.document;
	let target: vscode.Range | undefined;

	if (edit.search) {
		const offset = document.getText().indexOf(edit.search);
		if (offset !== -1) {
			target = new vscode.Range(
				document.positionAt(offset),
				document.positionAt(offset + edit.search.length),
			);
		} else {
			vscode.window.showWarningMessage(
				"Patterngen: couldn't locate the code to change — applying at the selection/cursor instead.",
			);
		}
	}

	return editor.edit((editBuilder) => {
		if (target) {
			editBuilder.replace(target, edit.replace);
		} else if (!selection.isEmpty) {
			editBuilder.replace(selection, edit.replace);
		} else {
			editBuilder.insert(selection.active, edit.replace);
		}
	});
}

export default async function generateBoilerplate(context: vscode.ExtensionContext) {
	try {
		// capture editor + selection first, before any dialogs shift focus
		const editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showWarningMessage("No active editor found");
			return;
		}
		const selection = editor.selection;

		const input = await vscode.window.showInputBox({
			prompt: "What do you want to generate?",
			placeHolder: "e.g. express route handler for user authentication",
		});

		if (!input || input.trim().length === 0) {
			return;
		}

		const edit = await vscode.window.withProgress(
			{
				location: vscode.ProgressLocation.Notification,
				title: "Patterngen: generating boilerplate...",
				cancellable: false,
			},
			async () => {
				const language = editor.document.languageId;
				const selectedText = editor.document.getText(selection);
				const fileContent = editor.document.getText();
				const response = await boilerplateService.generateBoilerplate(
					input,
					language,
					selectedText,
					fileContent,
				);
				return response.data as BoilerplateEdit;
			},
		);

		// locate where the edit goes from its `search` anchor (falls back to selection/cursor)
		const applied = await applyBoilerplateEdit(editor, selection, edit);

		// generated code omits imports by design — let the editor add the correct ones
		if (applied) {
			await applyAddMissingImports(editor.document);
		}
	} catch (error) {
		console.error("generateBoilerplate error:", error); // full error in Debug Console
		vscode.window.showErrorMessage(`Error: ${error instanceof Error ? error.message : String(error)}`);
	}
}
