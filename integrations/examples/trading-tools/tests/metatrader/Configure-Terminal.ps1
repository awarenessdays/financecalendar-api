# Configure only the disposable CI terminal, through its visible settings UI.
# No broker account, API key, DLL permission or trade permission is introduced.
param([Parameter(Mandatory=$true)][string]$Terminal,
      [Parameter(Mandatory=$true)][string]$Evidence,
      [Parameter(Mandatory=$true)][string]$Version)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$script:process = $null
function Dump-VisibleUI($root, $name) {
  try {
    $rows = foreach ($el in $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)) {
      if (-not $el.Current.IsOffscreen) { [ordered]@{name=$el.Current.Name; type=$el.Current.ControlType.ProgrammaticName; class=$el.Current.ClassName; id=$el.Current.AutomationId} }
    }
    $rows | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Evidence "mt$Version-$name-ui.json")
    $screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bitmap = [System.Drawing.Bitmap]::new($screen.Width, $screen.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Left,$screen.Top,0,0,$bitmap.Size)
    $bitmap.Save((Join-Path $Evidence "mt$Version-$name.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose(); $bitmap.Dispose()
  } catch { Write-Host "UI diagnostics unavailable: $_" }
}
function Get-VisibleElements($root) {
  return @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition) | Where-Object { -not $_.Current.IsOffscreen })
}
try {
  $script:process = Start-Process $Terminal -ArgumentList '/portable' -PassThru
  Start-Sleep -Seconds 18
  $shell = New-Object -ComObject WScript.Shell
  $null = $shell.AppActivate($script:process.Id)
  # Dismiss an optional first-start account-selection dialog; never create an account.
  [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
  Start-Sleep -Seconds 1
  [System.Windows.Forms.SendKeys]::SendWait('^o')
  Start-Sleep -Seconds 2
  $desktop = [System.Windows.Automation.AutomationElement]::RootElement
  $elements = Get-VisibleElements $desktop
  $tab = $elements | Where-Object { $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem -and $_.Current.Name -match 'Expert Advisors' } | Select-Object -First 1
  if (-not $tab) { Dump-VisibleUI $desktop 'options-missing'; throw 'Expert Advisors settings tab was not found' }
  $selection = $tab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
  $selection.Select()
  Start-Sleep -Seconds 1
  $elements = Get-VisibleElements $desktop
  $checkbox = $elements | Where-Object { $_.Current.Name -match '^Allow WebRequest' -and $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::CheckBox } | Select-Object -First 1
  if (-not $checkbox) { Dump-VisibleUI $desktop 'webrequest-missing'; throw 'WebRequest checkbox was not found' }
  $toggle = $checkbox.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
  if ($toggle.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::On) { $toggle.Toggle() }
  $checkbox.SetFocus()
  [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
  [System.Windows.Forms.SendKeys]::SendWait('{END}{ENTER}')
  Start-Sleep -Milliseconds 300
  [System.Windows.Forms.SendKeys]::SendWait('https://www.financecalendar.com')
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  Start-Sleep -Seconds 1
  $elements = Get-VisibleElements $desktop
  $url = $elements | Where-Object { $_.Current.Name -eq 'https://www.financecalendar.com' } | Select-Object -First 1
  Dump-VisibleUI $desktop 'webrequest-configured'
  if (-not $url) { throw 'The allowed URL could not be verified in the visible settings list' }
  $ok = $elements | Where-Object { $_.Current.Name -eq 'OK' -and $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button } | Select-Object -First 1
  if (-not $ok) { throw 'Settings OK button was not found' }
  $invoke = $ok.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern); $invoke.Invoke()
  Start-Sleep -Seconds 2
  Write-Host "MT${Version}: WebRequest allowlist was configured through the visible terminal settings."
} catch {
  Dump-VisibleUI ([System.Windows.Automation.AutomationElement]::RootElement) 'allowlist-failed'
  Write-Warning "MT${Version}: allowlist UI setup was not established: $_"
} finally {
  if ($script:process -and -not $script:process.HasExited) {
    $null = $script:process.CloseMainWindow()
    try { $null = $script:process.WaitForExit(10000) } catch {}
    if (-not $script:process.HasExited) { Stop-Process -Id $script:process.Id -Force -ErrorAction SilentlyContinue }
  }
}
