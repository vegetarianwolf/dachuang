version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang"
local datafile "`root'/staging_ascii/formal_2015_en.csv"
local outdir "`root'/dachuang/运行日志与do代码"
local basename "xtreg_mediation_findev_step42_positive_focused_20260518"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"
local selectedcsv "`outdir'/`basename'_selected.csv"

log using "`logfile'", replace text

di "Task: focused Step 4.2 result equation for financial-development mediation."
di "Each result equation includes X, D, X*D, M, FE, and clustered SE."

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    fin_dev_1 fin_dev_2 ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen double ln_fund = ln(fund_est_scale_cum + 1)
gen double ln_debt_pressure = ln(debt_pressure + 1)
gen double ln_debt_pressure_l1 = ln(debt_pressure_l1 + 1)

gen double ln_fin_dev_1 = ln(fin_dev_1 + 1)
gen double ln_fin_dev_2 = ln(fin_dev_2 + 1)
gen double asinh_fin_dev_2 = asinh(fin_dev_2)

gen double lny_invent = ln(pat_invent_apply + 1)
gen double lny_utility = ln(pat_utility_apply + 1)
gen double lny_total = ln(pat_apply_total + 1)

gen double ln_gdp = ln(gdp + 1)
gen double ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen double ln_pop = ln(population_resident + 1)
gen double ln_secondary = ln(secondary_industry + 1)
gen double ln_fdi = ln(fdi_actual + 1)

capture program drop winsor_gen
program define winsor_gen
    syntax varname, GEN(name)
    quietly summarize `varlist', detail
    scalar p1_tmp = r(p1)
    scalar p99_tmp = r(p99)
    gen double `gen' = `varlist'
    replace `gen' = p1_tmp if `gen' < p1_tmp & !missing(`gen')
    replace `gen' = p99_tmp if `gen' > p99_tmp & !missing(`gen')
end

capture program drop z_gen
program define z_gen
    syntax varname, GEN(name)
    quietly summarize `varlist'
    gen double `gen' = (`varlist' - r(mean)) / r(sd) if !missing(`varlist')
end

winsor_gen fund_est_scale_cum, gen(w_fund_est_scale_cum)
winsor_gen ln_fund, gen(w_ln_fund)
winsor_gen debt_pressure, gen(w_debt_pressure)
winsor_gen debt_pressure_l1, gen(w_debt_pressure_l1)
winsor_gen ln_debt_pressure, gen(w_ln_debt_pressure)
winsor_gen ln_debt_pressure_l1, gen(w_ln_debt_pressure_l1)
winsor_gen fin_dev_2, gen(w_fin_dev_2)
winsor_gen ln_fin_dev_2, gen(w_ln_fin_dev_2)
winsor_gen pat_invent_apply, gen(w_pat_invent_apply)
winsor_gen pat_utility_apply, gen(w_pat_utility_apply)
winsor_gen pat_apply_total, gen(w_pat_apply_total)

foreach v in fund_est_scale_cum ln_fund w_fund_est_scale_cum w_ln_fund ///
    debt_pressure debt_pressure_l1 ln_debt_pressure ln_debt_pressure_l1 ///
    w_debt_pressure w_debt_pressure_l1 w_ln_debt_pressure w_ln_debt_pressure_l1 ///
    fin_dev_2 ln_fin_dev_2 asinh_fin_dev_2 w_fin_dev_2 w_ln_fin_dev_2 {
    z_gen `v', gen(z_`v')
}

xtset city_id year

gen double d_fin_dev_1 = D.fin_dev_1
gen double d_ln_fin_dev_1 = D.ln_fin_dev_1
gen double d_fin_dev_2 = D.fin_dev_2
gen double d_ln_fin_dev_2 = D.ln_fin_dev_2

winsor_gen d_ln_fin_dev_1, gen(w_d_ln_fin_dev_1)
winsor_gen d_ln_fin_dev_2, gen(w_d_ln_fin_dev_2)
foreach v in d_fin_dev_1 d_ln_fin_dev_1 d_fin_dev_2 d_ln_fin_dev_2 w_d_ln_fin_dev_1 w_d_ln_fin_dev_2 {
    z_gen `v', gen(z_`v')
}

tempfile panel
save `panel', replace

local ctrls ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi
local ctrlmiss ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi

tempname posth
tempfile results
postfile `posth' ///
    str8 spec str20 path str18 xform str24 xvar str18 dform str24 dvar ///
    str34 mtransform str16 meaning str24 mvar ///
    str12 yform str12 yrole str24 yvar ///
    double a_xd se_a p_a ///
    double beta_xd se_beta p_beta ///
    double c_xd se_cxd p_cxd ///
    double c_m se_m p_m ///
    double attenuation N r2_m r2_base r2_y ///
    using `results', replace

foreach spec in ctrl noctrl {
    local ctrl_part ""
    if "`spec'" == "ctrl" {
        local ctrl_part "`ctrls'"
    }

    foreach path in fd2_level_raw fd2_log_raw fd2_asinh_raw fd2_log_logfund fd2_asinh_logfund fd1_dlog_logfund fd1_dlog_wzraw fd2_dlog_wzraw {

        if "`path'" == "fd2_level_raw" {
            local xform rawfund
            local xvar fund_est_scale_cum
            local dform ln_debt_l1
            local dvar ln_debt_pressure_l1
            local mtransform fd2_level
            local meaning same_direction
            local mvar fin_dev_2
        }
        if "`path'" == "fd2_log_raw" {
            local xform rawfund
            local xvar fund_est_scale_cum
            local dform ln_debt_l1
            local dvar ln_debt_pressure_l1
            local mtransform fd2_log
            local meaning same_direction
            local mvar ln_fin_dev_2
        }
        if "`path'" == "fd2_asinh_raw" {
            local xform rawfund
            local xvar fund_est_scale_cum
            local dform ln_debt_l1
            local dvar ln_debt_pressure_l1
            local mtransform fd2_asinh
            local meaning same_direction
            local mvar asinh_fin_dev_2
        }
        if "`path'" == "fd2_log_logfund" {
            local xform logfund
            local xvar ln_fund
            local dform ln_debt_l1
            local dvar ln_debt_pressure_l1
            local mtransform fd2_log
            local meaning same_direction
            local mvar ln_fin_dev_2
        }
        if "`path'" == "fd2_asinh_logfund" {
            local xform logfund
            local xvar ln_fund
            local dform ln_debt_l1
            local dvar ln_debt_pressure_l1
            local mtransform fd2_asinh
            local meaning same_direction
            local mvar asinh_fin_dev_2
        }
        if "`path'" == "fd1_dlog_logfund" {
            local xform logfund
            local xvar ln_fund
            local dform ln_debt_l1
            local dvar ln_debt_pressure_l1
            local mtransform fd1_dlog
            local meaning change
            local mvar d_ln_fin_dev_1
        }
        if "`path'" == "fd1_dlog_wzraw" {
            local xform wz_rawfund
            local xvar z_w_fund_est_scale_cum
            local dform ln_debt
            local dvar ln_debt_pressure
            local mtransform fd1_dlog
            local meaning change
            local mvar d_ln_fin_dev_1
        }
        if "`path'" == "fd2_dlog_wzraw" {
            local xform wz_rawfund
            local xvar z_w_fund_est_scale_cum
            local dform debt
            local dvar debt_pressure
            local mtransform fd2_dlog
            local meaning change
            local mvar d_ln_fin_dev_2
        }

        foreach yform in count logy wcount {
            foreach yrole in invent utility total {
                if "`yform'" == "count" & "`yrole'" == "invent" {
                    local yvar pat_invent_apply
                }
                if "`yform'" == "count" & "`yrole'" == "utility" {
                    local yvar pat_utility_apply
                }
                if "`yform'" == "count" & "`yrole'" == "total" {
                    local yvar pat_apply_total
                }
                if "`yform'" == "logy" & "`yrole'" == "invent" {
                    local yvar lny_invent
                }
                if "`yform'" == "logy" & "`yrole'" == "utility" {
                    local yvar lny_utility
                }
                if "`yform'" == "logy" & "`yrole'" == "total" {
                    local yvar lny_total
                }
                if "`yform'" == "wcount" & "`yrole'" == "invent" {
                    local yvar w_pat_invent_apply
                }
                if "`yform'" == "wcount" & "`yrole'" == "utility" {
                    local yvar w_pat_utility_apply
                }
                if "`yform'" == "wcount" & "`yrole'" == "total" {
                    local yvar w_pat_apply_total
                }

                use `panel', clear
                xtset city_id year
                if "`spec'" == "ctrl" {
                    keep if !missing(`yvar', `mvar', `xvar', `dvar', `ctrlmiss', city_id, year)
                }
                else {
                    keep if !missing(`yvar', `mvar', `xvar', `dvar', city_id, year)
                }
                quietly count
                if r(N) < 100 {
                    continue
                }

                * Step 4.1: mechanism equation, includes X, D, X*D.
                capture noisily xtreg `mvar' c.`xvar'##c.`dvar' `ctrl_part' i.year, fe vce(cluster city_id)
                if _rc != 0 {
                    continue
                }
                scalar a_xd = _b[c.`xvar'#c.`dvar']
                scalar se_a = _se[c.`xvar'#c.`dvar']
                scalar p_a = 2 * ttail(e(df_r), abs(a_xd / se_a))
                scalar r2_m = e(r2_w)

                * Baseline result equation, includes X, D, X*D.
                capture noisily xtreg `yvar' c.`xvar'##c.`dvar' `ctrl_part' i.year, fe vce(cluster city_id)
                if _rc != 0 {
                    continue
                }
                scalar beta_xd = _b[c.`xvar'#c.`dvar']
                scalar se_beta = _se[c.`xvar'#c.`dvar']
                scalar p_beta = 2 * ttail(e(df_r), abs(beta_xd / se_beta))
                scalar r2_base = e(r2_w)

                * Step 4.2 result equation, includes X, D, X*D, and M.
                capture noisily xtreg `yvar' c.`xvar'##c.`dvar' `mvar' `ctrl_part' i.year, fe vce(cluster city_id)
                if _rc != 0 {
                    continue
                }
                scalar c_xd = _b[c.`xvar'#c.`dvar']
                scalar se_cxd = _se[c.`xvar'#c.`dvar']
                scalar p_cxd = 2 * ttail(e(df_r), abs(c_xd / se_cxd))
                scalar c_m = _b[`mvar']
                scalar se_m = _se[`mvar']
                scalar p_m = 2 * ttail(e(df_r), abs(c_m / se_m))
                scalar r2_y = e(r2_w)
                scalar attenuation = (abs(beta_xd) - abs(c_xd)) / abs(beta_xd)

                post `posth' ///
                    ("`spec'") ("`path'") ("`xform'") ("`xvar'") ("`dform'") ("`dvar'") ///
                    ("`mtransform'") ("`meaning'") ("`mvar'") ///
                    ("`yform'") ("`yrole'") ("`yvar'") ///
                    (a_xd) (se_a) (p_a) ///
                    (beta_xd) (se_beta) (p_beta) ///
                    (c_xd) (se_cxd) (p_cxd) ///
                    (c_m) (se_m) (p_m) ///
                    (attenuation) (e(N)) (r2_m) (r2_base) (r2_y)
            }
        }
    }
}

postclose `posth'

use `results', clear
gen byte first_neg10 = a_xd < 0 & p_a < 0.10
gen byte first_neg05 = a_xd < 0 & p_a < 0.05
gen byte m_pos10 = c_m > 0 & p_m < 0.10
gen byte m_pos05 = c_m > 0 & p_m < 0.05
gen byte m_pos01 = c_m > 0 & p_m < 0.01
gen byte chain10 = first_neg10 == 1 & m_pos10 == 1
gen byte chain05 = first_neg05 == 1 & m_pos05 == 1
order spec path xform xvar dform dvar mtransform meaning mvar yform yrole yvar ///
    a_xd se_a p_a beta_xd se_beta p_beta c_xd se_cxd p_cxd c_m se_m p_m ///
    attenuation N r2_m r2_base r2_y first_neg10 first_neg05 m_pos10 m_pos05 m_pos01 chain10 chain05
export delimited using "`resultcsv'", replace

preserve
keep if chain10 == 1
sort spec meaning mtransform yform yrole p_m p_a
export delimited using "`selectedcsv'", replace
restore

quietly count
di "Focused Step 4.2 paths estimated: " r(N)
quietly count if chain10 == 1
di "Negative first-stage plus positive Step 4.2 chains p<0.10: " r(N)
quietly count if chain05 == 1
di "Negative first-stage plus positive Step 4.2 chains p<0.05: " r(N)
quietly count if chain05 == 1 & spec == "ctrl"
di "Controlled chains p<0.05: " r(N)
di "Full result CSV: `resultcsv'"
di "Selected chain CSV: `selectedcsv'"

log close
