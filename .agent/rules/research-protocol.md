---
trigger: model_decision
description: Apply proactively when adding features or external libraries. Sync your knowledge with the exact versions in the project manifest and official examples before coding. Never guess APIs.
---

# Agent Rule: Universal Research Protocol

## 1. The Golden Rule
**"Never Guess APIs."**
Libraries, frameworks, and languages are fast-moving targets. Breaking changes happen constantly.
Your internal training data is likely outdated regarding specific recent versions.
Before writing code for a complex or unfamiliar task, you must strictly follow this research protocol.

## 2. Step 1: Establish the "Source of Truth"
You cannot research effectively without knowing the target.
1.  **Read the Manifest:** Locate the dependency definition file (e.g., `Cargo.toml`, `requirements.txt`, `package.json`, `pom.xml`, `project.godot`).
2.  **Identify Core Version:** Note the exact version of the primary language or framework (e.g., `Bevy 0.16`, `Python 3.12`, `Godot 4.3`, `Spring Boot 3.2`).
3.  **Identify Dependency Versions:** If using specific libraries (e.g., `pandas`, `serde`, `godot-rust`), note their specific versions as well.

## 3. Step 2: Targeted Information Retrieval
Once versions are confirmed, search for information **scoped to those specific tags/versions**.

### A. The Hierarchy of Reliability
When searching for "how to do X", prioritize sources in this order:
1.  **Official Examples (Repository):** The `examples/` folder in the specific Git Tag/Release of the project.
2.  **Integration Tests (Repository):** The `tests/` folder often shows edge cases, setup logic, and expected usage not found in examples.
3.  **Source Code (Interface):** Reading the actual function signatures/class definitions in the source files.
4.  **Official Documentation:** Ensure you are viewing the *correct version* of the documentation (e.g., docs.rs, ReadTheDocs, Javadoc).

### B. Execution Strategy
* **Version Scoping:** When searching, always append the version number or verify the Git branch matches the manifest.
* **Third-Party Deps:** Always check the third-party library's repository for an `examples` folder first, before looking at generic tutorials which may be outdated.

---

## 4. Step 3: Synthesis
Do not simply copy-paste found solutions.
1.  **Contextualize:** Adapt the example code to the current project's architecture (e.g., "Dependency Injection," "ECS Patterns," "OOP Class Structure").
2.  **Modernize:** Ensure the solution fits the project's established standards (e.g., "Universal Error Handling," specific logging patterns).
3.  **Verify:** If the example uses a parameter or method you don't recognize, double-check its definition in the source to ensure it exists in your version.

---

## 5. Research Checklist
*Before* writing the solution, ask:
1.  [ ] Did I check the manifest file for the current versions?
2.  [ ] Did I find an official example or documentation matching this *specific* version?
3.  [ ] Am I sure this API hasn't been deprecated or renamed in the version I am using?
4.  [ ] If using a specific library, did I check *its* specific examples/tests?