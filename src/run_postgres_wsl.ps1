$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
Push-Location (Split-Path -Parent $PSScriptRoot)
$name = "stat420-report-" + [guid]::NewGuid().ToString('N').Substring(0, 8)
$image = 'postgres@sha256:0d938e975177bef9f1f61f3f9dbcf2e0aa0a139568f66d3415ed8892eb97f6ac'
$env:PGPASSWORD = [guid]::NewGuid().ToString('N')
$env:POSTGRES_PASSWORD = $env:PGPASSWORD
$env:WSLENV = ($env:WSLENV + ':POSTGRES_PASSWORD').Trim(':')
$env:PGHOST = '127.0.0.1'
$env:PGPORT = '55420'
$env:PGUSER = 'stat420'
$env:PGDATABASE = 'stat420_energy'
$env:PGCONNECT_TIMEOUT = '3'
$started = $false
try {
    wsl -d Ubuntu -- docker run -d --name $name -e POSTGRES_PASSWORD -e POSTGRES_USER=stat420 -e POSTGRES_DB=stat420_energy -p 127.0.0.1:55420:5432 $image | Out-Null
    $started = $true
    # Keep a WSL client attached while Windows Python is working.
    $keepAlive = Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d','Ubuntu','--','docker','wait',$name) -WindowStyle Hidden -PassThru
    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        try {
            python -c 'import psycopg; psycopg.connect().close()' 2>$null
            $ready = $true
            break
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (!$ready) { throw 'The local PostgreSQL service did not become ready.' }

    python -m src.run_pipeline --db postgres
    wsl -d Ubuntu -- docker exec $name pg_dump -U stat420 -d stat420_energy -n stat420_energy --no-owner --no-privileges -Fc -f /tmp/stat420.dump
    wsl -d Ubuntu -- docker exec $name createdb -U stat420 stat420_restore_check
    wsl -d Ubuntu -- docker exec $name pg_restore --exit-on-error -U stat420 -d stat420_restore_check /tmp/stat420.dump
    $restored = [int](wsl -d Ubuntu -- docker exec $name psql -XAt -U stat420 -d stat420_restore_check -c 'SELECT COUNT(*) FROM stat420_energy.energy_observation')
    $record = Get-Content -Raw results/database_run.json | ConvertFrom-Json
    if ($restored -ne $record.tables.energy_observation) { throw 'Restored row count differs from the loaded table.' }
    $out = (Get-Location).Path + '\results\energy.postgres.dump'
    $linuxPath = (wsl -d Ubuntu -- wslpath -a ($out.Replace('\','/'))).Trim()
    wsl -d Ubuntu -- docker cp "${name}:/tmp/stat420.dump" $linuxPath
    [ordered]@{status='restored successfully'; table='stat420_energy.energy_observation'; rows=$restored} |
        ConvertTo-Json | Set-Content -Encoding utf8NoBOM results/postgres_restore_check.json
} finally {
    if ($started) { wsl -d Ubuntu -- docker rm -fv $name | Out-Null }
    if ($keepAlive) { $keepAlive.WaitForExit(5000) | Out-Null }
    Pop-Location
}
