$ErrorActionPreference = 'Stop'
$folder = 'C:\Users\One Gears\.openclaw\workspace\portfolio-website'

$targets = @(
    'blog-post-building-autonomous-web-systems.html',
    'blog-post-hidden-costs-of-cloud-ai.html',
    'blog-post-quantum-machine-learning-breakthroughs.html'
)

foreach ($name in $targets) {
    $path = Join-Path $folder $name
    if (!(Test-Path $path)) { continue }
    $c = Get-Content $path -Raw -Encoding UTF8

    # Fix broken share section injected by bad PowerShell replace
    if ($c -match 'param\$\$m') {
        $c = $c -replace '(?s)<div class="a-share">Share on:.*?</div>', { 
            '<div class="a-share">Share on:
                <a class="share-btn" href="https://twitter.com/intent/tweet?url=https://autonomous-portfolio-2026.live/' + $name.Replace('blog-post-','').Replace('.html','') + '&text=' + ([regex]::Match($c, '<title>(.+?)</title>').Groups[1].Value) + '" target="_blank">X</a>
                <a class="share-btn" href="https://www.linkedin.com/shareArticle?mini=true&url=https://autonomous-portfolio-2026.live/' + $name.Replace('blog-post-','').Replace('.html','') + '" target="_blank">in</a>
            </div>'
        }
    }

    # Fix nav-toggle character
    $c = $c -replace 'Menu">â˜°', 'Menu">&#9776;'
    $c = $c -replace 'Menu">�', 'Menu">&#9776;'

    [System.IO.File]::WriteAllText($path, $c, [System.Text.Encoding]::UTF8)
    Write-Host "Fixed $name"
}

Write-Host "`nDone."
