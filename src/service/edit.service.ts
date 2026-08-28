import * as vscode from "vscode";

export interface CodeEdit {
	search: string;
	replace: string;
}

export interface ApplyEditsResult {
	applied: number;
	missed: number;
}

// Locate an edit's `search` text in the file. Tries an exact match first, then a
// whitespace-tolerant match — runs of whitespace become flexible, so differences in
// indentation, spacing, or line breaks between the model's copy and the real file
// don't cause a miss. Returns the character range to replace, or null if not found.
function locateEdit(text: string, search: string): { start: number; end: number } | null {
	const exact = text.indexOf(search);
	if (exact !== -1) {
		return { start: exact, end: exact + search.length };
	}

	const trimmed = search.trim();
	if (trimmed.length === 0) {
		return null;
	}

	// escape regex specials, then relax the differences that are semantically
	// insignificant in most languages: any run of whitespace matches any other run,
	// and semicolons are optional (JS/TS, Ruby, Kotlin, Swift, Go, Lua, Scala).
	const pattern = trimmed
		.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
		.replace(/\s+/g, "\\s+")
		.replace(/;/g, ";?");
	const match = new RegExp(pattern).exec(text);
	if (match) {
		return { start: match.index, end: match.index + match[0].length };
	}

	return null;
}

// Apply a set of search/replace edits to the editor's document. Every `search`
// anchor is located against the ORIGINAL document text and all edits are applied
// together in a single edit() call, so earlier replacements don't shift the offsets
// of later ones. An edit with an empty `search` is inserted at the selection/cursor
// (new code with no anchor). Returns how many edits were applied vs. not located.
//
// Kept independent of any one command so the input-box flow and a future chat/coding
// session can share the same edit-application engine.
export async function applyCodeEdits(
	editor: vscode.TextEditor,
	selection: vscode.Selection,
	edits: CodeEdit[],
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

		const located = locateEdit(originalText, edit.search);
		if (!located) {
			missed++;
			continue;
		}

		ops.push({
			range: new vscode.Range(
				document.positionAt(located.start),
				document.positionAt(located.end),
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
