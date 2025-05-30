HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - ORMD Render</title>
  <link rel="stylesheet" href="static/style.css">
  <!-- D3.js for document graph -->
  <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
  <div id="container">
    <div id="sidebar" class="collapsed">
      <button id="collapse-btn" title="Toggle sidebar">☰</button>
      <nav>
        <button id="toggle-raw" class="active">👁 Raw .ormd</button>
        <button id="toggle-graph">🧬 Document Graph</button>
        <button id="toggle-history">✍️ Change History</button>
      </nav>
      <div id="panel-raw" class="panel active">
        <h3>Raw .ormd</h3>
        <pre id="raw-content">{raw_ormd}</pre>
      </div>
      <div id="panel-graph" class="panel">
        <h3>Document Graph</h3>
        <div id="graph-container" style="width:100%;height:400px;"></div>
      </div>
      <div id="panel-history" class="panel">
        <h3>Change History</h3>
        <div id="history-content">{history}</div>
      </div>
    </div>
    <div id="main-doc">
      {main_html}
    </div>
  </div>
  <script>
    // Sidebar toggle logic
    const sidebar = document.getElementById('sidebar');
    const collapseBtn = document.getElementById('collapse-btn');
    collapseBtn.onclick = () => {{
      sidebar.classList.toggle('collapsed');
    }};
    // Panel switching logic
    const panels = ['raw', 'graph', 'history'];
    let ormdLinksData = null; // Will be set by renderGraph injection
    let graphRendered = false;
    panels.forEach(name => {{
      document.getElementById('toggle-' + name).onclick = () => {{
        panels.forEach(n => {{
          document.getElementById('toggle-' + n).classList.remove('active');
          document.getElementById('panel-' + n).classList.remove('active');
        }});
        document.getElementById('toggle-' + name).classList.add('active');
        document.getElementById('panel-' + name).classList.add('active');
        // Render the graph when the graph panel is activated
        if (name === 'graph' && ormdLinksData && !graphRendered) {{
          // Clear previous SVG if any
          const gc = document.getElementById('graph-container');
          gc.innerHTML = '';
          renderGraph(ormdLinksData);
          graphRendered = true;
        }}
      }};
    }});
    // D3.js graph rendering placeholder
    function renderGraph(links) {{
      ormdLinksData = links; // Store globally for panel switching
      const width = document.getElementById('graph-container').clientWidth;
      const height = 400;
      const svg = d3.select('#graph-container').append('svg')
        .attr('width', width)
        .attr('height', height);
      // Example: nodes and links
      // Replace with actual data
      const nodes = links.reduce((acc, l) => {{
        acc.add(l.id);
        acc.add(l.to);
        return acc;
      }}, new Set());
      const nodeData = Array.from(nodes).map(id => ({{id}}));
      const linkData = links.map(l => ({{source: l.id, target: l.to, rel: l.rel}}));
      const simulation = d3.forceSimulation(nodeData)
        .force('link', d3.forceLink(linkData).id(d => d.id).distance(80))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width/2, height/2));
      const link = svg.append('g')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .selectAll('line')
        .data(linkData)
        .enter().append('line')
        .attr('stroke-width', 2);
      const node = svg.append('g')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .selectAll('circle')
        .data(nodeData)
        .enter().append('circle')
        .attr('r', 18)
        .attr('fill', '#1976d2');
      const label = svg.append('g')
        .selectAll('text')
        .data(nodeData)
        .enter().append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '.35em')
        .attr('fill', '#fff')
        .text(d => d.id);
      simulation.on('tick', () => {{
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
        node
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
        label
          .attr('x', d => d.x)
          .attr('y', d => d.y);
      }});
    }}
    // renderGraph();
  </script>
</body>
</html>
'''
