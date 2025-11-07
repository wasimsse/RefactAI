import * as vscode from 'vscode';
import { RefactAIClient } from './client';

export class FindingsProvider implements vscode.TreeDataProvider<FindingItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<FindingItem | undefined | null | void> = new vscode.EventEmitter<FindingItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<FindingItem | undefined | null | void> = this._onDidChangeTreeData.event;

  constructor(private client: RefactAIClient) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: FindingItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: FindingItem): Thenable<FindingItem[]> {
    if (element) {
      return Promise.resolve([]);
    }

    return this.getFindings();
  }

  private async getFindings(): Promise<FindingItem[]> {
    try {
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders || workspaceFolders.length === 0) {
        return [new FindingItem('No workspace folder found', vscode.TreeItemCollapsibleState.None)];
      }

      const result = await this.client.assessProject(workspaceFolders[0].uri.fsPath);
      
      if (!result.findings || result.findings.length === 0) {
        return [new FindingItem('No findings detected', vscode.TreeItemCollapsibleState.None)];
      }

      return result.findings.map(finding => {
        const severity = finding.severity || 'INFO';
        const icon = this.getSeverityIcon(severity);
        const tooltip = `${finding.summary}\nCategory: ${finding.category}\nSeverity: ${severity}`;
        
        const item = new FindingItem(
          finding.summary,
          vscode.TreeItemCollapsibleState.None,
          icon,
          tooltip
        );
        
        item.command = {
          command: 'vscode.open',
          title: 'Open File',
          arguments: [
            vscode.Uri.file(finding.location?.file || ''),
            {
              selection: new vscode.Range(
                (finding.location?.line || 1) - 1,
                (finding.location?.column || 1) - 1,
                (finding.location?.line || 1) - 1,
                (finding.location?.column || 1) - 1
              )
            }
          ]
        };
        
        return item;
      });
    } catch (error) {
      return [new FindingItem(`Error: ${error}`, vscode.TreeItemCollapsibleState.None)];
    }
  }

  private getSeverityIcon(severity: string): string {
    switch (severity.toUpperCase()) {
      case 'BLOCKER':
        return '🔴';
      case 'CRITICAL':
        return '🟠';
      case 'MAJOR':
        return '🟡';
      case 'MINOR':
        return '🔵';
      case 'INFO':
        return '⚪';
      default:
        return '⚪';
    }
  }
}

export class FindingItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly icon?: string,
    public readonly tooltip?: string
  ) {
    super(label, collapsibleState);
    
    if (icon) {
      this.iconPath = new vscode.ThemeIcon('warning');
    }
    
    if (tooltip) {
      this.tooltip = tooltip;
    }
  }
}
