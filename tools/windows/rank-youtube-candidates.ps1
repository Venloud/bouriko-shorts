# Topic-independent metadata ranking. Dot-source; no network or file side effects.
function Get-YoutubeField($Object, [string]$Name, $Default = '') {
    $property = $Object.PSObject.Properties[$Name]
    if ($null -ne $property -and $null -ne $property.Value) { return $property.Value }
    return $Default
}
function ConvertTo-YoutubeWords([string]$Text) {
    return (($Text.ToLowerInvariant() -replace '[^\p{L}\p{Nd}]+', ' ').Trim() -replace '\s+', ' ')
}
function Get-RankedYoutubeCandidates {
    param([string]$Query, [object[]]$Candidates, [string]$ExpectedChannel = '')
    $q = ConvertTo-YoutubeWords $Query
    $official = $q -match '\b(official|presentation|keynote|launch|unveiling|unveil)\b'
    $full = $q -match '\b(full|entire|complete|keynote)\b'
    $short = $q -match '\b(short|trailer|teaser|ad|commercial)\b'
    $review = $q -match '\b(review|reaction|recap|opinion|analysis)\b'
    $stop = @('the','a','an','of','for','and','to','on','in','new','latest','official','presentation','keynote','launch','video','full','entire','complete','introducing','introduction','review','reaction','recap','trailer','teaser','ad','commercial')
    $tokens = @($q.Split(' ') | Where-Object { $_ -and $_ -notin $stop } | Select-Object -Unique)
    foreach ($video in $Candidates) {
        $id = [string](Get-YoutubeField $video 'id')
        if ($id -notmatch '^[A-Za-z0-9_-]{11}$') { continue }
        $title = [string](Get-YoutubeField $video 'title')
        $words = ConvertTo-YoutubeWords $title
        $channel = [string](Get-YoutubeField $video 'channel' (Get-YoutubeField $video 'uploader'))
        $cw = ConvertTo-YoutubeWords $channel
        $dur = [double](Get-YoutubeField $video 'duration' 0)
        $hits = @($tokens | Where-Object { (' '+$words+' ').Contains(' '+$_+' ') }).Count
        $coverage = if ($tokens.Count) { $hits / $tokens.Count } else { 0 }
        $score = 20 * $coverage
        $why = @("subject coverage $hits/$($tokens.Count)")
        # Publisher inference is conservative: an exact query prefix, not a substring.
        # Explicit channel takes precedence. Neither display-name match proves identity.
        $publisher = if ($ExpectedChannel) { $cw -eq (ConvertTo-YoutubeWords $ExpectedChannel) } else { $cw.Length -gt 1 -and $q.StartsWith($cw+' ') }
        $verified = (Get-YoutubeField $video 'channel_is_verified' $false) -eq $true
        if ($official -and -not $review) {
            if ($publisher -and $coverage -ge .5) { $score += 24; $why += 'requested publisher display-name match (identity not authenticated)' }
            if ($publisher -and $verified) { $score += 4; $why += 'YouTube verified-channel metadata' }
            if ($words -match '\b(event|keynote|presentation|launch|unveiling)\b') { $score += 12; $why += 'presentation format' }
            elseif ($words -match '\b(introducing|introduction|unveils|announces)\b') { $score += 7; $why += 'introduction format' }
            if ($words -match '\b(review|reaction|recap|opinions|first look|things to know|preorder)\b') { $score -= 15; $why += 'commentary or shopping rather than presentation' }
        }
        if ($review -and $words -match '\b(review|reaction|recap|opinions|analysis)\b') { $score += 12; $why += 'requested commentary format' }
        if ($full -and $dur -ge 1200) { $score += 7; $why += 'full-length format' }
        if ($full -and $dur -gt 0 -and $dur -lt 180) { $score -= 10; $why += 'too short for full presentation' }
        if ($short -and $dur -gt 0 -and $dur -le 240) { $score += 7; $why += 'requested short format' }
        if ($coverage -lt .5) { $score -= 30; $why += 'weak subject match' }
        [pscustomobject]@{
            id=$id; title=$title; duration=$dur; score=[math]::Round($score,2)
            url="https://www.youtube.com/watch?v=$id"; uploader=$channel
            channel_id=[string](Get-YoutubeField $video 'channel_id')
            channel_url=[string](Get-YoutubeField $video 'channel_url')
            publisher_name_match=[bool]$publisher; channel_verified_metadata=[bool]$verified
            identity_status='METADATA_ONLY_NOT_AUTHENTICATED'; ranking_reasons=$why
        }
    }
}
function Sort-YoutubeCandidates([object[]]$Candidates) {
    # Stable upstream order on equal scores; duration alone does not imply relevance.
    $indexed = for ($i=0; $i -lt $Candidates.Count; $i++) { [pscustomobject]@{candidate=$Candidates[$i]; order=$i} }
    return @($indexed | Sort-Object -Property @{Expression={$_.candidate.score};Descending=$true}, @{Expression='order';Descending=$false} | ForEach-Object {$_.candidate})
}
