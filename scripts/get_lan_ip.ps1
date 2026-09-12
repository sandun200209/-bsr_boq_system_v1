$adapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -notlike '127.*' -and 
    $_.IPAddress -notlike '169.254.*' -and 
    $_.InterfaceAlias -notlike '*Loopback*' -and 
    $_.InterfaceAlias -notlike '*vEthernet*' 
}

if ($adapters) {
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host "  OFFICE NETWORK / WI-FI URLS FOR OTHER PCS AND LAPTOPS:" -ForegroundColor Green
    Write-Host "=====================================================================" -ForegroundColor Cyan
    foreach ($adapter in $adapters) {
        $ip = $adapter.IPAddress
        $alias = $adapter.InterfaceAlias
        Write-Host "   -> http://${ip}:8080   ($alias)" -ForegroundColor Yellow
    }
    Write-Host "=====================================================================" -ForegroundColor Cyan
} else {
    Write-Host "[WARNING] No active local network connection detected." -ForegroundColor Yellow
}
