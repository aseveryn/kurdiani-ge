// kurdiani.ge — lightbox, mobile nav, back-to-top, page fade
(function () {
  'use strict';

  document.body.classList.add('loaded');

  var T = window.__i18n || {
    lightbox: 'Image viewer', prev: 'Previous image',
    next: 'Next image', close: 'Close'
  };
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function scrollToTop(e) {
    if (e) e.preventDefault();
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  }

  // ----- mobile nav -----
  var burger = document.querySelector('.hamburger');
  var rnav = document.querySelector('.responsive-nav');
  if (burger && rnav) {
    var closeBtn = rnav.querySelector('.close-nav');
    var openNav = function () {
      rnav.classList.add('open');
      document.body.classList.add('nav-open');
      burger.setAttribute('aria-expanded', 'true');
      if (closeBtn) closeBtn.focus();
    };
    var closeNav = function () {
      rnav.classList.remove('open');
      document.body.classList.remove('nav-open');
      burger.setAttribute('aria-expanded', 'false');
      burger.focus();
    };
    burger.addEventListener('click', openNav);
    if (closeBtn) closeBtn.addEventListener('click', closeNav);
    rnav.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeNav();
    });
  }

  // ----- fixed back-to-top -----
  var btt = document.querySelector('.btt-fixed');
  if (btt) {
    var onScroll = function () {
      btt.classList.toggle('show', window.scrollY > window.innerHeight);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    btt.addEventListener('click', scrollToTop);
  }
  var bttInline = document.querySelector('.back-to-top a');
  if (bttInline) bttInline.addEventListener('click', scrollToTop);

  // ----- lightbox -----
  var slides = Array.prototype.slice.call(document.querySelectorAll('[data-lightbox]'));
  if (!slides.length) return;

  var lb = document.createElement('div');
  lb.className = 'lightbox';
  lb.setAttribute('role', 'dialog');
  lb.setAttribute('aria-modal', 'true');
  lb.setAttribute('aria-label', T.lightbox);
  lb.hidden = true;
  lb.innerHTML =
    '<img alt="">' +
    '<button type="button" class="lb-prev" aria-label="' + T.prev + '">' +
      '<svg viewBox="0 0 60 60" aria-hidden="true"><circle class="lb-arrow-bg" cx="30" cy="30" r="30"/>' +
      '<path class="lb-arrow" d="M34.6 18.2 22.8 30l11.8 11.8 2.1-2.1L27 30l9.7-9.7z"/></svg></button>' +
    '<button type="button" class="lb-next" aria-label="' + T.next + '">' +
      '<svg viewBox="0 0 60 60" aria-hidden="true"><circle class="lb-arrow-bg" cx="30" cy="30" r="30"/>' +
      '<path class="lb-arrow" d="M25.4 18.2 37.2 30 25.4 41.8l-2.1-2.1L33 30l-9.7-9.7z"/></svg></button>' +
    '<button type="button" class="lb-close" aria-label="' + T.close + '"></button>';
  document.body.appendChild(lb);

  var lbImg = lb.querySelector('img');
  var prevBtn = lb.querySelector('.lb-prev');
  var nextBtn = lb.querySelector('.lb-next');
  var closeLbBtn = lb.querySelector('.lb-close');
  var idx = -1;
  var lastFocus = null;

  function show(i) {
    idx = (i + slides.length) % slides.length;
    var src = slides[idx];
    lbImg.src = src.getAttribute('data-lightbox');
    // carry the thumbnail's description over to the enlarged image
    lbImg.alt = src.getAttribute('alt') || '';
  }

  function open(i) {
    lastFocus = document.activeElement;
    show(i);
    lb.hidden = false;
    lb.classList.add('open');
    document.body.classList.add('lightbox-open');
    closeLbBtn.focus();
  }

  function hide() {
    lb.classList.remove('open');
    lb.hidden = true;
    document.body.classList.remove('lightbox-open');
    idx = -1;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  slides.forEach(function (el, i) {
    el.addEventListener('click', function () { open(i); });
    // the triggers are <img role="button" tabindex="0">, so they need the
    // keyboard activation a real button would give for free
    el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault();
        open(i);
      }
    });
  });

  prevBtn.addEventListener('click', function (e) { e.stopPropagation(); show(idx - 1); });
  nextBtn.addEventListener('click', function (e) { e.stopPropagation(); show(idx + 1); });
  closeLbBtn.addEventListener('click', hide);
  lb.addEventListener('click', function (e) {
    if (e.target === lb || e.target === lbImg) hide();
  });

  document.addEventListener('keydown', function (e) {
    if (idx < 0) return;
    if (e.key === 'Escape') { hide(); return; }
    if (e.key === 'ArrowLeft') { show(idx - 1); return; }
    if (e.key === 'ArrowRight') { show(idx + 1); return; }
    // keep Tab inside the dialog while it is open
    if (e.key === 'Tab') {
      var focusable = [prevBtn, nextBtn, closeLbBtn];
      var at = focusable.indexOf(document.activeElement);
      var next = e.shiftKey ? at - 1 : at + 1;
      if (at === -1 || next < 0 || next >= focusable.length) {
        e.preventDefault();
        focusable[e.shiftKey ? focusable.length - 1 : 0].focus();
      }
    }
  });

  // swipe to move between images on touch devices
  var touchX = null, touchY = null;
  lb.addEventListener('touchstart', function (e) {
    if (e.changedTouches.length !== 1) return;
    touchX = e.changedTouches[0].clientX;
    touchY = e.changedTouches[0].clientY;
  }, { passive: true });
  lb.addEventListener('touchend', function (e) {
    if (touchX === null || idx < 0) return;
    var dx = e.changedTouches[0].clientX - touchX;
    var dy = e.changedTouches[0].clientY - touchY;
    touchX = touchY = null;
    // ignore mostly-vertical drags so scrolling gestures don't page around
    if (Math.abs(dx) < 45 || Math.abs(dx) < Math.abs(dy)) return;
    show(dx < 0 ? idx + 1 : idx - 1);
  }, { passive: true });
})();
