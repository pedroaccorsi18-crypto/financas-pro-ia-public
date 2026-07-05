[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message"
}

function Write-Warn {
    param([string]$Message)
    Write-Warning $Message
}

function Find-Python {
    $candidates = @()
    if ($env:PYTHON) {
        $candidates += @{
            Command = $env:PYTHON
            Args = @()
            Label = "PYTHON"
        }
    }

    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $candidates += @{
            Command = $venvPython
            Args = @()
            Label = ".venv"
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $candidates += @{
            Command = $python.Source
            Args = @()
            Label = "python"
        }
    }

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3) {
        $candidates += @{
            Command = $python3.Source
            Args = @()
            Label = "python3"
        }
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        $candidates += @{
            Command = $py.Source
            Args = @("-3")
            Label = "py -3"
        }
    }

    foreach ($candidate in $candidates) {
        try {
            $versionArgs = @()
            $versionArgs += $candidate.Args
            $versionArgs += "--version"
            $versionOutput = & $candidate.Command @versionArgs 2>&1
            $versionText = ($versionOutput | Out-String).Trim()
            if (($LASTEXITCODE -eq 0) -and ($versionText -match "^Python \d+")) {
                $dependencyArgs = @()
                $dependencyArgs += $candidate.Args
                $dependencyArgs += @(
                    "-c",
                    "import pandas, streamlit, supabase, google.genai"
                )
                & $candidate.Command @dependencyArgs *> $null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host $versionText
                    return $candidate
                }
                Write-Warn "Python candidato sem dependencias do projeto: $($candidate.Label)"
                continue
            }
            Write-Warn "Python candidato falhou: $($candidate.Label)"
        } catch {
            Write-Warn "Python candidato indisponivel: $($candidate.Label)"
        }
    }

    throw "Python valido nao encontrado. Crie um ambiente virtual com 'python -m venv .venv' e instale 'python -m pip install -r requirements.txt', ou configure a variavel PYTHON para um runtime com as dependencias do projeto."
}

function Invoke-Python {
    param(
        [hashtable]$Python,
        [string[]]$Arguments
    )

    $allArgs = @()
    $allArgs += $Python.Args
    $allArgs += $Arguments
    & $Python.Command @allArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Comando Python falhou: $($Python.Label) $($Arguments -join ' ')"
    }
}

Write-Step "Validando estrutura basica"
$requiredPaths = @(
    "app.py",
    "requirements.txt",
    "README.md",
    "tests"
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path (Join-Path $repoRoot $path))) {
        throw "Arquivo ou pasta obrigatoria ausente: $path"
    }
}
Write-Ok "Arquivos principais encontrados"

$optionalPaths = @(
    ".env.example",
    ".streamlit\secrets.example.toml"
)

foreach ($path in $optionalPaths) {
    if (-not (Test-Path (Join-Path $repoRoot $path))) {
        Write-Warn "Arquivo de exemplo nao encontrado: $path"
    }
}

Write-Step "Localizando Python"
$pythonRuntime = Find-Python
Write-Ok "Runtime selecionado: $($pythonRuntime.Label)"

Write-Step "Checando sintaxe dos modulos"
Invoke-Python $pythonRuntime @(
    "-m",
    "compileall",
    "-q",
    "app.py",
    "auth.py",
    "app_config.py",
    "finance_categories.py",
    "finance_constants.py",
    "finance_core.py",
    "session_state.py",
    "repositories",
    "utils",
    "tests"
)
Write-Ok "Sintaxe valida"

if ($SkipTests) {
    Write-Warn "Testes pulados por opcao do usuario."
} else {
    Write-Step "Rodando testes unitarios e contratos locais"
    Invoke-Python $pythonRuntime @("-m", "unittest", "discover", "-s", "tests", "-v")
    Write-Ok "Testes locais passaram"
}

Write-Host ""
Write-Ok "Check concluido"
