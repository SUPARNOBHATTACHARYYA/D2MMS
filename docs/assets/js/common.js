/**
 * Common functionality for Vibrations & Dynamics Course Portal
 * Theme toggle, scroll-spy, code tabs, diagnostic quiz, KaTeX math auto-render
 */

(function () {
  'use strict';

  /* ==========================================================================
     COURSE ACCESS PASSWORD CONFIGURATION
     To change the password in the future, simply edit the string below:
     ========================================================================== */
  const COURSE_PASSWORDS = [
    'vibrations2026'   // <-- Change your password here
  ];

  // --- Safe LocalStorage helpers ---
  function getStoredTheme() {
    try {
      return localStorage.getItem('vibrations_theme') || 'light';
    } catch (e) {
      return 'light';
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem('vibrations_theme', theme);
    } catch (e) {}
  }

  // --- Theme Toggle ---
  function initTheme() {
    const savedTheme = getStoredTheme();
    document.documentElement.setAttribute('data-theme', savedTheme);

    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (themeToggleBtn) {
      updateThemeBtn(themeToggleBtn, savedTheme);
      themeToggleBtn.onclick = function () {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        setStoredTheme(next);
        updateThemeBtn(themeToggleBtn, next);
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: next } }));
      };
    }
  }

  function updateThemeBtn(btn, theme) {
    btn.innerHTML = theme === 'dark' 
      ? '<span>☀️ Light</span>' 
      : '<span>🌙 Dark</span>';
  }

  // --- KaTeX Auto-Render ---
  function renderMath() {
    if (window.renderMathInElement) {
      window.renderMathInElement(document.body, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '\\[', right: '\\]', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false }
        ],
        throwOnError: false
      });
    }
  }

  // --- Scroll-Spy Navigation ---
  function initScrollSpy() {
    const navLinks = document.querySelectorAll('.chapter-nav a[href^="#"]');
    if (!navLinks.length) return;

    const sections = [];
    navLinks.forEach(link => {
      const id = link.getAttribute('href').slice(1);
      const section = document.getElementById(id);
      if (section) sections.push({ link, section });
    });

    function onScroll() {
      const scrollPos = window.scrollY + 140;
      let active = null;
      for (let i = 0; i < sections.length; i++) {
        if (sections[i].section.offsetTop <= scrollPos) {
          active = sections[i].link;
        }
      }
      navLinks.forEach(l => l.classList.remove('active'));
      if (active) active.classList.add('active');
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // --- Code Tabs Switching & Copy ---
  function initCodeBlocks() {
    document.querySelectorAll('.code-box').forEach(box => {
      const tabs = box.querySelectorAll('.code-tab-btn');
      const blocks = box.querySelectorAll('.code-block');
      const copyBtn = box.querySelector('.btn-copy');

      tabs.forEach((tab, idx) => {
        tab.onclick = function () {
          tabs.forEach(t => t.classList.remove('active'));
          blocks.forEach(b => (b.hidden = true));
          tab.classList.add('active');
          if (blocks[idx]) blocks[idx].hidden = false;
        };
      });

      if (copyBtn) {
        copyBtn.onclick = function () {
          const visibleBlock = box.querySelector('.code-block:not([hidden])') || blocks[0];
          if (visibleBlock) {
            navigator.clipboard.writeText(visibleBlock.innerText.trim()).then(() => {
              const orig = copyBtn.innerText;
              copyBtn.innerText = 'Copied!';
              setTimeout(() => (copyBtn.innerText = orig), 1500);
            });
          }
        };
      }
    });
  }

  // --- Diagnostic Quiz Block (Atomic Layer Processing Style) ---
  function initQuizzes() {
    document.querySelectorAll('.quiz-box').forEach(box => {
      const opts = box.querySelectorAll('.quiz-opt');
      const feedback = box.querySelector('.quiz-feedback');

      opts.forEach(opt => {
        opt.onclick = function () {
          const isCorrect = opt.getAttribute('data-correct') === 'true';
          const msg = opt.getAttribute('data-explanation');

          opts.forEach(o => o.classList.remove('correct', 'incorrect'));

          if (isCorrect) {
            opt.classList.add('correct');
            if (feedback) {
              feedback.innerHTML = '<div style="margin-top: 10px; padding: 10px 14px; background: rgba(0, 137, 123, 0.1); border-left: 3px solid var(--c-teal);"><strong style="color: var(--c-teal);">✓ Correct:</strong> ' + msg + '</div>';
            }
          } else {
            opt.classList.add('incorrect');
            if (feedback) {
              feedback.innerHTML = '<div style="margin-top: 10px; padding: 10px 14px; background: rgba(207, 34, 46, 0.1); border-left: 3px solid var(--c-crimson);"><strong style="color: var(--c-crimson);">✗ Incorrect:</strong> ' + msg + '</div>';
            }
          }
        };
      });
    });
  }

  // --- Gatekeeper / Course Access Authentication ---
  function isUserAuthenticated() {
    try {
      return sessionStorage.getItem('course_auth') === 'granted' || localStorage.getItem('course_auth') === 'granted';
    } catch (e) {
      return false;
    }
  }

  function setAuthenticated(remember) {
    try {
      sessionStorage.setItem('course_auth', 'granted');
      if (remember) {
        localStorage.setItem('course_auth', 'granted');
      }
    } catch (e) {}
  }

  function clearAuthentication() {
    try {
      sessionStorage.removeItem('course_auth');
      localStorage.removeItem('course_auth');
    } catch (e) {}
  }

  function initGatekeeper() {
    const isAuth = isUserAuthenticated();

    // Setup Topbar Lock Button if topbar actions exist
    const topbarActions = document.querySelector('.topbar-actions');
    if (topbarActions && !document.getElementById('lock-portal-btn')) {
      const lockBtn = document.createElement('button');
      lockBtn.id = 'lock-portal-btn';
      lockBtn.className = 'btn-nav btn-lock';
      lockBtn.title = 'Lock course portal';
      lockBtn.setAttribute('aria-label', 'Lock course portal');
      lockBtn.innerHTML = '<span>🔒 Lock</span>';
      lockBtn.onclick = function() {
        clearAuthentication();
        document.documentElement.classList.add('gatekeeper-locked');
        initGatekeeper();
      };
      // Insert before theme toggle button
      topbarActions.insertBefore(lockBtn, topbarActions.firstChild);
    }

    if (isAuth) {
      document.documentElement.classList.remove('gatekeeper-locked');
      const existing = document.getElementById('gatekeeper-screen');
      if (existing) existing.remove();
      return;
    }

    // Otherwise user is not authenticated: ensure locked class and show screen
    document.documentElement.classList.add('gatekeeper-locked');

    let screen = document.getElementById('gatekeeper-screen');
    if (!screen) {
      screen = document.createElement('div');
      screen.id = 'gatekeeper-screen';
      screen.className = 'gatekeeper-screen';
      screen.innerHTML = `
        <div class="gatekeeper-card">
          <div class="gatekeeper-brand">
            <span class="gatekeeper-mark">ω</span>
            <h2>Mechanical Systems Dynamics</h2>
            <div class="gatekeeper-sub">NMED 5XX / CS 401 · Student Access Gateway</div>
          </div>
          <div class="gatekeeper-divider"></div>
          <p class="gatekeeper-desc">
            This educational portal is restricted to authorized students. Please enter your course access password to continue.
          </p>
          <form id="gatekeeper-form" class="gatekeeper-form">
            <div class="gatekeeper-field">
              <label for="gatekeeper-input">Course Access Password</label>
              <input type="password" id="gatekeeper-input" class="gatekeeper-input" placeholder="Enter password..." autocomplete="current-password" autofocus required>
            </div>
            <div id="gatekeeper-error" class="gatekeeper-error" style="display: none;">
              ✗ Incorrect password. Please try again.
            </div>
            <div class="gatekeeper-remember">
              <label>
                <input type="checkbox" id="gatekeeper-remember" checked> Remember access on this browser
              </label>
            </div>
            <button type="submit" id="gatekeeper-submit" class="gatekeeper-btn">
              Unlock Course Portal &rarr;
            </button>
          </form>
        </div>
      `;
      document.body.appendChild(screen);
    }

    const form = screen.querySelector('#gatekeeper-form');
    const input = screen.querySelector('#gatekeeper-input');
    const errorMsg = screen.querySelector('#gatekeeper-error');
    const rememberBox = screen.querySelector('#gatekeeper-remember');
    const card = screen.querySelector('.gatekeeper-card');

    if (input) {
      setTimeout(() => input.focus(), 100);
      input.oninput = function() {
        errorMsg.style.display = 'none';
        input.classList.remove('error');
      };
    }

    if (form) {
      form.onsubmit = function(e) {
        e.preventDefault();
        const entered = (input.value || '').trim();
        const matches = COURSE_PASSWORDS.some(p => p.toLowerCase() === entered.toLowerCase());

        if (matches) {
          setAuthenticated(rememberBox && rememberBox.checked);
          screen.classList.add('unlocked');
          document.documentElement.classList.remove('gatekeeper-locked');
          setTimeout(() => {
            if (screen.parentNode) screen.parentNode.removeChild(screen);
            // Trigger window resize so canvases recalculate their bounds properly
            window.dispatchEvent(new Event('resize'));
            if (window.VibrationsSim && window.VibrationsSim.runAll) {
              window.VibrationsSim.runAll();
            }
          }, 350);
        } else {
          errorMsg.style.display = 'block';
          input.classList.add('error');
          card.classList.remove('shake');
          void card.offsetWidth; // Trigger reflow
          card.classList.add('shake');
          input.select();
        }
      };
    }
  }

  function runAll() {
    try { initGatekeeper(); } catch(e) { console.error('initGatekeeper error:', e); }
    try { initTheme(); } catch(e) { console.error('initTheme error:', e); }
    try { renderMath(); } catch(e) { console.error('renderMath error:', e); }
    try { initScrollSpy(); } catch(e) { console.error('initScrollSpy error:', e); }
    try { initCodeBlocks(); } catch(e) { console.error('initCodeBlocks error:', e); }
    try { initQuizzes(); } catch(e) { console.error('initQuizzes error:', e); }
  }

  // Run immediately
  runAll();

  // Execute on DOMContentLoaded and load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAll);
  }
  window.addEventListener('load', runAll);

  window.VibrationsCommon = { runAll, renderMath };
})();
