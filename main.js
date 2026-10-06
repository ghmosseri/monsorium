/* =========================================================
   MONSORIUM — main.js  (animations)
   1. Home light flicker + the visitor's on/off toggle (remembered)
   2. Slide-ins for the Alleyway exhibit
   3. Current-section highlight in the nav
   4. Multimedia video slots that show blank until a file is added
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
    links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });

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

  function init() {
    initFlicker();
    initSlideIns();
    initNavState();
    initVideoSlots();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
