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

    // ---------- Update Post Count on Homepage ----------
    var postCountEl = document.getElementById('post-count');
    if (postCountEl) {
        fetch('https://api.github.com/repos/kchour96-dev/autonomous-portfolio-2026/contents/?ref=main')
            .then(function(res) { return res.json(); })
            .then(function(files) {
                var posts = files.filter(function(f) { return f.name.match(/^blog-post-.*\.html$/); });
                postCountEl.textContent = posts.length;
            })
            .catch(function() {
                // Fallback: keep existing if fetch fails
                console.log('Using fallback post count');
            });
    }

    // ---------- Blog Pagination (on blog.html) ----------
    var blogGrid = document.getElementById('blog-grid');
    var paginationEl = document.getElementById('pagination');
    var PER_PAGE = 6;

    if (blogGrid && paginationEl) {
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

        function loadPosts(page) {
            fetch('https://api.github.com/repos/kchour96-dev/autonomous-portfolio-2026/contents/?ref=main')
                .then(function(res) { return res.json(); })
                .then(function(files) {
                    var posts = files.filter(function(f) { return f.name.match(/^blog-post-.*\.html$/); }).sort(function(a, b) {
                        return new Date(b.created_at || b.updated_at) - new Date(a.created_at || a.updated_at);
                    });
                    // Update homepage count as well
                    if (postCountEl) postCountEl.textContent = posts.length;

                    var start = (page - 1) * PER_PAGE;
                    var end = start + PER_PAGE;
                    var pagePosts = posts.slice(start, end);
                    blogGrid.innerHTML = '';
                    pagePosts.forEach(function(post) {
                        blogGrid.appendChild(createCard(post));
                    });

                    // Render pagination controls
                    paginationEl.innerHTML = '';
                    var totalPages = Math.ceil(posts.length / PER_PAGE);
                    if (totalPages > 1) {
                        var makePageBtn = function(p, label) {
                            var btn = document.createElement('button');
                            btn.className = 'page-btn' + (p === page ? ' active' : '');
                            btn.textContent = label || p;
                            btn.dataset.page = p;
                            btn.addEventListener('click', function() {
                                loadPosts(p);
                                window.history.replaceState(null, '', '?page=' + p);
                                window.scrollTo({ top: 0, behavior: 'smooth' });
                            });
                            return btn;
                        };
                        if (page > 1) {
                            paginationEl.appendChild(makePageBtn(page - 1, '&larr;'));
                        }
                        for (var i = 1; i <= totalPages; i++) {
                            paginationEl.appendChild(makePageBtn(i));
                        }
                        if (page < totalPages) {
                            paginationEl.appendChild(makePageBtn(page + 1, '&rarr;'));
                        }
                    }
                })
                .catch(function(err) {
                    console.error('Blog load failed:', err);
                });
        }

        // Initialize blog pagination
        var initialPage = 1;
        var params = new URLSearchParams(window.location.search);
        var pageParam = params.get('page');
        if (pageParam && !isNaN(pageParam) && parseInt(pageParam) > 0) {
            initialPage = parseInt(pageParam);
        }
        loadPosts(initialPage);
    }
});
