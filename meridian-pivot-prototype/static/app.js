const attendeeSelect = document.querySelector('#attendee');
const scanButton = document.querySelector('#scan');
const notice = document.querySelector('#notice');

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  return response.json();
}

function statusLabel(status) {
  return status.replace('-', ' ');
}

async function refresh() {
  const [attendees, queue, events] = await Promise.all([
    request('/attendees'),
    request('/queue'),
    request('/events'),
  ]);
  const checked = attendees.filter((attendee) => attendee.status === 'checked-in').length;
  document.querySelector('#checked').textContent = `${checked} / ${attendees.length}`;
  document.querySelector('#pending').textContent = queue.length;
  attendeeSelect.innerHTML = attendees.map((attendee) => `<option value="${attendee.id}">${attendee.id} · ${attendee.name}</option>`).join('');
  document.querySelector('#roster').innerHTML = attendees.map((attendee) => `<div class="row"><span>${attendee.name}<small>${attendee.id}</small></span><b class="${attendee.status}">${statusLabel(attendee.status)}</b></div>`).join('');
  document.querySelector('#events').innerHTML = events.slice(0, 6).map((event) => `<div class="event"><b>${event.event}</b><span>${event.detail}</span></div>`).join('') || '<p class="muted">No events yet.</p>';
}

scanButton.addEventListener('click', async () => {
  scanButton.disabled = true;
  const result = await request('/scan', { method: 'POST', body: JSON.stringify({ attendee_id: attendeeSelect.value }) });
  notice.textContent = result.message;
  notice.className = `notice ${result.duplicate ? 'warning' : 'pending'}`;
  scanButton.disabled = false;
  await refresh();
});

document.querySelector('#reset').addEventListener('click', async () => {
  await request('/reset', { method: 'POST' });
  notice.textContent = 'Ready to scan an attendee.';
  notice.className = 'notice';
  await refresh();
});

refresh();
