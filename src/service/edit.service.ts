import * as vscode from "vscode";

export interface BoilerplateEdit {
	search: string;
	replace: string;
}

export interface ApplyEditsResult {
	applied: number;
	missed: number;
}

// Apply a set of search/replace edits to the editor's document. Every `search`
// anchor is located against the ORIGINAL document text and all edits are applied
// together in a single edit() call, so earlier replacements don't shift the offsets
// of later ones. An edit with an empty `search` is inserted at the selection/cursor
// (new code with no anchor). Returns how many edits were applied vs. not located.
//
// Kept independent of any one command so the input-box flow and a future chat/coding
// session can share the same edit-application engine.
export async function applyBoilerplateEdits(
	editor: vscode.TextEditor,
	selection: vscode.Selection,
	edits: BoilerplateEdit[],
): Promise<ApplyEditsResult> {
	const document = editor.document;
	const originalText = document.getText();

	type Op = { range?: vscode.Range; insertAt?: vscode.Position; replace: string };
	const ops: Op[] = [];
	let missed = 0;

	for (const edit of edits) {
		if (!edit.search) {
			// no anchor — insert at the selection/cursor (typically new code in an empty file)
			ops.push({ insertAt: selection.active, replace: edit.replace });
			continue;
		}

		const offset = originalText.indexOf(edit.search);
		if (offset === -1) {
			missed++;
			continue;
		}

		ops.push({
			range: new vscode.Range(
				document.positionAt(offset),
				document.positionAt(offset + edit.search.length),
			),
			replace: edit.replace,
		});
	}

	if (ops.length === 0) {
		return { applied: 0, missed };
	}

	const ok = await editor.edit((editBuilder) => {
		for (const op of ops) {
			if (op.range) {
				editBuilder.replace(op.range, op.replace);
			} else if (op.insertAt) {
				editBuilder.insert(op.insertAt, op.replace);
			}
		}
	});

	return { applied: ok ? ops.length : 0, missed };
}
