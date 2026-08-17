/* DocVerify AI - Main JavaScript Utilities */

/**
 * Show an alert message in the #alert-box element.
 * @param {string} msg - Message to display
 * @param {'error'|'success'|'info'} type - Alert type
 */
function showAlert(msg, type = 'error') {
  const box = document.getElementById('alert-box');
  if (!box) return;
  box.className = `alert alert-${type}`;
  box.textContent = msg;
  box.style.display = 'block';
  setTimeout(() => { box.style.display = 'none'; }, 6000);
}

/**
 * Toggle password visibility for a password input.
 * @param {string} inputId - ID of the password input
 */
function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
}

/**
 * Format a date string in a human-readable format.
 * @param {string} dateStr - ISO date string
 */
function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleString('en-IN', { 
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch { return dateStr; }
}

/**
 * Determine a CSS color class for a given authenticity score.
 */
function scoreToClass(score) {
  if (score >= 90) return 'good';
  if (score >= 75) return 'warn';
  if (score >= 50) return 'warn';
  return 'bad';
}

// Global fetch error handler for API calls
async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  if (res.status === 401) {
    window.location.href = '/login';
    return null;
  }
  return res;
}
