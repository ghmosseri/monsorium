/* =========================================================
   MONSORIUM — main.js  (animations)
   1. Home light flicker + the visitor's on/off toggle (remembered)
   2. Slide-ins for the Alleyway exhibit
   3. Current-section highlight in the nav
   4. Multimedia video slots that show blank until a file is added
   5. Sticky masthead height (so section links land below it)
   6. Text carousels: The Heretic, and the Bottles at Sea reading room
   ========================================================= */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* storage can be blocked (private windows, strict settings) */
  var STORE_KEY = 'monsorium:flicker';
  function readPref() {
    try { return window.localStorage.getItem(STORE_KEY); } catch (e) { return null; }
  }
  function writePref(value) {
    try { window.localStorage.setItem(STORE_KEY, value); } catch (e) { /* ignore */ }
  }

  /* =======================================================
     1. FLICKER (home only)
     ======================================================= */
  function initFlicker() {
    var home = document.getElementById('home');
    var toggle = document.querySelector('[data-flicker-toggle]');
    if (!home || !toggle) return;

    var stateLabel = toggle.querySelector('[data-flicker-state]');
    var light = home.querySelector('.home__light');
    var words = home.querySelectorAll('.title .w');
    var timer = null;
    var homeVisible = true;

    function rand(min, max) { return min + Math.random() * (max - min); }

    // One "event": the light wash blinks once or twice, and a word may stutter.
    function burst() {
      if (!light) return;
      var flashes = Math.random() < 0.35 ? 2 : 1;
      var t = 0;
      for (var i = 0; i < flashes; i++) {
        (function (delay) {
          setTimeout(function () { light.classList.add('is-flash'); }, delay);
          setTimeout(function () { light.classList.remove('is-flash'); }, delay + rand(50, 140));
        })(t);
        t += rand(160, 260);
      }
      if (words.length && Math.random() < 0.5) {
        var w = words[Math.floor(Math.random() * words.length)];
        w.classList.add('is-stutter');
        setTimeout(function () { w.classList.remove('is-stutter'); }, rand(70, 160));
      }
    }

    function schedule() {
      timer = setTimeout(function () {
        if (homeVisible && !document.hidden) burst();
        schedule();
      }, rand(900, 3800));
    }

    function setFlicker(on, remember) {
      home.classList.toggle('is-flickering', on);
      home.classList.toggle('is-static', !on);
      toggle.setAttribute('aria-pressed', on ? 'true' : 'false');
      if (stateLabel) stateLabel.textContent = on ? 'on' : 'off';
      clearTimeout(timer);
      timer = null;
      if (light) light.classList.remove('is-flash');
      if (on) schedule();
      if (remember) writePref(on ? 'on' : 'off');
    }

    toggle.addEventListener('click', function () {
      setFlicker(toggle.getAttribute('aria-pressed') !== 'true', true);
    });

    // Only flash while the home section is on screen.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        homeVisible = entries[0].isIntersecting;
      }, { threshold: 0.05 }).observe(home);
    }

    // Default: on, unless the visitor prefers reduced motion. A saved choice wins.
    var saved = readPref();
    setFlicker(saved ? saved === 'on' : !reduceMotion, false);
  }

  /* =======================================================
     2. SLIDE-INS (the Alleyway)
     ======================================================= */
  function initSlideIns() {
    // Titles are fully clipped until revealed, so watch their gallery instead.
    var targets = document.querySelectorAll('#alleyway .tile, #alleyway .gallery');
    if (!targets.length) return;

    if (reduceMotion || !('IntersectionObserver' in window)) {
      document.querySelectorAll('#alleyway .tile, #alleyway .gallery__title').forEach(function (t) { t.classList.add('is-in'); });
      return;
    }

    // Stagger within each row of a gallery.
    document.querySelectorAll('#alleyway .tiles').forEach(function (list) {
      Array.prototype.forEach.call(list.children, function (tile, i) {
        tile.style.setProperty('--delay', (i % 4) * 120 + 'ms');
      });
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var title = entry.target.querySelector(':scope > .gallery__title');
          (title || entry.target).classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });

    targets.forEach(function (t) { io.observe(t); });
  }

  /* =======================================================
     3. NAV: mark the section in view
     ======================================================= */
  function initNavState() {
    if (!('IntersectionObserver' in window)) return;
    var links = document.querySelectorAll('.nav-list .nav-btn');
    var map = {};
    links.forEach(function (a) {
      // Only links to sections on this page (the reading room links back to index.html).
      if (a.pathname === location.pathname && a.hash) map[a.hash.slice(1)] = a;
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (a) { a.removeAttribute('aria-current'); });
        var link = map[entry.target.id];
        if (link) link.setAttribute('aria-current', 'true');
      });
    }, { rootMargin: '-45% 0px -50% 0px' });

    Object.keys(map).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) io.observe(el);
    });
  }

  /* =======================================================
     4. VIDEO SLOTS (Multimedia): blank frame until the file exists
     ======================================================= */
  function initVideoSlots() {
    document.querySelectorAll('video[data-video-slot]').forEach(function (video) {
      var tile = video.closest('.tile');
      var sources = video.querySelectorAll('source');
      function markEmpty() { if (tile) tile.classList.add('is-empty'); }
      function markFilled() { if (tile) tile.classList.remove('is-empty'); }
      // A missing file errors on its <source>, not on the <video>.
      if (sources.length) sources[sources.length - 1].addEventListener('error', markEmpty);
      video.addEventListener('error', markEmpty);
      video.addEventListener('loadedmetadata', markFilled);
      // The error may have fired before this script ran.
      if (video.networkState === 3 /* NETWORK_NO_SOURCE */) markEmpty();
    });
  }

  /* =======================================================
     5. MASTHEAD: the ribbon + nav stick to the top; keep section
        links landing below it by tracking its height.
     ======================================================= */
  function initMasthead() {
    var mast = document.querySelector('.masthead');
    if (!mast) return;
    function measure() {
      document.documentElement.style.setProperty('--mast-h', mast.offsetHeight + 'px');
    }
    measure();
    window.addEventListener('resize', measure);
    if ('ResizeObserver' in window) new ResizeObserver(measure).observe(mast);
  }

  /* =======================================================
     6. CAROUSELS: The Heretic's three parts, the poem reading room.
        One slide shows at a time; arrows, arrow keys and the
        contents list move between them. With data-carousel-hash the
        current slide follows the URL (#slug), so bottles link in.
     ======================================================= */
  function initCarousels() {
    var ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV'];
    document.querySelectorAll('[data-carousel]').forEach(function (car) {
      var slides = car.querySelectorAll('.carousel__slide');
      var counts = car.querySelectorAll('[data-carousel-count]');
      var prev = car.querySelector('[data-carousel-prev]');
      var next = car.querySelector('[data-carousel-next]');
      var useHash = car.hasAttribute('data-carousel-hash');
      var gotos = document.querySelectorAll('[data-carousel-goto]');
      var current = 0;
      if (!slides.length) return;

      function show(i, fromHash) {
        current = (i + slides.length) % slides.length;
        slides.forEach(function (s, k) { s.classList.toggle('is-current', k === current); });
        counts.forEach(function (c) { c.textContent = ROMAN[current] + ' / ' + ROMAN[slides.length - 1]; });
        gotos.forEach(function (g) {
          if (+g.getAttribute('data-carousel-goto') === current) g.setAttribute('aria-current', 'true');
          else g.removeAttribute('aria-current');
        });
        if (useHash && !fromHash && slides[current].id && history.replaceState) {
          history.replaceState(null, '', '#' + slides[current].id);
        }
      }
      function indexOfHash() {
        var id = decodeURIComponent(location.hash.slice(1));
        for (var k = 0; k < slides.length; k++) if (slides[k].id === id) return k;
        return -1;
      }

      car.classList.add('is-ready');
      if (prev) prev.addEventListener('click', function () { show(current - 1); });
      if (next) next.addEventListener('click', function () { show(current + 1); });
      car.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') { show(current - 1); e.preventDefault(); }
        if (e.key === 'ArrowRight') { show(current + 1); e.preventDefault(); }
      });
      gotos.forEach(function (g) {
        g.addEventListener('click', function (e) {
          e.preventDefault();
          show(+g.getAttribute('data-carousel-goto'));
          car.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
        });
      });
      if (useHash) {
        window.addEventListener('hashchange', function () { var k = indexOfHash(); if (k >= 0) show(k, true); });
        var start = indexOfHash();
        show(start >= 0 ? start : 0, true);
        if (start >= 0) {
          // The browser jumps to the #slug slide on load; settle the whole
          // carousel just below the sticky masthead instead.
          var settle = function () {
            var mast = document.querySelector('.masthead');
            var y = car.getBoundingClientRect().top + window.pageYOffset - (mast ? mast.offsetHeight : 0) - 12;
            window.scrollTo(0, Math.max(0, y));
          };
          settle();
          window.addEventListener('load', function () { setTimeout(settle, 0); });
        }
      } else {
        show(0, true);
      }
    });
  }

  function init() {
    initMasthead();
    initFlicker();
    initSlideIns();
    initNavState();
    initVideoSlots();
    initCarousels();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
