import * as vscode from 'vscode';
import { RefactAIClient } from './client';

export class PlanProvider implements vscode.TreeDataProvider<PlanItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<PlanItem | undefined | null | void> = new vscode.EventEmitter<PlanItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<PlanItem | undefined | null | void> = this._onDidChangeTreeData.event;

  constructor(private client: RefactAIClient) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: PlanItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: PlanItem): Thenable<PlanItem[]> {
    if (element) {
      return Promise.resolve([]);
    }

    return this.getPlan();
  }

  private async getPlan(): Promise<PlanItem[]> {
    try {
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders || workspaceFolders.length === 0) {
        return [new PlanItem('No workspace folder found', vscode.TreeItemCollapsibleState.None)];
      }

      const result = await this.client.plan(workspaceFolders[0].uri.fsPath);
      
      if (!result.transforms || result.transforms.length === 0) {
        return [new PlanItem('No refactoring plan available', vscode.TreeItemCollapsibleState.None)];
      }

      return result.transforms.map(transform => {
        const priority = this.calculatePriority(transform.risk, transform.payoff, transform.cost);
        const icon = this.getPriorityIcon(priority);
        const tooltip = `${transform.description}\nRisk: ${transform.risk}\nPayoff: ${transform.payoff}\nCost: ${transform.cost}\nPriority: ${priority.toFixed(2)}`;
        
        const item = new PlanItem(
          transform.description,
          vscode.TreeItemCollapsibleState.None,
          icon,
          tooltip
        );
        
        item.contextValue = 'transform';
        item.command = {
          command: 'refactai.previewTransform',
          title: 'Preview Transform',
          arguments: [transform]
        };
        
        return item;
      });
    } catch (error) {
      return [new PlanItem(`Error: ${error}`, vscode.TreeItemCollapsibleState.None)];
    }
  }

  private calculatePriority(risk: number, payoff: number, cost: number): number {
    // Simple priority calculation: payoff - risk - cost
    return payoff - risk - cost;
  }

  private getPriorityIcon(priority: number): string {
    if (priority >= 0.5) {
      return '🟢'; // High priority
    } else if (priority >= 0.0) {
      return '🟡'; // Medium priority
    } else {
      return '🔴'; // Low priority
    }
  }
}

export class PlanItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly icon?: string,
    public readonly tooltip?: string
  ) {
    super(label, collapsibleState);
    
    if (icon) {
      this.iconPath = new vscode.ThemeIcon('lightbulb');
    }
    
    if (tooltip) {
      this.tooltip = tooltip;
    }
  }
}
