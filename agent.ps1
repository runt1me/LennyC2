<# 
RunDiscordCommand_Embed.ps1
Requires:
  $env:DISCORD_BOT_TOKEN  - your bot token (no "Bot " prefix needed; we add it)
  $env:DISCORD_CHANNEL_ID - target channel ID
Usage:
  .\RunDiscordCommand_Embed.ps1 -Watch
#>

param(
    [switch]$Watch,
    [int]$PollSeconds = 5,
    [string]$Prefix = "!run"
)

# --- Config ---
$BaseUrl   = "https://discord.com/api/v10"
$BotToken  = $env:DISCORD_BOT_TOKEN
$ChannelId = $env:DISCORD_CHANNEL_ID

if (-not $BotToken -or -not $ChannelId) {
    Write-Error "Missing DISCORD_BOT_TOKEN or DISCORD_CHANNEL_ID environment variables."
    exit 1
}

$Headers = @{
    "Authorization" = "Bot $BotToken"
    "Content-Type"  = "application/json"
}

function Get-DiscordMessages {
    param([int]$Limit = 1, [string]$AfterId)
    $uri = "$BaseUrl/channels/$ChannelId/messages?limit=$Limit"
    if ($AfterId) { $uri += "&after=$AfterId" }
    try {
        Invoke-RestMethod -Uri $uri -Headers $Headers -Method GET -TimeoutSec 15
    } catch {
        Write-Error "GET messages failed: $($_.Exception.Message)"
        @()
    }
}

function Post-DiscordCommandResult {
    param([string]$Command, [string]$Output)

    # Discord embed field value limit is 1024 chars; keep things safe
    $maxField = 1000
    if ($Command.Length -gt $maxField) { $Command = $Command.Substring(0, $maxField) + " …(truncated)" }
    if ($Output.Length  -gt $maxField) { $Output  = $Output.Substring(0,  $maxField) + " …(truncated)" }

    $body = @{
        embeds = @(@{
            title  = "Command Result"
            color  = 5793266  # optional
            fields = @(
                @{ name = "command"; value = $Command; inline = $false },
                @{ name = "output";  value = $Output;  inline = $false }
            )
        })
    } | ConvertTo-Json -Depth 6

    try {
        Invoke-RestMethod -Uri "$BaseUrl/channels/$ChannelId/messages" -Headers $Headers -Method POST -Body $body -TimeoutSec 15 | Out-Null
    } catch {
        Write-Error "POST embed failed: $($_.Exception.Message)"
    }
}

function Run-CommandSmart {
    param([string]$CmdString)

    $parts = $CmdString -split '\s+', 2
    $name  = $parts[0]
    $args  = if ($parts.Count -gt 1) { $parts[1] } else { "" }

    $cmdInfo = Get-Command $name -ErrorAction SilentlyContinue
    try {
        if ($cmdInfo -and $cmdInfo.CommandType -match 'Cmdlet|Function|Alias') {
            if ($args) { (Invoke-Expression "$name $args") 2>&1 | Out-String }
            else       { (& $name)                          2>&1 | Out-String }
        }
        elseif ($cmdInfo -and $cmdInfo.CommandType -eq 'Application') {
            if ($args) { (& $name $args) 2>&1 | Out-String }
            else       { (& $name)       2>&1 | Out-String }
        }
        else {
            "Unknown command: $name"
        }
    } catch {
        "Error: $($_.Exception.Message)"
    }
}

function Handle-NewCommands {
    param([object[]]$Messages)
    if (-not $Messages) { return $null }

    # sort oldest->newest so replies follow order
    $ordered = $Messages | Sort-Object { [int64]$_."id" }
    $lastId = $null

    foreach ($m in $ordered) {
        $content = ($m.content | ToString).Trim()
        if ($content.StartsWith($Prefix)) {
            $cmd = $content.Substring($Prefix.Length).Trim()
            if ($cmd) {
                $result = Run-CommandSmart -CmdString $cmd
                Post-DiscordCommandResult -Command $cmd -Output $result
            } else {
                Post-DiscordCommandResult -Command "(none)" -Output "No command provided after prefix '$Prefix'."
            }
        }
        $lastId = $m.id
    }

    $lastId
}

# --- main ---
if ($Watch) {
    $lastSeen = $null
    $prime = Get-DiscordMessages -Limit 1
    if ($prime.Count -gt 0) { $lastSeen = $prime[0].id }

    Write-Host "Watching channel $ChannelId for '$Prefix'…"
    while ($true) {
        Start-Sleep -Seconds $PollSeconds
        $msgs = Get-DiscordMessages -Limit 10 -AfterId $lastSeen
        $lastSeen = Handle-NewCommands -Messages $msgs
    }
} else {
    # one-shot: check the latest single message only
    $msgs = Get-DiscordMessages -Limit 1
    [void](Handle-NewCommands -Messages $msgs)
}
