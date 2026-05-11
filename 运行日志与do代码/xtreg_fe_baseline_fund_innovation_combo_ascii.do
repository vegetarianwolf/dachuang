version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "C:/Users/Joe，/OneDrive/Desktop/dachuang/staging_ascii/panel_2015_2024_regression_ascii.csv"
local outdir "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"
local basename "xtreg_fe_baseline_fund_innovation_combo_ascii"
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
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)

xtset city_id year

local xvars ///
    fund_est_count ///
    fund_est_scale ///
    fund_est_count_cum ///
    fund_est_scale_cum

local yvars ///
    pat_invent_apply ///
    pat_utility_apply ///
    pat_apply_total ///
    ln_pat_invent_apply ///
    ln_pat_utility_apply ///
    ln_pat_apply_total

local ctrls ///
    ln_gdp ///
    ln_fiscal_scitech ///
    ln_pop ///
    ln_secondary ///
    ln_fdi

tempname posth
tempfile results
postfile `posth' str40 yvar str40 xvar str12 spec double b se t p N r2w using `results', replace

foreach y of local yvars {
    foreach x of local xvars {
        import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
        encode city, gen(city_id)
        destring year, replace force
        duplicates tag city year, gen(dup_tag)
        sort city year
        collapse (firstnm) ///
            fund_est_count fund_est_scale fund_est_count_cum fund_est_scale_cum ///
            pat_invent_apply pat_utility_apply pat_apply_total ///
            ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
            gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
            by(city year city_id)
        gen ln_gdp = ln(gdp + 1)
        gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
        gen ln_pop = ln(population_resident + 1)
        gen ln_secondary = ln(secondary_industry + 1)
        gen ln_fdi = ln(fdi_actual + 1)
        xtset city_id year
        keep if !missing(`y', `x', city_id, year)
        quietly xtreg `y' `x' i.year, fe vce(cluster city_id)
        if _rc == 0 {
            local b = _b[`x']
            local se = _se[`x']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            local N = e(N)
            local r2w = e(r2_w)
            post `posth' ("`y'") ("`x'") ("noctrl") (`b') (`se') (`t') (`p') (`N') (`r2w')
            di as text "----------------------------------------"
            di as result "y = `y' ; x = `x' ; spec = noctrl"
            di as result "coef = " %10.6f `b' " , se = " %10.6f `se' " , p = " %10.6f `p' " , N = " %9.0f `N'
        }

        import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
        encode city, gen(city_id)
        destring year, replace force
        duplicates tag city year, gen(dup_tag)
        sort city year
        collapse (firstnm) ///
            fund_est_count fund_est_scale fund_est_count_cum fund_est_scale_cum ///
            pat_invent_apply pat_utility_apply pat_apply_total ///
            ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
            gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
            by(city year city_id)
        gen ln_gdp = ln(gdp + 1)
        gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
        gen ln_pop = ln(population_resident + 1)
        gen ln_secondary = ln(secondary_industry + 1)
        gen ln_fdi = ln(fdi_actual + 1)
        xtset city_id year
        keep if !missing(`y', `x', ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi, city_id, year)
        quietly xtreg `y' `x' `ctrls' i.year, fe vce(cluster city_id)
        if _rc == 0 {
            local b = _b[`x']
            local se = _se[`x']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            local N = e(N)
            local r2w = e(r2_w)
            post `posth' ("`y'") ("`x'") ("ctrl") (`b') (`se') (`t') (`p') (`N') (`r2w')
            di as text "----------------------------------------"
            di as result "y = `y' ; x = `x' ; spec = ctrl"
            di as result "coef = " %10.6f `b' " , se = " %10.6f `se' " , p = " %10.6f `p' " , N = " %9.0f `N'
        }
    }
}

postclose `posth'
use `results', clear
sort yvar xvar spec
export delimited using "`resultcsv'", replace
list, sepby(yvar)

log close
