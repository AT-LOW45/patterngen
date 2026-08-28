import * as dotenv from "dotenv";
import * as vscode from "vscode";
import generateCode from "./commands/generate-code";
import openKnowledgeBase from "./commands/open-knowledge-base";
import symbolSpike from "./commands/symbol-spike";
import wrapInTryCatch from "./commands/wrap-in-try-catch";
import COMMANDS from "./constants/commands";
import { startLivelinessCheck, withBackendReady } from "./service/system.service";

dotenv.config();

/** Extension entry point — registers the commands and starts the backend liveness check. */
export async function activate(context: vscode.ExtensionContext) {
	const { registerCommand } = vscode.commands;
	console.log("welcome to patterngen!");

	context.subscriptions.push(
		registerCommand(COMMANDS.tryCatch.id, () => wrapInTryCatch(context)),
		registerCommand(
			COMMANDS.generateCode.id,
			withBackendReady(() => generateCode(context)),
		),
		registerCommand(
			COMMANDS.openKnowledgeBase.id,
			withBackendReady(() => openKnowledgeBase()),
		),
		registerCommand(COMMANDS.symbolSpike.id, () => symbolSpike(context)),
	);

	// commands are already registered; run the check in the background so it can
	// never delay activation. Gated commands consult its status via withBackendReady.
	startLivelinessCheck();
}

/** Called when the extension is deactivated. */
export function deactivate() {
	console.log("Thanks for using patterngen!");
}
