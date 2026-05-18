version 18
clear all
set more off
capture log close

cd "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"

local basename "xtreg_mechanism_early_share_focus_ascii"
local datafile "../../staging_ascii/panel_2015_2024_regression_ascii_clean.csv"
local resultcsv "`basename'_results.csv"
local selectcsv "`basename'_selected.csv"

log using "`basename'.log", replace text

display "Task: early-investment share mechanism test"
display "Data: `datafile'"
display "Note: only early investment share/proportion variables are used as mechanism variables."

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum ///
    debt_pressure debt_pressure_l1 ///
    early_inv_amt_share early_inv_count_share ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)

xtset city_id year

foreach v in early_inv_amt_share early_inv_count_share {
    gen `v'_raw = `v' if inrange(`v', 0, 1)

    quietly summarize `v' if inrange(`v', 0, 1), detail
    local p1 = r(p1)
    local p99 = r(p99)
    gen `v'_winsor = `v' if inrange(`v', 0, 1)
    replace `v'_winsor = `p1' if `v'_winsor < `p1' & !missing(`v'_winsor)
    replace `v'_winsor = `p99' if `v'_winsor > `p99' & !missing(`v'_winsor)

    gen `v'_asin = asin(sqrt(`v')) if inrange(`v', 0, 1)
    gen `v'_logit = log((`v' + 0.001) / (1 - `v' + 0.001)) if inrange(`v', 0, 1)
}

tempname posth
tempfile results
postfile `posth' ///
    str16 model ///
    str24 yvar ///
    str18 dvar ///
    str24 m_source ///
    str12 transform ///
    str32 mvar ///
    str8 spec ///
    double N ///
    double coef_path1 se_path1 p_path1 ///
    double coef_path2 se_path2 p_path2 ///
    double coef_xd se_xd p_xd ///
    double r2w ///
    double pass10 pass05 ///
    using `results', replace

local yvars pat_invent_apply pat_utility_apply pat_apply_total
local dvars debt_pressure debt_pressure_l1
local share_sources early_inv_amt_share early_inv_count_share
local transforms raw winsor asin logit
local ctrlvars ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi

foreach y of local yvars {
    foreach d of local dvars {
        foreach src of local share_sources {
            foreach tr of local transforms {
                local m "`src'_`tr'"
                foreach spec in noctrl ctrl {
                    local controls ""
                    local req "`y' `d' fund_est_scale_cum `m' city_id year"
                    if "`spec'" == "ctrl" {
                        local controls "`ctrlvars'"
                        local req "`req' `ctrlvars'"
                    }

                    preserve
                    egen rowmiss = rowmiss(`req')
                    keep if rowmiss == 0
                    drop rowmiss
                    quietly count
                    local NN = r(N)
                    xtset city_id year

                    * Model A: mediated moderation, X * debt -> share -> Y.
                    local coef_path1 = .
                    local se_path1 = .
                    local p_path1 = .
                    local coef_path2 = .
                    local se_path2 = .
                    local p_path2 = .
                    local coef_xd = .
                    local se_xd = .
                    local p_xd = .
                    local r2w = .
                    local pass10 = 0
                    local pass05 = 0

                    if `NN' >= 80 {
                        capture quietly xtreg `m' c.fund_est_scale_cum##c.`d' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture scalar btmp = _b[c.fund_est_scale_cum#c.`d']
                            if _rc == 0 {
                                scalar setmp = _se[c.fund_est_scale_cum#c.`d']
                                local coef_path1 = scalar(btmp)
                                local se_path1 = scalar(setmp)
                                local p_path1 = 2 * ttail(e(df_r), abs(`coef_path1' / `se_path1'))
                            }
                        }

                        capture quietly xtreg `y' c.fund_est_scale_cum##c.`d' c.`m' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local r2w = e(r2_w)
                            local NN = e(N)
                            capture scalar btmp = _b[`m']
                            if _rc == 0 {
                                scalar setmp = _se[`m']
                                local coef_path2 = scalar(btmp)
                                local se_path2 = scalar(setmp)
                                local p_path2 = 2 * ttail(e(df_r), abs(`coef_path2' / `se_path2'))
                            }
                            capture scalar btmp = _b[c.fund_est_scale_cum#c.`d']
                            if _rc == 0 {
                                scalar setmp = _se[c.fund_est_scale_cum#c.`d']
                                local coef_xd = scalar(btmp)
                                local se_xd = scalar(setmp)
                                local p_xd = 2 * ttail(e(df_r), abs(`coef_xd' / `se_xd'))
                            }
                        }

                        if `p_path1' < . & `p_path2' < . & `p_path1' <= 0.1 & `p_path2' <= 0.1 local pass10 = 1
                        if `p_path1' < . & `p_path2' < . & `p_path1' <= 0.05 & `p_path2' <= 0.05 local pass05 = 1
                    }
                    post `posth' ("mediator") ("`y'") ("`d'") ("`src'") ("`tr'") ("`m'") ("`spec'") ///
                        (`NN') (`coef_path1') (`se_path1') (`p_path1') ///
                        (`coef_path2') (`se_path2') (`p_path2') ///
                        (`coef_xd') (`se_xd') (`p_xd') (`r2w') (`pass10') (`pass05')

                    * Model B: share as a moderating mechanism, debt -> share and X * share -> Y.
                    local coef_path1 = .
                    local se_path1 = .
                    local p_path1 = .
                    local coef_path2 = .
                    local se_path2 = .
                    local p_path2 = .
                    local coef_xd = .
                    local se_xd = .
                    local p_xd = .
                    local r2w = .
                    local pass10 = 0
                    local pass05 = 0

                    if `NN' >= 80 {
                        capture quietly xtreg `m' c.fund_est_scale_cum c.`d' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture scalar btmp = _b[`d']
                            if _rc == 0 {
                                scalar setmp = _se[`d']
                                local coef_path1 = scalar(btmp)
                                local se_path1 = scalar(setmp)
                                local p_path1 = 2 * ttail(e(df_r), abs(`coef_path1' / `se_path1'))
                            }
                        }

                        capture quietly xtreg `y' c.fund_est_scale_cum##c.`d' c.fund_est_scale_cum##c.`m' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local r2w = e(r2_w)
                            local NN = e(N)
                            capture scalar btmp = _b[c.fund_est_scale_cum#c.`m']
                            if _rc == 0 {
                                scalar setmp = _se[c.fund_est_scale_cum#c.`m']
                                local coef_path2 = scalar(btmp)
                                local se_path2 = scalar(setmp)
                                local p_path2 = 2 * ttail(e(df_r), abs(`coef_path2' / `se_path2'))
                            }
                            capture scalar btmp = _b[c.fund_est_scale_cum#c.`d']
                            if _rc == 0 {
                                scalar setmp = _se[c.fund_est_scale_cum#c.`d']
                                local coef_xd = scalar(btmp)
                                local se_xd = scalar(setmp)
                                local p_xd = 2 * ttail(e(df_r), abs(`coef_xd' / `se_xd'))
                            }
                        }

                        if `p_path1' < . & `p_path2' < . & `p_path1' <= 0.1 & `p_path2' <= 0.1 local pass10 = 1
                        if `p_path1' < . & `p_path2' < . & `p_path1' <= 0.05 & `p_path2' <= 0.05 local pass05 = 1
                    }
                    post `posth' ("moderator") ("`y'") ("`d'") ("`src'") ("`tr'") ("`m'") ("`spec'") ///
                        (`NN') (`coef_path1') (`se_path1') (`p_path1') ///
                        (`coef_path2') (`se_path2') (`p_path2') ///
                        (`coef_xd') (`se_xd') (`p_xd') (`r2w') (`pass10') (`pass05')

                    * Model C: extended triple interaction, X * debt * share -> Y.
                    local coef_path1 = .
                    local se_path1 = .
                    local p_path1 = .
                    local coef_path2 = .
                    local se_path2 = .
                    local p_path2 = .
                    local coef_xd = .
                    local se_xd = .
                    local p_xd = .
                    local r2w = .
                    local pass10 = 0
                    local pass05 = 0

                    if `NN' >= 80 {
                        capture quietly xtreg `m' c.fund_est_scale_cum c.`d' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture scalar btmp = _b[`d']
                            if _rc == 0 {
                                scalar setmp = _se[`d']
                                local coef_path1 = scalar(btmp)
                                local se_path1 = scalar(setmp)
                                local p_path1 = 2 * ttail(e(df_r), abs(`coef_path1' / `se_path1'))
                            }
                        }

                        capture quietly xtreg `y' c.fund_est_scale_cum##c.`d'##c.`m' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local r2w = e(r2_w)
                            local NN = e(N)
                            capture scalar btmp = _b[c.fund_est_scale_cum#c.`d'#c.`m']
                            if _rc == 0 {
                                scalar setmp = _se[c.fund_est_scale_cum#c.`d'#c.`m']
                                local coef_path2 = scalar(btmp)
                                local se_path2 = scalar(setmp)
                                local p_path2 = 2 * ttail(e(df_r), abs(`coef_path2' / `se_path2'))
                            }
                            capture scalar btmp = _b[c.fund_est_scale_cum#c.`d']
                            if _rc == 0 {
                                scalar setmp = _se[c.fund_est_scale_cum#c.`d']
                                local coef_xd = scalar(btmp)
                                local se_xd = scalar(setmp)
                                local p_xd = 2 * ttail(e(df_r), abs(`coef_xd' / `se_xd'))
                            }
                        }

                        if `p_path1' < . & `p_path2' < . & `p_path1' <= 0.1 & `p_path2' <= 0.1 local pass10 = 1
                        if `p_path1' < . & `p_path2' < . & `p_path1' <= 0.05 & `p_path2' <= 0.05 local pass05 = 1
                    }
                    post `posth' ("triple") ("`y'") ("`d'") ("`src'") ("`tr'") ("`m'") ("`spec'") ///
                        (`NN') (`coef_path1') (`se_path1') (`p_path1') ///
                        (`coef_path2') (`se_path2') (`p_path2') ///
                        (`coef_xd') (`se_xd') (`p_xd') (`r2w') (`pass10') (`pass05')

                    restore
                }
            }
        }
    }
}

postclose `posth'
use `results', clear
sort model pass05 pass10 m_source transform yvar dvar spec
export delimited using "`resultcsv'", replace

preserve
keep if pass05 == 1 | pass10 == 1
sort pass05 pass10 model m_source transform yvar dvar spec p_path2
export delimited using "`selectcsv'", replace
restore

display "Selected rows at 10% or 5% level:"
list model yvar dvar m_source transform spec N coef_path1 p_path1 coef_path2 p_path2 coef_xd p_xd pass10 pass05 if pass05 == 1 | pass10 == 1, abbreviate(24) sepby(model m_source transform)

display "All results written to `resultcsv'"
display "Selected results written to `selectcsv'"
log close
