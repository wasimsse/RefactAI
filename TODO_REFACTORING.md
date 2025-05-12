# RefactAI – Professional Refactoring Tab Improvement Plan

## 1. LLM Model Selection (Professional & Dynamic)
- Show all available LLMs in a dropdown, clearly labeled, with model details (type, size, etc.).
- Dropdown in the sidebar or at the top of the Refactoring tab.
- Show model info (e.g., "Viking-33B (GPT-Lab, 33B params)").
- Optionally, show model status (available, busy, etc.) if possible.

## 2. Step-by-Step Professional Workflow
- Guide the user through a clear, logical, and professional refactoring process.
- Phases:
  1. File Selection: Search/filter files, show file info (size, last modified, LOC).
  2. Code Analysis: Show metrics (LOC, complexity, coupling, etc.), visualize code smells.
  3. Pattern Selection: Enable/disable patterns based on analysis, show descriptions.
  4. LLM Model & Parameter Selection: Model dropdown, temperature, max tokens, etc.
  5. Preview Refactoring: Side-by-side diff, highlighted changes, LLM's reasoning.
  6. Apply & Save: Confirm/apply changes, download before/after code and diff.

## 3. Accuracy & Quality Controls
- Show the exact prompt sent to the LLM.
- Show the LLM's explanation/reasoning (if returned).
- Allow user to rate/refine the output.
- Optionally, allow user to edit the prompt or add custom instructions.
- Optionally, run static analysis on the refactored code and show new metrics/smells.

## 4. Professional UI/UX Enhancements
- Progress indicator for workflow steps.
- Clear error/success messages.
- Tooltips/help for each option.
- Consistent, modern design (colors, spacing, icons).

## 5. (Optional) Advanced Features
- Batch refactoring (multiple files/classes).
- Refactoring history and undo.
- Export full refactoring report (PDF/HTML).
- Compare outputs from multiple LLMs side-by-side.

---

## Implementation Roadmap

1. Model Selection UI: Add a professional dropdown for all LLMs, with info and status.
2. Refactoring Workflow Polish: Refine each step for clarity, guidance, and professional look.
3. Accuracy/Quality Feedback: Show prompt, LLM reasoning, and allow user feedback.
4. UI/UX Enhancements: Progress bar, tooltips, error handling, and visual polish.
5. (Optional) Advanced Features: Batch, history, export, multi-LLM comparison.

---

## Refactoring Pattern System: Enhancement Plan (for tomorrow)

- [ ] **Pattern Recommendation Intelligence**
    - [ ] Dynamic Pattern Ranking: Rank and highlight patterns based on severity, frequency, code metrics, and past user choices
    - [ ] Pattern Impact Preview: Show a summary of what each pattern will change in the code
- [ ] **Pattern-Driven LLM Prompting**
    - [ ] Pattern-to-Prompt Mapping: Generate tailored prompt snippets for each selected pattern
    - [ ] Pattern Combination Handling: Combine instructions for multiple patterns intelligently
- [ ] **User Experience & UI**
    - [ ] Pattern Details Modal: Click for before/after code, usage tips, and external links
    - [ ] Pattern Search & Filter: Quickly find patterns by name, category, or effect
- [ ] **Feedback Loop**
    - [ ] User Feedback on Patterns: Let users rate usefulness and suggest improvements
    - [ ] Pattern Effectiveness Tracking: Track which patterns lead to successful refactorings
- [ ] **Extensibility**
    - [ ] Pattern Plugin System: Allow adding new/custom patterns via config or plugin

**Suggested Implementation Steps:**
1. Refactor `refactoring_patterns.py` to add ranking, metadata, and prompt generation
2. Update Pattern Selection UI with search/filter, modal, impact preview, and ranking
3. Integrate Pattern-to-Prompt logic in the LLM refactoring step
4. Add Feedback UI (optional)
5. Document extensibility in README or config example

**This file is the single source of truth for the professional refactoring workflow plan. All improvements and discussions should reference and update this document as the project evolves.**
