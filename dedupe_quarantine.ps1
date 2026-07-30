# dedupe_quarantine.ps1
param(
  [string[]]$Roots = @("C:\","D:\","C:\Users\%USERNAME%\OneDrive","C:\semptify_inbox"),
  [string]$Quarantine = "C:\semptify_quarantine",
  [string]$LogCsv = "C:\semptify_quarantine\dedupe_log.csv"
)

$Roots = $Roots | ForEach-Object { $_ -replace "%USERNAME%", $env:USERNAME }
New-Item -ItemType Directory -Path $Quarantine -Force | Out-Null
$hashTable = @{}

$log = @()
foreach ($root in $Roots) {
  Write-Output "Scanning $root ..."
  Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    try {
      $path = $_.FullName
      $h = Get-FileHash -Algorithm SHA256 -Path $path
      $hash = $h.Hash
      if (-not $hashTable.ContainsKey($hash)) {
        $hashTable[$hash] = @($path)
      } else {
        $hashTable[$hash] += $path
      }
    } catch {
      Write-Warning "Skipped: $($_.FullName) - $_"
    }
  }
}

# Move duplicates (keep first seen)
foreach ($entry in $hashTable.GetEnumerator()) {
  $files = $entry.Value
  if ($files.Count -gt 1) {
    $keep = $files[0]
    for ($i=1; $i -lt $files.Count; $i++) {
      $f = $files[$i]
      $dest = Join-Path $Quarantine ([IO.Path]::GetFileName($f))
      $counter = 1
      while (Test-Path $dest) {
        $stem = [IO.Path]::GetFileNameWithoutExtension($f)
        $ext = [IO.Path]::GetExtension($f)
        $dest = Join-Path $Quarantine "$stem`_$counter$ext"
        $counter++
      }
      try {
        Move-Item -Path $f -Destination $dest -Force
        $log += [PSCustomObject]@{Hash=$entry.Key;Kept=$keep;Moved=$f;MovedTo=$dest;Time=(Get-Date)}
        Write-Output "Moved duplicate: $f -> $dest"
      } catch {
        Write-Warning "Failed to move $f : $_"
      }
    }
  }
}

# Save CSV log
$log | Export-Csv -Path $LogCsv -NoTypeInformation -Force
Write-Output "Deduplication complete. Quarantine: $Quarantine. Log: $LogCsv"
