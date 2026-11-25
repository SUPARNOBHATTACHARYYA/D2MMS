# tests/test_live_server.ps1
param()

$caddy = "C:\Users\iamjo\AppData\Local\Microsoft\WinGet\Packages\CaddyServer.Caddy_Microsoft.Winget.Source_8wekyb3d8bbwe\caddy.exe"
if (-not (Test-Path $caddy)) {
    $caddy = (Get-Command caddy).Source
}

$testUser = "student"
$testPass = "classpass2026"
$hash = (& $caddy hash-password --plaintext $testPass).Trim()

$env:CLASS_USERNAME = $testUser
$env:CLASS_PASSWORD_HASH = $hash

Write-Host "=== Starting Caddy Local Verification Server on 127.0.0.1:8080 ==="
$process = Start-Process -FilePath $caddy -ArgumentList "run", "--config", "Caddyfile" -PassThru -NoNewWindow
Start-Sleep -Seconds 3

try {
    # 1. Test Unauthenticated Access (Must be 401)
    Write-Host "`n1. Testing Unauthenticated Access to /..."
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8080/" -Method Get -TimeoutSec 5 -UseBasicParsing
        Write-Host "FAILED: Expected 401 Unauthorized but got $($resp.StatusCode)"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 401) {
            Write-Host "✓ PASS: Unauthenticated access blocked with HTTP 401 Unauthorized"
        } else {
            Write-Host "FAILED: Unexpected error: $_"
        }
    }

    # 2. Test Authenticated Access with Credentials (Must be 200)
    Write-Host "`n2. Testing Authenticated Access to /..."
    $pair = "${testUser}:${testPass}"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
    $headers = @{ "Authorization" = "Basic $encoded" }

    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8080/" -Headers $headers -TimeoutSec 5 -UseBasicParsing
    if ($resp.StatusCode -eq 200) {
        Write-Host "✓ PASS: Authenticated access succeeded with HTTP 200 OK"
    } else {
        Write-Host "FAILED: Got status code $($resp.StatusCode)"
    }

    # 3. Test Lecture 01 Workspace Page
    Write-Host "`n3. Testing Lecture 01 Workspace Page..."
    $lecResp = Invoke-WebRequest -Uri "http://127.0.0.1:8080/lectures/01-intro-example/index.html" -Headers $headers -TimeoutSec 5 -UseBasicParsing
    if ($lecResp.StatusCode -eq 200) {
        Write-Host "✓ PASS: Lecture 01 workspace loaded with HTTP 200 OK"
    }

    # 4. Test Beamer Slides PDF & Inline Disposition
    Write-Host "`n4. Testing Beamer Slides PDF headers..."
    $pdfResp = Invoke-WebRequest -Uri "http://127.0.0.1:8080/lectures/01-intro-example/slides.pdf" -Headers $headers -TimeoutSec 5 -UseBasicParsing
    Write-Host "   HTTP Status: $($pdfResp.StatusCode)"
    Write-Host "   Content-Disposition: $($pdfResp.Headers['Content-Disposition'])"
    Write-Host "   Content-Length: $($pdfResp.RawContentLength) bytes"
    if ($pdfResp.Headers['Content-Disposition'] -like "*inline*") {
        Write-Host "✓ PASS: Slides PDF served with Content-Disposition: inline"
    }

    # 5. Test JupyterLite Single Notebook URL
    Write-Host "`n5. Testing JupyterLite Single Notebook Endpoint..."
    $liteResp = Invoke-WebRequest -Uri "http://127.0.0.1:8080/lite/notebooks/index.html?path=01-intro-example%2Fnotebook.ipynb" -Headers $headers -TimeoutSec 5 -UseBasicParsing
    if ($liteResp.StatusCode -eq 200) {
        Write-Host "✓ PASS: JupyterLite single-notebook endpoint returned HTTP 200 OK"
    }

    # 6. Verify Local Transferred Size for Lecture 01 (< 2 MB)
    Write-Host "`n6. Calculating Total Local File Transfer Size for Lecture 01..."
    $htmlSize = (Get-Item "_site/lectures/01-intro-example/index.html").Length
    $pdfSize = (Get-Item "_site/lectures/01-intro-example/slides.pdf").Length
    $nbSize = (Get-Item "_site/lectures/01-intro-example/notebook.ipynb").Length
    $cssSize = (Get-Item "_site/assets/styles.css").Length
    $jsSize = (Get-Item "_site/assets/workspace.js").Length
    $totalBytes = $htmlSize + $pdfSize + $nbSize + $cssSize + $jsSize
    $totalKB = [math]::Round($totalBytes / 1024, 2)
    Write-Host "   HTML: $htmlSize B | PDF: $pdfSize B | Notebook: $nbSize B | CSS: $cssSize B | JS: $jsSize B"
    Write-Host "   Total: $totalKB KB"
    if ($totalBytes -lt 2097152) {
        Write-Host "✓ PASS: Total local transfer ($totalKB KB) is well under the 2 MB limit!"
    }
} finally {
    Write-Host "`nStopping Caddy process..."
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Caddy stopped."
}
