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

// Simple straight line path (no longer used but kept for potential future use)
function createElbowPath(sourceX, sourceY, targetX, targetY) {
    return `M ${sourceX},${sourceY} L ${targetX},${targetY}`;
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

// Simplified spouse offset - no longer used in simplified version
function computeSpouseOffsetByIds(personId, spouseId) {
    // Simplified version - returns basic spacing
    return 60; // fixed spacing for simplicity
}

// Simplified node extents - just basic width calculation
function getNodeHalfExtents(node) {
    const width = node.cardWidth || 120;
    return { leftHalf: width / 2, rightHalf: width / 2 };
}

// Enhanced collision resolution with better spouse detection and spacing
function resolveCollisionsByDepth(nodes) {
    const nodesByDepth = d3.group(nodes, n => n.depth);
    const baseGap = 35; // increased minimum gap for better readability
    
    nodesByDepth.forEach(group => {
        group.sort((a, b) => a.x - b.x);
        let prev = null;
        
        group.forEach(n => {
            // Calculate actual node width including spouse if present
            const name = (n.data && n.data.name) ? n.data.name : n.data.id;
            const nodeWidth = computeCardWidthByName(name);
            let totalWidth = nodeWidth;
            
            // Check if this is actually a married couple (not just two separate people)
            let hasValidSpouse = false;
            if (n.data.spouse && characterData[n.data.spouse.id]) {
                const spouseData = characterData[n.data.spouse.id];
                if (spouseData && spouseData.spouse_id === n.data.id) {
                    hasValidSpouse = true;
                    const spouseName = spouseData.name; // Use the spouse's actual name
                    const spouseWidth = computeCardWidthByName(spouseName);
                    totalWidth = nodeWidth + 35 + spouseWidth; // 35 = gap between person and spouse
                }
            }
            
            if (prev) {
                // Calculate previous node's total width
                const prevName = (prev.data && prev.data.name) ? prev.data.name : prev.data.id;
                const prevNodeWidth = computeCardWidthByName(prevName);
                let prevTotalWidth = prevNodeWidth;
                
                // Check if previous node has valid spouse
                let prevHasValidSpouse = false;
                if (prev.data.spouse && characterData[prev.data.spouse.id]) {
                    const prevSpouseData = characterData[prev.data.spouse.id];
                    if (prevSpouseData && prevSpouseData.spouse_id === prev.data.id) {
                        prevHasValidSpouse = true;
                        const prevSpouseName = prevSpouseData.name; // Use the spouse's actual name
                        const prevSpouseWidth = computeCardWidthByName(prevSpouseName);
                        prevTotalWidth = prevNodeWidth + 35 + prevSpouseWidth;
                    }
                }
                
                // Ensure consistent spacing between nodes regardless of marital status
                const minX = prev.x + (prevTotalWidth / 2) + (totalWidth / 2) + baseGap;
                if (n.x < minX) {
                    n.x = minX;
                }
            }
            prev = n;
        });
    });
}

// Simplified family key function - no longer used in simplified version
function getFamilyKeyForChild(childData) {
    // Simplified version - returns basic parent info
    if (!childData) return null;
    const father = childData.father_id || '';
    const mother = childData.mother_id || '';
    if (!father && !mother) return null;
    return `${father}|${mother}`;
}

// Family-aware spacing: keep siblings tight, add extra space between different families,
// and center each sibling block under the midpoint of their parents
function resolveFamilyAwareLayout(nodes, nodeById) {
    const nodesByDepth = d3.group(nodes, n => n.depth);
    
    nodesByDepth.forEach(group => {
        // Group nodes by family (same parents)
        const familyGroups = new Map();
        
        group.forEach(n => {
            const parentId = n.parent ? n.parent.data.id : null;
            if (parentId && parentId !== 'virtual_root') {
                if (!familyGroups.has(parentId)) {
                    familyGroups.set(parentId, []);
                }
                familyGroups.get(parentId).push(n);
            }
        });
        
        // Sort family groups by their center X position
        const sortedFamilies = Array.from(familyGroups.entries())
            .map(([parentId, children]) => {
                const centerX = children.reduce((sum, child) => sum + child.x, 0) / children.length;
                return { parentId, children, centerX };
            })
            .sort((a, b) => a.centerX - b.centerX);
        
        // Ensure consistent spacing between different families
        const familyGap = 50; // increased gap between different families for better separation
        let lastFamilyEnd = -Infinity;
        
        sortedFamilies.forEach(family => {
            // Calculate family bounds
            let familyMinX = Infinity, familyMaxX = -Infinity;
            family.children.forEach(child => {
                const name = (child.data && child.data.name) ? child.data.name : child.data.id;
                const nodeWidth = computeCardWidthByName(name);
                let totalWidth = nodeWidth;
                
                // Check if this is actually a married couple (not just two separate people)
                if (child.data.spouse && characterData[child.data.spouse.id]) {
                    const spouseData = characterData[child.data.spouse.id];
                    if (spouseData && spouseData.spouse_id === child.data.id) {
                        const spouseName = spouseData.name; // Use the spouse's actual name
                        const spouseWidth = computeCardWidthByName(spouseName);
                        totalWidth = nodeWidth + 35 + spouseWidth;
                    }
                }
                
                familyMinX = Math.min(familyMinX, child.x - totalWidth / 2);
                familyMaxX = Math.max(familyMaxX, child.x + totalWidth / 2);
            });
            
            // Ensure consistent gap from previous family
            if (lastFamilyEnd !== -Infinity) {
                const requiredX = lastFamilyEnd + familyGap;
                if (familyMinX < requiredX) {
                    const shift = requiredX - familyMinX;
                    family.children.forEach(child => {
                        child.x += shift;
                    });
                    familyMinX += shift;
                    familyMaxX += shift;
                }
            }
            
            lastFamilyEnd = familyMaxX;
        });
    });
}

// Simplified family underlays - removed complex visual grouping
function drawFamilyUnderlays(descendantNodes, nodeById) {
    // Simplified version - no visual grouping for now
    console.log('Using simplified family underlays');
}

// Dynamic spacing adjustment for optimal readability
function applyDynamicSpacing(nodes) {
    const nodesByDepth = d3.group(nodes, n => n.depth);
    
    nodesByDepth.forEach(group => {
        if (group.length < 2) return; // Skip if only one node in generation
        
        // Calculate average name length in this generation
        const nameLengths = group.map(n => {
            const name = (n.data && n.data.name) ? n.data.name : n.data.id;
            return name.length;
        });
        const avgNameLength = nameLengths.reduce((sum, len) => sum + len, 0) / nameLengths.length;
        
        // Adjust spacing based on name length complexity
        let dynamicGap = 30; // base gap
        if (avgNameLength > 20) {
            dynamicGap = 40; // more space for longer names
        } else if (avgNameLength > 15) {
            dynamicGap = 35; // moderate space for medium names
        }
        
        // Apply dynamic spacing
        group.sort((a, b) => a.x - b.x);
        let prev = null;
        
        group.forEach(n => {
            if (prev) {
                // Calculate actual node width including spouse if present
                const name = (n.data && n.data.name) ? n.data.name : n.data.id;
                const nodeWidth = computeCardWidthByName(name);
                let totalWidth = nodeWidth;
                
                // Check if this is actually a married couple (not just two separate people)
                if (n.data.spouse && characterData[n.data.spouse.id]) {
                    const spouseData = characterData[n.data.spouse.id];
                    if (spouseData && spouseData.spouse_id === n.data.id) {
                        const spouseName = spouseData.name; // Use the spouse's actual name
                        const spouseWidth = computeCardWidthByName(spouseName);
                        totalWidth = nodeWidth + 35 + spouseWidth;
                    }
                }
                
                // Calculate previous node's total width
                const prevName = (prev.data && prev.data.name) ? prev.data.name : prev.data.id;
                const prevNodeWidth = computeCardWidthByName(prevName);
                let prevTotalWidth = prevNodeWidth;
                
                // Check if previous node has valid spouse
                if (prev.data.spouse && characterData[prev.data.spouse.id]) {
                    const prevSpouseData = characterData[prev.data.spouse.id];
                    if (prevSpouseData && prevSpouseData.spouse_id === prev.data.id) {
                        const prevSpouseName = prevSpouseData.name; // Use the spouse's actual name
                        const prevSpouseWidth = computeCardWidthByName(prevSpouseName);
                        prevTotalWidth = prevNodeWidth + 35 + prevSpouseWidth;
                    }
                }
                
                // Apply dynamic spacing
                const minX = prev.x + (prevTotalWidth / 2) + (totalWidth / 2) + dynamicGap;
                if (n.x < minX) {
                    n.x = minX;
                }
            }
            prev = n;
        });
    });
}

// Enhanced spouse validation to prevent false spouse relationships
function validateSpouseRelationships(nodes) {
    console.group('Validating Spouse Relationships');
    let validSpouses = 0;
    let invalidSpouses = 0;
    
    nodes.forEach(node => {
        // Skip spouse nodes in validation
        if (node.isSpouse) {
            return;
        }
        
        if (node.data.spouse && characterData[node.data.spouse.id]) {
            // Check if spouse relationship is valid
            const spouseData = characterData[node.data.spouse.id];
            if (spouseData && spouseData.spouse_id === node.data.id) {
                validSpouses++;
                console.log(`✓ Valid spouse: ${node.data.name} ↔ ${spouseData.name}`);
            } else {
                invalidSpouses++;
                console.log(`✗ Invalid spouse: ${node.data.name} -> ${spouseData?.name || 'unknown'}, expected: ${node.data.id}`);
                // Remove invalid spouse relationship
                delete node.data.spouse;
            }
        }
    });
    
    console.log(`Spouse validation complete: ${validSpouses} valid, ${invalidSpouses} invalid relationships removed`);
    console.groupEnd();
}

// Tree layout - use vertical layout for top-down view with proper spacing
const treeLayout = d3.tree()
    .size([window.innerWidth - 200, window.innerHeight - 100])
    .separation(dynamicSeparation);

// Enhanced generational spacing for better readability
function ensureGenerationalSpacing(nodes) {
    const nodesByDepth = d3.group(nodes, n => n.depth);
    const baseSpacing = 100; // base spacing between generations
    
    nodesByDepth.forEach((group, depth) => {
        if (depth === 0) return; // Skip root level
        
        // Increase spacing for deeper generations to prevent overlap
        const adjustedSpacing = baseSpacing + (depth * 15);
        group.forEach(n => {
            n.y += adjustedSpacing;
        });
    });
}

// Enhanced separation for better node spacing
function dynamicSeparation(a, b) {
    // Base separation
    let separation = 1.4;
    
    // Add extra space for siblings (same parent)
    if (a.parent === b.parent) {
        separation += 0.3;
    }
    
    // Add extra space if either node has a spouse
    const aHasSpouse = a.data.spouse && a.data.spouse.id;
    const bHasSpouse = b.data.spouse && b.data.spouse.id;
    if (aHasSpouse || bHasSpouse) {
        separation += 0.4;
    }
    
    // Add extra space for deeper generations
    const depthFactor = Math.max(a.depth, b.depth) * 0.15;
    separation += depthFactor;
    
    // Add extra space based on name complexity
    const aName = a.data.name || a.data.id || '';
    const bName = b.data.name || b.data.id || '';
    const nameComplexity = Math.max(aName.length, bName.length);
    if (nameComplexity > 25) {
        separation += 0.3;
    } else if (nameComplexity > 20) {
        separation += 0.2;
    }
    
    return Math.min(separation, 2.5); // Increased cap for better spacing
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
    const containerWidth = window.innerWidth - 300; // use more width for better spacing
    const containerHeight = window.innerHeight - 150; // increased height for better spacing
    treeLayout
        .size([containerWidth, containerHeight])
        .separation(dynamicSeparation)
        (root);
    
    const allNodes = root.descendants();
    const nodeById = new Map(allNodes.map(n => [n.data.id, n]));
    
    // Apply enhanced layout adjustments in optimal order
    ensureGenerationalSpacing(allNodes);
    resolveFamilyAwareLayout(allNodes, nodeById); // Family grouping first
    resolveCollisionsByDepth(allNodes); // Then collision resolution
    
    // Draw the tree
    drawTree(root);
    
    // Fit to window initially
    setTimeout(() => fitToWindow(), 100);
}

function buildTreeData() {
    console.group('Building Family Tree');
    console.log('Total people in data:', Object.keys(characterData).length);
    
    const processed = new Set();
    const rootAncestorIds = [];
    
    // Find root ancestors (people with no parents in the data)
    // BUT avoid creating duplicate trees for married couples
    const potentialRoots = [];
    
    // First pass: find all people without parents
    for (const [id, person] of Object.entries(characterData)) {
        const hasFather = person.father_id && characterData[person.father_id];
        const hasMother = person.mother_id && characterData[person.mother_id];
        
        if (!hasFather && !hasMother) {
            potentialRoots.push(id);
        }
    }
    
    console.log(`Found ${potentialRoots.length} potential roots:`, potentialRoots.map(id => characterData[id]?.name || id));
    
    // Second pass: avoid duplicate trees for married couples
    const processedSpouses = new Set();
    for (const id of potentialRoots) {
        if (processedSpouses.has(id)) {
            console.log(`📝 Skipping ${characterData[id]?.name} - already included as spouse of another root`);
            continue;
        }
        
        rootAncestorIds.push(id);
        
        // Mark their spouse as processed to avoid duplicate trees
        const person = characterData[id];
        if (person.spouse_id && characterData[person.spouse_id]) {
            const spouse = characterData[person.spouse_id];
            // Only mark spouse as processed if they would also be a root ancestor
            if (potentialRoots.includes(person.spouse_id)) {
                processedSpouses.add(person.spouse_id);
                console.log(`📝 Marked ${spouse.name} as processed (spouse of ${person.name})`);
            }
        }
    }
    
    console.log(`Found ${rootAncestorIds.length} root ancestors:`, rootAncestorIds.map(id => characterData[id]?.name || id));
    
    // Debug: Log detailed info about each root ancestor
    console.group('🔍 Detailed Root Ancestor Analysis:');
    rootAncestorIds.forEach(id => {
        const person = characterData[id];
        console.log(`ID: ${id}, Name: ${person?.name}, Father: ${person?.father_id}, Mother: ${person?.mother_id}`);
    });
    console.groupEnd();
    
    // Build trees starting from root ancestors
    const rootTrees = [];
    for (const rootId of rootAncestorIds) {
        if (processed.has(rootId)) continue;
        
        console.log(`Creating root tree for: ${characterData[rootId]?.name} (ID: ${rootId})`);
        const tree = buildFamilyTree(rootId);
        if (tree) {
            rootTrees.push(tree);
            console.log(`✅ Successfully added tree for: ${tree.name}`);
        } else {
            console.log(`❌ Failed to create tree for: ${characterData[rootId]?.name}`);
        }
    }
    
    console.log(`\n📊 Final Summary:`);
    console.log(`- Root ancestor IDs found: ${rootAncestorIds.length}`);
    console.log(`- Root trees created: ${rootTrees.length}`);
    console.log(`- Root tree names: [${rootTrees.map(t => t.name).join(', ')}]`);
    
    // Create virtual root to hold all trees
    const virtualRoot = {
        id: "virtual_root",
        name: "Family Tree",
        data: { id: "virtual_root", name: "Family Tree" },
        children: rootTrees
    };
    
    console.log(`\nCreated ${rootTrees.length} root trees:`, rootTrees.map(n => n.name).join(', '));
    console.groupEnd();
    
    // Helper function to build family tree  
    function buildFamilyTree(personId, depth = 0) {
        if (processed.has(personId)) {
            console.log(`⚠ Already processed: ${personId}`);
            return null;
        }
        processed.add(personId);
        
        const person = characterData[personId];
        if (!person) {
            console.log(`⚠ Person not found: ${personId}`);
            return null;
        }
        
        console.log(`🔍 Building tree for: ${person.name} (ID: ${personId}, depth: ${depth})`);
        
        // Create node for this person
        const node = {
            id: personId,
            name: person.name || personId,
            data: person,
            children: []
        };
        
        // Add spouse if exists
        if (person.spouse_id && characterData[person.spouse_id]) {
            const spouseData = characterData[person.spouse_id];
            if (spouseData.spouse_id === personId) {
                node.spouse = {
                    id: person.spouse_id,
                    name: spouseData.name || person.spouse_id,
                    data: spouseData
                };
                console.log(`✓ Found spouse: ${person.name} ↔ ${spouseData.name}`);
            }
        }
        
        // Find all children where this person is father or mother
        console.log(`🔍 Looking for children of: ${person.name}`);
        for (const [childId, childData] of Object.entries(characterData)) {
            const isDirectChild = childData.father_id === personId || childData.mother_id === personId;
            const isSpouseChild = node.spouse && (childData.father_id === node.spouse.id || childData.mother_id === node.spouse.id);
            
            if (isDirectChild || isSpouseChild) {
                console.log(`👶 Found child: ${childData.name} (ID: ${childId}) - Direct: ${isDirectChild}, Spouse: ${isSpouseChild}`);
                const childNode = buildFamilyTree(childId, depth + 1);
                if (childNode) {
                    node.children.push(childNode);
                    console.log(`✅ Added child: ${childData.name} to ${person.name}`);
                }
            }
        }
        
        console.log(`📊 ${person.name} has ${node.children.length} children`);
        
        // Sort children by birth year (simplified)
        if (node.children.length > 0) {
            node.children.sort((a, b) => {
                const birthA = a.data.birthday || "1900";
                const birthB = b.data.birthday || "1900";
                const yearA = parseInt(birthA.match(/\d{4}/) || "1900");
                const yearB = parseInt(birthB.match(/\d{4}/) || "1900");
                return yearA - yearB;
            });
        }
        
        console.log(`🏁 Finished building tree for: ${person.name}`);
        return node;
    }
    
    return virtualRoot;
}

function drawTree(root) {
    console.group('Drawing Tree');
    console.log('Total nodes:', root.descendants().length);
    
    // Clear existing content
    g.selectAll("*").remove();
    
    // Prepare node lookup
    const descendantNodes = root.descendants();
    const nodeById = new Map(descendantNodes.map(n => [n.data.id, n]));
    
    // Log node positions
    console.log('\nNode Positions:');
    descendantNodes.forEach(node => {
        if (node.data.id === 'virtual_root') return;
        
        console.group(`Node: ${node.data.name}`);
        console.log(`  Position: (${Math.round(node.x)}, ${Math.round(node.y)})`);
        console.log(`  Depth: ${node.depth}`);
        console.log(`  Parent: ${node.parent?.data?.name || 'none'}`);
        if (node.children?.length > 0) {
            console.log(`  Children: ${node.children.map(c => c.data.name).join(', ')}`);
        }
        console.groupEnd();
    });
    
    // Create simple parent-child links
    const links = g.selectAll(".link")
        .data(root.links().filter(d => d.source.data.id !== "virtual_root" && d.target.data.id !== "virtual_root"))
        .enter().append("path")
        .attr("class", "link")
        .attr("stroke", "#666")
        .attr("stroke-width", 2)
        .attr("d", function(d) {
            // Simple straight line from parent to child
            const sourceBottomY = d.source.y + (d.source.cardHeight ? d.source.cardHeight / 2 : 18);
            const childTopY = d.target.y - (d.target.cardHeight ? d.target.cardHeight / 2 : 18);
            return `M ${d.source.x},${sourceBottomY} L ${d.target.x},${childTopY}`;
        });
    
    // Create nodes (skip virtual root node)
    const filteredNodes = descendantNodes.filter(d => d.data.id !== "virtual_root");
    
    // Create a list of all nodes including spouses
    const allNodes = [];
    const spouseNodes = new Map(); // Track spouse nodes to avoid duplicates
    
    filteredNodes.forEach(d => {
        // Add main person node
        allNodes.push({
            ...d,
            isSpouse: false,
            originalNode: d
        });
        
        // Add spouse node if this person has a spouse and it hasn't been added yet
        if (d.data.spouse && characterData[d.data.spouse.id] && !spouseNodes.has(d.data.spouse.id)) {
            const spouseData = characterData[d.data.spouse.id];
            const spouseNode = {
                id: d.data.spouse.id,
                name: spouseData.name || d.data.spouse.id,
                data: spouseData,
                x: d.x + 120, // Position spouse to the right
                y: d.y,        // Same vertical position
                depth: d.depth,
                parent: d.parent,
                children: d.children,
                isSpouse: true,
                originalNode: d,
                spouse_id: d.data.id // Reference back to original person
            };
            allNodes.push(spouseNode);
            spouseNodes.set(d.data.spouse.id, spouseNode);
        }
    });
    
    const nodes = g.selectAll(".node")
        .data(allNodes)
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`);
    
    // Add node cards
    nodes.each(function(d) {
        const name = d.name;
        const height = 30;
        const width = computeCardWidthByName(name);
        d.cardWidth = width;
        d.cardHeight = height;
        const color = getGenerationColor(d.depth);
        
        const group = d3.select(this);
        
        // Add person card
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
            .attr("stroke-width", 2)
            .attr("data-person-id", d.id);
        
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
    
    // Add spouse connection lines
    filteredNodes.forEach(d => {
        if (d.data.spouse && characterData[d.data.spouse.id] && spouseNodes.has(d.data.spouse.id)) {
            const spouseNode = spouseNodes.get(d.data.spouse.id);
            const gap = 120; // Gap between main person and spouse
            
            // Calculate card widths for positioning
            const mainPersonWidth = computeCardWidthByName(d.data.name || d.data.id);
            const spouseWidth = computeCardWidthByName(spouseNode.name);
            
            g.append("line")
                .attr("class", "spouse-connection")
                .attr("x1", d.x + mainPersonWidth / 2)
                .attr("y1", d.y)
                .attr("x2", d.x + gap - spouseWidth / 2)
                .attr("y2", d.y)
                .attr("stroke", "#e74c3c")
                .attr("stroke-width", 2)
                .attr("stroke-dasharray", "5,5");
        }
    });
    
    // Add click events
    nodes.on("click", handleNodeClick);
    
    // Add hover events
    nodes.on("mouseenter", handleNodeHover);
    nodes.on("mouseleave", handleNodeLeave);
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
    
    // Get the person ID from the node data
    let personId;
    if (nodeData.isSpouse) {
        // This is a spouse node, use the spouse's ID
        personId = nodeData.id;
    } else {
        // This is a main person node
        personId = nodeData.data.id;
    }
    
    if (!personId) {
        console.error("Could not resolve person id for clicked node", nodeData);
        return;
    }

    // Get the person's name
    let personName;
    if (nodeData.isSpouse) {
        personName = nodeData.name;
    } else {
        personName = nodeData.data.name || nodeData.data.id;
    }

    // Show person details
    showPersonDetails(personId);
    updateStatus(`Selected: ${personName}`);
}

function handleNodeHover(event, d) {
    let personId, personName;
    
    if (d.isSpouse) {
        // This is a spouse node
        personId = d.id;
        personName = d.name;
    } else {
        // This is a main person node
        personId = d.data.id;
        personName = d.data.name || d.data.id;
    }
    
    if (personId) {
        updateStatus(`${personName} - Click for details`);
    }
}

function handleNodeLeave(event, d) {
    updateStatus('Click on a person to see details | Drag to pan | Scroll to zoom');
}

function showPersonDetails(personId) {
    const personData = characterData[personId];
    const detailsContainer = document.getElementById('person-details');
    const modalTitle = document.getElementById('modal-title');
    
    if (!personData) {
        modalTitle.textContent = 'Person Not Found';
        detailsContainer.innerHTML = `
            <div class="person-info">
                <div class="welcome-message">
                    <h3>Person Not Found</h3>
                    <p>No data available for ID: ${personId}</p>
                </div>
            </div>
        `;
        showPersonModal();
        return;
    }
    
    // Update modal title
    modalTitle.textContent = personData.name || 'Unknown Person';
    
    const name = personData.name || 'Unknown';
    const birthDate = personData.birth_date || personData.birthday || '';
    const deathDate = personData.death_date || '';
    const marriageDate = personData.marriage_date || '';
    const spouseId = personData.spouse_id || '';
    const fatherId = personData.father_id || '';
    const motherId = personData.mother_id || '';
    const birthPlace = personData.birth_place || '';
    const deathPlace = personData.death_place || '';
    const occupation = personData.occupation || '';
    const notes = personData.notes || '';
    const gender = personData.gender || '';
    
    // Calculate age and life span
    let lifeSpan = '';
    if (birthDate) {
        lifeSpan = birthDate;
        if (deathDate) {
            lifeSpan += ` - ${deathDate}`;
            // Calculate age at death if both dates are available
            const birth = new Date(birthDate);
            const death = new Date(deathDate);
            if (!isNaN(birth) && !isNaN(death)) {
                const ageAtDeath = Math.floor((death - birth) / (365.25 * 24 * 60 * 60 * 1000));
                lifeSpan += ` (age ${ageAtDeath})`;
            }
        } else {
            // Calculate current age if still alive
            const birth = new Date(birthDate);
            if (!isNaN(birth)) {
                const currentAge = Math.floor((new Date() - birth) / (365.25 * 24 * 60 * 60 * 1000));
                lifeSpan += ` (age ${currentAge})`;
            }
        }
    }
    
    // Get family relationships
    const relationships = getPersonRelationships(personId);
    
    detailsContainer.innerHTML = `
        <div class="person-info">
            <div class="person-header">
                <div class="person-photo">
                    ${getPersonPhoto(personId, name)}
                </div>
                <div class="person-basic-info">
                    <h3>${name}</h3>
                    <p class="person-id">ID: ${personId}</p>
                    ${lifeSpan ? `<p class="person-life-span">${lifeSpan}</p>` : ''}
                </div>
            </div>
            
            <div class="tabs">
                <button class="tab-button active" onclick="switchTab('details', this)">Details</button>
                <button class="tab-button" onclick="switchTab('family', this)">Family</button>
                <button class="tab-button" onclick="switchTab('timeline', this)">Timeline</button>
                <button class="tab-button" onclick="switchTab('photos', this)">Photos</button>
            </div>
            
            <div class="tab-content">
                <div id="details-panel" class="tab-panel active">
                    ${generateDetailsPanel(personData, birthPlace, deathPlace, occupation, notes, gender)}
                </div>
                
                <div id="family-panel" class="tab-panel">
                    ${generateFamilyPanel(relationships, personId)}
                </div>
                
                <div id="timeline-panel" class="tab-panel">
                    ${generateTimelinePanel(personData, relationships)}
                </div>
                
                <div id="photos-panel" class="tab-panel">
                    ${generatePhotosPanel(personId)}
                </div>
            </div>
        </div>
    `;
    
    // Show the modal
    showPersonModal();
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
            <div class="search-result" onclick="handleSearchResultClick('${match.id}')">
                ${match.name}
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
    // Recalculate tree layout with improved spacing
    const containerWidth = window.innerWidth - 300;
    const containerHeight = window.innerHeight - 150;

    const root = d3.hierarchy(buildTreeData());
    treeLayout
        .size([containerWidth, containerHeight])
        .separation(dynamicSeparation)
        (root);
    
    const allNodes = root.descendants();
    const nodeById = new Map(allNodes.map(n => [n.data.id, n]));
    
    // Apply enhanced layout adjustments in optimal order
    validateSpouseRelationships(allNodes); // Validate spouse relationships first
    ensureGenerationalSpacing(allNodes);
    resolveFamilyAwareLayout(allNodes, nodeById); // Family grouping first
    resolveCollisionsByDepth(allNodes); // Then collision resolution
    applyDynamicSpacing(allNodes); // Final dynamic spacing adjustment
    drawTree(root);
    
    // Refit to window
    setTimeout(() => fitToWindow(), 100);
});

// Enhanced person details panel functions

function switchTab(tabName, buttonElement) {
    // Hide all tab panels
    const panels = document.querySelectorAll('.tab-panel');
    panels.forEach(panel => panel.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => button.classList.remove('active'));
    
    // Show selected panel and activate button
    const selectedPanel = document.getElementById(`${tabName}-panel`);
    if (selectedPanel) {
        selectedPanel.classList.add('active');
    }
    buttonElement.classList.add('active');
}

function getPersonPhoto(personId, name) {
    // For now, return initials as placeholder
    // In future implementation, this would check for actual photos
    const initials = name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    return `<span title="Click to add photo">${initials}</span>`;
}

function getPersonRelationships(personId) {
    const personData = characterData[personId];
    const relationships = {
        spouse: null,
        parents: [],
        children: [],
        siblings: []
    };
    
    if (!personData) return relationships;
    
    // Get spouse
    if (personData.spouse_id && characterData[personData.spouse_id]) {
        relationships.spouse = {
            id: personData.spouse_id,
            name: characterData[personData.spouse_id].name,
            marriageDate: personData.marriage_date
        };
    }
    
    // Get parents
    if (personData.father_id && characterData[personData.father_id]) {
        relationships.parents.push({
            id: personData.father_id,
            name: characterData[personData.father_id].name,
            type: 'Father'
        });
    }
    if (personData.mother_id && characterData[personData.mother_id]) {
        relationships.parents.push({
            id: personData.mother_id,
            name: characterData[personData.mother_id].name,
            type: 'Mother'
        });
    }
    
    // Get children and siblings by scanning all characters
    for (const [id, person] of Object.entries(characterData)) {
        if (id === personId) continue;
        
        // Check for children
        if (person.father_id === personId || person.mother_id === personId) {
            relationships.children.push({
                id: id,
                name: person.name,
                birthDate: person.birth_date || person.birthday
            });
        }
        
        // Check for siblings (same parents)
        if ((person.father_id && person.father_id === personData.father_id && personData.father_id) ||
            (person.mother_id && person.mother_id === personData.mother_id && personData.mother_id)) {
            relationships.siblings.push({
                id: id,
                name: person.name,
                birthDate: person.birth_date || person.birthday
            });
        }
    }
    
    return relationships;
}

function generateDetailsPanel(personData, birthPlace, deathPlace, occupation, notes, gender) {
    let content = '';
    
    // Basic information
    if (gender) {
        content += `
            <div class="info-item">
                <div class="info-label">Gender</div>
                <div class="info-value">${gender}</div>
            </div>
        `;
    }
    
    if (birthPlace) {
        content += `
            <div class="info-item">
                <div class="info-label">Birth Place</div>
                <div class="info-value">${birthPlace}</div>
            </div>
        `;
    }
    
    if (deathPlace) {
        content += `
            <div class="info-item">
                <div class="info-label">Death Place</div>
                <div class="info-value">${deathPlace}</div>
            </div>
        `;
    }
    
    if (occupation) {
        content += `
            <div class="info-item">
                <div class="info-label">Occupation</div>
                <div class="info-value">${occupation}</div>
            </div>
        `;
    }
    
    if (notes) {
        content += `
            <div class="info-item">
                <div class="info-label">Notes</div>
                <div class="info-value">${notes}</div>
            </div>
        `;
    }
    
    if (!content) {
        content = '<p class="info-value">No additional details available.</p>';
    }
    
    return content;
}

function generateFamilyPanel(relationships, currentPersonId) {
    let content = '';
    
    // Parents
    if (relationships.parents.length > 0) {
        content += '<div class="info-label">Parents</div>';
        relationships.parents.forEach(parent => {
            content += `
                <div class="relationship-item" onclick="selectPersonById('${parent.id}')">
                    <div class="relationship-type">${parent.type}</div>
                    <div class="relationship-name">${parent.name}</div>
                </div>
            `;
        });
    }
    
    // Spouse
    if (relationships.spouse) {
        content += '<div class="info-label">Spouse</div>';
        content += `
            <div class="relationship-item" onclick="selectPersonById('${relationships.spouse.id}')">
                <div class="relationship-type">Spouse</div>
                <div class="relationship-name">${relationships.spouse.name}</div>
                ${relationships.spouse.marriageDate ? `<div style="font-size: 0.8em; color: #7f8c8d;">Married: ${relationships.spouse.marriageDate}</div>` : ''}
            </div>
        `;
    }
    
    // Children
    if (relationships.children.length > 0) {
        content += '<div class="info-label">Children</div>';
        relationships.children
            .sort((a, b) => (a.birthDate || '').localeCompare(b.birthDate || ''))
            .forEach(child => {
                content += `
                    <div class="relationship-item" onclick="selectPersonById('${child.id}')">
                        <div class="relationship-type">Child</div>
                        <div class="relationship-name">${child.name}</div>
                        ${child.birthDate ? `<div style="font-size: 0.8em; color: #7f8c8d;">Born: ${child.birthDate}</div>` : ''}
                    </div>
                `;
            });
    }
    
    // Siblings
    if (relationships.siblings.length > 0) {
        content += '<div class="info-label">Siblings</div>';
        relationships.siblings
            .sort((a, b) => (a.birthDate || '').localeCompare(b.birthDate || ''))
            .forEach(sibling => {
                content += `
                    <div class="relationship-item" onclick="selectPersonById('${sibling.id}')">
                        <div class="relationship-type">Sibling</div>
                        <div class="relationship-name">${sibling.name}</div>
                        ${sibling.birthDate ? `<div style="font-size: 0.8em; color: #7f8c8d;">Born: ${sibling.birthDate}</div>` : ''}
                    </div>
                `;
            });
    }
    
    // Mini family tree
    content += generateMiniTree(relationships, currentPersonId);
    
    if (!content) {
        content = '<p class="info-value">No family relationships found.</p>';
    }
    
    return content;
}

function generateMiniTree(relationships, currentPersonId) {
    const currentPerson = characterData[currentPersonId];
    if (!currentPerson) return '';
    
    let miniTree = '<div class="mini-tree"><div class="mini-tree-title">Immediate Family</div>';
    
    // Parents level
    if (relationships.parents.length > 0) {
        miniTree += '<div class="family-level">';
        relationships.parents.forEach((parent, index) => {
            if (index > 0) miniTree += '<div class="family-connector"></div>';
            miniTree += `<div class="family-member" onclick="selectPersonById('${parent.id}')">${parent.name.split(' ')[0]}</div>`;
        });
        miniTree += '</div>';
    }
    
    // Current person + spouse level
    miniTree += '<div class="family-level">';
    if (relationships.spouse) {
        miniTree += `<div class="family-member" onclick="selectPersonById('${relationships.spouse.id}')">${relationships.spouse.name.split(' ')[0]}</div>`;
        miniTree += '<div class="family-connector"></div>';
    }
    miniTree += `<div class="family-member current">${currentPerson.name.split(' ')[0]}</div>`;
    miniTree += '</div>';
    
    // Children level
    if (relationships.children.length > 0) {
        miniTree += '<div class="family-level">';
        relationships.children.forEach((child, index) => {
            if (index > 0) miniTree += '<div class="family-connector"></div>';
            miniTree += `<div class="family-member" onclick="selectPersonById('${child.id}')">${child.name.split(' ')[0]}</div>`;
        });
        miniTree += '</div>';
    }
    
    miniTree += '</div>';
    return miniTree;
}

function generateTimelinePanel(personData, relationships) {
    const events = [];
    
    // Birth
    if (personData.birth_date || personData.birthday) {
        events.push({
            date: personData.birth_date || personData.birthday,
            event: 'Born',
            location: personData.birth_place || ''
        });
    }
    
    // Marriage
    if (personData.marriage_date && relationships.spouse) {
        events.push({
            date: personData.marriage_date,
            event: `Married ${relationships.spouse.name}`,
            location: ''
        });
    }
    
    // Children births
    relationships.children.forEach(child => {
        if (child.birthDate) {
            events.push({
                date: child.birthDate,
                event: `${child.name} born`,
                location: ''
            });
        }
    });
    
    // Death
    if (personData.death_date) {
        events.push({
            date: personData.death_date,
            event: 'Died',
            location: personData.death_place || ''
        });
    }
    
    // Sort events by date
    events.sort((a, b) => a.date.localeCompare(b.date));
    
    let content = '';
    events.forEach(event => {
        content += `
            <div class="info-item">
                <div class="info-label">${event.date}</div>
                <div class="info-value">
                    ${event.event}
                    ${event.location ? `<br><small>Location: ${event.location}</small>` : ''}
                </div>
            </div>
        `;
    });
    
    if (!content) {
        content = '<p class="info-value">No timeline events available.</p>';
    }
    
    return content;
}

function generatePhotosPanel(personId) {
    // For now, show placeholder for photo upload
    // In future implementation, this would load actual photos from storage
    return `
        <div class="photo-gallery">
            <div class="photo-placeholder" onclick="uploadPhoto('${personId}')" title="Click to add photos">
                📷
            </div>
        </div>
        <div style="margin-top: 15px; color: #7f8c8d; font-size: 0.9em; text-align: center;">
            Photo management will be available in a future update.
        </div>
    `;
}

function selectPersonById(personId) {
    // Clear previous selection
    d3.selectAll('.node rect').classed('selected', false);
    
    // Find and select the node
    const targetNode = d3.selectAll('.node').filter(d => d.data.id === personId);
    if (!targetNode.empty()) {
        targetNode.select('rect').classed('selected', true);
        
        // Center on the selected node
        const nodeData = targetNode.datum();
        if (nodeData) {
            centerOnNode(nodeData);
        }
    }
    
    // Show person details
    showPersonDetails(personId);
    
    // Update search if person is not visible
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        const personData = characterData[personId];
        if (personData && personData.name) {
            searchInput.value = personData.name;
            searchPeople(personData.name);
        }
    }
}

function uploadPhoto(personId) {
    // Placeholder function for photo upload functionality
    alert('Photo upload functionality will be implemented in a future update.');
}

function centerOnNode(nodeData) {
    const svg = d3.select("#tree-svg svg");
    const g = svg.select("g");
    
    if (svg.empty() || g.empty()) return;
    
    const svgRect = svg.node().getBoundingClientRect();
    const svgWidth = svgRect.width;
    const svgHeight = svgRect.height;
    
    // Calculate the transform to center the node
    const scale = d3.zoomTransform(svg.node()).k;
    const x = -nodeData.x * scale + svgWidth / 2;
    const y = -nodeData.y * scale + svgHeight / 2;
    
    // Apply smooth transition to the new position
    svg.transition()
        .duration(750)
        .call(d3.zoom().transform, d3.zoomIdentity.translate(x, y).scale(scale));
}

// Modal management functions

function showPersonModal() {
    const modal = document.getElementById('person-modal');
    const backdrop = document.getElementById('modal-backdrop');
    
    if (modal && backdrop) {
        modal.classList.add('show');
        backdrop.classList.add('show');
        
        // Add escape key listener
        document.addEventListener('keydown', handleModalEscape);
        
        // Initialize draggable functionality
        initModalDrag();
    }
}

function closePersonModal() {
    const modal = document.getElementById('person-modal');
    const backdrop = document.getElementById('modal-backdrop');
    
    if (modal && backdrop) {
        modal.classList.remove('show');
        backdrop.classList.remove('show');
        
        // Remove escape key listener
        document.removeEventListener('keydown', handleModalEscape);
        
        // Clear selection highlighting
        d3.selectAll('.node rect').classed('selected', false);
    }
}

function handleModalEscape(event) {
    if (event.key === 'Escape') {
        closePersonModal();
    }
}

// Update search results handling for modal
function handleSearchResultClick(personId) {
    // Clear previous selection
    d3.selectAll('.node rect').classed('selected', false);
    
    // Find and select the node
    const targetNode = d3.selectAll('.node').filter(d => d.data.id === personId);
    if (!targetNode.empty()) {
        targetNode.select('rect').classed('selected', true);
        
        // Center on the selected node
        const nodeData = targetNode.datum();
        if (nodeData) {
            centerOnNode(nodeData);
        }
    }
    
    // Show person details in modal
    showPersonDetails(personId);
    
    // Clear search results
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    if (searchInput) searchInput.value = '';
    if (searchResults) searchResults.innerHTML = '';
}

// Modal dragging functionality
let isDragging = false;
let currentX;
let currentY;
let initialX;
let initialY;
let xOffset = 0;
let yOffset = 0;

function initModalDrag() {
    const modal = document.getElementById('person-modal');
    const header = modal.querySelector('.modal-header');
    
    if (!header) return;
    
    header.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', dragMove);
    document.addEventListener('mouseup', dragEnd);
    
    // Touch events for mobile
    header.addEventListener('touchstart', dragStart);
    document.addEventListener('touchmove', dragMove);
    document.addEventListener('touchend', dragEnd);
}

function dragStart(e) {
    const modal = document.getElementById('person-modal');
    if (!modal) return;
    
    if (e.type === "touchstart") {
        initialX = e.touches[0].clientX - xOffset;
        initialY = e.touches[0].clientY - yOffset;
    } else {
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;
    }

    if (e.target.closest('.modal-header')) {
        isDragging = true;
        modal.style.transition = 'none';
    }
}

function dragMove(e) {
    if (isDragging) {
        e.preventDefault();
        
        if (e.type === "touchmove") {
            currentX = e.touches[0].clientX - initialX;
            currentY = e.touches[0].clientY - initialY;
        } else {
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
        }

        xOffset = currentX;
        yOffset = currentY;

        const modal = document.getElementById('person-modal');
        if (modal) {
            // Keep modal within viewport bounds
            const rect = modal.getBoundingClientRect();
            const maxX = window.innerWidth - rect.width;
            const maxY = window.innerHeight - rect.height;
            
            xOffset = Math.max(-rect.width/2, Math.min(maxX - rect.width/2, xOffset));
            yOffset = Math.max(-rect.height/2, Math.min(maxY - rect.height/2, yOffset));
            
            modal.style.transform = `translate(calc(-50% + ${xOffset}px), calc(-50% + ${yOffset}px))`;
        }
    }
}

function dragEnd(e) {
    if (isDragging) {
        const modal = document.getElementById('person-modal');
        if (modal) {
            modal.style.transition = '';
        }
        isDragging = false;
    }
} 