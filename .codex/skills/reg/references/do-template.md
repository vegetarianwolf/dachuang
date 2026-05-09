# Stata Do-File Template

Use this as a pattern, then tailor it to the actual dataset and user request.

```stata
version 18.0
clear all
set more off

local project_root "C:/path/to/project"
local data_file "`project_root'/面板数据/example.dta"
local out_dir "`project_root'/运行日志与do代码"
local run_name "xtreg_fe_y_x"
local log_file "`out_dir'/`run_name'.log"

capture log close
log using "`log_file'", replace text

use "`data_file'", clear

* Minimal preparation only when needed
* encode firm_id, gen(firm_id_num)
* destring year, replace force

xtset firm_id year

xtreg y x control1 control2 i.year, fe vce(cluster firm_id)

log close
```

## Notes

- Replace path separators with forms Stata accepts reliably.
- Use `use` for `.dta`.
- Use `import delimited` for `.csv`.
- Use `import excel` for `.xlsx` or `.xls`.
- Keep preprocessing minimal and explicit.
- If several models are required, store them clearly and keep the log open until all runs finish.
