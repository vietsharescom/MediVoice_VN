// suggestions.js — UI-SUGGEST-001 — FID-VN-010
// Drug chips + Dialect badge + Terminology sidebar
// Requires: /api/drug-candidates, /api/terms, /api/dialect-check

'use strict';

const Suggestions = (() => {

  let _currentSpecialty = 'noi_khoa';
  let _termsCache = null; // {specialty, terms}

  // ─── Drug Candidates ────────────────────────────────────────────────────

  async function fetchDrugCandidates(transcript, chanDoan = '', n = 3) {
    if (!transcript || !transcript.trim()) return [];
    try {
      const params = new URLSearchParams({
        q: transcript.trim(),
        diagnosis: chanDoan || '',
        n: String(n),
      });
      const resp = await fetch(`/api/drug-candidates?${params}`);
      if (!resp.ok) return [];
      const data = await resp.json();
      return data.candidates || [];
    } catch (_) {
      return [];
    }
  }

  function renderDrugChips(candidates) {
    const panel = document.getElementById('suggest-drug-panel');
    if (!panel) return;
    if (!candidates || candidates.length === 0) {
      panel.classList.add('hidden');
      return;
    }
    panel.classList.remove('hidden');
    const list = document.getElementById('suggest-drug-chips');
    if (!list) return;
    list.innerHTML = '';
    candidates.forEach(c => {
      const score = Math.round((c.score || 0) * 100);
      const btn = document.createElement('button');
      btn.className = 'drug-chip';
      btn.type = 'button';
      btn.title = c.drug_class ? `Nhóm: ${c.drug_class}` : c.inn;
      btn.innerHTML =
        `<strong>${escHtml(c.inn)}</strong>` +
        `<span class="chip-score">${score}%</span>`;
      btn.addEventListener('click', () => _insertDrug(c.inn));
      list.appendChild(btn);
    });
  }

  function _insertDrug(inn) {
    // Không tự điền — BS tự chọn. Chỉ toast để BS biết đã tap.
    _showToast(`Thuốc gợi ý: ${inn} — điền vào form nếu đúng`);
  }

  // ─── Dialect Badge ────────────────────────────────────────────────────────

  async function fetchDialectCheck(text, region = 'auto') {
    if (!text || !text.trim()) return null;
    try {
      const resp = await fetch('/api/dialect-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim(), region }),
      });
      if (!resp.ok) return null;
      return await resp.json();
    } catch (_) {
      return null;
    }
  }

  function renderDialectBadge(result) {
    const badge = document.getElementById('suggest-dialect-badge');
    const textEl = document.getElementById('dialect-badge-text');
    if (!badge || !textEl) return;
    if (!result || !result.changed || !result.substitutions.length) {
      badge.classList.add('hidden');
      return;
    }
    const regionLabel = { central: 'Trung', southern: 'Nam', northern: 'Bắc' }[result.region] || result.region;
    // Show max 4 substitutions to avoid overflow on mobile
    const subs = result.substitutions.slice(0, 4).join(' | ');
    textEl.textContent = `Giọng ${regionLabel}: ${subs}`;
    badge.classList.remove('hidden');
  }

  function dismissDialectBadge() {
    const badge = document.getElementById('suggest-dialect-badge');
    if (badge) badge.classList.add('hidden');
  }

  // ─── Terminology Sidebar ──────────────────────────────────────────────────

  async function fetchTerms(specialty) {
    if (_termsCache && _termsCache.specialty === specialty) return _termsCache.terms;
    try {
      const resp = await fetch(`/api/terms?specialty=${encodeURIComponent(specialty)}&n=20`);
      if (!resp.ok) return [];
      const data = await resp.json();
      _termsCache = { specialty, terms: data.terms || [] };
      return _termsCache.terms;
    } catch (_) {
      return [];
    }
  }

  function renderTermSidebar(terms) {
    const sidebar = document.getElementById('suggest-term-sidebar');
    const list = document.getElementById('suggest-term-list');
    const label = document.getElementById('suggest-term-specialty');
    if (!sidebar || !list) return;

    if (!terms || terms.length === 0) {
      sidebar.classList.add('hidden');
      return;
    }
    sidebar.classList.remove('hidden');

    const specialtyLabel = {
      noi_khoa: 'Nội khoa', ho_hap: 'Hô hấp', tieu_hoa: 'Tiêu hóa',
      noi_tiet: 'Nội tiết', tai_mui_hong: 'TMH', da_lieu: 'Da liễu',
      co_xuong_khop: 'CXK', nhi_khoa: 'Nhi khoa',
    }[_currentSpecialty] || _currentSpecialty;
    if (label) label.textContent = specialtyLabel;

    list.innerHTML = '';
    terms.forEach(t => {
      const btn = document.createElement('button');
      btn.className = 'term-chip';
      btn.type = 'button';
      btn.title = t.common || t.term;
      btn.innerHTML = `${escHtml(t.term)}<span class="term-icd">${escHtml(t.icd)}</span>`;
      btn.addEventListener('click', () => _fillTerm(t));
      list.appendChild(btn);
    });
  }

  function _fillTerm(t) {
    const chanDoan = document.getElementById('f-chan-doan');
    const icd = document.getElementById('f-icd');
    if (chanDoan && !chanDoan.value.trim()) {
      chanDoan.value = t.term;
    }
    if (icd && !icd.value.trim()) {
      icd.value = t.icd;
    }
    _showToast(`Chèn: ${t.term} (${t.icd})`);
  }

  function toggleTermList() {
    const list = document.getElementById('suggest-term-list');
    const btn = document.querySelector('.btn-toggle-terms');
    if (!list) return;
    const hidden = list.classList.toggle('hidden');
    if (btn) btn.textContent = hidden ? '▶' : '▼';
  }

  // ─── Public entry points ──────────────────────────────────────────────────

  /**
   * Gọi sau khi transcript + chanDoan có.
   * Song song: drug candidates + dialect check.
   */
  async function onTranscriptReady(transcript, chanDoan) {
    if (!transcript) return;
    const [candidates, dialectResult] = await Promise.all([
      fetchDrugCandidates(transcript, chanDoan),
      fetchDialectCheck(transcript),
    ]);
    renderDrugChips(candidates);
    renderDialectBadge(dialectResult);
  }

  /**
   * Gọi khi BS đổi chuyên khoa.
   */
  async function onSpecialtyChange(specialty) {
    _currentSpecialty = specialty;
    _termsCache = null;
    const terms = await fetchTerms(specialty);
    renderTermSidebar(terms);
  }

  /**
   * Gọi một lần khi trang load xong.
   */
  async function init(specialty) {
    _currentSpecialty = specialty || 'noi_khoa';
    const terms = await fetchTerms(_currentSpecialty);
    renderTermSidebar(terms);
  }

  // ─── Helpers ─────────────────────────────────────────────────────────────

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function _showToast(msg) {
    // Reuse existing showToast from index.html if available
    if (typeof showToast === 'function') {
      showToast(msg);
    }
  }

  return {
    onTranscriptReady,
    onSpecialtyChange,
    init,
    dismissDialectBadge,
    toggleTermList,
    // Expose for tests
    _fetchDrugCandidates: fetchDrugCandidates,
    _fetchDialectCheck: fetchDialectCheck,
    _fetchTerms: fetchTerms,
  };

})();

window.Suggestions = Suggestions;
