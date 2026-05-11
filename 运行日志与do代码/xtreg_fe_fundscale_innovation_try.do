version 18
clear all
set more off
capture log close

local root "C:\Users\Joe，\OneDrive\Desktop\dachuang\dachuang"
local datafile "`root'\面板数据\地级市总面板_2015_2024版.csv"
local outdir "`root'\运行日志与do代码"
local basename "xtreg_fe_fundscale_innovation_try"
local logfile "`outdir'\`basename'.log"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)

capture confirm variable 城市
if _rc {
    di as error "未找到城市变量"
    log close
    exit 198
}

capture confirm variable 年份
if _rc {
    di as error "未找到年份变量"
    log close
    exit 198
}

encode 城市, gen(city_id)
destring 年份, replace force

* Resolve a few duplicated city-year rows by collapsing identical keys.
duplicates tag 城市 年份, gen(dup_tag)
sort 城市 年份
collapse (firstnm) ///
    基金当年设立数量 基金当年设立规模_人民币万元 基金累计设立数量 基金累计设立规模_人民币万元 ///
    发明申请量 实用新型申请量 外观设计申请量 专利申请总量 ///
    发明申请量_对数 实用新型申请量_对数 外观设计申请量_对数 专利申请总量_对数, ///
    by(城市 年份 city_id)

xtset city_id 年份

local xvars ///
    基金当年设立数量 ///
    基金当年设立规模_人民币万元 ///
    基金累计设立数量 ///
    基金累计设立规模_人民币万元

local yvars ///
    发明申请量 ///
    实用新型申请量 ///
    外观设计申请量 ///
    专利申请总量 ///
    发明申请量_对数 ///
    实用新型申请量_对数 ///
    外观设计申请量_对数 ///
    专利申请总量_对数

tempname posth
tempfile results
postfile `posth' str40 yvar str40 xvar double b se t p N using `results', replace

foreach y of local yvars {
    foreach x of local xvars {
        preserve
        keep if !missing(`y', `x', city_id, 年份)
        quietly xtreg `y' `x' i.年份, fe vce(cluster city_id)
        if _rc == 0 {
            local b = _b[`x']
            local se = _se[`x']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            local N = e(N)
            post `posth' ("`y'") ("`x'") (`b') (`se') (`t') (`p') (`N')
            di as text "----------------------------------------"
            di as result "因变量: `y'  自变量: `x'"
            di as result "coef = " %9.4f `b' " , se = " %9.4f `se' " , p = " %9.4f `p' " , N = " %9.0f `N'
        }
        else {
            di as error "回归失败: y=`y' x=`x'"
        }
        restore
    }
}

postclose `posth'
use `results', clear
sort yvar xvar
export delimited using "`outdir'\`basename'_results.csv", replace
list, sepby(yvar)

log close
