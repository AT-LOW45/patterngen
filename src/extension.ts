// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import COMMANDS from "./constants/commands";
import wrapInTryCatch from "./commands/wrap-in-try-catch";

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	// console.log('Congratulations, your extension "patterngen" is now active!');
	const { registerCommand } = vscode.commands;
	console.log("welcome to patterngen!");

	context.subscriptions.push(registerCommand(COMMANDS.tryCatch.id, () => wrapInTryCatch(context)));
}

// This method is called when your extension is deactivated
export function deactivate() {
	console.log("Thanks for using patterngen!");
}
