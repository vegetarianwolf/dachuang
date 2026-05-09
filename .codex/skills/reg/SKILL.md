---
name: reg
description: Write and run Stata panel-data regressions for the current workspace. Use when the user asks for panel regression, fixed effects, random effects, baseline regression, robustness, heterogeneity, mediation, or other econometric regressions that should read data from a `面板数据` directory, generate a runnable `.do` file, save `.do` and `.log` outputs under `运行日志与do代码`, and execute the regression through Stata MCP.
---

# Reg

## Overview

Turn a regression request into a complete Stata workflow: inspect the panel dataset, write a runnable `.do` file, save it in `运行日志与do代码`, run it with Stata MCP, save the `.log` beside it, and then report the result back to the user.

## Required Workflow

1. Resolve the project root.
   - Start from the current workspace.
   - Prefer the nearest directory that contains `面板数据` and `运行日志与do代码`.
   - If only one exists, continue with that root and note the assumption.

2. Find the input dataset.
   - Inspect `面板数据` first.
   - Prefer `.dta`.
   - If there is no `.dta`, fall back to `.csv`, `.xlsx`, or `.xls`.
   - If multiple files match, choose the one that best matches the user's request.
   - If the choice is materially ambiguous, ask one short clarifying question instead of guessing.

3. Inspect the data before writing code.
   - Never invent variable names.
   - Read filenames and, when needed, inspect columns with lightweight commands or a short Stata probe.
   - Infer panel id and time variables only when the evidence is strong.
   - If panel id or time variable cannot be inferred safely, ask the user.

4. Write a complete `.do` file under `运行日志与do代码`.
   - Name the file after the regression content, using actual variable names when possible.
   - Prefer concise ASCII names such as `xtreg_fe_y_x_corecontrols.do`.
   - If a same-name file already exists, append a timestamp suffix.
   - The `.do` file must be directly runnable without manual edits.

5. Always include log handling in the `.do` file.
   - Start with `capture log close`.
   - Open the log with `log using "...", replace text`.
   - Save the `.log` in the same `运行日志与do代码` directory and use the same basename as the `.do` file.
   - Close the log before exit even if the script contains multiple estimation blocks.

6. Include the Stata setup and data loading code.
   - Use `version`, `clear all`, and `set more off`.
   - Define path locals for root, data file, output directory, and log path.
   - Use `use` for `.dta`, and `import delimited` or `import excel` for non-Stata formats.
   - Add only the minimum cleaning or encoding needed to make the requested regression run.

7. Implement the requested regression faithfully.
   - If the user specifies FE, RE, OLS, DID, mediation, heterogeneity, threshold, or robustness checks, follow that request.
   - If the user simply asks for panel regression and the panel structure is clear, default to a panel specification rather than plain OLS.
   - Use `xtset` before panel estimators.
   - Add fixed effects, clustered standard errors, controls, or tests only when requested or clearly implied by the standard specification.
   - Avoid adding large extras the user did not ask for.

8. Run the saved `.do` file through Stata MCP.
   - Prefer `stata_run_file` once the `.do` file is saved.
   - If a first run fails, fix the `.do` file and rerun it before replying.
   - Do not stop after only writing code when the user asked for regression results.

9. Report back with artifact paths and outcome.
   - Mention which dataset was used.
   - Mention the saved `.do` and `.log` paths.
   - Summarize whether the run succeeded, and note important warnings or estimation failures.

## Do-File Requirements

Every generated `.do` file should usually include:

- `version`
- `clear all`
- `set more off`
- `capture log close`
- local macros for root, data path, output path, do-file basename, and log path
- the data import or `use` statement
- any needed `destring`, `encode`, `drop if missing(...)`, or `egen` steps
- `xtset` when running panel models
- the requested estimation commands
- optional `estimates store` lines when there are multiple models
- `log close`

Use comments sparingly and only where they help the next reader understand non-obvious logic.

## Naming Rules

- Base names should reflect method plus key variables, for example:
  - `xtreg_fe_tfp_dig.do`
  - `re_sales_policy_controls.do`
  - `did_innovation_treat_post.do`
- Reuse the same basename for `.do` and `.log`.
- If the request contains multiple stages, add a short qualifier such as `baseline`, `robust`, or `heterogeneity`.

## Decision Rules

- Ask the user when the dependent variable, key explanatory variable, panel id, time variable, or dataset choice cannot be inferred with reasonable confidence.
- Do not silently change the econometric method requested by the user.
- Do not claim a regression has been run unless Stata MCP has actually executed it.
- If Stata returns an error, treat the task as unfinished until the script is corrected or the blocking ambiguity is surfaced to the user.

## Reference Files

- Read [references/workflow.md](references/workflow.md) for a fuller execution checklist and output expectations.
- Read [references/do-template.md](references/do-template.md) when you need a concrete skeleton for the generated Stata script.
