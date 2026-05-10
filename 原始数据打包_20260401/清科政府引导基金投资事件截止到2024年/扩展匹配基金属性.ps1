param(
  [string]$ProjectRoot = (Join-Path $PSScriptRoot '..'),
  [string]$OutputFile = (Join-Path $PSScriptRoot '2015-2024投资事件_附基金级别分类注册地区_扩展匹配.csv')
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
      $result.Add($name)
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
        $value = if ($i -lt $fields.Count) { $fields[$i] } else { '' }
        $props[$headers[$i]] = $value
      }
      [void]$rows.Add([pscustomobject]$props)
    }
    return $rows
  } finally {
    $parser.Close()
  }
}

function Get-TrimmedValue {
  param($Row, [string]$ColumnName)
  if ($null -eq $Row.PSObject.Properties[$ColumnName]) { return '' }
  return ([string]$Row.$ColumnName).Trim()
}

function Get-BracketContents {
  param([string]$Text)
  $contents = New-Object System.Collections.ArrayList
  if ([string]::IsNullOrWhiteSpace($Text)) { return @() }

  foreach ($match in [regex]::Matches($Text, '【([^】]+)】')) {
    $value = $match.Groups[1].Value.Trim()
    if ($value -and -not $contents.Contains($value)) { [void]$contents.Add($value) }
  }
  return $contents
}

function Normalize-Region {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text) -or $Text -eq '--' -or $Text -eq '未披露') { return '' }
  $t = $Text.Trim()
  $t = $t -replace '\s+', ''
  $t = $t -replace '-', '|'
  return $t
}

function Get-RegionPrefixes {
  param([string]$RegionText)
  $prefixes = New-Object System.Collections.ArrayList
  $region = Normalize-Region $RegionText
  if (-not $region) { return @() }

  $parts = $region.Split('|') | Where-Object { $_ -and $_ -ne '中国' }
  foreach ($part in $parts) {
    $p = $part.Trim()
    if (-not $p) { continue }
    $p = $p -replace '特别行政区', ''
    $p = $p -replace '自治州', ''
    $p = $p -replace '自治区', ''
    $p = $p -replace '[省市区县盟州旗]$', ''
    if ($p.Length -ge 2 -and -not $prefixes.Contains($p)) { [void]$prefixes.Add($p) }
  }
  return $prefixes
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

function Get-NameVariants {
  param(
    [string]$Text,
    [string]$RegionText = ''
  )

  $raw = New-Object System.Collections.ArrayList
  $norm = New-Object System.Collections.ArrayList
  if ([string]::IsNullOrWhiteSpace($Text)) {
    return [pscustomobject]@{ Raw = @(); Normalized = @() }
  }

  $baseTexts = New-Object System.Collections.ArrayList
  $trimmed = $Text.Trim()
  if ($trimmed -and -not $baseTexts.Contains($trimmed)) { [void]$baseTexts.Add($trimmed) }

  $withoutBrackets = ($trimmed -replace '【[^】]*】', '').Trim()
  if ($withoutBrackets -and -not $baseTexts.Contains($withoutBrackets)) { [void]$baseTexts.Add($withoutBrackets) }

  foreach ($content in Get-BracketContents $trimmed) {
    if ($content -and -not $baseTexts.Contains($content)) { [void]$baseTexts.Add($content) }
  }

  foreach ($baseText in @($baseTexts)) {
    if (-not $raw.Contains($baseText)) { [void]$raw.Add($baseText) }
    $normalized = Normalize-Name $baseText
    if ($normalized -and -not $norm.Contains($normalized)) { [void]$norm.Add($normalized) }
  }

  $prefixes = Get-RegionPrefixes $RegionText
  foreach ($normalized in @($norm)) {
    foreach ($prefix in $prefixes) {
      if ($normalized.StartsWith($prefix) -and $normalized.Length -gt ($prefix.Length + 1)) {
        $trimmedNorm = $normalized.Substring($prefix.Length)
        if ($trimmedNorm.Length -ge 3 -and -not $norm.Contains($trimmedNorm)) { [void]$norm.Add($trimmedNorm) }
      }
    }
  }

  return [pscustomobject]@{ Raw = $raw; Normalized = $norm }
}

function New-SourceRecord {
  param(
    [string]$SourceName,
    [int]$Priority,
    [string]$Level,
    [string]$Category,
    [string]$Region,
    [string[]]$RawAliases,
    [string[]]$NormalizedAliases
  )

  return [pscustomobject]@{
    SourceName = $SourceName
    Priority = $Priority
    Level = $Level
    Category = $Category
    Region = Normalize-Region $Region
    RawAliases = @($RawAliases | Where-Object { $_ } | Select-Object -Unique)
    NormalizedAliases = @($NormalizedAliases | Where-Object { $_ } | Select-Object -Unique)
    Richness = @($Level, $Category, (Normalize-Region $Region) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count
  }
}

function Add-SourceRows {
  param(
    [object[]]$Rows,
    [string]$SourceName,
    [int]$Priority,
    [string[]]$AliasColumns,
    [string]$LevelColumn,
    [string]$CategoryColumn,
    [string]$RegionColumn
  )

  $output = New-Object System.Collections.ArrayList
  foreach ($row in $Rows) {
    $level = if ($LevelColumn) { Get-TrimmedValue $row $LevelColumn } else { '' }
    $category = if ($CategoryColumn) { Get-TrimmedValue $row $CategoryColumn } else { '' }
    $region = if ($RegionColumn) { Get-TrimmedValue $row $RegionColumn } else { '' }

    $rawAliases = New-Object System.Collections.ArrayList
    $normalizedAliases = New-Object System.Collections.ArrayList
    foreach ($column in $AliasColumns) {
      $value = Get-TrimmedValue $row $column
      $variants = Get-NameVariants $value $region
      foreach ($alias in $variants.Raw) {
        if (-not $rawAliases.Contains($alias)) { [void]$rawAliases.Add($alias) }
      }
      foreach ($alias in $variants.Normalized) {
        if (-not $normalizedAliases.Contains($alias)) { [void]$normalizedAliases.Add($alias) }
      }
    }

    if ($rawAliases.Count -eq 0 -and $normalizedAliases.Count -eq 0) { continue }
    [void]$output.Add((New-SourceRecord $SourceName $Priority $level $category $region $rawAliases $normalizedAliases))
  }
  return $output
}

function Add-ToMap {
  param([hashtable]$Map, [string]$Key, $Value)
  if ([string]::IsNullOrWhiteSpace($Key)) { return }
  if (-not $Map.ContainsKey($Key)) { $Map[$Key] = New-Object System.Collections.ArrayList }
  [void]$Map[$Key].Add($Value)
}

function Get-EventVariants {
  param($Row)
  $raw = New-Object System.Collections.ArrayList
  $normalized = New-Object System.Collections.ArrayList
  $fields = @(
    Get-TrimmedValue $Row '基金名称',
    Get-TrimmedValue $Row '基金全称',
    Get-TrimmedValue $Row '投资方',
    Get-TrimmedValue $Row '投资方全称'
  ) | Where-Object { $_ }

  foreach ($field in $fields) {
    $variants = Get-NameVariants $field ''
    foreach ($alias in $variants.Raw) {
      if (-not $raw.Contains($alias)) { [void]$raw.Add($alias) }
    }
    foreach ($alias in $variants.Normalized) {
      if (-not $normalized.Contains($alias)) { [void]$normalized.Add($alias) }
    }
  }

  return [pscustomobject]@{ Raw = $raw; Normalized = $normalized }
}

function Add-CandidatesFromMap {
  param(
    [hashtable]$Map,
    [string[]]$Aliases,
    [string]$Method,
    [System.Collections.Generic.List[object]]$Collector
  )

  foreach ($alias in $Aliases) {
    if (-not $Map.ContainsKey($alias)) { continue }
    foreach ($record in $Map[$alias]) {
      $Collector.Add([pscustomobject]@{
        Record = $record
        MatchMethod = $Method
        MatchAlias = $alias
      })
    }
  }
}

function Select-BestCandidate {
  param($Candidates)
  if (-not $Candidates -or $Candidates.Count -eq 0) { return $null }
  return $Candidates |
    Sort-Object `
      @{ Expression = { if ($_.Record.Level) { 1 } else { 0 } }; Descending = $true }, `
      @{ Expression = { $_.Record.Richness }; Descending = $true }, `
      @{ Expression = { $_.Record.Priority }; Descending = $false }, `
      @{ Expression = { $_.MatchAlias.Length }; Descending = $true }, `
      @{ Expression = { $_.Record.SourceName }; Descending = $false } |
    Select-Object -First 1
}

function Merge-Field {
  param(
    $Candidates,
    [string]$PropertyName
  )
  $sorted = $Candidates |
    Sort-Object `
      @{ Expression = { if ($_.Record.Level) { 1 } else { 0 } }; Descending = $true }, `
      @{ Expression = { $_.Record.Richness }; Descending = $true }, `
      @{ Expression = { $_.Record.Priority }; Descending = $false }
  foreach ($candidate in $sorted) {
    $value = [string]$candidate.Record.$PropertyName
    if (-not [string]::IsNullOrWhiteSpace($value)) { return $value }
  }
  return ''
}

$projectRootResolved = Resolve-Path -LiteralPath $ProjectRoot
$catalogDir = Join-Path $projectRootResolved '政府引导基金清科目录（3）'
$eventDir = Join-Path $projectRootResolved '清科政府引导基金投资事件截止到2024年'

$sourceRecords = New-Object System.Collections.ArrayList
foreach ($item in (Add-SourceRows (Import-CsvWithHeaderRow (Join-Path $catalogDir '政府引导基金清科目录（1).csv')) '政府引导基金清科目录（1)' 1 @('基金简称','基金全称') '基金级别' '基金分类' '注册地区')) { [void]$sourceRecords.Add($item) }
foreach ($item in (Add-SourceRows (Import-CsvWithHeaderRow (Join-Path $catalogDir '政府引导基金清科目录（2).csv')) '政府引导基金清科目录（2)' 1 @('基金简称','基金全称') '基金级别' '基金分类' '注册地区')) { [void]$sourceRecords.Add($item) }
foreach ($item in (Add-SourceRows (Import-CsvWithHeaderRow (Join-Path $catalogDir '政府引导基金清科目录（3）.csv')) '政府引导基金清科目录（3）' 1 @('基金简称','基金全称') '基金级别' '基金分类' '注册地区')) { [void]$sourceRecords.Add($item) }
foreach ($item in (Add-SourceRows (Import-CsvWithHeaderRow (Join-Path $catalogDir '引导基金基金清科目录24-25（1）.csv')) '引导基金基金清科目录24-25（1）' 2 @('基金名称') '' '基金类型' '注册地区')) { [void]$sourceRecords.Add($item) }
foreach ($item in (Add-SourceRows (Import-CsvWithHeaderRow (Join-Path $catalogDir '引导基金基金清科目录24-25（2）.csv')) '引导基金基金清科目录24-25（2）' 2 @('基金名称') '' '基金类型' '注册地区')) { [void]$sourceRecords.Add($item) }
foreach ($item in (Add-SourceRows (Import-CsvWithHeaderRow (Join-Path $catalogDir '投中数据全部政府引导基金名录（上）.csv')) '投中数据全部政府引导基金名录（上）' 3 @('基金简称','基金全称') '' '基金类型' '所在地')) { [void]$sourceRecords.Add($item) }
foreach ($item in (Add-SourceRows (Import-CsvWithHeaderRow (Join-Path $catalogDir '投资数据全部政府引导基金目录（下）.csv')) '投资数据全部政府引导基金目录（下）' 3 @('基金简称','基金全称') '' '基金类型' '所在地')) { [void]$sourceRecords.Add($item) }

$rawMap = @{}
$normalizedMap = @{}
foreach ($record in $sourceRecords) {
  foreach ($alias in $record.RawAliases) { Add-ToMap $rawMap $alias $record }
  foreach ($alias in $record.NormalizedAliases) { Add-ToMap $normalizedMap $alias $record }
}

$eventFiles = @(
  '政府引导基金投资2015.csv','政府引导基金投资2016.csv','政府引导基金投资2017.csv','政府引导基金投资2018.csv','政府引导基金投资2019.csv',
  '政府引导基金投资2020.csv','政府引导基金投资2021.csv','政府引导基金投资2022.csv','政府引导基金投资2023.csv',
  '政府引导基金投资2024（1).csv','政府引导基金投资2024（2).csv','政府引导基金投资2024（3）.csv'
)

$investments = foreach ($fileName in $eventFiles) {
  $filePath = Join-Path $eventDir $fileName
  Import-Csv -LiteralPath $filePath | ForEach-Object {
    $_ | Add-Member -NotePropertyName 投资事件来源 -NotePropertyValue $fileName -PassThru
  }
}

$results = New-Object System.Collections.Generic.List[object]
$stats = [ordered]@{
  total_rows = 0
  matched_any = 0
  matched_level = 0
  matched_category = 0
  matched_region = 0
  raw_exact = 0
  normalized_exact = 0
}

foreach ($row in $investments) {
  $stats.total_rows++
  $variants = Get-EventVariants $row
  $candidates = New-Object System.Collections.Generic.List[object]
  Add-CandidatesFromMap $rawMap $variants.Raw '原始别名精确匹配' $candidates

  $best = Select-BestCandidate @($candidates)
  if ($null -eq $best) {
    Add-CandidatesFromMap $normalizedMap $variants.Normalized '标准化精确匹配' $candidates
    $best = Select-BestCandidate @($candidates)
  }

  $props = [ordered]@{}
  foreach ($property in $row.PSObject.Properties) { $props[$property.Name] = $property.Value }
  $props['基金级别'] = ''
  $props['基金分类'] = ''
  $props['注册地区_基金目录'] = ''
  $props['标注匹配方式'] = ''
  $props['标注来源表'] = ''
  $props['命中别名'] = ''

  if ($best) {
    $stats.matched_any++
    if ($best.Record.Level) { $stats.matched_level++ }
    if ($best.Record.Category) { $stats.matched_category++ }
    if ($best.Record.Region) { $stats.matched_region++ }
    if ($best.MatchMethod -eq '原始别名精确匹配') { $stats.raw_exact++ }
    if ($best.MatchMethod -eq '标准化精确匹配') { $stats.normalized_exact++ }

    $props['基金级别'] = Merge-Field @($candidates) 'Level'
    $props['基金分类'] = Merge-Field @($candidates) 'Category'
    $props['注册地区_基金目录'] = Merge-Field @($candidates) 'Region'
    $props['标注匹配方式'] = $best.MatchMethod
    $props['标注来源表'] = $best.Record.SourceName
    $props['命中别名'] = $best.MatchAlias
  }

  $results.Add([pscustomobject]$props)
}

$results | Export-Csv -LiteralPath $OutputFile -NoTypeInformation -Encoding UTF8
Write-Output ('output=' + $OutputFile)
$stats.GetEnumerator() | ForEach-Object { Write-Output ($_.Key + '=' + $_.Value) }
