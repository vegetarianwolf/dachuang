version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang/dachuang"
local datafile "`root'/面板数据/地级市总面板_2015_2024_英文版.csv"
local outdir "`root'/运行日志与do代码"
local logfile "`outdir'/probe_soccap_ratio_vars.log"

log using "`logfile'", replace text

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum ///
    pat_invent_apply pat_utility_apply pat_apply_total ///
    ln_pat_invent_apply ln_pat_utility_apply ln_pat_apply_total ///
    debt_pressure debt_pressure_l1 ///
    soccap_share_total gov_share_total soccap_leverage matched_share_total ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

xtset city_id year

di "==== panel dimensions ===="
xtdescribe

di "==== ratio variable distributions ===="
foreach v in soccap_share_total gov_share_total soccap_leverage matched_share_total {
    di "---- `v' ----"
    summarize `v', detail
    count if !missing(`v')
    count if `v' == 0
    count if `v' < 0
    count if `v' > 1 & inlist("`v'", "soccap_share_total", "gov_share_total", "matched_share_total")
}

di "==== correlations ===="
pwcorr soccap_share_total gov_share_total soccap_leverage matched_share_total fund_est_scale_cum debt_pressure debt_pressure_l1 pat_invent_apply pat_apply_total ln_pat_invent_apply ln_pat_apply_total, sig obs

log close
