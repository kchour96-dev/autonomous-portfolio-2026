$ErrorActionPreference = 'Stop'
$folder = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

Write-Host '=== FIX ALL BLOG POSTS ===' -ForegroundColor Cyan

$templatePath = Join-Path $folder 'blog-post-template.html'
$template = Get-Content $templatePath -Raw -Encoding UTF8

$articleFiles = Get-ChildItem $folder -Filter 'blog-post-*.html' | Where-Object { $_.BaseName -ne 'blog-post-template' }

foreach ($file in $articleFiles) {
    Write-Host "`nProcessing $($file.Name)..." -ForegroundColor Yellow
    $old = Get-Content $file.FullName -Raw -Encoding UTF8

    $slug = $file.BaseName.Substring('blog-post-'.Length)
    Write-Host "  Slug: $slug" -ForegroundColor Gray

    # Extract title
    $title = ''
    if ($old -match '<h1 class="atitle"[^>]*>(.+?)</h1>') {
        $title = $matches[1].Trim()
    }

    # Extract lead
    $lead = ''
    if ($old -match '<p class="alead">(.+?)</p>') {
        $lead = $matches[1].Trim()
    }

    # Extract date
    $dateIso = ''
    $date = ''
    if ($old -match '<time[^>]*datetime="([^"]+)"[^>]*>(.+?)</time>') {
        $dateIso = $matches[1]
        $date = $matches[2].Trim()
    }
    if (!$date) { $date = 'April 5, 2026'; $dateIso = '2026-04-05' }

    # Extract content between <div class="acontent"...> and <footer>
    $content = ''
    $startIdx = $old.IndexOf('<div class="acontent"')
    if ($startIdx -ge 0) {
        $opening = $old.IndexOf('>', $startIdx) + 1
        $endMarker = '</div>'
        $footerIdx = $old.IndexOf('<footer class="article-footer"', $startIdx)
        # Find the </div> that closes acontent (right before article-footer or with proper nesting)
        $closeIdx = $old.LastIndexOf($endMarker, $footerIdx)
        if ($closeIdx -ge 0) {
            $content = $old.Substring($opening, $closeIdx - $opening).Trim()
        }
    }

    if (!$content -or $content.Length -lt 50) {
        Write-Host "  WARN: Could not extract content, using empty" -ForegroundColor Red
        $content = "<h2>$title</h2><p>$lead</p>"
    } else {
        Write-Host "  Content: $($content.Length) chars" -ForegroundColor Gray
    }

    # Rebuild from clean template
    $article = $template -replace '\[\[TITLE\]\]', $title
    $article = $article -replace '\[\[DESCRIPTION\]\]', $lead
    $article = $article -replace '\[\[KEYWORDS\]\]', 'AI,autonomous,Ollama,local LLM,GTX 1650,OpenClaw'
    $article = $article -replace '\[\[DATE\]\]', $date
    $article = $article -replace '\[\[DATE_ISO\]\]', $dateIso
    $article = $article -replace '\[\[SLUG\]\]', $slug
    $article = $article -replace '\[\[LEAD\]\]', $lead
    $article = $article -replace '\[\[CONTENT\]\]', $content

    [System.IO.File]::WriteAllText($file.FullName, $article, [System.Text.Encoding]::UTF8)
    Write-Host "  Fixed $($file.Name)" -ForegroundColor Green
}

# Fix blog.html - remove empty href cards, fix broken links
$blogPath = Join-Path $folder 'blog.html'
$blogOld = Get-Content $blogPath -Raw -Encoding UTF8

# Remove cards with empty href="" that are broken
# Pattern: <a class="blog-card" href="">...</a>
$cleanBlog = [RegEx]::Replace($blogOld, '(?s)\s*<a class="blog-card" href="">.*?</a>\s*\n?', '', [System.Text.RegularExpressions.RegexOptions]::Singleline)

# Fix double-quote href: href=""something""
$cleanBlog = $cleanBlog -replace 'href=""([^"]+)""', 'href="$1"'

if ($cleanBlog -ne $blogOld) {
    [System.IO.File]::WriteAllText($blogPath, $cleanBlog, [System.Text.Encoding]::UTF8)
    Write-Host "`nFixed blog.html (removed broken cards, fixed links)" -ForegroundColor Green
} else {
    Write-Host "`nblog.html looks clean" -ForegroundColor Green
}

Write-Host "`n=== DONE ===" -ForegroundColor Cyan
