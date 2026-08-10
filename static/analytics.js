(function () {
  'use strict';

  const DEBUG = new URLSearchParams(window.location.search).get('analytics_debug') === '1';
  const article = document.querySelector('[data-analytics-article]');

  function sendEvent(name, parameters) {
    const payload = Object.assign({}, parameters || {});
    Object.keys(payload).forEach(function (key) {
      if (payload[key] === undefined || payload[key] === '') delete payload[key];
    });
    if (DEBUG) {
      payload.debug_mode = true;
      console.info('[Existo analytics]', name, payload);
    }
    try {
      if (typeof window.gtag === 'function') window.gtag('event', name, payload);
    } catch (_) {
      // Analytics nunca debe afectar la lectura si gtag falla o es bloqueado.
    }
  }

  window.ExistoAnalytics = Object.freeze({sendEvent: sendEvent});

  if (!article) return;

  const body = article.querySelector('[data-article-body]');
  if (!body) return;

  const numberValue = function (value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  };
  const metadata = {
    article_slug: article.dataset.articleSlug,
    article_title: article.dataset.articleTitle,
    article_date: article.dataset.articleDate,
    article_topic: article.dataset.articleTopic,
    article_type: article.dataset.articleType,
    word_count: numberValue(article.dataset.articleWordCount),
    estimated_read_time: numberValue(article.dataset.articleEstimatedReadTime)
  };
  Object.keys(metadata).forEach(function (key) {
    if (metadata[key] === undefined || metadata[key] === '') delete metadata[key];
  });

  sendEvent('article_open', metadata);

  const reached = new Set();
  const checkpoints = [25, 50, 75, 90, 100];
  let scheduled = false;

  function measureDepth() {
    scheduled = false;
    const rect = body.getBoundingClientRect();
    const height = Math.max(body.scrollHeight, rect.height, 1);
    const reachedPixels = Math.min(Math.max(window.innerHeight - rect.top, 0), height);
    const percent = (reachedPixels / height) * 100;

    checkpoints.forEach(function (checkpoint) {
      if (percent < checkpoint || reached.has(checkpoint)) return;
      reached.add(checkpoint);
      const eventName = checkpoint === 100 ? 'article_complete' : 'article_' + checkpoint;
      sendEvent(eventName, metadata);
    });
  }

  function scheduleDepthMeasurement() {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(measureDepth);
  }

  window.addEventListener('scroll', scheduleDepthMeasurement, {passive: true});
  window.addEventListener('resize', scheduleDepthMeasurement, {passive: true});
  scheduleDepthMeasurement();

  let activeStartedAt = null;
  let activeMilliseconds = 0;
  let sentMilliseconds = 0;

  function isActive() {
    return document.visibilityState === 'visible' && document.hasFocus();
  }

  function updateActiveClock() {
    const now = performance.now();
    if (activeStartedAt !== null) {
      activeMilliseconds += Math.max(0, now - activeStartedAt);
      activeStartedAt = null;
    }
    if (isActive()) activeStartedAt = now;
  }

  function flushActiveTime(reason) {
    updateActiveClock();
    const unsentSeconds = Math.floor((activeMilliseconds - sentMilliseconds) / 1000);
    if (unsentSeconds < 1) return;
    sentMilliseconds += unsentSeconds * 1000;
    sendEvent('article_active_time', {
      article_slug: metadata.article_slug,
      article_title: metadata.article_title,
      active_seconds: unsentSeconds,
      word_count: metadata.word_count,
      estimated_read_time: metadata.estimated_read_time,
      send_reason: reason,
      transport_type: reason === 'checkpoint' ? undefined : 'beacon'
    });
  }

  updateActiveClock();
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') flushActiveTime('hidden');
    else updateActiveClock();
  });
  window.addEventListener('focus', updateActiveClock);
  window.addEventListener('blur', function () { flushActiveTime('blur'); });
  window.addEventListener('pagehide', function () { flushActiveTime('pagehide'); });
  window.setInterval(function () { flushActiveTime('checkpoint'); }, 30000);

  document.addEventListener('click', function (event) {
    const link = event.target.closest('a[href]');
    if (!link) return;

    let destination;
    try { destination = new URL(link.href, window.location.href); }
    catch (_) { return; }

    const current = new URL(window.location.href);
    const match = destination.pathname.match(/\/escritos\/([^/]+)\.html$/);
    const currentMatch = current.pathname.match(/\/escritos\/([^/]+)\.html$/);
    if (!match || destination.origin !== current.origin || (currentMatch && match[1] === currentMatch[1])) return;

    const destinationTitle = link.dataset.articleTitle || link.textContent.trim();
    const nextParameters = {
      source_article_slug: metadata.article_slug,
      source_article_title: metadata.article_title,
      destination_article_slug: decodeURIComponent(match[1]),
      link_location: link.closest('article') ? 'article' : link.closest('header') ? 'header' : link.closest('footer') ? 'footer' : 'page'
    };
    if (destinationTitle) nextParameters.destination_article_title = destinationTitle;
    sendEvent('article_next', nextParameters);
  });
})();
