# Install Superpowers (https://github.com/obra/superpowers) globally for:
# - Codex (~/.agents/skills)
# - Cursor (~/.cursor/skills)
# - Claude Code (~/.claude/skills)
# Run in PowerShell as current user (no admin required).

$ErrorActionPreference = "Stop"
$repo = "https://github.com/obra/superpowers.git"
$cloneRoot = Join-Path $env:USERPROFILE ".codex"
$clonePath = Join-Path $cloneRoot "superpowers"
$skillsSource = Join-Path $clonePath "skills"

Write-Host "=== Superpowers 全局安装 ===" -ForegroundColor Cyan

# 1. Clone or update repo
if (Test-Path $clonePath) {
    Write-Host "仓库已存在，正在拉取更新..." -ForegroundColor Yellow
    Push-Location $clonePath
    git pull
    Pop-Location
} else {
    New-Item -ItemType Directory -Force -Path $cloneRoot | Out-Null
    Write-Host "正在克隆 $repo ..." -ForegroundColor Yellow
    git clone $repo $clonePath
}

if (-not (Test-Path $skillsSource)) {
    Write-Error "克隆后未找到 skills 目录: $skillsSource"
}

# 2. Codex: ~/.agents/skills/superpowers -> clone/skills
$agentsSkills = Join-Path $env:USERPROFILE ".agents\skills"
$codexLink = Join-Path $agentsSkills "superpowers"
New-Item -ItemType Directory -Force -Path $agentsSkills | Out-Null
if (Test-Path $codexLink) {
    Write-Host "Codex 链接已存在: $codexLink" -ForegroundColor Gray
} else {
    cmd /c mklink /J "$codexLink" "$skillsSource"
    Write-Host "已创建 Codex 技能链接: $codexLink" -ForegroundColor Green
}

# 3. Cursor: ~/.cursor/skills/superpowers -> clone/skills
$cursorSkills = Join-Path $env:USERPROFILE ".cursor\skills"
$cursorLink = Join-Path $cursorSkills "superpowers"
New-Item -ItemType Directory -Force -Path $cursorSkills | Out-Null
if (Test-Path $cursorLink) {
    Write-Host "Cursor 链接已存在: $cursorLink" -ForegroundColor Gray
} else {
    cmd /c mklink /J "$cursorLink" "$skillsSource"
    Write-Host "已创建 Cursor 技能链接: $cursorLink" -ForegroundColor Green
}

# 4. Claude: ~/.claude/skills/superpowers -> clone/skills
$claudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
$claudeLink = Join-Path $claudeSkills "superpowers"
New-Item -ItemType Directory -Force -Path $claudeSkills | Out-Null
if (Test-Path $claudeLink) {
    Write-Host "Claude 链接已存在: $claudeLink" -ForegroundColor Gray
} else {
    cmd /c mklink /J "$claudeLink" "$skillsSource"
    Write-Host "已创建 Claude Code 技能链接: $claudeLink" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "Repo: $clonePath"
$updateMsg = "To update: cd " + $clonePath + " ; git pull"
Write-Host $updateMsg
Write-Host ""
