# RefactAI VS Code Extension

Professional Java refactoring suite with assessment-first workflow for VS Code.

## Features

- **Assessment-First Workflow**: Analyze code quality before making changes
- **Multiple Assessment Modes**: Project-wide, file-specific, and selection-based analysis
- **Refactoring Planning**: Generate and review refactoring plans
- **Tree View Integration**: View findings and plans in dedicated panels
- **Local-First**: All processing happens locally by default

## Installation

1. Install the extension from the VS Code marketplace
2. Configure the RefactAI server URL in settings (default: `http://localhost:8080`)
3. Open a Java project workspace

## Usage

### Commands

- **RefactAI: Assess Project** - Analyze the entire project for code smells
- **RefactAI: Assess File** - Analyze the currently open Java file
- **RefactAI: Assess Selection** - Analyze the selected code in the editor
- **RefactAI: Plan Refactoring** - Generate a refactoring plan based on findings
- **RefactAI: Apply Refactoring** - Apply the generated refactoring plan

### Views

- **Refactor Reasons** - Shows detected code smells and issues
- **Refactoring Plan** - Shows planned refactoring transformations

### Context Menu

Right-click on Java files or selected code to access RefactAI commands.

## Configuration

### Settings

- `refactai.serverUrl`: URL of the RefactAI server (default: `http://localhost:8080`)
- `refactai.enableAutoAssessment`: Automatically assess files when opened (default: `false`)
- `refactai.showFindingsInProblems`: Show findings in Problems panel (default: `true`)

## Development

### Building

```bash
npm install
npm run compile
```

### Testing

```bash
npm run test
```

### Packaging

```bash
vsce package
```

## Requirements

- VS Code 1.74.0 or higher
- Java project workspace
- RefactAI server running (for full functionality)

## License

[License information to be added]
