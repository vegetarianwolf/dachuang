version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_mechanism_finance_dualmodel_ascii"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    loan_balance_yearend deposit_balance_yearend gdp_finance_src ///
    fin_dev_1 fin_dev_2 ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)
gen ln_loan_balance = ln(loan_balance_yearend + 1)
gen ln_deposit_balance = ln(deposit_balance_yearend + 1)
gen ln_gdp_finance_src = ln(gdp_finance_src + 1)

xtset city_id year

tempfile panel
save `panel', replace

local xvar fund_est_scale_cum

local yvars ///
    pat_invent_apply ///
    pat_utility_apply ///
    pat_apply_total

local dvars ///
    debt_pressure ///
    debt_pressure_l1

local financevars ///
    fin_dev_1 ///
    fin_dev_2 ///
    ln_loan_balance ///
    ln_deposit_balance ///
    ln_gdp_finance_src

local ctrls ///
    ln_gdp ///
    ln_fiscal_scitech ///
    ln_pop ///
    ln_secondary ///
    ln_fdi

local ctrlmiss ///
    ln_gdp, ///
    ln_fiscal_scitech, ///
    ln_pop, ///
    ln_secondary, ///
    ln_fdi

tempname posth
tempfile results
postfile `posth' ///
    str18 model_family ///
    str6 spec ///
    str8 step ///
    str20 yvar ///
    str20 xvar ///
    str18 dvar ///
    str24 mvar ///
    str30 term1 ///
    double b1 se1 p1 ///
    str30 term2 ///
    double b2 se2 p2 ///
    str30 term3 ///
    double b3 se3 p3 ///
    double N r2w using `results', replace

foreach spec in noctrl ctrl {

    local ctrl_part ""
    if "`spec'" == "ctrl" {
        local ctrl_part "`ctrls'"
    }

    foreach d of local dvars {

        * Baseline moderation: Y = X + D + X#D + FE
        foreach y of local yvars {
            use `panel', clear
            xtset city_id year
            if "`spec'" == "ctrl" {
                keep if !missing(`y', `xvar', `d', `ctrlmiss', city_id, year)
            }
            else {
                keep if !missing(`y', `xvar', `d', city_id, year)
            }
            capture noisily xtreg `y' c.`xvar'##c.`d' `ctrl_part' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local b_xd = _b[c.`xvar'#c.`d']
                local se_xd = _se[c.`xvar'#c.`d']
                local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                post `posth' ///
                    ("baseline") ("`spec'") ("Y_eq") ///
                    ("`y'") ("`xvar'") ("`d'") ("") ///
                    ("`xvar'#`d'") (`b_xd') (`se_xd') (`p_xd') ///
                    ("") (.) (.) (.) ///
                    ("") (.) (.) (.) ///
                    (e(N)) (e(r2_w))
            }
        }

        foreach m of local financevars {

            * Model A: finance variable as mediator of the moderation effect
            use `panel', clear
            xtset city_id year
            if "`spec'" == "ctrl" {
                keep if !missing(`m', `xvar', `d', `ctrlmiss', city_id, year)
            }
            else {
                keep if !missing(`m', `xvar', `d', city_id, year)
            }
            capture noisily xtreg `m' c.`xvar'##c.`d' `ctrl_part' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local b_xd = _b[c.`xvar'#c.`d']
                local se_xd = _se[c.`xvar'#c.`d']
                local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                post `posth' ///
                    ("mediated") ("`spec'") ("M_eq") ///
                    ("") ("`xvar'") ("`d'") ("`m'") ///
                    ("`xvar'#`d'") (`b_xd') (`se_xd') (`p_xd') ///
                    ("") (.) (.) (.) ///
                    ("") (.) (.) (.) ///
                    (e(N)) (e(r2_w))
            }

            foreach y of local yvars {
                use `panel', clear
                xtset city_id year
                if "`spec'" == "ctrl" {
                    keep if !missing(`y', `m', `xvar', `d', `ctrlmiss', city_id, year)
                }
                else {
                    keep if !missing(`y', `m', `xvar', `d', city_id, year)
                }
                capture noisily xtreg `y' c.`xvar'##c.`d' `m' `ctrl_part' i.year, fe vce(cluster city_id)
                if _rc == 0 {
                    local b_xd = _b[c.`xvar'#c.`d']
                    local se_xd = _se[c.`xvar'#c.`d']
                    local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                    local b_m = _b[`m']
                    local se_m = _se[`m']
                    local p_m = 2 * ttail(e(df_r), abs(`b_m' / `se_m'))
                    post `posth' ///
                        ("mediated") ("`spec'") ("Y_eq") ///
                        ("`y'") ("`xvar'") ("`d'") ("`m'") ///
                        ("`xvar'#`d'") (`b_xd') (`se_xd') (`p_xd') ///
                        ("`m'") (`b_m') (`se_m') (`p_m') ///
                        ("") (.) (.) (.) ///
                        (e(N)) (e(r2_w))
                }
            }

            * Model B: finance variable as moderator carrying the debt-pressure mechanism
            use `panel', clear
            xtset city_id year
            if "`spec'" == "ctrl" {
                keep if !missing(`m', `xvar', `d', `ctrlmiss', city_id, year)
            }
            else {
                keep if !missing(`m', `xvar', `d', city_id, year)
            }
            capture noisily xtreg `m' `xvar' `d' `ctrl_part' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local b_d = _b[`d']
                local se_d = _se[`d']
                local p_d = 2 * ttail(e(df_r), abs(`b_d' / `se_d'))
                local b_x = _b[`xvar']
                local se_x = _se[`xvar']
                local p_x = 2 * ttail(e(df_r), abs(`b_x' / `se_x'))
                post `posth' ///
                    ("moderator") ("`spec'") ("M_eq") ///
                    ("") ("`xvar'") ("`d'") ("`m'") ///
                    ("`d'") (`b_d') (`se_d') (`p_d') ///
                    ("`xvar'") (`b_x') (`se_x') (`p_x') ///
                    ("") (.) (.) (.) ///
                    (e(N)) (e(r2_w))
            }

            foreach y of local yvars {
                use `panel', clear
                xtset city_id year
                if "`spec'" == "ctrl" {
                    keep if !missing(`y', `m', `xvar', `d', `ctrlmiss', city_id, year)
                }
                else {
                    keep if !missing(`y', `m', `xvar', `d', city_id, year)
                }
                capture noisily xtreg `y' c.`xvar'##c.`d' `m' c.`xvar'#c.`m' `ctrl_part' i.year, fe vce(cluster city_id)
                if _rc == 0 {
                    local b_xd = _b[c.`xvar'#c.`d']
                    local se_xd = _se[c.`xvar'#c.`d']
                    local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                    local b_m = _b[`m']
                    local se_m = _se[`m']
                    local p_m = 2 * ttail(e(df_r), abs(`b_m' / `se_m'))
                    local b_xm = _b[c.`xvar'#c.`m']
                    local se_xm = _se[c.`xvar'#c.`m']
                    local p_xm = 2 * ttail(e(df_r), abs(`b_xm' / `se_xm'))
                    post `posth' ///
                        ("moderator") ("`spec'") ("Y_eq") ///
                        ("`y'") ("`xvar'") ("`d'") ("`m'") ///
                        ("`xvar'#`d'") (`b_xd') (`se_xd') (`p_xd') ///
                        ("`m'") (`b_m') (`se_m') (`p_m') ///
                        ("`xvar'#`m'") (`b_xm') (`se_xm') (`p_xm') ///
                        (e(N)) (e(r2_w))
                }
            }
        }
    }
}

postclose `posth'
use `results', clear
export delimited using "`resultcsv'", replace

di "resultcsv = `resultcsv'"
log close
