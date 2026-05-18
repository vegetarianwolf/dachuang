version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_soccap_theory_chain_no_log_20260518"
local logfile "`outdir'/`basename'.log"
local allcsv "`outdir'/`basename'_all_results.csv"
local selectedcsv "`outdir'/`basename'_theory_consistent.csv"

log using "`logfile'", replace text

di "Task: theory-consistent social-capital mechanism scan, no log transform on fund size or soccap leverage"
di "Data: `datafile'"

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

local numeric_vars ///
    fund_est_scale fund_est_scale_cum fund_est_scale_roll5 ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    soccap_share_total gov_share_total soccap_leverage ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual ///
    fin_dev marketization

foreach v of local numeric_vars {
    capture confirm variable `v'
    if !_rc {
        capture confirm string variable `v'
        if !_rc {
            replace `v' = "" if inlist(strtrim(`v'), "NA", "N/A", "nan", "NaN", "--", "null")
            destring `v', replace ignore(", %") force
        }
    }
}

collapse (firstnm) ///
    fund_est_scale fund_est_scale_cum fund_est_scale_roll5 ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    soccap_share_total gov_share_total soccap_leverage ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual ///
    fin_dev marketization, ///
    by(city year city_id)

foreach v in soccap_share_total gov_share_total {
    replace `v' = . if !missing(`v') & (`v' < 0 | `v' > 1)
}
replace soccap_leverage = . if !missing(soccap_leverage) & soccap_leverage < 0

gen nongov_share_total = 1 - gov_share_total if !missing(gov_share_total)

gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)

foreach v in soccap_leverage soccap_share_total nongov_share_total {
    gen `v'_w = `v'
    quietly summarize `v' if !missing(`v'), detail
    if r(N) > 0 {
        local p1 = r(p1)
        local p99 = r(p99)
        replace `v'_w = `p1' if !missing(`v'_w) & `v'_w < `p1'
        replace `v'_w = `p99' if !missing(`v'_w) & `v'_w > `p99'
    }

    gen `v'_zero = `v'
    replace `v'_zero = 0 if missing(`v'_zero)
    gen `v'_zero_w = `v'_zero
    quietly summarize `v'_zero if !missing(`v'_zero), detail
    if r(N) > 0 {
        local p1 = r(p1)
        local p99 = r(p99)
        replace `v'_zero_w = `p1' if !missing(`v'_zero_w) & `v'_zero_w < `p1'
        replace `v'_zero_w = `p99' if !missing(`v'_zero_w) & `v'_zero_w > `p99'
    }
}

xtset city_id year
foreach v in soccap_leverage_zero_w soccap_share_total_zero_w nongov_share_total_zero_w {
    gen L1_`v' = L.`v'
}

tempfile panel
save `panel', replace

local xvars ///
    fund_est_scale_cum ///
    fund_est_scale_roll5

local dvars ///
    debt_pressure ///
    debt_pressure_l1

local mvars ///
    soccap_leverage ///
    soccap_leverage_w ///
    soccap_leverage_zero_w ///
    L1_soccap_leverage_zero_w ///
    soccap_share_total ///
    soccap_share_total_zero_w ///
    L1_soccap_share_total_zero_w ///
    nongov_share_total_zero_w ///
    L1_nongov_share_total_zero_w

local yvars ///
    pat_invent_apply ///
    pat_utility_apply ///
    pat_apply_total ///
    ln_pat_invent_apply ///
    ln_pat_utility_apply ///
    ln_pat_apply_total

tempname posth
tempfile results
postfile `posth' ///
    str24 sample ///
    str12 spec ///
    str24 xvar ///
    str18 dvar ///
    str32 mvar ///
    str24 yvar ///
    double b_debt se_debt p_debt N_m r2w_m ///
    double b_m se_m p_m N_y r2w_y using `results', replace

local samples all post2016 through2023 post2016_through2023 active_cum active_cum_2016_2023 no2020 no2020_through2023
local specs noctrl basic full

foreach sample of local samples {

    local samplecond "1"
    if "`sample'" == "post2016" local samplecond "year>=2016"
    if "`sample'" == "through2023" local samplecond "year<=2023"
    if "`sample'" == "post2016_through2023" local samplecond "year>=2016 & year<=2023"
    if "`sample'" == "active_cum" local samplecond "fund_est_scale_cum>0"
    if "`sample'" == "active_cum_2016_2023" local samplecond "fund_est_scale_cum>0 & year>=2016 & year<=2023"
    if "`sample'" == "no2020" local samplecond "year!=2020"
    if "`sample'" == "no2020_through2023" local samplecond "year!=2020 & year<=2023"

    foreach spec of local specs {

        local ctrl_part ""
        local ctrlmiss ""
        if "`spec'" == "basic" {
            local ctrl_part "ln_gdp ln_pop"
            local ctrlmiss "ln_gdp, ln_pop"
        }
        if "`spec'" == "full" {
            local ctrl_part "ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi fin_dev marketization"
            local ctrlmiss "ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi, fin_dev, marketization"
        }

        foreach x of local xvars {
            foreach d of local dvars {
                foreach m of local mvars {

                    use `panel', clear
                    xtset city_id year
                    keep if `samplecond'
                    if "`spec'" == "noctrl" {
                        keep if !missing(`m', `x', `d', city_id, year)
                    }
                    else {
                        keep if !missing(`m', `x', `d', `ctrlmiss', city_id, year)
                    }

                    local b_debt = .
                    local se_debt = .
                    local p_debt = .
                    local N_m = .
                    local r2w_m = .

                    capture quietly xtreg `m' `x' `d' `ctrl_part' i.year, fe vce(cluster city_id)
                    if _rc == 0 {
                        capture local b_debt = _b[`d']
                        if _rc == 0 {
                            local se_debt = _se[`d']
                            if `se_debt' > 0 & `se_debt' < . {
                                local p_debt = 2 * ttail(e(df_r), abs(`b_debt' / `se_debt'))
                            }
                            local N_m = e(N)
                            local r2w_m = e(r2_w)
                        }
                    }

                    foreach y of local yvars {
                        use `panel', clear
                        xtset city_id year
                        keep if `samplecond'
                        if "`spec'" == "noctrl" {
                            keep if !missing(`y', `m', `x', `d', city_id, year)
                        }
                        else {
                            keep if !missing(`y', `m', `x', `d', `ctrlmiss', city_id, year)
                        }

                        capture quietly xtreg `y' `x' `d' `m' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_m = _b[`m']
                            if _rc == 0 {
                                local se_m = _se[`m']
                                local p_m = .
                                if `se_m' > 0 & `se_m' < . {
                                    local p_m = 2 * ttail(e(df_r), abs(`b_m' / `se_m'))
                                }
                                post `posth' ///
                                    ("`sample'") ("`spec'") ("`x'") ("`d'") ("`m'") ("`y'") ///
                                    (`b_debt') (`se_debt') (`p_debt') (`N_m') (`r2w_m') ///
                                    (`b_m') (`se_m') (`p_m') (e(N)) (e(r2_w))
                            }
                        }
                    }
                }
            }
        }
    }
}

postclose `posth'
use `results', clear

gen mech_ok10 = b_debt < 0 & p_debt < 0.1
gen y_ok10 = b_m > 0 & p_m < 0.1
gen chain_ok10 = mech_ok10 & y_ok10
gen mech_ok05 = b_debt < 0 & p_debt < 0.05
gen y_ok05 = b_m > 0 & p_m < 0.05
gen chain_ok05 = mech_ok05 & y_ok05

gen sig_debt = ""
replace sig_debt = "***" if p_debt < 0.01
replace sig_debt = "**" if p_debt >= 0.01 & p_debt < 0.05
replace sig_debt = "*" if p_debt >= 0.05 & p_debt < 0.1
gen sig_m = ""
replace sig_m = "***" if p_m < 0.01
replace sig_m = "**" if p_m >= 0.01 & p_m < 0.05
replace sig_m = "*" if p_m >= 0.05 & p_m < 0.1

sort chain_ok05 chain_ok10 sample spec xvar dvar mvar yvar
export delimited using "`allcsv'", replace

preserve
keep if chain_ok10 == 1
sort p_debt p_m sample spec xvar dvar mvar yvar
export delimited using "`selectedcsv'", replace
restore

di "All results: `allcsv'"
di "Theory-consistent results: `selectedcsv'"
di "Number of 10% theory-consistent chains:"
count if chain_ok10 == 1
di "Number of 5% theory-consistent chains:"
count if chain_ok05 == 1

log close
