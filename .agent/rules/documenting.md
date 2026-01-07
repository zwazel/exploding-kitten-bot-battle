---
trigger: always_on
---

# Agent Rule: Universal Documentation Protocol

## 1. The Golden Rule
**If it isn't documented, it doesn't exist.**
Code explains *how* something works. Documentation explains *why* it exists and *how* to use it. Every code change requires a corresponding documentation check.

## 2. Categorization & Scope
You must categorize your changes to determine the required level of documentation.

### Level A: Inline Comments (The "Why")
* **Trigger:** Complex algorithms, non-obvious logic, regular expressions, or workarounds (hacks).
* **Scope:** Inside function/method bodies or script logic.
* **Rule:** Do not describe the code syntax (e.g., `// loop through array`). Describe the **intent** and **context** (e.g., `// Offset required to align text based on dynamic viewport width`).
* **Format:** Standard language-specific single-line comments (e.g., `//`, `#`, `--`).

### Level B: Interface Documentation (The "What" & "How")
* **Trigger:** Creating or modifying public APIs, classes, functions, modules, or global state managers.
* **Scope:** The exposed interface that other parts of the codebase interact with.
* **Rule:** All accessible items must have documentation explaining usage.
    * **Parameters/Inputs:** What does it expect? (Types, constraints).
    * **Returns/Outputs:** What does it produce?
    * **Side Effects:** Does it mutate global state, write to a database, or modify a generic component? (Critical for ECS Systems or Global Singletons).
    * **Errors:** What exceptions or errors might it throw?
* **Format:** Standard language-specific docstrings or block comments (e.g., Python Docstrings, Javadoc, Rustdoc, JSDoc).
    * *Example:*
        ```text
        [Description of function]

        Inputs: [Param A], [Param B]
        Returns: [Result]
        Side Effects: Modifies [Global State X]
        ```

### Level C: High-Level Documentation (The Big Picture)
* **Trigger:** Major features, architectural changes, environment setup, or new dependencies.
* **Scope:** Markdown files in the project root.
* **Files:**
    1.  **`README.md`**: User-facing. Update this when adding high-level features, changing build/run instructions, or adding dependencies.
    2.  **`AGENTS.md`** (or `DEVELOPMENT.md`): Developer-facing. Update this when establishing new patterns, recording architectural decisions, or noting "gotchas" for future developers/agents.

---

## 3. Protocol for `AGENTS.md`
`AGENTS.md` is the "long-term memory" of the project. You must check and update this file when:

1.  **New Patterns:** You introduce a specific way of doing things (e.g., "We always use dependency injection for services" or "Always prefer composition over inheritance").
2.  **Common Pitfalls:** You fix a bug caused by a specific language or framework quirk (record it so we don't repeat the mistake).
3.  **Refactoring:** You change the folder structure, module organization, or naming conventions.

---

## 4. Documentation Checklist
Before finishing a task, verify:

1.  [ ] **Inline:** Did I explain *why* any complex logic exists?
2.  [ ] **Interface:** Do my new functions/classes/modules have docstrings defining inputs, outputs, and side effects?
3.  [ ] **README:** Did I add a major feature or dependency that needs to be listed?
4.  [ ] **AGENTS.md:** Did I learn something new or change a core pattern that other agents need to know?