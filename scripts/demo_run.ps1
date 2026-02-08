$ErrorActionPreference = "Stop"

$base = "http://localhost:8000"

function PostJson($path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 10
  return Invoke-RestMethod -Method POST -Uri ($base + $path) -ContentType "application/json" -Body $json
}

Write-Host "== Demo: reset user 1 + events (DB) =="
sqlite3 data/app.db @"
DELETE FROM events WHERE user_id=1;
UPDATE users SET profile_json='{}', summary='' WHERE id=1;
"@

Write-Host "== Demo: seed preferences via /chat =="
PostJson "/chat" @{ user_id = 1; message = "Mi piacciono i thriller psicologici tipo Shutter Island. Niente gore." } | Out-Null
PostJson "/chat" @{ user_id = 1; message = "In musica: dark ambient e colonne sonore tese, atmosfera cupa." } | Out-Null
PostJson "/chat" @{ user_id = 1; message = "Nei videogiochi: horror narrativo e psicologico. No jumpscare continui." } | Out-Null

Write-Host "== Demo: recommend baseline =="
$r1 = PostJson "/recommend" @{ user_id = 1; top_k_per_domain = 8 }

Write-Host "-- Bundle baseline --"
$r1.recommendations.bundle | ConvertTo-Json -Depth 10

$musicId = $r1.recommendations.bundle.music.item_id
$filmId  = $r1.recommendations.bundle.film.item_id

Write-Host "Baseline music item_id=$musicId, film item_id=$filmId"

Write-Host "== Demo: like music =="
PostJson "/feedback" @{ user_id = 1; item_id = $musicId; action = "like" } | Out-Null

Write-Host "== Demo: recommend after like (should boost ONLY music domain) =="
$r2 = PostJson "/recommend" @{ user_id = 1; top_k_per_domain = 8 }
Write-Host "-- Bundle after like --"
$r2.recommendations.bundle | ConvertTo-Json -Depth 10

Write-Host "== Demo: dislike film =="
PostJson "/feedback" @{ user_id = 1; item_id = $filmId; action = "dislike" } | Out-Null

Write-Host "== Demo: recommend after dislike (film should shift) =="
$r3 = PostJson "/recommend" @{ user_id = 1; top_k_per_domain = 8 }
Write-Host "-- Bundle after dislike --"
$r3.recommendations.bundle | ConvertTo-Json -Depth 10

Write-Host "== Demo done =="
