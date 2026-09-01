/* cli0ck contact form — posts to the Worker at form.cli0ck.com.
   No credentials here; the endpoint holds them. */
(function () {
  var f = document.getElementById('contactform');
  if (!f) return;
  var btn = f.querySelector('.c-submit'),
      lbl = btn.querySelector('.txt'),
      box = document.getElementById('formstatus');

  var MSG = {
    missing_fields:    'Name and message are both required.',
    bad_email:         'That email address does not look right.',
    message_too_short: 'Tell us a little more — twenty characters minimum.',
    rate_limited:      'You have already sent a few. Email info@cli0ck.com directly and we will pick it up.',
    challenge_failed:  'The bot check did not pass. Reload and try again.',
    send_failed:       'Our end failed to send it. Email info@cli0ck.com and we will still get it.',
    forbidden:         'This form only accepts submissions from cli0ck.com.'
  };

  function show(kind, title, body) {
    box.className = 'c-status show ' + kind;
    box.innerHTML = '<b>' + title + '</b>' + body;
    box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var d = new FormData(f), payload = {};
    ['name', 'email', 'company', 'budget', 'message', 'website'].forEach(function (k) {
      payload[k] = (d.get(k) || '').toString().trim();
    });
    payload.services = d.getAll('services');
    var t = f.querySelector('[name="cf-turnstile-response"]');
    if (t) payload.token = t.value;

    btn.disabled = true;
    lbl.textContent = 'Sending…';
    box.className = 'c-status';

    fetch(f.dataset.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok && res.j.ok) {
          f.reset();
          show('ok', 'Received — reference ' + (res.j.ref || ''),
               'We read every enquiry ourselves and answer within two working days. If it is urgent, ' +
               '<a class="hover:underline text-accent" href="mailto:info@cli0ck.com">email us directly</a>.');
        } else {
          show('err', 'Not sent', MSG[res.j.error] || 'Something went wrong. Email info@cli0ck.com instead.');
        }
      })
      .catch(function () {
        show('err', 'Could not reach us',
             'Check your connection, or email <a class="hover:underline text-accent" href="mailto:info@cli0ck.com">info@cli0ck.com</a> directly.');
      })
      .finally(function () {
        btn.disabled = false;
        lbl.textContent = 'Send enquiry';
      });
  });
})();
