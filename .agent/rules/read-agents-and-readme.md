---
trigger: always_on
---

# Agent Rule: Context Loading & Memory Management

## 1. The Initialization Phase (Read)
**You are a visitor in an evolving codebase.**
Before analyzing a task, creating a plan, or writing a single line of code, you **must** establish situational awareness:
1.  **`README.md`**: To understand the project's scope, build environment, and entry points.
2.  **`AGENTS.md`** (or `DEVELOPMENT.md`): To upload the project's "long-term memory" (established patterns, past lessons, and architectural constraints).
3.  **Project Structure**: Briefly scan the file hierarchy to understand the prevailing naming conventions and modularization strategy.

## 2. Alignment (Act)
* **Respect the Past:** If `AGENTS.md` dictates a specific pattern (e.g., "Use Dependency Injection for services" or "Snake_case for file names"), adhere to it strictly.
* **Consistency Over Novelty:** Do not introduce conflicting patterns or new libraries without a compelling reason. Your code should look like it was written by the same team that wrote the rest of the project.
* **Context First:** Your solutions must fit into the existing architecture. If the project uses a specific Error Handling strategy, adopt it immediately.

## 3. Memory Consolidation (Write)
**Leave the campsite smarter than you found it.**
You are responsible for maintaining the collective intelligence of the project.
Before finishing a task, you must **update `AGENTS.md`** if:
1.  **New Patterns:** You established a new standard (e.g., "All asynchronous calls must use a specific wrapper" or "UI components must be decoupled from logic").
2.  **Hard Lessons:** You spent time debugging a specific framework quirk, environment issue, or "gotcha." Record the solution so future agents (or you) don't waste time on it.
3.  **Architectural Shifts:** You added a new major dependency, module, or changed how components communicate.

## 4. Checklist
1.  [ ] **Context:** Did I read `README.md` and `AGENTS.md` before starting?
2.  [ ] **Consistency:** Did I follow the patterns found in the memory/existing code?
3.  [ ] **Crucial:** Did I learn something new or change a pattern?
4.  [ ] **Handover:** If yes, did I document it in `AGENTS.md` for the next agent?