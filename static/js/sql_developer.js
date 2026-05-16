const token = localStorage.getItem('clinicToken');
let currentUser = null;
try {
  currentUser = JSON.parse(localStorage.getItem('clinicUser') || 'null');
} catch {
  currentUser = null;
}

function requireAdmin() {
  if (!token || !currentUser || (currentUser.role || '').toLowerCase() !== 'admin') {
    window.location.href = '/auth';
    return false;
  }
  return true;
}

if (!requireAdmin()) {
  throw new Error('Not authorized');
}

function apiHeaders() {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
    'X-User-Email': (currentUser?.email || '').toLowerCase()
  };
}

function showMessage(el, text, type) {
  if (!el) return;
  el.style.display = 'block';
  el.textContent = text;
  if (type === 'success') {
    el.className = 'message success';
  } else if (type === 'error') {
    el.className = 'message error';
  } else {
    el.className = 'message';
  }
}

function renderTable(rows) {
  const container = document.getElementById('sql-result');
  if (!container) return;
  container.innerHTML = '';

  if (!rows || rows.length === 0) {
    container.innerHTML = '<p style="color:var(--light-text);margin:0.5rem 0;">No rows returned.</p>';
    return;
  }

  const columns = Object.keys(rows[0]);

  container.innerHTML = `
    <table>
      <tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr>
      ${rows.map(r => `
        <tr>${columns.map(c => `<td>${r[c] === null || r[c] === undefined ? '-' : String(r[c])}</td>`).join('')}</tr>
      `).join('')}
    </table>
  `;
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('sql-form');
  const queryEl = document.getElementById('sql-query');
  const limitEl = document.getElementById('sql-limit');
  const msgEl = document.getElementById('sql-message');
  const errEl = document.getElementById('sql-error');

  if (!form || !queryEl || !limitEl) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    msgEl.style.display = 'none';
    errEl.style.display = 'none';

    const query = (queryEl.value || '').trim();
    const limit = Math.max(1, Math.min(2000, parseInt(limitEl.value, 10) || 200));

    if (!query) {
      showMessage(errEl, 'SQL query is required.', 'error');
      return;
    }

    try {
      const res = await fetch('/api/sql-exec', {
        method: 'POST',
        headers: apiHeaders(),
        body: JSON.stringify({ query, limit })
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        showMessage(errEl, data.error || data.message || 'Query failed.', 'error');
        return;
      }

      showMessage(msgEl, `Success. Returned ${data.rows.length} row(s).`, 'success');
      renderTable(data.rows);
    } catch (err) {
      showMessage(errEl, 'Server error while executing SQL.', 'error');
      console.error(err);
    }
  });

  const logoutBtn = document.getElementById('logout-button');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      localStorage.removeItem('clinicToken');
      localStorage.removeItem('clinicUser');
      window.location.href = '/auth';
    });
  }
});

