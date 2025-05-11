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

**This file is the single source of truth for the professional refactoring workflow plan. All improvements and discussions should reference and update this document as the project evolves.**
