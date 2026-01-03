# AGENTS.md (docs/)

This folder contains the project documentation site built with **MkDocs**, **mkdocs-material**, and **mkdocstrings** (API reference rendered from Python docstrings).  
If you’re an agent making changes here, optimize for **clarity, consistency, and zero broken builds**.

---

## Goals for docs changes

- Keep docs **user-first**: practical, without jargon, clear, and accurate.
- Ensure docs are **complete enough** for new users to onboard and use the project.
- Maintain **buildability**: docs should always build without errors or warnings.
- Preserve **link integrity**: no broken internal or external links.

---

## Documentation structure (conventional)

We follow the *Diátaxis* style split. Put content where it belongs:

- **Tutorials** (`docs/tutorials/`): learning-oriented, step-by-step, “do this then that”. Serves as getting started section and onboarding. Can link to how-to guides for specific tasks. Assumes nothing, includes commands/output, tiny dataset, happy path only.
- **How-to guides** (`docs/how-to/`): task-oriented, goal-driven, examples assumes basic familiarity.
- **Topics & Concepts / Explanation** (`docs/references/`): Understanding-oriented, clarifying a particular topic. Detailed explanations of features, architecture, design decisions. Can contain nested subfolders properly organizing conceptual content if needed.
- **API Reference** (`docs/api/`): auto-generated from code docstrings (mkdocstrings), follows code structure of packages/modules and contains mkdocstrings references to modules. Information-oriented, technical descriptions of machinery, API documentation. Follows package and module structure of main python codebase. Includes potentially nested subfolders properly organizing conceptual content if needed.

If the repo doesn’t have these folders yet, create them and wire them into `mkdocs.yml` navigation.

---

## Recommended folder layout

Suggested baseline (adjust to what already exists):

- `docs/index.md` – landing page / quickstart
- `docs/tutorials/` – learning guides
- `docs/how_to/` – task recipes
- `docs/explanation/` – explanations, feature descriptions, architecture, decisions. Should contain nested subfolders properly organizing conceptual content if needed.
- `docs/examples/` – practical examples and code-based tutorials. Also contains code snippets that may be referenced in other documentation.
- `docs/api/` – API reference (mkdocstrings). There should be ideally one file per top-level package or module.
- `docs/assets/` – images, diagrams, small static files

Keep filenames lowercase with underscores: `my_feature.md`. Sample applies to folders too: `my_feature/`. Each folder will have an `index.md` as landing page.

---

## Documentation tools & formats

We document using markdown files and syntax. We use the following tools and libraries:

- mkdocs
- mkdocs-material
- mkdocs-material-extensions
- mkdocstring for API docs
- YAML for configuration files
- Python for code examples and API docs
- mermaid plugin for diagrams

---

## MkDocs navigation rules

- Update `mkdocs.yml` `nav:` when adding/removing pages if mkdocs.yml is present.
- Keep nav shallow when possible (2 levels is usually enough).
- Page titles should be human-readable; file names can be mechanical.

---

## API docs with mkdocstrings (the “source of truth”)

**Docstrings in the Python code are the primary source.** Docs pages should link/compose them, not rewrite them.

In `docs/reference/*.md`, use mkdocstrings directives, e.g.:

- Module docs
  - `::: package.module`
- Class docs
  - `::: package.module.ClassName`
- Function docs
  - `::: package.module.function_name`

Fetch and See https://mkdocstrings.github.io/handlers/python/ for details.

## Examples for mkdocstrings usage
You can customize mkdocstrings rendering with options. Here are some examples:

### Example For Class API Docs:
```md
::: tms_calibration.data.CalibrationData
    options:
        show_source: true
        show_heading: false
        heading_level: 3
        separate_signature: true
        group_by_category: true
        show_category_heading: true
        members: [load_from_catalog, update_outliers, update_predictions, save_predictions, update_thresholds, save_thresholds]
```

### For Module API Docs:
```
::: tms_calibration.candidate_selection.algorithms.threshold_grid
    options:
        show_source: true
        heading_level: 2
        separate_signature: true
        group_by_category: true
        show_category_heading: false
        methods: [fit, visualize]
```

Guidelines:
- Don’t paste full function signatures manually—mkdocstrings will render them.
- Prefer **small wrapper pages** (one module per page, or one top-level package page with sections).
- Keep reference pages stable: avoid churn in headings/anchors.

---

## Writing style rules (docs) for writing documentation

- Keep it direct. Prefer short sentences.
- Use “you” for user-facing docs.
- Prefer active voice.
- Use consistent terms (don’t rename concepts across pages).
- Headings should be descriptive (avoid “Misc”, “Other”).
- Include front matter

### Front Matter

- **Front Matter**: Include the following fields in the YAML front matter:
  - `title`: The title of the post.
  - `description`: The URL of the featured image.
  - `icon`: The icon for the post.
  - `summary`: A very brief summary of the post. Recommend a summary based on the content when possible.


#### Icon Example:
```md
---
icon: material/emoticon-happy 
---
```


### Links
- Prefer **relative links** within docs.
- Don’t link to generated site URLs.
- Avoid linking to unstable external sources unless necessary.

### Syntax & Structure conventions for documentation markdown files
- One top-level `#` per page.
- Wrap lines reasonably (don’t hard-wrap aggressively unless the repo does).
- Use fenced code blocks with language tags: ```python, ```bash, ```yaml.
- Use fenced code blocks with language identifiers for all code snippets.
- Use Mermaid diagrams when appropriate (flowchart, sequenceDiagram, classDiagram, erDiagram).
- Use headings and subheadings to organize content clearly.
- Use bullet points or numbered lists for clarity.
- Use bold or italics to emphasize important points.
- Include links to relevant resources or documentation where appropriate.
- IMPORTANT: **Use mkdocs material admonitions for notes, tips, warnings, etc.**
    - https://squidfunk.github.io/mkdocs-material/reference/admonitions/
- IMPORTANT: **Use mkdocs content tabs for organizing related content.**
    - https://squidfunk.github.io/mkdocs-material/reference/content-tabs/


#### How to use Admonitions and Content Tabs

##### Admonitions
```md
!!! note "What is Data Factory"
    The data catalog factories are patterns to match dataset files and are used to quickly access the data with the help 
    of the data catalog without registering each dataset one by one.

!!! tip "Phasellus posuere in sem ut cursus"

    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
    nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
    massa, nec semper lorem quam in massa.
```

##### Content Tabs
Content tabs to group and organize related content
```md
=== "C"

    ``` c
    #include <stdio.h>

    int main(void) {
      printf("Hello world!\n");
      return 0;
    }
    ```

=== "C++"

    ``` c++
    #include <iostream>

    int main(void) {
      std::cout << "Hello world!" << std::endl;
      return 0;
    }
    ```
```md

##### Combine Tabs and Admonitions

```md
!!! example

    === "Unordered List"

        ``` markdown
        * Sed sagittis eleifend rutrum
        * Donec vitae suscipit est
        * Nulla tempor lobortis orci
        ```

    === "Ordered List"

        ``` markdown
        1. Sed sagittis eleifend rutrum
        2. Donec vitae suscipit est
        3. Nulla tempor lobortis orci
        ```
```


### For Examples:
- For longer examples. You ideally store them inside `docs/examples/`. You can inject the script or include it as a code block with a file reference. Ensure that the example is relevant to the context. The example should be clear, concise, and easy to understand. If the script is long, consider wrapping it in a toggled admonition (`???`) for better visibility.
  
```md
??? example "Example: Using Threshold Grid"
    ```python
    --8<-- "docs/examples/calibration/initial_threshold_setting_with_grid.py"
    ```
```

---

## Build & preview commands (agent must keep docs buildable)

Use whatever the project already uses, but these are the common options:

- Local preview:
  - `mkdocs serve`
  - or `python -m mkdocs serve`
  - or (if using uv) `uv run mkdocs serve`

If CI runs a strict build, treat warnings as failures.

---

## What to check before finishing

- ✅ `mkdocs build` succeeds without failures
- ✅ No broken internal links
- ✅ API reference pages render (mkdocstrings directives resolve)
- ✅ Examples match the current API (names/import paths)

---

## When adding a new feature to the codebase

Minimum docs expectation:
1. Add or update a **How-to** or **Tutorial** (depending on complexity).
2. Ensure docstrings are complete so the **Reference** page stays correct.
3. Add a short note to `docs/index.md` or a “Quickstart” section if it changes onboarding.

---

## Safe defaults for agents

If you’re unsure where something goes:
- Put procedural “do X” content in **How-to**
- Put “what is X and why” in **Concepts**
- Put exact signatures/parameters in **API** (mkdocstrings)

Don’t invent behavior. If you can’t confirm from code/tests, say so or leave it out.