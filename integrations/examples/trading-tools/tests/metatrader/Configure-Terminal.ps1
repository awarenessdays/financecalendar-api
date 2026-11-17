# Configure only the disposable CI terminal, through its visible settings UI.
# No broker account, API key, DLL permission or trade permission is introduced.
param([Parameter(Mandatory=$true)][string]$Terminal,
      [Parameter(Mandatory=$true)][string]$Evidence,
      [Parameter(Mandatory=$true)][string]$Version)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
if (-not ('FcTerminalUi' -as [type])) {
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class FcTerminalUi {
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hwnd, uint message, IntPtr wparam, IntPtr lparam);
}
'@
}
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
  # Legacy MetaTrader controls expose their names/HWNDs but are UIA Panes,
  # not TabItem/CheckBox patterns. Cycle visible tabs until the actual label appears.
  $checkbox = $null
  foreach ($tabIndex in 0..13) {
    $elements = Get-VisibleElements $desktop
    $checkbox = $elements | Where-Object { $_.Current.Name -match '^Allow WebRequest' -and $_.Current.ClassName -eq 'Button' } | Select-Object -First 1
    if ($checkbox) { break }
    [System.Windows.Forms.SendKeys]::SendWait('^{TAB}')
    Start-Sleep -Milliseconds 300
  }
  if (-not $checkbox) { Dump-VisibleUI $desktop 'webrequest-missing'; throw 'WebRequest checkbox was not found on any settings tab' }
  $handle = [IntPtr]::new($checkbox.Current.NativeWindowHandle)
  $checked = [FcTerminalUi]::SendMessage($handle, 0x00F0, [IntPtr]::Zero, [IntPtr]::Zero).ToInt64()
  if ($checked -ne 1) { $null = [FcTerminalUi]::SendMessage($handle, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero) }
  $options = $elements | Where-Object { $_.Current.Name -eq 'Options' -and $_.Current.ClassName -eq '#32770' } | Select-Object -First 1
  if (-not $options) { throw 'Visible Options dialog was not found' }
  # WM_NEXTDLGCTL focuses this real visible checkbox before tabbing to its URL list.
  $null = [FcTerminalUi]::SendMessage([IntPtr]::new($options.Current.NativeWindowHandle), 0x0028, $handle, [IntPtr]::new(1))
  [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
  [System.Windows.Forms.SendKeys]::SendWait('{END}{ENTER}')
  Start-Sleep -Milliseconds 300
  [System.Windows.Forms.SendKeys]::SendWait('https://www.financecalendar.com')
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  Start-Sleep -Seconds 1
  $elements = Get-VisibleElements $desktop
  $url = $elements | Where-Object { $_.Current.Name -eq 'https://www.financecalendar.com' } | Select-Object -First 1
  Dump-VisibleUI $desktop 'webrequest-configured'
  if (-not $url) { Write-Host 'Legacy URL list does not expose row text to UIA; real HTTPS smoke must verify the entry.' }
  $ok = $elements | Where-Object { $_.Current.Name -eq 'OK' -and $_.Current.ClassName -eq 'Button' } | Select-Object -First 1
  if (-not $ok) { throw 'Settings OK button was not found' }
  $null = [FcTerminalUi]::SendMessage([IntPtr]::new($ok.Current.NativeWindowHandle), 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero)
  Start-Sleep -Seconds 2
  Write-Host "MT${Version}: WebRequest allowlist entry was submitted through visible terminal settings; HTTPS smoke decides acceptance."
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
