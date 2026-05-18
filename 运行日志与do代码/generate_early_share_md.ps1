$ErrorActionPreference = "Stop"

$logDir = "..\运行日志与do代码"
$basename = "xtreg_mechanism_early_share_focus_ascii"
$resultsPath = Join-Path $logDir "$basename`_results.csv"
$selectedPath = Join-Path $logDir "$basename`_selected.csv"
$outPath = "$basename.md"

$results = Import-Csv $resultsPath
$selected = Import-Csv $selectedPath

function ToDoubleOrNull([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    return [double]$value
}

function FmtNum([string]$value) {
    $d = ToDoubleOrNull $value
    if ($null -eq $d) { return "" }
    if ([math]::Abs($d) -gt 0 -and [math]::Abs($d) -lt 0.001) {
        return ("{0:E3}" -f $d)
    }
    return ("{0:N4}" -f $d)
}

function FmtP([string]$value) {
    $d = ToDoubleOrNull $value
    if ($null -eq $d) { return "" }
    if ($d -lt 0.001) { return ("{0:E3}" -f $d) }
    return ("{0:N4}" -f $d)
}

function Stars([string]$p) {
    $d = ToDoubleOrNull $p
    if ($null -eq $d) { return "" }
    if ($d -le 0.01) { return "***" }
    if ($d -le 0.05) { return "**" }
    if ($d -le 0.1) { return "*" }
    return ""
}

function ModelLabel([string]$model) {
    switch ($model) {
        "mediator" { return "A 中介传导" }
        "moderator" { return "B 调节机制" }
        "triple" { return "C 三重交互" }
        default { return $model }
    }
}

function TransformLabel([string]$transform) {
    switch ($transform) {
        "raw" { return "原始比例" }
        "winsor" { return "1/99缩尾" }
        "asin" { return "arcsin-sqrt" }
        "logit" { return "logit" }
        default { return $transform }
    }
}

function SourceLabel([string]$source) {
    switch ($source) {
        "early_inv_amt_share" { return "早期投资金额占比" }
        "early_inv_count_share" { return "早期投资事件占比" }
        default { return $source }
    }
}

function EscapeMd([string]$value) {
    if ($null -eq $value) { return "" }
    return ($value -replace "\|", "\|")
}

function AddLine([System.Collections.Generic.List[string]]$lines, [string]$line = "") {
    [void]$lines.Add($line)
}

function AddSelectedTable([System.Collections.Generic.List[string]]$lines, $rows) {
    AddLine $lines "| 模型 | 因变量 | 债务变量 | 比例变量 | 变换 | 规格 | N | 路径1系数 | 路径1p | 路径2系数 | 路径2p | X×D系数 | X×Dp | 判定 |"
    AddLine $lines "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"
    foreach ($r in $rows) {
        $judge = if ($r.pass05 -eq "1") { "5%成立" } elseif ($r.pass10 -eq "1") { "10%成立" } else { "" }
        AddLine $lines ("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7}{8} | {9} | {10}{11} | {12} | {13}{14} | {15} | {16} |" -f `
            (ModelLabel $r.model), (EscapeMd $r.yvar), (EscapeMd $r.dvar), (SourceLabel $r.m_source), (TransformLabel $r.transform), $r.spec, $r.N, `
            (FmtNum $r.coef_path1), (Stars $r.p_path1), (FmtP $r.p_path1), `
            (FmtNum $r.coef_path2), (Stars $r.p_path2), (FmtP $r.p_path2), `
            (FmtNum $r.coef_xd), (Stars $r.p_xd), (FmtP $r.p_xd), $judge)
    }
}

function AddFullTable([System.Collections.Generic.List[string]]$lines, $rows) {
    AddLine $lines "| 模型 | 因变量 | 债务变量 | 比例变量 | 变换 | 规格 | N | 路径1 coef | 路径1 se | 路径1 p | 路径2 coef | 路径2 se | 路径2 p | X×D coef | X×D se | X×D p |"
    AddLine $lines "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    foreach ($r in $rows) {
        AddLine $lines ("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7}{8} | {9} | {10} | {11}{12} | {13} | {14} | {15}{16} | {17} | {18} |" -f `
            (ModelLabel $r.model), (EscapeMd $r.yvar), (EscapeMd $r.dvar), (SourceLabel $r.m_source), (TransformLabel $r.transform), $r.spec, $r.N, `
            (FmtNum $r.coef_path1), (Stars $r.p_path1), (FmtNum $r.se_path1), (FmtP $r.p_path1), `
            (FmtNum $r.coef_path2), (Stars $r.p_path2), (FmtNum $r.se_path2), (FmtP $r.p_path2), `
            (FmtNum $r.coef_xd), (Stars $r.p_xd), (FmtNum $r.se_xd), (FmtP $r.p_xd))
    }
}

$total = $results.Count
$mediatorTotal = ($results | Where-Object { $_.model -eq "mediator" }).Count
$moderatorTotal = ($results | Where-Object { $_.model -eq "moderator" }).Count
$tripleTotal = ($results | Where-Object { $_.model -eq "triple" }).Count
$selected10 = ($results | Where-Object { $_.pass10 -eq "1" }).Count
$selected05 = ($results | Where-Object { $_.pass05 -eq "1" }).Count
$mediatorPass10 = ($results | Where-Object { $_.model -eq "mediator" -and $_.pass10 -eq "1" }).Count
$moderatorPass10 = ($results | Where-Object { $_.model -eq "moderator" -and $_.pass10 -eq "1" }).Count
$triplePass10 = ($results | Where-Object { $_.model -eq "triple" -and $_.pass10 -eq "1" }).Count

$lines = [System.Collections.Generic.List[string]]::new()
AddLine $lines "# 早期投资比例机制检验：区别于绝对数量口径的聚焦结果"
AddLine $lines
AddLine $lines "回归日期：2026-05-16"
AddLine $lines
AddLine $lines "## 本次操作"
AddLine $lines
AddLine $lines "- 数据集：staging_ascii/panel_2015_2024_regression_ascii_clean.csv"
AddLine $lines "- 任务：按用户要求，只使用早期投资比例变量做机制检验，不使用 early_inv_amt 或 early_inv_count 作为机制变量。"
AddLine $lines "- 面板设定：地级市固定效应 + 年份固定效应，标准误按城市聚类。"
AddLine $lines "- 控制变量：ln_gdp、ln_fiscal_scitech、ln_pop、ln_secondary、ln_fdi。"
AddLine $lines "- 因变量：pat_invent_apply、pat_utility_apply、pat_apply_total。"
AddLine $lines "- 核心解释变量：fund_est_scale_cum。"
AddLine $lines "- 债务压力变量：debt_pressure、debt_pressure_l1。"
AddLine $lines "- 早期投资比例变量：early_inv_amt_share、early_inv_count_share。"
AddLine $lines "- 比例变量变换：原始比例、1/99 缩尾、arcsin-sqrt、logit。"
AddLine $lines
AddLine $lines "## 模型设定"
AddLine $lines
AddLine $lines "A. 中介传导模型：检验 fund_est_scale_cum × debt_pressure -> 早期投资比例 -> 创新产出。其中路径1为 X×D -> M，路径2为 M -> Y。"
AddLine $lines
AddLine $lines "B. 调节机制模型：先检验 debt_pressure -> 早期投资比例，再检验 fund_est_scale_cum × 早期投资比例 -> 创新产出。其中路径1为 D -> M，路径2为 X×M -> Y。"
AddLine $lines
AddLine $lines "C. 三重交互模型：先检验 debt_pressure -> 早期投资比例，再检验 fund_est_scale_cum × debt_pressure × 早期投资比例 -> 创新产出。其中路径2为三重交互项。"
AddLine $lines
AddLine $lines "## 总体结果"
AddLine $lines
AddLine $lines "- 共尝试 $total 个比例口径规格，其中中介传导 $mediatorTotal 个、调节机制 $moderatorTotal 个、三重交互 $tripleTotal 个。"
AddLine $lines "- 中介传导模型没有规格同时通过两条路径的 10% 显著性要求，因此不建议把早期投资比例写成普通中介。"
AddLine $lines "- 调节机制模型有 $moderatorPass10 个规格在 10% 水平成立，其中 early_inv_amt_share 对 pat_invent_apply 的滞后债务压力口径在 5% 水平成立。"
AddLine $lines "- 三重交互模型有 $triplePass10 个规格在 10% 水平成立，其中 early_inv_count_share 对 pat_invent_apply 的当期和滞后债务压力口径在 5% 水平成立。"
AddLine $lines "- 总体上，比例口径下更稳的写法是：早期投资比例不是普通中介，而是债务压力调节效应的承接性调节机制。"
AddLine $lines
AddLine $lines "## 显著结果"
AddLine $lines
AddLine $lines "下表仅列出路径1和路径2同时达到 10% 显著性的规格。星号规则：*** p≤0.01，** p≤0.05，* p≤0.1。"
AddLine $lines
AddSelectedTable $lines $selected
AddLine $lines
AddLine $lines "## 主要解释"
AddLine $lines
AddLine $lines "- early_inv_amt_share：在 debt_pressure_l1 口径下，债务压力显著影响早期投资金额占比，且该占比显著调节基金累计设立规模对发明专利申请的影响。原始比例和缩尾比例均在 5% 水平成立；arcsin-sqrt 变换在 10% 水平成立。"
AddLine $lines "- early_inv_count_share：事件占比在三重交互模型中更稳定。对于 pat_invent_apply，当期债务压力和滞后债务压力口径下的三重交互项均在 5% 水平显著；对于 pat_apply_total，滞后债务压力口径在 10% 水平显著。"
AddLine $lines "- 由于三重交互项多为正，而 fund_est_scale_cum × debt_pressure 项为负，结果更适合解释为：早期投资事件占比越高时，债务压力对基金创新扶持效应的负向调节有所改变或缓冲。该解释应以调节机制表述，不宜写成简单中介。"
AddLine $lines "- 中介传导模型中，部分规格的路径1显著，但路径2没有同时显著；因此本轮比例口径不支持早期投资比例作为普通中介变量。"
AddLine $lines
AddLine $lines "## 样本与缺失处理"
AddLine $lines
AddLine $lines "- 每个规格按所需变量逐项删除缺失值。"
AddLine $lines "- 原始比例变量仅在 0 <= share <= 1 范围内进入估计。"
AddLine $lines "- 缩尾变换使用样本内 1% 和 99% 分位数；本轮显著行中原始比例与缩尾结果相同，说明极端值不是显著性的来源。"
AddLine $lines "- logit 变换使用 log((share + 0.001)/(1 - share + 0.001))，用于保留 0 和 1 边界比例观测。"
AddLine $lines
AddLine $lines "## 输出文件"
AddLine $lines
AddLine $lines "- do 文件：运行日志与do代码/xtreg_mechanism_early_share_focus_ascii.do"
AddLine $lines "- log 文件：运行日志与do代码/xtreg_mechanism_early_share_focus_ascii.log"
AddLine $lines "- 完整结果表：运行日志与do代码/xtreg_mechanism_early_share_focus_ascii_results.csv"
AddLine $lines "- 显著结果表：运行日志与do代码/xtreg_mechanism_early_share_focus_ascii_selected.csv"
AddLine $lines
AddLine $lines "## 全部规格结果附录"
AddLine $lines
AddLine $lines "下表列出全部 288 个尝试规格。路径1、路径2 和 X×D 的含义见上文模型设定。"
AddLine $lines
AddFullTable $lines $results

[System.IO.File]::WriteAllLines($outPath, $lines, [System.Text.UTF8Encoding]::new($false))
