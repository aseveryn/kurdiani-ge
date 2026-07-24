// kurdiani.ge — lightbox, mobile nav, back-to-top, page fade
(function () {
  'use strict';

  document.body.classList.add('loaded');

  // ----- mobile nav -----
  var burger = document.querySelector('.hamburger');
  var rnav = document.querySelector('.responsive-nav');
  if (burger && rnav) {
    burger.addEventListener('click', function () {
      rnav.classList.add('open');
      document.body.classList.add('nav-open');
    });
    rnav.querySelector('.close-nav').addEventListener('click', function () {
      rnav.classList.remove('open');
      document.body.classList.remove('nav-open');
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
    btt.addEventListener('click', function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
  var bttInline = document.querySelector('.back-to-top a');
  if (bttInline) {
    bttInline.addEventListener('click', function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ----- lightbox -----
  var slides = Array.prototype.slice.call(document.querySelectorAll('[data-lightbox]'));
  if (!slides.length) return;

  var lb = document.createElement('div');
  lb.className = 'lightbox';
  lb.innerHTML =
    '<img alt="">' +
    '<div class="lb-prev"><svg viewBox="0 0 60 60"><circle class="lb-arrow-bg" cx="30" cy="30" r="30"/><path class="lb-arrow" d="M34.6 18.2 22.8 30l11.8 11.8 2.1-2.1L27 30l9.7-9.7z"/></svg></div>' +
    '<div class="lb-next"><svg viewBox="0 0 60 60"><circle class="lb-arrow-bg" cx="30" cy="30" r="30"/><path class="lb-arrow" d="M25.4 18.2 37.2 30 25.4 41.8l-2.1-2.1L33 30l-9.7-9.7z"/></svg></div>' +
    '<div class="lb-close"></div>';
  document.body.appendChild(lb);
  var lbImg = lb.querySelector('img');
  var idx = -1;

  function show(i) {
    idx = (i + slides.length) % slides.length;
    lbImg.src = slides[idx].getAttribute('data-lightbox');
    lb.classList.add('open');
    document.body.classList.add('lightbox-open');
  }
  function hide() {
    lb.classList.remove('open');
    document.body.classList.remove('lightbox-open');
    idx = -1;
  }

  slides.forEach(function (el, i) {
    el.addEventListener('click', function () { show(i); });
  });
  lb.querySelector('.lb-prev').addEventListener('click', function (e) { e.stopPropagation(); show(idx - 1); });
  lb.querySelector('.lb-next').addEventListener('click', function (e) { e.stopPropagation(); show(idx + 1); });
  lb.querySelector('.lb-close').addEventListener('click', hide);
  lb.addEventListener('click', function (e) {
    if (e.target === lb || e.target === lbImg) hide();
  });
  document.addEventListener('keydown', function (e) {
    if (idx < 0) return;
    if (e.key === 'Escape') hide();
    else if (e.key === 'ArrowLeft') show(idx - 1);
    else if (e.key === 'ArrowRight') show(idx + 1);
  });
})();
