param([string]$Python = 'D:\python\python.exe', [int]$Port = 8766)
$ErrorActionPreference = 'Stop'
$atlasRoot = $PSScriptRoot
if (-not $atlasRoot.StartsWith('D:\', [System.StringComparison]::OrdinalIgnoreCase)) { throw '本项目按约定只允许从 D 盘运行。' }
$atlasRuntime = Join-Path $atlasRoot '.runtime\workbench'
New-Item -ItemType Directory -Force -Path $atlasRuntime | Out-Null
$env:TEMP = $atlasRuntime
$env:TMP = $atlasRuntime
$env:TMPDIR = $atlasRuntime
$env:PYTHONDONTWRITEBYTECODE = '1'
Write-Host "Research Atlas: http://127.0.0.1:$Port / Ctrl+C 停止"
& $Python -B (Join-Path $atlasRoot 'serve_atlas.py') --port $Port
