version 18
clear all
set more off
capture log close

cd "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"

local basename "xtreg_early_share_path1_screen_20260518"
local datafile "../../staging_ascii/panel_2015_2024_regression_ascii_clean.csv"
local logfile "`basename'.log"
local resultcsv "`basename'_results.csv"
local selectedcsv "`basename'_negative_selected.csv"

log using "`logfile'", replace text

display "Task: fast path-1 screen for theory-consistent early-investment share mechanism."
display "Theory expected path 1: debt pressure lowers early investment share. No log transform on share variables."

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum fund_inv_amt fund_inv_count ///
    debt_pressure debt_pressure_l1 ///
    early_inv_amt_share early_inv_count_share ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen double ln_gdp = ln(gdp + 1)
gen double ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen double ln_pop = ln(population_resident + 1)
gen double ln_secondary = ln(secondary_industry + 1)
gen double ln_fdi = ln(fdi_actual + 1)
local controls ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi

xtset city_id year

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

winsor_gen fund_est_scale_cum, gen(w_fund_est_scale_cum)
winsor_gen debt_pressure, gen(w_debt_pressure)
winsor_gen debt_pressure_l1, gen(w_debt_pressure_l1)
winsor_gen early_inv_amt_share, gen(w_early_inv_amt_share)
winsor_gen early_inv_count_share, gen(w_early_inv_count_share)
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
gen byte ok_debt_5_95 = inrange(debt_pressure, r(p5), r(p95))
quietly summarize debt_pressure_l1 if !missing(debt_pressure_l1), detail
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
    str12 model str12 dbase str12 dtransform str12 xtransform ///
    str24 msource str12 mtransform str24 sample_rule ///
    str32 xvar str32 dvar str32 mvar ///
    double N b se p r2w using `results', replace

local dbases debt debt_l1
local dtransforms raw winsor
local xtransforms raw logx winsor
local msources early_inv_amt_share early_inv_count_share
local mtransforms raw winsor asin
local sample_rules base interior exclude_one denom_ge2 denom_ge3 denom_high25 denom_high50 debt_trim_5_95 no_covid pre2020 active3 active5 interior_debt_trim denom_high_debt_trim no_covid_debt_trim

foreach dbase of local dbases {
    foreach dtransform of local dtransforms {
        if "`dbase'" == "debt" & "`dtransform'" == "raw" {
            local dvar z_debt_pressure
            local okdebt ok_debt_5_95
        }
        if "`dbase'" == "debt" & "`dtransform'" == "winsor" {
            local dvar z_w_debt_pressure
            local okdebt ok_debt_5_95
        }
        if "`dbase'" == "debt_l1" & "`dtransform'" == "raw" {
            local dvar z_debt_pressure_l1
            local okdebt ok_debt_l1_5_95
        }
        if "`dbase'" == "debt_l1" & "`dtransform'" == "winsor" {
            local dvar z_w_debt_pressure_l1
            local okdebt ok_debt_l1_5_95
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
                        egen miss_needed = rowmiss(`xvar' `dvar' `mvar' `controls' city_id year)
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
                        if "`sample_rule'" == "debt_trim_5_95" keep if `okdebt' == 1
                        if "`sample_rule'" == "no_covid" keep if !inrange(year, 2020, 2022)
                        if "`sample_rule'" == "pre2020" keep if year <= 2019
                        if "`sample_rule'" == "active3" keep if `activevar' >= 3
                        if "`sample_rule'" == "active5" keep if `activevar' >= 5
                        if "`sample_rule'" == "interior_debt_trim" keep if `msource' > 0 & `msource' < 1 & `okdebt' == 1
                        if "`sample_rule'" == "denom_high_debt_trim" {
                            if "`msource'" == "early_inv_amt_share" keep if ok_amt_p50 == 1 & `okdebt' == 1
                            if "`msource'" == "early_inv_count_share" keep if fund_inv_count >= 3 & !missing(fund_inv_count) & `okdebt' == 1
                        }
                        if "`sample_rule'" == "no_covid_debt_trim" keep if !inrange(year, 2020, 2022) & `okdebt' == 1

                        quietly count
                        if r(N) < 80 continue

                        capture quietly xtreg `mvar' c.`xvar'##c.`dvar' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local b = _b[c.`xvar'#c.`dvar']
                            local se = _se[c.`xvar'#c.`dvar']
                            local p = 2 * ttail(e(df_r), abs(`b' / `se'))
                            post `posth' ("mediated") ("`dbase'") ("`dtransform'") ("`xtransform'") ///
                                ("`msource'") ("`mtransform'") ("`sample_rule'") ///
                                ("`xvar'") ("`dvar'") ("`mvar'") (e(N)) (`b') (`se') (`p') (e(r2_w))
                        }

                        capture quietly xtreg `mvar' `xvar' `dvar' `controls' i.year, fe vce(cluster city_id)
                        if _rc == 0 {
                            local b = _b[`dvar']
                            local se = _se[`dvar']
                            local p = 2 * ttail(e(df_r), abs(`b' / `se'))
                            post `posth' ("moderator") ("`dbase'") ("`dtransform'") ("`xtransform'") ///
                                ("`msource'") ("`mtransform'") ("`sample_rule'") ///
                                ("`xvar'") ("`dvar'") ("`mvar'") (e(N)) (`b') (`se') (`p') (e(r2_w))
                        }
                    }
                }
            }
        }
    }
}

postclose `posth'
use `results', clear
gen byte theory_path1_10 = b < 0 & p <= 0.10
gen byte theory_path1_05 = b < 0 & p <= 0.05
export delimited using "`resultcsv'", replace
preserve
    keep if theory_path1_10 == 1
    gsort -theory_path1_05 p model msource mtransform sample_rule
    export delimited using "`selectedcsv'", replace
restore

display "resultcsv=`resultcsv'"
display "selectedcsv=`selectedcsv'"
log close
