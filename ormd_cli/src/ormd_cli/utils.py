# Replace the HTML_TEMPLATE in src/ormd_cli/utils.py with this:

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - ORMD Render</title>
  <style>
    /* Inlined CSS for full portability */
    body {{
      margin: 0;
      font-family: system-ui, sans-serif;
      background: #121212;
      color: #e0e0e0;
    }}
    #container {{
      display: flex;
      min-height: 100vh;
    }}
    #sidebar {{
      width: 320px;
      background: #1c1c1c;
      border-right: 1px solid #373e47;
      transition: width 0.2s;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      color: #e0e0e0;
    }}
    #sidebar.collapsed {{
      width: 48px;
    }}
    #sidebar.collapsed nav {{
      display: none;
    }}
    #sidebar.collapsed .panel {{
      display: none;
    }}
    #sidebar nav {{
      display: flex;
      flex-direction: column;
      border-bottom: 1px solid #373e47;
    }}
    #sidebar nav button {{
      background: none;
      border: none;
      padding: 16px;
      font-size: 1.2em;
      cursor: pointer;
      text-align: left;
      transition: background 0.1s;
      color: #e0e0e0;
    }}
    #sidebar nav button:hover {{
      background: #333333;
    }}
    #sidebar nav button.active {{
      background: #004080;
      font-weight: bold;
      color: #ffffff;
    }}
    .panel {{
      display: none;
      padding: 16px;
      overflow-y: auto;
      flex: 1;
      background: #1c1c1c;
      color: #e0e0e0;
    }}
    .panel.active {{
      display: block;
    }}
    #collapse-btn {{
      background: none;
      border: none;
      font-size: 1.5em;
      cursor: pointer;
      align-self: flex-end;
      margin: 8px;
      color: #e0e0e0;
    }}
    #collapse-btn:hover {{
      color: #ffffff;
    }}
    #main-doc {{
      flex: 1;
      padding: 40px 5vw;
      background: #121212;
      min-width: 0;
      color: #e0e0e0;
    }}
    pre, code {{
      background: #22272e;
      border: 1px solid #373e47;
      border-radius: 4px;
      padding: 8px;
      font-size: 0.95em;
      overflow-x: auto;
      color: #c9d1d9;
    }}
    .panel h3 {{
      color: #e0e0e0;
      border-bottom: 1px solid #373e47;
      padding-bottom: 8px;
    }}
    
    /* ORMD Link Styles */
    .ormd-link {{ 
      padding: 2px 6px; 
      border-radius: 4px; 
      text-decoration: underline; 
      font-weight: 500; 
    }}
    .ormd-link-supports {{ 
      background: #e3f6e3; 
      color: #217a21; 
      border: 1px solid #b6e6b6; 
    }}
    .ormd-link-refutes {{ 
      background: #ffeaea; 
      color: #b80000; 
      border: 1px solid #ffb3b3; 
    }}
    .ormd-link-related {{ 
      background: #eaf4ff; 
      color: #1a4d80; 
      border: 1px solid #b3d1ff; 
    }}
    .ormd-link-undefined {{ 
      background: #f9e6e6; 
      color: #a94442; 
      border: 1px solid #e4b9b9; 
    }}

    @media (max-width: 700px) {{
      #sidebar {{
        position: absolute;
        z-index: 10;
        height: 100vh;
        left: 0;
        top: 0;
        border-right: 1px solid #373e47;
      }}
      #main-doc {{
        padding: 24px 2vw;
      }}
      #collapse-btn {{
        font-size: 1.8em;
        padding: 8px;
        margin: 4px;
      }}
    }}
  </style>
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
    let ormdLinksData = null;
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
          const gc = document.getElementById('graph-container');
          gc.innerHTML = '';
          renderGraph(ormdLinksData);
          graphRendered = true;
        }}
      }};
    }});
    
    // D3.js graph rendering
    function renderGraph(links) {{
      ormdLinksData = links;
      const width = document.getElementById('graph-container').clientWidth;
      const height = 400;
      const svg = d3.select('#graph-container').append('svg')
        .attr('width', width)
        .attr('height', height);
        
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
  </script>
</body>
</html>
'''