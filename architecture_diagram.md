# RefactAI Application Architecture Diagram

```mermaid
graph TD
    subgraph UI[User Interface (Streamlit Tabs)]
        Home[Home]
        Upload[Project Upload]
        Detection[Smell Detection]
        Refactoring[Refactoring]
        Testing[Testing & Metrics]
    end

    subgraph ProjectManager[Project/File Management]
        FileUpload[Upload ZIP/Files]
        GitHub[GitHub Import]
        FileBrowser[File Browser]
    end

    subgraph Analysis[Code Analysis]
        Metrics[Metrics Calculation]
        SmellDetection[Code Smell Detection]
        AST[AST Analysis]
    end

    subgraph Refactor[LLM-Powered Refactoring]
        LLM[GPT-Lab Integration]
        Ripple[LLM Ripple Check]
        Preview[Preview Changes]
        Apply[Apply Refactoring]
        Undo[Undo/History]
    end

    subgraph Testing[Testing & Coverage]
        JUnit[JUnit Test Runner]
        JaCoCo[JaCoCo Coverage]
        TestParse[Test Result Parsing]
    end

    subgraph Export[Export/Reporting]
        Download[Download Code/Diff]
        Report[Markdown Report]
    end

    UI -->|User Actions| ProjectManager
    UI -->|User Actions| Analysis
    UI -->|User Actions| Refactor
    UI -->|User Actions| Testing
    UI -->|User Actions| Export

    ProjectManager -->|Project Data| Analysis
    ProjectManager -->|Project Data| Refactor
    ProjectManager -->|Project Data| Testing

    Analysis -->|Metrics/Smells| Refactor
    Analysis -->|Metrics/Smells| UI

    Refactor -->|Refactored Code| ProjectManager
    Refactor -->|Refactored Code| Testing
    Refactor -->|History| Undo
    Refactor -->|Preview/Apply| UI
    Refactor -->|LLM Calls| LLM
    Refactor -->|Ripple Check| Ripple

    Testing -->|Test Results| UI
    Testing -->|Coverage| UI
    Testing -->|Test Results| Export
    Testing -->|JUnit/JaCoCo| JUnit
    Testing -->|JUnit/JaCoCo| JaCoCo
    Testing -->|Parse| TestParse

    Export -->|Downloads| UI
    Export -->|Reports| UI

    LLM -.->|API Calls| GPTLab[GPT-Lab Endpoints]
    GitHub -.->|Repo ZIP| GitHubAPI[GitHub]
    ProjectManager -.->|File IO| FileSystem[Local File System]

    classDef ext fill:#f9f,stroke:#333,stroke-width:2px;
    class GPTLab,GitHubAPI,FileSystem ext;
```

---

## Legend & Explanation
- **UI (User Interface):** Streamlit tabs for user interaction.
- **Project/File Management:** Handles uploads, GitHub imports, and file browsing.
- **Code Analysis:** Calculates metrics, detects code smells, and performs AST analysis.
- **LLM-Powered Refactoring:** Integrates with GPT-Lab for refactoring, ripple checks, preview, apply, and undo/history.
- **Testing & Coverage:** Runs JUnit tests, collects JaCoCo coverage, and parses results.
- **Export/Reporting:** Allows users to download code, diffs, and reports.
- **External Dependencies:** GPT-Lab endpoints (LLM), GitHub, and the local file system.
- **Arrows** show data flow and interactions between components.

This diagram provides a high-level overview of the end-to-end process and architecture of the RefactAI application, showing how user actions flow through the system and how each major component interacts with others and with external services. 