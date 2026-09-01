/* cli0ck contact form.
   Posts to Web3Forms, which relays to info@cli0ck.com with the sender's
   address as Reply-To. The visitor never leaves the page and signs into
   nothing. Field names are chosen and ordered so the email that lands in
   the inbox reads as a tidy briefing rather than a dump of inputs. */
(function () {
  var f = document.getElementById('contactform');
  if (!f) return;

  var btn  = f.querySelector('.c-submit'),
      lbl  = btn.querySelector('.txt'),
      box  = document.getElementById('formstatus'),
      prog = document.getElementById('cprog'),
      MAIL = '<a class="hover:underline text-accent" href="mailto:info@cli0ck.com">info@cli0ck.com</a>';

  var g = function (k) {
    var el = f.elements[k];
    return el ? (el.value || '').trim() : '';
  };

  /* ---------- motion: progress, ticks, counter ---------- */
  var required = ['name', 'email', 'message'];

  function fieldOf(el) {
    while (el && !el.classList.contains('c-field')) el = el.parentElement;
    return el;
  }

  function valid(k) {
    var v = g(k);
    if (k === 'email') return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
    if (k === 'message') return v.length >= 20;
    return v.length > 0;
  }

  function refresh() {
    var done = 0;
    required.forEach(function (k) {
      var el = f.elements[k], fd = fieldOf(el);
      if (!fd) return;
      var ok = valid(k);
      fd.classList.toggle('is-done', ok);
      if (ok) done++;
    });
    if (prog) prog.style.width = Math.round((done / required.length) * 100) + '%';

    var msg = f.elements.message, c = document.getElementById('ccount');
    if (msg && c) {
      var n = msg.value.trim().length;
      c.textContent = n < 20 ? (20 - n) + ' more' : n + ' characters';
      c.classList.toggle('ready', n >= 20);
    }
  }

  // counter lives under the message box
  var msgField = fieldOf(f.elements.message);
  if (msgField) {
    var c = document.createElement('span');
    c.className = 'c-count'; c.id = 'ccount'; c.textContent = '20 more';
    msgField.appendChild(c);
  }

  f.addEventListener('input', refresh);
  f.addEventListener('change', refresh);
  refresh();

  /* ---------- submit ---------- */
  function show(kind, title, body) {
    box.className = 'c-status show ' + kind;
    box.innerHTML = '<b>' + title + '</b>' + body;
    box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  function shake(k) {
    var el = f.elements[k];
    if (el) { el.focus(); }
  }

  f.addEventListener('submit', function (e) {
    e.preventDefault();
    if (f.elements.botcheck && f.elements.botcheck.checked) return;   // honeypot

    if (!g('name'))            { shake('name');    return show('err', 'Almost', 'We need a name to reply to.'); }
    if (!valid('email'))       { shake('email');   return show('err', 'Check the email', 'That address does not look right.'); }
    if (!valid('message'))     { shake('message'); return show('err', 'Tell us a bit more', 'Twenty characters minimum &mdash; it makes our reply useful.'); }

    var now = new Date();
    var stamp = now.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';

    /* Web3Forms prints the fields in the order it receives them, so the keys
       are named and ordered to read as a briefing in the inbox. */
    var payload = {
      access_key: f.dataset.key,
      subject: 'cli0ck enquiry — ' + g('topic') + ' — ' + g('name'),
      from_name: 'cli0ck.com',
      replyto: g('email'),

      '── ENQUIRY ─────────────': g('topic'),
      'From': g('name'),
      'Email': g('email'),
      'Company or team': g('company') || '—',
      'Received': stamp,
      '── MESSAGE ─────────────': ' ',
      'Their message': g('message'),
      '── ': ' ',
      'Reply to': g('email') + '  (just hit reply)',
      'Sent from': 'cli0ck.com/contact'
    };

    btn.disabled = true;
    btn.classList.add('is-busy');
    lbl.textContent = 'Sending';
    box.className = 'c-status';

    fetch('https://api.web3forms.com/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok && res.j.success) {
          f.reset(); refresh();
          btn.classList.remove('is-busy');
          btn.classList.add('is-sent');
          lbl.textContent = 'Sent';
          show('ok', 'Sent &mdash; thank you',
               'It is in our inbox. We read every message ourselves and reply to the address you gave.');
          setTimeout(function () {
            btn.classList.remove('is-sent');
            lbl.textContent = 'Send message';
            btn.disabled = false;
          }, 3200);
        } else {
          btn.classList.remove('is-busy');
          lbl.textContent = 'Send message';
          btn.disabled = false;
          show('err', 'Not sent', 'Something went wrong on the way. Email ' + MAIL + ' and it will still reach us.');
        }
      })
      .catch(function () {
        btn.classList.remove('is-busy');
        lbl.textContent = 'Send message';
        btn.disabled = false;
        show('err', 'Could not reach us', 'Check your connection, or email ' + MAIL + ' directly.');
      });
  });
})();
