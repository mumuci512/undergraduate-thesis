param([string]$Source = 'proposal.tex')
$ErrorActionPreference = 'Stop'
$proposalRepo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$proposalTexInputs = $env:TEXINPUTS
Push-Location -LiteralPath $proposalRepo
try {
  $proposalEngine = Get-Command xelatex -ErrorAction Stop
  $env:TEXINPUTS = './style//;./chapters//;./figures//;' + $proposalTexInputs
  for ($proposalPass = 1; $proposalPass -le 2; $proposalPass++) {
    & $proposalEngine.Source '-no-shell-escape' '-interaction=nonstopmode' '-halt-on-error' $Source
    if ($LASTEXITCODE -ne 0) { throw ('XeLaTeX failed on pass ' + $proposalPass) }
  }
} finally {
  $env:TEXINPUTS = $proposalTexInputs
  Pop-Location
}
