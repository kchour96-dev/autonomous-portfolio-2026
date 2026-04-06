document.addEventListener('DOMContentLoaded', function() {
    // Responsive nav toggle
    var toggle = document.querySelector('.nav-toggle');
    var menu = document.querySelector('.nav-links');
    if (toggle && menu) {
        toggle.addEventListener('click', function() {
            menu.classList.toggle('open');
        });
    }
    // Close nav on link click
    var links = document.querySelectorAll('.nav-links a');
    links.forEach(function(a) {
        a.addEventListener('click', function() {
            if (menu) menu.classList.remove('open');
        });
    });
    // Giscus chat comments
    var chatTarget = document.getElementById('giscus-chat');
    if (chatTarget) {
        var script = document.createElement('script');
        script.src = 'https://giscus.app/client.js';
        script.setAttribute('data-repo', 'kchour96-dev/autonomous-portfolio-2026');
        script.setAttribute('data-repo-id', 'R_kgDON9gXZg');
        script.setAttribute('data-category', 'Comments');
        script.setAttribute('data-category-id', '');
        script.setAttribute('data-mapping', 'pathname');
        script.setAttribute('data-strict', '0');
        script.setAttribute('data-reactions-enabled', '1');
        script.setAttribute('data-emit-metadata', '0');
        script.setAttribute('data-input-position', 'top');
        script.setAttribute('data-theme', 'preferred_color_scheme');
        script.setAttribute('data-lang', 'en');
        script.async = true;
        chatTarget.appendChild(script);
    }
    // Load blog posts preview dynamically
    var blogGrid = document.getElementById('blog-grid');
    var postCountEl = document.getElementById('post-count');
    if (postCountEl) {
        var totalPosts = 19; // keep in sync with actual count; API will override if available
        postCountEl.textContent = totalPosts;
    }

    // Only attempt dynamic load if blog-grid has data-dynamic attribute
    if (blogGrid && blogGrid.getAttribute('data-dynamic') === 'true') {
        fetch('https://api.github.com/repos/kchour96-dev/autonomous-portfolio-2026/contents/?ref=main')
            .then(function(res) { return res.json(); })
            .then(function(files) {
                var posts = files.filter(function(f) { return f.name.match(/^blog-post-.*\.html$/); }).reverse();
                if (postCountEl) {
                    postCountEl.textContent = posts.length;
                }
                posts.forEach(function(post, idx) {
                    var slug = post.name.replace('.html', '').replace('blog-post-', '').replace(/-/g, ' ');
                    var title = slug.charAt(0).toUpperCase() + slug.slice(1);
                    var link = post.name;
                    var created = new Date(post.created_at);
                    var dateStr = created.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
                    var card = document.createElement('a');
                    card.className = 'blog-card';
                    card.href = link;
                    var dateDisplay = (idx < 5) ? dateStr : 'Recent';
                    card.innerHTML = '<div class="blog-card-img"><img src="https://picsum.photos/seed/' + slug + '/400/200.jpg" alt="' + title + '" loading="lazy"></div><div class="blog-card-body"><div class="blog-card-meta"><span class="blog-card-date">' + dateDisplay + '</span><span class="blog-card-tag">AI</span></div><h3>' + title + '</h3><p>Automated post about ' + title + '.</p><span class="rmore">Read article &rarr;</span></div>';
                    blogGrid.appendChild(card);
                });
            })
            .catch(function() { console.log('Blog dynamic load failed; using static cards'); });
    }
});