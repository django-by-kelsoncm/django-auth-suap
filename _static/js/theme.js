/**
 * django_docs_theme - JavaScript
 * Handles dark mode, mobile menu toggle, copy code blocks, and UI interactions.
 */

// Immediately check and apply theme before DOM complete to avoid FOUC
(function syncThemeState() {
  const storedTheme = localStorage.getItem('django-theme');
  const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = storedTheme || (systemPrefersDark ? 'dark' : 'light');
  
  if (initialTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
})();

document.addEventListener('DOMContentLoaded', () => {
  initDarkMode();
  initMobileMenu();
  initCopyCodeButtons();
  initExternalLinks();
});

/**
 * Initialize Dark Mode toggle & state persistence
 */
function initDarkMode() {
  const themeToggleBtn = document.getElementById('theme-toggle');
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  
  updateToggleBtnIcon(isDark ? '☀️' : '🌙');

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const newTheme = (currentTheme === 'dark') ? 'light' : 'dark';
      
      applyTheme(newTheme);
      localStorage.setItem('django-theme', newTheme);
    });
  }
}

function applyTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    updateToggleBtnIcon('☀️');
  } else {
    document.documentElement.removeAttribute('data-theme');
    updateToggleBtnIcon('🌙');
  }
}

function updateToggleBtnIcon(iconSymbol) {
  const btnIcon = document.getElementById('theme-toggle-icon');
  if (btnIcon) {
    btnIcon.textContent = iconSymbol;
  }
}

/**
 * Initialize Mobile Navigation Menu Toggle
 */
function initMobileMenu() {
  const mobileMenuBtn = document.getElementById('mobile-menu-toggle');
  const headerNav = document.getElementById('django-header-nav');

  if (mobileMenuBtn && headerNav) {
    mobileMenuBtn.addEventListener('click', () => {
      const expanded = headerNav.classList.toggle('active');
      mobileMenuBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    });
  }
}

/**
 * Add Copy-to-Clipboard buttons to code blocks
 */
function initCopyCodeButtons() {
  const codeBlocks = document.querySelectorAll('div.highlight, pre');

  codeBlocks.forEach((block) => {
    // Avoid duplicate buttons or inner elements
    if (block.querySelector('.copy-btn') || (block.tagName === 'PRE' && block.parentElement.classList.contains('highlight'))) {
      return;
    }

    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.setAttribute('type', 'button');
    copyBtn.setAttribute('aria-label', 'Copiar código');
    copyBtn.textContent = 'Copiar';

    copyBtn.addEventListener('click', async () => {
      const codeText = block.querySelector('code') ? block.querySelector('code').innerText : block.innerText;
      
      try {
        await navigator.clipboard.writeText(codeText.trim());
        copyBtn.textContent = 'Copiado!';
        copyBtn.classList.add('copied');

        setTimeout(() => {
          copyBtn.textContent = 'Copiar';
          copyBtn.classList.remove('copied');
        }, 2000);
      } catch (err) {
        console.error('Falha ao copiar texto: ', err);
      }
    });

    block.style.position = 'relative';
    block.appendChild(copyBtn);
  });
}

/**
 * Set target="_blank" on external links
 */
function initExternalLinks() {
  const links = document.querySelectorAll('.django-content a[href^="http://"], .django-content a[href^="https://"]');
  const currentHost = window.location.hostname;

  links.forEach((link) => {
    if (link.hostname !== currentHost) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });
}
