// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import COMMANDS from './constants/commands';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  // console.log('Congratulations, your extension "patterngen" is now active!');
  const {registerCommand} = vscode.commands;

  // The command has been defined in the package.json file
  // Now provide the implementation of the command with registerCommand
  // The commandId parameter must match the command field in package.json
  const disposable = registerCommand(COMMANDS.helloWorld.id, () => {
    // The code you place here will be executed every time your command is executed
    // Display a message box to the user
    vscode.window.showInformationMessage('Hello World from patterngen!');
  });

  const anotherCommand = registerCommand(COMMANDS.tryCatch.id, () => {
    const editor = vscode.window.activeTextEditor;
		
  });

  context.subscriptions.push(disposable);
  context.subscriptions.push(anotherCommand);
}

// This method is called when your extension is deactivated
export function deactivate() {
  // console.log('Goodbye!');
}
