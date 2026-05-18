version 18
clear all
set more off
capture log close

local root "C:/Users/Joe，/OneDrive/Desktop/dachuang"
local datafile "`root'/staging_ascii/formal_2015_en.csv"
local outdir "`root'/dachuang/运行日志与do代码"
local basename "xtreg_mediation_findev_transform_negative_20260516"
local logfile "`outdir'/`basename'.log"
local resultcsv "`outdir'/`basename'_results.csv"
local selectedcsv "`outdir'/`basename'_negative_selected.csv"

log using "`logfile'", replace text

di "Task: transform financial-development mechanism variables to check whether X*D -> M can become negative."
di "Focus: mediated model 4.1 from xtreg_mechanism_finance_dualmodel_ascii.md."
di "Data: `datafile'"

import delimited using "`datafile'", clear varnames(1) encoding(UTF-8)
encode city, gen(city_id)
destring year, replace force

collapse (firstnm) ///
    fund_est_scale_cum ///
    debt_pressure debt_pressure_l1 ///
    fin_dev_1 fin_dev_2 ///
    loan_balance_yearend deposit_balance_yearend gdp_finance_src ///
    gdp fiscal_scitech population_resident secondary_industry fdi_actual, ///
    by(city year city_id)

gen double ln_fund = ln(fund_est_scale_cum + 1)
gen double ln_debt_pressure = ln(debt_pressure + 1)
gen double ln_debt_pressure_l1 = ln(debt_pressure_l1 + 1)

gen double ln_fin_dev_1 = ln(fin_dev_1 + 1)
gen double asinh_fin_dev_1 = asinh(fin_dev_1)
gen double inv_fin_dev_1 = 1 / (fin_dev_1 + 1)
gen double neg_fin_dev_1 = -fin_dev_1
gen double neg_ln_fin_dev_1 = -ln(fin_dev_1 + 1)

gen double ln_fin_dev_2 = ln(fin_dev_2 + 1)
gen double asinh_fin_dev_2 = asinh(fin_dev_2)
gen double inv_fin_dev_2 = 1 / (fin_dev_2 + 1)
gen double neg_fin_dev_2 = -fin_dev_2
gen double neg_ln_fin_dev_2 = -ln(fin_dev_2 + 1)

gen double ln_loan_balance = ln(loan_balance_yearend + 1)
gen double ln_deposit_balance = ln(deposit_balance_yearend + 1)
gen double ln_gdp_finance_src = ln(gdp_finance_src + 1)

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
winsor_gen ln_debt_pressure, gen(w_ln_debt_pressure)
winsor_gen ln_debt_pressure_l1, gen(w_ln_debt_pressure_l1)
winsor_gen fin_dev_1, gen(w_fin_dev_1)
winsor_gen ln_fin_dev_1, gen(w_ln_fin_dev_1)
winsor_gen fin_dev_2, gen(w_fin_dev_2)
winsor_gen ln_fin_dev_2, gen(w_ln_fin_dev_2)

foreach v in ///
    fund_est_scale_cum ln_fund w_fund_est_scale_cum w_ln_fund ///
    debt_pressure debt_pressure_l1 ln_debt_pressure ln_debt_pressure_l1 ///
    w_debt_pressure w_debt_pressure_l1 w_ln_debt_pressure w_ln_debt_pressure_l1 ///
    fin_dev_1 ln_fin_dev_1 asinh_fin_dev_1 w_fin_dev_1 w_ln_fin_dev_1 ///
    fin_dev_2 ln_fin_dev_2 asinh_fin_dev_2 w_fin_dev_2 w_ln_fin_dev_2 ///
    inv_fin_dev_1 neg_fin_dev_1 neg_ln_fin_dev_1 inv_fin_dev_2 neg_fin_dev_2 neg_ln_fin_dev_2 ///
    ln_loan_balance ln_deposit_balance ln_gdp_finance_src {
    z_gen `v', gen(z_`v')
}

xtset city_id year

gen double d_fin_dev_1 = D.fin_dev_1
gen double d_ln_fin_dev_1 = D.ln_fin_dev_1
gen double d_fin_dev_2 = D.fin_dev_2
gen double d_ln_fin_dev_2 = D.ln_fin_dev_2

summarize fin_dev_1 fin_dev_2 ln_fin_dev_1 ln_fin_dev_2 d_fin_dev_1 d_ln_fin_dev_1 ///
    fund_est_scale_cum ln_fund debt_pressure debt_pressure_l1

tempfile panel
save `panel', replace

local ctrls ln_gdp ln_fiscal_scitech ln_pop ln_secondary ln_fdi
local ctrlmiss ln_gdp, ln_fiscal_scitech, ln_pop, ln_secondary, ln_fdi

tempname posth
tempfile results
postfile `posth' ///
    str8 spec str18 xform str24 xvar str18 dform str24 dvar ///
    str34 mtransform str16 meaning str24 mvar ///
    double b_xd se_xd p_xd N r2w ///
    using `results', replace

foreach spec in noctrl ctrl {
    local ctrl_part ""
    if "`spec'" == "ctrl" {
        local ctrl_part "`ctrls'"
    }

    foreach xform in rawfund logfund z_rawfund z_logfund wz_rawfund wz_logfund {
        if "`xform'" == "rawfund" {
            local xvar fund_est_scale_cum
        }
        if "`xform'" == "logfund" {
            local xvar ln_fund
        }
        if "`xform'" == "z_rawfund" {
            local xvar z_fund_est_scale_cum
        }
        if "`xform'" == "z_logfund" {
            local xvar z_ln_fund
        }
        if "`xform'" == "wz_rawfund" {
            local xvar z_w_fund_est_scale_cum
        }
        if "`xform'" == "wz_logfund" {
            local xvar z_w_ln_fund
        }

        foreach dform in debt debt_l1 ln_debt ln_debt_l1 wz_debt wz_debt_l1 wz_ln_debt wz_ln_debt_l1 {
            if "`dform'" == "debt" {
                local dvar debt_pressure
            }
            if "`dform'" == "debt_l1" {
                local dvar debt_pressure_l1
            }
            if "`dform'" == "ln_debt" {
                local dvar ln_debt_pressure
            }
            if "`dform'" == "ln_debt_l1" {
                local dvar ln_debt_pressure_l1
            }
            if "`dform'" == "wz_debt" {
                local dvar z_w_debt_pressure
            }
            if "`dform'" == "wz_debt_l1" {
                local dvar z_w_debt_pressure_l1
            }
            if "`dform'" == "wz_ln_debt" {
                local dvar z_w_ln_debt_pressure
            }
            if "`dform'" == "wz_ln_debt_l1" {
                local dvar z_w_ln_debt_pressure_l1
            }

            foreach mtransform in ///
                fd1_level fd1_log fd1_asinh fd1_winsor fd1_z fd1_log_winsor ///
                fd1_delta fd1_dlog ///
                fd1_deficit fd1_log_deficit fd1_inverse ///
                fd2_level fd2_log fd2_asinh fd2_winsor fd2_z fd2_log_winsor ///
                fd2_delta fd2_dlog ///
                fd2_deficit fd2_log_deficit fd2_inverse {

                if "`mtransform'" == "fd1_level" {
                    local mvar fin_dev_1
                    local meaning same_direction
                }
                if "`mtransform'" == "fd1_log" {
                    local mvar ln_fin_dev_1
                    local meaning same_direction
                }
                if "`mtransform'" == "fd1_asinh" {
                    local mvar asinh_fin_dev_1
                    local meaning same_direction
                }
                if "`mtransform'" == "fd1_winsor" {
                    local mvar w_fin_dev_1
                    local meaning same_direction
                }
                if "`mtransform'" == "fd1_z" {
                    local mvar z_fin_dev_1
                    local meaning same_direction
                }
                if "`mtransform'" == "fd1_log_winsor" {
                    local mvar w_ln_fin_dev_1
                    local meaning same_direction
                }
                if "`mtransform'" == "fd1_delta" {
                    local mvar d_fin_dev_1
                    local meaning change
                }
                if "`mtransform'" == "fd1_dlog" {
                    local mvar d_ln_fin_dev_1
                    local meaning change
                }
                if "`mtransform'" == "fd1_deficit" {
                    local mvar neg_fin_dev_1
                    local meaning reverse_coded
                }
                if "`mtransform'" == "fd1_log_deficit" {
                    local mvar neg_ln_fin_dev_1
                    local meaning reverse_coded
                }
                if "`mtransform'" == "fd1_inverse" {
                    local mvar inv_fin_dev_1
                    local meaning inverse
                }

                if "`mtransform'" == "fd2_level" {
                    local mvar fin_dev_2
                    local meaning same_direction
                }
                if "`mtransform'" == "fd2_log" {
                    local mvar ln_fin_dev_2
                    local meaning same_direction
                }
                if "`mtransform'" == "fd2_asinh" {
                    local mvar asinh_fin_dev_2
                    local meaning same_direction
                }
                if "`mtransform'" == "fd2_winsor" {
                    local mvar w_fin_dev_2
                    local meaning same_direction
                }
                if "`mtransform'" == "fd2_z" {
                    local mvar z_fin_dev_2
                    local meaning same_direction
                }
                if "`mtransform'" == "fd2_log_winsor" {
                    local mvar w_ln_fin_dev_2
                    local meaning same_direction
                }
                if "`mtransform'" == "fd2_delta" {
                    local mvar d_fin_dev_2
                    local meaning change
                }
                if "`mtransform'" == "fd2_dlog" {
                    local mvar d_ln_fin_dev_2
                    local meaning change
                }
                if "`mtransform'" == "fd2_deficit" {
                    local mvar neg_fin_dev_2
                    local meaning reverse_coded
                }
                if "`mtransform'" == "fd2_log_deficit" {
                    local mvar neg_ln_fin_dev_2
                    local meaning reverse_coded
                }
                if "`mtransform'" == "fd2_inverse" {
                    local mvar inv_fin_dev_2
                    local meaning inverse
                }

                use `panel', clear
                xtset city_id year
                if "`spec'" == "ctrl" {
                    keep if !missing(`mvar', `xvar', `dvar', `ctrlmiss', city_id, year)
                }
                else {
                    keep if !missing(`mvar', `xvar', `dvar', city_id, year)
                }
                quietly count
                if r(N) < 100 {
                    continue
                }

                capture noisily xtreg `mvar' c.`xvar'##c.`dvar' `ctrl_part' i.year, fe vce(cluster city_id)
                if _rc == 0 {
                    scalar b_xd = _b[c.`xvar'#c.`dvar']
                    scalar se_xd = _se[c.`xvar'#c.`dvar']
                    scalar p_xd = 2 * ttail(e(df_r), abs(b_xd / se_xd))
                    post `posth' ///
                        ("`spec'") ("`xform'") ("`xvar'") ("`dform'") ("`dvar'") ///
                        ("`mtransform'") ("`meaning'") ("`mvar'") ///
                        (b_xd) (se_xd) (p_xd) (e(N)) (e(r2_w))
                }
            }
        }
    }
}

postclose `posth'

use `results', clear
gen byte sig10 = p_xd < 0.10
gen byte sig05 = p_xd < 0.05
gen byte sig01 = p_xd < 0.01
gen byte neg_sig10 = b_xd < 0 & sig10 == 1
gen byte neg_sig05 = b_xd < 0 & sig05 == 1
gen byte neg_sig01 = b_xd < 0 & sig01 == 1
order spec xform xvar dform dvar mtransform meaning mvar b_xd se_xd p_xd N r2w sig10 sig05 sig01 neg_sig10 neg_sig05 neg_sig01
export delimited using "`resultcsv'", replace

preserve
keep if neg_sig10 == 1
sort meaning spec mtransform xform dform p_xd
export delimited using "`selectedcsv'", replace
restore

quietly count
di "All mechanism-equation paths estimated: " r(N)
quietly count if neg_sig10 == 1
di "Negative significant paths p<0.10: " r(N)
quietly count if neg_sig05 == 1
di "Negative significant paths p<0.05: " r(N)
quietly count if neg_sig05 == 1 & meaning == "same_direction"
di "Negative significant same-direction paths p<0.05: " r(N)
quietly count if neg_sig05 == 1 & meaning == "change"
di "Negative significant change paths p<0.05: " r(N)
quietly count if neg_sig05 == 1 & inlist(meaning, "reverse_coded", "inverse")
di "Negative significant reverse/inverse paths p<0.05: " r(N)
di "Full result CSV: `resultcsv'"
di "Selected negative result CSV: `selectedcsv'"

log close
