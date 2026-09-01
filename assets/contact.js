/* cli0ck contact form.
   Posts to Web3Forms, which relays to info@cli0ck.com. The visitor never
   leaves the page and never signs into anything. */
(function () {
  var f = document.getElementById('contactform');
  if (!f) return;
  var btn = f.querySelector('.c-submit'),
      lbl = btn.querySelector('.txt'),
      box = document.getElementById('formstatus');

  function show(kind, title, body) {
    box.className = 'c-status show ' + kind;
    box.innerHTML = '<b>' + title + '</b>' + body;
    box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  var MAIL = '<a class="hover:underline text-accent" href="mailto:info@cli0ck.com">info@cli0ck.com</a>';

  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var d = new FormData(f);
    var get = function (k) { return (d.get(k) || '').toString().trim(); };

    if (get('botcheck')) return;                         // honeypot
    if (!get('name') || !get('email') || !get('message')) {
      return show('err', 'Almost', 'Name, email and message are all required.');
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(get('email'))) {
      return show('err', 'Check the email', 'That address does not look right.');
    }
    if (get('message').length < 20) {
      return show('err', 'Tell us a bit more', 'Twenty characters minimum — it makes our reply useful.');
    }

    var payload = {
      access_key: f.dataset.key,
      subject: '[cli0ck] ' + get('topic') + ' — ' + get('name'),
      from_name: 'cli0ck contact form',
      name: get('name'),
      email: get('email'),
      company: get('company') || '—',
      topic: get('topic'),
      message: get('message')
    };

    btn.disabled = true;
    lbl.textContent = 'Sending…';
    box.className = 'c-status';

    fetch('https://api.web3forms.com/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok && res.j.success) {
          f.reset();
          show('ok', 'Sent — thank you',
               'It is in our inbox. We read every message ourselves and reply to the address you gave.');
        } else {
          show('err', 'Not sent',
               'Something went wrong on the way. Email ' + MAIL + ' and it will still reach us.');
        }
      })
      .catch(function () {
        show('err', 'Could not reach us',
             'Check your connection, or email ' + MAIL + ' directly.');
      })
      .finally(function () {
        btn.disabled = false;
        lbl.textContent = 'Send message';
      });
  });
})();
