$ErrorActionPreference = 'Stop'

$root = 'C:\Users\Joe，\OneDrive\Desktop\dachuang\dachuang'
$resultCsv = Join-Path $root '运行日志与do代码\xtreg_mechanism_dualmodel_focus_ascii_results.csv'
$resultDir = Join-Path $root '实证结果'
$doPath = Join-Path $root '运行日志与do代码\xtreg_mechanism_dualmodel_focus_ascii.do'
$logPath = Join-Path $root '运行日志与do代码\xtreg_mechanism_dualmodel_focus_ascii.log'

$rows = Import-Csv -LiteralPath $resultCsv

function Format-Num {
    param([object]$Value)
    if ($null -eq $Value) { return '' }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return '' }
    try {
        return ('{0:G10}' -f [double]$text)
    }
    catch {
        return $text
    }
}

function Sig-Star {
    param([object]$PValue)
    if ($null -eq $PValue) { return '' }
    $text = [string]$PValue
    if ([string]::IsNullOrWhiteSpace($text)) { return '' }
    $p = [double]$text
    if ($p -lt 0.01) { return '***' }
    if ($p -lt 0.05) { return '**' }
    if ($p -lt 0.1) { return '*' }
    return ''
}

function Is-Sig {
    param([object]$PValue)
    if ($null -eq $PValue) { return $false }
    $text = [string]$PValue
    if ([string]::IsNullOrWhiteSpace($text)) { return $false }
    return ([double]$text -lt 0.1)
}

function Add-Line {
    param([System.Text.StringBuilder]$Builder, [string]$Text = '')
    [void]$Builder.AppendLine($Text)
}

function Add-Table {
    param(
        [System.Text.StringBuilder]$Builder,
        [System.Collections.IEnumerable]$Rows,
        [string[]]$Headers,
        [string[]]$Props
    )
    Add-Line $Builder ('| ' + ($Headers -join ' | ') + ' |')
    Add-Line $Builder ('| ' + (($Headers | ForEach-Object { '---' }) -join ' | ') + ' |')
    foreach ($row in $Rows) {
        $vals = foreach ($prop in $Props) {
            $val = $row.$prop
            if ($null -eq $val) { '' } else { ([string]$val).Replace("`r",' ').Replace("`n",' ') }
        }
        Add-Line $Builder ('| ' + ($vals -join ' | ') + ' |')
    }
    Add-Line $Builder
}

function Build-SummaryRows {
    param([object[]]$CategoryRows)

    $items = foreach ($grp in ($CategoryRows | Group-Object model_family, mvar)) {
        $nameParts = $grp.Name -split ', '
        $modelFamily = $nameParts[0]
        $mvar = $nameParts[1]
        [pscustomobject]@{
            model_family = $modelFamily
            mvar = $mvar
            m_eq_sig = ($grp.Group | Where-Object { $_.step -eq 'M_eq' -and (Is-Sig $_.p1 -or Is-Sig $_.p2 -or Is-Sig $_.p3) }).Count
            y_term1_sig = ($grp.Group | Where-Object { $_.step -eq 'Y_eq' -and (Is-Sig $_.p1) }).Count
            y_term2_sig = ($grp.Group | Where-Object { $_.step -eq 'Y_eq' -and (Is-Sig $_.p2) }).Count
            y_term3_sig = ($grp.Group | Where-Object { $_.step -eq 'Y_eq' -and (Is-Sig $_.p3) }).Count
            total_rows = $grp.Count
        }
    }

    return $items | Sort-Object model_family, @{Expression='m_eq_sig';Descending=$true}, @{Expression='y_term3_sig';Descending=$true}, @{Expression='y_term2_sig';Descending=$true}, @{Expression='y_term1_sig';Descending=$true}, mvar
}

function Build-TableRows {
    param(
        [object[]]$InputRows,
        [string]$ModelFamily,
        [string]$Step
    )

    $rows = $InputRows | Where-Object { $_.model_family -eq $ModelFamily -and $_.step -eq $Step } | Sort-Object mvar, dvar, spec, yvar

    if ($ModelFamily -eq 'mediated' -and $Step -eq 'M_eq') {
        return $rows | ForEach-Object {
            [pscustomobject]@{
                spec = $_.spec
                dvar = $_.dvar
                mvar = $_.mvar
                term1 = $_.term1
                coef1 = Format-Num $_.b1
                se1 = Format-Num $_.se1
                p1 = Format-Num $_.p1
                sig1 = Sig-Star $_.p1
                N = Format-Num $_.N
                r2w = Format-Num $_.r2w
            }
        }
    }

    if ($ModelFamily -eq 'mediated' -and $Step -eq 'Y_eq') {
        return $rows | ForEach-Object {
            [pscustomobject]@{
                spec = $_.spec
                yvar = $_.yvar
                dvar = $_.dvar
                mvar = $_.mvar
                term1 = $_.term1
                coef1 = Format-Num $_.b1
                se1 = Format-Num $_.se1
                p1 = Format-Num $_.p1
                sig1 = Sig-Star $_.p1
                term2 = $_.term2
                coef2 = Format-Num $_.b2
                se2 = Format-Num $_.se2
                p2 = Format-Num $_.p2
                sig2 = Sig-Star $_.p2
                N = Format-Num $_.N
                r2w = Format-Num $_.r2w
            }
        }
    }

    if ($ModelFamily -eq 'moderator' -and $Step -eq 'M_eq') {
        return $rows | ForEach-Object {
            [pscustomobject]@{
                spec = $_.spec
                dvar = $_.dvar
                mvar = $_.mvar
                term1 = $_.term1
                coef1 = Format-Num $_.b1
                se1 = Format-Num $_.se1
                p1 = Format-Num $_.p1
                sig1 = Sig-Star $_.p1
                term2 = $_.term2
                coef2 = Format-Num $_.b2
                se2 = Format-Num $_.se2
                p2 = Format-Num $_.p2
                sig2 = Sig-Star $_.p2
                N = Format-Num $_.N
                r2w = Format-Num $_.r2w
            }
        }
    }

    return $rows | ForEach-Object {
        [pscustomobject]@{
            spec = $_.spec
            yvar = $_.yvar
            dvar = $_.dvar
            mvar = $_.mvar
            term1 = $_.term1
            coef1 = Format-Num $_.b1
            se1 = Format-Num $_.se1
            p1 = Format-Num $_.p1
            sig1 = Sig-Star $_.p1
            term2 = $_.term2
            coef2 = Format-Num $_.b2
            se2 = Format-Num $_.se2
            p2 = Format-Num $_.p2
            sig2 = Sig-Star $_.p2
            term3 = $_.term3
            coef3 = Format-Num $_.b3
            se3 = Format-Num $_.se3
            p3 = Format-Num $_.p3
            sig3 = Sig-Star $_.p3
            N = Format-Num $_.N
            r2w = Format-Num $_.r2w
        }
    }
}

$categoryMap = [ordered]@{
    early = '早期投资'
    soccap = '社会资本撬动效率'
    fc = '融资约束'
}

$overview = [System.Text.StringBuilder]::new()
Add-Line $overview '# 机制检验总览：早期投资、社会资本撬动效率与融资约束'
Add-Line $overview
Add-Line $overview '## 本次操作'
Add-Line $overview '- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`'
Add-Line $overview '- 基准主线：`fund_est_scale_cum × debt_pressure` 与 `fund_est_scale_cum × debt_pressure_l1`'
Add-Line $overview '- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`'
Add-Line $overview '- 控制变量版本：同时报告 `noctrl` 和 `ctrl` 两类结果'
Add-Line $overview '- 机制模型 A：`X × N -> M -> Y`，即把机制变量 `M` 视为调节效应的中介传导变量'
Add-Line $overview '- 机制模型 B：先检验 `N -> M`，再在结果方程中加入 `X × M`，即把机制变量 `M` 视为承接债务压力调节效应的调节变量'
Add-Line $overview '- 结果总行数：`' + $rows.Count + '`'
Add-Line $overview
Add-Line $overview '## 各类别显著性概览'

$overviewRows = foreach ($key in $categoryMap.Keys) {
    $subset = $rows | Where-Object { $_.category -eq $key }
    $summary = Build-SummaryRows $subset
    foreach ($s in $summary) {
        [pscustomobject]@{
            category = $categoryMap[$key]
            model_family = $s.model_family
            mvar = $s.mvar
            m_eq_sig = $s.m_eq_sig
            y_term1_sig = $s.y_term1_sig
            y_term2_sig = $s.y_term2_sig
            y_term3_sig = $s.y_term3_sig
            total_rows = $s.total_rows
        }
    }
}

Add-Table $overview $overviewRows @('category','model','mvar','M_eq_sig','Y_term1_sig','Y_term2_sig','Y_term3_sig','total_rows') @('category','model_family','mvar','m_eq_sig','y_term1_sig','y_term2_sig','y_term3_sig','total_rows')

Add-Line $overview '## 结论摘要'
Add-Line $overview '- 早期投资类中，`early_inv_amt`、`early_inv_amt_share` 在机制方程里更容易出现显著，`early_inv_count` 在结果方程里显著最多。'
Add-Line $overview '- 社会资本类中，`gov_amt`、`matched_commit_amt`、`fund_commit_total`、`gp_amt` 的信号相对更多，`soccap_leverage` 本身并不是最强口径。'
Add-Line $overview '- 融资约束类中，`fcity_fc_mean` 在机制方程里最稳定；若把机制变量视为调节变量，则 `fcity_fc_mean` 与 `fcity_sa_mean` 的 `X × M` 项显著最多。'
Add-Line $overview '- 绝大多数结果方程里，原始债务调节项 `fund_est_scale_cum × debt_pressure` 仍保持负向显著，说明债务压力削弱基金扶持创新效果这一主结论较稳。'
Add-Line $overview
Add-Line $overview '## 输出文件'
Add-Line $overview '- do 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.do`'
Add-Line $overview '- log 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.log`'
Add-Line $overview '- 结果表：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii_results.csv`'
Add-Line $overview '- 分类结果：'
Add-Line $overview '  - `xtreg_mechanism_early_dualmodel_focus.md`'
Add-Line $overview '  - `xtreg_mechanism_soccap_dualmodel_focus.md`'
Add-Line $overview '  - `xtreg_mechanism_fc_dualmodel_focus.md`'

[System.IO.File]::WriteAllText((Join-Path $resultDir 'xtreg_mechanism_dualmodel_focus_overview.md'), $overview.ToString(), [System.Text.Encoding]::UTF8)

foreach ($key in $categoryMap.Keys) {
    $title = $categoryMap[$key]
    $categoryRows = $rows | Where-Object { $_.category -eq $key }
    $summaryRows = Build-SummaryRows $categoryRows
    $builder = [System.Text.StringBuilder]::new()

    Add-Line $builder ('# 机制检验：' + $title)
    Add-Line $builder
    Add-Line $builder '## 本次操作'
    Add-Line $builder '- 数据集：`面板数据/地级市总面板_2015_2024_英文版.csv`'
    Add-Line $builder '- 核心解释变量：`fund_est_scale_cum`'
    Add-Line $builder '- 债务调节变量：`debt_pressure`、`debt_pressure_l1`'
    Add-Line $builder '- 因变量：`pat_invent_apply`、`pat_utility_apply`、`pat_apply_total`'
    Add-Line $builder '- 回归方法：地级市固定效应 + 年份固定效应，标准误按城市聚类'
    Add-Line $builder '- 报告说明：以下表格完整记录该类别下所有已尝试规格的系数、标准误、p 值和显著性星号'
    Add-Line $builder

    Add-Line $builder '## 模型设定'
    Add-Line $builder '### 模型 A：机制变量作为中介传导变量'
    Add-Line $builder '- 机制方程：`M_it = a0 + a1 X_it + a2 N_it + a3 X_it × N_it + controls + FE + u_it`'
    Add-Line $builder '- 结果方程：`Y_it = c0 + c1 X_it + c2 N_it + c3 X_it × N_it + c4 M_it + controls + FE + v_it`'
    Add-Line $builder '- 关注系数：机制方程中的 `X × N`，以及结果方程中的 `M`'
    Add-Line $builder '### 模型 B：机制变量作为调节变量'
    Add-Line $builder '- 机制方程：`M_it = d0 + d1 X_it + d2 N_it + controls + FE + r_it`'
    Add-Line $builder '- 结果方程：`Y_it = e0 + e1 X_it + e2 N_it + e3 X_it × N_it + e4 M_it + e5 X_it × M_it + controls + FE + w_it`'
    Add-Line $builder '- 关注系数：机制方程中的 `N`，以及结果方程中的 `X × M`'
    Add-Line $builder

    Add-Line $builder '## 显著结果摘要'
    Add-Table $builder $summaryRows @('model','mvar','M_eq_sig','Y_term1_sig','Y_term2_sig','Y_term3_sig','total_rows') @('model_family','mvar','m_eq_sig','y_term1_sig','y_term2_sig','y_term3_sig','total_rows')

    Add-Line $builder '## 完整结果'

    Add-Line $builder '### 模型 A：机制变量作为中介传导变量'
    Add-Line $builder '#### A1. 机制方程完整结果'
    $tableA1 = Build-TableRows $categoryRows 'mediated' 'M_eq'
    Add-Table $builder $tableA1 @('spec','dvar','mvar','term1','coef','se','p','sig','N','r2w') @('spec','dvar','mvar','term1','coef1','se1','p1','sig1','N','r2w')

    Add-Line $builder '#### A2. 结果方程完整结果'
    $tableA2 = Build-TableRows $categoryRows 'mediated' 'Y_eq'
    Add-Table $builder $tableA2 @('spec','yvar','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','N','r2w') @('spec','yvar','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','N','r2w')

    Add-Line $builder '### 模型 B：机制变量作为调节变量'
    Add-Line $builder '#### B1. 机制方程完整结果'
    $tableB1 = Build-TableRows $categoryRows 'moderator' 'M_eq'
    Add-Table $builder $tableB1 @('spec','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','N','r2w') @('spec','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','N','r2w')

    Add-Line $builder '#### B2. 结果方程完整结果'
    $tableB2 = Build-TableRows $categoryRows 'moderator' 'Y_eq'
    Add-Table $builder $tableB2 @('spec','yvar','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','term3','coef3','se3','p3','sig3','N','r2w') @('spec','yvar','dvar','mvar','term1','coef1','se1','p1','sig1','term2','coef2','se2','p2','sig2','term3','coef3','se3','p3','sig3','N','r2w')

    Add-Line $builder '## 输出文件'
    Add-Line $builder '- do 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.do`'
    Add-Line $builder '- log 文件：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii.log`'
    Add-Line $builder '- 结果表：`运行日志与do代码/xtreg_mechanism_dualmodel_focus_ascii_results.csv`'

    $filename = switch ($key) {
        'early' { 'xtreg_mechanism_early_dualmodel_focus.md' }
        'soccap' { 'xtreg_mechanism_soccap_dualmodel_focus.md' }
        'fc' { 'xtreg_mechanism_fc_dualmodel_focus.md' }
    }

    [System.IO.File]::WriteAllText((Join-Path $resultDir $filename), $builder.ToString(), [System.Text.Encoding]::UTF8)
}
