/* Pure Play — nav drawer + client-side search */
(function () {
  var prefix = window.SEARCH_PREFIX || "";

  /* ---- mobile nav drawer ---- */
  var toggle = document.getElementById("navToggle");
  var body = document.body;
  var scrim = document.createElement("div");
  scrim.className = "scrim";
  body.appendChild(scrim);

  function openNav() { body.classList.add("nav-open"); scrim.classList.add("show"); }
  function closeNav() { body.classList.remove("nav-open"); scrim.classList.remove("show"); }

  if (toggle) {
    toggle.addEventListener("click", function () {
      if (body.classList.contains("nav-open")) closeNav(); else openNav();
    });
  }
  scrim.addEventListener("click", closeNav);
  // close drawer after navigating on mobile
  document.querySelectorAll(".nav a").forEach(function (a) {
    a.addEventListener("click", function () {
      if (window.innerWidth <= 900) closeNav();
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closeNav(); hideResults(); }
  });

  /* ---- search ---- */
  var input = document.getElementById("search");
  var results = document.getElementById("search-results");
  var index = null, loading = false;

  function hideResults() { if (results) results.classList.remove("show"); }

  function loadIndex(cb) {
    if (index) return cb();
    if (loading) return;
    loading = true;
    fetch(prefix + "assets/search-index.json")
      .then(function (r) { return r.json(); })
      .then(function (data) { index = data; loading = false; cb(); })
      .catch(function () { loading = false; });
  }

  function render(matches, q) {
    if (!results) return;
    if (!matches.length) {
      results.innerHTML = '<div class="search-empty">No matches for "' + escapeHtml(q) + '"</div>';
      results.classList.add("show");
      return;
    }
    var html = matches.slice(0, 40).map(function (m) {
      return '<a href="' + prefix + m.u + '">' +
        '<span class="sr-k">' + escapeHtml(m.k) + '</span><br>' +
        '<strong>' + escapeHtml(m.t) + '</strong>' +
        (m.d ? '<div class="sr-d">' + escapeHtml(m.d) + '</div>' : '') +
        '</a>';
    }).join("");
    results.innerHTML = html;
    results.classList.add("show");
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function doSearch() {
    var q = input.value.trim().toLowerCase();
    if (q.length < 2) { hideResults(); return; }
    loadIndex(function () {
      if (!index) return;
      // rank: title startswith > title includes > description includes
      var starts = [], incl = [], desc = [];
      for (var i = 0; i < index.length; i++) {
        var it = index[i], t = it.t.toLowerCase();
        if (t.indexOf(q) === 0) starts.push(it);
        else if (t.indexOf(q) !== -1) incl.push(it);
        else if (it.d && it.d.toLowerCase().indexOf(q) !== -1) desc.push(it);
      }
      render(starts.concat(incl, desc), q);
    });
  }

  if (input) {
    var tmr;
    input.addEventListener("input", function () { clearTimeout(tmr); tmr = setTimeout(doSearch, 120); });
    input.addEventListener("focus", function () { if (input.value.trim().length >= 2) doSearch(); });
    document.addEventListener("click", function (e) {
      if (results && !results.contains(e.target) && e.target !== input) hideResults();
    });
  }
})();
