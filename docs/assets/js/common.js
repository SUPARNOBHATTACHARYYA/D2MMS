/**
 * Common functionality for Vibrations & Dynamics Course Portal
 * Theme toggle, scroll-spy, code tabs, diagnostic quiz, KaTeX math auto-render
 */

(function () {
  'use strict';

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

  function runAll() {
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
