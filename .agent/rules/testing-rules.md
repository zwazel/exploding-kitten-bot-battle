---
trigger: always_on
---

# Agent Rule: Universal Testing Protocol

## 1. The Golden Rule
**Every code change must be accompanied by a test.**
Do not assume your code works. Verify it. If you modify logic, update existing tests. If you add features, write new tests.

## 2. Categorization & Location
You must distinguish between **Unit Tests** and **Integration Tests** based on the complexity and scope of the change.

### A. Unit Tests (Isolated Logic)
* **Scope:** Individual functions, classes, math helpers, or algorithmic logic that has no external dependencies (no database, no game engine, no network).
* **Location:** Follow the language convention (e.g., inside the source file for Rust/Go, or in a parallel `tests/unit` directory for Java/Python).
* **Format:** Use the standard language testing framework (e.g., `pytest`, `JUnit`, `cargo test`). Focus on edge cases and pure inputs/outputs.

### B. Integration Tests (System Interaction)
* **Scope:** System interactions, module communication, database queries, API endpoints, or Game Loop logic.
* **Location:** Strictly inside the dedicated test suite directory (e.g., `tests/`, `src/test/java`, `test/integration`).
* **Format:** Tests here should verify that different parts of the application work together correctly.

---

## 3. Integration Testing Strategy: "The Simulation Pattern"
Integration tests must simulate the actual runtime environment as closely as possible. Do not mock internal framework structures unless absolutely necessary.

### Step 1: Environment Alignment
Before writing a test, you **must**:
1.  Read the **Project Manifest** (e.g., `Cargo.toml`, `pom.xml`, `package.json`) to determine the exact versions of the framework/libraries.
2.  Consult the official documentation or repository examples for that *specific version* to understand how to initialize a test environment.

### Step 2: Simulation (Headless Execution)
Construct a minimal, headless instance of the application to run the test.
* **Minimal Context:** Do not load heavy assets (graphics, audio, UI) unless explicitly testing them. Load only the core modules required.
* **Registration:** Register only the specific services, components, or dependencies needed for the test.
* **Manual Execution:** Manually trigger the "tick," "update," or "request" cycle to simulate the passage of time or data processing.

**Generic Pattern (Setup -> Act -> Assert):**
```text
[Test Function]
    1. SETUP: Initialize minimal App/Container/Context.
       -> Inject dependencies or Register Systems.
       -> Spawn initial state (Entities/Objects).
    
    2. ACT: Trigger the execution manually.
       -> e.g., app.update(), service.process(), game_loop.tick().
    
    3. ASSERT: Query the resulting state.
       -> Check if data changed as expected.
```

---

## 4. Test Utilities & Fixtures (DRY)
The test suite should contain a shared "Common" or "Fixtures" module to improve Developer Experience (DX).

* **Inspect First:** Before writing boilerplate setup code, check the shared test utilities. If a helper exists (e.g., `create_test_user()`, `spawn_test_world()`), **use it**.
* **Improve & Refactor:** You are explicitly authorized and encouraged to modify these utilities.
    * If you write a setup function that could be useful elsewhere, move it to the common module.
    * If an existing helper is clumsy or outdated, refactor it to be better.
    * Treat test code as first-class citizens; keep it clean and DRY (Don't Repeat Yourself).

---

## 5. Checklist Before Committing
1.  [ ] Did I check the Project Manifest for version context?
2.  [ ] Is this a logic test (Unit) or a system interaction test (Integration)?
3.  [ ] If Integration: Did I set up a proper "Headless" simulation?
4.  [ ] Did I check the shared utilities/fixtures for existing tools?
5.  [ ] Did I improve the shared utilities if I wrote reusable boilerplate?
6.  [ ] Do all tests pass locally?