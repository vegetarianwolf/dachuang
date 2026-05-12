$ErrorActionPreference = 'Stop'

$root = (Resolve-Path -LiteralPath '.\dachuang').Path
$resultCsv = Join-Path $root '运行日志与do代码\xtreg_mechanism_dualmodel_focus_ascii_results.csv'
$resultDir = Join-Path $root '实证结果'

$rows = Import-Csv -LiteralPath $resultCsv

function FNum([object]$v) {
    if ($null -eq $v) { return '' }
    $s = [string]$v
    if ([string]::IsNullOrWhiteSpace($s)) { return '' }
    try { return ('{0:G10}' -f [double]$s) } catch { return $s }
}

function FStar([object]$v) {
    if ($null -eq $v) { return '' }
    $s = [string]$v
    if ([string]::IsNullOrWhiteSpace($s)) { return '' }
    $p = [double]$s
    if ($p -lt 0.01) { return '***' }
    if ($p -lt 0.05) { return '**' }
    if ($p -lt 0.1) { return '*' }
    return ''
}

function IsSig([object]$v) {
    if ($null -eq $v) { return $false }
    $s = [string]$v
    if ([string]::IsNullOrWhiteSpace($s)) { return $false }
    return ([double]$s -lt 0.1)
}

function AddLine($sb, [string]$text='') { [void]$sb.AppendLine($text) }

function AddTable($sb, $rows, [string[]]$headers, [string[]]$props) {
    AddLine $sb ('| ' + ($headers -join ' | ') + ' |')
    AddLine $sb ('| ' + (($headers | ForEach-Object { '---' }) -join ' | ') + ' |')
    foreach ($row in $rows) {
        $vals = foreach ($p in $props) {
            $x = $row.$p
            if ($null -eq $x) { '' } else { ([string]$x).Replace("`r",' ').Replace("`n",' ') }
        }
        AddLine $sb ('| ' + ($vals -join ' | ') + ' |')
    }
    AddLine $sb
}

function BuildSummary($subset) {
    $items = foreach ($g in ($subset | Group-Object model_family, mvar)) {
        $parts = $g.Name -split ', '
        [pscustomobject]@{
            model_family = $parts[0]
            mvar = $parts[1]
            m_eq_sig = ($g.Group | Where-Object { $_.step -eq 'M_eq' -and (IsSig $_.p1 -or IsSig $_.p2 -or IsSig $_.p3) }).Count
            y_term1_sig = ($g.Group | Where-Object { $_.step -eq 'Y_eq' -and (IsSig $_.p1) }).Count
            y_term2_sig = ($g.Group | Where-Object { $_.step -eq 'Y_eq' -and (IsSig $_.p2) }).Count
            y_term3_sig = ($g.Group | Where-Object { $_.step -eq 'Y_eq' -and (IsSig $_.p3) }).Count
            total_rows = $g.Count
        }
    }
    return $items | Sort-Object model_family, @{Expression='m_eq_sig';Descending=$true}, @{Expression='y_term3_sig';Descending=$true}, @{Expression='y_term2_sig';Descending=$true}, @{Expression='y_term1_sig';Descending=$true}, mvar
}

function BuildTableRows($subset, [string]$modelFamily, [string]$step) {
    $rows0 = $subset | Where-Object { $_.model_family -eq $modelFamily -and $_.step -eq $step } | Sort-Object mvar, dvar, spec, yvar
    foreach ($r in $rows0) {
        [pscustomobject]@{
            spec = $r.spec
            yvar = $r.yvar
            dvar = $r.dvar
            mvar = $r.mvar
            term1 = $r.term1
            coef1 = FNum $r.b1
            se1 = FNum $r.se1
            p1 = FNum $r.p1
            sig1 = FStar $r.p1
            term2 = $r.term2
            coef2 = FNum $r.b2
            se2 = FNum $r.se2
            p2 = FNum $r.p2
            sig2 = FStar $r.p2
            term3 = $r.term3
            coef3 = FNum $r.b3
            se3 = FNum $r.se3
            p3 = FNum $r.p3
            sig3 = FStar $r.p3
            N = FNum $r.N
            r2w = FNum $r.r2w
        }
    }
}

$categoryMap = [ordered]@{
    early = '早期投资'
    soccap = '社会资本撬动效率'
    fc = '融资约束'
}

$overview = [System.Text.StringBuilder]::new()
AddLine $overview '# 机制检验总览：早期投资、社会资本撬动效率与融资约束'
AddLine $overview
AddLine $overview '## 本次操作'
AddLine $overview '- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`'
AddLine $overview '- 基准主线：`fund_est_scale_cum × debt_pressure` 与 `fund_est_scale_cum × debt_pressure_l1`'
AddLine $overview '- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`'
AddLine $overview '- 机制模型 A：`X × N -> M -> Y`'
AddLine $overview '- 机制模型 B：先检验 `N -> M`，再在结果方程中加入 `X × M`'
AddLine $overview '- 结果总行数：`' + $rows.Count + '`'
AddLine $overview
AddLine $overview '## 各类别显著性概览'

$overviewRows = foreach ($k in $categoryMap.Keys) {
    $subset = $rows | Where-Object { $_.category -eq $k }
    foreach ($s in (BuildSummary $subset)) {
        [pscustomobject]@{
            category = $categoryMap[$k]
            model = $s.model_family
            mvar = $s.mvar
            M_eq_sig = $s.m_eq_sig
            Y_term1_sig = $s.y_term1_sig
            Y_term2_sig = $s.y_term2_sig
            Y_term3_sig = $s.y_term3_sig
            total_rows = $s.total_rows
        }
    }
}

AddTable $overview $overviewRows @('category','model','mvar','M_eq_sig','Y_term1_sig','Y_term2_sig','Y_term3_sig','total_rows') @('category','model','mvar','M_eq_sig','Y_term1_sig','Y_term2_sig','Y_term3_sig','total_rows')

AddLine $overview '## 输出文件'
AddLine $overview '- do 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.do`'
AddLine $overview '- log 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.log`'
AddLine $overview '- 结果表：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii_results.csv`'

[System.IO.File]::WriteAllText((Join-Path $resultDir 'xtreg_mechanism_dualmodel_focus_overview.md'), $overview.ToString(), [System.Text.Encoding]::UTF8)

foreach ($k in $categoryMap.Keys) {
    $title = $categoryMap[$k]
    $subset = $rows | Where-Object { $_.category -eq $k }
    $summary = BuildSummary $subset
    $sb = [System.Text.StringBuilder]::new()
    AddLine $sb ('# 机制检验：' + $title)
    AddLine $sb
    AddLine $sb '## 本次操作'
    AddLine $sb '- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`'
    AddLine $sb '- 核心解释变量：`fund_est_scale_cum`'
    AddLine $sb '- 债务调节变量：`debt_pressure`、`debt_pressure_l1`'
    AddLine $sb '- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`'
    AddLine $sb '- 回归方法：地级市固定效应 + 年份固定效应，标准误按城市聚类'
    AddLine $sb
    AddLine $sb '## 显著结果摘要'
    AddTable $sb $summary @('model','mvar','M_eq_sig','Y_term1_sig','Y_term2_sig','Y_term3_sig','total_rows') @('model_family','mvar','m_eq_sig','y_term1_sig','y_term2_sig','y_term3_sig','total_rows')
    AddLine $sb '## 完整结果'
    AddLine $sb '### 模型 A：机制变量作为中介传导变量'
    AddLine $sb '#### A1. M_eq'
    AddTable $sb (BuildTableRows $subset 'mediated' 'M_eq') @('spec','dvar','mvar','term1','coef1','se1','p1','sig1','N','r2w') @('spec','dvar','mvar','term1','coef1','se1','p1','sig1','N','r2w')
    AddLine $sb '#### A2. Y_eq'
    AddTable $sb (BuildTableRows $subset 'mediated' 'Y_eq') @('spec','yvar','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','N','r2w') @('spec','yvar','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','N','r2w')
    AddLine $sb '### 模型 B：机制变量作为调节变量'
    AddLine $sb '#### B1. M_eq'
    AddTable $sb (BuildTableRows $subset 'moderator' 'M_eq') @('spec','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','N','r2w') @('spec','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','N','r2w')
    AddLine $sb '#### B2. Y_eq'
    AddTable $sb (BuildTableRows $subset 'moderator' 'Y_eq') @('spec','yvar','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','term3','coef3','se3','p3','sig3','N','r2w') @('spec','yvar','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','term3','coef3','se3','p3','sig3','N','r2w')
    $name = switch ($k) {
        'early' { 'xtreg_mechanism_early_dualmodel_focus.md' }
        'soccap' { 'xtreg_mechanism_soccap_dualmodel_focus.md' }
        'fc' { 'xtreg_mechanism_fc_dualmodel_focus.md' }
    }
    [System.IO.File]::WriteAllText((Join-Path $resultDir $name), $sb.ToString(), [System.Text.Encoding]::UTF8)
}
