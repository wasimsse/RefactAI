import * as vscode from 'vscode';
import { RefactAIClient } from './client';
import { FindingsProvider } from './findingsProvider';
import { PlanProvider } from './planProvider';

let client: RefactAIClient;
let findingsProvider: FindingsProvider;
let planProvider: PlanProvider;

export function activate(context: vscode.ExtensionContext) {
  console.log('RefactAI extension is now active!');

  // Initialize client
  const config = vscode.workspace.getConfiguration('refactai');
  const serverUrl = config.get<string>('serverUrl', 'http://localhost:8080');
  client = new RefactAIClient(serverUrl);

  // Register tree data providers
  findingsProvider = new FindingsProvider(client);
  planProvider = new PlanProvider(client);

  vscode.window.registerTreeDataProvider('refactai.findings', findingsProvider);
  vscode.window.registerTreeDataProvider('refactai.plan', planProvider);

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('refactai.assessProject', assessProject),
    vscode.commands.registerCommand('refactai.assessFile', assessFile),
    vscode.commands.registerCommand('refactai.assessSelection', assessSelection),
    vscode.commands.registerCommand('refactai.plan', plan),
    vscode.commands.registerCommand('refactai.apply', apply),
    vscode.commands.registerCommand('refactai.refreshFindings', () => {
      findingsProvider.refresh();
    }),
    vscode.commands.registerCommand('refactai.refreshPlan', () => {
      planProvider.refresh();
    })
  );
}

export function deactivate() {
  console.log('RefactAI extension is now deactivated!');
}

async function assessProject() {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    vscode.window.showErrorMessage('No workspace folder found');
    return;
  }

  const workspaceFolder = workspaceFolders[0];
  
  try {
    vscode.window.showInformationMessage('Assessing project...');
    
    const result = await client.assessProject(workspaceFolder.uri.fsPath);
    
    vscode.window.showInformationMessage(`Assessment complete! Found ${result.findings?.length || 0} issues.`);
    
    // Refresh the findings view
    findingsProvider.refresh();
    
  } catch (error) {
    vscode.window.showErrorMessage(`Assessment failed: ${error}`);
  }
}

async function assessFile() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active editor');
    return;
  }

  const document = editor.document;
  if (document.languageId !== 'java') {
    vscode.window.showErrorMessage('Current file is not a Java file');
    return;
  }

  try {
    vscode.window.showInformationMessage('Assessing file...');
    
    const result = await client.assessFile(document.uri.fsPath);
    
    vscode.window.showInformationMessage(`Assessment complete! Found ${result.findings?.length || 0} issues.`);
    
    // Refresh the findings view
    findingsProvider.refresh();
    
  } catch (error) {
    vscode.window.showErrorMessage(`Assessment failed: ${error}`);
  }
}

async function assessSelection() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active editor');
    return;
  }

  const selection = editor.selection;
  if (selection.isEmpty) {
    vscode.window.showErrorMessage('No text selected');
    return;
  }

  const document = editor.document;
  if (document.languageId !== 'java') {
    vscode.window.showErrorMessage('Current file is not a Java file');
    return;
  }

  try {
    vscode.window.showInformationMessage('Assessing selection...');
    
    const selectedText = document.getText(selection);
    const result = await client.assessSelection(document.uri.fsPath, selectedText, selection);
    
    vscode.window.showInformationMessage(`Assessment complete! Found ${result.findings?.length || 0} issues.`);
    
    // Refresh the findings view
    findingsProvider.refresh();
    
  } catch (error) {
    vscode.window.showErrorMessage(`Assessment failed: ${error}`);
  }
}

async function plan() {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    vscode.window.showErrorMessage('No workspace folder found');
    return;
  }

  try {
    vscode.window.showInformationMessage('Generating refactoring plan...');
    
    const result = await client.plan(workspaceFolders[0].uri.fsPath);
    
    vscode.window.showInformationMessage(`Plan generated! ${result.transforms?.length || 0} transforms planned.`);
    
    // Refresh the plan view
    planProvider.refresh();
    
  } catch (error) {
    vscode.window.showErrorMessage(`Plan generation failed: ${error}`);
  }
}

async function apply() {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    vscode.window.showErrorMessage('No workspace folder found');
    return;
  }

  try {
    vscode.window.showInformationMessage('Applying refactoring...');
    
    const result = await client.apply(workspaceFolders[0].uri.fsPath);
    
    if (result.success) {
      vscode.window.showInformationMessage('Refactoring applied successfully!');
    } else {
      vscode.window.showWarningMessage('Refactoring completed with issues. Check the output for details.');
    }
    
  } catch (error) {
    vscode.window.showErrorMessage(`Refactoring failed: ${error}`);
  }
}
