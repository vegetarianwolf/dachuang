version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "C:/Users/Joe，/OneDrive/Desktop/dachuang/staging_ascii/panel_2015_2024_regression_ascii_clean.csv"
local outdir "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"
local basename "xtreg_mediated_moderation_mechanism_ascii"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)

encode city, gen(city_id)
destring year, replace force

duplicates tag city year, gen(dup_tag)
sort city year
collapse (firstnm) ///
    fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    early_inv_amt early_inv_count early_inv_count_share ///
    soccap_leverage soccap_amt soccap_share_total ///
    fcity_sa_mean fcity_fc_mean fcity_kz_mean fcity_ww_mean ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen ln_gdp = ln(gdp + 1)
gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
gen ln_pop = ln(population_resident + 1)
gen ln_secondary = ln(secondary_industry + 1)
gen ln_fdi = ln(fdi_actual + 1)

xtset city_id year

local yvars ///
    pat_invent_apply ///
    pat_utility_apply ///
    pat_apply_total

local mvars ///
    early_inv_amt ///
    early_inv_count ///
    early_inv_count_share ///
    soccap_leverage ///
    soccap_amt ///
    soccap_share_total ///
    fcity_sa_mean ///
    fcity_fc_mean ///
    fcity_kz_mean ///
    fcity_ww_mean

local dvars ///
    debt_pressure ///
    debt_pressure_l1

local ctrls ///
    ln_gdp ///
    ln_fiscal_scitech ///
    ln_pop ///
    ln_secondary ///
    ln_fdi

tempname posth
tempfile results
postfile `posth' str20 yvar str20 mvar str16 dvar str12 step ///
    double b_xw se_xw p_xw b_m se_m p_m N using `results', replace

foreach y of local yvars {
    foreach d of local dvars {
        foreach m of local mvars {
            * Step 1: mediator equation
            import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
            encode city, gen(city_id)
            destring year, replace force
            duplicates tag city year, gen(dup_tag)
            sort city year
            collapse (firstnm) ///
                fund_est_scale_cum ///
                pat_invent_apply pat_utility_apply pat_apply_total ///
                debt_pressure debt_pressure_l1 ///
                early_inv_amt early_inv_count early_inv_count_share ///
                soccap_leverage soccap_amt soccap_share_total ///
                fcity_sa_mean fcity_fc_mean fcity_kz_mean fcity_ww_mean ///
                gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
                by(city year city_id)
            gen ln_gdp = ln(gdp + 1)
            gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
            gen ln_pop = ln(population_resident + 1)
            gen ln_secondary = ln(secondary_industry + 1)
            gen ln_fdi = ln(fdi_actual + 1)
            xtset city_id year
            keep if !missing(`m', fund_est_scale_cum, `d', ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi, city_id, year)
            quietly xtreg `m' c.fund_est_scale_cum##c.`d' `ctrls' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local b_xw = _b[c.fund_est_scale_cum#c.`d']
                local se_xw = _se[c.fund_est_scale_cum#c.`d']
                local t_xw = `b_xw' / `se_xw'
                local p_xw = 2 * ttail(e(df_r), abs(`t_xw'))
                local N1 = e(N)
                post `posth' ("`y'") ("`m'") ("`d'") ("M_eq") (`b_xw') (`se_xw') (`p_xw') (.) (.) (.) (`N1')
            }

            * Step 2: outcome equation with mediator
            import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
            encode city, gen(city_id)
            destring year, replace force
            duplicates tag city year, gen(dup_tag)
            sort city year
            collapse (firstnm) ///
                fund_est_scale_cum ///
                pat_invent_apply pat_utility_apply pat_apply_total ///
                debt_pressure debt_pressure_l1 ///
                early_inv_amt early_inv_count early_inv_count_share ///
                soccap_leverage soccap_amt soccap_share_total ///
                fcity_sa_mean fcity_fc_mean fcity_kz_mean fcity_ww_mean ///
                gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
                by(city year city_id)
            gen ln_gdp = ln(gdp + 1)
            gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
            gen ln_pop = ln(population_resident + 1)
            gen ln_secondary = ln(secondary_industry + 1)
            gen ln_fdi = ln(fdi_actual + 1)
            xtset city_id year
            keep if !missing(`y', `m', fund_est_scale_cum, `d', ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi, city_id, year)
            quietly xtreg `y' c.fund_est_scale_cum##c.`d' `m' `ctrls' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local b_xw = _b[c.fund_est_scale_cum#c.`d']
                local se_xw = _se[c.fund_est_scale_cum#c.`d']
                local t_xw = `b_xw' / `se_xw'
                local p_xw = 2 * ttail(e(df_r), abs(`t_xw'))
                local b_m = _b[`m']
                local se_m = _se[`m']
                local t_m = `b_m' / `se_m'
                local p_m = 2 * ttail(e(df_r), abs(`t_m'))
                local N2 = e(N)
                post `posth' ("`y'") ("`m'") ("`d'") ("Y_eq") (`b_xw') (`se_xw') (`p_xw') (`b_m') (`se_m') (`p_m') (`N2')
                di as text "----------------------------------------"
                di as result "y = `y' ; m = `m' ; d = `d'"
                di as result "interaction coef = " %10.6f `b_xw' " , p = " %10.6f `p_xw' " ; mediator coef = " %10.6f `b_m' " , p = " %10.6f `p_m' " , N = " %9.0f `N2'
            }
        }
    }
}

postclose `posth'
use `results', clear
sort yvar dvar mvar step
export delimited using "`resultcsv'", replace
list, sepby(yvar)

log close
