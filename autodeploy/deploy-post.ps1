$ErrorActionPreference = 'Stop'

$envPath = '..\.env'
if (!(Test-Path $envPath)) { throw '.env not found' }
$tokenLine = (Get-Content $envPath | Where-Object { $_ -match '^GITHUB_TOKEN=' })[0]
$GitHubToken = ($tokenLine -replace '^GITHUB_TOKEN=', '').Trim()

$GitHubUser = 'kchour96-dev'
$GitHubRepo = 'autonomous-portfolio-2026'
$GitHubBranch = 'main'
$OllamaAPI = 'http://localhost:11434/api/generate'
$TemplatePath = '..\blog-post-template.html'

Write-Host '=== AUTONOMOUS POST DEPLOYER ===' -ForegroundColor Cyan

Write-Host '[1/4] Checking Ollama...' -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 5
    $model = $resp.models[0].name
    Write-Host ("   OK - Model: " + $model) -ForegroundColor Green
} catch {
    Write-Host '   FAIL - ollama not running' -ForegroundColor Red
    pause; exit 1
}

Write-Host '[2/4] Selecting topic...' -ForegroundColor Yellow
$topics = @(
  'Edge AI and On-Device Intelligence','AI Agents Replacing Traditional Software',
  'Open Source LLMs in 2026','Machine Learning for Climate',
  'AI-Powered Code Review','Quantum Machine Learning Breakthroughs',
  'Building Autonomous Web Systems','Hidden Costs of Cloud AI',
  'Generative AI in Game Design','Tiny Models Mobile AI','AI Security Threats',
  'Computer Vision in Healthcare','Synthetic Data Training',
  'NLP for Small Languages','AI Ethics That Actually Work'
)
$topic = $topics[(Get-Random -Maximum $topics.Count)]
Write-Host ('   OK - ' + $topic) -ForegroundColor Green

Write-Host '[3/4] Generating article...' -ForegroundColor Yellow
$prompt = 'Write a comprehensive 1500+ word SEO blog article about: "' + $topic + '".'
$prompt += ' Use only HTML tags: h1, h2, p, strong, img, form, input, button, ul, li, ol.'
$prompt += ' Include 3 images like https://picsum.photos/seed/SLUG/800/400.jpg'
$prompt += ' Write 5-8 paragraphs. Under 2000 chars total HTML.'

$body = @{
    model = $model
    prompt = $prompt
    stream = $false
    options = @{ num_predict = 1200; temperature = 0.75; top_p = 0.9 }
} | ConvertTo-Json -Depth 4

try {
    $raw = Invoke-WebRequest -Uri $OllamaAPI -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 300 -UseBasicParsing
    $parsed = $raw.Content | ConvertFrom-Json
    $content = ($parsed.response -split "`n" | Where-Object { $_ -match '<(h|p|img|form|input|button|ul|ol|li|strong|em)' }) -join "`n"
    if ($content.Length -lt 800) { throw 'too short' }
    Write-Host ('   OK - ' + $content.Length + ' chars') -ForegroundColor Green
} catch {
    Write-Host '   WARN - Using fallback article' -ForegroundColor Yellow
    $slug = ($topic.ToLower() -replace '[^a-z0-9]+','-')
    $h1 = '<h1>' + $topic + '</h1>'
    $intro = '<p><strong>' + $topic + '</strong> is reshaping how developers work. Running models locally on a GTX 1650 with Ollama means no cloud costs, full privacy, and instant iteration.</p>'
    $img1 = '<img src="https://picsum.photos/seed/' + $slug + '-1/800/400.jpg" alt="Concept illustration">'
    $s1 = '<h2>Why It Matters</h2><p>Understanding this trend gives developers a competitive edge. Early adopters of local LLMs see faster workflows, reduced costs, and better data control.</p>'
    $s2 = '<h2>Practical Applications</h2><p>From code autocomplete to autonomous content generation, use cases are expanding daily. OpenClaw and Ollama make these pipelines accessible on consumer hardware.</p>'
    $img2 = '<img src="https://picsum.photos/seed/' + $slug + '-2/800/400.jpg" alt="Local LLM setup">'
    $s3 = '<h2>Getting Started</h2><p>Install Ollama, pull a model like phi:latest, and experiment. For 1500+ word articles, set num_predict high and use structured prompts.</p>'
    $img3 = '<img src="https://picsum.photos/seed/' + $slug + '-3/800/400.jpg" alt="Automation workflow">'
    $concl = '<h2>Conclusion</h2><p>The future of content creation is autonomous. Start building your pipeline today.</p>'
    $nl = '<form action="#" method="post" style="margin:24px 0;display:flex;gap:8px;flex-wrap:wrap"><input type="email" placeholder="your@email.com" required style="padding:12px 16px;border-radius:8px;border:1px solid #2c2c2e;background:#151516;color:#e8e8ed;min-width:240px"><button type="submit" style="padding:12px 24px;background:#bf5af2;color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer">Subscribe</button></form>'
    $content = $h1 + "`n" + $intro + "`n" + $img1 + "`n" + $s1 + "`n" + $s2 + "`n" + $img2 + "`n" + $s3 + "`n" + $img3 + "`n" + $concl + "`n" + $nl
}

Write-Host '[4/4] Building and uploading...' -ForegroundColor Yellow
$date = Get-Date -Format 'MMMM d, yyyy'
$dateTag = Get-Date -Format 'yyyy-MM-dd'
$slug = ($topic.ToLower() -replace '[^a-z0-9]+','-')
$slug = $slug.Substring(0,[Math]::Min(60,$slug.Length))
$fileName = 'blog-post-' + $slug + '.html'
Write-Host ('   Creating ' + $fileName) -ForegroundColor Gray

$template = Get-Content $TemplatePath -Raw
$lead = 'Exploring ' + $topic + ': how it works, why it matters, and practical steps to implement with local AI tools.'
$desc = 'Deep dive into ' + $topic + ' with examples on Ollama, local LLMs, and autonomous coding.'

$article = $template -replace '\[\[TITLE\]\]', $topic
$article = $article -replace '\[\[DESCRIPTION\]\]', $desc
$article = $article -replace '\[\[KEYWORDS\]\]', 'AI,autonomous,Ollama,local LLM,GTX 1650,OpenClaw'
$article = $article -replace '\[\[DATE\]\]', $date
$article = $article -replace '\[\[DATE_ISO\]\]', $dateTag
$article = $article -replace '\[\[SLUG\]\]', $slug
$article = $article -replace '\[\[LEAD\]\]', $lead
$article = $article -replace '\[\[CONTENT\]\]', $content

$apiUrl = 'https://api.github.com/repos/' + $GitHubUser + '/' + $GitHubRepo + '/contents/' + $fileName
$headers = @{
    Authorization = 'token ' + $GitHubToken
    Accept = 'application/vnd.github.v3+json'
    'User-Agent' = 'OpenClaw-AutoPost'
}
$payload = @{
    message = 'Add article: ' + $topic
    content = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($article))
    branch = $GitHubBranch
} | ConvertTo-Json -Depth 4

try {
    $put = Invoke-WebRequest -Uri $apiUrl -Method Put -Body $payload -Headers $headers -ContentType 'application/json' -TimeoutSec 20 -UseBasicParsing
    if ($put.StatusCode -ge 200 -and $put.StatusCode -lt 300) {
        Write-Host '   OK - Uploaded article!' -ForegroundColor Green
    } else {
        throw ('HTTP ' + $put.StatusCode)
    }
} catch {
    Write-Host ('   FAIL - ' + $_.Exception.Message) -ForegroundColor Red
    pause; exit 1
}

# Update blog.html with new card
Write-Host '   Updating blog.html...' -ForegroundColor Gray
$blogApiUrl = 'https://api.github.com/repos/' + $GitHubUser + '/' + $GitHubRepo + '/contents/blog.html'
$blogFetch = Invoke-WebRequest -Uri $blogApiUrl -Method Get -Headers $headers -UseBasicParsing
$blogData = $blogFetch.Content | ConvertFrom-Json
$blogSha = $blogData.sha
$blogHtml = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($blogData.content))

$card = @"
<a class="blog-card" href=""$fileName"">
    <div class="blog-card-img"><span>📄</span></div>
    <div class="blog-card-body">
        <div class="blog-card-meta">
            <span class="blog-card-date">$date</span>
            <span class="blog-card-tag">AI</span>
        </div>
        <h3>$topic</h3>
        <p>Automatically generated article about $topic. Explore the full content.</p>
        <span class="rmore">Read article →</span>
    </div>
</a>
"@

$insertPos = $blogHtml.IndexOf('<div class="blog-grid">')
if ($insertPos -ge 0) {
    $insertPos = $blogHtml.IndexOf('>', $insertPos) + 1
    $updatedBlog = $blogHtml.Insert($insertPos, "`n$card`n")
} else {
    $insertPos = $blogHtml.IndexOf('<div class="blog-grid" id="blog-grid">')
    if ($insertPos -ge 0) {
        $insertPos = $blogHtml.IndexOf('>', $insertPos) + 1
        $updatedBlog = $blogHtml.Insert($insertPos, "`n$card`n")
    } else {
        $sectionClose = $blogHtml.LastIndexOf('</div></section>')
        if ($sectionClose -lt 0) { throw 'Cannot find blog-grid' }
        $updatedBlog = $blogHtml.Insert($sectionClose, "`n$card`n")
    }
}

$blogPayload = [PSCustomObject]@{
    message = 'Add blog card: ' + $topic
    content = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($updatedBlog))
    sha = $blogSha
    branch = $GitHubBranch
} | ConvertTo-Json -Depth 4

Invoke-WebRequest -Uri $blogApiUrl -Method Put -Headers $headers -Body $blogPayload -ContentType 'application/json' -TimeoutSec 20 -UseBasicParsing | Out-Null
Write-Host '   OK - Updated blog.html with new card!' -ForegroundColor Green

$liveUrl = 'https://' + $GitHubUser + '.github.io/' + $GitHubRepo + '/' + $fileName
$blogUrl = 'https://' + $GitHubUser + '.github.io/' + $GitHubRepo + '/blog.html'
Write-Host '=== SUCCESS ===' -ForegroundColor Green
Write-Host ('Article: ' + $topic) -ForegroundColor White
Write-Host ('Article URL: ' + $liveUrl) -ForegroundColor Cyan
Write-Host ('Blog page: ' + $blogUrl) -ForegroundColor Cyan
Write-Host 'Live in ~30 seconds.' -ForegroundColor Yellow