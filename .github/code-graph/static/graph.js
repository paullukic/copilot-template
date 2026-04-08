/* ================================================================
   Code Graph — graph.js
   D3 force-directed graph with three drill-down levels:
     1. Services  →  2. Files  →  3. Symbols

   Depends on: d3 (global), graphData (global), Panel (panel.js)
   ================================================================ */

const Graph = (() => {

  /* ==============================================================
     Colour palettes
     ============================================================== */
  const SVC_COLORS = id => {
    if (id.startsWith("gateway-"))             return "#e07b39";
    if (id.startsWith("common-") || id === "common-sdk") return "#9b59b6";
    if (id.includes("worker"))                 return "#2a9d5c";
    if (id.startsWith("cybernoc"))             return "#c0392b";
    if (id.startsWith("template-") || id === "terraform" || id === "kubernetes") return "#5d7a8a";
    return "#4a7fa5";
  };

  const EXT_COLORS = {
    java: "#4a7fa5", kt: "#7b68ee", scala: "#dc322f",
    xml: "#e07b39", yaml: "#d4b43a", yml: "#d4b43a",
    sql: "#c0392b", json: "#2a9d5c",
    py: "#3498db", ts: "#e67e22", tsx: "#e67e22", js: "#f1c40f", jsx: "#f1c40f",
    properties: "#95a5a6", md: "#556", txt: "#556", gradle: "#5a9",
  };
  const fileColor = ext => EXT_COLORS[ext] || "#556";

  const SYM_COLORS = {
    "class": "#2980b9", "interface": "#8e44ad", "enum": "#27ae60",
    "function": "#e67e22", "method": "#d35400",
    "annotation": "#c0392b", "table": "#16a085", "endpoint": "#2c3e50",
  };
  const symColor = kind => SYM_COLORS[kind] || "#556";

  const EDGE_COLORS = {
    depends_on: "#c8851a", tests_for: "#2a9d5c",
    inherits: "#e74c3c", implements: "#1abc9c", contains: "#334",
  };
  const EDGE_STYLES = {
    depends_on: { w: 1.2, dash: null,  op: 0.7 },
    tests_for:  { w: 1.8, dash: "4 3", op: 0.7 },
    inherits:   { w: 2.0, dash: null,  op: 0.8 },
    implements: { w: 1.5, dash: "6 3", op: 0.7 },
    contains:   { w: 0.8, dash: "2 2", op: 0.3 },
  };

  /* ==============================================================
     Pre-compute adjacency indices
     ============================================================== */
  const adj = {};
  for (const [kind, list] of Object.entries(graphData.edges)) {
    adj[kind] = { out: new Map(), in: new Map() };
    for (const e of list) {
      if (!adj[kind].out.has(e.s)) adj[kind].out.set(e.s, []);
      adj[kind].out.get(e.s).push(e.t);
      if (!adj[kind].in.has(e.t))  adj[kind].in.set(e.t, []);
      adj[kind].in.get(e.t).push(e.s);
    }
  }

  const svcAdj = { out: new Map(), in: new Map() };
  for (const e of graphData.serviceEdges) {
    const total = (e.depends_on||0) + (e.tests_for||0) + (e.inherits||0) + (e.implements||0);
    if (!svcAdj.out.has(e.s)) svcAdj.out.set(e.s, []);
    svcAdj.out.get(e.s).push({ id: e.t, n: total, ...e });
    if (!svcAdj.in.has(e.t))  svcAdj.in.set(e.t, []);
    svcAdj.in.get(e.t).push({ id: e.s, n: total, ...e });
  }

  // file id → file object
  const fileById = new Map();
  for (const files of Object.values(graphData.filesByService))
    for (const f of files) fileById.set(f.id, f);

  // Populate edge counts in panel
  for (const [kind, list] of Object.entries(graphData.edges)) {
    const el = document.getElementById("cnt-" + kind);
    if (el) el.textContent = list.length.toLocaleString();
  }

  /* ==============================================================
     SVG setup
     ============================================================== */
  const PANEL_W = 280;
  let W = window.innerWidth - PANEL_W;
  let H = window.innerHeight;

  const svg   = d3.select("#graph").attr("width", W).attr("height", H).style("margin-left", PANEL_W + "px");
  const scene = svg.append("g");
  const gEdge = scene.append("g");
  const gNode = scene.append("g");
  const gLbl  = scene.append("g");

  const zoom = d3.zoom().scaleExtent([0.04, 20])
    .on("zoom", e => scene.attr("transform", e.transform));
  svg.call(zoom);
  svg.on("click", e => { if (e.target.tagName === "svg") deselect(); });

  window.addEventListener("resize", () => {
    W = window.innerWidth - PANEL_W; H = window.innerHeight;
    svg.attr("width", W).attr("height", H);
    if (sim) sim.force("center", d3.forceCenter(W / 2, H / 2)).alpha(0.2).restart();
  });

  /* ==============================================================
     State
     ============================================================== */
  let view       = "services";
  let selectedId = null;
  let sim        = null;
  let curNodes   = [];

  /* ==============================================================
     Shared helpers
     ============================================================== */
  const maxFiles = Math.max(...graphData.services.map(s => s.files));
  const svcR = d => 6 + Math.sqrt(d.files / maxFiles) * 28;

  function stopSim()    { if (sim) { sim.stop(); sim = null; } }
  function clearGraph() { gEdge.selectAll("*").remove(); gNode.selectAll("*").remove(); gLbl.selectAll("*").remove(); }
  function clearEdges() { gEdge.selectAll("line").remove(); }
  function setStats(t)  { document.getElementById("stats").textContent = t; }
  function nodeMap()    { return new Map(curNodes.map(n => [n.id, n])); }

  /** Run simulation synchronously to convergence, then place elements. */
  function settleAndPlace(s, placeFn) {
    s.stop();
    const n = Math.ceil(Math.log(s.alphaMin()) / Math.log(1 - s.alphaDecay()));
    for (let i = 0; i < n; i++) s.tick();
    placeFn();
    // Keep sim alive but stopped — drag will reheat it
    s.on("tick", placeFn).alpha(0).restart().stop();
  }

  function drag() {
    return d3.drag()
      .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
      .on("end",   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = d.fy = null; });
  }

  /* ---- Tooltip ---- */
  const tip = document.getElementById("tooltip");
  function showTip(e, title, sub, extra) {
    tip.style.display = "block";
    document.getElementById("tt-title").textContent = title;
    document.getElementById("tt-sub").textContent   = sub || "";
    document.getElementById("tt-extra").textContent  = extra || "";
    moveTip(e);
  }
  function moveTip(e) {
    tip.style.left = Math.min(e.clientX - PANEL_W + 14, W - 370) + PANEL_W + "px";
    tip.style.top  = (e.clientY - 10) + "px";
  }
  function hideTip() { tip.style.display = "none"; }

  /* ---- Active edge-type filters ---- */
  function activeTypes() {
    return [...document.querySelectorAll("[data-etype]")]
      .filter(cb => cb.checked).map(cb => cb.dataset.etype);
  }

  /* ==============================================================
     Edge rendering
     ============================================================== */
  function renderEdgeLines(lines, nm, opOverride) {
    gEdge.selectAll("line").remove();
    gEdge.selectAll("line")
      .data(lines).join("line")
      .attr("x1", e => nm.get(e.s)?.x ?? 0).attr("y1", e => nm.get(e.s)?.y ?? 0)
      .attr("x2", e => nm.get(e.t)?.x ?? 0).attr("y2", e => nm.get(e.t)?.y ?? 0)
      .attr("stroke",         e => EDGE_COLORS[e.kind] || "#666")
      .attr("stroke-width",   e => (EDGE_STYLES[e.kind]?.w || 1))
      .attr("stroke-opacity", e => opOverride ?? (EDGE_STYLES[e.kind]?.op || 0.5))
      .attr("stroke-dasharray", e => EDGE_STYLES[e.kind]?.dash || null);
  }

  function tickEdges() {
    const nm = nodeMap();
    gEdge.selectAll("line")
      .attr("x1", e => nm.get(e.s)?.x ?? 0).attr("y1", e => nm.get(e.s)?.y ?? 0)
      .attr("x2", e => nm.get(e.t)?.x ?? 0).attr("y2", e => nm.get(e.t)?.y ?? 0);
  }

  function drawEdgesForNode(d) {
    const nm = nodeMap(), types = activeTypes(), lines = [];
    for (const kind of types) {
      for (const t of (adj[kind]?.out.get(d.id) || [])) if (nm.has(t)) lines.push({ s: d.id, t, kind });
      for (const s of (adj[kind]?.in.get(d.id)  || [])) if (nm.has(s)) lines.push({ s, t: d.id, kind });
    }
    renderEdgeLines(lines, nm, null);
    return lines;
  }

  function drawAllEdgesInView() {
    const nm = nodeMap(), types = activeTypes(), lines = [];
    for (const kind of types) {
      for (const e of (graphData.edges[kind] || []))
        if (nm.has(e.s) && nm.has(e.t)) lines.push({ s: e.s, t: e.t, kind });
    }
    renderEdgeLines(lines, nm, 0.35);
  }

  /* ==============================================================
     Deselect
     ============================================================== */
  function deselect() {
    selectedId = null;
    Panel.hideNodeInfo();
    if (document.getElementById("show-all-cb").checked) drawAllEdgesInView();
    else clearEdges();
    gNode.selectAll("circle").attr("opacity", 1).attr("stroke", "#000").attr("stroke-width", 0.5).attr("r", d => d._r || 5);
    gLbl.selectAll("text").attr("opacity", 1);
  }

  /* ==============================================================
     SERVICE VIEW
     ============================================================== */
  function renderServiceView() {
    view = "services"; selectedId = null;
    clearGraph(); stopSim();
    curNodes = graphData.services.map(s => ({ ...s }));

    document.getElementById("crumb-text").textContent = "Services";
    document.getElementById("back-btn").style.display = "none";
    document.getElementById("show-all-row").style.display = "none";
    document.getElementById("file-legend").style.display = "none";
    document.getElementById("sym-legend").style.display = "none";
    document.getElementById("svc-legend").style.display = "";
    document.getElementById("ext-filters").style.display = "none";
    document.getElementById("ext-title").style.display = "none";
    document.getElementById("search").value = "";
    document.getElementById("search").placeholder = "Filter services…";
    Panel.hideNodeInfo();

    const totalEdges = graphData.serviceEdges.reduce(
      (a, e) => a + (e.depends_on||0) + (e.tests_for||0) + (e.inherits||0) + (e.implements||0), 0);
    setStats(curNodes.length + " services │ " + graphData.totalFiles.toLocaleString() +
      " files │ " + graphData.totalSymbols.toLocaleString() + " symbols │ " +
      totalEdges.toLocaleString() + " cross-svc edges");

    const circle = gNode.selectAll("circle")
      .data(curNodes, d => d.id).join("circle")
      .attr("r",       d => svcR(d))
      .attr("fill",    d => SVC_COLORS(d.id))
      .attr("stroke",  "#0008").attr("stroke-width", 1)
      .attr("cursor",  "pointer")
      .call(drag())
      .on("mouseover", (e, d) => showTip(e, d.label, d.files.toLocaleString() + " files", d.classes + " classes │ " + d.functions + " functions"))
      .on("mousemove", moveTip).on("mouseout", hideTip)
      .on("click",    (e, d) => { e.stopPropagation(); selectService(d); })
      .on("dblclick", (e, d) => { e.stopPropagation(); renderFileView(d.id); });

    gLbl.selectAll("text")
      .data(curNodes, d => d.id).join("text")
      .attr("class", "node-label")
      .attr("text-anchor", "middle").attr("font-size", 10)
      .attr("fill", "#ccc").attr("pointer-events", "none")
      .text(d => d.label);

    sim = d3.forceSimulation(curNodes)
      .force("charge",    d3.forceManyBody().strength(-400))
      .force("center",    d3.forceCenter(W / 2, H / 2))
      .force("collision", d3.forceCollide(d => svcR(d) + 18))
      .alphaDecay(0.03);

    const placeSvc = () => {
      gNode.selectAll("circle").attr("cx", d => d.x).attr("cy", d => d.y);
      gLbl.selectAll("text").attr("x", d => d.x).attr("y", d => d.y + svcR(d) + 14);
      tickEdges();
    };
    settleAndPlace(sim, placeSvc);
  }

  function selectService(d) {
    if (selectedId === d.id) { deselect(); return; }
    selectedId = d.id;

    const outE = svcAdj.out.get(d.id) || [];
    const inE  = svcAdj.in.get(d.id)  || [];
    const conn = new Set([d.id, ...outE.map(e => e.id), ...inE.map(e => e.id)]);

    gNode.selectAll("circle")
      .attr("opacity",      n => conn.has(n.id) ? 1 : 0.1)
      .attr("stroke",       n => n.id === d.id ? "#fff" : "#0008")
      .attr("stroke-width", n => n.id === d.id ? 2 : 1);
    gLbl.selectAll("text").attr("opacity", n => conn.has(n.id) ? 1 : 0.1);

    // Draw service edges
    const nm = nodeMap();
    const lines = [
      ...outE.map(e => ({ s: d.id, t: e.id, kind: "depends_on" })),
      ...inE .map(e => ({ s: e.id, t: d.id, kind: "depends_on" })),
    ];
    gEdge.selectAll("line").remove();
    gEdge.selectAll("line")
      .data(lines).join("line")
      .attr("x1", e => nm.get(e.s)?.x ?? 0).attr("y1", e => nm.get(e.s)?.y ?? 0)
      .attr("x2", e => nm.get(e.t)?.x ?? 0).attr("y2", e => nm.get(e.t)?.y ?? 0)
      .attr("stroke", e => EDGE_COLORS[e.kind])
      .attr("stroke-width", e => {
        const edge = [...outE, ...inE].find(x => x.id === e.s || x.id === e.t);
        return Math.min(1 + Math.log((edge?.n || 1) + 1), 5);
      })
      .attr("stroke-opacity", 0.75);

    Panel.showNodeInfo(d.label,
      d.files.toLocaleString() + " files │ " + d.classes + " classes │ " + d.functions + " functions");
    Panel.showServiceConnections(d);
  }

  /* ==============================================================
     FILE VIEW
     ============================================================== */
  function renderFileView(svcName) {
    view = "files:" + svcName; selectedId = null;
    clearGraph(); stopSim();

    curNodes = (graphData.filesByService[svcName] || []).map(f => ({ ...f, _r: 5 }));

    document.getElementById("crumb-text").textContent = svcName;
    document.getElementById("back-btn").style.display = "inline-block";
    document.getElementById("show-all-row").style.display = "";
    document.getElementById("show-all-cb").checked = false;
    document.getElementById("file-legend").style.display = "";
    document.getElementById("sym-legend").style.display = "none";
    document.getElementById("svc-legend").style.display = "none";
    document.getElementById("ext-filters").style.display = "flex";
    document.getElementById("ext-title").style.display = "";
    document.getElementById("search").value = "";
    document.getElementById("search").placeholder = "Filter files…";
    Panel.hideNodeInfo();
    Panel.buildExtFilters();

    const fileIds = new Set(curNodes.map(n => n.id));
    const edgeCounts = {};
    for (const [kind, list] of Object.entries(graphData.edges))
      edgeCounts[kind] = list.filter(e => fileIds.has(e.s) && fileIds.has(e.t)).length;
    const parts = Object.entries(edgeCounts).filter(kv => kv[1] > 0).map(kv => kv[1] + " " + kv[0]);
    setStats(curNodes.length.toLocaleString() + " files │ " + (parts.join(" │ ") || "no intra-service edges"));

    gNode.selectAll("circle")
      .data(curNodes, d => d.id).join("circle")
      .attr("r", 5)
      .attr("fill",    d => fileColor(d.ext))
      .attr("stroke",  "#0008").attr("stroke-width", 0.5)
      .attr("cursor",  "pointer")
      .call(drag())
      .on("mouseover", (e, d) => {
        const syms = graphData.symbolsByFile[d.id] || [];
        showTip(e, d.label, d.file, syms.length ? syms.length + " symbols" : "no symbols");
      })
      .on("mousemove", moveTip).on("mouseout", hideTip)
      .on("click",    (e, d) => { e.stopPropagation(); selectFile(d); })
      .on("dblclick", (e, d) => {
        e.stopPropagation();
        if ((graphData.symbolsByFile[d.id] || []).length) renderSymbolView(d.id, d.label);
      });

    gLbl.selectAll("text")
      .data(curNodes, d => d.id).join("text")
      .attr("class", "node-label")
      .attr("text-anchor", "start").attr("font-size", 9)
      .attr("fill", "#bbb").attr("pointer-events", "none")
      .text(d => d.label);

    const fileCharge = curNodes.length > 500 ? -30 : curNodes.length > 200 ? -55 : -90;
    const fileCollide = curNodes.length > 500 ? 12 : curNodes.length > 200 ? 18 : 28;

    sim = d3.forceSimulation(curNodes)
      .force("charge",    d3.forceManyBody().strength(fileCharge))
      .force("center",    d3.forceCenter(W / 2, H / 2))
      .force("collision", d3.forceCollide(fileCollide))
      .alphaDecay(0.03);

    const placeFile = () => {
      gNode.selectAll("circle").attr("cx", d => d.x).attr("cy", d => d.y);
      gLbl.selectAll("text").attr("x", d => d.x + 7).attr("y", d => d.y + 3);
      tickEdges();
    };
    settleAndPlace(sim, placeFile);

    // Auto-show depends_on if enabled
    if (document.querySelector('[data-etype="depends_on"]').checked) {
      drawAllEdgesInView(); document.getElementById("show-all-cb").checked = true;
    }
  }

  function selectFile(d) {
    if (selectedId === d.id) { deselect(); return; }
    selectedId = d.id;

    const lines = drawEdgesForNode(d);
    const connIds = new Set([d.id, ...lines.map(e => e.s), ...lines.map(e => e.t)]);

    gNode.selectAll("circle")
      .attr("opacity",      n => connIds.has(n.id) ? 1 : 0.08)
      .attr("stroke",       n => n.id === d.id ? "#fff" : "#0008")
      .attr("stroke-width", n => n.id === d.id ? 2 : 0.5)
      .attr("r",            n => n.id === d.id ? 7 : 5);
    gLbl.selectAll("text").attr("opacity", n => connIds.has(n.id) ? 1 : 0.06);

    Panel.showNodeInfo(d.label, d.file);
    Panel.showFileConnections(d);
    Panel.showSymbolList(d.id);
  }

  /* ==============================================================
     SYMBOL VIEW
     ============================================================== */
  function renderSymbolView(fileId, fileName) {
    const syms = graphData.symbolsByFile[fileId] || [];
    if (!syms.length) return;

    view = "symbols:" + fileId; selectedId = null;
    clearGraph(); stopSim();

    curNodes = syms.map(s => ({
      ...s,
      _r: (s.kind === "class" || s.kind === "interface") ? 8 :
          s.kind === "enum" ? 7 : s.kind === "annotation" ? 6 : 5,
    }));

    document.getElementById("crumb-text").textContent = fileName;
    document.getElementById("back-btn").style.display = "inline-block";
    document.getElementById("show-all-row").style.display = "none";
    document.getElementById("file-legend").style.display = "none";
    document.getElementById("sym-legend").style.display = "";
    document.getElementById("svc-legend").style.display = "none";
    document.getElementById("ext-filters").style.display = "none";
    document.getElementById("ext-title").style.display = "none";
    document.getElementById("search").value = "";
    document.getElementById("search").placeholder = "Filter symbols…";
    Panel.hideNodeInfo();

    setStats(curNodes.length + " symbols in " + fileName);

    gNode.selectAll("circle")
      .data(curNodes, d => d.id).join("circle")
      .attr("r",       d => d._r)
      .attr("fill",    d => symColor(d.kind))
      .attr("stroke",  "#0008").attr("stroke-width", 0.5)
      .attr("cursor",  "pointer")
      .call(drag())
      .on("mouseover", (e, d) => showTip(e, d.name, d.kind, d.line ? "Line " + d.line : ""))
      .on("mousemove", moveTip).on("mouseout", hideTip)
      .on("click",    (e, d) => { e.stopPropagation(); selectSymbol(d); });

    gLbl.selectAll("text")
      .data(curNodes.filter(d => d.kind !== "function" && d.kind !== "method"), d => d.id).join("text")
      .attr("class", "node-label")
      .attr("text-anchor", "middle").attr("font-size", 9)
      .attr("fill", "#ccc").attr("pointer-events", "none")
      .text(d => d.name);

    sim = d3.forceSimulation(curNodes)
      .force("charge",    d3.forceManyBody().strength(-180))
      .force("center",    d3.forceCenter(W / 2, H / 2))
      .force("collision", d3.forceCollide(d => d._r + 14))
      .alphaDecay(0.04);

    const placeSym = () => {
      gNode.selectAll("circle").attr("cx", d => d.x).attr("cy", d => d.y);
      gLbl.selectAll("text").attr("x", d => d.x).attr("y", d => d.y + d._r + 12);
      tickEdges();
    };
    settleAndPlace(sim, placeSym);

    // Draw symbol-level edges
    const nm = nodeMap(), lines = [];
    for (const [kind, elist] of Object.entries(graphData.symbolEdges))
      for (const e of elist)
        if (nm.has(e.s) && nm.has(e.t)) lines.push({ s: e.s, t: e.t, kind });
    renderEdgeLines(lines, nm, null);
  }

  function selectSymbol(d) {
    if (selectedId === d.id) { deselect(); return; }
    selectedId = d.id;
    gNode.selectAll("circle")
      .attr("stroke",       n => n.id === d.id ? "#fff" : "#0008")
      .attr("stroke-width", n => n.id === d.id ? 2 : 0.5);
    Panel.showNodeInfo(d.name, d.kind + " │ Line " + (d.line || "?"));
  }

  /* ==============================================================
     Callbacks from panel
     ============================================================== */
  function onEdgeFilterChange() {
    if (!selectedId) {
      if (document.getElementById("show-all-cb").checked) drawAllEdgesInView();
      else clearEdges();
    } else {
      const d = curNodes.find(n => n.id === selectedId);
      if (d) {
        if (view.startsWith("files")) selectFile(d);
        else if (view === "services") selectService(d);
      }
    }
  }

  function filterCurrentView() {
    if (!view.startsWith("files:")) return;
    const exts = Panel.getActiveExts();
    const hasFilter = exts.size > 0 && exts.size < graphData.topExts.length;
    const opFn = d => (!hasFilter || exts.has(d.ext)) ? 1 : 0.05;
    gNode.selectAll("circle").attr("opacity", opFn);
    gLbl.selectAll("text").attr("opacity", opFn);
  }

  function applySearch(q) {
    gNode.selectAll("circle").attr("opacity", !q ? 1 : d =>
      (d.label?.toLowerCase().includes(q) || d.file?.toLowerCase().includes(q) || d.name?.toLowerCase().includes(q)) ? 1 : 0.04);
    gLbl.selectAll("text").attr("opacity", !q ? 1 : d =>
      (d.label?.toLowerCase().includes(q) || d.name?.toLowerCase().includes(q)) ? 1 : 0.04);
  }

  /* ==============================================================
     Public API — exposed to Panel
     ============================================================== */
  return {
    // State (read by panel)
    get view() { return view; },
    get curNodes() { return curNodes; },
    adj, svcAdj, fileById,

    // Navigation
    renderServiceView, renderFileView, renderSymbolView,
    selectService, selectFile,

    // Edges
    activeTypes, drawAllEdgesInView, clearEdges, deselect,

    // Panel callbacks
    onEdgeFilterChange, filterCurrentView, applySearch,
  };

})();

/* Boot */
Panel.buildExtFilters();
Graph.renderServiceView();
