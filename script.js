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
    // ---------- Blog Pagination ----------
    var blogGrid = document.getElementById('blog-grid');
    var paginationEl = document.getElementById('pagination');
    var postCountEl = document.getElementById('post-count');
    var PER_PAGE = 6;

    // Helper: create a blog card element from post object
    function createCard(post) {
        var slug = post.name.replace('.html', '').replace('blog-post-', '').replace(/-/g, ' ');
        var title = slug.charAt(0).toUpperCase() + slug.slice(1);
        var link = post.name;
        var created = new Date(post.created_at || post.updated_at);
        var dateStr = created.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
        var card = document.createElement('a');
        card.className = 'blog-card';
        card.href = link;
        card.innerHTML = '<div class="blog-card-img"><img src="https://picsum.photos/seed/' + slug + '/400/200.jpg" alt="' + title + '" loading="lazy"></div><div class="blog-card-body"><div class="blog-card-meta"><span class="blog-card-date">' + dateStr + '</span><span class="blog-card-tag">AI</span></div><h3>' + title + '</h3><p>Automated post about ' + title + '.</p><span class="rmore">Read article &rarr;</span></div>';
        return card;
    }

    // Fetch posts and render with pagination
    function loadPosts(page) {
        fetch('https://api.github.com/repos/kchour96-dev/autonomous-portfolio-2026/contents/?ref=main')
            .then(function(res) { return res.json(); })
            .then(function(files) {
                var posts = files.filter(function(f) { return f.name.match(/^blog-post-.*\.html$/); }).sort(function(a, b) {
                    return new Date(b.created_at || b.updated_at) - new Date(a.created_at || a.updated_at);
                });
                // Update total count if element present
                if (postCountEl) {
                    postCountEl.textContent = posts.length;
                }
                // Render current page
                var start = (page - 1) * PER_PAGE;
                var end = start + PER_PAGE;
                if (start < 0) start = 0;
                var pagePosts = posts.slice(start, end);
                blogGrid.innerHTML = '';
                pagePosts.forEach(function(post) {
                    blogGrid.appendChild(createCard(post));
                });
                // Render pagination controls
                if (paginationEl) {
                    paginationEl.innerHTML = '';
                    var totalPages = Math.ceil(posts.length / PER_PAGE);
                    if (totalPages > 1) {
                        var makePageBtn = function(p, label) {
                            var btn = document.createElement('button');
                            btn.className = 'page-btn' + (p === page ? ' active' : '');
                            btn.textContent = label || p;
                            btn.addEventListener('click', function() {
                                loadPosts(p);
                                window.scrollTo({ top: 0, behavior: 'smooth' });
                            });
                            return btn;
                        };
                        // Prev
                        if (page > 1) {
                            var prev = makePageBtn(page - 1, '&larr;');
                            paginationEl.appendChild(prev);
                        }
                        // Page numbers
                        for (var i = 1; i <= totalPages; i++) {
                            paginationEl.appendChild(makePageBtn(i));
                        }
                        // Next
                        if (page < totalPages) {
                            var next = makePageBtn(page + 1, '&rarr;');
                            paginationEl.appendChild(next);
                        }
                    }
                }
            })
            .catch(function(err) {
                console.error('Blog load failed:', err);
                if (postCountEl) postCountEl.textContent = '19';
            });
    }

    // Initialize: load page 1 by default
    var initialPage = 1;
    // If URL has ?page=N, use that
    var params = new URLSearchParams(window.location.search);
    var pageParam = params.get('page');
    if (pageParam && !isNaN(pageParam) && parseInt(pageParam) > 0) {
        initialPage = parseInt(pageParam);
    }
    loadPosts(initialPage);
});
