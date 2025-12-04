# Configure Windows Firewall to allow outbound SMTP on port 587
# Run this script as Administrator

Write-Host "=" * 70
Write-Host "Configuring Windows Firewall for SMTP Port 587"
Write-Host "=" * 70
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To run as Administrator:"
    Write-Host "1. Right-click PowerShell"
    Write-Host "2. Select 'Run as Administrator'"
    Write-Host "3. Navigate to backend folder"
    Write-Host "4. Run: .\configure_firewall_port587.ps1"
    Write-Host ""
    exit 1
}

Write-Host "Checking for existing firewall rule..." -ForegroundColor Yellow

# Check if rule already exists
$existingRule = Get-NetFirewallRule -Name "SMTP_Port_587_Outbound" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "Firewall rule already exists. Removing old rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -Name "SMTP_Port_587_Outbound" -ErrorAction SilentlyContinue
}

Write-Host "Creating new firewall rule..." -ForegroundColor Yellow

try {
    # Create outbound rule for port 587
    New-NetFirewallRule `
        -DisplayName "SMTP Port 587 (Outbound)" `
        -Name "SMTP_Port_587_Outbound" `
        -Description "Allow outbound SMTP connections on port 587 for email sending" `
        -Direction Outbound `
        -Protocol TCP `
        -LocalPort 587 `
        -Action Allow `
        -Enabled True `
        -Profile Any `
        | Out-Null

    Write-Host "SUCCESS: Firewall rule created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Rule Details:"
    Write-Host "  Name: SMTP Port 587 (Outbound)"
    Write-Host "  Direction: Outbound"
    Write-Host "  Protocol: TCP"
    Write-Host "  Port: 587"
    Write-Host "  Action: Allow"
    Write-Host "  Status: Enabled"
    Write-Host ""
    Write-Host "=" * 70
    Write-Host "Firewall configuration complete!"
    Write-Host "=" * 70
    Write-Host ""
    Write-Host "You can now test SMTP connection with port 587."
    Write-Host "Update your .env file:"
    Write-Host "  SMTP_PORT=587"
    Write-Host "  SMTP_USE_TLS=True"
    Write-Host ""
    
} catch {
    Write-Host "ERROR: Failed to create firewall rule" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Configure manually through Windows Defender Firewall GUI"
    exit 1
}

