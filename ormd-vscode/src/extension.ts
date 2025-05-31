import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('Congratulations, your extension "ormd-vscode" is now active!');

    // Log that the extension has been activated for ORMD language
    vscode.window.showInformationMessage('ORMD VSCode Extension Activated');

    // Example: Register a simple command (optional, can be removed if not needed initially)
    let disposable = vscode.commands.registerCommand('ormd-vscode.helloWorld', () => {
        vscode.window.showInformationMessage('Hello World from ORMD VSCode!');
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {
    console.log('Your extension "ormd-vscode" is now deactivated.');
}
