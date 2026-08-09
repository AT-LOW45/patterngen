// src/commands/symbol-spike.ts
//
// THROWAWAY SPIKE — delete once we've learned what the LSP gives us.
//
// Purpose: prove out "Need 1" symbol selection. Given a set of candidate
// identifiers (the union we'd get from: retrieved ADRs + current-file refs +
// prompt), ask VS Code's language server what it knows about each via
// `vscode.executeWorkspaceSymbolProvider`, and print a resolved table:
//     name -> kind, defining file, best-effort default|named export
//
// HOW TO RUN:
//   1. Press F5 to launch the Extension Development Host.
//   2. In that window, open the TARGET repo as the workspace folder
//      (e.g. customer-frontend) so its TS/Vue language server is active.
//   3. Command Palette -> "Patterngen: Symbol Spike (debug)".
//   4. Read the "Patterngen Symbol Spike" output channel.
//
// The default candidate list is the News.vue union from our test.
import * as vscode from "vscode";

// The union we'd normally compute from ADRs + current file + prompt.
// Hardcoded here so the spike is one keypress; editable at runtime.
const DEFAULT_CANDIDATES = ["useAsyncCallWithFeedback", "parentAPI", "fileAPI", "handleApiError", "useToast"];

// A few SymbolKinds we actually care about; everything else prints its number.
const KIND_LABEL: Partial<Record<vscode.SymbolKind, string>> = {
	[vscode.SymbolKind.Function]: "function",
	[vscode.SymbolKind.Variable]: "variable",
	[vscode.SymbolKind.Constant]: "constant",
	[vscode.SymbolKind.Class]: "class",
	[vscode.SymbolKind.Method]: "method",
	[vscode.SymbolKind.Object]: "object",
	[vscode.SymbolKind.Interface]: "interface",
	[vscode.SymbolKind.Module]: "module",
	[vscode.SymbolKind.Property]: "property",
};

function kindLabel(kind: vscode.SymbolKind): string {
	return KIND_LABEL[kind] ?? `kind#${kind}`;
}

// Best-effort export-style guess by reading the defining file. This is exactly
// the fact the model got wrong (default vs named), so we want to see whether we
// can derive it cheaply here — or whether we should defer it to add-missing-imports.
// Line-based and bounded on purpose: whole-file regexes with nested `[^}]*`
// can hit catastrophic backtracking on long/minified lines and hang the host.
function guessExportStyle(fileText: string, name: string): "default" | "named" | "unknown" {
	const n = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // escape for regex
	const nameWord = new RegExp(`\\b${n}\\b`);
	const namedDecl = new RegExp(`^export\\s+(const|let|var|function|class|async\\s+function)\\s+${n}\\b`);

	// scan at most the first ~4000 lines, skip pathologically long lines
	const lines = fileText.split("\n", 4000);
	let sawNamed = false;
	for (const raw of lines) {
		if (raw.length > 500) {
			continue; // minified / generated — not worth the backtracking risk
		}
		const line = raw.trim();
		if (!line.startsWith("export")) {
			continue;
		}
		if (line.includes("default") && (nameWord.test(line) || line.includes("as default"))) {
			return "default"; // `export default <name>` or `{ <name> as default }`
		}
		if (namedDecl.test(line) || (line.startsWith("export {") && nameWord.test(line))) {
			sawNamed = true;
		}
	}
	return sawNamed ? "named" : "unknown";
}

function relPath(uri: vscode.Uri): string {
	return vscode.workspace.asRelativePath(uri, false);
}

export default async function symbolSpike(_context: vscode.ExtensionContext) {
	const out = vscode.window.createOutputChannel("Patterngen Symbol Spike");
	out.show(true);

	const folders = vscode.workspace.workspaceFolders;
	if (!folders || folders.length === 0) {
		out.appendLine("No workspace folder open. Open the TARGET repo (e.g. customer-frontend) and re-run.");
		return;
	}
	out.appendLine(`Workspace: ${folders.map((f) => f.uri.fsPath).join(", ")}`);

	const raw = await vscode.window.showInputBox({
		prompt: "Candidate identifiers to resolve (comma-separated)",
		value: DEFAULT_CANDIDATES.join(", "),
	});
	if (raw === undefined) {
		return; // cancelled
	}
	const candidates = raw
		.split(",")
		.map((s) => s.trim())
		.filter(Boolean);

	out.appendLine(`\nResolving ${candidates.length} candidate(s) via executeWorkspaceSymbolProvider...\n`);

	// cache file text so we don't re-open the same defining file per candidate
	const fileTextCache = new Map<string, string>();

	for (const name of candidates) {
		const matches =
			(await vscode.commands.executeCommand<vscode.SymbolInformation[]>(
				"vscode.executeWorkspaceSymbolProvider",
				name,
			)) ?? [];

		// The provider does fuzzy matching, so filter to exact-name hits — that's
		// what "select the right symbol" would actually key on. Functions come back
		// with trailing "()" in their name, so normalise before comparing.
		const clean = (s: string) => s.replace(/\(\)$/, "");
		const exact = matches.filter((m) => clean(m.name) === name);
		const shown = exact.length > 0 ? exact : matches;

		out.appendLine(`■ ${name}  (${matches.length} raw match(es), ${exact.length} exact)`);

		if (shown.length === 0) {
			out.appendLine("    (nothing — LSP not ready, or symbol not in this workspace)\n");
			continue;
		}

		for (const m of shown.slice(0, 15)) {
			const uri = m.location.uri;
			const key = uri.toString();
			if (!fileTextCache.has(key)) {
				try {
					const doc = await vscode.workspace.openTextDocument(uri);
					fileTextCache.set(key, doc.getText());
				} catch {
					fileTextCache.set(key, "");
				}
			}
			const style = guessExportStyle(fileTextCache.get(key) ?? "", clean(m.name));
			const line = m.location.range.start.line + 1;
			out.appendLine(
				`    ${m.name}  [${kindLabel(m.kind)}]  ${relPath(uri)}:${line}  export=${style}` +
					(m.containerName ? `  (in ${m.containerName})` : ""),
			);
		}
		if (shown.length > 15) {
			out.appendLine(`    ... ${shown.length - 15} more`);
		}
		out.appendLine("");
	}

	out.appendLine("Done.");
}
