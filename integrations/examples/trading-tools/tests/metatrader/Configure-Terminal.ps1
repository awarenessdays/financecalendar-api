# Configure only a disposable CI terminal through its visible settings UI.
# No broker credentials, account creation, trade permission or DLL permission.
param([Parameter(Mandatory=$true)][string]$Terminal,
      [Parameter(Mandatory=$true)][string]$Evidence,
      [Parameter(Mandatory=$true)][string]$Version,
      [int]$ExistingProcessId=0, [switch]$DismissOnly)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
if (-not ('FcTerminalUi' -as [type])) {
Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;
public class FcVisibleControl { public long Handle; public string Text; public string Class; }
public static class FcTerminalUi {
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hwnd, uint message, IntPtr wparam, IntPtr lparam);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hwnd,uint message,IntPtr wparam,IntPtr lparam);
  public delegate bool WindowProc(IntPtr window, IntPtr state);
  [DllImport("user32.dll")] public static extern bool EnumWindows(WindowProc callback,IntPtr state);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent,WindowProc callback,IntPtr state);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr window,out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr window);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr window,StringBuilder text,int count);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr window,StringBuilder text,int count);
  public static FcVisibleControl[] Controls(int wanted) {
    var found=new List<FcVisibleControl>();
    Action<IntPtr> add=(h)=>{if(!IsWindowVisible(h)) return;var text=new StringBuilder(512);var cls=new StringBuilder(128);GetWindowText(h,text,512);GetClassName(h,cls,128);found.Add(new FcVisibleControl{Handle=h.ToInt64(),Text=text.ToString(),Class=cls.ToString()});};
    EnumWindows((h,l)=>{uint pid;GetWindowThreadProcessId(h,out pid);if(pid==(uint)wanted){add(h);EnumChildWindows(h,(c,v)=>{add(c);return true;},IntPtr.Zero);}return true;},IntPtr.Zero);
    return found.ToArray();
  }
}
'@
}
$script:process = $null
function Get-AppElements {
  # Never walk Desktop descendants: unrelated UI providers can stall enumeration.
  $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ProcessIdProperty, [int]$script:process.Id)
  $roots = [System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,$condition)
  return @($(foreach ($root in $roots) {
    $root
    $root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  }) | Where-Object {-not $_.Current.IsOffscreen})
}
function Dump-VisibleUI($name) {
  try {
    $rows = if($Version -eq '4') { [FcTerminalUi]::Controls($script:process.Id) } else { foreach ($el in (Get-AppElements)) { [ordered]@{name=$el.Current.Name;type=$el.Current.ControlType.ProgrammaticName;class=$el.Current.ClassName;id=$el.Current.AutomationId} } }
    $rows | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Evidence "mt$Version-$name-ui.json")
    $screen=[System.Windows.Forms.SystemInformation]::VirtualScreen
    $bitmap=[System.Drawing.Bitmap]::new($screen.Width,$screen.Height)
    $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Left,$screen.Top,0,0,$bitmap.Size)
    $bitmap.Save((Join-Path $Evidence "mt$Version-$name.png"),[System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose();$bitmap.Dispose()
  } catch {Write-Host "UI diagnostics unavailable: $_"}
}
function Click-Button($element) {
  $null=[FcTerminalUi]::SendMessage([IntPtr]::new($element.Current.NativeWindowHandle),0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)
}
function Configure-Mt4VisibleControls {
  Write-Host 'MT4: inspecting visible HWND controls without UIAutomation providers.'
  foreach ($attempt in 1..3) {
    $controls=[FcTerminalUi]::Controls($script:process.Id)
    $auth=$controls | Where-Object {$_.Text -match '^Authorization allows|^Open an Account$'} | Select-Object -First 1
    if(-not $auth){break}
    $cancel=$controls | Where-Object {$_.Text -eq 'Cancel' -and $_.Class -eq 'Button'} | Select-Object -First 1
    if($cancel){$null=[FcTerminalUi]::SendMessage([IntPtr]::new($cancel.Handle),0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)}
    else{[System.Windows.Forms.SendKeys]::SendWait('{ESC}')}
    Start-Sleep -Milliseconds 500
  }
  [System.Windows.Forms.SendKeys]::SendWait('^o');Start-Sleep -Seconds 1
  $checkbox=$null
  foreach($tabIndex in 0..13){
    $controls=[FcTerminalUi]::Controls($script:process.Id)
    $checkbox=$controls | Where-Object {$_.Text -match '^Allow WebRequest' -and $_.Class -eq 'Button'} | Select-Object -First 1
    if($checkbox){break}
    [System.Windows.Forms.SendKeys]::SendWait('^{TAB}');Start-Sleep -Milliseconds 200
  }
  if(-not $checkbox){throw 'MT4 visible WebRequest checkbox was not found'}
  $handle=[IntPtr]::new($checkbox.Handle)
  if([FcTerminalUi]::SendMessage($handle,0x00F0,[IntPtr]::Zero,[IntPtr]::Zero).ToInt64() -ne 1){$null=[FcTerminalUi]::SendMessage($handle,0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)}
  $options=$controls | Where-Object {$_.Text -eq 'Options' -and $_.Class -eq '#32770'} | Select-Object -First 1
  if(-not $options){throw 'MT4 Options HWND was not found'}
  $null=[FcTerminalUi]::SendMessage([IntPtr]::new($options.Handle),0x0028,$handle,[IntPtr]::new(1))
  [System.Windows.Forms.SendKeys]::SendWait('{TAB}{END}{ENTER}');Start-Sleep -Milliseconds 300
  [System.Windows.Forms.SendKeys]::SendWait('https://www.financecalendar.com{ENTER}');Start-Sleep -Seconds 1
  Dump-VisibleUI 'webrequest-configured'
  $ok=[FcTerminalUi]::Controls($script:process.Id) | Where-Object {$_.Text -eq 'OK' -and $_.Class -eq 'Button'} | Select-Object -First 1
  if(-not $ok){throw 'MT4 Options OK button was not found'}
  $null=[FcTerminalUi]::SendMessage([IntPtr]::new($ok.Handle),0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)
  Start-Sleep -Seconds 2
  Write-Host 'MT4 visible allowlist entry submitted; HTTPS smoke decides acceptance.'
}
try {
  if($DismissOnly){
    $script:process=Get-Process -Id $ExistingProcessId -ErrorAction Stop
    $dismissed=@()
    foreach($attempt in 1..4){
      $controls=[FcTerminalUi]::Controls($script:process.Id)
      $prompt=$controls | Where-Object {$_.Text -match '^Authorization allows|^Open an Account$'} | Select-Object -First 1
      if(-not $prompt){break}
      $cancel=$controls | Where-Object {$_.Text -eq 'Cancel' -and $_.Class -eq 'Button'} | Select-Object -First 1
      if(-not $cancel){break}
      $posted=[FcTerminalUi]::PostMessage([IntPtr]::new($cancel.Handle),0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)
      $dismissed+=[ordered]@{prompt=$prompt.Text;cancel_posted=$posted}
      Start-Sleep -Milliseconds 500
    }
    $dismissed | ConvertTo-Json | Set-Content (Join-Path $Evidence "mt$Version-dismissed-startup-dialogs.json")
    return
  }
  $script:process=Start-Process $Terminal -ArgumentList '/portable' -PassThru
  Start-Sleep -Seconds 18
  $shell=New-Object -ComObject WScript.Shell
  $null=$shell.AppActivate($script:process.Id)
  if($Version -eq '4'){Configure-Mt4VisibleControls;return}
  foreach ($attempt in 1..3) {
    $elements=Get-AppElements
    $authorization=$elements | Where-Object {$_.Current.Name -match '^Authorization allows|^Open an Account$'} | Select-Object -First 1
    if (-not $authorization) {break}
    $cancel=$elements | Where-Object {$_.Current.Name -eq 'Cancel' -and $_.Current.ClassName -eq 'Button'} | Select-Object -First 1
    if ($cancel) {Click-Button $cancel} else {[System.Windows.Forms.SendKeys]::SendWait('{ESC}')}
    Start-Sleep -Milliseconds 500
  }
  [System.Windows.Forms.SendKeys]::SendWait('^o')
  Start-Sleep -Seconds 2
  $checkbox=$null
  foreach ($tabIndex in 0..13) {
    $elements=Get-AppElements
    $checkbox=$elements | Where-Object {$_.Current.Name -match '^Allow WebRequest' -and $_.Current.ClassName -eq 'Button'} | Select-Object -First 1
    if ($checkbox) {break}
    [System.Windows.Forms.SendKeys]::SendWait('^{TAB}')
    Start-Sleep -Milliseconds 300
  }
  if (-not $checkbox) {Dump-VisibleUI 'webrequest-missing';throw 'WebRequest checkbox was not found in terminal Options'}
  $handle=[IntPtr]::new($checkbox.Current.NativeWindowHandle)
  if ([FcTerminalUi]::SendMessage($handle,0x00F0,[IntPtr]::Zero,[IntPtr]::Zero).ToInt64() -ne 1) {Click-Button $checkbox}
  $options=$elements | Where-Object {$_.Current.Name -eq 'Options' -and $_.Current.ClassName -eq '#32770'} | Select-Object -First 1
  if (-not $options) {throw 'Visible Options dialog was not found'}
  $optionsRoot=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]::new($options.Current.NativeWindowHandle))
  $null=[FcTerminalUi]::SendMessage([IntPtr]::new($options.Current.NativeWindowHandle),0x0028,$handle,[IntPtr]::new(1))
  [System.Windows.Forms.SendKeys]::SendWait('{TAB}{END}{ENTER}')
  Start-Sleep -Milliseconds 300
  [System.Windows.Forms.SendKeys]::SendWait('https://www.financecalendar.com{ENTER}')
  Start-Sleep -Seconds 1
  Dump-VisibleUI 'webrequest-configured'
  $ok=$optionsRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition) | Where-Object {$_.Current.Name -eq 'OK' -and $_.Current.ClassName -eq 'Button'} | Select-Object -First 1
  if (-not $ok) {throw 'Settings OK button was not found'}
  Click-Button $ok
  Start-Sleep -Seconds 2
  Write-Host "MT${Version}: visible allowlist entry submitted; HTTPS smoke decides acceptance."
} catch {
  Dump-VisibleUI 'allowlist-failed'
  Write-Warning "MT${Version}: allowlist UI setup was not established: $_"
} finally {
  if (-not $DismissOnly -and $script:process -and -not $script:process.HasExited) {
    [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
    $null=$script:process.CloseMainWindow()
    try {$null=$script:process.WaitForExit(5000)} catch {}
    if (-not $script:process.HasExited) {Stop-Process -Id $script:process.Id -Force -ErrorAction SilentlyContinue}
  }
}
