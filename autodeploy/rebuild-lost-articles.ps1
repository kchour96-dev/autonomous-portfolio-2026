$ErrorActionPreference = 'Stop'
$folder = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$templatePath = Join-Path $folder 'blog-post-template.html'
$template = Get-Content $templatePath -Raw -Encoding UTF8

$articles = @(
    @{ title='Building Autonomous Web Systems'; slug='building-autonomous-web-systems' },
    @{ title='Hidden Costs of Cloud AI'; slug='hidden-costs-of-cloud-ai' },
    @{ title='Quantum Machine Learning Breakthroughs'; slug='quantum-machine-learning-breakthroughs' }
)

foreach ($art in $articles) {
    Write-Host "`n=== Generating: $($art.title) ===" -ForegroundColor Cyan
    
    $prompt = "Write a 500+ word blog article about: $($art.title). Include sections: What is it, Why It Matters, Practical Applications, Getting Started, Conclusion. Use HTML tags only: <h2>, <p>, <ul>, <ol>, <li>, <strong>, <em>. DO NOT use markdown. Output ONLY the HTML body content, no <!DOCTYPE>, no <html>, no title header. Include numbered lists where helpful."
    $json = @{ model='phi'; prompt=$prompt; stream=$false } | ConvertTo-Json
    $resp = (Invoke-WebRequest -Uri 'http://localhost:11434/api/generate' -Method Post -Body $json -TimeoutSec 120 -UseBasicParsing).Content | ConvertFrom-Json
    
    $content = $resp.response
    
    # Clean markdown artifacts  
    $content = $content -replace '```html\s*', '' -replace '```\s*', ''
    
    # Build article from template
    $dateIso = '2026-04-05'
    $date = 'April 5, 2026'
    $lead = "Exploring $($art.title): how it works, why it matters, and practical steps to implement with local AI tools."
    
    $article = $template -replace '\[\[TITLE\]\]', $art.title
    $article = $article -replace '\[\[DESCRIPTION\]\]', $lead
    $article = $article -replace '\[\[KEYWORDS\]\]', 'AI,autonomous,Ollama,local LLM,GTX 1650,OpenClaw'
    $article = $article -replace '\[\[DATE\]\]', $date
    $article = $article -replace '\[\[DATE_ISO\]\]', $dateIso
    $article = $article -replace '\[\[SLUG\]\]', $art.slug
    $article = $article -replace '\[\[LEAD\]\]', $lead
    $article = $article -replace '\[\[CONTENT\]\]', $content
    
    $path = Join-Path $folder ("blog-post-" + $art.slug + ".html")
    [System.IO.File]::WriteAllText($path, $article, [System.Text.Encoding]::UTF8)
    Write-Host "Saved $($art.slug) ($($content.Length) chars content)" -ForegroundColor Green
}

Write-Host "`n=== All rebuilt ===" -ForegroundColor Cyan
