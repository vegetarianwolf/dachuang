version 18
clear all
set more off
set type double
capture log close
args root
if `"`root'"' == "" local root "/Users/vegetarianwolf/Projects/dachuang"
local datafile "`root'/面板数据/f2_influence_round2_20261117.csv"
local outdir "`root'/实证结果/fiscal_fund_design_round2_20261117"
local basename "fiscal_round2_f2_influence_20261117"
local logfile "`root'/运行日志与do代码/`basename'.log"
log using "`logfile'", replace text
import delimited using "`datafile'", clear varnames(1) encoding(UTF-8) case(preserve)
tempname handle
tempfile results
postfile `handle' int variant str60 omitted_city long omitted_source_id str30 status double b se p lo hi N clusters funds r2 using `results', replace
preserve
keep if use_drop_01 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (1) ("丽水市") (5) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 1 丽水市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (1) ("丽水市") (5) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (1) ("丽水市") (5) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_02 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (2) ("亳州市") (8) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 2 亳州市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (2) ("亳州市") (8) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (2) ("亳州市") (8) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_03 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (3) ("兰州市") (10) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 3 兰州市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (3) ("兰州市") (10) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (3) ("兰州市") (10) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_04 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (4) ("南京市") (12) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 4 南京市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (4) ("南京市") (12) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (4) ("南京市") (12) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_05 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (5) ("南通市") (14) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 5 南通市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (5) ("南通市") (14) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (5) ("南通市") (14) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_06 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (6) ("合肥市") (18) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 6 合肥市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (6) ("合肥市") (18) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (6) ("合肥市") (18) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_07 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (7) ("咸宁市") (23) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 7 咸宁市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (7) ("咸宁市") (23) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (7) ("咸宁市") (23) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_08 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (8) ("哈尔滨市") (24) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 8 哈尔滨市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (8) ("哈尔滨市") (24) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (8) ("哈尔滨市") (24) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_09 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (9) ("宁波市") (27) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 9 宁波市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (9) ("宁波市") (27) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (9) ("宁波市") (27) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_10 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (10) ("安庆市") (28) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 10 安庆市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (10) ("安庆市") (28) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (10) ("安庆市") (28) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_11 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (11) ("安阳市") (30) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 11 安阳市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (11) ("安阳市") (30) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (11) ("安阳市") (30) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_12 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (12) ("宜宾市") (31) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 12 宜宾市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (12) ("宜宾市") (31) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (12) ("宜宾市") (31) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_13 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (13) ("宜昌市") (32) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 13 宜昌市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (13) ("宜昌市") (32) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (13) ("宜昌市") (32) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_14 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (14) ("宿迁市") (35) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 14 宿迁市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (14) ("宿迁市") (35) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (14) ("宿迁市") (35) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_15 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (15) ("常州市") (37) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 15 常州市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (15) ("常州市") (37) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (15) ("常州市") (37) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_16 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (16) ("常德市") (38) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 16 常德市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (16) ("常德市") (38) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (16) ("常德市") (38) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_17 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (17) ("广州市") (40) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 17 广州市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (17) ("广州市") (40) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (17) ("广州市") (40) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_18 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (18) ("德阳市") (42) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 18 德阳市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (18) ("德阳市") (42) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (18) ("德阳市") (42) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_19 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (19) ("成都市") (45) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 19 成都市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (19) ("成都市") (45) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (19) ("成都市") (45) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_20 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (20) ("新乡市") (48) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 20 新乡市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (20) ("新乡市") (48) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (20) ("新乡市") (48) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_21 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (21) ("无锡市") (50) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 21 无锡市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (21) ("无锡市") (50) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (21) ("无锡市") (50) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_22 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (22) ("晋城市") (52) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 22 晋城市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (22) ("晋城市") (52) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (22) ("晋城市") (52) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_23 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (23) ("榆林市") (55) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 23 榆林市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (23) ("榆林市") (55) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (23) ("榆林市") (55) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_24 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (24) ("武汉市") (56) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 24 武汉市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (24) ("武汉市") (56) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (24) ("武汉市") (56) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_25 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (25) ("泰州市") (61) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 25 泰州市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (25) ("泰州市") (61) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (25) ("泰州市") (61) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_26 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (26) ("洛阳市") (63) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 26 洛阳市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (26) ("洛阳市") (63) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (26) ("洛阳市") (63) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_27 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (27) ("深圳市") (68) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 27 深圳市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (27) ("深圳市") (68) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (27) ("深圳市") (68) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_28 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (28) ("湘潭市") (71) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 28 湘潭市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (28) ("湘潭市") (71) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (28) ("湘潭市") (71) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_29 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (29) ("湛江市") (72) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 29 湛江市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (29) ("湛江市") (72) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (29) ("湛江市") (72) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_30 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (30) ("焦作市") (75) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 30 焦作市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (30) ("焦作市") (75) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (30) ("焦作市") (75) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_31 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (31) ("盐城市") (78) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 31 盐城市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (31) ("盐城市") (78) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (31) ("盐城市") (78) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_32 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (32) ("眉山市") (79) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 32 眉山市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (32) ("眉山市") (79) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (32) ("眉山市") (79) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_33 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (33) ("蚌埠市") (87) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 33 蚌埠市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (33) ("蚌埠市") (87) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (33) ("蚌埠市") (87) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_34 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (34) ("西安市") (91) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 34 西安市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (34) ("西安市") (91) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (34) ("西安市") (91) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_35 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (35) ("贵阳市") (92) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 35 贵阳市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (35) ("贵阳市") (92) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (35) ("贵阳市") (92) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_36 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (36) ("郑州市") (97) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 36 郑州市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (36) ("郑州市") (97) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (36) ("郑州市") (97) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_37 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (37) ("长沙市") (102) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 37 长沙市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (37) ("长沙市") (102) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (37) ("长沙市") (102) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_38 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (38) ("阜阳市") (103) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 38 阜阳市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (38) ("阜阳市") (103) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (38) ("阜阳市") (103) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_39 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (39) ("青岛市") (106) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 39 青岛市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (39) ("青岛市") (106) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (39) ("青岛市") (106) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
preserve
keep if use_drop_40 == 1
quietly count
local n=r(N)
quietly egen __city_tag=tag(source_id)
quietly count if __city_tag==1
local clusters=r(N)
quietly egen __fund_tag=tag(fund_id)
quietly count if __fund_tag==1
local funds=r(N)
if `n'<40 | `clusters'<20 {
    post `handle' (40) ("马鞍山市") (108) ("insufficient_sample") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
}
else {
    display "F2_LEAVE_ONE_CITY 40 马鞍山市"
    capture noisily areg early p l_gdp l_secondary i.destination_year i.sector_id, absorb(fund_id) vce(cluster source_id)
    local rc=_rc
    if `rc'!=0 {
        post `handle' (40) ("马鞍山市") (108) ("stata_error_`rc'") (.) (.) (.) (.) (.) (`n') (`clusters') (`funds') (.)
    }
    else {
        local b=_b[p]
        local se=_se[p]
        local pval=cond(`se'>0,2*ttail(e(df_r),abs(`b'/`se')),.)
        local crit=invttail(e(df_r),.025)
        local status "ok"
        if `se'==0 local status "target_omitted"
        post `handle' (40) ("马鞍山市") (108) ("`status'") (`b') (`se') (`pval') (`b'-`crit'*`se') (`b'+`crit'*`se') (e(N)) (`clusters') (`funds') (e(r2))
    }
}
restore
postclose `handle'
use `results', clear
export delimited using "`outdir'/f2_leave_one_city.csv", replace
list omitted_city status b se p N clusters, noobs
display "F2_INFLUENCE_COMPLETED"
log close
