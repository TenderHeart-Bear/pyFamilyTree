// D3.js Family Tree Viewer Script
// Character data will be injected by Python

// D3.js variables
let svg, g, zoom, simulation;
let selectedNode = null;
let currentZoom = 1;

// Tree layout - use vertical layout for top-down view
const treeLayout = d3.tree().size([window.innerWidth - 500, window.innerHeight - 200]);

// Initialize the viewer
document.addEventListener('DOMContentLoaded', function() {
    initializeTree();
});

function initializeTree() {
    // Create SVG with full height
    svg = d3.select("#tree-svg")
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100vh")
        .style("background", "white");
    
    // Create zoom behavior
    zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on("zoom", handleZoom);
    
    svg.call(zoom);
    
    // Create main group
    g = svg.append("g");
    
    // Build tree data
    const treeData = buildTreeData();
    
    // Create hierarchy
    const root = d3.hierarchy(treeData);
    
    // Apply tree layout with better spacing for vertical layout
    const containerWidth = window.innerWidth - 500;
    const containerHeight = window.innerHeight - 200;
    treeLayout.size([containerWidth, containerHeight])(root);
    treeLayout.nodeSize([300, 120])(root);
    
    // Draw the tree
    drawTree(root);
    
    // Fit to window initially
    setTimeout(() => fitToWindow(), 100);
}

function buildTreeData() {
    // Find root nodes (people without parents or with parents not in data)
    const rootNodes = [];
    const processed = new Set();
    
    // First, find all people without parents (root nodes)
    for (const [id, person] of Object.entries(characterData)) {
        const fatherId = person.father_id;
        const motherId = person.mother_id;
        
        // If no parents or parents not in data, this is a root node
        if ((!fatherId || !characterData[fatherId]) && 
            (!motherId || !characterData[motherId])) {
            if (!processed.has(id)) {
                const node = createTreeNode(id, person, processed);
                rootNodes.push(node);
                processed.add(id);
            }
        }
    }
    
    // If no root nodes found, just use the first person as root
    if (rootNodes.length === 0) {
        const firstPerson = Object.entries(characterData)[0];
        if (firstPerson) {
            const [id, person] = firstPerson;
            const node = createTreeNode(id, person, processed);
            rootNodes.push(node);
            processed.add(id);
        }
    }
    
    // If multiple root nodes, just use the first one (no virtual root)
    if (rootNodes.length > 1) {
        return rootNodes[0];
    } else if (rootNodes.length === 1) {
        return rootNodes[0];
    } else {
        return { id: "empty", name: "No data" };
    }
}

function createTreeNode(id, person, processed) {
    const node = {
        id: id,
        name: person.name || id,
        data: person,
        children: []
    };
    
    // Add children (only parent-child relationships, not spouses)
    const children = [];
    for (const [childId, childData] of Object.entries(characterData)) {
        if (childData.father_id === id || childData.mother_id === id) {
            if (!processed.has(childId)) {
                children.push(createTreeNode(childId, childData, processed));
                processed.add(childId);
            }
        }
    }
    
    if (children.length > 0) {
        children.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
        node.children = children;
    }
    
    return node;
}

function drawTree(root) {
    // Clear existing content
    g.selectAll("*").remove();
    
    // Create links - use vertical layout
    const links = g.selectAll(".link")
        .data(root.links())
        .enter().append("path")
        .attr("class", "link")
        .attr("d", d3.linkVertical()
            .x(d => d.x)
            .y(d => d.y));
    
    // Create nodes
    const nodes = g.selectAll(".node")
        .data(root.descendants())
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`);
    
    // Add node circles
    nodes.append("circle")
        .attr("r", 15)
        .attr("fill", d => "#3498db")
        .attr("stroke", "#2c3e50")
        .attr("stroke-width", 2);
    
    // Add node labels
    nodes.append("text")
        .attr("class", "node-label")
        .attr("dy", "0.35em")
        .attr("y", 25)
        .text(d => d.data.name)
        .style("font-size", "14px")
        .style("font-weight", "bold")
        .style("fill", "#2c3e50")
        .style("text-anchor", "middle")
        .style("pointer-events", "none");
    
    // Add spouse nodes separately
    addSpouseNodes();
    
    // Add spouse connections
    addSpouseConnections();
    
    // Add click events
    nodes.on("click", handleNodeClick);
    
    // Add hover events
    nodes.on("mouseenter", handleNodeHover);
    nodes.on("mouseleave", handleNodeLeave);
}

function addSpouseNodes() {
    // Find all spouses that aren't already in the tree
    const existingNodes = new Set();
    g.selectAll(".node").each(function(d) {
        existingNodes.add(d.data.id);
    });
    
    // Add spouse nodes next to their partners
    g.selectAll(".node").each(function(d) {
        const personId = d.data.id;
        const personData = characterData[personId];
        const spouseId = personData.spouse_id;
        
        if (spouseId && characterData[spouseId] && !existingNodes.has(spouseId)) {
            // Create spouse node next to the person
            const spouseData = characterData[spouseId];
            const spouseX = d.x + 100;
            const spouseY = d.y;
            
            const spouseGroup = g.append("g")
                .attr("class", "node spouse-node")
                .attr("transform", `translate(${spouseX},${spouseY})`)
                .attr("data-person-id", spouseId);
            
            // Add spouse circle
            spouseGroup.append("circle")
                .attr("r", 15)
                .attr("fill", "#e74c3c")
                .attr("stroke", "#2c3e50")
                .attr("stroke-width", 2);
            
            // Add spouse label
            spouseGroup.append("text")
                .attr("class", "node-label")
                .attr("dy", "0.35em")
                .attr("y", 25)
                .text(spouseData.name)
                .style("font-size", "14px")
                .style("font-weight", "bold")
                .style("fill", "#2c3e50")
                .style("text-anchor", "middle")
                .style("pointer-events", "none");
            
            // Add click events for spouse nodes
            spouseGroup.on("click", function(event) {
                handleNodeClick(event, { data: { id: spouseId }, x: spouseX, y: spouseY });
            });
            
            // Add hover events for spouse nodes
            spouseGroup.on("mouseenter", function(event) {
                handleNodeHover(event, { data: { id: spouseId }, x: spouseX, y: spouseY });
            });
            spouseGroup.on("mouseleave", function(event) {
                handleNodeLeave(event, { data: { id: spouseId }, x: spouseX, y: spouseY });
            });
            
            existingNodes.add(spouseId);
        }
    });
}

function addSpouseConnections() {
    // Add spouse connections (dashed lines between spouses)
    const spouseConnections = [];
    
    console.log("🔍 Debugging spouse connections...");
    console.log("Character data:", characterData);
    
    for (const [id, person] of Object.entries(characterData)) {
        const spouseId = person.spouse_id;
        if (spouseId && characterData[spouseId]) {
            // Only add one direction to avoid duplicates
            if (id < spouseId) {
                spouseConnections.push({
                    source: id,
                    target: spouseId,
                    type: 'spouse'
                });
                console.log(`💕 Found spouse connection: ${person.name} (${id}) ↔ ${characterData[spouseId].name} (${spouseId})`);
            }
        }
    }
    
    console.log(`🎯 Creating ${spouseConnections.length} spouse connections:`, spouseConnections);
    
    // Draw spouse connections
    g.selectAll(".spouse-link")
        .data(spouseConnections)
        .enter().append("path")
        .attr("class", "spouse-link")
        .attr("d", d => {
            // Find the positions of the spouse nodes - check both main nodes and spouse nodes
            let sourceNode = g.selectAll(".node").filter(function() {
                const nodeData = d3.select(this).datum();
                return nodeData && nodeData.data && nodeData.data.id === d.source;
            });
            let targetNode = g.selectAll(".node").filter(function() {
                const nodeData = d3.select(this).datum();
                return nodeData && nodeData.data && nodeData.data.id === d.target;
            });
            
            // If not found in main nodes, check spouse nodes
            if (sourceNode.empty()) {
                sourceNode = g.selectAll(".spouse-node").filter(function() {
                    return d3.select(this).attr("data-person-id") === d.source;
                });
            }
            if (targetNode.empty()) {
                targetNode = g.selectAll(".spouse-node").filter(function() {
                    return d3.select(this).attr("data-person-id") === d.target;
                });
            }
            
            console.log(`🔗 Drawing spouse link: ${d.source} → ${d.target}`);
            console.log(`  Source node found: ${!sourceNode.empty()}`);
            console.log(`  Target node found: ${!targetNode.empty()}`);
            
            if (!sourceNode.empty() && !targetNode.empty()) {
                let sourceX, sourceY, targetX, targetY;
                
                // Get position from main tree node
                const sourceDatum = sourceNode.datum();
                if (sourceDatum && sourceDatum.x !== undefined && sourceDatum.y !== undefined) {
                    sourceX = sourceDatum.x;
                    sourceY = sourceDatum.y;
                } else {
                    // Get position from spouse node transform
                    const sourceTransform = sourceNode.attr("transform");
                    const match = sourceTransform.match(/translate\\(([^,]+),([^)]+)\\)/);
                    if (match) {
                        sourceX = parseFloat(match[1]);
                        sourceY = parseFloat(match[2]);
                    }
                }
                
                const targetDatum = targetNode.datum();
                if (targetDatum && targetDatum.x !== undefined && targetDatum.y !== undefined) {
                    targetX = targetDatum.x;
                    targetY = targetDatum.y;
                } else {
                    // Get position from spouse node transform
                    const targetTransform = targetNode.attr("transform");
                    const match = targetTransform.match(/translate\\(([^,]+),([^)]+)\\)/);
                    if (match) {
                        targetX = parseFloat(match[1]);
                        targetY = parseFloat(match[2]);
                    }
                }
                
                if (sourceX !== undefined && sourceY !== undefined && 
                    targetX !== undefined && targetY !== undefined) {
                    console.log(`  Source position: (${sourceX}, ${sourceY})`);
                    console.log(`  Target position: (${targetX}, ${targetY})`);
                    
                    return d3.linkVertical()
                        .x(d => d.x)
                        .y(d => d.y)({
                            source: { x: sourceX, y: sourceY },
                            target: { x: targetX, y: targetY }
                        });
                }
            }
            console.log(`  ❌ Could not find nodes for spouse connection`);
            return "";
        })
        .attr("stroke", "#e74c3c")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "5,5")
        .attr("fill", "none")
        .style("opacity", 0.6);
}

function handleZoom(event) {
    g.attr("transform", event.transform);
    currentZoom = event.transform.k;
    updateStatus(`Zoom: ${Math.round(currentZoom * 100)}%`);
}

function handleNodeClick(event, d) {
    // Handle both direct clicks and programmatic calls
    let nodeData, nodeElement;
    
    if (event && event.currentTarget) {
        // Direct click event
        nodeElement = d3.select(event.currentTarget);
        nodeData = nodeElement.datum();
    } else if (d && d.data) {
        // Programmatic call with data
        nodeData = d;
        nodeElement = d3.select(event); // event is actually the element
    } else {
        console.error("Invalid click event or data");
        return;
    }
    
    // Remove previous selection
    if (selectedNode) {
        selectedNode.select("circle").classed("selected", false);
    }
    
    // Select new node
    selectedNode = nodeElement;
    selectedNode.select("circle").classed("selected", true);
    
    // Show person details
    showPersonDetails(nodeData.data.id);
    updateStatus(`Selected: ${nodeData.data.name}`);
}

function handleNodeHover(event, d) {
    const personData = characterData[d.data.id];
    if (personData) {
        updateStatus(`${personData.name || d.data.id} - Click for details`);
    }
}

function handleNodeLeave(event, d) {
    updateStatus('Click on a person to see details | Drag to pan | Scroll to zoom');
}

function showPersonDetails(personId) {
    const personData = characterData[personId];
    const detailsContainer = document.getElementById('person-details');
    
    if (!personData) {
        detailsContainer.innerHTML = `
            <div class="person-info">
                <h3>Person Not Found</h3>
                <p>No data available for ID: ${personId}</p>
            </div>
        `;
        return;
    }
    
    const name = personData.name || 'Unknown';
    const birthDate = personData.birth_date || '';
    const deathDate = personData.death_date || '';
    const marriageDate = personData.marriage_date || '';
    const spouseId = personData.spouse_id || '';
    const fatherId = personData.father_id || '';
    const motherId = personData.mother_id || '';
    
    let spouseName = '';
    if (spouseId && characterData[spouseId]) {
        spouseName = characterData[spouseId].name || spouseId;
    }
    
    let fatherName = '';
    if (fatherId && characterData[fatherId]) {
        fatherName = characterData[fatherId].name || fatherId;
    }
    
    let motherName = '';
    if (motherId && characterData[motherId]) {
        motherName = characterData[motherId].name || motherId;
    }
    
    detailsContainer.innerHTML = `
        <div class="person-info">
            <h3>${name}</h3>
            <p><strong>ID:</strong> ${personId}</p>
            ${birthDate ? `<p><strong>Birth:</strong> ${birthDate}</p>` : ''}
            ${deathDate ? `<p><strong>Death:</strong> ${deathDate}</p>` : ''}
            ${marriageDate ? `<p><strong>Marriage:</strong> ${marriageDate}</p>` : ''}
            ${spouseName ? `<p><strong>Spouse:</strong> ${spouseName}</p>` : ''}
            ${fatherName ? `<p><strong>Father:</strong> ${fatherName}</p>` : ''}
            ${motherName ? `<p><strong>Mother:</strong> ${motherName}</p>` : ''}
        </div>
    `;
}

function searchPeople(query) {
    const resultsContainer = document.getElementById('search-results');
    
    if (!query.trim()) {
        resultsContainer.innerHTML = '';
        return;
    }
    
    const matches = [];
    for (const [id, person] of Object.entries(characterData)) {
        const name = person.name || '';
        if (name.toLowerCase().includes(query.toLowerCase())) {
            matches.push({ id, name });
        }
    }
    
    if (matches.length === 0) {
        resultsContainer.innerHTML = '<div class="search-result">No matches found</div>';
        return;
    }
    
    resultsContainer.innerHTML = matches
        .slice(0, 10)
        .map(match => `
            <div class="search-result" onclick="selectPerson('${match.id}')">
                ${match.name} (${match.id})
            </div>
        `)
        .join('');
}

function selectPerson(personId) {
    // Find and select the node
    const nodes = g.selectAll(".node");
    nodes.each(function(d) {
        if (d.data.id === personId) {
            d3.select(this).dispatch("click");
            centerOnNode(d);
        }
    });
    
    // Clear search
    document.getElementById('search-input').value = '';
    document.getElementById('search-results').innerHTML = '';
}

function centerOnNode(node) {
    const transform = d3.zoomIdentity
        .translate(window.innerWidth / 2 - node.x, window.innerHeight / 2 - node.y)
        .scale(1);
    
    d3.select(svg.node()).transition().duration(750).call(zoom.transform, transform);
}

function zoomIn() {
    d3.select(svg.node()).transition().duration(300).call(zoom.scaleBy, 1.3);
}

function zoomOut() {
    d3.select(svg.node()).transition().duration(300).call(zoom.scaleBy, 1 / 1.3);
}

function resetView() {
    d3.select(svg.node()).transition().duration(750).call(zoom.transform, d3.zoomIdentity);
}

function fitToWindow() {
    const svgElement = document.querySelector('svg');
    const treeContainer = document.querySelector('.tree-container');
    
    if (!svgElement || !treeContainer) return;
    
    const svgRect = svgElement.getBoundingClientRect();
    const containerRect = treeContainer.getBoundingClientRect();
    
    // Calculate zoom to fit with some padding
    const zoomX = (containerRect.width - 100) / svgRect.width;
    const zoomY = (containerRect.height - 100) / svgRect.height;
    currentZoom = Math.min(zoomX, zoomY, 1) * 0.9;
    
    // Center the SVG
    const scaledWidth = svgRect.width * currentZoom;
    const scaledHeight = svgRect.height * currentZoom;
    
    const translateX = (containerRect.width - scaledWidth) / 2;
    const translateY = (containerRect.height - scaledHeight) / 2;
    
    // Apply transform using d3.select instead of direct svg reference
    const transform = d3.zoomIdentity
        .translate(translateX, translateY)
        .scale(currentZoom);
    
    d3.select(svgElement).transition().duration(750).call(zoom.transform, transform);
    updateStatus(`Fitted to window - Zoom: ${Math.round(currentZoom * 100)}%`);
}

function centerOnSelected() {
    if (selectedNode) {
        const node = selectedNode.datum();
        centerOnNode(node);
    }
}

function updateStatus(message) {
    const statusElement = document.getElementById('status');
    if (statusElement) {
        statusElement.textContent = message;
    }
}

// Handle window resize
window.addEventListener('resize', function() {
    // Recalculate tree layout with full height
    const containerWidth = window.innerWidth - 500;
    const containerHeight = window.innerHeight - 200;
    
    const root = d3.hierarchy(buildTreeData());
    treeLayout.size([containerWidth, containerHeight])(root);
    treeLayout.nodeSize([300, 120])(root);
    drawTree(root);
    
    // Refit to window
    setTimeout(() => fitToWindow(), 100);
}); 