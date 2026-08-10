(function () {
  'use strict';

  const FORCE_FALLBACK = new URLSearchParams(window.location.search).get('share_fallback') === '1';
  const buttons = Array.from(document.querySelectorAll('[data-share-url]'));
  if (!buttons.length) return;

  let activeButton = null;
  let feedbackTimer = null;
  const popover = document.createElement('div');
  popover.id = 'compartir-opciones';
  popover.className = 'compartir-opciones';
  popover.hidden = true;
  popover.setAttribute('role', 'menu');
  popover.setAttribute('aria-label', 'Opciones para compartir');
  document.body.appendChild(popover);

  function analytics(method, button) {
    const type = button.dataset.shareType;
    const surface = button.dataset.shareSurface;
    if (type === 'site') {
      window.ExistoAnalytics?.sendEvent('site_share', {share_method: method, share_surface: surface});
      return;
    }
    const context = button.closest('.tarjeta, [data-analytics-article]');
    window.ExistoAnalytics?.sendEvent('article_share', {
      article_slug: button.dataset.shareSlug || context?.dataset.articleSlug,
      article_title: button.dataset.shareTitle || context?.dataset.articleTitle,
      article_topic: context?.dataset.tema || context?.dataset.articleTopic,
      article_type: context?.dataset.tipo || context?.dataset.articleType,
      share_method: method,
      share_surface: surface
    });
  }

  function closePopover(restoreFocus) {
    if (activeButton) activeButton.setAttribute('aria-expanded', 'false');
    popover.hidden = true;
    popover.replaceChildren();
    if (restoreFocus && activeButton) activeButton.focus();
    activeButton = null;
  }

  function placePopover(button) {
    const rect = button.getBoundingClientRect();
    popover.style.left = Math.max(8, Math.min(rect.right - popover.offsetWidth, window.innerWidth - popover.offsetWidth - 8)) + 'px';
    popover.style.top = Math.min(rect.bottom + 6, window.innerHeight - popover.offsetHeight - 8) + 'px';
  }

  function makeLink(label, href, method, button) {
    const link = document.createElement('a');
    link.href = href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.role = 'menuitem';
    link.textContent = label;
    link.addEventListener('click', function () { analytics(method, button); closePopover(false); });
    return link;
  }

  async function copyLink(button, copyButton) {
    const url = button.dataset.shareUrl;
    let copied = false;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        copied = true;
      } else {
        const input = document.createElement('textarea');
        input.value = url;
        input.setAttribute('readonly', '');
        input.style.position = 'fixed';
        input.style.opacity = '0';
        document.body.appendChild(input);
        input.select();
        copied = document.execCommand('copy');
        input.remove();
      }
    } catch (_) {
      copied = false;
    }
    if (!copied) return;
    analytics('copy_link', button);
    copyButton.textContent = 'Enlace copiado';
    window.clearTimeout(feedbackTimer);
    feedbackTimer = window.setTimeout(function () { closePopover(true); }, 1400);
  }

  function openPopover(button) {
    closePopover(false);
    activeButton = button;
    button.setAttribute('aria-expanded', 'true');
    button.setAttribute('aria-controls', popover.id);

    const title = button.dataset.shareTitle;
    const url = button.dataset.shareUrl;
    const copy = document.createElement('button');
    copy.type = 'button';
    copy.role = 'menuitem';
    copy.textContent = 'Copiar enlace';
    copy.addEventListener('click', function () { copyLink(button, copy); });
    popover.append(
      copy,
      makeLink('WhatsApp', 'https://wa.me/?text=' + encodeURIComponent(title + ' ' + url), 'whatsapp', button),
      makeLink('LinkedIn', 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(url), 'linkedin', button),
      makeLink('X / Twitter', 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(title) + '&url=' + encodeURIComponent(url), 'twitter', button)
    );
    popover.hidden = false;
    placePopover(button);
    copy.focus();
  }

  async function share(button) {
    const data = {title: button.dataset.shareTitle, text: button.dataset.shareText, url: button.dataset.shareUrl};
    if (!FORCE_FALLBACK && typeof navigator.share === 'function') {
      try {
        await navigator.share(data);
        analytics('native', button);
        return;
      } catch (error) {
        if (error?.name === 'AbortError') return;
      }
    }
    openPopover(button);
  }

  buttons.forEach(function (button) {
    button.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      share(button);
    });
  });

  document.addEventListener('click', function (event) {
    if (!popover.hidden && !popover.contains(event.target) && event.target !== activeButton) closePopover(false);
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && !popover.hidden) closePopover(true);
  });
  window.addEventListener('resize', function () { if (!popover.hidden && activeButton) placePopover(activeButton); });
  window.addEventListener('scroll', function () { if (!popover.hidden) closePopover(false); }, {passive: true});
})();
