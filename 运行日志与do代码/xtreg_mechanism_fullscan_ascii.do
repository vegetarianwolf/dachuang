version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_mechanism_fullscan_ascii"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_count fund_est_scale fund_est_count_cum fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    early_inv_amt early_inv_count early_inv_amt_share early_inv_count_share ///
    soccap_fund_count soccap_amt gov_amt gp_amt unknown_amt ///
    fund_commit_total matched_commit_amt soccap_share_total gov_share_total ///
    soccap_leverage matched_share_total ///
    fcity_sa_mean fcity_fc_mean fcity_kz_mean fcity_ww_mean ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)

xtset city_id year

tempfile panel
save `panel', replace

local xvars ///
    fund_est_count ///
    fund_est_scale ///
    fund_est_count_cum ///
    fund_est_scale_cum

local yvars ///
    pat_invent_apply ///
    pat_utility_apply ///
    pat_apply_total

local dvars ///
    debt_pressure ///
    debt_pressure_l1

local earlyvars ///
    early_inv_amt ///
    early_inv_count ///
    early_inv_amt_share ///
    early_inv_count_share

local soccapvars ///
    soccap_fund_count ///
    soccap_amt ///
    gov_amt ///
    gp_amt ///
    unknown_amt ///
    fund_commit_total ///
    matched_commit_amt ///
    soccap_share_total ///
    gov_share_total ///
    soccap_leverage ///
    matched_share_total

local fcvars ///
    fcity_sa_mean ///
    fcity_fc_mean ///
    fcity_kz_mean ///
    fcity_ww_mean

local ctrls ///
    ln_gdp ///
    ln_fiscal_scitech ///
    ln_pop ///
    ln_secondary ///
    ln_fdi

tempname posth
tempfile results
postfile `posth' ///
    str16 category ///
    str12 model_type ///
    str20 yvar ///
    str20 xvar ///
    str18 dvar ///
    str22 mvar ///
    str8 spec ///
    str8 step ///
    double b_xd se_xd p_xd ///
    double b_m se_m p_m ///
    double b_xm se_xm p_xm ///
    double b_dm se_dm p_dm ///
    double b_xdm se_xdm p_xdm ///
    double N r2w using `results', replace

foreach spec in noctrl ctrl {

    local ctrl_part ""
    if "`spec'" == "ctrl" {
        local ctrl_part "`ctrls'"
    }

    foreach category in early soccap fc {

        local mlist ""
        if "`category'" == "early" {
            local mlist "`earlyvars'"
        }
        else if "`category'" == "soccap" {
            local mlist "`soccapvars'"
        }
        else if "`category'" == "fc" {
            local mlist "`fcvars'"
        }

        foreach x of local xvars {
            foreach d of local dvars {
                foreach m of local mlist {

                    * Model 1: mediated moderation / mechanism equation
                    use `panel', clear
                    xtset city_id year
                    preserve
                    if "`spec'" == "ctrl" {
                        keep if !missing(`m', `x', `d', `ctrls', city_id, year)
                    }
                    else {
                        keep if !missing(`m', `x', `d', city_id, year)
                    }
                    capture noisily xtreg `m' c.`x'##c.`d' `ctrl_part' i.year, fe vce(cluster city_id)
                    if _rc == 0 {
                        local b_xd = _b[c.`x'#c.`d']
                        local se_xd = _se[c.`x'#c.`d']
                        local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                        post `posth' ///
                            ("`category'") ("mediated") ("") ("`x'") ("`d'") ("`m'") ("`spec'") ("M_eq") ///
                            (`b_xd') (`se_xd') (`p_xd') ///
                            (.) (.) (.) ///
                            (.) (.) (.) ///
                            (.) (.) (.) ///
                            (.) (.) (.) ///
                            (e(N)) (e(r2_w))
                    }
                    restore

                    * Model 1: mediated moderation / outcome equation
                    foreach y of local yvars {
                        use `panel', clear
                        xtset city_id year
                        preserve
                        if "`spec'" == "ctrl" {
                            keep if !missing(`y', `m', `x', `d', `ctrls', city_id, year)
                        }
                        else {
                            keep if !missing(`y', `m', `x', `d', city_id, year)
                        }
                        capture noisily xtreg `y' c.`x'##c.`d' `m' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local b_xd = _b[c.`x'#c.`d']
                            local se_xd = _se[c.`x'#c.`d']
                            local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                            local b_m = _b[`m']
                            local se_m = _se[`m']
                            local p_m = 2 * ttail(e(df_r), abs(`b_m' / `se_m'))
                            post `posth' ///
                                ("`category'") ("mediated") ("`y'") ("`x'") ("`d'") ("`m'") ("`spec'") ("Y_eq") ///
                                (`b_xd') (`se_xd') (`p_xd') ///
                                (`b_m') (`se_m') (`p_m') ///
                                (.) (.) (.) ///
                                (.) (.) (.) ///
                                (.) (.) (.) ///
                                (e(N)) (e(r2_w))
                        }
                        restore
                    }

                    * Model 2: triple interaction / moderated mechanism
                    foreach y of local yvars {
                        use `panel', clear
                        xtset city_id year
                        preserve
                        if "`spec'" == "ctrl" {
                            keep if !missing(`y', `m', `x', `d', `ctrls', city_id, year)
                        }
                        else {
                            keep if !missing(`y', `m', `x', `d', city_id, year)
                        }
                        capture noisily xtreg `y' c.`x'##c.`d'##c.`m' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local b_xd = _b[c.`x'#c.`d']
                            local se_xd = _se[c.`x'#c.`d']
                            local p_xd = 2 * ttail(e(df_r), abs(`b_xd' / `se_xd'))
                            local b_xm = _b[c.`x'#c.`m']
                            local se_xm = _se[c.`x'#c.`m']
                            local p_xm = 2 * ttail(e(df_r), abs(`b_xm' / `se_xm'))
                            local b_dm = _b[c.`d'#c.`m']
                            local se_dm = _se[c.`d'#c.`m']
                            local p_dm = 2 * ttail(e(df_r), abs(`b_dm' / `se_dm'))
                            local b_xdm = _b[c.`x'#c.`d'#c.`m']
                            local se_xdm = _se[c.`x'#c.`d'#c.`m']
                            local p_xdm = 2 * ttail(e(df_r), abs(`b_xdm' / `se_xdm'))
                            post `posth' ///
                                ("`category'") ("triple") ("`y'") ("`x'") ("`d'") ("`m'") ("`spec'") ("full") ///
                                (`b_xd') (`se_xd') (`p_xd') ///
                                (.) (.) (.) ///
                                (`b_xm') (`se_xm') (`p_xm') ///
                                (`b_dm') (`se_dm') (`p_dm') ///
                                (`b_xdm') (`se_xdm') (`p_xdm') ///
                                (e(N)) (e(r2_w))
                        }
                        restore
                    }
                }
            }
        }
    }
}

postclose `posth'
use `results', clear
sort category model_type mvar xvar dvar yvar spec step
export delimited using "`resultcsv'", replace
list in 1/40, sepby(category model_type)

log close
