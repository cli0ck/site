/* cli0ck disclosure map — live.
   Every figure in the caption is fetched at page load from the NVD 2.0 API
   (services.nvd.nist.gov, CORS open, no key required). Nothing is simulated:
   the arcs are our own disclosures and the scores are whatever NIST is
   publishing right now. If the API is unreachable the panel falls back to the
   values recorded at build time and says so. */
(function () {
  var cv = document.getElementById('reachmap'); if (!cv) return;
  var ctx = cv.getContext('2d'), COLS = 200, R0 = 6, SPAN = 69;
  var dots = [], ready = false;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* our disclosures. score/status/published are refreshed from NVD below;
     these are the values recorded at build time and used only as a fallback. */
  var CVES = [
    { id: 'CVE-2026-74943', what: 'Use-after-free in RasterImage surface discard', vendor: 'Mozilla Firefox',
      score: '9.8', sev: 'CRITICAL', status: 'Modified',  pub: '2026-08-18' },
    { id: 'CVE-2026-74945', what: 'Uninitialised heap disclosure through a crafted web font', vendor: 'Mozilla Firefox',
      score: '6.5', sev: 'MEDIUM',   status: 'Analyzed',  pub: '2026-08-18' },
    { id: 'CVE-2026-39154', what: 'Stored XSS in CometChat group messages', vendor: 'CometChat',
      score: '',    sev: '',         status: 'Vendor-confirmed', pub: '' },
    { id: 'CVE-2026-74970', what: 'Fission site-isolation bypass via missing PipelineId namespace check', vendor: 'Mozilla Firefox',
      score: '5.4', sev: 'MEDIUM',   status: 'Analyzed',  pub: '2026-08-18' },
    { id: 'CVE-2026-6765',  what: 'Test-only FormAutofill handlers exposed in production', vendor: 'Mozilla Firefox',
      score: '5.3', sev: 'MEDIUM',   status: 'Analyzed',  pub: '2026-04-21' }
  ];

  var DEST = [[-122.1,37.4],[-74.0,40.7],[-99.1,19.4],[-46.6,-23.5],[-0.1,51.5],[13.4,52.5],
              [37.6,55.8],[3.4,6.5],[28.0,-26.2],[72.9,19.1],[103.8,1.4],[116.4,39.9],
              [139.7,35.7],[151.2,-33.9],[174.8,-41.3],[-58.4,-34.6],[31.2,30.0],[55.3,25.2]];
  var ORIGIN = [46.7, 24.7];

  var els = {
    id:   document.getElementById('mapcve'),
    what: document.getElementById('mapwhat'),
    score:document.getElementById('mapscore'),
    stat: document.getElementById('mapstatus'),
    sync: document.getElementById('mapsync'),
    dot:  document.getElementById('mapdot'),
    total:document.getElementById('maptotal')
  };

  /* ---------- live pull from NVD ---------- */
  var NVD = 'https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=';
  var live = 0, tried = 0;

  function setSync(text, ok) {
    if (els.sync) els.sync.textContent = text;
    if (els.dot) els.dot.className = ok ? 'c-live-dot is-live' : 'c-live-dot is-cached';
  }

  function pull(c) {
    return fetch(NVD + c.id, { headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        tried++;
        if (!j || !j.totalResults) return;
        var v = j.vulnerabilities[0].cve, m = v.metrics || {};
        var arr = m.cvssMetricV40 || m.cvssMetricV31 || m.cvssMetricV30 || [];
        var d = (arr[0] || {}).cvssData || {};
        if (d.baseScore != null) { c.score = String(d.baseScore); c.sev = d.baseSeverity || ''; }
        if (v.vulnStatus) c.status = v.vulnStatus;
        if (v.published) c.pub = v.published.slice(0, 10);
        c.liveAt = new Date();
        live++;
      })
      .catch(function () { tried++; });
  }

  function refresh() {
    setSync('syncing…', false);
    Promise.all(CVES.map(pull)).then(function () {
      var t = new Date();
      if (live) {
        setSync('live · NVD · ' + t.toTimeString().slice(0, 8) + ' ' +
                (t.toTimeString().match(/\(([^)]+)\)/) ? '' : 'local'), true);
      } else {
        setSync('offline · showing values recorded at build time', false);
      }
      paint();
    });
    fetch('https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=1')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (j && j.totalResults && els.total)
          els.total.textContent = j.totalResults.toLocaleString('en-US');
      }).catch(function () {});
  }

  /* ---------- map ---------- */
  fetch('assets/world.txt').then(function (r) { return r.text(); }).then(function (t) {
    for (var i = 0; i + 4 <= t.length; i += 4)
      dots.push([parseInt(t.substr(i, 2), 36), parseInt(t.substr(i + 2, 2), 36)]);
    ready = true; resize();
  }).catch(function () {});

  function xy(lon, lat, w, h) {
    return [((lon + 180) / 360 * COLS) / COLS * w, (((90 - lat) / 180 * 92) - R0) / SPAN * h];
  }

  var W = 0, H = 0, dpr = 1;
  function resize() {
    var r = cv.getBoundingClientRect(); if (r.width < 2) return;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = r.width; H = r.height;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  if (window.ResizeObserver) new ResizeObserver(resize).observe(cv);
  else window.addEventListener('resize', resize);

  var arcs = [], idx = -1, t0 = 0;

  function paint() {
    var c = CVES[Math.max(0, idx)];
    if (els.id) els.id.textContent = c.id;
    if (els.what) els.what.textContent = c.what + ' · ' + c.vendor;
    if (els.score) {
      els.score.textContent = c.score ? c.score + ' ' + c.sev : '—';
      els.score.className = 'c-live-score' + (c.sev ? ' sev-' + c.sev.toLowerCase() : '');
    }
    if (els.stat) els.stat.textContent = c.status + (c.pub ? ' · published ' + c.pub : '');
  }

  function fire() {
    idx = (idx + 1) % CVES.length;
    paint();
    DEST.forEach(function (d, k) { arcs.push({ d: d, t: -k * 0.035 }); });
  }

  function draw(ts) {
    if (!ready) { requestAnimationFrame(draw); return; }
    if (!W) resize();
    if (!t0) t0 = ts;
    ctx.clearRect(0, 0, W, H);

    var s = Math.max(1, W / COLS * 0.62);
    ctx.fillStyle = 'rgba(231,229,228,0.10)';
    for (var i = 0; i < dots.length; i++)
      ctx.fillRect(dots[i][0] / COLS * W, (dots[i][1] - R0) / SPAN * H, s, s);

    var o = xy(ORIGIN[0], ORIGIN[1], W, H);
    for (var a = arcs.length - 1; a >= 0; a--) {
      var A = arcs[a];
      A.t += reduce ? 0.02 : 0.011;
      if (A.t < 0) continue;
      if (A.t > 1.6) { arcs.splice(a, 1); continue; }
      var e = xy(A.d[0], A.d[1], W, H);
      var mx = (o[0] + e[0]) / 2,
          my = (o[1] + e[1]) / 2 - Math.hypot(e[0] - o[0], e[1] - o[1]) * 0.32;
      var p = Math.min(1, A.t), ease = 1 - Math.pow(1 - p, 2), fade = A.t > 1 ? Math.max(0, 1 - (A.t - 1) / 0.6) : 1;
      ctx.beginPath(); ctx.moveTo(o[0], o[1]);
      var steps = 26, drawn = Math.max(2, Math.round(steps * ease));
      for (var k = 1; k <= drawn; k++) {
        var u = k / steps, iu = 1 - u;
        ctx.lineTo(iu * iu * o[0] + 2 * iu * u * mx + u * u * e[0],
                   iu * iu * o[1] + 2 * iu * u * my + u * u * e[1]);
      }
      ctx.strokeStyle = 'rgba(245,158,11,' + (0.55 * fade) + ')';
      ctx.lineWidth = 1.1; ctx.stroke();
      if (p >= 1) {
        var pr = (A.t - 1) / 0.6;
        ctx.beginPath(); ctx.arc(e[0], e[1], 2 + pr * 9, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(231,229,228,' + (0.5 * (1 - pr)) + ')'; ctx.lineWidth = 1; ctx.stroke();
        ctx.beginPath(); ctx.arc(e[0], e[1], 1.7, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(231,229,228,' + (0.85 * fade) + ')'; ctx.fill();
      }
    }

    var pulse = reduce ? 0.5 : (Math.sin(ts / 620) + 1) / 2;
    ctx.beginPath(); ctx.arc(o[0], o[1], 3.2 + pulse * 4.5, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(245,158,11,' + (0.42 - pulse * 0.24) + ')'; ctx.lineWidth = 1.2; ctx.stroke();
    ctx.beginPath(); ctx.arc(o[0], o[1], 2.6, 0, Math.PI * 2);
    ctx.fillStyle = '#f59e0b'; ctx.fill();

    if (ts - t0 > (reduce ? 6500 : 4600)) { t0 = ts; fire(); }
    requestAnimationFrame(draw);
  }

  refresh();
  setInterval(refresh, 15 * 60 * 1000);   /* re-sync every 15 minutes */
  fire();
  requestAnimationFrame(draw);
})();
