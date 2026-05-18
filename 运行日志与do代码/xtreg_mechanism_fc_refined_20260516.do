version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_mechanism_fc_refined_20260516"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"
local selectedcsv "`outdir'/`basename'_selected.csv"
local diagcsv "`outdir'/`basename'_diagnostics.csv"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    fcity_sa_mean fcity_sa_firms fcity_sa_median ///
    fcity_fc_mean fcity_fc_firms fcity_fc_median ///
    fcity_kz_mean fcity_kz_firms fcity_kz_median ///
    fcity_ww_mean fcity_ww_firms fcity_ww_median ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen double ln_gdp = ln(gdp + 1)
gen double ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen double ln_pop = ln(population_resident + 1)
gen double ln_secondary = ln(secondary_industry + 1)
gen double ln_fdi = ln(fdi_actual + 1)

gen double lny_invent = ln(pat_invent_apply + 1)
gen double lny_utility = ln(pat_utility_apply + 1)
gen double lny_total = ln(pat_apply_total + 1)

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

winsor_gen fund_est_scale_cum, gen(w_fund_est_scale_cum)
winsor_gen debt_pressure, gen(w_debt_pressure)
winsor_gen debt_pressure_l1, gen(w_debt_pressure_l1)
winsor_gen pat_invent_apply, gen(w_pat_invent_apply)
winsor_gen pat_utility_apply, gen(w_pat_utility_apply)
winsor_gen pat_apply_total, gen(w_pat_apply_total)
winsor_gen fcity_sa_mean, gen(w_fcity_sa_mean)
winsor_gen fcity_fc_mean, gen(w_fcity_fc_mean)
winsor_gen fcity_kz_mean, gen(w_fcity_kz_mean)
winsor_gen fcity_ww_mean, gen(w_fcity_ww_mean)

foreach v in ///
    fund_est_scale_cum debt_pressure debt_pressure_l1 ///
    fcity_sa_mean fcity_fc_mean fcity_kz_mean fcity_ww_mean ///
    w_fund_est_scale_cum w_debt_pressure w_debt_pressure_l1 ///
    w_fcity_sa_mean w_fcity_fc_mean w_fcity_kz_mean w_fcity_ww_mean {
    quietly summarize `v'
    gen double z_`v' = (`v' - r(mean)) / r(sd)
}

xtset city_id year

tempfile panel
save `panel', replace

local ctrls ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi
local ctrlmiss ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi

tempname posth
tempfile results
postfile `posth' ///
    str12 model_family ///
    str8 spec ///
    str12 transform ///
    str10 sample_rule ///
    str12 yrole ///
    str12 drole ///
    str8 mrole ///
    str8 step ///
    str32 yvar ///
    str32 xvar ///
    str32 dvar ///
    str32 mvar ///
    str32 term1 ///
    double b1 se1 p1 ///
    str32 term2 ///
    double b2 se2 p2 ///
    str32 term3 ///
    double b3 se3 p3 ///
    str32 aux_name ///
    double aux_b aux_p ///
    double beta_b beta_p attenuation ///
    double N r2w ///
    byte pass10 pass05 ///
    str40 verdict using `results', replace

foreach transform in count logy winsor {

    if "`transform'" == "winsor" {
        local xvar z_w_fund_est_scale_cum
    }
    else {
        local xvar z_fund_est_scale_cum
    }

    foreach yrole in invent utility total {

        if "`transform'" == "count" & "`yrole'" == "invent" {
            local yvar pat_invent_apply
        }
        if "`transform'" == "count" & "`yrole'" == "utility" {
            local yvar pat_utility_apply
        }
        if "`transform'" == "count" & "`yrole'" == "total" {
            local yvar pat_apply_total
        }
        if "`transform'" == "logy" & "`yrole'" == "invent" {
            local yvar lny_invent
        }
        if "`transform'" == "logy" & "`yrole'" == "utility" {
            local yvar lny_utility
        }
        if "`transform'" == "logy" & "`yrole'" == "total" {
            local yvar lny_total
        }
        if "`transform'" == "winsor" & "`yrole'" == "invent" {
            local yvar w_pat_invent_apply
        }
        if "`transform'" == "winsor" & "`yrole'" == "utility" {
            local yvar w_pat_utility_apply
        }
        if "`transform'" == "winsor" & "`yrole'" == "total" {
            local yvar w_pat_apply_total
        }

        foreach drole in debt debt_l1 {

            if "`transform'" == "winsor" & "`drole'" == "debt" {
                local dvar z_w_debt_pressure
                local draw debt_pressure
            }
            if "`transform'" == "winsor" & "`drole'" == "debt_l1" {
                local dvar z_w_debt_pressure_l1
                local draw debt_pressure_l1
            }
            if "`transform'" != "winsor" & "`drole'" == "debt" {
                local dvar z_debt_pressure
                local draw debt_pressure
            }
            if "`transform'" != "winsor" & "`drole'" == "debt_l1" {
                local dvar z_debt_pressure_l1
                local draw debt_pressure_l1
            }

            foreach mrole in sa fc kz ww {

                if "`mrole'" == "sa" {
                    local mraw fcity_sa_mean
                    local firmvar fcity_sa_firms
                }
                if "`mrole'" == "fc" {
                    local mraw fcity_fc_mean
                    local firmvar fcity_fc_firms
                }
                if "`mrole'" == "kz" {
                    local mraw fcity_kz_mean
                    local firmvar fcity_kz_firms
                }
                if "`mrole'" == "ww" {
                    local mraw fcity_ww_mean
                    local firmvar fcity_ww_firms
                }

                if "`transform'" == "winsor" {
                    local mvar z_w_`mraw'
                }
                else {
                    local mvar z_`mraw'
                }

                foreach sample_rule in all firm_ge3 firm_ge5 {
                    foreach spec in noctrl ctrl {

                        local ctrl_part ""
                        if "`spec'" == "ctrl" {
                            local ctrl_part "`ctrls'"
                        }

                        use `panel', clear
                        xtset city_id year
                        if "`sample_rule'" == "firm_ge3" {
                            keep if `firmvar' >= 3 & !missing(`firmvar')
                        }
                        if "`sample_rule'" == "firm_ge5" {
                            keep if `firmvar' >= 5 & !missing(`firmvar')
                        }
                        if "`spec'" == "ctrl" {
                            keep if !missing(`yvar', `xvar', `dvar', `mvar', `ctrlmiss', city_id, year)
                        }
                        else {
                            keep if !missing(`yvar', `xvar', `dvar', `mvar', city_id, year)
                        }

                        local beta_b = .
                        local beta_se = .
                        local beta_p = .
                        local beta_N = .
                        local beta_r2w = .
                        capture noisily xtreg `yvar' c.`xvar'##c.`dvar' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local beta_b = _b[c.`xvar'#c.`dvar']
                            capture local beta_se = _se[c.`xvar'#c.`dvar']
                            if `beta_se' < . & `beta_se' > 0 {
                                local beta_p = 2 * ttail(e(df_r), abs(`beta_b' / `beta_se'))
                            }
                            local beta_N = e(N)
                            local beta_r2w = e(r2_w)
                            post `posth' ///
                                ("baseline") ("`spec'") ("`transform'") ("`sample_rule'") ///
                                ("`yrole'") ("`drole'") ("`mrole'") ("Y_eq") ///
                                ("`yvar'") ("`xvar'") ("`dvar'") ("`mvar'") ///
                                ("XxD") (`beta_b') (`beta_se') (`beta_p') ///
                                ("") (.) (.) (.) ///
                                ("") (.) (.) (.) ///
                                ("") (.) (.) ///
                                (`beta_b') (`beta_p') (.) ///
                                (`beta_N') (`beta_r2w') ///
                                (0) (0) ("baseline")
                        }

                        local a3_b = .
                        local a3_se = .
                        local a3_p = .
                        local a3_N = .
                        local a3_r2w = .
                        capture noisily xtreg `mvar' c.`xvar'##c.`dvar' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local a3_b = _b[c.`xvar'#c.`dvar']
                            capture local a3_se = _se[c.`xvar'#c.`dvar']
                            if `a3_se' < . & `a3_se' > 0 {
                                local a3_p = 2 * ttail(e(df_r), abs(`a3_b' / `a3_se'))
                            }
                            local a3_N = e(N)
                            local a3_r2w = e(r2_w)
                            post `posth' ///
                                ("mediated") ("`spec'") ("`transform'") ("`sample_rule'") ///
                                ("`yrole'") ("`drole'") ("`mrole'") ("M_eq") ///
                                ("") ("`xvar'") ("`dvar'") ("`mvar'") ///
                                ("XxD_to_M") (`a3_b') (`a3_se') (`a3_p') ///
                                ("") (.) (.) (.) ///
                                ("") (.) (.) (.) ///
                                ("") (.) (.) ///
                                (`beta_b') (`beta_p') (.) ///
                                (`a3_N') (`a3_r2w') ///
                                (0) (0) ("mechanism_equation")
                        }

                        local c3_b = .
                        local c3_se = .
                        local c3_p = .
                        local c4_b = .
                        local c4_se = .
                        local c4_p = .
                        local cN = .
                        local cr2w = .
                        capture noisily xtreg `yvar' c.`xvar'##c.`dvar' `mvar' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local c3_b = _b[c.`xvar'#c.`dvar']
                            capture local c3_se = _se[c.`xvar'#c.`dvar']
                            if `c3_se' < . & `c3_se' > 0 {
                                local c3_p = 2 * ttail(e(df_r), abs(`c3_b' / `c3_se'))
                            }
                            capture local c4_b = _b[`mvar']
                            capture local c4_se = _se[`mvar']
                            if `c4_se' < . & `c4_se' > 0 {
                                local c4_p = 2 * ttail(e(df_r), abs(`c4_b' / `c4_se'))
                            }
                            local attenuation = abs(`beta_b') - abs(`c3_b')
                            local pass10 = (`beta_p' <= 0.10 & `a3_p' <= 0.10 & `c4_p' <= 0.10 & `attenuation' > 0)
                            local pass05 = (`beta_p' <= 0.05 & `a3_p' <= 0.05 & `c4_p' <= 0.05 & `attenuation' > 0)
                            local verdict "not_pass"
                            if `pass10' == 1 {
                                local verdict "pass_10pct_mediated"
                            }
                            if `pass05' == 1 {
                                local verdict "pass_5pct_mediated"
                            }
                            local cN = e(N)
                            local cr2w = e(r2_w)
                            post `posth' ///
                                ("mediated") ("`spec'") ("`transform'") ("`sample_rule'") ///
                                ("`yrole'") ("`drole'") ("`mrole'") ("Y_eq") ///
                                ("`yvar'") ("`xvar'") ("`dvar'") ("`mvar'") ///
                                ("XxD_direct") (`c3_b') (`c3_se') (`c3_p') ///
                                ("M") (`c4_b') (`c4_se') (`c4_p') ///
                                ("") (.) (.) (.) ///
                                ("a3_XxD_to_M") (`a3_b') (`a3_p') ///
                                (`beta_b') (`beta_p') (`attenuation') ///
                                (`cN') (`cr2w') ///
                                (`pass10') (`pass05') ("`verdict'")
                        }

                        local d2_b = .
                        local d2_se = .
                        local d2_p = .
                        local dx_b = .
                        local dx_se = .
                        local dx_p = .
                        local dN = .
                        local dr2w = .
                        capture noisily xtreg `mvar' `xvar' `dvar' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local d2_b = _b[`dvar']
                            capture local d2_se = _se[`dvar']
                            if `d2_se' < . & `d2_se' > 0 {
                                local d2_p = 2 * ttail(e(df_r), abs(`d2_b' / `d2_se'))
                            }
                            capture local dx_b = _b[`xvar']
                            capture local dx_se = _se[`xvar']
                            if `dx_se' < . & `dx_se' > 0 {
                                local dx_p = 2 * ttail(e(df_r), abs(`dx_b' / `dx_se'))
                            }
                            local dN = e(N)
                            local dr2w = e(r2_w)
                            post `posth' ///
                                ("moderator") ("`spec'") ("`transform'") ("`sample_rule'") ///
                                ("`yrole'") ("`drole'") ("`mrole'") ("M_eq") ///
                                ("") ("`xvar'") ("`dvar'") ("`mvar'") ///
                                ("D_to_M") (`d2_b') (`d2_se') (`d2_p') ///
                                ("X_to_M") (`dx_b') (`dx_se') (`dx_p') ///
                                ("") (.) (.) (.) ///
                                ("") (.) (.) ///
                                (`beta_b') (`beta_p') (.) ///
                                (`dN') (`dr2w') ///
                                (0) (0) ("mechanism_equation")
                        }

                        local e3_b = .
                        local e3_se = .
                        local e3_p = .
                        local e4_b = .
                        local e4_se = .
                        local e4_p = .
                        local e5_b = .
                        local e5_se = .
                        local e5_p = .
                        local eN = .
                        local er2w = .
                        capture noisily xtreg `yvar' c.`xvar'##c.`dvar' `mvar' c.`xvar'#c.`mvar' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            capture local e3_b = _b[c.`xvar'#c.`dvar']
                            capture local e3_se = _se[c.`xvar'#c.`dvar']
                            if `e3_se' < . & `e3_se' > 0 {
                                local e3_p = 2 * ttail(e(df_r), abs(`e3_b' / `e3_se'))
                            }
                            capture local e4_b = _b[`mvar']
                            capture local e4_se = _se[`mvar']
                            if `e4_se' < . & `e4_se' > 0 {
                                local e4_p = 2 * ttail(e(df_r), abs(`e4_b' / `e4_se'))
                            }
                            capture local e5_b = _b[c.`xvar'#c.`mvar']
                            capture local e5_se = _se[c.`xvar'#c.`mvar']
                            if `e5_se' < . & `e5_se' > 0 {
                                local e5_p = 2 * ttail(e(df_r), abs(`e5_b' / `e5_se'))
                            }
                            local attenuation = abs(`beta_b') - abs(`e3_b')
                            local pass10 = (`beta_p' <= 0.10 & `d2_p' <= 0.10 & `e5_p' <= 0.10 & `attenuation' > 0)
                            local pass05 = (`beta_p' <= 0.05 & `d2_p' <= 0.05 & `e5_p' <= 0.05 & `attenuation' > 0)
                            local verdict "not_pass"
                            if `pass10' == 1 {
                                local verdict "pass_10pct_moderator"
                            }
                            if `pass05' == 1 {
                                local verdict "pass_5pct_moderator"
                            }
                            local eN = e(N)
                            local er2w = e(r2_w)
                            post `posth' ///
                                ("moderator") ("`spec'") ("`transform'") ("`sample_rule'") ///
                                ("`yrole'") ("`drole'") ("`mrole'") ("Y_eq") ///
                                ("`yvar'") ("`xvar'") ("`dvar'") ("`mvar'") ///
                                ("XxD_direct") (`e3_b') (`e3_se') (`e3_p') ///
                                ("M") (`e4_b') (`e4_se') (`e4_p') ///
                                ("XxM") (`e5_b') (`e5_se') (`e5_p') ///
                                ("d2_D_to_M") (`d2_b') (`d2_p') ///
                                (`beta_b') (`beta_p') (`attenuation') ///
                                (`eN') (`er2w') ///
                                (`pass10') (`pass05') ("`verdict'")
                        }
                    }
                }
            }
        }
    }
}

postclose `posth'
use `results', clear

gen double main_mech_p = .
replace main_mech_p = p2 if model_family == "mediated" & step == "Y_eq"
replace main_mech_p = p3 if model_family == "moderator" & step == "Y_eq"

gen str3 sig1 = ""
replace sig1 = "*" if p1 <= 0.10
replace sig1 = "**" if p1 <= 0.05
replace sig1 = "***" if p1 <= 0.01

gen str3 sig2 = ""
replace sig2 = "*" if p2 <= 0.10
replace sig2 = "**" if p2 <= 0.05
replace sig2 = "***" if p2 <= 0.01

gen str3 sig3 = ""
replace sig3 = "*" if p3 <= 0.10
replace sig3 = "**" if p3 <= 0.05
replace sig3 = "***" if p3 <= 0.01

export delimited using "`resultcsv'", replace

preserve
    keep if step == "Y_eq" & pass10 == 1
    gsort -pass05 main_mech_p aux_p -attenuation
    export delimited using "`selectedcsv'", replace
restore

preserve
    keep if step == "Y_eq"
    contract model_family transform sample_rule spec mrole pass10 pass05, freq(n)
    export delimited using "`diagcsv'", replace
restore

di as text "resultcsv = `resultcsv'"
di as text "selectedcsv = `selectedcsv'"
di as text "diagcsv = `diagcsv'"
log close
