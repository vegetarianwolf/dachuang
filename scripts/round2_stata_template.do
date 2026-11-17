version 18
clear all
set more off
set type double
capture log close
args root
if `"`root'"' == "" local root `"`c(pwd)'"'
local outdir "`root'/实证结果/fiscal_fund_design_round2_20261117"
local basename "fiscal_fund_micro_round2_20261117"
local logfile "`root'/运行日志与do代码/`basename'.log"
log using "`logfile'", replace text
global r2out "`outdir'"
tempname results coefficients
tempfile resfile coeffile
postfile `results' str10 group str6 model str20 outcome str30 target str30 status double b se p lo hi N clusters units year_min year_max r2 using `resfile', replace
postfile `coefficients' str10 group str6 model str80 term double b se p lo hi using `coeffile', replace
global r2res `results'
global r2coef `coefficients'

capture program drop est
program define est
    syntax, group(string) model(string) y(name) rhs(string) target(name) flag(name) [absorb(name)]
    tempvar tag unit_tag used
    quietly count if `flag'
    local n=r(N)
    quietly egen `tag'=tag(source_id) if `flag'
    quietly count if `tag'==1
    local clusters=r(N)
    quietly egen `unit_tag'=tag(unit_id) if `flag'
    quietly count if `unit_tag'==1
    local units=r(N)
    if `n'<40 | `clusters'<20 {
        post $r2res ("`group'") ("`model'") ("`y'") ("`target'") ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`units') (.) (.) (.)
        exit
    }
    display "ROUND2 `model' `y' `rhs'"
    if "`absorb'"!="" {
        capture noisily areg `y' `rhs' if `flag', absorb(`absorb') vce(cluster source_id)
    }
    else {
        capture noisily regress `y' `rhs' if `flag', vce(cluster source_id)
    }
    local rc=_rc
    if `rc'!=0 {
        post $r2res ("`group'") ("`model'") ("`y'") ("`target'") ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`units') (.) (.) (.)
        exit
    }
    generate byte `used'=e(sample)
    quietly summarize year if `used', meanonly
    local ymin=r(min)
    local ymax=r(max)
    local b=_b[`target']
    local se=_se[`target']
    local p=cond(`se'>0, 2*ttail(e(df_r),abs(`b'/`se')),.)
    local critical=invttail(e(df_r),.025)
    local status "ok"
    if `se'==0 local status "target_omitted"
    post $r2res ("`group'") ("`model'") ("`y'") ("`target'") ("`status'") (`b') (`se') (`p') (`b'-`critical'*`se') (`b'+`critical'*`se') (e(N)) (`clusters') (`units') (`ymin') (`ymax') (e(r2))
    local terms : colnames e(b)
    foreach term of local terms {
        local b=_b[`term']
        local se=_se[`term']
        local p=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        post $r2coef ("`group'") ("`model'") ("`term'") (`b') (`se') (`p') (`b'-`critical'*`se') (`b'+`critical'*`se')
    }
    preserve
    keep if `used'
    keep obs_id unit_id unit_name source_city source_id year `y' p l_gdp l_secondary
    export delimited using "$r2out/samples/`model'.csv", replace
    restore
end

* MODEL_CALLS

postclose `results'
postclose `coefficients'
use `resfile', clear
export delimited using "`outdir'/model_results.csv", replace
list model status b se p N clusters units, noobs
use `coeffile', clear
export delimited using "`outdir'/all_coefficients.csv", replace
macro drop r2out r2res r2coef
display "ROUND2_COMPLETED"
log close
