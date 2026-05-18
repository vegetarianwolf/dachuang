version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_soccap_moderated_mechanism_dual_20260518"
local logfile "`outdir'/`basename'.log"
local allcsv "`outdir'/`basename'_all_results.csv"
local selectedcsv "`outdir'/`basename'_theory_selected.csv"
local scheme1csv "`outdir'/`basename'_scheme1_selected.csv"
local scheme2csv "`outdir'/`basename'_scheme2_selected.csv"
local strictcsv "`outdir'/`basename'_strict_attenuated.csv"

log using "`logfile'", replace text

di "Task: debt negative moderation mechanism through social capital leverage variables"
di "Model families: scheme1 mediated moderation and scheme2 mediated/moderating mechanism"
di "Restrictions: no log transform on fund scale or social-capital leverage variables"

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

local numeric_vars ///
    fund_est_scale fund_est_scale_cum fund_est_scale_roll5 ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 debt_burden debt_burden_l1 ///
    soccap_share_total gov_share_total soccap_leverage gov_amt ///
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
    debt_pressure debt_pressure_l1 debt_burden debt_burden_l1 ///
    soccap_share_total gov_share_total soccap_leverage gov_amt ///
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

quietly summarize gov_amt if gov_amt > 0, detail
local gov_p5 = r(p5)
gen soccap_leverage_govp5 = soccap_leverage
replace soccap_leverage_govp5 = . if !missing(gov_amt) & gov_amt > 0 & gov_amt < `gov_p5'

foreach v in debt_pressure debt_pressure_l1 debt_burden debt_burden_l1 ///
    soccap_leverage soccap_leverage_govp5 soccap_share_total nongov_share_total {
    capture confirm variable `v'
    if !_rc {
        gen `v'_w = `v'
        quietly summarize `v' if !missing(`v'), detail
        if r(N) > 0 {
            local p1 = r(p1)
            local p99 = r(p99)
            replace `v'_w = `p1' if !missing(`v'_w) & `v'_w < `p1'
            replace `v'_w = `p99' if !missing(`v'_w) & `v'_w > `p99'
        }
    }
}

foreach v in soccap_leverage soccap_share_total nongov_share_total {
    capture confirm variable `v'
    if !_rc {
        gen `v'_zero_w = `v'
        replace `v'_zero_w = 0 if missing(`v'_zero_w)
        quietly summarize `v'_zero_w if !missing(`v'_zero_w), detail
        if r(N) > 0 {
            local p1 = r(p1)
            local p99 = r(p99)
            replace `v'_zero_w = `p1' if !missing(`v'_zero_w) & `v'_zero_w < `p1'
            replace `v'_zero_w = `p99' if !missing(`v'_zero_w) & `v'_zero_w > `p99'
        }
    }
}

xtset city_id year
local lagdiff_vars ///
    soccap_leverage_w soccap_leverage_zero_w soccap_leverage_govp5_w ///
    soccap_share_total_w soccap_share_total_zero_w ///
    nongov_share_total_w nongov_share_total_zero_w

foreach v of local lagdiff_vars {
    capture confirm variable `v'
    if !_rc {
        gen L1_`v' = L.`v'
        gen D1_`v' = D.`v'
    }
}

quietly summarize fin_dev if !missing(fin_dev), detail
gen low_fin = fin_dev < r(p50) if !missing(fin_dev)
gen high_fin = fin_dev >= r(p50) if !missing(fin_dev)

quietly summarize marketization if !missing(marketization), detail
gen low_market = marketization < r(p50) if !missing(marketization)
gen high_market = marketization >= r(p50) if !missing(marketization)

tempfile panel
save `panel', replace

local xvars fund_est_scale_cum
local dvars debt_pressure debt_pressure_l1 debt_pressure_w debt_pressure_l1_w ///
    debt_burden debt_burden_l1 debt_burden_w debt_burden_l1_w
local yvars pat_apply_total pat_invent_apply pat_utility_apply ///
    ln_pat_apply_total ln_pat_invent_apply ln_pat_utility_apply
local mvars soccap_leverage_w soccap_leverage_zero_w soccap_leverage_govp5_w ///
    D1_soccap_leverage_w D1_soccap_leverage_zero_w L1_soccap_leverage_zero_w ///
    soccap_share_total_zero_w L1_soccap_share_total_zero_w ///
    nongov_share_total_zero_w L1_nongov_share_total_zero_w
local samples all post2016 through2023 no2020 no2020_through2023 active_cum active_cum_no2020 low_market low_fin
local specs noctrl basic full

tempname posth
tempfile results
postfile `posth' ///
    str18 scheme str24 sample str12 spec str24 xvar str24 dvar str44 mvar str24 yvar ///
    double b_base_xn se_base_xn p_base_xn N_base r2w_base ///
    double b_mech se_mech p_mech N_mech r2w_mech ///
    double b_y_key se_y_key p_y_key ///
    double b_y_m se_y_m p_y_m ///
    double b_y_xn se_y_xn p_y_xn N_y r2w_y using `results', replace

foreach sample of local samples {
    local samplecond "1"
    if "`sample'" == "post2016" local samplecond "year>=2016"
    if "`sample'" == "through2023" local samplecond "year<=2023"
    if "`sample'" == "no2020" local samplecond "year!=2020"
    if "`sample'" == "no2020_through2023" local samplecond "year!=2020 & year<=2023"
    if "`sample'" == "active_cum" local samplecond "fund_est_scale_cum>0"
    if "`sample'" == "active_cum_no2020" local samplecond "fund_est_scale_cum>0 & year!=2020"
    if "`sample'" == "low_market" local samplecond "low_market==1"
    if "`sample'" == "low_fin" local samplecond "low_fin==1"

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
                foreach y of local yvars {
                    use `panel', clear
                    xtset city_id year
                    capture confirm variable `d'
                    if _rc continue
                    keep if `samplecond'
                    if "`ctrlmiss'" == "" {
                        keep if !missing(`y', `x', `d', city_id, year)
                    }
                    else {
                        keep if !missing(`y', `x', `d', `ctrlmiss', city_id, year)
                    }

                    local b_base_xn = .
                    local se_base_xn = .
                    local p_base_xn = .
                    local N_base = .
                    local r2w_base = .

                    capture quietly xtreg `y' c.`x'##c.`d' `ctrl_part' i.year, fe vce(cluster city_id)
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

                    foreach m of local mvars {
                        capture confirm variable `m'
                        if _rc continue

                        * Scheme 1: X*N first affects M; M then enters the innovation equation.
                        use `panel', clear
                        xtset city_id year
                        keep if `samplecond'
                        if "`ctrlmiss'" == "" {
                            keep if !missing(`m', `x', `d', city_id, year)
                        }
                        else {
                            keep if !missing(`m', `x', `d', `ctrlmiss', city_id, year)
                        }

                        local b_m_xn = .
                        local se_m_xn = .
                        local p_m_xn = .
                        local N_m1 = .
                        local r2w_m1 = .
                        capture quietly xtreg `m' c.`x'##c.`d' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_m_xn = _b[c.`x'#c.`d']
                            if _rc == 0 {
                                local se_m_xn = _se[c.`x'#c.`d']
                                if `se_m_xn' > 0 & `se_m_xn' < . {
                                    local p_m_xn = 2 * ttail(e(df_r), abs(`b_m_xn' / `se_m_xn'))
                                }
                                local N_m1 = e(N)
                                local r2w_m1 = e(r2_w)
                            }
                        }

                        use `panel', clear
                        xtset city_id year
                        keep if `samplecond'
                        if "`ctrlmiss'" == "" {
                            keep if !missing(`y', `m', `x', `d', city_id, year)
                        }
                        else {
                            keep if !missing(`y', `m', `x', `d', `ctrlmiss', city_id, year)
                        }

                        local b_y_m1 = .
                        local se_y_m1 = .
                        local p_y_m1 = .
                        local b_y_xn1 = .
                        local se_y_xn1 = .
                        local p_y_xn1 = .
                        local N_y1 = .
                        local r2w_y1 = .
                        capture quietly xtreg `y' c.`x'##c.`d' `m' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_y_m1 = _b[`m']
                            if _rc == 0 {
                                local se_y_m1 = _se[`m']
                                if `se_y_m1' > 0 & `se_y_m1' < . {
                                    local p_y_m1 = 2 * ttail(e(df_r), abs(`b_y_m1' / `se_y_m1'))
                                }
                            }
                            capture local b_y_xn1 = _b[c.`x'#c.`d']
                            if _rc == 0 {
                                local se_y_xn1 = _se[c.`x'#c.`d']
                                if `se_y_xn1' > 0 & `se_y_xn1' < . {
                                    local p_y_xn1 = 2 * ttail(e(df_r), abs(`b_y_xn1' / `se_y_xn1'))
                                }
                            }
                            local N_y1 = e(N)
                            local r2w_y1 = e(r2_w)
                        }
                        post `posth' ("scheme1_mediator") ("`sample'") ("`spec'") ("`x'") ("`d'") ("`m'") ("`y'") ///
                            (`b_base_xn') (`se_base_xn') (`p_base_xn') (`N_base') (`r2w_base') ///
                            (`b_m_xn') (`se_m_xn') (`p_m_xn') (`N_m1') (`r2w_m1') ///
                            (`b_y_m1') (`se_y_m1') (`p_y_m1') ///
                            (`b_y_m1') (`se_y_m1') (`p_y_m1') ///
                            (`b_y_xn1') (`se_y_xn1') (`p_y_xn1') (`N_y1') (`r2w_y1')

                        * Scheme 2: debt affects M; M moderates the fund-innovation relationship.
                        use `panel', clear
                        xtset city_id year
                        keep if `samplecond'
                        if "`ctrlmiss'" == "" {
                            keep if !missing(`m', `x', `d', city_id, year)
                        }
                        else {
                            keep if !missing(`m', `x', `d', `ctrlmiss', city_id, year)
                        }

                        local b_m_d = .
                        local se_m_d = .
                        local p_m_d = .
                        local N_m2 = .
                        local r2w_m2 = .
                        capture quietly xtreg `m' `x' `d' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_m_d = _b[`d']
                            if _rc == 0 {
                                local se_m_d = _se[`d']
                                if `se_m_d' > 0 & `se_m_d' < . {
                                    local p_m_d = 2 * ttail(e(df_r), abs(`b_m_d' / `se_m_d'))
                                }
                                local N_m2 = e(N)
                                local r2w_m2 = e(r2_w)
                            }
                        }

                        use `panel', clear
                        xtset city_id year
                        keep if `samplecond'
                        if "`ctrlmiss'" == "" {
                            keep if !missing(`y', `m', `x', `d', city_id, year)
                        }
                        else {
                            keep if !missing(`y', `m', `x', `d', `ctrlmiss', city_id, year)
                        }

                        local b_y_xm2 = .
                        local se_y_xm2 = .
                        local p_y_xm2 = .
                        local b_y_m2 = .
                        local se_y_m2 = .
                        local p_y_m2 = .
                        local b_y_xn2 = .
                        local se_y_xn2 = .
                        local p_y_xn2 = .
                        local N_y2 = .
                        local r2w_y2 = .
                        capture quietly xtreg `y' c.`x'##c.`d' c.`x'##c.`m' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local b_y_xm2 = _b[c.`x'#c.`m']
                            if _rc == 0 {
                                local se_y_xm2 = _se[c.`x'#c.`m']
                                if `se_y_xm2' > 0 & `se_y_xm2' < . {
                                    local p_y_xm2 = 2 * ttail(e(df_r), abs(`b_y_xm2' / `se_y_xm2'))
                                }
                            }
                            capture local b_y_m2 = _b[`m']
                            if _rc == 0 {
                                local se_y_m2 = _se[`m']
                                if `se_y_m2' > 0 & `se_y_m2' < . {
                                    local p_y_m2 = 2 * ttail(e(df_r), abs(`b_y_m2' / `se_y_m2'))
                                }
                            }
                            capture local b_y_xn2 = _b[c.`x'#c.`d']
                            if _rc == 0 {
                                local se_y_xn2 = _se[c.`x'#c.`d']
                                if `se_y_xn2' > 0 & `se_y_xn2' < . {
                                    local p_y_xn2 = 2 * ttail(e(df_r), abs(`b_y_xn2' / `se_y_xn2'))
                                }
                            }
                            local N_y2 = e(N)
                            local r2w_y2 = e(r2_w)
                        }
                        post `posth' ("scheme2_moderator") ("`sample'") ("`spec'") ("`x'") ("`d'") ("`m'") ("`y'") ///
                            (`b_base_xn') (`se_base_xn') (`p_base_xn') (`N_base') (`r2w_base') ///
                            (`b_m_d') (`se_m_d') (`p_m_d') (`N_m2') (`r2w_m2') ///
                            (`b_y_xm2') (`se_y_xm2') (`p_y_xm2') ///
                            (`b_y_m2') (`se_y_m2') (`p_y_m2') ///
                            (`b_y_xn2') (`se_y_xn2') (`p_y_xn2') (`N_y2') (`r2w_y2')
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
sort scheme p_base_xn p_mech p_y_key sample spec dvar mvar yvar
export delimited using "`selectedcsv'", replace
restore

preserve
keep if scheme == "scheme1_mediator" & theory_ok10 == 1
sort p_base_xn p_mech p_y_key sample spec dvar mvar yvar
export delimited using "`scheme1csv'", replace
restore

preserve
keep if scheme == "scheme2_moderator" & theory_ok10 == 1
sort p_base_xn p_mech p_y_key sample spec dvar mvar yvar
export delimited using "`scheme2csv'", replace
restore

preserve
keep if strict_ok10 == 1
sort scheme p_base_xn p_mech p_y_key sample spec dvar mvar yvar
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
