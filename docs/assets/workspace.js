/**
 * University Lecture Portal - Interactive Workspace & Search Client
 */
(function() {
  'use strict';

  // 1. Theme Toggle Management
  function initThemeToggle() {
    const toggleBtns = document.querySelectorAll('.theme-toggle');
    if (!toggleBtns.length) return;

    toggleBtns.forEach(function(btn) {
      btn.addEventListener('click', function() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        try {
          localStorage.setItem('portal_theme', next);
        } catch (e) {}
      });
    });
  }

  // 2. Sidebar Dock (Toggle, Backdrop, Responsive Collapse)
  function initSidebar() {
    const sidebar = document.getElementById('lecture-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    const openBtn = document.getElementById('sidebar-open-btn');
    const portalRoot = document.querySelector('.portal-root');
    if (!sidebar) return;

    // Create backdrop for mobile drawer if missing
    let backdrop = document.querySelector('.sidebar-backdrop');
    if (!backdrop && portalRoot) {
      backdrop = document.createElement('div');
      backdrop.className = 'sidebar-backdrop';
      portalRoot.appendChild(backdrop);
    }

    function toggleSidebar(forceState) {
      const isCollapsed = portalRoot.classList.contains('sidebar-collapsed');
      const shouldCollapse = (typeof forceState === 'boolean') ? !forceState : !isCollapsed;
      
      portalRoot.classList.toggle('sidebar-collapsed', shouldCollapse);
      portalRoot.classList.toggle('sidebar-mobile-open', !shouldCollapse && window.innerWidth <= 1024);

      try {
        localStorage.setItem('portal_sidebar_collapsed', shouldCollapse ? 'true' : 'false');
      } catch (e) {}
    }

    if (toggleBtn) {
      toggleBtn.addEventListener('click', function() {
        toggleSidebar(false);
      });
    }

    if (openBtn) {
      openBtn.addEventListener('click', function() {
        const isCollapsed = portalRoot.classList.contains('sidebar-collapsed');
        if (window.innerWidth <= 1024) {
          portalRoot.classList.toggle('sidebar-mobile-open');
        } else {
          toggleSidebar(isCollapsed);
        }
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', function() {
        portalRoot.classList.remove('sidebar-mobile-open');
      });
    }

    // Restore desktop preference
    try {
      const saved = localStorage.getItem('portal_sidebar_collapsed');
      if (saved === 'true' && window.innerWidth > 1024) {
        portalRoot.classList.add('sidebar-collapsed');
      }
    } catch (e) {}

    // Synchronize select dropdown if present
    const lectureSelect = document.getElementById('lecture-selector');
    if (lectureSelect) {
      lectureSelect.addEventListener('change', function() {
        const targetSlug = lectureSelect.value;
        if (targetSlug) {
          window.location.href = `../${targetSlug}/index.html`;
        }
      });
    }
  }

  // 3. Home Page Instant Search & Topic Filter
  function initLectureSearch() {
    const searchInput = document.getElementById('lecture-search');
    const clearBtn = document.getElementById('search-clear-btn');
    const chipBtns = document.querySelectorAll('.filter-chips .chip');
    const statusText = document.getElementById('filter-status');
    const cards = document.querySelectorAll('.lecture-card');
    const noResults = document.getElementById('no-search-results');
    if (!searchInput || !cards.length) return;

    let activeTag = 'all';

    function filterLectures() {
      const query = (searchInput.value || '').toLowerCase().trim();
      if (clearBtn) clearBtn.hidden = !query;
      let visibleCount = 0;

      cards.forEach(function(card) {
        const title = (card.dataset.title || '').toLowerCase();
        const number = (card.dataset.number || '').toLowerCase();
        const tags = (card.dataset.tags || '').toLowerCase();
        const text = (card.textContent || '').toLowerCase();

        const matchesQuery = !query || title.includes(query) || number.includes(query) || tags.includes(query) || text.includes(query);
        const matchesTag = (activeTag === 'all') || tags.includes(activeTag.toLowerCase());

        if (matchesQuery && matchesTag) {
          card.style.display = '';
          visibleCount++;
        } else {
          card.style.display = 'none';
        }
      });

      if (statusText) {
        statusText.textContent = `Showing ${visibleCount} of ${cards.length} lecture${cards.length === 1 ? '' : 's'}`;
      }
      if (noResults) {
        noResults.hidden = (visibleCount > 0);
      }
    }

    searchInput.addEventListener('input', filterLectures);
    if (clearBtn) {
      clearBtn.addEventListener('click', function() {
        searchInput.value = '';
        filterLectures();
        searchInput.focus();
      });
    }

    chipBtns.forEach(function(chip) {
      chip.addEventListener('click', function() {
        chipBtns.forEach(function(c) { c.classList.remove('active'); });
        chip.classList.add('active');
        activeTag = chip.dataset.tag || 'all';
        filterLectures();
      });
    });
  }

  // 4. Draggable Split Divider
  function initSplitDivider() {
    const container = document.querySelector('.workspace-container');
    const divider = document.querySelector('.workspace-divider');
    const paneSlides = document.querySelector('.pane-slides');
    if (!container || !divider || !paneSlides) return;

    // Restore saved ratio
    try {
      const savedRatio = localStorage.getItem('workspace_split_ratio');
      if (savedRatio && container.classList.contains('layout-split')) {
        if (savedRatio.endsWith('%')) {
          paneSlides.style.width = savedRatio;
        } else {
          paneSlides.style.width = '50%';
        }
      }
    } catch (e) {}

    let isDragging = false;

    function onPointerDown(e) {
      if (e.button !== 0) return;
      isDragging = true;
      document.body.classList.add('is-resizing');
      divider.setPointerCapture(e.pointerId);
    }

    function onPointerMove(e) {
      if (!isDragging) return;
      const rect = container.getBoundingClientRect();
      const pointerX = e.clientX - rect.left;
      let ratio = (pointerX / rect.width) * 100;
      // Clamp between 15% and 85%
      ratio = Math.max(15, Math.min(85, ratio));
      paneSlides.style.width = ratio.toFixed(2) + '%';
    }

    function onPointerUp(e) {
      if (!isDragging) return;
      isDragging = false;
      document.body.classList.remove('is-resizing');
      try {
        divider.releasePointerCapture(e.pointerId);
      } catch (err) {}
      try {
        localStorage.setItem('workspace_split_ratio', paneSlides.style.width);
      } catch (err) {}
    }

    divider.addEventListener('pointerdown', onPointerDown);
    divider.addEventListener('pointermove', onPointerMove);
    divider.addEventListener('pointerup', onPointerUp);
    divider.addEventListener('pointercancel', onPointerUp);

    // WCAG Keyboard accessibility
    divider.addEventListener('keydown', function(e) {
      let currentWidth = parseFloat(paneSlides.style.width) || 50;
      if (e.key === 'ArrowLeft') {
        currentWidth = Math.max(15, currentWidth - 2);
        paneSlides.style.width = currentWidth + '%';
        e.preventDefault();
      } else if (e.key === 'ArrowRight') {
        currentWidth = Math.min(85, currentWidth + 2);
        paneSlides.style.width = currentWidth + '%';
        e.preventDefault();
      } else if (e.key === 'Home') {
        paneSlides.style.width = '50%';
        e.preventDefault();
      }
      try {
        localStorage.setItem('workspace_split_ratio', paneSlides.style.width);
      } catch (err) {}
    });

    divider.addEventListener('dblclick', function() {
      paneSlides.style.width = '50%';
      try {
        localStorage.setItem('workspace_split_ratio', '50%');
      } catch (err) {}
    });
  }

  // 5. Layout Switcher (Split, Slides, Notebook)
  function initLayoutSwitcher() {
    const container = document.querySelector('.workspace-container');
    const buttons = document.querySelectorAll('.layout-switcher .layout-btn');
    if (!container || !buttons.length) return;

    function setLayout(mode) {
      container.classList.remove('layout-split', 'layout-slides', 'layout-notebook');
      container.classList.add(`layout-${mode}`);

      buttons.forEach(function(btn) {
        const isActive = btn.dataset.layout === mode;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
      });

      try {
        localStorage.setItem('portal_layout_mode', mode);
      } catch (e) {}
    }

    buttons.forEach(function(btn) {
      btn.addEventListener('click', function() {
        setLayout(btn.dataset.layout);
      });
    });

    // Restore saved layout
    try {
      const savedMode = localStorage.getItem('portal_layout_mode');
      if (savedMode && ['split', 'slides', 'notebook'].includes(savedMode)) {
        setLayout(savedMode);
      } else {
        setLayout('split');
      }
    } catch (e) {
      setLayout('split');
    }
  }

  // 6. Mobile Tab Switcher
  function initMobileTabs() {
    const tabSlides = document.getElementById('tab-slides');
    const tabNotebook = document.getElementById('tab-notebook');
    const paneSlides = document.querySelector('.pane-slides');
    const paneNotebook = document.querySelector('.pane-notebook');
    if (!tabSlides || !tabNotebook || !paneSlides || !paneNotebook) return;

    tabSlides.addEventListener('click', function() {
      tabSlides.classList.add('active');
      tabSlides.setAttribute('aria-selected', 'true');
      tabNotebook.classList.remove('active');
      tabNotebook.setAttribute('aria-selected', 'false');

      paneSlides.classList.remove('is-hidden-mobile');
      paneNotebook.classList.add('is-hidden-mobile');
    });

    tabNotebook.addEventListener('click', function() {
      tabNotebook.classList.add('active');
      tabNotebook.setAttribute('aria-selected', 'true');
      tabSlides.classList.remove('active');
      tabSlides.setAttribute('aria-selected', 'false');

      paneNotebook.classList.remove('is-hidden-mobile');
      paneSlides.classList.add('is-hidden-mobile');
    });
  }

  // 7. Status Banner Dismissal
  function initStatusBanner() {
    const banner = document.getElementById('workspace-status-banner');
    const closeBtn = document.getElementById('banner-close-btn');
    if (!banner || !closeBtn) return;

    try {
      if (sessionStorage.getItem('banner_dismissed') === 'true') {
        banner.style.display = 'none';
        return;
      }
    } catch (e) {}

    closeBtn.addEventListener('click', function() {
      banner.style.display = 'none';
      try {
        sessionStorage.setItem('banner_dismissed', 'true');
      } catch (e) {}
    });
  }

  // 8. Sanitize Iframe Source (Prevent Credential Leak into Fetch)
  function sanitizeIframeSrc() {
    const iframe = document.getElementById('jupyterlite-iframe');
    if (iframe) {
      const rawSrc = iframe.getAttribute('src');
      if (rawSrc && !rawSrc.startsWith('http')) {
        const cleanOrigin = window.location.protocol + '//' + window.location.host;
        const normalizedPath = rawSrc.replace(/^(\.\.\/)+/, '/');
        const targetUrl = cleanOrigin + normalizedPath;
        if (iframe.src !== targetUrl) {
          iframe.src = targetUrl;
        }
      }
    }
  }

  // Run on DOM ready or immediately if already loaded
  function initAll() {
    sanitizeIframeSrc();
    initThemeToggle();
    initSidebar();
    initLectureSearch();
    initSplitDivider();
    initLayoutSwitcher();
    initMobileTabs();
    initStatusBanner();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
