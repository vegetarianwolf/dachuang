version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_mechanism_city_findev12_refined_20260516"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"
local selectedcsv "`outdir'/`basename'_selected.csv"

log using "`logfile'", replace text

di "Task: city-level financial development mechanism test; only fin_dev_1 and fin_dev_2 are used."
di "Data: `datafile'"

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    fin_dev_1 fin_dev_2 ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen ln_fund = ln(fund_est_scale_cum + 1)
gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)

xtset city_id year

di _n "Variable summary for the two allowed financial-development measures:"
summarize fin_dev_1 fin_dev_2 fund_est_scale_cum ln_fund debt_pressure debt_pressure_l1 ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total

tempfile panel
save `panel', replace

local xvars fund_est_scale_cum ln_fund
local yvars pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total
local dvars debt_pressure debt_pressure_l1
local mvars fin_dev_1 fin_dev_2
local ctrls ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi
local base_ok !missing(ln_gdp) & !missing(ln_fiscal_scitech) & !missing(ln_pop) & !missing(ln_secondary) & !missing(ln_fdi) & !missing(city_id) & !missing(year)

tempname posth
tempfile results
postfile `posth' ///
    str12 family str8 step str24 yvar str24 xvar str20 dvar str16 mvar str18 focus ///
    double b_focus se_focus p_focus ///
    double b_xd p_xd b_d p_d b_m p_m b_xm p_xm ///
    double N r2w ///
    using `results', replace

foreach x of local xvars {
    foreach d of local dvars {

        foreach y of local yvars {
            use `panel', clear
            xtset city_id year
            keep if !missing(`y') & !missing(`x') & !missing(`d') & `base_ok'
            capture noisily xtreg `y' c.`x'##c.`d' `ctrls' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                scalar b_xd = _b[c.`x'#c.`d']
                scalar se_xd = _se[c.`x'#c.`d']
                scalar p_xd = 2 * ttail(e(df_r), abs(b_xd / se_xd))
                post `posth' ///
                    ("baseline") ("Y_eq") ("`y'") ("`x'") ("`d'") ("") ("XxD") ///
                    (b_xd) (se_xd) (p_xd) ///
                    (b_xd) (p_xd) (.) (.) (.) (.) (.) (.) ///
                    (e(N)) (e(r2_w))
            }
        }

        foreach m of local mvars {

            use `panel', clear
            xtset city_id year
            keep if !missing(`m') & !missing(`x') & !missing(`d') & `base_ok'
            capture noisily xtreg `m' c.`x'##c.`d' `ctrls' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                scalar b_xd = _b[c.`x'#c.`d']
                scalar se_xd = _se[c.`x'#c.`d']
                scalar p_xd = 2 * ttail(e(df_r), abs(b_xd / se_xd))
                post `posth' ///
                    ("mediated") ("M_eq") ("") ("`x'") ("`d'") ("`m'") ("XxD") ///
                    (b_xd) (se_xd) (p_xd) ///
                    (b_xd) (p_xd) (.) (.) (.) (.) (.) (.) ///
                    (e(N)) (e(r2_w))
            }

            use `panel', clear
            xtset city_id year
            keep if !missing(`m') & !missing(`x') & !missing(`d') & `base_ok'
            capture noisily xtreg `m' `x' `d' `ctrls' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                scalar b_d = _b[`d']
                scalar se_d = _se[`d']
                scalar p_d = 2 * ttail(e(df_r), abs(b_d / se_d))
                post `posth' ///
                    ("moderator") ("M_eq") ("") ("`x'") ("`d'") ("`m'") ("D") ///
                    (b_d) (se_d) (p_d) ///
                    (.) (.) (b_d) (p_d) (.) (.) (.) (.) ///
                    (e(N)) (e(r2_w))
            }

            foreach y of local yvars {
                use `panel', clear
                xtset city_id year
                keep if !missing(`y') & !missing(`m') & !missing(`x') & !missing(`d') & `base_ok'
                capture noisily xtreg `y' c.`x'##c.`d' `m' `ctrls' i.year, fe vce(cluster city_id)
                if _rc == 0 {
                    scalar b_xd = _b[c.`x'#c.`d']
                    scalar se_xd = _se[c.`x'#c.`d']
                    scalar p_xd = 2 * ttail(e(df_r), abs(b_xd / se_xd))
                    scalar b_m = _b[`m']
                    scalar se_m = _se[`m']
                    scalar p_m = 2 * ttail(e(df_r), abs(b_m / se_m))
                    post `posth' ///
                        ("mediated") ("Y_eq") ("`y'") ("`x'") ("`d'") ("`m'") ("M") ///
                        (b_m) (se_m) (p_m) ///
                        (b_xd) (p_xd) (.) (.) (b_m) (p_m) (.) (.) ///
                        (e(N)) (e(r2_w))
                }

                use `panel', clear
                xtset city_id year
                keep if !missing(`y') & !missing(`m') & !missing(`x') & !missing(`d') & `base_ok'
                capture noisily xtreg `y' c.`x'##c.`d' `m' c.`x'#c.`m' `ctrls' i.year, fe vce(cluster city_id)
                if _rc == 0 {
                    scalar b_xd = _b[c.`x'#c.`d']
                    scalar se_xd = _se[c.`x'#c.`d']
                    scalar p_xd = 2 * ttail(e(df_r), abs(b_xd / se_xd))
                    scalar b_m = _b[`m']
                    scalar se_m = _se[`m']
                    scalar p_m = 2 * ttail(e(df_r), abs(b_m / se_m))
                    scalar b_xm = _b[c.`x'#c.`m']
                    scalar se_xm = _se[c.`x'#c.`m']
                    scalar p_xm = 2 * ttail(e(df_r), abs(b_xm / se_xm))
                    post `posth' ///
                        ("moderator") ("Y_eq") ("`y'") ("`x'") ("`d'") ("`m'") ("XxM") ///
                        (b_xm) (se_xm) (p_xm) ///
                        (b_xd) (p_xd) (.) (.) (b_m) (p_m) (b_xm) (p_xm) ///
                        (e(N)) (e(r2_w))
                }
            }
        }
    }
}

postclose `posth'
use `results', clear
gen sig_10 = p_focus < 0.1 if !missing(p_focus)
gen sig_5 = p_focus < 0.05 if !missing(p_focus)
gen sig_1 = p_focus < 0.01 if !missing(p_focus)
order family step yvar xvar dvar mvar focus b_focus se_focus p_focus b_xd p_xd b_d p_d b_m p_m b_xm p_xm N r2w sig_10 sig_5 sig_1
export delimited using "`resultcsv'", replace

preserve
keep if sig_10 == 1
sort family step mvar xvar dvar yvar p_focus
export delimited using "`selectedcsv'", replace
restore

di _n "Full result CSV: `resultcsv'"
di "Selected p<0.10 CSV: `selectedcsv'"

log close
