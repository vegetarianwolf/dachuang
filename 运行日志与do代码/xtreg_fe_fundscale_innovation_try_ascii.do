version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "C:/Users/Joe，/OneDrive/Desktop/dachuang/staging_ascii/panel_2015_2024_regression_ascii.csv"
local outdir "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"
local basename "xtreg_fe_fundscale_innovation_try_ascii"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)

encode city, gen(city_id)
destring year, replace force

duplicates tag city year, gen(dup_tag)
sort city year
collapse (firstnm) ///
    fund_est_count fund_est_scale fund_est_count_cum fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_design_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_design_apply ln_pat_apply_total, ///
    by(city year city_id)

xtset city_id year

local xvars ///
    fund_est_count ///
    fund_est_scale ///
    fund_est_count_cum ///
    fund_est_scale_cum

local yvars ///
    pat_invent_apply ///
    pat_utility_apply ///
    pat_design_apply ///
    pat_apply_total ///
    ln_pat_invent_apply ///
    ln_pat_utility_apply ///
    ln_pat_design_apply ///
    ln_pat_apply_total

tempname posth
tempfile results
postfile `posth' str40 yvar str40 xvar double b se t p N using `results', replace

foreach y of local yvars {
    foreach x of local xvars {
        preserve
        keep if !missing(`y', `x', city_id, year)
        quietly xtreg `y' `x' i.year, fe vce(cluster city_id)
        if _rc == 0 {
            local b = _b[`x']
            local se = _se[`x']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            local N = e(N)
            post `posth' ("`y'") ("`x'") (`b') (`se') (`t') (`p') (`N')
            di as text "----------------------------------------"
            di as result "y = `y' ; x = `x'"
            di as result "coef = " %9.6f `b' " , se = " %9.6f `se' " , p = " %9.6f `p' " , N = " %9.0f `N'
        }
        else {
            di as error "Regression failed: y=`y' x=`x'"
        }
        restore
    }
}

postclose `posth'
use `results', clear
sort yvar xvar
export delimited using "`resultcsv'", replace
list, sepby(yvar)

log close
