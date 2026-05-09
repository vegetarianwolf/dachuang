# Reg Workflow

## Goal

Convert a user request about panel-data regression into:

1. A runnable Stata `.do` file saved under `运行日志与do代码`
2. A matching `.log` file saved in the same directory
3. A completed Stata MCP execution
4. A concise report that states what data, model, and outputs were used

## Directory Conventions

- Input data directory: `面板数据`
- Output directory: `运行日志与do代码`
- If the current workspace is not the project root, search upward or within the repo for these folders before asking the user.

## Dataset Selection Heuristics

1. Prefer `.dta` over imported formats.
2. If filenames mention the dependent variable, policy, or sample window from the request, prefer those matches.
3. If there are multiple candidate files and no clear winner, ask exactly one short question.

## Minimum Data Inspection

Before writing the final `.do` file, inspect enough to avoid hallucinated code:

- filename and extension
- variable names
- obvious panel id candidates such as `id`, `firm`, `code`, `stkcd`, `province`, `city`
- obvious time candidates such as `year`, `time`, `date`

If needed, use a short Stata probe such as `describe`, `ds`, `summarize`, or `codebook` before composing the final script.

## Output Naming Heuristics

Use actual variable names from the dataset whenever possible.

Recommended basename patterns:

- `xtreg_fe_<y>_<x>`
- `xtreg_re_<y>_<x>`
- `ols_<y>_<x>`
- `did_<y>_<treat>`
- `heterogeneity_<y>_<x>`
- `robust_<y>_<x>`

Append `_baseline`, `_robust`, `_mech`, or `_hetero` when the user asks for multiple related runs.

## Execution Standard

The workflow is not complete until `stata_run_file` has run the saved `.do` file.

If Stata errors:

1. Read the error carefully
2. Fix the `.do` file
3. Rerun it
4. Only stop to ask the user if the remaining blocker is conceptual or requires a modeling choice

## Reporting Standard

The final response should include:

- the dataset chosen
- the saved `.do` path
- the saved `.log` path
- whether the regression ran successfully
- the main estimation command used
- any unresolved warning that affects interpretation
