param(
  [string]$BaseDir = 'c:\Users\Joe，\OneDrive\Desktop\dachuang\dachuang\原始数据打包_20260401',
  [string]$OutputFile = 'c:\Users\Joe，\OneDrive\Desktop\dachuang\dachuang\原始数据打包_20260401\2015-2024基金目录_合并去重_8135.csv'
)

Add-Type -AssemblyName Microsoft.VisualBasic

function Get-UniqueHeaders {
  param([string[]]$Headers)
  $seen = @{}
  $result = New-Object System.Collections.ArrayList
  foreach ($header in $Headers) {
    $name = [string]$header
    if ([string]::IsNullOrWhiteSpace($name)) { $name = 'Unnamed' }
    if (-not $seen.ContainsKey($name)) {
      $seen[$name] = 1
      [void]$result.Add($name)
    } else {
      $seen[$name]++
      [void]$result.Add(('{0}__{1}' -f $name, $seen[$name]))
    }
  }
  return $result
}

function Import-CsvWithHeaderRow {
  param(
    [string]$Path,
    [int]$HeaderRowIndex = 1
  )

  $parser = New-Object Microsoft.VisualBasic.FileIO.TextFieldParser((Resolve-Path -LiteralPath $Path))
  $parser.TextFieldType = [Microsoft.VisualBasic.FileIO.FieldType]::Delimited
  $parser.SetDelimiters(',')
  $parser.HasFieldsEnclosedInQuotes = $true
  $parser.TrimWhiteSpace = $false

  try {
    $rowIndex = 0
    $headers = $null
    while (-not $parser.EndOfData) {
      $fields = $parser.ReadFields()
      if ($rowIndex -eq $HeaderRowIndex) {
        $headers = Get-UniqueHeaders $fields
        break
      }
      $rowIndex++
    }

    if ($null -eq $headers) { return @() }

    $rows = New-Object System.Collections.ArrayList
    while (-not $parser.EndOfData) {
      $fields = $parser.ReadFields()
      $props = [ordered]@{}
      for ($i = 0; $i -lt $headers.Count; $i++) {
        $props[$headers[$i]] = if ($i -lt $fields.Count) { $fields[$i] } else { '' }
      }
      [void]$rows.Add([pscustomobject]$props)
    }
    return $rows
  } finally {
    $parser.Close()
  }
}

function Normalize-Name {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return '' }

  $t = $Text.Trim()
  $t = $t -replace '【[^】]*】', ''
  $t = $t -replace '\([^)]*\)', ''
  $t = $t -replace '（[^）]*）', ''
  $t = $t -replace '人民币基金', '基金'
  $t = $t -replace '创投', '创业投资'
  $t = $t -replace '产投', '产业投资'
  $t = $t -replace '风投', '风险投资'
  $t = $t -replace '私募', ''
  $t = $t -replace '[\s\-_—,.，/\\|·:：''"“”‘’\[\]【】()（）]', ''

  $suffixes = @(
    '创业投资基金合伙企业有限合伙','股权投资基金合伙企业有限合伙','私募股权投资基金合伙企业有限合伙','产业投资基金合伙企业有限合伙','投资基金合伙企业有限合伙',
    '创业投资合伙企业有限合伙','股权投资合伙企业有限合伙','产业投资合伙企业有限合伙','投资合伙企业有限合伙','基金合伙企业有限合伙',
    '创业投资企业有限合伙','股权投资企业有限合伙','投资企业有限合伙','有限合伙企业',
    '创业投资基金有限公司','股权投资基金有限公司','私募股权投资基金有限公司','产业投资基金有限公司','投资基金有限公司',
    '创业投资有限公司','股权投资有限公司','产业投资有限公司','投资有限公司',
    '有限责任公司','股份有限公司','有限公司','有限合伙','合伙企业','合伙',
    '创业投资基金','股权投资基金','产业投资基金','投资基金','创业投资','股权投资','产业投资','投资','基金'
  )

  $changed = $true
  while ($changed) {
    $changed = $false
    foreach ($suffix in $suffixes) {
      if ($t.EndsWith($suffix) -and $t.Length -gt $suffix.Length + 1) {
        $t = $t.Substring(0, $t.Length - $suffix.Length)
        $changed = $true
        break
      }
    }
  }

  return $t
}

function Parse-Date {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text) -or $Text -eq '--') { return $null }

  $s = $Text.Trim()
  $formats = @(
    'yyyy-MM-dd','yyyy/M/d','yyyy/M/dd','yyyy/MM/d','yyyy/MM/dd',
    'yyyy-M-d','yyyy-M-dd','yyyy-MM-d','yyyy.MM.dd','yyyy.M.d','yyyy.M.dd','yyyy.MM.d'
  )

  foreach ($fmt in $formats) {
    try { return [datetime]::ParseExact($s, $fmt, $null) } catch {}
  }

  try { return [datetime]$s } catch { return $null }
}

function Parse-Decimal {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text) -or $Text -eq '--') { return $null }

  $s = $Text.Trim()
  $s = $s -replace ',', ''
  $s = $s -replace '\(e\)', ''
  $s = $s -replace '\s+', ''

  $m = [regex]::Match($s, '[-+]?\d+(\.\d+)?')
  if (-not $m.Success) { return $null }

  try { return [decimal]$m.Value } catch { return $null }
}

function Get-ScaleInfo {
  param($Row)

  $raw = ''
  $currency = ''
  $unit = ''
  $rmbMillion = $null

  if ($Row.PSObject.Properties['目标规模(人民币/百万)']) {
    $raw = ([string]$Row.'目标规模(人民币/百万)').Trim()
    $currency = 'RMB'
    $unit = '百万人民币'
    $rmbMillion = Parse-Decimal $raw
  } elseif ($Row.PSObject.Properties['募集目标规模（万元）']) {
    $raw = ([string]$Row.'募集目标规模（万元）').Trim()
    $currency = 'RMB'
    $unit = '万元人民币'
    $value = Parse-Decimal $raw
    if ($null -ne $value) { $rmbMillion = [decimal]($value / 100) }
  } elseif ($Row.PSObject.Properties['募集目标规模']) {
    $raw = ([string]$Row.'募集目标规模').Trim()
    $unitText = ''
    if ($Row.PSObject.Properties['单位']) { $unitText = ([string]$Row.单位).Trim() }
    $currencyText = ''
    if ($Row.PSObject.Properties['基金币种']) { $currencyText = ([string]$Row.'基金币种').Trim() }

    $value = Parse-Decimal $raw
    $currency = if ($currencyText) { $currencyText } else { '未知' }
    $unit = if ($unitText) { $unitText } else { '未知' }

    if ($null -ne $value) {
      if ($unitText -match '万元') {
        if ($currencyText -match '人民币|RMB|CNY') { $rmbMillion = [decimal]($value / 100) }
      } elseif ($unitText -match '亿') {
        if ($currencyText -match '人民币|RMB|CNY') { $rmbMillion = [decimal]($value * 100) }
      } elseif ($unitText -match '百万') {
        if ($currencyText -match '人民币|RMB|CNY') { $rmbMillion = [decimal]$value }
      }
    }
  }

  $rmbBillion = $null
  if ($null -ne $rmbMillion) {
    $rmbBillion = [math]::Round(([double]$rmbMillion / 1000), 6)
  }

  return [pscustomobject]@{
    原始规模文本 = $raw
    规模币种 = $currency
    规模单位 = $unit
    目标规模_RMB_百万 = $rmbMillion
    目标规模_RMB_亿元 = $rmbBillion
  }
}

function Pick-Better {
  param(
    $Current,
    $Candidate,
    [string]$PropertyName
  )

  $currentValue = [string]$Current.$PropertyName
  $candidateValue = [string]$Candidate.$PropertyName

  if ([string]::IsNullOrWhiteSpace($currentValue) -and -not [string]::IsNullOrWhiteSpace($candidateValue)) {
    return $candidateValue
  }

  if ([string]::IsNullOrWhiteSpace($candidateValue)) {
    return $currentValue
  }

  if ($candidateValue.Length -gt $currentValue.Length) {
    return $candidateValue
  }

  return $currentValue
}

function New-FundRow {
  param(
    $Row,
    [string]$SourceName,
    [string]$SourceType
  )

  $full = ([string]$Row.基金全称).Trim()
  $short = ([string]$Row.基金简称).Trim()
  $dateText = ([string]$Row.成立时间).Trim()
  $date = Parse-Date $dateText
  $normKey = if (Normalize-Name $full) { Normalize-Name $full } else { Normalize-Name $short }

  $manager = ''
  if ($Row.PSObject.Properties['管理机构']) {
    $manager = ([string]$Row.管理机构).Trim()
  } elseif ($Row.PSObject.Properties['管理公司']) {
    $manager = ([string]$Row.管理公司).Trim()
  }

  $managerFull = ''
  if ($Row.PSObject.Properties['管理机构全称']) {
    $managerFull = ([string]$Row.管理机构全称).Trim()
  }

  $fundLevel = ''
  if ($Row.PSObject.Properties['基金级别']) {
    $fundLevel = ([string]$Row.基金级别).Trim()
    if ($fundLevel -eq '--') { $fundLevel = '' }
  }

  $fundCategory = ''
  if ($Row.PSObject.Properties['基金分类']) {
    $fundCategory = ([string]$Row.基金分类).Trim()
  } elseif ($Row.PSObject.Properties['基金类型']) {
    $fundCategory = ([string]$Row.基金类型).Trim()
  }

  $region = ''
  if ($Row.PSObject.Properties['注册地区']) {
    $region = ([string]$Row.注册地区).Trim()
  } elseif ($Row.PSObject.Properties['所在地']) {
    $region = ([string]$Row.所在地).Trim()
  }

  $scaleInfo = Get-ScaleInfo $Row

  return [pscustomobject]@{
    来源类型 = $SourceType
    来源表 = $SourceName
    基金简称 = $short
    基金全称 = $full
    标准化基金名 = $normKey
    成立时间 = $dateText
    成立日期 = $date
    成立年份 = if ($date) { $date.Year } else { '' }
    基金级别 = $fundLevel
    基金分类 = $fundCategory
    注册地区 = $region
    原始规模文本 = $scaleInfo.原始规模文本
    规模币种 = $scaleInfo.规模币种
    规模单位 = $scaleInfo.规模单位
    目标规模_RMB_百万 = $scaleInfo.目标规模_RMB_百万
    目标规模_RMB_亿元 = $scaleInfo.目标规模_RMB_亿元
    管理机构 = $manager
    管理机构全称 = $managerFull
  }
}

$infoDir = Join-Path $BaseDir '政府引导基金相关信息'
$catalogDir = Join-Path $BaseDir '政府引导基金清科投中目录'

$allRows = @()

foreach ($f in @('政府引导基金1 的副本.csv', '政府引导基金2 的副本.csv', '政府引导基金3 的副本.csv')) {
  $allRows += Import-Csv -LiteralPath (Join-Path $infoDir $f) | ForEach-Object {
    New-FundRow $_ $f '政府引导基金123'
  }
}

foreach ($f in @('政府引导基金清科目录（1).csv', '政府引导基金清科目录（2).csv', '政府引导基金清科目录（3）.csv')) {
  $allRows += Import-CsvWithHeaderRow (Join-Path $catalogDir $f) | ForEach-Object {
    New-FundRow $_ $f '清科目录'
  }
}

foreach ($f in @('投中数据全部政府引导基金名录（上）.csv', '投资数据全部政府引导基金目录（下）.csv')) {
  $allRows += Import-CsvWithHeaderRow (Join-Path $catalogDir $f) | ForEach-Object {
    New-FundRow $_ $f '投中目录'
  }
}

$filtered = @(
  $allRows |
    Where-Object {
      $_.成立日期 -and
      $_.成立日期 -ge [datetime]'2015-01-01' -and
      $_.成立日期 -lt [datetime]'2025-01-01' -and
      -not [string]::IsNullOrWhiteSpace($_.标准化基金名)
    }
)

$grouped = $filtered | Group-Object 标准化基金名 | Where-Object { $_.Name }
$finalRows = New-Object System.Collections.Generic.List[object]

foreach ($group in $grouped) {
  $ordered = $group.Group | Sort-Object `
    @{ Expression = { if ($_.来源类型 -eq '政府引导基金123') { 1 } elseif ($_.来源类型 -eq '清科目录') { 2 } else { 3 } } }, `
    @{ Expression = { if ($_.基金级别) { 0 } else { 1 } } }, `
    @{ Expression = { if ($_.基金全称) { 0 } else { 1 } } }, `
    @{ Expression = { $_.基金全称.Length }; Descending = $true }

  $base = $ordered | Select-Object -First 1
  $merged = [pscustomobject]@{
    标准化基金名 = $group.Name
    基金简称 = $base.基金简称
    基金全称 = $base.基金全称
    成立时间 = $base.成立时间
    成立年份 = $base.成立年份
    基金级别 = $base.基金级别
    基金分类 = $base.基金分类
    注册地区 = $base.注册地区
    原始规模文本 = $base.原始规模文本
    规模币种 = $base.规模币种
    规模单位 = $base.规模单位
    目标规模_RMB_百万 = $base.目标规模_RMB_百万
    目标规模_RMB_亿元 = $base.目标规模_RMB_亿元
    管理机构 = $base.管理机构
    管理机构全称 = $base.管理机构全称
    来源类型_主记录 = $base.来源类型
    来源表_主记录 = $base.来源表
    合并来源数 = ($group.Group | Select-Object -ExpandProperty 来源表 -Unique).Count
    合并来源表 = (($group.Group | Select-Object -ExpandProperty 来源表 -Unique) -join ' | ')
    合并来源类型 = (($group.Group | Select-Object -ExpandProperty 来源类型 -Unique) -join ' | ')
  }

  foreach ($item in $ordered | Select-Object -Skip 1) {
    $merged.基金简称 = Pick-Better $merged $item '基金简称'
    $merged.基金全称 = Pick-Better $merged $item '基金全称'
    $merged.基金级别 = Pick-Better $merged $item '基金级别'
    $merged.基金分类 = Pick-Better $merged $item '基金分类'
    $merged.注册地区 = Pick-Better $merged $item '注册地区'
    $merged.原始规模文本 = Pick-Better $merged $item '原始规模文本'
    $merged.规模币种 = Pick-Better $merged $item '规模币种'
    $merged.规模单位 = Pick-Better $merged $item '规模单位'
    if ($null -eq $merged.目标规模_RMB_百万 -and $null -ne $item.目标规模_RMB_百万) {
      $merged.目标规模_RMB_百万 = $item.目标规模_RMB_百万
    }
    if ($null -eq $merged.目标规模_RMB_亿元 -and $null -ne $item.目标规模_RMB_亿元) {
      $merged.目标规模_RMB_亿元 = $item.目标规模_RMB_亿元
    }
    $merged.管理机构 = Pick-Better $merged $item '管理机构'
    $merged.管理机构全称 = Pick-Better $merged $item '管理机构全称'
  }

  $finalRows.Add($merged)
}

$finalRows | Sort-Object 成立年份, 标准化基金名 | Export-Csv -LiteralPath $OutputFile -NoTypeInformation -Encoding UTF8

Write-Output ('output=' + $OutputFile)
Write-Output ('all_rows=' + $allRows.Count)
Write-Output ('filtered_rows_2015_2024=' + $filtered.Count)
Write-Output ('final_unique_rows=' + $finalRows.Count)
