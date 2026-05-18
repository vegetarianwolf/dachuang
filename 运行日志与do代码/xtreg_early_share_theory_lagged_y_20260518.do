version 18
clear all
set more off
capture log close

cd "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"

local basename "xtreg_early_share_theory_lagged_y_20260518"
local datafile "../../staging_ascii/panel_2015_2024_regression_ascii_clean.csv"
local logfile "`basename'.log"
local resultcsv "`basename'_results.csv"
local selectedcsv "`basename'_selected.csv"

log using "`logfile'", replace text

display "Task: lagged innovation-output extension for early-investment share mechanism."
display "Share variables are raw/winsor/asinh-sqrt only; no log transform on share variables."

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum fund_inv_count ///
    debt_pressure_l1 ///
    early_inv_count_share ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    pat_invent_grant pat_utility_grant pat_grant_total ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

xtset city_id year
foreach y in pat_invent_apply pat_utility_apply pat_apply_total pat_invent_grant pat_utility_grant pat_grant_total {
    gen double F1_`y' = F.`y'
    gen double F2_`y' = F2.`y'
    gen double F3_`y' = F3.`y'
    gen double ln_`y' = ln(`y' + 1)
    gen double ln_F1_`y' = ln(F1_`y' + 1)
    gen double ln_F2_`y' = ln(F2_`y' + 1)
    gen double ln_F3_`y' = ln(F3_`y' + 1)
}

gen double ln_gdp = ln(gdp + 1)
gen double ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen double ln_pop = ln(population_resident + 1)
gen double ln_secondary = ln(secondary_industry + 1)
gen double ln_fdi = ln(fdi_actual + 1)
local controls ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi

capture program drop winsor_gen
program define winsor_gen
    syntax varname, GEN(name)
    quietly summarize `varlist', detail
    local lo = r(p1)
    local hi = r(p99)
    gen double `gen' = `varlist'
    replace `gen' = `lo' if `gen' < `lo' & !missing(`gen')
    replace `gen' = `hi' if `gen' > `hi' & !missing(`gen')
end

winsor_gen debt_pressure_l1, gen(w_debt_pressure_l1)
winsor_gen early_inv_count_share, gen(w_early_inv_count_share)
gen double asin_early_inv_count_share = asin(sqrt(early_inv_count_share)) if inrange(early_inv_count_share, 0, 1)
gen double asin_w_early_inv_count_share = asin(sqrt(w_early_inv_count_share)) if inrange(w_early_inv_count_share, 0, 1)
gen double ln_fund_est_scale_cum = ln(fund_est_scale_cum + 1)

foreach v in ln_fund_est_scale_cum debt_pressure_l1 w_debt_pressure_l1 {
    quietly summarize `v'
    gen double z_`v' = (`v' - r(mean)) / r(sd)
}

quietly summarize debt_pressure_l1 if !missing(debt_pressure_l1), detail
gen byte ok_debt_l1_5_95 = inrange(debt_pressure_l1, r(p5), r(p95))

tempfile panel
save `panel', replace

tempname posth
tempfile results
postfile `posth' ///
    str12 model str18 ybase str8 lag str8 ytransform ///
    str12 dtransform str12 mtransform str24 sample_rule ///
    str32 yvar str32 dvar str32 mvar ///
    double N beta_b beta_se beta_p ///
    double path1_b path1_se path1_p ///
    double path2_b path2_se path2_p ///
    double direct_b direct_se direct_p ///
    double attenuation r2w ///
    byte theory10 theory05 using `results', replace

local ybases pat_invent_apply pat_utility_apply pat_apply_total pat_invent_grant pat_utility_grant pat_grant_total
local lags cur F1 F2 F3
local ytransforms count logy
local dtransforms raw winsor
local mtransforms raw winsor asin asin_w
local sample_rules denom_ge2 denom_ge3 interior interior_debt_trim denom_ge2_debt_trim denom_ge3_debt_trim no_covid_denom_ge2

foreach ybase of local ybases {
    foreach lag of local lags {
        foreach ytransform of local ytransforms {
            if "`lag'" == "cur" & "`ytransform'" == "count" local yvar `ybase'
            if "`lag'" == "cur" & "`ytransform'" == "logy" local yvar ln_`ybase'
            if "`lag'" != "cur" & "`ytransform'" == "count" local yvar `lag'_`ybase'
            if "`lag'" != "cur" & "`ytransform'" == "logy" local yvar ln_`lag'_`ybase'

            foreach dtransform of local dtransforms {
                if "`dtransform'" == "raw" local dvar z_debt_pressure_l1
                if "`dtransform'" == "winsor" local dvar z_w_debt_pressure_l1

                foreach mtransform of local mtransforms {
                    if "`mtransform'" == "raw" local mvar early_inv_count_share
                    if "`mtransform'" == "winsor" local mvar w_early_inv_count_share
                    if "`mtransform'" == "asin" local mvar asin_early_inv_count_share
                    if "`mtransform'" == "asin_w" local mvar asin_w_early_inv_count_share

                    foreach sample_rule of local sample_rules {
                        use `panel', clear
                        xtset city_id year
                        egen miss_needed = rowmiss(`yvar' z_ln_fund_est_scale_cum `dvar' `mvar' `controls' city_id year)
                        keep if miss_needed == 0
                        drop miss_needed
                        keep if inrange(early_inv_count_share, 0, 1)

                        if "`sample_rule'" == "denom_ge2" keep if fund_inv_count >= 2 & !missing(fund_inv_count)
                        if "`sample_rule'" == "denom_ge3" keep if fund_inv_count >= 3 & !missing(fund_inv_count)
                        if "`sample_rule'" == "interior" keep if early_inv_count_share > 0 & early_inv_count_share < 1
                        if "`sample_rule'" == "interior_debt_trim" keep if early_inv_count_share > 0 & early_inv_count_share < 1 & ok_debt_l1_5_95 == 1
                        if "`sample_rule'" == "denom_ge2_debt_trim" keep if fund_inv_count >= 2 & !missing(fund_inv_count) & ok_debt_l1_5_95 == 1
                        if "`sample_rule'" == "denom_ge3_debt_trim" keep if fund_inv_count >= 3 & !missing(fund_inv_count) & ok_debt_l1_5_95 == 1
                        if "`sample_rule'" == "no_covid_denom_ge2" keep if fund_inv_count >= 2 & !missing(fund_inv_count) & !inrange(year, 2020, 2022)

                        quietly count
                        if r(N) < 70 continue

                        capture quietly xtreg `yvar' c.z_ln_fund_est_scale_cum##c.`dvar' `controls' i.year, fe vce(cluster city_id)
                        if _rc != 0 continue
                        local beta_b = _b[c.z_ln_fund_est_scale_cum#c.`dvar']
                        local beta_se = _se[c.z_ln_fund_est_scale_cum#c.`dvar']
                        local beta_p = 2 * ttail(e(df_r), abs(`beta_b' / `beta_se'))

                        local path1_b = .
                        local path1_se = .
                        local path1_p = .
                        capture quietly xtreg `mvar' c.z_ln_fund_est_scale_cum##c.`dvar' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local path1_b = _b[c.z_ln_fund_est_scale_cum#c.`dvar']
                            local path1_se = _se[c.z_ln_fund_est_scale_cum#c.`dvar']
                            local path1_p = 2 * ttail(e(df_r), abs(`path1_b' / `path1_se'))
                        }

                        capture quietly xtreg `yvar' c.z_ln_fund_est_scale_cum##c.`dvar' `mvar' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local direct_b = _b[c.z_ln_fund_est_scale_cum#c.`dvar']
                            local direct_se = _se[c.z_ln_fund_est_scale_cum#c.`dvar']
                            local direct_p = 2 * ttail(e(df_r), abs(`direct_b' / `direct_se'))
                            local path2_b = _b[`mvar']
                            local path2_se = _se[`mvar']
                            local path2_p = 2 * ttail(e(df_r), abs(`path2_b' / `path2_se'))
                            local attenuation = abs(`beta_b') - abs(`direct_b')
                            local pass10 = (`beta_b' < 0 & `beta_p' <= 0.10 & `path1_b' < 0 & `path1_p' <= 0.10 & `path2_b' > 0 & `path2_p' <= 0.10)
                            local pass05 = (`beta_b' < 0 & `beta_p' <= 0.05 & `path1_b' < 0 & `path1_p' <= 0.05 & `path2_b' > 0 & `path2_p' <= 0.05)
                            post `posth' ("mediated") ("`ybase'") ("`lag'") ("`ytransform'") ("`dtransform'") ("`mtransform'") ("`sample_rule'") ///
                                ("`yvar'") ("`dvar'") ("`mvar'") (e(N)) ///
                                (`beta_b') (`beta_se') (`beta_p') ///
                                (`path1_b') (`path1_se') (`path1_p') ///
                                (`path2_b') (`path2_se') (`path2_p') ///
                                (`direct_b') (`direct_se') (`direct_p') ///
                                (`attenuation') (e(r2_w)) (`pass10') (`pass05')
                        }

                        local path1_b = .
                        local path1_se = .
                        local path1_p = .
                        capture quietly xtreg `mvar' z_ln_fund_est_scale_cum `dvar' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local path1_b = _b[`dvar']
                            local path1_se = _se[`dvar']
                            local path1_p = 2 * ttail(e(df_r), abs(`path1_b' / `path1_se'))
                        }

                        capture quietly xtreg `yvar' c.z_ln_fund_est_scale_cum##c.`dvar' `mvar' c.z_ln_fund_est_scale_cum#c.`mvar' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local direct_b = _b[c.z_ln_fund_est_scale_cum#c.`dvar']
                            local direct_se = _se[c.z_ln_fund_est_scale_cum#c.`dvar']
                            local direct_p = 2 * ttail(e(df_r), abs(`direct_b' / `direct_se'))
                            local path2_b = _b[c.z_ln_fund_est_scale_cum#c.`mvar']
                            local path2_se = _se[c.z_ln_fund_est_scale_cum#c.`mvar']
                            local path2_p = 2 * ttail(e(df_r), abs(`path2_b' / `path2_se'))
                            local attenuation = abs(`beta_b') - abs(`direct_b')
                            local pass10 = (`beta_b' < 0 & `beta_p' <= 0.10 & `path1_b' < 0 & `path1_p' <= 0.10 & `path2_b' > 0 & `path2_p' <= 0.10)
                            local pass05 = (`beta_b' < 0 & `beta_p' <= 0.05 & `path1_b' < 0 & `path1_p' <= 0.05 & `path2_b' > 0 & `path2_p' <= 0.10)
                            post `posth' ("moderator") ("`ybase'") ("`lag'") ("`ytransform'") ("`dtransform'") ("`mtransform'") ("`sample_rule'") ///
                                ("`yvar'") ("`dvar'") ("`mvar'") (e(N)) ///
                                (`beta_b') (`beta_se') (`beta_p') ///
                                (`path1_b') (`path1_se') (`path1_p') ///
                                (`path2_b') (`path2_se') (`path2_p') ///
                                (`direct_b') (`direct_se') (`direct_p') ///
                                (`attenuation') (e(r2_w)) (`pass10') (`pass05')
                        }
                    }
                }
            }
        }
    }
}

postclose `posth'
use `results', clear
gen byte path1_theory = path1_b < 0 & path1_p <= 0.10
gen byte path2_theory = path2_b > 0 & path2_p <= 0.10
gen byte beta_theory = beta_b < 0 & beta_p <= 0.10
gen str3 beta_sig = ""
replace beta_sig = "*" if beta_p <= 0.10
replace beta_sig = "**" if beta_p <= 0.05
replace beta_sig = "***" if beta_p <= 0.01
gen str3 path1_sig = ""
replace path1_sig = "*" if path1_p <= 0.10
replace path1_sig = "**" if path1_p <= 0.05
replace path1_sig = "***" if path1_p <= 0.01
gen str3 path2_sig = ""
replace path2_sig = "*" if path2_p <= 0.10
replace path2_sig = "**" if path2_p <= 0.05
replace path2_sig = "***" if path2_p <= 0.01

export delimited using "`resultcsv'", replace
preserve
    keep if theory10 == 1
    gsort -theory05 model ybase lag ytransform path2_p path1_p
    export delimited using "`selectedcsv'", replace
restore

display "resultcsv=`resultcsv'"
display "selectedcsv=`selectedcsv'"
log close
