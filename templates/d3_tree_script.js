// D3.js Family Tree Viewer Script
// Character data will be injected by Python

// D3.js variables
let svg, g, zoom, simulation;
let selectedNode = null;
let currentZoom = 1;

// Utility: measure text width for dynamic card sizing
function measureTextWidth(text, font) {
    const context = measureTextWidth._ctx || (measureTextWidth._ctx = document.createElement('canvas').getContext('2d'));
    context.font = font || '12px Arial';
    return context.measureText(text || '').width;
}

// Create an orthogonal elbow path (vertical → horizontal → vertical)
function createElbowPath(sourceX, sourceY, targetX, targetY) {
    const midY = sourceY + (targetY - sourceY) / 2;
    return `M ${sourceX},${sourceY} V ${midY} H ${targetX} V ${targetY}`;
}

// Generation color scheme (by depth/generation)
const generationPalette = [
    '#1f77b4', // Gen 0
    '#ff7f0e', // Gen 1
    '#2ca02c', // Gen 2
    '#d62728', // Gen 3
    '#9467bd', // Gen 4
    '#8c564b', // Gen 5
    '#e377c2', // Gen 6
    '#17becf', // Gen 7
    '#bcbd22', // Gen 8
    '#7f7f7f'  // Gen 9
];

function getGenerationColor(depth) {
    const idx = Math.abs(depth || 0) % generationPalette.length;
    return generationPalette[idx];
}

function computeCardWidthByName(name) {
    const font = '12px Arial';
    const horizontalPadding = 14;
    const measuredWidth = measureTextWidth(name || '', font) + horizontalPadding * 2;
    return Math.max(90, Math.min(170, Math.round(measuredWidth)));
}

function computeSpouseOffsetByIds(personId, spouseId) {
    const personName = (characterData[personId] && characterData[personId].name) ? characterData[personId].name : personId;
    const spouseName = (characterData[spouseId] && characterData[spouseId].name) ? characterData[spouseId].name : spouseId;
    const personWidth = computeCardWidthByName(personName);
    const spouseWidth = computeCardWidthByName(spouseName);
    const desiredGap = 28; // increased gap between spouses for readability
    return (personWidth / 2) + (spouseWidth / 2) + desiredGap;
}

// Compute half extents for a node, accounting for spouse span to the right
function getNodeHalfExtents(node) {
    const id = node && node.data ? node.data.id : null;
    const person = id ? characterData[id] : null;
    const width = node.cardWidth || 120;
    const leftHalf = width / 2;
    let rightHalf = width / 2;
    if (person && person.spouse_id && characterData[person.spouse_id]) {
        const spouseWidth = computeCardWidthByName(characterData[person.spouse_id].name || person.spouse_id);
        const desiredGap = 28;
        rightHalf = width / 2 + desiredGap + spouseWidth; // conservative: include spouse full width to the right
    }
    return { leftHalf, rightHalf };
}

// Resolve horizontal collisions within each generation depth
function resolveCollisionsByDepth(nodes) {
    const nodesByDepth = d3.group(nodes, n => n.depth);
    const baseGap = 14; // more breathing room between unrelated nodes
    nodesByDepth.forEach(group => {
        group.sort((a, b) => a.x - b.x);
        let prev = null;
        let prevRightHalf = 0;
        group.forEach(n => {
            // ensure cardWidth exists for accurate spacing
            const name = (n.data && n.data.name) ? n.data.name : n.data.id;
            n.cardWidth = n.cardWidth || computeCardWidthByName(name);
            const ext = getNodeHalfExtents(n);
            if (prev) {
                const minX = prev.x + prevRightHalf + ext.leftHalf + baseGap;
                if (n.x < minX) {
                    const shift = minX - n.x;
                    n.x += shift;
                }
            }
            prev = n;
            prevRightHalf = getNodeHalfExtents(n).rightHalf;
        });
    });
}

// Derive a stable family key for a child based on its parents
function getFamilyKeyForChild(childData) {
    if (!childData) return null;
    const father = childData.father_id || '';
    const mother = childData.mother_id || '';
    if (!father && !mother) return null;
    return [father, mother].sort().join('|');
}

// Family-aware spacing: keep siblings tight, add extra space between different families,
// and center each sibling block under the midpoint of their parents
function resolveFamilyAwareLayout(nodes, nodeById) {
    const nodesByDepth = d3.group(nodes, n => n.depth);
    nodesByDepth.forEach(group => {
        // Map familyKey -> array of child nodes in this depth
        const familyToChildren = new Map();
        for (const n of group) {
            const familyKey = getFamilyKeyForChild(n.data);
            if (!familyKey) continue;
            if (!familyToChildren.has(familyKey)) familyToChildren.set(familyKey, []);
            familyToChildren.get(familyKey).push(n);
        }

        // Compute blocks (one per family)
        const blocks = [];
        familyToChildren.forEach((children, key) => {
            children.sort((a, b) => a.x - b.x);
            // Compute children bounds
            let minX = Infinity, maxX = -Infinity;
            for (const c of children) {
                const ext = getNodeHalfExtents(c);
                minX = Math.min(minX, c.x - ext.leftHalf);
                maxX = Math.max(maxX, c.x + ext.rightHalf);
            }
            // Parent midpoint
            const [p1, p2] = key.split('|');
            const parent1 = nodeById.get(p1 || '');
            const parent2 = nodeById.get(p2 || '');
            let parentMidX = null;
            if (parent1 && parent2) parentMidX = (parent1.x + parent2.x) / 2;
            else if (parent1) parentMidX = parent1.x;
            else if (parent2) parentMidX = parent2.x;
            const block = {
                key,
                children,
                minX,
                maxX,
                get center() { return (this.minX + this.maxX) / 2; },
                parentMidX
            };
            blocks.push(block);
        });

        if (blocks.length === 0) return;

        // Center each block under its parents
        for (const b of blocks) {
            if (b.parentMidX == null) continue;
            const shift = b.parentMidX - b.center;
            if (shift === 0) continue;
            b.minX += shift;
            b.maxX += shift;
            for (const c of b.children) c.x += shift;
        }

        // Prevent overlaps between blocks with a larger gap, while keeping siblings tight
        blocks.sort((a, b) => a.minX - b.minX);
        const blockGap = 80;  // much clearer spacing between families
        for (let i = 1; i < blocks.length; i++) {
            const prev = blocks[i - 1];
            const cur = blocks[i];
            if (cur.minX < prev.maxX + blockGap) {
                const push = prev.maxX + blockGap - cur.minX;
                cur.minX += push;
                cur.maxX += push;
                for (const c of cur.children) c.x += push;
            }
        }

        // Tighten siblings inside each block a bit (post-shift)
        const siblingGap = 16;
        for (const b of blocks) {
            let running = -Infinity;
            for (const c of b.children) {
                const ext = getNodeHalfExtents(c);
                const desiredMinX = Math.max(running, c.x - ext.leftHalf);
                const shift = desiredMinX - (c.x - ext.leftHalf);
                if (shift > 0) c.x += shift;
                running = c.x + ext.rightHalf + siblingGap;
            }
        }
    });
}

// Draw subtle background rectangles for each family to visually separate households
function drawFamilyUnderlays(descendantNodes, nodeById) {
    // Clear existing underlays and labels
    g.selectAll('.family-underlay').remove();
    g.selectAll('.family-label').remove();

    const nodesByDepth = d3.group(descendantNodes, n => n.depth);
    nodesByDepth.forEach(group => {
        const familyToChildren = new Map();
        for (const n of group) {
            const key = getFamilyKeyForChild(n.data);
            if (!key) continue;
            if (!familyToChildren.has(key)) familyToChildren.set(key, []);
            familyToChildren.get(key).push(n);
        }
        familyToChildren.forEach((children, key) => {
            // Compute bounds including parents if present
            const [p1, p2] = key.split('|');
            const parent1 = nodeById.get(p1 || '');
            const parent2 = nodeById.get(p2 || '');
            let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
            const includeNode = (n) => {
                if (!n) return;
                const ext = getNodeHalfExtents(n);
                xMin = Math.min(xMin, n.x - ext.leftHalf - 10);
                xMax = Math.max(xMax, n.x + ext.rightHalf + 10);
                yMin = Math.min(yMin, n.y - (n.cardHeight ? n.cardHeight / 2 : 18) - 14);
                yMax = Math.max(yMax, n.y + (n.cardHeight ? n.cardHeight / 2 : 18) + 14);
            };
            for (const c of children) includeNode(c);
            includeNode(parent1);
            includeNode(parent2);
            if (!isFinite(xMin) || !isFinite(xMax) || !isFinite(yMin) || !isFinite(yMax)) return;

            const colorHue = Math.abs(key.split('|').join('').split('').reduce((a, ch) => a + ch.charCodeAt(0), 0)) % 360;
            const fill = `hsla(${colorHue}, 55%, 85%, 0.18)`; // slightly stronger to be noticeable
            const stroke = `hsla(${colorHue}, 55%, 45%, 0.75)`;

            g.insert('rect', ':first-child')
                .attr('class', 'family-underlay')
                .attr('x', xMin)
                .attr('y', yMin)
                .attr('rx', 12)
                .attr('ry', 12)
                .attr('width', Math.max(0, xMax - xMin))
                .attr('height', Math.max(0, yMax - yMin))
                .attr('fill', fill)
                .attr('stroke', stroke)
                .attr('stroke-width', 2.25);

            // Add a simple family label on top (above shapes and links)
            const parentNames = [p1, p2]
                .filter(Boolean)
                .map(pid => (characterData[pid] && characterData[pid].name) ? characterData[pid].name : pid)
                .join(' & ');
            const label = parentNames || 'Family';
            g.append('text')
                .attr('class', 'family-label')
                .attr('x', (xMin + xMax) / 2)
                .attr('y', yMin - 8)
                .attr('text-anchor', 'middle')
                .attr('fill', stroke)
                .attr('font-size', 11)
                .attr('font-weight', '600')
                .text(label);
        });
    });
}

// Tree layout - use vertical layout for top-down view
const treeLayout = d3.tree().size([window.innerWidth - 500, window.innerHeight - 200]);
// Use dynamic separation to account for spouse width and reduce overlap across siblings
const constantSeparation = (a, b) => (a.parent === b.parent ? 1.3 : 1.6);
const dynamicSeparation = (a, b) => {
    const isSiblingRow = (a.parent === b.parent);
    const depth = Math.max(a.depth || 0, b.depth || 0);
    const base = isSiblingRow ? 1.2 : 1.6; // looser base spacing
    // Light attenuation so later generations remain readable
    const attenuation = Math.max(0.85, 1 - depth * 0.03);
    const extraFor = (n) => {
        if (!n || !n.data) return 0;
        const id = n.data.id;
        const spouseId = characterData[id] ? characterData[id].spouse_id : null;
        if (!spouseId) return 0;
        const offset = computeSpouseOffsetByIds(id, spouseId);
        // normalize by a typical node width to keep the value modest
        return Math.min(0.8, offset / 240);
    };
    const extra = (extraFor(a) + extraFor(b)) * 0.5; // average extra
    const sep = (base + 0.25 * extra) * attenuation;
    return Math.max(1.0, sep);
};

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
    
    // Apply tree layout with controlled spacing
    const containerWidth = window.innerWidth - 500;
    const containerHeight = window.innerHeight - 200;
    treeLayout
        .size([containerWidth, containerHeight])
        .separation(dynamicSeparation)
        .nodeSize([240, 110])(root); // looser horizontal and vertical spacing
    
    // Resolve in-generation collisions and apply family-aware layout
    const allNodes = root.descendants();
    const nodeById = new Map(allNodes.map(n => [n.data.id, n]));
    resolveCollisionsByDepth(allNodes);
    resolveFamilyAwareLayout(allNodes, nodeById);
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
    
    // Prepare node lookup to compute spouse midpoints for children
    const descendantNodes = root.descendants();
    const nodeById = new Map(descendantNodes.map(n => [n.data.id, n]));

    // Compute branch keys and a deterministic color for each branch (first generation under root)
    const branchKeyById = new Map();
    const branchKeys = new Set();
    descendantNodes.forEach(n => {
        let key = n.data && n.data.id;
        if (n.depth >= 1) {
            const ancestors = n.ancestors();
            // ancestors(): [node, parent, ..., root]; pick depth-1 ancestor when possible
            const maybeTopChild = ancestors[ancestors.length - 2];
            key = (maybeTopChild && maybeTopChild.data) ? maybeTopChild.data.id : key;
        }
        branchKeyById.set(n.data.id, key);
        branchKeys.add(key);
    });

    const branchColorCache = new Map();
    function colorFromKey(key) {
        if (branchColorCache.has(key)) return branchColorCache.get(key);
        const hash = String(key || '')
            .split('')
            .reduce((acc, ch) => (acc * 131 + ch.charCodeAt(0)) >>> 0, 0);
        const hue = hash % 360;
        const color = `hsl(${hue}, 70%, 40%)`;
        branchColorCache.set(key, color);
        return color;
    }

    // Create links - use vertical layout, but if a child has two parents,
    // route the link from the midpoint between the parents; anchor to card edges (bottom/top)
    const links = g.selectAll(".link")
        .data(root.links())
        .enter().append("path")
        .attr("class", "link")
        .attr("stroke", function(d){
            const childId = d.target && d.target.data ? d.target.data.id : null;
            const key = branchKeyById.get(childId);
            return colorFromKey(key);
        })
        .attr("d", function(d) {
            const childId = d.target && d.target.data ? d.target.data.id : null;
            const childData = childId ? characterData[childId] : null;

            // Default link generator (unused in elbow path but kept for reference)
            const gen = d3.linkVertical().x(p => p.x).y(p => p.y);

            if (childData && childData.father_id && childData.mother_id) {
                const thisParentId = d.source.data.id;
                const otherParentId = thisParentId === childData.father_id ? childData.mother_id : childData.father_id;

                // Only draw a single link for the pair: from the midpoint to the child.
                // Choose the parent with the lexicographically smaller id as the drawer.
                const firstParentId = [childData.father_id, childData.mother_id].sort()[0];
                if (thisParentId !== firstParentId) {
                    return ""; // suppress duplicate link from the second parent
                }

                // Try to find the other parent as a main node
                const otherParentNode = nodeById.get(otherParentId);
                let otherX, otherY;
                if (otherParentNode) {
                    otherX = otherParentNode.x;
                    otherY = otherParentNode.y;
                } else if (characterData[otherParentId]) {
                    // If not in the main tree, estimate spouse position using dynamic card widths
                    const offset = computeSpouseOffsetByIds(thisParentId, otherParentId);
                    otherX = d.source.x + offset;
                    otherY = d.source.y;
                }

                if (otherX !== undefined && otherY !== undefined) {
                    // Connect from the spouse bar (horizontal line between parents at card center) to top of child card
                    const coupleY = d.source.y; // spouse link is drawn at card center Y
                    const childTopY = d.target.y - (d.target.cardHeight ? d.target.cardHeight / 2 : 18);
                    const midX = (d.source.x + otherX) / 2;
                    return createElbowPath(midX, coupleY, d.target.x, childTopY);
                }
            }

            // Fallback: single-parent case → connect from bottom edge of parent card to top of child card
            const sourceBottomY = d.source.y + (d.source.cardHeight ? d.source.cardHeight / 2 : 18);
            const childTopY = d.target.y - (d.target.cardHeight ? d.target.cardHeight / 2 : 18);
            return createElbowPath(d.source.x, sourceBottomY, d.target.x, childTopY);
        });
    
    // Create nodes
    const nodes = g.selectAll(".node")
        .data(descendantNodes)
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`);

    // Add node cards (rounded rectangles) with embedded labels
    nodes.each(function(d) {
        const name = (d.data && d.data.name) ? d.data.name : d.data.id;
        const height = 30;
        const width = computeCardWidthByName(name);
        d.cardWidth = width;
        d.cardHeight = height;
        const color = getGenerationColor(d.depth);

        const group = d3.select(this);

        group.append("rect")
            .attr("x", -width / 2)
            .attr("y", -height / 2)
            .attr("rx", 10)
            .attr("ry", 10)
            .attr("width", width)
            .attr("height", height)
            .attr("fill", color)
            .attr("fill-opacity", 0.12)
            .attr("stroke", color)
            .attr("stroke-width", 2);

        group.append("text")
            .attr("class", "node-label")
            .attr("dy", "0.35em")
            .attr("y", 0)
            .text(name)
            .style("font-size", "12px")
            .style("font-weight", "bold")
            .style("fill", "#2c3e50")
            .style("text-anchor", "middle")
            .style("pointer-events", "none");
    });
    
    // Add spouse nodes separately
    addSpouseNodes();
    
    // Add spouse connections
    addSpouseConnectionsWithBranchColors(branchKeyById, colorFromKey);

    // Draw family underlays after nodes/links so bounds are accurate, but insert behind
    drawFamilyUnderlays(descendantNodes, nodeById);
    
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
            
            // Add spouse card (rounded rectangle) with embedded label
            const spouseName = spouseData.name || spouseId;
            const height = 30;
            const width = computeCardWidthByName(spouseName);
            const color = getGenerationColor(d.depth);

            // Recompute x to account for both card widths and gap
            const offset = computeSpouseOffsetByIds(personId, spouseId);
            const adjustedSpouseX = d.x + offset;
            spouseGroup.attr("transform", `translate(${adjustedSpouseX},${spouseY})`);

            // Bind a datum so generic handlers can read node data from spouse nodes
            spouseGroup.datum({ data: { id: spouseId, name: spouseName }, x: adjustedSpouseX, y: spouseY });

            spouseGroup.append("rect")
                .attr("x", -width / 2)
                .attr("y", -height / 2)
                .attr("rx", 10)
                .attr("ry", 10)
                .attr("width", width)
                .attr("height", height)
                .attr("fill", color)
                .attr("fill-opacity", 0.12)
                .attr("stroke", color)
                .attr("stroke-width", 2);

            spouseGroup.append("text")
                .attr("class", "node-label")
                .attr("dy", "0.35em")
                .attr("y", 0)
                .text(spouseName)
                .style("font-size", "12px")
                .style("font-weight", "bold")
                .style("fill", "#2c3e50")
                .style("text-anchor", "middle")
                .style("pointer-events", "none");
            
            // Add click events for spouse nodes
            spouseGroup.on("click", function(event) {
                handleNodeClick(event, { data: { id: spouseId, name: spouseName }, x: adjustedSpouseX, y: spouseY });
            });
            
            // Add hover events for spouse nodes
            spouseGroup.on("mouseenter", function(event) {
                handleNodeHover(event, { data: { id: spouseId }, x: adjustedSpouseX, y: spouseY });
            });
            spouseGroup.on("mouseleave", function(event) {
                handleNodeLeave(event, { data: { id: spouseId }, x: adjustedSpouseX, y: spouseY });
            });
            
            existingNodes.add(spouseId);
        }
    });
}

function addSpouseConnectionsWithBranchColors(branchKeyById, colorFromKey) {
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
        .attr("stroke", d => {
            const key = branchKeyById.get(d.source) || branchKeyById.get(d.target);
            return colorFromKey(key);
        })
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
                    const match = sourceTransform.match(/translate\(([^,]+),([^)]+)\)/);
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
                    const match = targetTransform.match(/translate\(([^,]+),([^)]+)\)/);
                    if (match) {
                        targetX = parseFloat(match[1]);
                        targetY = parseFloat(match[2]);
                    }
                }

                // Read rect widths to connect at card edges rather than centers
                const sourceRectWidth = parseFloat(sourceNode.select('rect').attr('width') || '0');
                const sourceRectStroke = parseFloat(sourceNode.select('rect').attr('stroke-width') || '0');
                const targetRectWidth = parseFloat(targetNode.select('rect').attr('width') || '0');
                const targetRectStroke = parseFloat(targetNode.select('rect').attr('stroke-width') || '0');
                const sourceHalf = sourceRectWidth > 0 ? sourceRectWidth / 2 : 0;
                const targetHalf = targetRectWidth > 0 ? targetRectWidth / 2 : 0;
                // Pull the spouse line a bit inside so it meets the darker border cleanly
                const edgePadding = Math.max(1, Math.round(((sourceRectStroke + targetRectStroke) / 2) || 2));

                if (sourceX !== undefined && sourceY !== undefined &&
                    targetX !== undefined && targetY !== undefined) {
                    // Determine left/right
                    let startX, startY, endX, endY;
                    if (sourceX <= targetX) {
                        startX = sourceX + sourceHalf - edgePadding;
                        endX = targetX - targetHalf + edgePadding;
                    } else {
                        startX = sourceX - sourceHalf + edgePadding;
                        endX = targetX + targetHalf - edgePadding;
                    }
                    startY = sourceY;
                    endY = targetY;

                    return `M ${startX},${startY} L ${endX},${endY}`;
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
        selectedNode.select("rect").classed("selected", false);
    }
    
    // Select new node
    selectedNode = nodeElement;
    selectedNode.select("rect").classed("selected", true);
    
    // Resolve person identity robustly for spouse nodes or unexpected data
    const resolvedPersonId = (nodeData && nodeData.data && nodeData.data.id)
        || nodeElement.attr("data-person-id");
    if (!resolvedPersonId) {
        console.error("Could not resolve person id for clicked node", nodeData);
        return;
    }

    const resolvedName = (nodeData && nodeData.data && nodeData.data.name)
        || (characterData[resolvedPersonId] && characterData[resolvedPersonId].name)
        || resolvedPersonId;

    // Show person details
    showPersonDetails(resolvedPersonId);
    updateStatus(`Selected: ${resolvedName}`);
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
    if (!svgElement || !treeContainer || !g) return;

    // Use the content bounding box rather than the viewport size
    let bbox;
    try {
        bbox = g.node().getBBox();
    } catch (e) {
        // Fallback to viewport bounds
        bbox = { x: 0, y: 0, width: svgElement.clientWidth, height: svgElement.clientHeight };
    }

    const containerRect = treeContainer.getBoundingClientRect();

    // Padding around content when fitting
    const padding = 40; // allow more space around edges when fitting
    const widthWithPad = bbox.width + padding * 2;
    const heightWithPad = bbox.height + padding * 2;

    const scaleX = containerRect.width / widthWithPad;
    const scaleY = containerRect.height / heightWithPad;
    currentZoom = Math.min(scaleX, scaleY, 1);

    // Translate so the content center is centered in the container
    const contentCenterX = bbox.x + bbox.width / 2;
    const contentCenterY = bbox.y + bbox.height / 2;

    const translateX = containerRect.width / 2 - contentCenterX * currentZoom;
    const translateY = containerRect.height / 2 - contentCenterY * currentZoom;

    const transform = d3.zoomIdentity.translate(translateX, translateY).scale(currentZoom);
    d3.select(svgElement).transition().duration(500).call(zoom.transform, transform);
    updateStatus(`Fitted to window - Zoom: ${Math.round(currentZoom * 100)}%`);
}

// Prepare a print-friendly fit for US Letter (landscape) and trigger print
function printLetter() {
    const body = document.body;
    if (!body) return;

    body.classList.add('print-mode');
    // Give layout one frame to apply before fitting
    setTimeout(() => {
        fitToLetterPage();
        // Slight delay to ensure transform is applied before printing
        setTimeout(() => {
            window.print();
            // Clean up after print (in case afterprint isn't fired)
            setTimeout(() => body.classList.remove('print-mode'), 300);
        }, 150);
    }, 50);
}

// Clean up print mode if supported
window.addEventListener('afterprint', () => {
    document.body.classList.remove('print-mode');
});

// Fit the SVG content to a US Letter landscape page (single page)
function fitToLetterPage() {
    const svgElement = document.querySelector('svg');
    if (!svgElement || !g) return;

    // Compute content bounds
    let bbox;
    try {
        bbox = g.node().getBBox();
    } catch (e) {
        return; // If unavailable, skip
    }

    // Page size: Letter landscape with 0.5in margins on each side
    const CSS_DPI = 96; // 1in = 96px in CSS
    const pageWidthInches = 11;
    const pageHeightInches = 8.5;
    const marginInches = 0.5;
    const targetWidthPx = (pageWidthInches - marginInches * 2) * CSS_DPI;  // 10in -> 960px
    const targetHeightPx = (pageHeightInches - marginInches * 2) * CSS_DPI; // 7.5in -> 720px

    const padding = 24; // small padding inside printable area
    const widthWithPad = bbox.width + padding * 2;
    const heightWithPad = bbox.height + padding * 2;

    const scaleX = targetWidthPx / widthWithPad;
    const scaleY = targetHeightPx / heightWithPad;
    // Only downscale for print to guarantee single page
    currentZoom = Math.min(scaleX, scaleY, 1);

    // Center content within the printable area
    const contentCenterX = bbox.x + bbox.width / 2;
    const contentCenterY = bbox.y + bbox.height / 2;
    const translateX = targetWidthPx / 2 - contentCenterX * currentZoom;
    const translateY = targetHeightPx / 2 - contentCenterY * currentZoom;

    const transform = d3.zoomIdentity.translate(translateX, translateY).scale(currentZoom);
    d3.select(svgElement).call(zoom.transform, transform);
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
    treeLayout
        .size([containerWidth, containerHeight])
        .separation(dynamicSeparation)
        .nodeSize([240, 110])(root);
    const allNodes = root.descendants();
    const nodeById = new Map(allNodes.map(n => [n.data.id, n]));
    resolveCollisionsByDepth(allNodes);
    resolveFamilyAwareLayout(allNodes, nodeById);
    drawTree(root);
    
    // Refit to window
    setTimeout(() => fitToWindow(), 100);
}); 