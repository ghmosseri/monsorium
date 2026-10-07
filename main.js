/* =========================================================
   MONSORIUM — main.js  (animations)
   1. Home light flicker + the visitor's on/off toggle (remembered)
   2. Slide-ins for the Alleyway exhibit
   3. Current-section highlight in the nav
   4. Multimedia posters that appear once a file is added
   5. Sticky masthead height (so section links land below it)
   6. Text carousels: The Heretic, and the Bottles at Sea reading room
   7. The Alleyway viewing room (art.html)
   8. The commission dialog (Conches)
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
     4. OPTIONAL IMAGES (video posters): drop the <img> if the file
        isn't there yet, so the designed title card shows instead.
     ======================================================= */
  function initVideoSlots() {
    document.querySelectorAll('img[data-optional]').forEach(function (img) {
      function drop() { img.remove(); }
      img.addEventListener('error', drop);
      if (img.complete && img.naturalWidth === 0 && img.getAttribute('loading') !== 'lazy') drop();
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

  /* =======================================================
     7. ART VIEWER (art.html): one clay frame in the middle; the
        neighbours wait at the sides, angled in perspective and
        blurred by distance. The frame takes each piece's
        proportions; the room advances by itself.
     ======================================================= */
  function initArtViewer() {
    var viewer = document.querySelector('[data-artviewer]');
    if (!viewer) return;
    var stage = viewer.querySelector('.viewer__stage');
    var ghostsBox = viewer.querySelector('.viewer__ghosts');
    var pieces = Array.prototype.slice.call(viewer.querySelectorAll('.art-piece'));
    var n = pieces.length;
    if (!n) return;
    var interval = (+viewer.getAttribute('data-interval') || 17) * 1000;
    var pauseBtn = viewer.querySelector('[data-art-pause]');
    var cap = {
      no: viewer.querySelector('[data-art-no]'), title: viewer.querySelector('[data-art-title]'),
      date: viewer.querySelector('[data-art-date]'), medium: viewer.querySelector('[data-art-medium]')
    };
    var current = 0, paused = false, timer = null, aw = 0, ah = 0;

    var ghosts = pieces.map(function (fig) {
      var g = document.createElement('div');
      g.className = 'art-ghost';
      var img = document.createElement('img');
      img.src = fig.querySelector('img').getAttribute('src');
      img.alt = '';
      img.loading = 'lazy';
      g.appendChild(img);
      g.addEventListener('click', function () { go(pieces.indexOf(fig)); });
      ghostsBox.appendChild(g);
      return g;
    });

    function ratio(k) { return (+pieces[k].getAttribute('data-w')) / (+pieces[k].getAttribute('data-h')); }

    // Fit the current piece into the room; the frame animates to that size.
    function fit() {
      var w = stage.clientWidth, narrow = w < 760;
      var maxW = w * (narrow ? 0.66 : 0.44);
      var maxH = Math.min(window.innerHeight * (narrow ? 0.46 : 0.5), 600);
      var r = ratio(current);
      if (maxW / maxH > r) { ah = maxH; aw = maxH * r; } else { aw = maxW; ah = maxW / r; }
      viewer.style.setProperty('--aw', Math.round(aw) + 'px');
      viewer.style.setProperty('--ah', Math.round(ah) + 'px');
      place();
    }

    // Lay out the neighbours: nearer ones slightly blurred, farther ones more.
    function place() {
      var narrow = stage.clientWidth < 760;
      var gh = ah * (narrow ? 0.8 : 0.9);
      var s1 = narrow ? 0.62 : 0.72, s2 = narrow ? 0.44 : 0.5;
      var edge = aw / 2 + (narrow ? 26 : 70);
      ghosts.forEach(function (g, k) {
        var d = (k - current + n) % n;
        if (d > n / 2) d -= n;
        var side = d < 0 ? -1 : 1, a = Math.abs(d);
        var gw = gh * ratio(k);
        g.style.height = Math.round(gh) + 'px';
        g.style.width = Math.round(gw) + 'px';
        var x, ry, s, blur, op, z;
        if (a === 0) { x = 0; ry = 0; s = 0.86; blur = 0; op = 0; z = 1; }
        else if (a === 1) { x = edge + gw * s1 * 0.38; ry = 40; s = s1; blur = 2.5; op = 0.92; z = 4; }
        else if (a === 2) { x = edge + gw * s1 * 0.62 + gw * s2 * 0.42 + 24; ry = 56; s = s2; blur = 8; op = 0.7; z = 3; }
        else { x = edge + gw * 1.3 + 120; ry = 64; s = 0.3; blur = 12; op = 0; z = 2; }
        g.style.transform = 'translate(-50%, -50%) translateX(' + Math.round(side * x) + 'px) rotateY(' + (-side * ry) + 'deg) scale(' + s + ')';
        g.style.filter = 'blur(' + blur + 'px)';
        g.style.opacity = op;
        g.style.zIndex = z;
        g.classList.toggle('is-near', a === 1 || a === 2);
      });
    }

    function show(i, fromHash) {
      current = (i + n) % n;
      pieces.forEach(function (p, k) {
        p.classList.toggle('is-current', k === current);
        p.setAttribute('aria-hidden', k === current ? 'false' : 'true');
      });
      var p = pieces[current];
      cap.no.textContent = p.getAttribute('data-no') + '.';
      cap.title.textContent = p.getAttribute('data-title');
      cap.title.classList.toggle('untitled', p.getAttribute('data-title') === 'Untitled');
      cap.date.textContent = p.getAttribute('data-date');
      cap.date.setAttribute('datetime', p.getAttribute('data-iso'));
      cap.medium.textContent = p.getAttribute('data-medium');
      fit();
      if (!fromHash && history.replaceState) history.replaceState(null, '', '#' + p.id);
    }

    function restart() {
      clearInterval(timer);
      if (!paused) timer = setInterval(function () { if (!document.hidden) show(current + 1); }, interval);
    }
    function go(i) { show(i); restart(); }

    viewer.querySelector('[data-art-prev]').addEventListener('click', function () { go(current - 1); });
    viewer.querySelector('[data-art-next]').addEventListener('click', function () { go(current + 1); });
    viewer.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { go(current - 1); e.preventDefault(); }
      if (e.key === 'ArrowRight') { go(current + 1); e.preventDefault(); }
    });
    if (pauseBtn) pauseBtn.addEventListener('click', function () {
      paused = !paused;
      pauseBtn.setAttribute('aria-pressed', paused ? 'true' : 'false');
      pauseBtn.textContent = paused ? 'Play slideshow' : 'Pause slideshow';
      restart();
    });
    window.addEventListener('resize', fit);
    window.addEventListener('hashchange', function () {
      for (var k = 0; k < n; k++) if ('#' + pieces[k].id === location.hash) { show(k, true); restart(); }
    });

    var start = 0;
    for (var k = 0; k < n; k++) if ('#' + pieces[k].id === location.hash) start = k;
    viewer.classList.add('is-ready');
    show(start, true);
    restart();
    if (location.hash) {
      var settle = function () {
        var mast = document.querySelector('.masthead');
        var y = viewer.getBoundingClientRect().top + window.pageYOffset - (mast ? mast.offsetHeight : 0) - 12;
        window.scrollTo(0, Math.max(0, y));
      };
      settle();
      window.addEventListener('load', function () { setTimeout(settle, 0); });
    }
  }

  /* =======================================================
     8. COMMISSION DIALOG (Conches)
     ======================================================= */
  function initCommission() {
    var dialog = document.getElementById('commission');
    var openers = document.querySelectorAll('[data-commission-open]');
    if (!dialog || typeof dialog.showModal !== 'function') {
      // Very old browsers: show the form inline instead of as a dialog.
      if (dialog) dialog.setAttribute('open', '');
      openers.forEach(function (b) { b.hidden = true; });
      return;
    }
    openers.forEach(function (b) {
      b.addEventListener('click', function () { dialog.showModal(); dialog.querySelector('input:not([type=hidden])').focus(); });
    });
    dialog.querySelectorAll('[data-commission-close]').forEach(function (b) {
      b.addEventListener('click', function () { dialog.close(); });
    });
    dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.close(); });

    // FormSubmit sends the visitor back here with #commission-sent.
    var toast = document.querySelector('[data-commission-sent]');
    if (toast && location.hash === '#commission-sent') {
      toast.hidden = false;
      setTimeout(function () { toast.hidden = true; }, 7000);
      if (history.replaceState) history.replaceState(null, '', location.pathname + '#conches');
    }
  }

  function init() {
    initMasthead();
    initFlicker();
    initSlideIns();
    initNavState();
    initVideoSlots();
    initCarousels();
    initArtViewer();
    initCommission();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
