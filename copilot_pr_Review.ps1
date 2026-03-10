param(
    [string]$DiffFile = "pr.diff"
)

Write-Host "Starting AI PR Review..."

if (!(Test-Path $DiffFile)) {
    Write-Host "Diff file not found: $DiffFile"
    exit 1
}

$tempDir = "temp_review_files"

if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}

New-Item -ItemType Directory -Path $tempDir | Out-Null

$diffContent = Get-Content $DiffFile -Raw

# Split diff by file
$files = $diffContent -split "diff --git"

$fileCounter = 0
$results = @()

foreach ($file in $files) {

    if ($file.Trim().Length -lt 50) { continue }

    $fileCounter++

    $fileName = "file_$fileCounter.diff"
    $tempFile = Join-Path $tempDir $fileName

    $file | Out-File $tempFile -Encoding utf8

    Write-Host "Reviewing $fileName ..."

    $prompt = "You are a senior code reviewer. Review this git diff and list only serious issues like logic bugs, security risks, null pointer issues, performance problems, or missing error handling. Ignore formatting issues."

    $review = cmd /c "copilot -p `"$prompt`" < $tempFile"

    $results += "### Review for $fileName"
    $results += $review
    $results += "`n--------------------------------`n"
}

$finalReport = "ai_review_report.md"

Write-Host "Generating final report..."

$header = @"
# AI Code Review Report

Generated using GitHub Copilot CLI

Total Files Reviewed: $fileCounter

--------------------------------

"@

$header | Out-File $finalReport -Encoding utf8

$results | Out-File $finalReport -Append -Encoding utf8

Write-Host "Review completed."

Write-Host "Report saved as: $finalReport"

# Cleanup
Remove-Item $tempDir -Recurse -Force

Write-Host "Temporary files deleted."
