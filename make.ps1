param(
    [Parameter(Position=0)]
    [string]$Target = "build",
    [Parameter(Position=1)]
    [string]$Arg1,
    [Parameter(Position=2)]
    [string]$Arg2
)

function Show-Help {
    Write-Host "Data-Driven Modelling for Mechanical Systems - Quarto Portal" -ForegroundColor Cyan
    Write-Host "Usage: .\make.ps1 <target> [arguments]"
    Write-Host "Targets:"
    Write-Host "  build            - Generate pages and build static Quarto website for GitHub Pages"
    Write-Host "  preview          - Launch interactive live-reload Quarto preview server"
    Write-Host "  serve            - Serve built _site locally on http://127.0.0.1:8080"
    Write-Host "  test             - Run test suite and link validations"
}

switch ($Target.ToLower()) {
    "build" {
        python scripts/generate_pages.py
        quarto render
    }
    "preview" {
        quarto preview
    }
    "serve" {
        python -m http.server 8080 --directory docs
    }
    "test" {
        python tests/run_tests.py
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown target: $Target" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
