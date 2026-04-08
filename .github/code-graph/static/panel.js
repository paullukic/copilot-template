/* ================================================================
   Code Graph — panel.js
   Manages the side-panel: connection list, node info, symbol list,
   extension filters, search, and back navigation.

   Depends on: graphData (global), graph.js providing:
     renderFileView(), renderServiceView(), renderSymbolView(),
     selectService(), selectFile(), deselect()
   ================================================================ */

/* ----------------------------------------------------------------
   Connection list — ASCII-art clickable edges
   Shows "service ──42 deps──▶ target" lines that navigate on click.
   ---------------------------------------------------------------- */

const Panel = (() => {

  const $ = id => document.getElementById(id);

  /* ---- Build the clickable connection list for a service node ---- */
  function showServiceConnections(d) {
    const wrap = $("conn-list");
    wrap.style.display = "";
    wrap.innerHTML = "";

    const outE = Graph.svcAdj.out.get(d.id) || [];
    const inE  = Graph.svcAdj.in.get(d.id)  || [];

    // Group outbound edges by type
    const outByTarget = new Map();
    for (const e of outE) {
      if (!outByTarget.has(e.id)) outByTarget.set(e.id, []);
      if (e.depends_on) outByTarget.get(e.id).push({ kind: "depends_on", n: e.depends_on });
      if (e.tests_for)  outByTarget.get(e.id).push({ kind: "tests_for",  n: e.tests_for });
      if (e.inherits)   outByTarget.get(e.id).push({ kind: "inherits",   n: e.inherits });
      if (e.implements) outByTarget.get(e.id).push({ kind: "implements", n: e.implements });
    }

    const inBySource = new Map();
    for (const e of inE) {
      if (!inBySource.has(e.id)) inBySource.set(e.id, []);
      if (e.depends_on) inBySource.get(e.id).push({ kind: "depends_on", n: e.depends_on });
      if (e.tests_for)  inBySource.get(e.id).push({ kind: "tests_for",  n: e.tests_for });
      if (e.inherits)   inBySource.get(e.id).push({ kind: "inherits",   n: e.inherits });
      if (e.implements) inBySource.get(e.id).push({ kind: "implements", n: e.implements });
    }

    // Render outbound section
    if (outByTarget.size) {
      const title = document.createElement("div");
      title.className = "conn-section-title";
      title.textContent = "OUTBOUND (" + outByTarget.size + " services)";
      wrap.appendChild(title);

      // Sort by total edge count descending
      const sorted = [...outByTarget.entries()].sort((a, b) => {
        const sumA = a[1].reduce((s, e) => s + e.n, 0);
        const sumB = b[1].reduce((s, e) => s + e.n, 0);
        return sumB - sumA;
      });

      for (const [targetId, edges] of sorted) {
        for (const edge of edges) {
          _appendConnRow(wrap, {
            direction: "out",
            count: edge.n,
            kind: edge.kind,
            target: targetId,
            onClick: () => Graph.renderFileView(targetId),
          });
        }
      }
    }

    // Render inbound section
    if (inBySource.size) {
      const title = document.createElement("div");
      title.className = "conn-section-title";
      title.textContent = "INBOUND (" + inBySource.size + " services)";
      wrap.appendChild(title);

      const sorted = [...inBySource.entries()].sort((a, b) => {
        const sumA = a[1].reduce((s, e) => s + e.n, 0);
        const sumB = b[1].reduce((s, e) => s + e.n, 0);
        return sumB - sumA;
      });

      for (const [sourceId, edges] of sorted) {
        for (const edge of edges) {
          _appendConnRow(wrap, {
            direction: "in",
            count: edge.n,
            kind: edge.kind,
            target: sourceId,
            onClick: () => Graph.renderFileView(sourceId),
          });
        }
      }
    }

    if (!outByTarget.size && !inBySource.size) {
      const empty = document.createElement("div");
      empty.style.cssText = "color:#334;font-size:11px;padding:4px 0";
      empty.textContent = "No cross-service connections";
      wrap.appendChild(empty);
    }
  }

  /* ---- Build clickable connection list for a file node ---- */
  function showFileConnections(d) {
    const wrap = $("conn-list");
    wrap.style.display = "";
    wrap.innerHTML = "";

    const types = Graph.activeTypes();
    let hasAny = false;

    for (const kind of types) {
      const outIds = Graph.adj[kind]?.out.get(d.id) || [];
      const inIds  = Graph.adj[kind]?.in.get(d.id)  || [];

      if (!outIds.length && !inIds.length) continue;
      hasAny = true;

      // Outbound
      for (const t of outIds) {
        const f = Graph.fileById.get(t);
        _appendConnRow(wrap, {
          direction: "out",
          count: 1,
          kind: kind,
          target: f?.label ?? t,
          targetSvc: f ? f.file.split("/")[0] : "",
          onClick: () => {
            if (f) {
              // Navigate to that file's service file view
              const svc = f.file.split("/")[0];
              if (!Graph.view.startsWith("files:" + svc)) {
                Graph.renderFileView(svc);
              }
              // Delay to let simulation settle, then select the file
              setTimeout(() => {
                const node = Graph.curNodes.find(n => n.id === t);
                if (node) Graph.selectFile(node);
              }, 600);
            }
          },
        });
      }

      // Inbound
      for (const s of inIds) {
        const f = Graph.fileById.get(s);
        _appendConnRow(wrap, {
          direction: "in",
          count: 1,
          kind: kind,
          target: f?.label ?? s,
          targetSvc: f ? f.file.split("/")[0] : "",
          onClick: () => {
            if (f) {
              const svc = f.file.split("/")[0];
              if (!Graph.view.startsWith("files:" + svc)) {
                Graph.renderFileView(svc);
              }
              setTimeout(() => {
                const node = Graph.curNodes.find(n => n.id === s);
                if (node) Graph.selectFile(node);
              }, 600);
            }
          },
        });
      }
    }

    if (!hasAny) {
      const empty = document.createElement("div");
      empty.style.cssText = "color:#334;font-size:11px;padding:4px 0";
      empty.textContent = "Enable edge types above to see connections";
      wrap.appendChild(empty);
    }
  }

  /* ---- Append one connection row ---- */
  function _appendConnRow(container, { direction, count, kind, target, targetSvc, onClick }) {
    const row = document.createElement("div");
    row.className = "conn-item";
    row.title = (direction === "out" ? "→ " : "← ") + target + (targetSvc ? " (" + targetSvc + ")" : "");

    // Arrow
    const arrow = document.createElement("span");
    arrow.className = "conn-arrow " + direction;
    arrow.textContent = direction === "out" ? "──" : "◄─";

    // Count
    const cnt = document.createElement("span");
    cnt.className = "conn-count " + kind;
    cnt.textContent = count > 1 ? String(count).padStart(3) : " ";

    // Kind badge
    const badge = document.createElement("span");
    badge.className = "conn-kind " + kind;
    badge.textContent = _shortKind(kind);

    // Arrow tip
    const tip = document.createElement("span");
    tip.className = "conn-arrow " + direction;
    tip.textContent = direction === "out" ? "─▶ " : "── ";

    // Target name
    const tgt = document.createElement("span");
    tgt.className = "conn-target";
    tgt.textContent = target;

    if (direction === "out") {
      row.append(arrow, cnt, badge, tip, tgt);
    } else {
      row.append(arrow, cnt, badge, tip, tgt);
    }

    row.addEventListener("click", onClick);
    container.appendChild(row);
  }

  function _shortKind(kind) {
    const m = { depends_on: "dep", tests_for: "test", inherits: "ext", implements: "impl" };
    return m[kind] || kind;
  }

  /* ---- Node info (name + path) ---- */
  function showNodeInfo(name, path) {
    $("node-info").style.display = "";
    $("ni-name").textContent = name;
    $("ni-path").textContent = path || "";
  }

  function hideNodeInfo() {
    $("node-info").style.display = "none";
    $("symbol-list").style.display = "none";
    $("conn-list").style.display = "none";
  }

  /* ---- Symbol list ---- */
  function showSymbolList(fileId) {
    const syms = graphData.symbolsByFile[fileId] || [];
    if (!syms.length) return;

    const el = $("sym-items");
    const wrap = $("symbol-list");
    wrap.style.display = "";
    el.innerHTML = "";

    const grouped = {};
    syms.forEach(s => { (grouped[s.kind] = grouped[s.kind] || []).push(s); });

    for (const [kind, items] of Object.entries(grouped)) {
      items.slice(0, 30).forEach(s => {
        const d = document.createElement("div");
        d.className = "sym-item";
        d.innerHTML = '<span class="sym-kind ' + kind + '">' + kind + '</span>' +
          _escHtml(s.name);
        if (s.line) d.title = "Line " + s.line;
        el.appendChild(d);
      });
      if (items.length > 30) {
        const d = document.createElement("div");
        d.className = "sym-item"; d.style.color = "#334";
        d.textContent = "… and " + (items.length - 30) + " more " + kind;
        el.appendChild(d);
      }
    }
  }

  function _escHtml(s) {
    const d = document.createElement("span");
    d.textContent = s;
    return d.innerHTML;
  }

  /* ---- Extension filters ---- */
  let activeExts = new Set();

  function buildExtFilters() {
    const container = $("ext-filters");
    container.innerHTML = "";
    graphData.topExts.forEach(ext => {
      const pill = document.createElement("span");
      pill.className = "ext-pill active";
      pill.textContent = "." + ext + " (" + graphData.extCounts[ext] + ")";
      pill.dataset.ext = ext;
      pill.addEventListener("click", () => {
        pill.classList.toggle("active");
        _updateActiveExts();
        Graph.filterCurrentView();
      });
      container.appendChild(pill);
    });
    _updateActiveExts();
  }

  function _updateActiveExts() {
    activeExts = new Set();
    document.querySelectorAll(".ext-pill.active").forEach(p => activeExts.add(p.dataset.ext));
  }

  function getActiveExts() { return activeExts; }

  /* ---- Search ---- */
  $("search").addEventListener("input", e => {
    const q = e.target.value.toLowerCase().trim();
    Graph.applySearch(q);
  });

  /* ---- Back ---- */
  $("back-btn").addEventListener("click", () => {
    if (Graph.view.startsWith("symbols:")) {
      const fileId = Graph.view.split(":")[1];
      const f = Graph.fileById.get(fileId);
      if (f) {
        Graph.renderFileView(f.file.split("/")[0]);
      } else {
        Graph.renderServiceView();
      }
    } else {
      Graph.renderServiceView();
    }
  });

  /* ---- Edge type checkboxes ---- */
  document.querySelectorAll("[data-etype]").forEach(cb => {
    cb.addEventListener("change", () => Graph.onEdgeFilterChange());
  });

  $("show-all-cb").addEventListener("change", e => {
    if (e.target.checked) { Graph.deselect(); Graph.drawAllEdgesInView(); }
    else Graph.clearEdges();
  });

  /* ---- Public API ---- */
  return {
    showServiceConnections,
    showFileConnections,
    showNodeInfo,
    hideNodeInfo,
    showSymbolList,
    buildExtFilters,
    getActiveExts,
  };

})();
