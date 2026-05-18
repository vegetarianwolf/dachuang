version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_mechanism_soccap_ratio_only_20260516"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"
local diagcsv "`outdir'/`basename'_diagnostics.csv"

log using "`logfile'", replace text

di "Task: social-capital leverage-efficiency mechanism test, ratio variables only"
di "Data: `datafile'"

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

local numeric_vars ///
    fund_est_count fund_est_scale fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    soccap_share_total gov_share_total soccap_leverage matched_share_total ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual

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
    fund_est_count fund_est_scale fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    soccap_share_total gov_share_total soccap_leverage matched_share_total ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

* Ratio-domain cleaning. Share variables are proportions and leverage is non-negative.
foreach v in soccap_share_total gov_share_total matched_share_total {
    replace `v' = . if !missing(`v') & (`v' < 0 | `v' > 1)
}
replace soccap_leverage = . if !missing(soccap_leverage) & soccap_leverage < 0

gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)
gen ln_fund_est_scale_cum = ln(fund_est_scale_cum + 1)

xtset city_id year

* Construct ratio-only mechanism variables.
gen scsh = soccap_share_total
gen matsh = matched_share_total
gen govinv = 1 - gov_share_total if !missing(gov_share_total)
gen lev = soccap_leverage

foreach v in scsh matsh govinv lev {
    gen `v'0 = `v'
    replace `v'0 = 0 if missing(`v'0)
}

foreach v in scsh scsh0 matsh matsh0 govinv govinv0 lev lev0 {
    gen `v'_w = `v'
    quietly summarize `v' if !missing(`v'), detail
    if r(N) > 0 {
        local p1 = r(p1)
        local p99 = r(p99)
        replace `v'_w = `p1' if !missing(`v'_w) & `v'_w < `p1'
        replace `v'_w = `p99' if !missing(`v'_w) & `v'_w > `p99'
    }
}

gen lnlev_w = ln(1 + lev_w)
gen lnlev0_w = ln(1 + lev0_w)

foreach v in scsh_w scsh0_w matsh_w matsh0_w govinv_w govinv0_w lnlev_w lnlev0_w {
    egen z_`v' = std(`v')
}

gen L1_z_scsh0_w = L.z_scsh0_w
gen L1_z_matsh0_w = L.z_matsh0_w
gen L1_z_govinv0_w = L.z_govinv0_w
gen L1_z_lnlev0_w = L.z_lnlev0_w

tempname diagpost
tempfile diagnostics
postfile `diagpost' str28 variable str16 treatment double N mean sd min p1 p50 p99 max using `diagnostics', replace
foreach v in soccap_share_total matched_share_total gov_share_total scsh_w scsh0_w matsh_w matsh0_w govinv_w govinv0_w lev lnlev_w lnlev0_w {
    quietly summarize `v', detail
    post `diagpost' ("`v'") ("ratio_clean") (r(N)) (r(mean)) (r(sd)) (r(min)) (r(p1)) (r(p50)) (r(p99)) (r(max))
}
postclose `diagpost'
preserve
use `diagnostics', clear
export delimited using "`diagcsv'", replace
restore

tempfile panel
save `panel', replace

local xvars fund_est_scale_cum ln_fund_est_scale_cum

local yvars ///
    pat_invent_apply ///
    pat_utility_apply ///
    pat_apply_total ///
    ln_pat_invent_apply ///
    ln_pat_utility_apply ///
    ln_pat_apply_total

local dvars ///
    debt_pressure ///
    debt_pressure_l1

local mvars ///
    z_scsh_w ///
    z_scsh0_w ///
    L1_z_scsh0_w ///
    z_matsh_w ///
    z_matsh0_w ///
    L1_z_matsh0_w ///
    z_govinv0_w ///
    L1_z_govinv0_w ///
    z_lnlev_w ///
    z_lnlev0_w ///
    L1_z_lnlev0_w

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
    str18 family ///
    str8 spec ///
    str24 yvar ///
    str24 xvar ///
    str18 dvar ///
    str24 mvar ///
    str12 step ///
    str64 focus_term ///
    double b se p ///
    str64 xd_term ///
    double b_xd se_xd p_xd ///
    str64 m_term ///
    double b_m se_m p_m ///
    double N r2w using `results', replace

foreach spec in noctrl ctrl {

    local ctrl_part ""
    if "`spec'" == "ctrl" {
        local ctrl_part "`ctrls'"
    }

    foreach x of local xvars {
        foreach d of local dvars {
            foreach m of local mvars {

                * Model A: mediated moderation, X*Debt -> ratio M -> innovation.
                use `panel', clear
                xtset city_id year
                if "`spec'" == "ctrl" {
                    keep if !missing(`m', `x', `d', `ctrlmiss', city_id, year)
                }
                else {
                    keep if !missing(`m', `x', `d', city_id, year)
                }
                capture noisily xtreg `m' c.`x'##c.`d' `ctrl_part' i.year, fe vce(cluster city_id)
                if _rc == 0 {
                    local term_xd c.`x'#c.`d'
                    capture local b_focus = _b[`term_xd']
                    if _rc == 0 {
                        local se_focus = _se[`term_xd']
                        local p_focus = .
                        if `se_focus' > 0 & `se_focus' < . {
                            local p_focus = 2 * ttail(e(df_r), abs(`b_focus' / `se_focus'))
                        }
                        post `posth' ("mediated") ("`spec'") ("") ("`x'") ("`d'") ("`m'") ("M_eq") ///
                            ("`term_xd'") (`b_focus') (`se_focus') (`p_focus') ///
                            ("`term_xd'") (`b_focus') (`se_focus') (`p_focus') ///
                            ("") (.) (.) (.) ///
                            (e(N)) (e(r2_w))
                    }
                }

                foreach y of local yvars {
                    use `panel', clear
                    xtset city_id year
                    if "`spec'" == "ctrl" {
                        keep if !missing(`y', `m', `x', `d', `ctrlmiss', city_id, year)
                    }
                    else {
                        keep if !missing(`y', `m', `x', `d', city_id, year)
                    }
                    capture noisily xtreg `y' c.`x'##c.`d' `m' `ctrl_part' i.year, fe vce(cluster city_id)
                    if _rc == 0 {
                        local term_xd c.`x'#c.`d'
                        capture local b_xd = _b[`term_xd']
                        if _rc == 0 {
                            local se_xd = _se[`term_xd']
                            local p_xd = .
                            if `se_xd' > 0 & `se_xd' < . {
                                local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                            }
                            local b_m = _b[`m']
                            local se_m = _se[`m']
                            local p_m = .
                            if `se_m' > 0 & `se_m' < . {
                                local p_m = 2 * ttail(e(df_r), abs(`b_m' / `se_m'))
                            }
                            post `posth' ("mediated") ("`spec'") ("`y'") ("`x'") ("`d'") ("`m'") ("Y_eq") ///
                                ("`m'") (`b_m') (`se_m') (`p_m') ///
                                ("`term_xd'") (`b_xd') (`se_xd') (`p_xd') ///
                                ("`m'") (`b_m') (`se_m') (`p_m') ///
                                (e(N)) (e(r2_w))
                        }
                    }
                }

                * Model B: ratio M moderates the marginal effect of fund scale.
                use `panel', clear
                xtset city_id year
                if "`spec'" == "ctrl" {
                    keep if !missing(`m', `x', `d', `ctrlmiss', city_id, year)
                }
                else {
                    keep if !missing(`m', `x', `d', city_id, year)
                }
                capture noisily xtreg `m' `x' `d' `ctrl_part' i.year, fe vce(cluster city_id)
                if _rc == 0 {
                    capture local b_d = _b[`d']
                    if _rc == 0 {
                        local se_d = _se[`d']
                        local p_d = .
                        if `se_d' > 0 & `se_d' < . {
                            local p_d = 2 * ttail(e(df_r), abs(`b_d' / `se_d'))
                        }
                        post `posth' ("fund_x_ratio") ("`spec'") ("") ("`x'") ("`d'") ("`m'") ("M_eq") ///
                            ("`d'") (`b_d') (`se_d') (`p_d') ///
                            ("") (.) (.) (.) ///
                            ("") (.) (.) (.) ///
                            (e(N)) (e(r2_w))
                    }
                }

                foreach y of local yvars {
                    use `panel', clear
                    xtset city_id year
                    if "`spec'" == "ctrl" {
                        keep if !missing(`y', `m', `x', `d', `ctrlmiss', city_id, year)
                    }
                    else {
                        keep if !missing(`y', `m', `x', `d', city_id, year)
                    }
                    capture noisily xtreg `y' c.`x'##c.`d' c.`x'#c.`m' `m' `ctrl_part' i.year, fe vce(cluster city_id)
                    if _rc == 0 {
                        local term_xd c.`x'#c.`d'
                        local term_xm c.`x'#c.`m'
                        capture local b_xm = _b[`term_xm']
                        if _rc == 0 {
                            local se_xm = _se[`term_xm']
                            local p_xm = .
                            if `se_xm' > 0 & `se_xm' < . {
                                local p_xm = 2 * ttail(e(df_r), abs(`b_xm' / `se_xm'))
                            }
                            local b_xd = _b[`term_xd']
                            local se_xd = _se[`term_xd']
                            local p_xd = .
                            if `se_xd' > 0 & `se_xd' < . {
                                local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                            }
                            local b_m = _b[`m']
                            local se_m = _se[`m']
                            local p_m = .
                            if `se_m' > 0 & `se_m' < . {
                                local p_m = 2 * ttail(e(df_r), abs(`b_m' / `se_m'))
                            }
                            post `posth' ("fund_x_ratio") ("`spec'") ("`y'") ("`x'") ("`d'") ("`m'") ("Y_eq") ///
                                ("`term_xm'") (`b_xm') (`se_xm') (`p_xm') ///
                                ("`term_xd'") (`b_xd') (`se_xd') (`p_xd') ///
                                ("`m'") (`b_m') (`se_m') (`p_m') ///
                                (e(N)) (e(r2_w))
                        }
                    }
                }

                * Model C: triple interaction, X*Debt effect varies with ratio M.
                foreach y of local yvars {
                    use `panel', clear
                    xtset city_id year
                    if "`spec'" == "ctrl" {
                        keep if !missing(`y', `m', `x', `d', `ctrlmiss', city_id, year)
                    }
                    else {
                        keep if !missing(`y', `m', `x', `d', city_id, year)
                    }
                    capture noisily xtreg `y' c.`x'##c.`d'##c.`m' `ctrl_part' i.year, fe vce(cluster city_id)
                    if _rc == 0 {
                        local term_triple c.`x'#c.`d'#c.`m'
                        local term_xd c.`x'#c.`d'
                        capture local b_tri = _b[`term_triple']
                        if _rc == 0 {
                            local se_tri = _se[`term_triple']
                            local p_tri = .
                            if `se_tri' > 0 & `se_tri' < . {
                                local p_tri = 2 * ttail(e(df_r), abs(`b_tri' / `se_tri'))
                            }
                            local b_xd = _b[`term_xd']
                            local se_xd = _se[`term_xd']
                            local p_xd = .
                            if `se_xd' > 0 & `se_xd' < . {
                                local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                            }
                            local b_m = _b[`m']
                            local se_m = _se[`m']
                            local p_m = .
                            if `se_m' > 0 & `se_m' < . {
                                local p_m = 2 * ttail(e(df_r), abs(`b_m' / `se_m'))
                            }
                            post `posth' ("triple") ("`spec'") ("`y'") ("`x'") ("`d'") ("`m'") ("Y_eq") ///
                                ("`term_triple'") (`b_tri') (`se_tri') (`p_tri') ///
                                ("`term_xd'") (`b_xd') (`se_xd') (`p_xd') ///
                                ("`m'") (`b_m') (`se_m') (`p_m') ///
                                (e(N)) (e(r2_w))
                        }
                    }
                }
            }
        }
    }
}

postclose `posth'
use `results', clear
gen sig = ""
replace sig = "***" if p < 0.01
replace sig = "**" if p >= 0.01 & p < 0.05
replace sig = "*" if p >= 0.05 & p < 0.1
sort family spec xvar dvar mvar yvar step
export delimited using "`resultcsv'", replace

di "==== Significant focus terms at 10% ===="
list family spec yvar xvar dvar mvar step focus_term b se p sig N r2w if p < 0.1, sepby(family mvar) abbreviate(24)

di "Results CSV: `resultcsv'"
di "Diagnostics CSV: `diagcsv'"
log close
