version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_soccap_moderated_mechanism_lowfin_booster_20260518"
local logfile "`outdir'/`basename'.log"
local allcsv "`outdir'/`basename'_all_results.csv"
local selectedcsv "`outdir'/`basename'_theory_selected.csv"
local strictcsv "`outdir'/`basename'_strict_attenuated.csv"

log using "`logfile'", replace text

di "Task: low-finance focused booster for scheme2 social-capital moderation mechanism"
di "Restrictions: no log transform on fund scale or social-capital leverage variables"

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

local numeric_vars ///
    fund_est_scale_cum fund_est_scale_roll5 ///
    pat_utility_apply pat_apply_total ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 debt_burden debt_burden_l1 ///
    soccap_leverage gov_amt gdp fiscal_scitech population_resident ///
    secondary_industry fdi_actual fin_dev

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
    fund_est_scale_cum fund_est_scale_roll5 ///
    pat_utility_apply pat_apply_total ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 debt_burden debt_burden_l1 ///
    soccap_leverage gov_amt gdp fiscal_scitech population_resident ///
    secondary_industry fdi_actual fin_dev, ///
    by(city year city_id)

replace soccap_leverage = . if !missing(soccap_leverage) & soccap_leverage < 0
gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)

quietly summarize gov_amt if gov_amt > 0, detail
local gov_p5 = r(p5)
gen soccap_leverage_govp5 = soccap_leverage
replace soccap_leverage_govp5 = . if !missing(gov_amt) & gov_amt > 0 & gov_amt < `gov_p5'

foreach v in debt_pressure debt_pressure_l1 debt_burden debt_burden_l1 soccap_leverage soccap_leverage_govp5 {
    gen `v'_w = `v'
    quietly summarize `v' if !missing(`v'), detail
    if r(N) > 0 {
        local p1 = r(p1)
        local p99 = r(p99)
        replace `v'_w = `p1' if !missing(`v'_w) & `v'_w < `p1'
        replace `v'_w = `p99' if !missing(`v'_w) & `v'_w > `p99'
    }
}

gen soccap_leverage_zero_w = soccap_leverage
replace soccap_leverage_zero_w = 0 if missing(soccap_leverage_zero_w)
quietly summarize soccap_leverage_zero_w if !missing(soccap_leverage_zero_w), detail
local p1 = r(p1)
local p99 = r(p99)
replace soccap_leverage_zero_w = `p1' if !missing(soccap_leverage_zero_w) & soccap_leverage_zero_w < `p1'
replace soccap_leverage_zero_w = `p99' if !missing(soccap_leverage_zero_w) & soccap_leverage_zero_w > `p99'

xtset city_id year
foreach y in pat_utility_apply pat_apply_total ln_pat_utility_apply ln_pat_apply_total {
    gen F1_`y' = F.`y'
}
foreach v in soccap_leverage_w soccap_leverage_zero_w soccap_leverage_govp5_w {
    gen D1_`v' = D.`v'
}

quietly summarize fin_dev if !missing(fin_dev), detail
gen low_fin = fin_dev < r(p50) if !missing(fin_dev)

local xvars fund_est_scale_cum fund_est_scale_roll5
local dvars debt_pressure_l1 debt_pressure_l1_w debt_burden debt_burden_w debt_burden_l1 debt_burden_l1_w
local yvars pat_utility_apply pat_apply_total F1_pat_utility_apply F1_pat_apply_total ln_pat_utility_apply F1_ln_pat_utility_apply
local mvars soccap_leverage_govp5_w soccap_leverage_w soccap_leverage_zero_w D1_soccap_leverage_zero_w
local samples low_fin low_fin_no2020 low_fin_through2023 low_fin_active_cum
local specs noctrl ctrl5

tempname posth
tempfile results
postfile `posth' ///
    str22 scheme str24 sample str12 spec str24 xvar str24 dvar str40 mvar str28 yvar ///
    double b_base_xn se_base_xn p_base_xn N_base r2w_base ///
    double b_mech se_mech p_mech N_mech r2w_mech ///
    double b_y_key se_y_key p_y_key ///
    double b_y_m se_y_m p_y_m ///
    double b_y_xn se_y_xn p_y_xn N_y r2w_y using `results', replace

foreach sample of local samples {
    local samplecond "low_fin==1"
    if "`sample'" == "low_fin_no2020" local samplecond "low_fin==1 & year!=2020"
    if "`sample'" == "low_fin_through2023" local samplecond "low_fin==1 & year<=2023"
    if "`sample'" == "low_fin_active_cum" local samplecond "low_fin==1 & fund_est_scale_cum>0"

    foreach spec of local specs {
        local ctrl_part ""
        local ctrlmiss ""
        if "`spec'" == "ctrl5" {
            local ctrl_part "ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi"
            local ctrlmiss "ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi"
        }

        foreach x of local xvars {
            foreach d of local dvars {
                foreach y of local yvars {
                    foreach m of local mvars {
                        local miss_all "`y', `x', `d', `m', city_id, year"
                        local miss_m "`m', `x', `d', city_id, year"
                        if "`ctrlmiss'" != "" {
                            local miss_all "`miss_all', `ctrlmiss'"
                            local miss_m "`miss_m', `ctrlmiss'"
                        }

                        local b_base_xn = .
                        local se_base_xn = .
                        local p_base_xn = .
                        local N_base = .
                        local r2w_base = .
                        capture quietly xtreg `y' c.`x'##c.`d' `ctrl_part' i.year ///
                            if `samplecond' & !missing(`miss_all'), fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_base_xn = _b[c.`x'#c.`d']
                            if _rc == 0 {
                                local se_base_xn = _se[c.`x'#c.`d']
                                if `se_base_xn' > 0 & `se_base_xn' < . {
                                    local p_base_xn = 2 * ttail(e(df_r), abs(`b_base_xn' / `se_base_xn'))
                                }
                                local N_base = e(N)
                                local r2w_base = e(r2_w)
                            }
                        }

                        local b_m_d = .
                        local se_m_d = .
                        local p_m_d = .
                        local N_m = .
                        local r2w_m = .
                        capture quietly xtreg `m' `x' `d' `ctrl_part' i.year ///
                            if `samplecond' & !missing(`miss_m'), fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_m_d = _b[`d']
                            if _rc == 0 {
                                local se_m_d = _se[`d']
                                if `se_m_d' > 0 & `se_m_d' < . {
                                    local p_m_d = 2 * ttail(e(df_r), abs(`b_m_d' / `se_m_d'))
                                }
                                local N_m = e(N)
                                local r2w_m = e(r2_w)
                            }
                        }

                        local b_m_xn = .
                        local se_m_xn = .
                        local p_m_xn = .
                        local N_mx = .
                        local r2w_mx = .
                        capture quietly xtreg `m' c.`x'##c.`d' `ctrl_part' i.year ///
                            if `samplecond' & !missing(`miss_m'), fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_m_xn = _b[c.`x'#c.`d']
                            if _rc == 0 {
                                local se_m_xn = _se[c.`x'#c.`d']
                                if `se_m_xn' > 0 & `se_m_xn' < . {
                                    local p_m_xn = 2 * ttail(e(df_r), abs(`b_m_xn' / `se_m_xn'))
                                }
                                local N_mx = e(N)
                                local r2w_mx = e(r2_w)
                            }
                        }

                        local b_y_xm = .
                        local se_y_xm = .
                        local p_y_xm = .
                        local b_y_m = .
                        local se_y_m = .
                        local p_y_m = .
                        local b_y_xn = .
                        local se_y_xn = .
                        local p_y_xn = .
                        local N_y = .
                        local r2w_y = .
                        capture quietly xtreg `y' c.`x'##c.`d' c.`x'##c.`m' `ctrl_part' i.year ///
                            if `samplecond' & !missing(`miss_all'), fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_y_xm = _b[c.`x'#c.`m']
                            if _rc == 0 {
                                local se_y_xm = _se[c.`x'#c.`m']
                                if `se_y_xm' > 0 & `se_y_xm' < . {
                                    local p_y_xm = 2 * ttail(e(df_r), abs(`b_y_xm' / `se_y_xm'))
                                }
                            }
                            capture local b_y_m = _b[`m']
                            if _rc == 0 {
                                local se_y_m = _se[`m']
                                if `se_y_m' > 0 & `se_y_m' < . {
                                    local p_y_m = 2 * ttail(e(df_r), abs(`b_y_m' / `se_y_m'))
                                }
                            }
                            capture local b_y_xn = _b[c.`x'#c.`d']
                            if _rc == 0 {
                                local se_y_xn = _se[c.`x'#c.`d']
                                if `se_y_xn' > 0 & `se_y_xn' < . {
                                    local p_y_xn = 2 * ttail(e(df_r), abs(`b_y_xn' / `se_y_xn'))
                                }
                            }
                            local N_y = e(N)
                            local r2w_y = e(r2_w)
                        }

                        post `posth' ("scheme2_moderator") ("`sample'") ("`spec'") ("`x'") ("`d'") ("`m'") ("`y'") ///
                            (`b_base_xn') (`se_base_xn') (`p_base_xn') (`N_base') (`r2w_base') ///
                            (`b_m_d') (`se_m_d') (`p_m_d') (`N_m') (`r2w_m') ///
                            (`b_y_xm') (`se_y_xm') (`p_y_xm') ///
                            (`b_y_m') (`se_y_m') (`p_y_m') ///
                            (`b_y_xn') (`se_y_xn') (`p_y_xn') (`N_y') (`r2w_y')

                        post `posth' ("scheme2_extended") ("`sample'") ("`spec'") ("`x'") ("`d'") ("`m'") ("`y'") ///
                            (`b_base_xn') (`se_base_xn') (`p_base_xn') (`N_base') (`r2w_base') ///
                            (`b_m_xn') (`se_m_xn') (`p_m_xn') (`N_mx') (`r2w_mx') ///
                            (`b_y_xm') (`se_y_xm') (`p_y_xm') ///
                            (`b_y_m') (`se_y_m') (`p_y_m') ///
                            (`b_y_xn') (`se_y_xn') (`p_y_xn') (`N_y') (`r2w_y')
                    }
                }
            }
        }
    }
}

postclose `posth'
use `results', clear

gen base_ok10 = b_base_xn < 0 & p_base_xn < 0.1
gen base_ok05 = b_base_xn < 0 & p_base_xn < 0.05
gen mech_ok10 = b_mech < 0 & p_mech < 0.1
gen mech_ok05 = b_mech < 0 & p_mech < 0.05
gen ykey_ok10 = b_y_key > 0 & p_y_key < 0.1
gen ykey_ok05 = b_y_key > 0 & p_y_key < 0.05
gen theory_ok10 = base_ok10 & mech_ok10 & ykey_ok10
gen theory_ok05 = base_ok05 & mech_ok05 & ykey_ok05
gen attenuated = abs(b_y_xn) < abs(b_base_xn) if !missing(b_y_xn, b_base_xn)
gen strict_ok10 = theory_ok10 & attenuated == 1
gen strict_ok05 = theory_ok05 & attenuated == 1

foreach p in base_xn mech y_key y_m y_xn {
    gen sig_`p' = ""
}
replace sig_base_xn = "***" if p_base_xn < 0.01
replace sig_base_xn = "**" if p_base_xn >= 0.01 & p_base_xn < 0.05
replace sig_base_xn = "*" if p_base_xn >= 0.05 & p_base_xn < 0.1
replace sig_mech = "***" if p_mech < 0.01
replace sig_mech = "**" if p_mech >= 0.01 & p_mech < 0.05
replace sig_mech = "*" if p_mech >= 0.05 & p_mech < 0.1
replace sig_y_key = "***" if p_y_key < 0.01
replace sig_y_key = "**" if p_y_key >= 0.01 & p_y_key < 0.05
replace sig_y_key = "*" if p_y_key >= 0.05 & p_y_key < 0.1
replace sig_y_m = "***" if p_y_m < 0.01
replace sig_y_m = "**" if p_y_m >= 0.01 & p_y_m < 0.05
replace sig_y_m = "*" if p_y_m >= 0.05 & p_y_m < 0.1
replace sig_y_xn = "***" if p_y_xn < 0.01
replace sig_y_xn = "**" if p_y_xn >= 0.01 & p_y_xn < 0.05
replace sig_y_xn = "*" if p_y_xn >= 0.05 & p_y_xn < 0.1

sort scheme sample spec xvar dvar mvar yvar
export delimited using "`allcsv'", replace

preserve
keep if theory_ok10 == 1
sort scheme p_base_xn p_mech p_y_key sample spec xvar dvar mvar yvar
export delimited using "`selectedcsv'", replace
restore

preserve
keep if strict_ok10 == 1
sort scheme p_base_xn p_mech p_y_key sample spec xvar dvar mvar yvar
export delimited using "`strictcsv'", replace
restore

di "Counts:"
count
count if theory_ok10 == 1
count if theory_ok05 == 1
count if strict_ok10 == 1
count if strict_ok05 == 1
tab scheme theory_ok10
tab scheme strict_ok10

log close
