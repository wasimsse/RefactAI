# RefactAI

A professional, plugin-based Java refactoring suite with an assessment-first workflow and polished Web UI + VS Code extension.

## What is RefactAI?

RefactAI is an intelligent refactoring assistant that helps developers identify code smells, plan refactoring strategies, and safely apply transformations. It prioritizes correctness, determinism, maintainability, and security.

### Key Features

- **Assessment-First Workflow**: Analyze code quality before making changes
- **Plugin Architecture**: Extensible detectors and transforms via SPI
- **Multiple Interfaces**: CLI, Web UI, and VS Code extension
- **Deterministic Results**: Same input → same output, version-pinned formatters
- **Local-First**: No code sent externally unless explicitly enabled

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │  VS Code Ext    │    │      CLI        │
│  (Next.js)      │    │   (TypeScript)  │    │   (picocli)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    REST API + LSP         │
                    │   (Spring Boot)           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │      Core Engine          │
                    │  (Hexagonal Architecture) │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐         ┌───────▼──────┐        ┌──────▼─────┐
    │ Detectors │         │ Transforms  │        │  Verifiers │
    │ (SPI)     │         │   (SPI)     │        │   (SPI)    │
    └───────────┘         └─────────────┘        └────────────┘
```

## Quick Start

### CLI

```bash
# Install
./gradlew :backend:cli:installDist

# Assess a project
refactai assess --format json,html --out build/refact/

# Plan refactoring
refactai plan --from build/refact/assessment.json --interactive

# Apply changes
refactai apply --plan build/refact/plan.json --verify
```

### Web UI

```bash
# Start backend
./gradlew :backend:server:bootRun

# Start frontend (in another terminal)
cd web/app && npm run dev
```

Visit `http://localhost:3000` to use the web interface.

### VS Code Extension

1. Install the RefactAI extension from the marketplace
2. Open a Java project
3. Use commands: `RefactAI: Assess Project`, `RefactAI: Plan`, `RefactAI: Apply`

## Configuration

### Policy Configuration (`config/policy.yaml`)

```yaml
weights:
  risk: 0.5
  payoff: 0.4
  cost: 0.2

gates:
  forbid_refactor_if_tests_red: true
  min_coverage_for_risky: 0.6

protected_packages:
  - "com.company.security.**"
```

### Smell Mapping (`config/smell_mapping.yaml`)

```yaml
mappings:
  design.long-method:
    transforms:
      - { id: extract-method, intent: "split responsibilities" }
      - { id: introduce-parameter-object, when: "params>5" }
  design.god-class:
    transforms:
      - { id: extract-class }
      - { id: move-method }
```

## Development

### Backend (Java 21)

```bash
# Build all modules
./gradlew build

# Run tests
./gradlew test

# Run specific module
./gradlew :backend:server:bootRun
```

### Web App (Next.js)

```bash
cd web/app
npm install
npm run dev
```

### VS Code Extension

```bash
cd vscode/client
npm install
npm run compile
```

## Security Model

- **Local-First**: All processing happens locally by default
- **Redaction Layer**: Sensitive data is redacted before any external calls
- **Plugin Permissions**: Granular permissions for filesystem, network, and process access
- **Provenance Logging**: All changes are logged with plugin versions and prompts

## Roadmap

### MVP (Current)
- [x] Basic project structure
- [ ] Core SPIs and plugin architecture
- [ ] Essential detectors (Long Method, God Class, etc.)
- [ ] Basic transforms (Extract Method, Rename, etc.)
- [ ] CLI with assessment workflow
- [ ] Web UI with ingestion and findings display
- [ ] VS Code extension with basic commands

### v1.0
- [ ] Advanced detectors and transforms
- [ ] Machine learning-powered suggestions
- [ ] Team collaboration features
- [ ] Integration with CI/CD pipelines
- [ ] Performance optimizations

### Future
- [ ] Multi-language support
- [ ] Cloud-based processing options
- [ ] Advanced visualization and analytics
- [ ] Integration with other IDEs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[License information to be added]
