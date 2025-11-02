Param(
  [string]$ProjectUrl = $env:SUPABASE_URL,
  [string]$ServiceRole = $env:SUPABASE_SERVICE_ROLE_KEY,
  [string]$Ollama = "http://localhost:11434",
  [string]$Model = "nomic-embed-text",
  [int]$Port = 3005
)

Write-Host "== Web Memory Local Demo ==" -ForegroundColor Cyan

if (-not $ProjectUrl -or -not $ServiceRole) {
  Write-Host "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or pass -ProjectUrl/-ServiceRole" -ForegroundColor Yellow
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $root "..")

# 1) Generate visits.json
Push-Location $repo
node tools/mock_extension_export.js visits.json

# 2) Ingest
$env:SUPABASE_URL = $ProjectUrl
$env:SUPABASE_SERVICE_ROLE_KEY = $ServiceRole
$env:OLLAMA_BASE_URL = $Ollama
$env:OLLAMA_EMBED_MODEL = $Model
node tools/ingest_visits_to_supabase.mjs visits.json

# 3) Start frontend
Push-Location "$repo\frontend"
if (-not (Test-Path ".env.local")) {
  @"
NEXT_PUBLIC_SUPABASE_URL=$ProjectUrl
NEXT_PUBLIC_SUPABASE_ANON_KEY=
OLLAMA_BASE_URL=$Ollama
OLLAMA_EMBED_MODEL=$Model
"@ | Out-File -Encoding UTF8 .env.local
  Write-Host "Created .env.local (fill your anon key)." -ForegroundColor Yellow
}

npm ci --no-audit --no-fund
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run","dev","--","-p",$Port
Write-Host "Frontend starting at http://127.0.0.1:$Port" -ForegroundColor Green
Pop-Location
