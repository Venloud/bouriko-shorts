$ErrorActionPreference='Stop'
. "$PSScriptRoot/../windows/rank-youtube-candidates.ps1"
function Check($name,$query,$candidates,$expected) {
 $ranked=@(Sort-YoutubeCandidates @(Get-RankedYoutubeCandidates -Query $query -Candidates $candidates))
 if ($ranked[0].id -ne $expected) {throw "$name failed: $($ranked[0].title)"}
 Write-Output "PASS: $name -> $($ranked[0].title)"
}
$saved=@(
 [pscustomobject]@{id='3fVDRJ-JKw0';title='New Apple CEO unveils the foldable iPhone Duo';uploader='Associated Press';duration=91},
 [pscustomobject]@{id='FUfGcZ092b0';title='Introducing the new iPhone Duo';uploader='Apple';duration=187},
 [pscustomobject]@{id='39BalPDuTo0';title='Apple Event September 9 2026: Introducing iPhone Duo and more';uploader='Apple';duration=4638},
 [pscustomobject]@{id='bxSGfpoFP30';title='iPhone Duo: The largest display of any iPhone';uploader='Apple';duration=66})
Check 'recorded Apple presentation vs news, ad and recap' 'Apple iPhone Duo official presentation' $saved '39BalPDuTo0'
$cases=@(
 [pscustomobject]@{id='xxxxxxxxxx1';title='NASA Mars mission official news recap';uploader='News Desk';duration=90},
 [pscustomobject]@{id='xxxxxxxxxx2';title='Mars mission launch presentation';uploader='NASA';duration=4200},
 [pscustomobject]@{id='xxxxxxxxxx3';title='Traffic signal car intersection';uploader='Road Channel';duration=120})
Check 'unrelated publisher and topic' 'NASA Mars mission official presentation' $cases 'xxxxxxxxxx2'
Check 'no traffic-specific bonus' 'Mars mission' $cases 'xxxxxxxxxx1'
$cases=@(
 [pscustomobject]@{id='xxxxxxxxxx4';title='Galaxy launch event';uploader='Samsung';duration=4800},
 [pscustomobject]@{id='xxxxxxxxxx5';title='Galaxy review';uploader='Independent Reviewer';duration=500})
Check 'review intent does not favor brand keynote' 'Samsung Galaxy review' $cases 'xxxxxxxxxx5'
$cases=@(
 [pscustomobject]@{id='xxxxxxxxxx6';title='Galaxy launch trailer';uploader='Samsung';duration=90},
 [pscustomobject]@{id='xxxxxxxxxx7';title='Galaxy launch keynote';uploader='Samsung';duration=4800})
Check 'full-length intent' 'Samsung Galaxy full keynote' $cases 'xxxxxxxxxx7'
$bad=@([pscustomobject]@{id='bad';title='Mars mission'})
if (@(Get-RankedYoutubeCandidates -Query 'Mars mission' -Candidates $bad).Count) {throw 'Invalid ID accepted'}
Write-Output 'PASS: malformed candidate rejected; missing optional channel fields supported'
