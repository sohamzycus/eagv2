# capture_logs.ps1
param([string]$Server = 'http://127.0.0.1:5000', [string]$Question = 'What are you doing? Learning that prompting really is the key!')
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = "llm_stdout_$timestamp.txt"
python agent.py --server $Server --question "$Question" *> $out
Write-Host "Captured logs to $out"
