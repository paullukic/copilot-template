"""Graph visualization generator.

Creates a standalone HTML file with an interactive force-directed graph
using D3.js (inlined from node_modules).  No external Python dependencies required.

Usage:
    from visualize import generate_html
    generate_html(Path("graph.db"), Path("graph.html"))
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Colour palettes
# ---------------------------------------------------------------------------

_NODE_COLORS = {
    "file": "#4a90d9",
    "class": "#9b59b6",
    "function": "#2ecc71",
    "method": "#e67e22",
}

_EDGE_COLORS = {
    "imports": "#95a5a6",
    "contains": "#85c1e9",
    "calls": "#e67e22",
    "tests_for": "#2ecc71",
    "depends_on": "#f39c12",
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_html(db_path: Path, output_path: Path) -> Path:
    """Read *db_path* and write a self-contained interactive HTML graph."""
    conn = sqlite3.connect(db_path)

    nodes = [
        {
            "id": nid,
            "kind": kind,
            "name": name,
            "file": file,
            "start_line": start,
            "end_line": end,
        }
        for nid, kind, name, file, start, end in conn.execute(
            "SELECT id, kind, name, file, start_line, end_line FROM nodes"
        )
    ]

    node_ids = {n["id"] for n in nodes}
    edges = [
        {"source": src, "target": dst, "kind": kind}
        for src, dst, kind in conn.execute("SELECT src, dst, kind FROM edges")
        if src in node_ids and dst in node_ids
    ]

    conn.close()

    # Load d3 from node_modules (installed via npm)
    d3_path = Path(__file__).parent / "node_modules" / "d3" / "dist" / "d3.min.js"
    if not d3_path.exists():
        raise FileNotFoundError(
            f"d3.min.js not found at {d3_path}. "
            "Run 'npm install' in .github/code-graph/ first."
        )
    d3_script = d3_path.read_text(encoding="utf-8")

    html = _HTML_TEMPLATE.replace("/*D3_INLINE*/", d3_script)
    html = html.replace(
        "/*GRAPH_DATA*/",
        f"const graphData = {json.dumps({'nodes': nodes, 'edges': edges})};"
    )
    html = html.replace("/*NODE_COLORS*/", json.dumps(_NODE_COLORS))
    html = html.replace("/*EDGE_COLORS*/", json.dumps(_EDGE_COLORS))

    output_path.write_text(html, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# HTML template (D3.js v7 inlined from node_modules)
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Code Graph</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #1a1a2e; color: #eee; overflow: hidden;
  }

  /* ---- Control panel ---- */
  #controls {
    position: fixed; top: 12px; left: 12px; z-index: 10;
    background: rgba(30,30,50,0.92); padding: 14px 18px;
    border-radius: 8px; font-size: 13px; max-width: 280px;
    backdrop-filter: blur(6px);
  }
  #controls h3 { margin-bottom: 8px; font-size: 15px; color: #fff; }
  #search {
    width: 100%; padding: 6px 10px; border: 1px solid #444;
    border-radius: 4px; background: #2a2a3e; color: #eee;
    font-size: 13px; margin-bottom: 10px; outline: none;
  }
  #search:focus { border-color: #4a90d9; }
  .section-label {
    margin-top: 8px; font-size: 11px; color: #777;
    text-transform: uppercase; letter-spacing: 1px;
  }
  .filter-row {
    display: flex; align-items: center; gap: 6px;
    margin: 4px 0; cursor: pointer;
  }
  .filter-row input { cursor: pointer; }
  .legend-dot {
    display: inline-block; width: 10px; height: 10px; border-radius: 50%;
  }
  .legend-line {
    display: inline-block; width: 18px; height: 3px;
    border-radius: 2px; vertical-align: middle;
  }

  /* ---- Stats bar ---- */
  #stats {
    position: fixed; bottom: 12px; left: 12px; z-index: 10;
    background: rgba(30,30,50,0.92); padding: 8px 14px;
    border-radius: 6px; font-size: 12px; color: #aaa;
    backdrop-filter: blur(6px);
  }

  /* ---- Tooltip ---- */
  #tooltip {
    position: fixed; display: none;
    background: rgba(20,20,40,0.96); border: 1px solid #555;
    border-radius: 6px; padding: 10px 14px;
    font-size: 12px; max-width: 380px; z-index: 20;
    pointer-events: none; backdrop-filter: blur(4px);
  }
  #tooltip .tt-kind {
    color: #888; text-transform: uppercase;
    font-size: 10px; letter-spacing: 1px;
  }
  #tooltip .tt-name { font-weight: 600; font-size: 14px; margin: 2px 0; }
  #tooltip .tt-file { color: #aaa; font-size: 11px; }

  svg { display: block; }
</style>
</head>
<body>

<!-- Control panel -->
<div id="controls">
  <h3>Code Graph</h3>
  <input id="search" type="text" placeholder="Search nodes\u2026" autocomplete="off">

  <div class="section-label">Nodes</div>
  <label class="filter-row">
    <input type="checkbox" data-filter="node" data-kind="file" checked>
    <span class="legend-dot" style="background:#4a90d9"></span> Files
  </label>
  <label class="filter-row">
    <input type="checkbox" data-filter="node" data-kind="class" checked>
    <span class="legend-dot" style="background:#9b59b6"></span> Classes
  </label>
  <label class="filter-row">
    <input type="checkbox" data-filter="node" data-kind="function" checked>
    <span class="legend-dot" style="background:#2ecc71"></span> Functions
  </label>
  <label class="filter-row">
    <input type="checkbox" data-filter="node" data-kind="method" checked>
    <span class="legend-dot" style="background:#e67e22"></span> Methods
  </label>

  <div class="section-label">Edges</div>
  <label class="filter-row">
    <input type="checkbox" data-filter="edge" data-kind="imports" checked>
    <span class="legend-line" style="background:#95a5a6"></span> imports
  </label>
  <label class="filter-row">
    <input type="checkbox" data-filter="edge" data-kind="contains" checked>
    <span class="legend-line" style="background:#85c1e9"></span> contains
  </label>
  <label class="filter-row">
    <input type="checkbox" data-filter="edge" data-kind="calls" checked>
    <span class="legend-line" style="background:#e67e22"></span> calls
  </label>
  <label class="filter-row">
    <input type="checkbox" data-filter="edge" data-kind="tests_for" checked>
    <span class="legend-line" style="background:#2ecc71"></span> tests_for
  </label>
  <label class="filter-row">
    <input type="checkbox" data-filter="edge" data-kind="depends_on" checked>
    <span class="legend-line" style="background:#f39c12"></span> depends_on
  </label>
</div>

<!-- Tooltip -->
<div id="tooltip">
  <div class="tt-kind"></div>
  <div class="tt-name"></div>
  <div class="tt-file"></div>
</div>

<!-- Stats -->
<div id="stats"></div>

<!-- Graph canvas -->
<svg id="graph"></svg>

<script>/*D3_INLINE*/</script>
<script>
/* ------------------------------------------------------------------ */
/* Data injected by visualize.py                                      */
/* ------------------------------------------------------------------ */
/*GRAPH_DATA*/
const NODE_COLORS = /*NODE_COLORS*/;
const EDGE_COLORS = /*EDGE_COLORS*/;

/* ------------------------------------------------------------------ */
/* Layout                                                             */
/* ------------------------------------------------------------------ */
const width  = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("#graph").attr("width", width).attr("height", height);
const g   = svg.append("g");

svg.call(
  d3.zoom().scaleExtent([0.02, 10])
    .on("zoom", e => g.attr("transform", e.transform))
);

document.getElementById("stats").textContent =
  graphData.nodes.length + " nodes \u00b7 " + graphData.edges.length + " edges";

/* ------------------------------------------------------------------ */
/* Force simulation                                                   */
/* ------------------------------------------------------------------ */
const simulation = d3.forceSimulation(graphData.nodes)
  .force("link",      d3.forceLink(graphData.edges).id(d => d.id).distance(60))
  .force("charge",    d3.forceManyBody().strength(-80))
  .force("center",    d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide(12));

/* ---- Edges ---- */
const linkG = g.append("g");
let link = linkG.selectAll("line")
  .data(graphData.edges).join("line")
  .attr("stroke",         d => EDGE_COLORS[d.kind] || "#666")
  .attr("stroke-width",   1)
  .attr("stroke-opacity", 0.4);

/* ---- Nodes ---- */
const nodeG = g.append("g");
let node = nodeG.selectAll("circle")
  .data(graphData.nodes).join("circle")
  .attr("r",            d => d.kind === "file" ? 6 : 4)
  .attr("fill",         d => NODE_COLORS[d.kind] || "#999")
  .attr("stroke",       "#000")
  .attr("stroke-width", 0.5)
  .call(d3.drag()
    .on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
    .on("end",   (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
  );

/* ---- Tooltip ---- */
const tip = document.getElementById("tooltip");
node
  .on("mouseover", (e, d) => {
    tip.style.display = "block";
    tip.querySelector(".tt-kind").textContent = d.kind;
    tip.querySelector(".tt-name").textContent = d.name;
    let info = d.file;
    if (d.start_line) info += ":" + d.start_line;
    if (d.end_line)   info += "-" + d.end_line;
    tip.querySelector(".tt-file").textContent = info;
  })
  .on("mousemove", e => {
    tip.style.left = (e.clientX + 14) + "px";
    tip.style.top  = (e.clientY - 10) + "px";
  })
  .on("mouseout", () => { tip.style.display = "none"; });

/* ---- Click: highlight neighbours ---- */
let highlighted = null;
node.on("click", (e, d) => {
  if (highlighted === d.id) {
    highlighted = null;
    node.attr("opacity", 1);
    link.attr("stroke-opacity", 0.4);
    return;
  }
  highlighted = d.id;
  const connected = new Set([d.id]);
  graphData.edges.forEach(l => {
    const s = typeof l.source === "object" ? l.source.id : l.source;
    const t = typeof l.target === "object" ? l.target.id : l.target;
    if (s === d.id) connected.add(t);
    if (t === d.id) connected.add(s);
  });
  node.attr("opacity", n => connected.has(n.id) ? 1 : 0.08);
  link.attr("stroke-opacity", l => {
    const s = typeof l.source === "object" ? l.source.id : l.source;
    const t = typeof l.target === "object" ? l.target.id : l.target;
    return (s === d.id || t === d.id) ? 0.8 : 0.03;
  });
});

/* ---- Tick ---- */
simulation.on("tick", () => {
  link
    .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("cx", d => d.x).attr("cy", d => d.y);
});

/* ------------------------------------------------------------------ */
/* Search                                                             */
/* ------------------------------------------------------------------ */
document.getElementById("search").addEventListener("input", e => {
  const q = e.target.value.toLowerCase();
  if (!q) { node.attr("opacity", 1); link.attr("stroke-opacity", 0.4); return; }
  node.attr("opacity", d =>
    (d.name.toLowerCase().includes(q) || d.file.toLowerCase().includes(q)) ? 1 : 0.08
  );
  link.attr("stroke-opacity", 0.08);
});

/* ------------------------------------------------------------------ */
/* Filters                                                            */
/* ------------------------------------------------------------------ */
function applyFilters() {
  const nodeVis = {};
  document.querySelectorAll("[data-filter=node]").forEach(cb => {
    nodeVis[cb.dataset.kind] = cb.checked;
  });
  const edgeVis = {};
  document.querySelectorAll("[data-filter=edge]").forEach(cb => {
    edgeVis[cb.dataset.kind] = cb.checked;
  });
  node.attr("display", d => nodeVis[d.kind] ? null : "none");
  link.attr("display", d => edgeVis[d.kind] ? null : "none");
}
document.querySelectorAll("#controls input[type=checkbox]")
  .forEach(cb => cb.addEventListener("change", applyFilters));
</script>
</body>
</html>
"""
