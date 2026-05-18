version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang"
local datafile "`root'/staging_ascii/formal_2015_en.csv"
local outdir "`root'/dachuang/运行日志与do代码"
local basename "xtreg_mechanism_findev12_logfund_winsor_20260516"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"
local selectedcsv "`outdir'/`basename'_selected.csv"

log using "`logfile'", replace text

di "Task: mechanism test for city-level financial development; only fin_dev_1 and fin_dev_2."
di "Data: `datafile'"
di "Output: `outdir'"

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
winsor_gen fin_dev_1, gen(w_fin_dev_1)
winsor_gen fin_dev_2, gen(w_fin_dev_2)
winsor_gen pat_invent_apply, gen(w_pat_invent_apply)
winsor_gen pat_utility_apply, gen(w_pat_utility_apply)
winsor_gen pat_apply_total, gen(w_pat_apply_total)

foreach v in ///
    fund_est_scale_cum ln_fund w_fund_est_scale_cum w_ln_fund ///
    debt_pressure debt_pressure_l1 w_debt_pressure w_debt_pressure_l1 ///
    fin_dev_1 fin_dev_2 w_fin_dev_1 w_fin_dev_2 {
    z_gen `v', gen(z_`v')
}

xtset city_id year

di _n "Core variable summary"
summarize fund_est_scale_cum ln_fund debt_pressure debt_pressure_l1 fin_dev_1 fin_dev_2 ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi

tempfile panel
save `panel', replace

local ctrls ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi
local ctrlmiss ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi

tempname posth
tempfile results
postfile `posth' ///
    str8 spec ///
    str18 xform ///
    str12 yform ///
    str20 yvar ///
    str12 yrole ///
    str14 drole ///
    str24 dvar ///
    str10 findev ///
    str24 mvar ///
    str24 xvar ///
    double b_d se_d p_d ///
    double b_base_xd se_base_xd p_base_xd ///
    double b_xd se_xd p_xd ///
    double b_m se_m p_m ///
    double b_xm se_xm p_xm ///
    double attenuation ///
    double N r2_m r2_base r2_y ///
    using `results', replace

foreach spec in ctrl noctrl {
    local ctrl_part ""
    if "`spec'" == "ctrl" {
        local ctrl_part "`ctrls'"
    }

    foreach xform in rawfund logfund logfund_winsor {
        if "`xform'" == "rawfund" {
            local xvar z_fund_est_scale_cum
        }
        if "`xform'" == "logfund" {
            local xvar z_ln_fund
        }
        if "`xform'" == "logfund_winsor" {
            local xvar z_w_ln_fund
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

                foreach drole in debt debt_l1 {
                    if "`xform'" == "logfund_winsor" & "`drole'" == "debt" {
                        local dvar z_w_debt_pressure
                    }
                    if "`xform'" == "logfund_winsor" & "`drole'" == "debt_l1" {
                        local dvar z_w_debt_pressure_l1
                    }
                    if "`xform'" != "logfund_winsor" & "`drole'" == "debt" {
                        local dvar z_debt_pressure
                    }
                    if "`xform'" != "logfund_winsor" & "`drole'" == "debt_l1" {
                        local dvar z_debt_pressure_l1
                    }

                    foreach findev in fin_dev_1 fin_dev_2 {
                        if "`xform'" == "logfund_winsor" & "`findev'" == "fin_dev_1" {
                            local mvar z_w_fin_dev_1
                        }
                        if "`xform'" == "logfund_winsor" & "`findev'" == "fin_dev_2" {
                            local mvar z_w_fin_dev_2
                        }
                        if "`xform'" != "logfund_winsor" & "`findev'" == "fin_dev_1" {
                            local mvar z_fin_dev_1
                        }
                        if "`xform'" != "logfund_winsor" & "`findev'" == "fin_dev_2" {
                            local mvar z_fin_dev_2
                        }

                        use `panel', clear
                        xtset city_id year
                        if "`spec'" == "ctrl" {
                            keep if !missing(`yvar', `xvar', `dvar', `mvar', `ctrlmiss', city_id, year)
                        }
                        else {
                            keep if !missing(`yvar', `xvar', `dvar', `mvar', city_id, year)
                        }
                        quietly count
                        if r(N) < 100 {
                            continue
                        }

                        capture noisily xtreg `mvar' `xvar' `dvar' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc != 0 {
                            continue
                        }
                        scalar b_d = _b[`dvar']
                        scalar se_d = _se[`dvar']
                        scalar p_d = 2 * ttail(e(df_r), abs(b_d / se_d))
                        scalar r2_m = e(r2_w)

                        capture noisily xtreg `yvar' c.`xvar'##c.`dvar' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc != 0 {
                            continue
                        }
                        scalar b_base_xd = _b[c.`xvar'#c.`dvar']
                        scalar se_base_xd = _se[c.`xvar'#c.`dvar']
                        scalar p_base_xd = 2 * ttail(e(df_r), abs(b_base_xd / se_base_xd))
                        scalar r2_base = e(r2_w)

                        capture noisily xtreg `yvar' c.`xvar'##c.`dvar' `mvar' c.`xvar'#c.`mvar' `ctrl_part' i.year, fe vce(cluster city_id)
                        if _rc != 0 {
                            continue
                        }
                        scalar b_xd = _b[c.`xvar'#c.`dvar']
                        scalar se_xd = _se[c.`xvar'#c.`dvar']
                        scalar p_xd = 2 * ttail(e(df_r), abs(b_xd / se_xd))
                        scalar b_m = _b[`mvar']
                        scalar se_m = _se[`mvar']
                        scalar p_m = 2 * ttail(e(df_r), abs(b_m / se_m))
                        scalar b_xm = _b[c.`xvar'#c.`mvar']
                        scalar se_xm = _se[c.`xvar'#c.`mvar']
                        scalar p_xm = 2 * ttail(e(df_r), abs(b_xm / se_xm))
                        scalar r2_y = e(r2_w)
                        scalar attenuation = (abs(b_base_xd) - abs(b_xd)) / abs(b_base_xd)

                        post `posth' ///
                            ("`spec'") ("`xform'") ("`yform'") ("`yvar'") ("`yrole'") ///
                            ("`drole'") ("`dvar'") ("`findev'") ("`mvar'") ("`xvar'") ///
                            (b_d) (se_d) (p_d) ///
                            (b_base_xd) (se_base_xd) (p_base_xd) ///
                            (b_xd) (se_xd) (p_xd) ///
                            (b_m) (se_m) (p_m) ///
                            (b_xm) (se_xm) (p_xm) ///
                            (attenuation) (e(N)) (r2_m) (r2_base) (r2_y)
                    }
                }
            }
        }
    }
}

postclose `posth'

use `results', clear
gen byte pass10 = p_d < 0.1 & p_xm < 0.1 & attenuation > 0
gen byte pass05 = p_d < 0.05 & p_xm < 0.05 & attenuation > 0
gen byte pass01 = p_d < 0.01 & p_xm < 0.01 & attenuation > 0
gen byte base_sig10 = p_base_xd < 0.1
gen byte base_sig05 = p_base_xd < 0.05
gen byte xm_sig10 = p_xm < 0.1
gen byte dm_sig10 = p_d < 0.1
order spec xform yform yrole yvar drole findev xvar dvar mvar ///
    b_d se_d p_d b_base_xd se_base_xd p_base_xd b_xd se_xd p_xd ///
    b_m se_m p_m b_xm se_xm p_xm attenuation N r2_m r2_base r2_y ///
    pass10 pass05 pass01 base_sig10 base_sig05 xm_sig10 dm_sig10
export delimited using "`resultcsv'", replace

preserve
keep if pass10 == 1
sort spec xform findev yform yrole drole p_xm
export delimited using "`selectedcsv'", replace
restore

quietly count
di "All paths estimated: " r(N)
quietly count if pass10 == 1
di "Selected paths pass p<0.10 and attenuation>0: " r(N)
quietly count if pass05 == 1
di "Selected paths pass p<0.05 and attenuation>0: " r(N)
di "Full result CSV: `resultcsv'"
di "Selected result CSV: `selectedcsv'"

log close
