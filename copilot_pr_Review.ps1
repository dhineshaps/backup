param(
    [string]$PR_ID
)

Write-Host "Fetching PR diff..."

# Call Python to fetch diff
python get_pr_diff.py $PR_ID

$diffFile = "pr.diff"

if (!(Test-Path $diffFile)) {
    Write-Host "Diff file not found"
    exit 1
}

Write-Host "Splitting diff by files..."

$tempDir = "temp_review_files"

if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}

New-Item -ItemType Directory -Path $tempDir | Out-Null

$diffContent = Get-Content $diffFile -Raw

# Split diff per file
$files = $diffContent -split "diff --git"

$fileCounter = 0
$results = @()

foreach ($file in $files) {

    if ($file.Trim().Length -lt 50) { continue }

    $fileCounter++

    $filePath = "$tempDir\file_$fileCounter.diff"

    $file | Out-File $filePath -Encoding utf8

    Write-Host "Reviewing file $fileCounter..."

    $prompt = "You are a senior code reviewer. Review this git diff and report only serious issues like logic bugs, security issues, null pointer risks, missing error handling, or performance problems."

    $review = cmd /c "copilot -p `"$prompt`" < $filePath"

    $results += "### Review for file_$fileCounter"
    $results += $review
    $results += "`n--------------------------------`n"
}

$reportFile = "ai_review_report.md"

Write-Host "Generating review report..."

$header = @"
# AI Code Review Report

Pull Request: $PR_ID

Total Files Reviewed: $fileCounter

--------------------------------

"@

$header | Out-File $reportFile -Encoding utf8
$results | Out-File $reportFile -Append -Encoding utf8

Write-Host "Review completed."

Write-Host "Report saved as $reportFile"

# Cleanup
Remove-Item $tempDir -Recurse -Force

Write-Host "Temporary files deleted."
