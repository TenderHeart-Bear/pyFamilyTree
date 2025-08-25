// Family Tree D3 Visualization - Simplified Engine
// =================================================

console.log("🌳 Family Tree D3 Script Loaded - Simplified Version");

// Global variables
let svg, g, zoom, treeLayout, selectedNode;
// characterData is loaded from the HTML template

// Simple color palette for generations
const generationColors = [
    '#1f77b4', // Blue - Virtual root (hidden)
    '#ff7f0e', // Orange - Root ancestors  
    '#2ca02c', // Green - Generation 2
    '#d62728', // Red - Generation 3
    '#9467bd', // Purple - Generation 4
    '#8c564b', // Brown - Generation 5
    '#e377c2', // Pink - Generation 6
    '#17becf', // Cyan - Generation 7
    '#bcbd22'  // Olive - Generation 8
];

function getGenerationColor(depth) {
    const idx = Math.abs(depth || 0) % generationColors.length;
    return generationColors[idx];
}

// Text measurement utilities
function measureTextWidth(text, font) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    context.font = font;
    return context.measureText(text).width;
}

function computeCardWidth(name) {
    const font = '12px Arial';
    const padding = 20;
    const minWidth = 100;
    const maxWidth = 180;
    const measuredWidth = measureTextWidth(name || '', font) + padding;
    return Math.max(minWidth, Math.min(maxWidth, Math.round(measuredWidth)));
}

// =================================================
// SIMPLIFIED TREE BUILDING
// =================================================

function buildSimplifiedTree() {
    console.group('🌳 Building Simplified Family Tree');
    console.log('Total people:', Object.keys(characterData).length);
    
    // Step 1: Python has already calculated the root ancestor(s) for us
    // We just need to find the people marked with is_root_ancestor = true
    const pythonRootAncestors = [];
    for (const [id, person] of Object.entries(characterData)) {
        if (person.is_root_ancestor === true) {
            pythonRootAncestors.push(id);
            console.log(`✅ Python identified root ancestor: ${person.name} (${id})`);
        }
    }
    
    console.log(`🧠 Using Python-calculated root ancestors: ${pythonRootAncestors.length}`);
    
    if (pythonRootAncestors.length === 0) {
        console.error('❌ No root ancestors found by Python. Cannot build tree.');
        console.groupEnd();
        return;
    }
    
    // Step 2: Build the tree structure from Python's root ancestor(s)
    let treeData;
    
    if (pythonRootAncestors.length === 1) {
        // Single root ancestor - build unified tree
        const rootPerson = pythonRootAncestors[0];
        console.log(`🌳 Building single unified tree from Python root: ${characterData[rootPerson]?.name}`);
        treeData = buildPersonTree(rootPerson, new Set());
    } else {
        // Multiple root ancestors - this is a complete tree view
        console.log(`🌳 Building complete tree with ${pythonRootAncestors.length} root branches from Python`);
        const rootTrees = [];
        const processed = new Set();
        
        for (const rootId of pythonRootAncestors) {
            if (!processed.has(rootId)) {
                const rootTree = buildPersonTree(rootId, processed);
                rootTrees.push(rootTree);
            }
        }
        
        treeData = {
            name: "Complete Family Tree",
            children: rootTrees
        };
    }
    
    console.log('Created tree with', pythonRootAncestors.length, 'root element(s)');
    console.groupEnd();
    
    // Return the tree data for the caller to use
    return treeData;
}

function buildPersonTree(personId, processed) {
        if (processed.has(personId)) {
            return null;
        }
        processed.add(personId);
        
        const person = characterData[personId];
        if (!person) {
            return null;
        }
        
    console.log(`Building tree for: ${person.name}`);
        
    // Create person node
        const node = {
            id: personId,
            name: person.name || personId,
            data: person,
            children: []
        };
        
    // Add spouse information (but don't create separate tree for spouse)
        if (person.spouse_id && characterData[person.spouse_id]) {
        const spouse = characterData[person.spouse_id];
                node.spouse = {
                    id: person.spouse_id,
            name: spouse.name || person.spouse_id,
            data: spouse
        };
    }
    
    // Find children
    const children = [];
        for (const [childId, childData] of Object.entries(characterData)) {
        const isChild = childData.father_id === personId || childData.mother_id === personId;
        const isSpouseChild = node.spouse && 
            (childData.father_id === node.spouse.id || childData.mother_id === node.spouse.id);
        
        if (isChild || isSpouseChild) {
            children.push(childId);
        }
    }
    
    // Build subtrees for children
    for (const childId of children) {
        const childTree = buildPersonTree(childId, processed);
        if (childTree) {
            node.children.push(childTree);
        }
    }
    
    // Sort children by birth year
        if (node.children.length > 0) {
            node.children.sort((a, b) => {
            const yearA = parseInt((a.data.birthday || "1900").match(/\d{4}/) || "1900");
            const yearB = parseInt((b.data.birthday || "1900").match(/\d{4}/) || "1900");
                return yearA - yearB;
            });
        }
        
    console.log(`${person.name} has ${node.children.length} children`);
        return node;
    }

// =================================================
// SIMPLIFIED LAYOUT & DRAWING
// =================================================

function drawSimplifiedTree(treeData) {
    console.group('🎨 Drawing Simplified Tree');
    
    // Clear existing content
    g.selectAll("*").remove();
    
    // Create D3 hierarchy
    const root = d3.hierarchy(treeData);
    
    // Calculate tree layout
    const width = window.innerWidth - 100;
    const height = window.innerHeight - 100;
    
    treeLayout = d3.tree()
        .size([width, height])
        .separation((a, b) => {
            // Dynamic separation based on content
            let baseSep = 1.5;
            
            // More space for nodes with spouses
            if ((a.data.spouse) || (b.data.spouse)) {
                baseSep += 0.8;
            }
            
            // More space for siblings
            if (a.parent === b.parent) {
                baseSep += 0.3;
            }
            
            return baseSep;
        });
    
    treeLayout(root);
    
    // Apply collision detection and spacing improvements
    applyCollisionDetection(root.descendants());
    
    // Get all nodes except virtual root
    const nodes = root.descendants().filter(d => d.data.id !== "virtual_root");
    
    console.log(`Drawing ${nodes.length} nodes`);
    
    // Draw links (parent-child connections)
    drawLinks(root);
    
    // Draw nodes
    drawNodes(nodes);
    
    // Center the tree
    centerTree();
    
    console.groupEnd();
}

function applyCollisionDetection(nodes) {
    const nodesByDepth = d3.group(nodes, d => d.depth);
    const minGap = 50;
    
    nodesByDepth.forEach((depthNodes) => {
        depthNodes.sort((a, b) => a.x - b.x);
        
        for (let i = 1; i < depthNodes.length; i++) {
            const current = depthNodes[i];
            const previous = depthNodes[i - 1];
            
            const currentWidth = computeCardWidth(current.data.name);
            const previousWidth = computeCardWidth(previous.data.name);
            
            // Add extra width for spouses
            const currentTotalWidth = currentWidth + (current.data.spouse ? 150 : 0);
            const previousTotalWidth = previousWidth + (previous.data.spouse ? 150 : 0);
            
            const requiredGap = (previousTotalWidth / 2) + (currentTotalWidth / 2) + minGap;
            const currentGap = current.x - previous.x;
            
            if (currentGap < requiredGap) {
                const adjustment = requiredGap - currentGap;
                current.x += adjustment;
                
                // Propagate adjustment to following nodes
                for (let j = i + 1; j < depthNodes.length; j++) {
                    depthNodes[j].x += adjustment;
                }
            }
        }
    });
}

function drawLinks(root) {
    const links = root.links().filter(d => 
        d.source.data.id !== "virtual_root" && d.target.data.id !== "virtual_root"
    );
    
    g.selectAll(".link")
        .data(links)
        .enter()
        .append("path")
        .attr("class", "link")
        .attr("stroke", "#666")
        .attr("stroke-width", 2)
        .attr("fill", "none")
        .attr("d", d => {
            const sourceY = d.source.y + 20;
            const targetY = d.target.y - 20;
            return `M ${d.source.x},${sourceY} L ${d.target.x},${targetY}`;
        });
}

function drawNodes(nodes) {
    // Create all display nodes (including spouses)
    const allDisplayNodes = [];
    const spouseTracker = new Set();
    
    nodes.forEach(d => {
        // Add main person
        allDisplayNodes.push({
            ...d,
            isSpouse: false,
            displayName: d.data.name || d.data.id
        });
        
        // Add spouse if exists and not already added
        if (d.data.spouse && !spouseTracker.has(d.data.spouse.id)) {
            allDisplayNodes.push({
                ...d,
                id: d.data.spouse.id,
                data: d.data.spouse.data,
                isSpouse: true,
                displayName: d.data.spouse.name,
                x: d.x + 130, // Position spouse to the right
                y: d.y
            });
            spouseTracker.add(d.data.spouse.id);
        }
    });
    
    // Create node groups
    const nodeGroups = g.selectAll(".node")
        .data(allDisplayNodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`)
        .style("cursor", "pointer")
        .on("click", handleNodeClick)
        .on("mouseenter", handleNodeHover);
    
    // Add rectangles
    nodeGroups.append("rect")
        .attr("width", d => computeCardWidth(d.displayName))
        .attr("height", 35)
        .attr("x", d => -computeCardWidth(d.displayName) / 2)
        .attr("y", -17.5)
        .attr("rx", 8)
        .attr("ry", 8)
        .attr("fill", d => getGenerationColor(d.depth))
        .attr("fill-opacity", 0.15)
        .attr("stroke", d => getGenerationColor(d.depth))
        .attr("stroke-width", 2);
    
    // Add text labels
    nodeGroups.append("text")
        .attr("dy", "0.35em")
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .style("font-weight", "bold")
        .style("fill", "#2c3e50")
        .style("pointer-events", "none")
        .text(d => d.displayName);
    
    // Add spouse connection lines
    nodes.forEach(d => {
        if (d.data.spouse && !spouseTracker.has(`connection_${d.data.id}`)) {
            g.append("line")
                .attr("class", "spouse-connection")
                .attr("x1", d.x + computeCardWidth(d.data.name) / 2)
                .attr("y1", d.y)
                .attr("x2", d.x + 130 - computeCardWidth(d.data.spouse.name) / 2)
                .attr("y2", d.y)
                .attr("stroke", "#e74c3c")
                .attr("stroke-width", 2)
                .attr("stroke-dasharray", "5,5");
            
            spouseTracker.add(`connection_${d.data.id}`);
        }
    });
}

function centerTree() {
    const bounds = g.node().getBBox();
    const fullWidth = svg.node().clientWidth;
    const fullHeight = svg.node().clientHeight;
    
    const width = bounds.width;
    const height = bounds.height;
    const midX = bounds.x + width / 2;
    const midY = bounds.y + height / 2;
    
    const scale = Math.min(fullWidth / width, fullHeight / height) * 0.8;
    const translateX = fullWidth / 2 - midX * scale;
    const translateY = fullHeight / 2 - midY * scale;
    
    svg.call(zoom.transform, d3.zoomIdentity
        .translate(translateX, translateY)
        .scale(Math.min(scale, 1))
    );
}

// =================================================
// EVENT HANDLERS
// =================================================

function handleNodeClick(event, d) {
    // Remove previous selection
    g.selectAll(".node rect").classed("selected", false);
    
    // Select current node
    d3.select(this).select("rect").classed("selected", true);
    selectedNode = d3.select(this);
    
    // Get person data
    const personId = d.isSpouse ? d.id : d.data.id;
    const personData = characterData[personId];
    
    if (personData) {
        updateDetailPanel(personData);
        updateStatus(`Selected: ${personData.name}`);
    }
}

function handleNodeHover(event, d) {
    const name = d.displayName || d.data.name || d.data.id;
    updateStatus(`${name} - Click for details`);
}

function handleZoom(event) {
    g.attr("transform", event.transform);
}

// =================================================
// INITIALIZATION
// =================================================

function initializeSimplifiedTree() {
    console.log("🚀 Initializing Simplified Family Tree");
    
    // Debug: Check if characterData exists and has content
    console.log("Character data check:", {
        exists: typeof characterData !== 'undefined',
        count: typeof characterData !== 'undefined' ? Object.keys(characterData).length : 0,
        sample: typeof characterData !== 'undefined' ? Object.keys(characterData).slice(0, 3) : []
    });
    
    if (typeof characterData === 'undefined' || Object.keys(characterData).length === 0) {
        console.error("❌ No character data available!");
        return;
    }
    
    // Check if the tree-svg element exists
    const svgContainer = d3.select("#tree-svg");
    if (svgContainer.empty()) {
        console.error("❌ #tree-svg element not found!");
        return;
    }
    
    // Create SVG
    svg = svgContainer
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100vh")
        .style("background", "white");
    
    // Create zoom behavior
    zoom = d3.zoom()
        .scaleExtent([0.1, 5])
        .on("zoom", handleZoom);
    
    svg.call(zoom);
    
    // Create main group
    g = svg.append("g");
    
    // Build and draw tree
    try {
        const treeData = buildSimplifiedTree();
        if (treeData && treeData.children && treeData.children.length > 0) {
            drawSimplifiedTree(treeData);
            console.log("✅ Simplified Family Tree Initialized");
        } else {
            console.error("❌ No tree data generated!");
        }
    } catch (error) {
        console.error("❌ Error initializing tree:", error);
    }
}

// =================================================
// UTILITY FUNCTIONS
// =================================================

function updateStatus(message) {
    // Update status display if it exists
    const statusElement = document.getElementById("status");
    if (statusElement) {
        statusElement.textContent = message;
    }
}

function updateDetailPanel(personData) {
    console.log("Selected person:", personData);
    // Update detail panel if it exists
    const detailPanel = document.getElementById("detail-panel");
    if (detailPanel) {
        detailPanel.innerHTML = `
            <h3>${personData.name}</h3>
            <p><strong>ID:</strong> ${personData.id || 'N/A'}</p>
            <p><strong>Birth:</strong> ${personData.birthday || personData.birth_date || 'N/A'}</p>
            <p><strong>Death:</strong> ${personData.death_date || 'N/A'}</p>
            <p><strong>Father:</strong> ${personData.father_id ? characterData[personData.father_id]?.name || personData.father_id : 'N/A'}</p>
            <p><strong>Mother:</strong> ${personData.mother_id ? characterData[personData.mother_id]?.name || personData.mother_id : 'N/A'}</p>
            <p><strong>Spouse:</strong> ${personData.spouse_id ? characterData[personData.spouse_id]?.name || personData.spouse_id : 'N/A'}</p>
        `;
    }
}

// CSS for selection highlighting
const style = document.createElement('style');
style.textContent = `
    .node rect.selected {
        stroke: #ff4444 !important;
        stroke-width: 4px !important;
        filter: drop-shadow(0 0 8px rgba(255, 68, 68, 0.6));
    }
    
    .link {
        transition: stroke-width 0.2s ease;
    }
    
    .spouse-connection {
        transition: stroke-width 0.2s ease;
    }
`;
document.head.appendChild(style);

// Initialize when everything is ready
function startInitialization() {
    console.log("🔍 Checking initialization requirements...");
    
    // Check if D3 is loaded
    if (typeof d3 === 'undefined') {
        console.log("⏳ Waiting for D3 to load...");
        setTimeout(startInitialization, 100);
        return;
    }
    
    // Check if characterData exists
    if (typeof characterData === 'undefined') {
        console.log("⏳ Waiting for character data...");
        setTimeout(startInitialization, 100);
        return;
    }
    
    // Check if characterData has content
    if (Object.keys(characterData).length === 0) {
        console.log("⏳ Character data is empty, waiting...");
        setTimeout(startInitialization, 100);
        return;
    }
    
    // Check if DOM element exists
    if (!document.getElementById("tree-svg")) {
        console.log("⏳ Waiting for #tree-svg element...");
        setTimeout(startInitialization, 100);
        return;
    }
    
    console.log("✅ All requirements met, initializing tree...");
    initializeSimplifiedTree();
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', startInitialization);

// Also try when window loads (fallback)
window.addEventListener('load', () => {
    if (!svg) { // Only if not already initialized
        console.log("🔄 Window loaded, trying initialization again...");
        startInitialization();
    }
});

console.log("📝 Simplified D3 Family Tree Script Ready");
