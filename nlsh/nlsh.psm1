# nlsh: type `ai <plain English>` and press Enter. The line is replaced (with a spinner while it thinks)
# by a PowerShell command you can review/edit; press Enter again to run it.
# Talks to a local Ollama server that keeps the model loaded in memory.

$script:Cfg = @{
    Host         = 'http://127.0.0.1:11434'
    Model        = 'nlsh'         # fine-tuned model; falls back to FewShotModel if missing
    FewShotModel = 'qwen3.5:2b'
    Trigger      = 'ai'           # prefix word that makes Enter translate instead of run
    TimeoutMs    = 15000
}
Add-Type -AssemblyName System.Net.Http
$script:Root = Split-Path -Parent $PSScriptRoot
$script:Last = $null              # @{ Query; Cmd } so repeating a query re-rolls it
$script:UseFewShot = $false
$script:Http = New-Object System.Net.Http.HttpClient
$script:Http.Timeout = [TimeSpan]::FromMilliseconds($script:Cfg.TimeoutMs)
$script:Frames = if ($env:WT_SESSION -or $env:TERM_PROGRAM) {
    [char[]]([string][char]0x280B + [char]0x2819 + [char]0x2839 + [char]0x2838 + [char]0x283C + [char]0x2834 + [char]0x2826 + [char]0x2827 + [char]0x2807 + [char]0x280F)
} else { [char[]]'|/-\' }

function script:Build-Messages([string]$Query) {
    $msgs = New-Object System.Collections.Generic.List[object]
    # [IO.File] (not Get-Content) so strings carry no PS note properties into ConvertTo-Json
    $msgs.Add(@{ role = 'system'; content = [IO.File]::ReadAllText((Join-Path $script:Root 'prompt\system.txt')) })
    foreach ($l in [IO.File]::ReadAllLines((Join-Path $script:Root 'prompt\fewshot.jsonl'))) {
        if (-not $l.Trim()) { continue }
        $s = $l | ConvertFrom-Json
        $msgs.Add(@{ role = 'user'; content = $s.q })
        $msgs.Add(@{ role = 'assistant'; content = $s.cmd })
    }
    $msgs.Add(@{ role = 'user'; content = $Query })
    , $msgs.ToArray()
}

# Starts the HTTP request and returns the Task, so callers can animate while it runs.
function script:Start-Request([string]$Query, [double]$Temperature) {
    $opts = @{ temperature = $Temperature; num_predict = 160; seed = (Get-Random) }
    if ($script:UseFewShot) {
        $url = "$($script:Cfg.Host)/api/chat"
        $body = @{ model = $script:Cfg.FewShotModel; stream = $false; think = $false; keep_alive = -1
                   messages = (Build-Messages $Query); options = $opts }
    } else {
        # fine-tuned model: its Modelfile holds the prompt template, send the raw query
        $url = "$($script:Cfg.Host)/api/generate"
        $body = @{ model = $script:Cfg.Model; stream = $false; keep_alive = -1; prompt = $Query; options = $opts }
    }
    $json = $body | ConvertTo-Json -Depth 6 -Compress
    $content = New-Object System.Net.Http.StringContent($json, [Text.Encoding]::UTF8, 'application/json')
    $script:Http.PostAsync($url, $content)
}

function script:Read-Response($Task) {
    $resp = $Task.GetAwaiter().GetResult()
    $text = $resp.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    if (-not $resp.IsSuccessStatusCode) {
        if ($text -match 'not found' -and -not $script:UseFewShot) { return $null }  # caller retries with fallback
        throw "ollama: $text"
    }
    $r = $text | ConvertFrom-Json
    $out = if ($script:UseFewShot) { $r.message.content } else { $r.response }
    # strip anything a model might wrap the command in
    $out = $out -replace '(?s)<think>.*?</think>', ''
    $out = $out.Trim() -replace '^```\w*\s*', '' -replace '\s*```$', ''
    $first = $out -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1
    if ($first) { $first.Trim() } else { '' }
}

# Runs one translation. $OnTick (optional) is called every ~80 ms with (frame, elapsedSeconds).
function script:Invoke-Model([string]$Query, [double]$Temperature = 0, [scriptblock]$OnTick) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $i = 0
    while ($true) {
        $task = Start-Request $Query $Temperature
        while (-not $task.Wait(80)) {
            if ($OnTick) { & $OnTick $script:Frames[$i++ % $script:Frames.Length] $sw.Elapsed.TotalSeconds }
        }
        $out = Read-Response $task
        if ($null -ne $out) { return $out }
        $script:UseFewShot = $true   # fine-tuned model not installed: retry with the few-shot fallback
    }
}

function script:Get-Query([string]$Line) {
    if ($Line -match "^\s*$([regex]::Escape($script:Cfg.Trigger))\s+(.+)$") { $Matches[1].Trim() }
}

# Enter handler: `ai <english>` gets translated in place; anything else is accepted as usual.
function script:Invoke-NlshEnter {
    $line = $null; $cursor = $null
    [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$cursor)
    $query = Get-Query $line
    if (-not $query) { [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine(); return }

    [Microsoft.PowerShell.PSConsoleReadLine]::AddToHistory($line)   # Up-arrow brings the English back
    # Asking the exact same thing twice in a row = "give me another option".
    $temp = if ($script:Last -and $script:Last.Query -eq $query) { 0.8 } else { 0.0 }

    # The spinner lives in the buffer itself; $ui.Shown tracks what's currently displayed.
    $ui = @{ Shown = $line; Line = $line }
    $tick = {
        param($frame, $secs)
        $next = '{0}   {1} thinking {2:0.0}s' -f $ui.Line, $frame, $secs
        [Microsoft.PowerShell.PSConsoleReadLine]::Replace(0, $ui.Shown.Length, $next)
        $ui.Shown = $next
    }.GetNewClosure()
    try {
        $cmd = Invoke-Model $query $temp $tick
    } catch {
        $cmd = $null
        $err = $_.Exception.InnerException, $_.Exception | Where-Object { $_ } | Select-Object -First 1
        $msg = if ($err.Message -match 'refused|actively') { 'Ollama is not running' } else { $err.Message }
        [Microsoft.PowerShell.PSConsoleReadLine]::Replace(0, $ui.Shown.Length, $line)
        [Microsoft.PowerShell.PSConsoleReadLine]::Ding()
        [Console]::Title = "ai: $msg"
        return
    }
    if (-not $cmd) {
        [Microsoft.PowerShell.PSConsoleReadLine]::Replace(0, $ui.Shown.Length, $line)
        [Microsoft.PowerShell.PSConsoleReadLine]::Ding(); return
    }
    $script:Last = @{ Query = $query; Cmd = $cmd }
    [Microsoft.PowerShell.PSConsoleReadLine]::Replace(0, $ui.Shown.Length, $cmd)
    [Microsoft.PowerShell.PSConsoleReadLine]::SetCursorPosition($cmd.Length)
}

function ai {
    <# Translate English into a PowerShell command and print it.
       At an interactive prompt you normally never reach this: Enter translates `ai ...` in place. #>
    param([Parameter(ValueFromRemainingArguments)][string[]]$Words)
    if (-not $Words) { Write-Host "usage: ai <what you want, in plain English>"; return }
    Invoke-Model ($Words -join ' ')
}

function Enable-Nlsh {
    param([string]$Trigger = 'ai')
    $script:Cfg.Trigger = $Trigger
    Set-PSReadLineKeyHandler -Key Enter -BriefDescription 'nlsh-enter' `
        -Description "Translate '$Trigger <english>' into a command; otherwise run the line" `
        -ScriptBlock { Invoke-NlshEnter }
    # Warm the model in the background so the first query is fast (no wait here).
    try {
        $c = New-Object System.Net.Http.StringContent("{`"model`":`"$($script:Cfg.Model)`",`"keep_alive`":-1}",
            [Text.Encoding]::UTF8, 'application/json')
        $null = $script:Http.PostAsync("$($script:Cfg.Host)/api/generate", $c)
    } catch { }
}

Export-ModuleMember -Function Enable-Nlsh, ai
