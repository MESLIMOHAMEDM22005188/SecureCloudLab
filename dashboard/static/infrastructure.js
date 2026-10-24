
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("infrastructure-form");
    if (!form) return;

    const $ = (id) => document.getElementById(id);

    const elements = {
        cidr: $("network-cidr"),
        prefix: $("subnet-prefix"),
        publicSubnets: $("public-subnets"),
        privateSubnets: $("private-subnets"),
        publicHosts: $("public-hosts"),
        privateHosts: $("private-hosts"),
        planButton: $("plan-button"),
        resetButton: $("reset-button"),
        generateButton: $("generate-terraform-button"),
        message: $("form-message"),
        terraformMessage: $("terraform-message"),
        empty: $("plan-empty"),
        results: $("plan-results"),
        publicList: $("public-subnet-list"),
        privateList: $("private-subnet-list"),
        terraformEmpty: $("terraform-empty"),
        terraformResults: $("terraform-results"),
        terraformCode: $("terraform-code"),
        copyButton: $("copy-terraform-button"),
    };

    let currentPlan = null;
    let currentTerraform = "";

    function showMessage(element, message, type = "info") {
        if (!element) return;

        element.textContent = message;
        element.hidden = false;
        element.className = `message message-${type}`;
    }

    function hideMessage(element) {
        if (element) {
            element.hidden = true;
            element.textContent = "";
        }
    }

    async function requestJSON(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
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
                    ? data.detail || data.message || JSON.stringify(data)
                    : data;

            throw new Error(detail || `HTTP error ${response.status}`);
        }

        return data;
    }

    function getConfiguration() {
        const config = {
            cidr: elements.cidr.value.trim(),
            subnet_prefix: Number(elements.prefix.value),
            public_subnets: Number(elements.publicSubnets.value),
            private_subnets: Number(elements.privateSubnets.value),
            public_hosts_per_subnet: Number(elements.publicHosts.value),
            private_hosts_per_subnet: Number(elements.privateHosts.value),
        };

        if (!config.cidr) {
            throw new Error("Enter a network CIDR.");
        }

        if (
            !Number.isInteger(config.subnet_prefix) ||
            config.subnet_prefix < 0 ||
            config.subnet_prefix > 32
        ) {
            throw new Error("The subnet prefix must be a valid integer.");
        }

        const integerFields = [
            ["Public subnets", config.public_subnets],
            ["Private subnets", config.private_subnets],
            ["Hosts per public subnet", config.public_hosts_per_subnet],
            ["Hosts per private subnet", config.private_hosts_per_subnet],
        ];

        for (const [label, value] of integerFields) {
            if (!Number.isInteger(value) || value < 0) {
                throw new Error(`${label} must be a non-negative integer.`);
            }
        }

        if (config.public_subnets + config.private_subnets < 1) {
            throw new Error("Configure at least one subnet.");
        }

        if (config.public_subnets + config.private_subnets > 128) {
            throw new Error("A maximum of 128 subnets is supported.");
        }

        return config;
    }

    function validateIPv4CIDR(value) {
        const parts = value.split("/");

        if (parts.length !== 2 || !/^\d+$/.test(parts[1])) {
            throw new Error("Enter a valid IPv4 CIDR, for example 10.0.0.0/16.");
        }

        const octets = parts[0].split(".");
        const prefix = Number(parts[1]);

        if (
            octets.length !== 4 ||
            octets.some(
                (octet) =>
                    !/^\d{1,3}$/.test(octet) ||
                    Number(octet) < 0 ||
                    Number(octet) > 255
            ) ||
            prefix < 0 ||
            prefix > 32
        ) {
            throw new Error("The IPv4 CIDR is invalid.");
        }

        const address = octets.map(Number);

        // Check that the address identifies the network itself.
        const value32 = address.reduce(
            (result, octet) => result * 256 + octet,
            0
        );
        const mask =
            prefix === 0 ? 0 : (0xffffffff << (32 - prefix)) >>> 0;

        if (((value32 >>> 0) & mask) !== (value32 >>> 0)) {
            throw new Error(
                "Use the network address, not a host address. For example: 10.0.0.0/16."
            );
        }
    }

    function renderSubnetList(container, subnets, kind) {
        container.replaceChildren();

        if (!Array.isArray(subnets) || subnets.length === 0) {
            const empty = document.createElement("p");
            empty.className = "muted-text";
            empty.textContent = "No subnets configured.";
            container.appendChild(empty);
            return;
        }

        for (const subnet of subnets) {
            const card = document.createElement("article");
            card.className = `subnet-card subnet-${kind}`;

            const header = document.createElement("div");
            header.className = "subnet-card-header";

            const name = document.createElement("strong");
            name.textContent = subnet.name || "Unnamed subnet";

            const badge = document.createElement("span");
            badge.className = `subnet-badge subnet-badge-${kind}`;
            badge.textContent = kind === "public" ? "PUBLIC" : "PRIVATE";

            header.append(name, badge);

            const cidr = document.createElement("p");
            cidr.className = "subnet-cidr";
            cidr.textContent = subnet.cidr || "CIDR unavailable";

            card.append(header, cidr);

            const hosts = Array.isArray(subnet.hosts) ? subnet.hosts : [];

            if (hosts.length > 0) {
                const hostTitle = document.createElement("span");
                hostTitle.className = "summary-label";
                hostTitle.textContent = "Planned hosts";
                card.appendChild(hostTitle);

                const hostList = document.createElement("ul");
                hostList.className = "subnet-host-list";

                for (const host of hosts) {
                    const item = document.createElement("li");
                    const hostName = document.createElement("span");
                    const hostIP = document.createElement("code");

                    hostName.textContent = host.name || "Host";
                    hostIP.textContent = host.ip || "IP unavailable";

                    item.append(hostName, hostIP);
                    hostList.appendChild(item);
                }

                card.appendChild(hostList);
            }

            container.appendChild(card);
        }
    }

    function renderPlan(plan) {
        if (!plan || typeof plan !== "object") {
            throw new Error("The server returned an invalid network plan.");
        }

        const publicSubnets = plan.public_subnets || [];
        const privateSubnets = plan.private_subnets || [];

        if (
            !Array.isArray(publicSubnets) ||
            !Array.isArray(privateSubnets)
        ) {
            throw new Error("The network plan contains invalid subnet data.");
        }

        const hostCount = [...publicSubnets, ...privateSubnets].reduce(
            (total, subnet) =>
                total + (Array.isArray(subnet.hosts) ? subnet.hosts.length : 0),
            0
        );

        $("stat-network").textContent = plan.network || "—";
        $("stat-subnets").textContent =
            publicSubnets.length + privateSubnets.length;
        $("stat-hosts").textContent = hostCount;

        $("result-network").textContent = plan.network || "—";
        $("result-prefix").textContent =
            plan.subnet_prefix !== undefined
                ? `Subnet prefix: /${plan.subnet_prefix}`
                : "";

        $("public-count").textContent = publicSubnets.length;
        $("private-count").textContent = privateSubnets.length;

        renderSubnetList(elements.publicList, publicSubnets, "public");
        renderSubnetList(elements.privateList, privateSubnets, "private");

        elements.empty.hidden = true;
        elements.results.hidden = false;

        // A new plan invalidates the previous Terraform preview.
        currentTerraform = "";
        elements.terraformCode.textContent = "";
        elements.terraformResults.hidden = true;
        elements.terraformEmpty.hidden = false;

        hideMessage(elements.terraformMessage);
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        hideMessage(elements.message);

        let config;

        try {
            config = getConfiguration();
            validateIPv4CIDR(config.cidr);
        } catch (error) {
            showMessage(elements.message, error.message, "error");
            return;
        }

        elements.planButton.disabled = true;
        elements.planButton.textContent = "Generating plan...";

        try {
            const plan = await requestJSON("/api/infrastructure/plan", {
                method: "POST",
                body: JSON.stringify(config),
            });

            renderPlan(plan);
            currentPlan = plan;

            showMessage(
                elements.message,
                "Network plan generated successfully.",
                "success"
            );

            $("stat-scan-status").textContent = "Planned";
        } catch (error) {
            showMessage(
                elements.message,
                `Unable to generate the network plan: ${error.message}`,
                "error"
            );
        } finally {
            elements.planButton.disabled = false;
            elements.planButton.textContent = "Generate network plan";
        }
    });

    elements.generateButton?.addEventListener("click", async () => {
        hideMessage(elements.terraformMessage);

        if (!currentPlan) {
            showMessage(
                elements.terraformMessage,
                "Generate a network plan before generating Terraform.",
                "error"
            );
            return;
        }

        elements.generateButton.disabled = true;
        elements.generateButton.textContent = "Generating Terraform...";

        try {
            // The backend route must accept this configuration payload.
            const result = await requestJSON(
                "/api/infrastructure/generate",
                {
                    method: "POST",
                    body: JSON.stringify({
                        ...getConfiguration(),
                    }),
                }
            );

            // Support either a raw Terraform string or a JSON response.
            let terraform = "";

            if (typeof result === "string") {
                terraform = result;
            } else if (result && typeof result === "object") {
                terraform =
                    result.terraform ??
                    result.content ??
                    result.code ??
                    result.terraform_content ??
                    "";
            }

            if (typeof terraform !== "string" || !terraform.trim()) {
                const location =
                    result && typeof result === "object"
                        ? result.path || result.file_path || result.filename
                        : null;

                if (location) {
                    showMessage(
                        elements.terraformMessage,
                        `Terraform was generated at ${location}. The API did not return its content for preview.`,
                        "success"
                    );
                    return;
                }

                throw new Error(
                    "The API did not return Terraform code. Check the response format in app.py."
                );
            }

            currentTerraform = terraform;
            elements.terraformCode.textContent = terraform;
            elements.terraformEmpty.hidden = true;
            elements.terraformResults.hidden = false;

            if (result && typeof result === "object") {
                const filename =
                    result.filename || result.file_name || "main.tf";
                $("terraform-filename").textContent = filename;
            }

            showMessage(
                elements.terraformMessage,
                "Terraform configuration generated. Review it before deployment.",
                "success"
            );
        } catch (error) {
            showMessage(
                elements.terraformMessage,
                `Unable to generate Terraform: ${error.message}`,
                "error"
            );
        } finally {
            elements.generateButton.disabled = false;
            elements.generateButton.textContent = "Generate Terraform";
        }
    });

    elements.copyButton?.addEventListener("click", async () => {
        if (!currentTerraform) {
            showMessage(
                elements.terraformMessage,
                "There is no Terraform code to copy.",
                "error"
            );
            return;
        }

        try {
            await navigator.clipboard.writeText(currentTerraform);
            showMessage(
                elements.terraformMessage,
                "Terraform code copied to clipboard.",
                "success"
            );
        } catch {
            // Fallback for environments where the Clipboard API is unavailable.
            const textarea = document.createElement("textarea");
            textarea.value = currentTerraform;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.select();

            const copied = document.execCommand("copy");
            textarea.remove();

            showMessage(
                elements.terraformMessage,
                copied
                    ? "Terraform code copied to clipboard."
                    : "Copy failed. Select and copy the code manually.",
                copied ? "success" : "error"
            );
        }
    });

    elements.resetButton?.addEventListener("click", () => {
        form.reset();

        currentPlan = null;
        currentTerraform = "";

        elements.results.hidden = true;
        elements.empty.hidden = false;

        elements.terraformResults.hidden = true;
        elements.terraformEmpty.hidden = false;

        elements.publicList.replaceChildren();
        elements.privateList.replaceChildren();
        elements.terraformCode.textContent = "";

        $("stat-network").textContent = "Not configured";
        $("stat-subnets").textContent = "0";
        $("stat-hosts").textContent = "0";
        $("stat-scan-status").textContent = "Not run";

        hideMessage(elements.message);
        hideMessage(elements.terraformMessage);
    });
});
