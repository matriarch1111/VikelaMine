/* ==========================================================
   VikelaMine — Supervisor Dashboard (real-data version)
   All hazard/site/alert/report data is rendered server-side by
   Django in dashboard.html. This file only handles: switching
   between the four panels, and filtering the hazard queue rows
   that are already on the page (no mock data, no fetch calls).
   ========================================================== */

const views = ['queue', 'zones', 'alerts', 'reports'];

function showView(name) {
  views.forEach(v => {
    document.getElementById('view-' + v).style.display = (v === name) ? '' : 'none';
  });
  document.querySelectorAll('.navitem[data-view]').forEach(b => {
    b.classList.toggle('active', b.dataset.view === name);
  });
  document.getElementById('nav').classList.remove('open');
}

document.querySelectorAll('.navitem[data-view]').forEach(b => {
  b.onclick = () => showView(b.dataset.view);
});

const menuBtn = document.getElementById('menuBtn');
if (menuBtn) {
  menuBtn.onclick = () => document.getElementById('nav').classList.toggle('open');
}

/* ---- hazard queue filter chips ---- */
document.querySelectorAll('.chip').forEach(chip => {
  chip.onclick = () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    const filter = chip.dataset.filter;
    document.querySelectorAll('.qrow').forEach(row => {
      row.style.display = (filter === 'all' || row.dataset.status === filter) ? '' : 'none';
    });
  };
});

showView('queue');