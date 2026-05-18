version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local basename "xtreg_bootstrap_mediation_eics"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum ///
    debt_pressure debt_pressure_l1 ///
    early_inv_count_share ///
    pat_invent_apply pat_apply_total ///
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

capture program drop med_manual_boot
program define med_manual_boot, rclass
    preserve
        keep if !missing($BOOT_YVAR, $BOOT_DVAR, fund_est_scale_cum, early_inv_count_share, ///
            ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi, city_id, year)

        tempfile sample_ids current_sample
        save `current_sample', replace
        keep city_id
        duplicates drop
        bsample
        gen boot_city_id = _n
        save `sample_ids', replace
        use `current_sample', clear

        joinby city_id using `sample_ids'
        keep boot_city_id year fund_est_scale_cum $BOOT_DVAR early_inv_count_share ///
            $BOOT_YVAR ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi
        rename boot_city_id city_boot
        xtset city_boot year

        quietly xtreg early_inv_count_share ///
            c.fund_est_scale_cum##c.$BOOT_DVAR ///
            ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, fe
        scalar a2 = _b[$BOOT_DVAR]
        scalar a3 = _b[c.fund_est_scale_cum#c.$BOOT_DVAR]

        quietly xtreg $BOOT_YVAR ///
            c.fund_est_scale_cum##c.$BOOT_DVAR ///
            early_inv_count_share ///
            ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, fe
        scalar b4 = _b[early_inv_count_share]

        return scalar a2 = a2
        return scalar a3 = a3
        return scalar b4 = b4
        return scalar indirect_a2b4 = a2 * b4
        return scalar indirect_a3b4 = a3 * b4
    restore
end

tempname posth
tempfile results
postfile `posth' ///
    str20 yvar ///
    str18 dvar ///
    double N ///
    double beta3_base beta3_base_se beta3_base_p ///
    double a2 a2_se a2_p ///
    double a3 a3_se a3_p ///
    double c3 c3_se c3_p ///
    double b4 b4_se b4_p ///
    double ind_a2b4 ind_a2b4_se ind_a2b4_p ind_a2b4_ll ind_a2b4_ul ///
    double ind_a3b4 ind_a3b4_se ind_a3b4_p ind_a3b4_ll ind_a3b4_ul ///
    using `results', replace

local yvars ///
    pat_invent_apply ///
    pat_apply_total

local dvars ///
    debt_pressure ///
    debt_pressure_l1

foreach y of local yvars {
    foreach d of local dvars {
        use `panel', clear
        xtset city_id year
        keep if !missing(`y', `d', fund_est_scale_cum, early_inv_count_share, ///
            ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi, city_id, year)
        count
        local N = r(N)

        quietly xtreg `y' c.fund_est_scale_cum##c.`d' ///
            ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, ///
            fe vce(cluster city_id)
        local beta3_base = _b[c.fund_est_scale_cum#c.`d']
        local beta3_base_se = _se[c.fund_est_scale_cum#c.`d']
        local beta3_base_p = 2 * ttail(e(df_r), abs(`beta3_base' / `beta3_base_se'))

        quietly xtreg early_inv_count_share ///
            c.fund_est_scale_cum##c.`d' ///
            ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, ///
            fe vce(cluster city_id)
        local a2 = _b[`d']
        local a2_se = _se[`d']
        local a2_p = 2 * ttail(e(df_r), abs(`a2' / `a2_se'))
        local a3 = _b[c.fund_est_scale_cum#c.`d']
        local a3_se = _se[c.fund_est_scale_cum#c.`d']
        local a3_p = 2 * ttail(e(df_r), abs(`a3' / `a3_se'))

        quietly xtreg `y' ///
            c.fund_est_scale_cum##c.`d' ///
            early_inv_count_share ///
            ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, ///
            fe vce(cluster city_id)
        local c3 = _b[c.fund_est_scale_cum#c.`d']
        local c3_se = _se[c.fund_est_scale_cum#c.`d']
        local c3_p = 2 * ttail(e(df_r), abs(`c3' / `c3_se'))
        local b4 = _b[early_inv_count_share]
        local b4_se = _se[early_inv_count_share]
        local b4_p = 2 * ttail(e(df_r), abs(`b4' / `b4_se'))

        global BOOT_YVAR "`y'"
        global BOOT_DVAR "`d'"

        simulate ///
            a2 = r(a2) ///
            a3 = r(a3) ///
            b4 = r(b4) ///
            indirect_a2b4 = r(indirect_a2b4) ///
            indirect_a3b4 = r(indirect_a3b4), ///
            reps(2000) seed(20260515) nodots: med_manual_boot

        tempname simres
        tempfile simfile
        save `simfile', replace

        quietly summarize indirect_a2b4
        local ind_a2b4 = r(mean)
        local ind_a2b4_se = r(sd)
        local ind_a2b4_p = 2 * normal(-abs(`ind_a2b4' / `ind_a2b4_se'))
        centile indirect_a2b4, centile(2.5 97.5)
        local ind_a2b4_ll = r(c_1)
        local ind_a2b4_ul = r(c_2)

        quietly summarize indirect_a3b4
        local ind_a3b4 = r(mean)
        local ind_a3b4_se = r(sd)
        local ind_a3b4_p = 2 * normal(-abs(`ind_a3b4' / `ind_a3b4_se'))
        centile indirect_a3b4, centile(2.5 97.5)
        local ind_a3b4_ll = r(c_1)
        local ind_a3b4_ul = r(c_2)

        post `posth' ///
            ("`y'") ///
            ("`d'") ///
            (`N') ///
            (`beta3_base') (`beta3_base_se') (`beta3_base_p') ///
            (`a2') (`a2_se') (`a2_p') ///
            (`a3') (`a3_se') (`a3_p') ///
            (`c3') (`c3_se') (`c3_p') ///
            (`b4') (`b4_se') (`b4_p') ///
            (`ind_a2b4') (`ind_a2b4_se') (`ind_a2b4_p') (`ind_a2b4_ll') (`ind_a2b4_ul') ///
            (`ind_a3b4') (`ind_a3b4_se') (`ind_a3b4_p') (`ind_a3b4_ll') (`ind_a3b4_ul')
    }
}

postclose `posth'
use `results', clear
export delimited using "`resultcsv'", replace

display "resultcsv=`resultcsv'"
log close
