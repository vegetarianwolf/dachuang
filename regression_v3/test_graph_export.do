* ============================================================================
* test_graph_export.do — Test which file extensions stata-mcp lets through
* ============================================================================
clear all
set more off

* Simple scatter plot for export testing
sysuse auto, clear

* Export trials: .png, .svg, .pdf, .gph
local OUTDIR "C:/Users/21288/Desktop/DACHUANG/dachuang/regression_v3"

twoway scatter mpg weight, title("Test graph") name(g1, replace)
graph export "`OUTDIR'/test_export.png", replace
graph export "`OUTDIR'/test_export.svg", replace
graph export "`OUTDIR'/test_export.pdf", replace
graph save   "`OUTDIR'/test_export.gph", replace

display "=== Export test complete ==="
display "Check which files appear in regression_v3/"
