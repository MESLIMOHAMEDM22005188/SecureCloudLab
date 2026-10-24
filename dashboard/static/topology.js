
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const $ = (id) => document.getElementById(id);

    const elements = {
        refresh: $("refresh-topology"),
        message: $("topology-message"),
        empty: $("topology-empty"),
        container: $("topology-container"),
        canvas: $("topology-canvas"),
        svg: $("topology-svg"),
        edges: $("topology-edges"),
        nodes: $("topology-nodes"),
        network: $("topology-network"),
        nodeCount: $("topology-node-count"),
        subnetCount: $("topology-subnet-count"),
        hostCount: $("topology-host-count"),
        status: $("topology-status"),
        componentsEmpty: $("components-empty"),
        componentsContainer: $("components-container"),
        componentsBody: $("topology-components-body"),
        zoomIn: $("topology-zoom-in"),
        zoomOut: $("topology-zoom-out"),
        zoomReset: $("topology-zoom-reset"),
    };

    if (!elements.svg || !elements.nodes || !elements.edges) return;

    const SVG_NS = "http://www.w3.org/2000/svg";

    let topologyData = null;
    let zoom = 1;
    let panX = 0;
    let panY = 0;
    let dragState = null;

    const NODE_WIDTH = 190;
    const NODE_HEIGHT = 66;
    const HORIZONTAL_GAP = 55;
    const VERTICAL_GAP = 100;
    const PADDING = 45;

    function showMessage(message, type = "info") {
        if (!elements.message) return;

        elements.message.textContent = message;
        elements.message.hidden = false;
        elements.message.className = `message message-${type}`;
    }

    function hideMessage() {
        if (!elements.message) return;
        elements.message.hidden = true;
        elements.message.textContent = "";
    }

    async function fetchJSON(url) {
        const response = await fetch(url, {
            headers: { Accept: "application/json" },
        });

        const contentType = response.headers.get("content-type") || "";
        let data;

        if (contentType.includes("application/json")) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            const detail =
                typeof data === "object" && data !== null
                    ? data.detail || data.message
                    : data;

            throw new Error(detail || `Request failed (${response.status}).`);
        }

        if (typeof data !== "object" || data === null) {
            throw new Error("The topology endpoint did not return JSON.");
        }

        return data;
    }

    function svgElement(tag, attributes = {}, text = null) {
        const element = document.createElementNS(SVG_NS, tag);

        for (const [name, value] of Object.entries(attributes)) {
            element.setAttribute(name, String(value));
        }

        if (text !== null) {
            element.textContent = String(text);
        }

        return element;
    }

    function nodeColor(kind) {
        switch (String(kind).toLowerCase()) {
            case "network":
            case "vpc":
                return "#6478f8";
            case "public":
                return "#21b88b";
            case "private":
                return "#e4a343";
            case "host":
                return "#64748b";
            default:
                return "#64748b";
        }
    }

    function nodeDescription(node) {
        if (node.cidr) return node.cidr;
        if (node.ip) return node.ip;
        return node.kind || "Network component";
    }

    function normalizeTopology(data) {
        if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
            throw new Error(
                "Invalid topology response: nodes and edges arrays are required."
            );
        }

        const ids = new Set();

        for (const node of data.nodes) {
            if (!node || typeof node.id !== "string" || !node.id) {
                throw new Error("Every topology node must have a valid ID.");
            }

            if (ids.has(node.id)) {
                throw new Error(`Duplicate topology node ID: ${node.id}`);
            }

            ids.add(node.id);
        }

        for (const edge of data.edges) {
            if (
                !edge ||
                !ids.has(edge.source) ||
                !ids.has(edge.target)
            ) {
                throw new Error("A topology connection references an unknown node.");
            }
        }

        return data;
    }

    function getNodeKind(node) {
        const kind = String(node.kind || "").toLowerCase();

        if (kind === "network" || kind === "vpc") return "network";
        if (kind === "public") return "public";
        if (kind === "private") return "private";
        if (kind === "host") return "host";

        return "other";
    }

    function layoutTopology(data) {
        const nodes = data.nodes;
        const nodeById = new Map(nodes.map((node) => [node.id, node]));
        const positions = new Map();

        const networkNodes = nodes.filter(
            (node) => getNodeKind(node) === "network"
        );

        const subnetNodes = nodes.filter((node) =>
            ["public", "private"].includes(getNodeKind(node))
        );

        const hostNodes = nodes.filter(
            (node) => getNodeKind(node) === "host"
        );

        const otherNodes = nodes.filter(
            (node) =>
                !["network", "public", "private", "host"].includes(
                    getNodeKind(node)
                )
        );

        const hostsBySubnet = new Map();
        for (const subnet of subnetNodes) {
            hostsBySubnet.set(subnet.id, []);
        }

        for (const host of hostNodes) {
            const subnetId = host.subnet;

            if (hostsBySubnet.has(subnetId)) {
                hostsBySubnet.get(subnetId).push(host);
            } else {
                const parentEdge = data.edges.find(
                    (edge) => edge.target === host.id
                );

                if (parentEdge && hostsBySubnet.has(parentEdge.source)) {
                    hostsBySubnet.get(parentEdge.source).push(host);
                }
            }
        }

        // Place the main network at the top.
        networkNodes.forEach((node, index) => {
            positions.set(node.id, {
                x: PADDING + index * (NODE_WIDTH + HORIZONTAL_GAP),
                y: PADDING,
            });
        });

        // Public and private subnets are arranged in separate columns.
        const columns = { public: [], private: [], other: [] };

        for (const subnet of subnetNodes) {
            const kind = getNodeKind(subnet);
            columns[kind].push(subnet);
        }

        const columnOrder = ["public", "private", "other"];
        let columnIndex = 0;

        for (const kind of columnOrder) {
            const group = columns[kind];

            if (!group.length) continue;

            const x = PADDING + columnIndex * (NODE_WIDTH + HORIZONTAL_GAP);

            group.forEach((subnet, index) => {
                positions.set(subnet.id, {
                    x,
                    y: PADDING + NODE_HEIGHT + VERTICAL_GAP +
                        index * (NODE_HEIGHT + VERTICAL_GAP),
                });
            });

            columnIndex++;
        }

        // Place each host underneath its parent subnet.
        for (const subnet of subnetNodes) {
            const subnetPosition = positions.get(subnet.id);
            if (!subnetPosition) continue;

            const hosts = hostsBySubnet.get(subnet.id) || [];

            hosts.forEach((host, index) => {
                positions.set(host.id, {
                    x: subnetPosition.x,
                    y:
                        subnetPosition.y +
                        NODE_HEIGHT +
                        38 +
                        index * (NODE_HEIGHT + 25),
                });
            });
        }

        // Keep unclassified nodes visible.
        for (const node of otherNodes) {
            if (positions.has(node.id)) continue;

            positions.set(node.id, {
                x: PADDING + columnIndex * (NODE_WIDTH + HORIZONTAL_GAP),
                y: PADDING + NODE_HEIGHT + VERTICAL_GAP,
            });

            columnIndex++;
        }

        // Ensure nodes not covered by the expected schema remain visible.
        let fallbackIndex = 0;

        for (const node of nodes) {
            if (positions.has(node.id)) continue;

            positions.set(node.id, {
                x: PADDING + fallbackIndex * (NODE_WIDTH + HORIZONTAL_GAP),
                y: PADDING + NODE_HEIGHT + VERTICAL_GAP,
            });

            fallbackIndex++;
        }

        const width = Math.max(
            1000,
            ...Array.from(positions.values()).map(
                (position) => position.x + NODE_WIDTH + PADDING
            )
        );

        const height = Math.max(
            600,
            ...Array.from(positions.values()).map(
                (position) => position.y + NODE_HEIGHT + PADDING
            )
        );

        return { positions, nodeById, width, height };
    }

    function drawEdge(edge, positions) {
        const source = positions.get(edge.source);
        const target = positions.get(edge.target);

        if (!source || !target) return null;

        const x1 = source.x + NODE_WIDTH / 2;
        const y1 = source.y + NODE_HEIGHT;
        const x2 = target.x + NODE_WIDTH / 2;
        const y2 = target.y;

        const middleY = y1 + Math.max(20, (y2 - y1) / 2);

        const path = svgElement("path", {
            d: `M ${x1} ${y1} V ${middleY} H ${x2} V ${y2}`,
            fill: "none",
            stroke: "#64748b",
            "stroke-width": 2,
            "stroke-opacity": 0.65,
            "stroke-linejoin": "round",
            "marker-end": "url(#topology-arrow)",
        });

        path.appendChild(
            svgElement("title", {}, `${edge.source} → ${edge.target}`)
        );

        return path;
    }

    function drawNode(node, position) {
        const kind = getNodeKind(node);
        const color = nodeColor(kind);
        const group = svgElement("g", {
            transform: `translate(${position.x}, ${position.y})`,
            class: `topology-node topology-node-${kind}`,
            tabindex: 0,
            role: "group",
            "aria-label": `${node.label || node.id}, ${nodeDescription(node)}`,
        });

        group.appendChild(
            svgElement("rect", {
                width: NODE_WIDTH,
                height: NODE_HEIGHT,
                rx: 10,
                fill: "#111c2e",
                stroke: color,
                "stroke-width": 2,
            })
        );

        group.appendChild(
            svgElement("rect", {
                width: 5,
                height: NODE_HEIGHT - 2,
                x: 1,
                y: 1,
                rx: 2,
                fill: color,
            })
        );

        const label = String(node.label || node.id);
        const maxLabelLength = 25;
        const visibleLabel =
            label.length > maxLabelLength
                ? `${label.slice(0, maxLabelLength - 1)}…`
                : label;

        group.appendChild(
            svgElement(
                "text",
                {
                    x: NODE_WIDTH / 2,
                    y: 27,
                    fill: "#f1f5f9",
                    "font-size": 13,
                    "font-weight": 600,
                    "text-anchor": "middle",
                },
                visibleLabel
            )
        );

        group.appendChild(
            svgElement(
                "text",
                {
                    x: NODE_WIDTH / 2,
                    y: 47,
                    fill: "#a7b4c8",
                    "font-size": 11,
                    "text-anchor": "middle",
                },
                nodeDescription(node)
            )
        );

        group.appendChild(
            svgElement(
                "title",
                {},
                `${label}\n${nodeDescription(node)}`
            )
        );

        return group;
    }

    function renderGraph(data) {
        const layout = layoutTopology(data);

        elements.edges.replaceChildren();
        elements.nodes.replaceChildren();

        const defs = svgElement("defs");
        const marker = svgElement("marker", {
            id: "topology-arrow",
            markerWidth: 8,
            markerHeight: 8,
            refX: 6,
            refY: 3,
            orient: "auto",
            markerUnits: "strokeWidth",
        });

        marker.appendChild(
            svgElement("path", {
                d: "M0,0 L0,6 L6,3 z",
                fill: "#64748b",
            })
        );

        defs.appendChild(marker);
        elements.svg.replaceChildren(defs);

        // The transformed group contains all graph elements.
        const viewport = svgElement("g", {
            id: "topology-viewport",
        });

        for (const edge of data.edges) {
            const edgeElement = drawEdge(edge, layout.positions);
            if (edgeElement) elements.edges.appendChild(edgeElement);
        }

        for (const node of data.nodes) {
            const position = layout.positions.get(node.id);
            if (position) {
                elements.nodes.appendChild(drawNode(node, position));
            }
        }

        viewport.append(elements.edges, elements.nodes);
        elements.svg.appendChild(viewport);

        elements.svg.setAttribute(
            "viewBox",
            `0 0 ${layout.width} ${layout.height}`
        );

        zoom = 1;
        panX = 0;
        panY = 0;
        applyTransform();

        elements.container.hidden = false;
        elements.empty.hidden = true;
    }

    function applyTransform() {
        const viewport = $("topology-viewport");
        if (!viewport) return;

        viewport.setAttribute(
            "transform",
            `translate(${panX}, ${panY}) scale(${zoom})`
        );
    }

    function renderComponentTable(data) {
        if (!elements.componentsBody) return;

        elements.componentsBody.replaceChildren();

        for (const node of data.nodes) {
            const row = document.createElement("tr");

            const nameCell = document.createElement("td");
            nameCell.textContent = node.label || node.id;

            const typeCell = document.createElement("td");
            typeCell.textContent = node.kind || "Unknown";

            const addressCell = document.createElement("td");
            const address = document.createElement("code");
            address.textContent = node.cidr || node.ip || "—";
            addressCell.appendChild(address);

            const parentCell = document.createElement("td");
            parentCell.textContent = node.subnet || "—";

            row.append(nameCell, typeCell, addressCell, parentCell);
            elements.componentsBody.appendChild(row);
        }

        if (elements.componentsEmpty) {
            elements.componentsEmpty.hidden = data.nodes.length > 0;
        }

        if (elements.componentsContainer) {
            elements.componentsContainer.hidden = data.nodes.length === 0;
        }
    }

    function renderStatistics(data) {
        const networkNode = data.nodes.find(
            (node) => getNodeKind(node) === "network"
        );

        const subnets = data.nodes.filter((node) =>
            ["public", "private"].includes(getNodeKind(node))
        );

        const hosts = data.nodes.filter(
            (node) => getNodeKind(node) === "host"
        );

        if (elements.network) {
            elements.network.textContent =
                data.network ||
                (networkNode && networkNode.cidr) ||
                "—";
        }

        if (elements.nodeCount) {
            elements.nodeCount.textContent = data.nodes.length;
        }

        if (elements.subnetCount) {
            elements.subnetCount.textContent = subnets.length;
        }

        if (elements.hostCount) {
            elements.hostCount.textContent = hosts.length;
        }
    }

    async function loadTopology() {
        hideMessage();

        if (elements.refresh) {
            elements.refresh.disabled = true;
            elements.refresh.textContent = "Loading...";
        }

        if (elements.status) {
            elements.status.textContent = "Loading topology...";
        }

        try {
            // This endpoint must return build_topology(plan).
            const data = await fetchJSON("/api/topology");
            topologyData = normalizeTopology(data);

            renderStatistics(topologyData);
            renderGraph(topologyData);
            renderComponentTable(topologyData);

            if (elements.status) {
                elements.status.textContent =
                    `Loaded ${topologyData.nodes.length} nodes and ` +
                    `${topologyData.edges.length} connections`;
            }

            if (topologyData.nodes.length === 0) {
                showMessage("The topology response contains no nodes.", "info");
            }
        } catch (error) {
            topologyData = null;

            if (elements.container) elements.container.hidden = true;
            if (elements.empty) elements.empty.hidden = false;

            if (elements.status) {
                elements.status.textContent = "Unable to load topology";
            }

            showMessage(
                `Could not load topology: ${error.message}`,
                "error"
            );
        } finally {
            if (elements.refresh) {
                elements.refresh.disabled = false;
                elements.refresh.textContent = "Refresh topology";
            }
        }
    }

    elements.refresh?.addEventListener("click", loadTopology);

    elements.zoomIn?.addEventListener("click", () => {
        zoom = Math.min(zoom * 1.2, 3);
        applyTransform();
    });

    elements.zoomOut?.addEventListener("click", () => {
        zoom = Math.max(zoom / 1.2, 0.4);
        applyTransform();
    });

    elements.zoomReset?.addEventListener("click", () => {
        zoom = 1;
        panX = 0;
        panY = 0;
        applyTransform();
    });

    // Drag the topology to pan around the diagram.
    elements.canvas?.addEventListener("pointerdown", (event) => {
        if (event.target.closest(".topology-node")) return;

        dragState = {
            pointerId: event.pointerId,
            startX: event.clientX,
            startY: event.clientY,
            originalX: panX,
            originalY: panY,
        };

        elements.canvas.setPointerCapture?.(event.pointerId);
    });

    elements.canvas?.addEventListener("pointermove", (event) => {
        if (!dragState || dragState.pointerId !== event.pointerId) return;

        panX =
            dragState.originalX +
            (event.clientX - dragState.startX) / zoom;
        panY =
            dragState.originalY +
            (event.clientY - dragState.startY) / zoom;

        applyTransform();
    });

    function endDrag(event) {
        if (!dragState || dragState.pointerId !== event.pointerId) return;
        dragState = null;
    }

    elements.canvas?.addEventListener("pointerup", endDrag);
    elements.canvas?.addEventListener("pointercancel", endDrag);

    // Support trackpad and mouse-wheel zoom.
    elements.canvas?.addEventListener(
        "wheel",
        (event) => {
            if (!event.ctrlKey && !event.metaKey) return;

            event.preventDefault();

            zoom = event.deltaY < 0
                ? Math.min(zoom * 1.1, 3)
                : Math.max(zoom / 1.1, 0.4);

            applyTransform();
        },
        { passive: false }
    );

    loadTopology();
});
