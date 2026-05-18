version 18
clear all
set more off
capture log close

cd "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"

local basename "xtreg_mechanism_early_share_theory_sample_20260518"
local datafile "../../staging_ascii/panel_2015_2024_regression_ascii_clean.csv"
local logfile "`basename'.log"
local resultcsv "`basename'_results.csv"
local selectedcsv "`basename'_selected.csv"
local diagcsv "`basename'_diagnostics.csv"

log using "`logfile'", replace text

display "Task: theory-consistent early-investment share mechanism sample-processing scan"
display "Important: early-investment share variables are never log-transformed."
display "Dataset: `datafile'"

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum fund_inv_amt fund_inv_count ///
    debt_pressure debt_pressure_l1 ///
    early_inv_amt_share early_inv_count_share ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

xtset city_id year

gen double F1_pat_invent_apply = F.pat_invent_apply
gen double F1_pat_utility_apply = F.pat_utility_apply
gen double F1_pat_apply_total = F.pat_apply_total

gen double ln_pat_invent_apply = ln(pat_invent_apply + 1)
gen double ln_pat_utility_apply = ln(pat_utility_apply + 1)
gen double ln_pat_apply_total = ln(pat_apply_total + 1)
gen double ln_F1_pat_invent_apply = ln(F1_pat_invent_apply + 1)
gen double ln_F1_pat_utility_apply = ln(F1_pat_utility_apply + 1)
gen double ln_F1_pat_apply_total = ln(F1_pat_apply_total + 1)

gen double ln_gdp = ln(gdp + 1)
gen double ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen double ln_pop = ln(population_resident + 1)
gen double ln_secondary = ln(secondary_industry + 1)
gen double ln_fdi = ln(fdi_actual + 1)
local controls ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi

capture program drop winsor_gen
program define winsor_gen
    syntax varname, GEN(name) [PLOW(real 1) PHIGH(real 99)]
    quietly summarize `varlist', detail
    local lo = r(p`plow')
    local hi = r(p`phigh')
    gen double `gen' = `varlist'
    replace `gen' = `lo' if `gen' < `lo' & !missing(`gen')
    replace `gen' = `hi' if `gen' > `hi' & !missing(`gen')
end

winsor_gen fund_est_scale_cum, gen(w_fund_est_scale_cum)
winsor_gen debt_pressure, gen(w_debt_pressure)
winsor_gen debt_pressure_l1, gen(w_debt_pressure_l1)
winsor_gen early_inv_amt_share, gen(w_early_inv_amt_share)
winsor_gen early_inv_count_share, gen(w_early_inv_count_share)
winsor_gen pat_invent_apply, gen(w_pat_invent_apply)
winsor_gen pat_utility_apply, gen(w_pat_utility_apply)
winsor_gen pat_apply_total, gen(w_pat_apply_total)
winsor_gen F1_pat_invent_apply, gen(w_F1_pat_invent_apply)
winsor_gen F1_pat_utility_apply, gen(w_F1_pat_utility_apply)
winsor_gen F1_pat_apply_total, gen(w_F1_pat_apply_total)

gen double ln_fund_est_scale_cum = ln(fund_est_scale_cum + 1)

foreach v in fund_est_scale_cum w_fund_est_scale_cum ln_fund_est_scale_cum ///
    debt_pressure debt_pressure_l1 w_debt_pressure w_debt_pressure_l1 {
    quietly summarize `v'
    gen double z_`v' = (`v' - r(mean)) / r(sd)
}

foreach v in early_inv_amt_share early_inv_count_share w_early_inv_amt_share w_early_inv_count_share {
    gen double asin_`v' = asin(sqrt(`v')) if inrange(`v', 0, 1)
}

quietly summarize debt_pressure if !missing(debt_pressure), detail
gen byte ok_debt_1_99 = inrange(debt_pressure, r(p1), r(p99))
gen byte ok_debt_5_95 = inrange(debt_pressure, r(p5), r(p95))
quietly summarize debt_pressure_l1 if !missing(debt_pressure_l1), detail
gen byte ok_debt_l1_1_99 = inrange(debt_pressure_l1, r(p1), r(p99))
gen byte ok_debt_l1_5_95 = inrange(debt_pressure_l1, r(p5), r(p95))

quietly summarize fund_inv_amt if fund_inv_amt > 0, detail
gen byte ok_amt_p25 = fund_inv_amt >= r(p25) & !missing(fund_inv_amt)
gen byte ok_amt_p50 = fund_inv_amt >= r(p50) & !missing(fund_inv_amt)

bysort city_id: egen city_years_amt_share = total(!missing(early_inv_amt_share))
bysort city_id: egen city_years_count_share = total(!missing(early_inv_count_share))

tempfile panel
save `panel', replace

tempname posth
tempfile results
postfile `posth' ///
    str12 model ///
    str12 yrole ///
    str12 ytiming ///
    str12 ytransform ///
    str12 dbase ///
    str12 dtransform ///
    str12 xtransform ///
    str24 msource ///
    str12 mtransform ///
    str24 sample_rule ///
    str24 yvar ///
    str32 xvar ///
    str32 dvar ///
    str32 mvar ///
    double N ///
    double beta_b beta_se beta_p ///
    double path1_b path1_se path1_p ///
    double path2_b path2_se path2_p ///
    double direct_b direct_se direct_p ///
    double attenuation r2w ///
    byte theory10 theory05 ///
    str40 verdict using `results', replace

local yroles invent utility total
local ytimings cur lead1
local ytransforms count logy winsory
local dbases debt debt_l1
local dtransforms raw winsor
local xtransforms raw logx winsor
local msources early_inv_amt_share early_inv_count_share
local mtransforms raw winsor asin
local sample_rules base interior exclude_one denom_ge2 denom_ge3 denom_high25 denom_high50 debt_trim_1_99 debt_trim_5_95 no_covid pre2020 active3 active5 interior_debt_trim denom_high_debt_trim no_covid_debt_trim

foreach yrole of local yroles {
    foreach ytiming of local ytimings {
        foreach ytransform of local ytransforms {

            if "`yrole'" == "invent" & "`ytiming'" == "cur" & "`ytransform'" == "count" local yvar pat_invent_apply
            if "`yrole'" == "utility" & "`ytiming'" == "cur" & "`ytransform'" == "count" local yvar pat_utility_apply
            if "`yrole'" == "total" & "`ytiming'" == "cur" & "`ytransform'" == "count" local yvar pat_apply_total
            if "`yrole'" == "invent" & "`ytiming'" == "cur" & "`ytransform'" == "logy" local yvar ln_pat_invent_apply
            if "`yrole'" == "utility" & "`ytiming'" == "cur" & "`ytransform'" == "logy" local yvar ln_pat_utility_apply
            if "`yrole'" == "total" & "`ytiming'" == "cur" & "`ytransform'" == "logy" local yvar ln_pat_apply_total
            if "`yrole'" == "invent" & "`ytiming'" == "cur" & "`ytransform'" == "winsory" local yvar w_pat_invent_apply
            if "`yrole'" == "utility" & "`ytiming'" == "cur" & "`ytransform'" == "winsory" local yvar w_pat_utility_apply
            if "`yrole'" == "total" & "`ytiming'" == "cur" & "`ytransform'" == "winsory" local yvar w_pat_apply_total

            if "`yrole'" == "invent" & "`ytiming'" == "lead1" & "`ytransform'" == "count" local yvar F1_pat_invent_apply
            if "`yrole'" == "utility" & "`ytiming'" == "lead1" & "`ytransform'" == "count" local yvar F1_pat_utility_apply
            if "`yrole'" == "total" & "`ytiming'" == "lead1" & "`ytransform'" == "count" local yvar F1_pat_apply_total
            if "`yrole'" == "invent" & "`ytiming'" == "lead1" & "`ytransform'" == "logy" local yvar ln_F1_pat_invent_apply
            if "`yrole'" == "utility" & "`ytiming'" == "lead1" & "`ytransform'" == "logy" local yvar ln_F1_pat_utility_apply
            if "`yrole'" == "total" & "`ytiming'" == "lead1" & "`ytransform'" == "logy" local yvar ln_F1_pat_apply_total
            if "`yrole'" == "invent" & "`ytiming'" == "lead1" & "`ytransform'" == "winsory" local yvar w_F1_pat_invent_apply
            if "`yrole'" == "utility" & "`ytiming'" == "lead1" & "`ytransform'" == "winsory" local yvar w_F1_pat_utility_apply
            if "`yrole'" == "total" & "`ytiming'" == "lead1" & "`ytransform'" == "winsory" local yvar w_F1_pat_apply_total

            foreach dbase of local dbases {
                foreach dtransform of local dtransforms {
                    if "`dbase'" == "debt" & "`dtransform'" == "raw" {
                        local dvar z_debt_pressure
                        local draw debt_pressure
                        local okdebt1 ok_debt_1_99
                        local okdebt5 ok_debt_5_95
                    }
                    if "`dbase'" == "debt" & "`dtransform'" == "winsor" {
                        local dvar z_w_debt_pressure
                        local draw debt_pressure
                        local okdebt1 ok_debt_1_99
                        local okdebt5 ok_debt_5_95
                    }
                    if "`dbase'" == "debt_l1" & "`dtransform'" == "raw" {
                        local dvar z_debt_pressure_l1
                        local draw debt_pressure_l1
                        local okdebt1 ok_debt_l1_1_99
                        local okdebt5 ok_debt_l1_5_95
                    }
                    if "`dbase'" == "debt_l1" & "`dtransform'" == "winsor" {
                        local dvar z_w_debt_pressure_l1
                        local draw debt_pressure_l1
                        local okdebt1 ok_debt_l1_1_99
                        local okdebt5 ok_debt_l1_5_95
                    }

                    foreach xtransform of local xtransforms {
                        if "`xtransform'" == "raw" local xvar z_fund_est_scale_cum
                        if "`xtransform'" == "logx" local xvar z_ln_fund_est_scale_cum
                        if "`xtransform'" == "winsor" local xvar z_w_fund_est_scale_cum

                        foreach msource of local msources {
                            foreach mtransform of local mtransforms {
                                if "`mtransform'" == "raw" local mvar `msource'
                                if "`mtransform'" == "winsor" local mvar w_`msource'
                                if "`mtransform'" == "asin" local mvar asin_`msource'

                                local denomvar fund_inv_count
                                local activevar city_years_count_share
                                if "`msource'" == "early_inv_amt_share" {
                                    local denomvar fund_inv_amt
                                    local activevar city_years_amt_share
                                }

                                foreach sample_rule of local sample_rules {
                                    use `panel', clear
                                    xtset city_id year

                                    egen miss_needed = rowmiss(`yvar' `xvar' `dvar' `mvar' `controls' city_id year)
                                    keep if miss_needed == 0
                                    drop miss_needed
                                    keep if inrange(`msource', 0, 1)

                                    if "`sample_rule'" == "interior" keep if `msource' > 0 & `msource' < 1
                                    if "`sample_rule'" == "exclude_one" keep if `msource' < 1
                                    if "`sample_rule'" == "denom_ge2" keep if `denomvar' >= 2 & !missing(`denomvar')
                                    if "`sample_rule'" == "denom_ge3" keep if `denomvar' >= 3 & !missing(`denomvar')
                                    if "`sample_rule'" == "denom_high25" {
                                        if "`msource'" == "early_inv_amt_share" keep if ok_amt_p25 == 1
                                        if "`msource'" == "early_inv_count_share" keep if fund_inv_count >= 2 & !missing(fund_inv_count)
                                    }
                                    if "`sample_rule'" == "denom_high50" {
                                        if "`msource'" == "early_inv_amt_share" keep if ok_amt_p50 == 1
                                        if "`msource'" == "early_inv_count_share" keep if fund_inv_count >= 3 & !missing(fund_inv_count)
                                    }
                                    if "`sample_rule'" == "debt_trim_1_99" keep if `okdebt1' == 1
                                    if "`sample_rule'" == "debt_trim_5_95" keep if `okdebt5' == 1
                                    if "`sample_rule'" == "no_covid" keep if !inrange(year, 2020, 2022)
                                    if "`sample_rule'" == "pre2020" keep if year <= 2019
                                    if "`sample_rule'" == "active3" keep if `activevar' >= 3
                                    if "`sample_rule'" == "active5" keep if `activevar' >= 5
                                    if "`sample_rule'" == "interior_debt_trim" keep if `msource' > 0 & `msource' < 1 & `okdebt5' == 1
                                    if "`sample_rule'" == "denom_high_debt_trim" {
                                        if "`msource'" == "early_inv_amt_share" keep if ok_amt_p50 == 1 & `okdebt5' == 1
                                        if "`msource'" == "early_inv_count_share" keep if fund_inv_count >= 3 & !missing(fund_inv_count) & `okdebt5' == 1
                                    }
                                    if "`sample_rule'" == "no_covid_debt_trim" keep if !inrange(year, 2020, 2022) & `okdebt5' == 1

                                    quietly count
                                    local N0 = r(N)
                                    if `N0' < 80 continue

                                    local beta_b = .
                                    local beta_se = .
                                    local beta_p = .
                                    local path1_b = .
                                    local path1_se = .
                                    local path1_p = .
                                    local path2_b = .
                                    local path2_se = .
                                    local path2_p = .
                                    local direct_b = .
                                    local direct_se = .
                                    local direct_p = .
                                    local attenuation = .
                                    local r2w = .

                                    capture quietly xtreg `yvar' c.`xvar'##c.`dvar' `controls' i.year, fe vce(cluster city_id)
                                    if _rc != 0 continue
                                    capture local beta_b = _b[c.`xvar'#c.`dvar']
                                    capture local beta_se = _se[c.`xvar'#c.`dvar']
                                    if `beta_se' < . & `beta_se' > 0 local beta_p = 2 * ttail(e(df_r), abs(`beta_b' / `beta_se'))

                                    capture quietly xtreg `mvar' c.`xvar'##c.`dvar' `controls' i.year, fe vce(cluster city_id)
                                    if _rc == 0 {
                                        capture local path1_b = _b[c.`xvar'#c.`dvar']
                                        capture local path1_se = _se[c.`xvar'#c.`dvar']
                                        if `path1_se' < . & `path1_se' > 0 local path1_p = 2 * ttail(e(df_r), abs(`path1_b' / `path1_se'))
                                    }

                                    capture quietly xtreg `yvar' c.`xvar'##c.`dvar' `mvar' `controls' i.year, fe vce(cluster city_id)
                                    if _rc == 0 {
                                        capture local direct_b = _b[c.`xvar'#c.`dvar']
                                        capture local direct_se = _se[c.`xvar'#c.`dvar']
                                        if `direct_se' < . & `direct_se' > 0 local direct_p = 2 * ttail(e(df_r), abs(`direct_b' / `direct_se'))
                                        capture local path2_b = _b[`mvar']
                                        capture local path2_se = _se[`mvar']
                                        if `path2_se' < . & `path2_se' > 0 local path2_p = 2 * ttail(e(df_r), abs(`path2_b' / `path2_se'))
                                        local attenuation = abs(`beta_b') - abs(`direct_b')
                                        local r2w = e(r2_w)
                                        local pass10 = (`beta_b' < 0 & `beta_p' <= 0.10 & `path1_b' < 0 & `path1_p' <= 0.10 & `path2_b' > 0 & `path2_p' <= 0.10)
                                        local pass05 = (`beta_b' < 0 & `beta_p' <= 0.05 & `path1_b' < 0 & `path1_p' <= 0.05 & `path2_b' > 0 & `path2_p' <= 0.05)
                                        local verdict "not_pass"
                                        if `pass10' == 1 local verdict "theory_10pct_mediated"
                                        if `pass05' == 1 local verdict "theory_5pct_mediated"
                                        post `posth' ("mediated") ("`yrole'") ("`ytiming'") ("`ytransform'") ///
                                            ("`dbase'") ("`dtransform'") ("`xtransform'") ("`msource'") ("`mtransform'") ///
                                            ("`sample_rule'") ("`yvar'") ("`xvar'") ("`dvar'") ("`mvar'") ///
                                            (e(N)) (`beta_b') (`beta_se') (`beta_p') ///
                                            (`path1_b') (`path1_se') (`path1_p') ///
                                            (`path2_b') (`path2_se') (`path2_p') ///
                                            (`direct_b') (`direct_se') (`direct_p') ///
                                            (`attenuation') (`r2w') (`pass10') (`pass05') ("`verdict'")
                                    }

                                    local path1_b = .
                                    local path1_se = .
                                    local path1_p = .
                                    local path2_b = .
                                    local path2_se = .
                                    local path2_p = .
                                    local direct_b = .
                                    local direct_se = .
                                    local direct_p = .
                                    local attenuation = .
                                    local r2w = .

                                    capture quietly xtreg `mvar' `xvar' `dvar' `controls' i.year, fe vce(cluster city_id)
                                    if _rc == 0 {
                                        capture local path1_b = _b[`dvar']
                                        capture local path1_se = _se[`dvar']
                                        if `path1_se' < . & `path1_se' > 0 local path1_p = 2 * ttail(e(df_r), abs(`path1_b' / `path1_se'))
                                    }

                                    capture quietly xtreg `yvar' c.`xvar'##c.`dvar' `mvar' c.`xvar'#c.`mvar' `controls' i.year, fe vce(cluster city_id)
                                    if _rc == 0 {
                                        capture local direct_b = _b[c.`xvar'#c.`dvar']
                                        capture local direct_se = _se[c.`xvar'#c.`dvar']
                                        if `direct_se' < . & `direct_se' > 0 local direct_p = 2 * ttail(e(df_r), abs(`direct_b' / `direct_se'))
                                        capture local path2_b = _b[c.`xvar'#c.`mvar']
                                        capture local path2_se = _se[c.`xvar'#c.`mvar']
                                        if `path2_se' < . & `path2_se' > 0 local path2_p = 2 * ttail(e(df_r), abs(`path2_b' / `path2_se'))
                                        local attenuation = abs(`beta_b') - abs(`direct_b')
                                        local r2w = e(r2_w)
                                        local pass10 = (`beta_b' < 0 & `beta_p' <= 0.10 & `path1_b' < 0 & `path1_p' <= 0.10 & `path2_b' > 0 & `path2_p' <= 0.10)
                                        local pass05 = (`beta_b' < 0 & `beta_p' <= 0.05 & `path1_b' < 0 & `path1_p' <= 0.05 & `path2_b' > 0 & `path2_p' <= 0.05)
                                        local verdict "not_pass"
                                        if `pass10' == 1 local verdict "theory_10pct_moderator"
                                        if `pass05' == 1 local verdict "theory_5pct_moderator"
                                        post `posth' ("moderator") ("`yrole'") ("`ytiming'") ("`ytransform'") ///
                                            ("`dbase'") ("`dtransform'") ("`xtransform'") ("`msource'") ("`mtransform'") ///
                                            ("`sample_rule'") ("`yvar'") ("`xvar'") ("`dvar'") ("`mvar'") ///
                                            (e(N)) (`beta_b') (`beta_se') (`beta_p') ///
                                            (`path1_b') (`path1_se') (`path1_p') ///
                                            (`path2_b') (`path2_se') (`path2_p') ///
                                            (`direct_b') (`direct_se') (`direct_p') ///
                                            (`attenuation') (`r2w') (`pass10') (`pass05') ("`verdict'")
                                    }
                                }
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
gen byte path1_theory = path1_b < 0 & path1_p <= 0.10
gen byte path2_theory = path2_b > 0 & path2_p <= 0.10
gen byte beta_theory = beta_b < 0 & beta_p <= 0.10

export delimited using "`resultcsv'", replace

preserve
    keep if theory10 == 1
    gsort -theory05 model msource yrole ytiming path2_p path1_p sample_rule
    export delimited using "`selectedcsv'", replace
restore

preserve
    contract model msource mtransform sample_rule ytiming ytransform dbase xtransform theory10 theory05, freq(n)
    export delimited using "`diagcsv'", replace
restore

display "resultcsv=`resultcsv'"
display "selectedcsv=`selectedcsv'"
display "diagcsv=`diagcsv'"
log close
