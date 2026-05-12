version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "C:/Users/Joe，/OneDrive/Desktop/dachuang/staging_ascii/panel_2015_2024_regression_ascii_clean.csv"
local outdir "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang/运行日志与do代码"
local basename "xtreg_fe_moderation_earlyinv_ascii"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"

log using "`logfile'", replace text

tempname posth
tempfile results
postfile `posth' str20 yvar str20 mvar str16 dvar str12 spec ///
    double b3 se3 p3 N r2w using `results', replace

local yvars pat_invent_apply pat_utility_apply pat_apply_total
local mvars early_inv_count early_inv_amt
local dvars debt_pressure debt_pressure_l1

foreach y of local yvars {
    foreach m of local mvars {
        foreach d of local dvars {

            * no controls
            import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
            encode city, gen(city_id)
            destring year, replace force
            collapse (firstnm) ///
                fund_est_scale_cum `y' `d' `m', ///
                by(city year city_id)
            quietly xtset city_id year
            keep if !missing(`y', fund_est_scale_cum, `d', `m', city_id, year)
            quietly xtreg `y' c.fund_est_scale_cum##c.`d'##c.`m' i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local b3 = _b[c.fund_est_scale_cum#c.`d'#c.`m']
                local se3 = _se[c.fund_est_scale_cum#c.`d'#c.`m']
                local p3 = 2 * ttail(e(df_r), abs(`b3'/`se3'))
                post `posth' ("`y'") ("`m'") ("`d'") ("noctrl") (`b3') (`se3') (`p3') (e(N)) (e(r2_w))
            }

            * with controls
            import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
            encode city, gen(city_id)
            destring year, replace force
            collapse (firstnm) ///
                fund_est_scale_cum `y' `d' `m' ///
                gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
                by(city year city_id)
            gen ln_gdp = ln(gdp + 1)
            gen ln_fiscal_scitech = ln(fiscal_scitech + 1)
            gen ln_pop = ln(population_resident + 1)
            gen ln_secondary = ln(secondary_industry + 1)
            gen ln_fdi = ln(fdi_actual + 1)
            quietly xtset city_id year
            keep if !missing(`y', fund_est_scale_cum, `d', `m', ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi, city_id, year)
            quietly xtreg `y' c.fund_est_scale_cum##c.`d'##c.`m' ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi i.year, fe vce(cluster city_id)
            if _rc == 0 {
                local b3 = _b[c.fund_est_scale_cum#c.`d'#c.`m']
                local se3 = _se[c.fund_est_scale_cum#c.`d'#c.`m']
                local p3 = 2 * ttail(e(df_r), abs(`b3'/`se3'))
                post `posth' ("`y'") ("`m'") ("`d'") ("ctrl") (`b3') (`se3') (`p3') (e(N)) (e(r2_w))
            }
        }
    }
}

postclose `posth'
use `results', clear
sort yvar mvar dvar spec
export delimited using "`resultcsv'", replace
list, sepby(yvar)

log close
