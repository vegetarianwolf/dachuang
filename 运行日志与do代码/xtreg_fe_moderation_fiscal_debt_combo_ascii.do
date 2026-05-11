version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"
local basename "xtreg_fe_moderation_fiscal_debt_combo_ascii"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)

encode city, gen(city_id)
destring year, replace force

duplicates tag city year, gen(dup_tag)
sort city year
collapse (firstnm) ///
    fund_est_count fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    fiscal_pressure fiscal_pressure_l1 debt_pressure debt_pressure_l1 ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)

xtset city_id year

local yvars ///
    pat_invent_apply ///
    pat_utility_apply ///
    pat_apply_total

local xvars ///
    fund_est_count ///
    fund_est_scale_cum

local mvars ///
    fiscal_pressure ///
    fiscal_pressure_l1 ///
    debt_pressure ///
    debt_pressure_l1

local ctrls ///
    ln_gdp ///
    ln_fiscal_scitech ///
    ln_pop ///
    ln_secondary ///
    ln_fdi

tempname posth
tempfile results
postfile `posth' str30 yvar str25 xvar str20 mvar str12 spec ///
    double bx bm bint seint pint N r2w using `results', replace

foreach y of local yvars {
    foreach x of local xvars {
        foreach m of local mvars {
            import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
            encode city, gen(city_id)
            destring year, replace force
            duplicates tag city year, gen(dup_tag)
            sort city year
            collapse (firstnm) ///
                fund_est_count fund_est_scale_cum ///
                pat_invent_apply pat_utility_apply pat_apply_total ///
                fiscal_pressure fiscal_pressure_l1 debt_pressure debt_pressure_l1 ///
                gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
                by(city year city_id)
            gen ln_gdp = ln(gdp + 1)
            gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
            gen ln_pop = ln(population_resident + 1)
            gen ln_secondary = ln(secondary_industry + 1)
            gen ln_fdi = ln(fdi_actual + 1)
            xtset city_id year

            keep if !missing(`y', `x', `m', city_id, year)
            quietly xtreg `y' c.`x'##c.`m' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local bx = _b[`x']
                local bm = _b[`m']
                local bint = _b[c.`x'#c.`m']
                local seint = _se[c.`x'#c.`m']
                local tint = `bint' / `seint'
                local pint = 2 * ttail(e(df_r), abs(`tint'))
                local N = e(N)
                local r2w = e(r2_w)
                post `posth' ("`y'") ("`x'") ("`m'") ("noctrl") (`bx') (`bm') (`bint') (`seint') (`pint') (`N') (`r2w')
                di as text "----------------------------------------"
                di as result "y = `y' ; x = `x' ; m = `m' ; spec = noctrl"
                di as result "interaction coef = " %10.6f `bint' " , se = " %10.6f `seint' " , p = " %10.6f `pint' " , N = " %9.0f `N'
            }

            import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
            encode city, gen(city_id)
            destring year, replace force
            duplicates tag city year, gen(dup_tag)
            sort city year
            collapse (firstnm) ///
                fund_est_count fund_est_scale_cum ///
                pat_invent_apply pat_utility_apply pat_apply_total ///
                fiscal_pressure fiscal_pressure_l1 debt_pressure debt_pressure_l1 ///
                gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
                by(city year city_id)
            gen ln_gdp = ln(gdp + 1)
            gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
            gen ln_pop = ln(population_resident + 1)
            gen ln_secondary = ln(secondary_industry + 1)
            gen ln_fdi = ln(fdi_actual + 1)
            xtset city_id year

            keep if !missing(`y', `x', `m', ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi, city_id, year)
            quietly xtreg `y' c.`x'##c.`m' `ctrls' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local bx = _b[`x']
                local bm = _b[`m']
                local bint = _b[c.`x'#c.`m']
                local seint = _se[c.`x'#c.`m']
                local tint = `bint' / `seint'
                local pint = 2 * ttail(e(df_r), abs(`tint'))
                local N = e(N)
                local r2w = e(r2_w)
                post `posth' ("`y'") ("`x'") ("`m'") ("ctrl") (`bx') (`bm') (`bint') (`seint') (`pint') (`N') (`r2w')
                di as text "----------------------------------------"
                di as result "y = `y' ; x = `x' ; m = `m' ; spec = ctrl"
                di as result "interaction coef = " %10.6f `bint' " , se = " %10.6f `seint' " , p = " %10.6f `pint' " , N = " %9.0f `N'
            }
        }
    }
}

postclose `posth'
use `results', clear
sort yvar xvar mvar spec
export delimited using "`resultcsv'", replace
list, sepby(yvar)

log close
