/**
 * NetArchitect Frontend Controller (Distilled Operate-Mode UI).
 */

let currentPlan = null;
let activePresetId = "campus-lan";
let activeDeviceFilter = "ALL";

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initTabs();
  initActions();
  initCustomBuilder();
  loadPreset(activePresetId);
});

function initNavigation() {
  const sidebar = document.getElementById("sidebar");
  const openBtn = document.getElementById("openSidebarBtn");
  const closeBtn = document.getElementById("closeSidebarBtn");

  openBtn.addEventListener("click", () => sidebar.classList.add("open"));
  closeBtn.addEventListener("click", () => sidebar.classList.remove("open"));

  // Preset sidebar navigation
  const presetNavBtns = document.querySelectorAll("#presetNav .nav-item");
  const customNavBtn = document.getElementById("openCustomTabBtn");

  presetNavBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      presetNavBtns.forEach(b => b.classList.remove("active"));
      customNavBtn.classList.remove("active");
      btn.classList.add("active");
      activePresetId = btn.dataset.id;
      sidebar.classList.remove("open");
      switchTab("overview");
      loadPreset(activePresetId);
    });
  });

  customNavBtn.addEventListener("click", () => {
    presetNavBtns.forEach(b => b.classList.remove("active"));
    customNavBtn.classList.add("active");
    sidebar.classList.remove("open");
    switchTab("custom");
  });
}

function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      switchTab(btn.dataset.tab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-pane").forEach(p => {
    p.classList.toggle("active", p.id === `pane-${tabId}`);
  });
}

function initActions() {
  // Header quick copy
  const quickCopyBtn = document.getElementById("quickCopyCfgBtn");
  quickCopyBtn.addEventListener("click", () => {
    if (!currentPlan) return;
    copyTextWithFeedback(currentPlan.unified_cisco_config, quickCopyBtn.querySelector("span"), "Copy IOS Config");
  });

  // Config tab copy current view
  const copyDeviceBtn = document.getElementById("copyDeviceCfgBtn");
  copyDeviceBtn.addEventListener("click", () => {
    const codeText = document.getElementById("ciscoConfigCode").innerText;
    copyTextWithFeedback(codeText, copyDeviceBtn, "Copy Current View");
  });

  // Download .cfg
  document.getElementById("quickDownloadCfgBtn").addEventListener("click", () => {
    if (!currentPlan) return;
    downloadFile(
      currentPlan.unified_cisco_config,
      `${currentPlan.scenario_id}_cisco.cfg`,
      "text/plain;charset=utf-8"
    );
  });

  // Download .csv
  document.getElementById("downloadCsvBtn").addEventListener("click", () => {
    if (!currentPlan) return;
    const headers = [
      "Subnet Name", "VLAN ID", "Security Zone", "Required Hosts", "Allocated Hosts",
      "CIDR", "Network Address", "Netmask", "Wildcard Mask", "Default Gateway",
      "First Usable", "Last Usable", "Broadcast", "Efficiency %"
    ];
    const rows = currentPlan.subnet_allocations.map(s => [
      s.name, s.vlan_id, s.security_zone, s.required_hosts, s.allocated_hosts,
      s.cidr, s.network_address, s.netmask, s.wildcard_mask, s.default_gateway,
      s.first_usable_ip, s.last_usable_ip, s.broadcast_address, `${s.efficiency_pct}%`
    ]);
    const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    downloadFile(csvContent, `${currentPlan.scenario_id}_subnets.csv`, "text/csv;charset=utf-8");
  });

  // Dismiss error alert
  document.getElementById("closeErrorBtn").addEventListener("click", hideError);

  // Command chips click-to-copy
  document.querySelectorAll(".cmd-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const original = chip.innerText;
      copyTextWithFeedback(original, chip, original);
    });
  });
}

function initCustomBuilder() {
  loadCustomTemplate("valid");

  const editor = document.getElementById("customJsonInput");
  const statusHint = document.getElementById("jsonSyntaxStatus");
  const runBtn = document.getElementById("executeCustomPlanBtn");

  const validateSyntaxLive = () => {
    const raw = editor.value.trim();
    if (!raw) {
      statusHint.innerText = "Editor is empty — paste JSON or load a template";
      statusHint.className = "editor-hint invalid";
      return false;
    }
    try {
      JSON.parse(raw);
      statusHint.innerText = "Valid JSON syntax · Ready to run";
      statusHint.className = "editor-hint valid";
      return true;
    } catch (err) {
      statusHint.innerText = `JSON Syntax Error: ${err.message}`;
      statusHint.className = "editor-hint invalid";
      return false;
    }
  };

  editor.addEventListener("input", validateSyntaxLive);

  document.getElementById("loadActivePresetBtn").addEventListener("click", async () => {
    hideError();
    try {
      const res = await fetch(`/api/presets/${activePresetId}/input`);
      if (!res.ok) throw new Error("Failed to load preset schema.");
      const data = await res.json();
      editor.value = JSON.stringify(data, null, 2);
      validateSyntaxLive();
    } catch (err) {
      showError("Preset Load Error", err.message);
    }
  });

  document.getElementById("loadTemplateValidBtn").addEventListener("click", () => {
    loadCustomTemplate("valid");
    validateSyntaxLive();
  });
  document.getElementById("loadTemplateCopperErrBtn").addEventListener("click", () => {
    loadCustomTemplate("copper_error");
    validateSyntaxLive();
  });
  document.getElementById("loadTemplateExhaustErrBtn").addEventListener("click", () => {
    loadCustomTemplate("exhaust_error");
    validateSyntaxLive();
  });

  document.getElementById("formatJsonBtn").addEventListener("click", () => {
    try {
      const parsed = JSON.parse(editor.value);
      editor.value = JSON.stringify(parsed, null, 2);
      validateSyntaxLive();
    } catch (err) {
      validateSyntaxLive();
      showError("Invalid JSON Syntax", err.message);
    }
  });

  runBtn.addEventListener("click", async () => {
    const raw = editor.value;
    let payload;
    try {
      payload = JSON.parse(raw);
    } catch (err) {
      validateSyntaxLive();
      showError("Invalid JSON Syntax", err.message);
      return;
    }

    runBtn.disabled = true;
    const originalText = runBtn.innerText;
    runBtn.innerText = "Evaluating Plan...";
    try {
      await executeCustomScenario(payload);
    } finally {
      runBtn.disabled = false;
      runBtn.innerText = originalText;
    }
  });
}

async function loadPreset(presetId) {
  hideError();
  try {
    const res = await fetch(`/api/presets/${presetId}`);
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(formatApiError(errData.detail) || "Unable to evaluate preset.");
    }
    const plan = await res.json();
    currentPlan = plan;
    activeDeviceFilter = "ALL";
    renderPlan(plan);
  } catch (err) {
    showError("Preset Loading Error", err.message);
  }
}

async function executeCustomScenario(payload) {
  hideError();
  try {
    const res = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const contentType = res.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const errData = await res.json();
        const detail = errData.detail;
        if (detail && typeof detail === "object" && !Array.isArray(detail) && detail.error_type) {
          showError(detail.error_type, detail.message);
          return;
        }
        showError("Scenario Validation Error", formatApiError(detail));
        return;
      }
      const textErr = await res.text();
      throw new Error(textErr || `HTTP ${res.status}`);
    }

    const plan = await res.json();
    currentPlan = plan;
    activeDeviceFilter = "ALL";
    renderPlan(plan);
    switchTab("overview");
  } catch (err) {
    showError("Scenario Planning Error", err.message);
  }
}

function formatApiError(detail) {
  if (!detail) return "Validation failed.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        const path = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "input";
        return `${path ? path + ": " : ""}${item.msg}`;
      })
      .join(" | ");
  }
  if (typeof detail === "object") {
    return detail.message || JSON.stringify(detail);
  }
  return String(detail);
}

function renderPlan(plan) {
  // Header & Sidebar Telemetry
  document.getElementById("scenarioTitle").innerText = plan.scenario_name;
  document.getElementById("scenarioMeta").innerText =
    `${plan.root_network} · ${plan.subnet_allocations.length} subnets · ${plan.media_recommendations.length} physical links`;

  document.getElementById("sideRootNet").innerText = plan.root_network;
  document.getElementById("sideEfficiency").innerText = `${plan.overall_efficiency_pct}%`;
  document.getElementById("sideHosts").innerText = plan.total_usable_hosts.toLocaleString();
  document.getElementById("sideAsn").innerText = `AS ${plan.routing_recommendation.autonomous_system}`;

  // Tab Counts
  document.getElementById("tabSubnetCount").innerText = plan.subnet_allocations.length;
  document.getElementById("tabLinkCount").innerText = plan.media_recommendations.length;

  // Overview KPI Strip
  const r = plan.routing_recommendation;
  document.getElementById("ovRoutingProto").innerText = r.protocol;
  document.getElementById("ovRfc").innerText = r.rfc_citation;
  document.getElementById("ovConvergence").innerText = r.convergence_profile;
  document.getElementById("ovTier").innerText = r.topology_tier;
  document.getElementById("ovEfficiency").innerText = `${plan.overall_efficiency_pct}%`;
  document.getElementById("ovTotalIps").innerText =
    `${plan.total_allocated_ips.toLocaleString()} reserved of ${plan.total_available_ips.toLocaleString()} total`;

  // Executive Rationales
  const rationaleContainer = document.getElementById("rationaleList");
  rationaleContainer.innerHTML = "";
  plan.executive_rationales.forEach(item => {
    const colonIdx = item.indexOf(":");
    const heading = colonIdx > 0 ? item.slice(0, colonIdx) : "Architectural Note";
    const body = colonIdx > 0 ? item.slice(colonIdx + 1).trim() : item;

    const row = document.createElement("div");
    row.className = "rationale-row";
    row.innerHTML = `
      <div class="rationale-heading">${escapeHtml(heading)}</div>
      <div class="rationale-text">${escapeHtml(body)}</div>
    `;
    rationaleContainer.appendChild(row);
  });

  document.getElementById("routingRationaleText").innerText = r.rationale;

  // Subnets Table
  const vlsmBody = document.querySelector("#vlsmTable tbody");
  vlsmBody.innerHTML = "";
  plan.subnet_allocations.forEach(s => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="cell-strong">${escapeHtml(s.name)}</td>
      <td><span class="pill font-mono">VLAN ${s.vlan_id}</span></td>
      <td class="font-mono cell-accent">${escapeHtml(s.cidr)}</td>
      <td class="font-mono">${escapeHtml(s.default_gateway)}</td>
      <td class="font-mono">${escapeHtml(s.first_usable_ip)} – ${escapeHtml(s.last_usable_ip)}</td>
      <td class="font-mono">${escapeHtml(s.wildcard_mask)}</td>
      <td class="text-right font-mono">${s.efficiency_pct}%</td>
    `;
    vlsmBody.appendChild(tr);
  });

  // Media Physics Table
  const mediaBody = document.querySelector("#mediaTable tbody");
  mediaBody.innerHTML = "";
  plan.media_recommendations.forEach(m => {
    const distLabel = m.distance_meters < 1000
      ? `${m.distance_meters.toFixed(0)} m`
      : `${(m.distance_meters / 1000).toFixed(1)} km`;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="font-mono cell-strong">${escapeHtml(m.link_id)}</td>
      <td>${escapeHtml(m.source)} &rarr; ${escapeHtml(m.destination)}</td>
      <td class="font-mono">${distLabel}</td>
      <td class="cell-strong">${escapeHtml(m.medium_type)}</td>
      <td><span class="pill font-mono">${escapeHtml(m.standard)}</span></td>
      <td class="font-mono">${m.attenuation_db_est} dB</td>
      <td style="max-width: 340px;">${escapeHtml(m.rationale)}</td>
    `;
    mediaBody.appendChild(tr);
  });

  // Cisco Device Filter Pills & Config Viewer
  renderDeviceFilters(plan);
  renderCiscoCode(plan);
}

function renderDeviceFilters(plan) {
  const bar = document.getElementById("deviceFilterBar");
  bar.innerHTML = "";

  const allPill = document.createElement("button");
  allPill.className = `filter-pill ${activeDeviceFilter === "ALL" ? "active" : ""}`;
  allPill.innerText = "All Devices";
  allPill.addEventListener("click", () => {
    activeDeviceFilter = "ALL";
    renderDeviceFilters(plan);
    renderCiscoCode(plan);
  });
  bar.appendChild(allPill);

  plan.device_configs.forEach(dev => {
    const pill = document.createElement("button");
    pill.className = `filter-pill ${activeDeviceFilter === dev.device_role ? "active" : ""}`;
    pill.innerText = `${dev.device_role} (${dev.hostname})`;
    pill.addEventListener("click", () => {
      activeDeviceFilter = dev.device_role;
      renderDeviceFilters(plan);
      renderCiscoCode(plan);
    });
    bar.appendChild(pill);
  });
}

function renderCiscoCode(plan) {
  const codeEl = document.getElementById("ciscoConfigCode");
  if (activeDeviceFilter === "ALL") {
    codeEl.innerText = plan.unified_cisco_config;
  } else {
    const dev = plan.device_configs.find(d => d.device_role === activeDeviceFilter);
    codeEl.innerText = dev ? dev.config_text : plan.unified_cisco_config;
  }
}

function showError(title, message) {
  document.getElementById("errorTitle").innerText = title;
  document.getElementById("errorMessage").innerText = message;
  document.getElementById("errorBanner").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function hideError() {
  document.getElementById("errorBanner").classList.add("hidden");
}

async function copyTextWithFeedback(text, labelEl, originalLabel) {
  try {
    await navigator.clipboard.writeText(text);
    labelEl.innerText = "Copied";
    setTimeout(() => {
      labelEl.innerText = originalLabel;
    }, 1600);
  } catch (err) {
    console.error("Copy failed:", err);
  }
}

function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function loadCustomTemplate(kind) {
  const templates = {
    valid: {
      id: "custom-datacenter",
      name: "Custom Enterprise Datacenter",
      description: "Compute cluster and remote DR optical span",
      root_network: "192.168.0.0/20",
      resiliency_mode: "DUAL_HOMED_RSTP",
      autonomous_system_number: 65100,
      links: [
        {
          link_id: "LINK-POD-A",
          source: "DC-Core",
          destination: "Compute-Pod-A",
          distance_meters: 75.0,
          bandwidth_gbps: 10.0,
          medium_preference: "AUTO",
          role: "Access"
        },
        {
          link_id: "LINK-DR-METRO",
          source: "DC-Core",
          destination: "DR-Facility",
          distance_meters: 22500.0,
          bandwidth_gbps: 10.0,
          medium_preference: "FIBER",
          role: "Metro"
        }
      ],
      subnets: [
        { name: "K8s_Worker_Pool", required_hosts: 400, vlan_id: 101, security_zone: "INTERNAL" },
        { name: "Database_Cluster", required_hosts: 120, vlan_id: 102, security_zone: "INTERNAL" },
        { name: "DMZ_Edge_Ingress", required_hosts: 60, vlan_id: 103, security_zone: "DMZ" }
      ]
    },
    copper_error: {
      id: "illegal-copper-test",
      name: "Boundary Test: Copper > 100m",
      description: "Demonstrates PhysicalDistanceViolationError enforcement",
      root_network: "10.0.0.0/24",
      resiliency_mode: "SINGLE_HOMED",
      autonomous_system_number: 65010,
      links: [
        {
          link_id: "LINK-ILLEGAL-RUN",
          source: "Building-A",
          destination: "Building-B",
          distance_meters: 160.0,
          bandwidth_gbps: 10.0,
          medium_preference: "COPPER",
          role: "Access"
        }
      ],
      subnets: [
        { name: "Workstations", required_hosts: 50, vlan_id: 10, security_zone: "INTERNAL" }
      ]
    },
    exhaust_error: {
      id: "exhaustion-test",
      name: "Boundary Test: IP Exhaustion",
      description: "Demonstrates AddressSpaceExhaustionError enforcement",
      root_network: "192.168.10.0/24",
      resiliency_mode: "SINGLE_HOMED",
      autonomous_system_number: 65020,
      links: [
        {
          link_id: "LINK-LOCAL",
          source: "Core",
          destination: "Access",
          distance_meters: 30.0,
          bandwidth_gbps: 10.0,
          medium_preference: "AUTO",
          role: "Access"
        }
      ],
      subnets: [
        { name: "Oversized_Corp", required_hosts: 200, vlan_id: 10, security_zone: "INTERNAL" },
        { name: "Oversized_Lab", required_hosts: 120, vlan_id: 20, security_zone: "INTERNAL" }
      ]
    }
  };

  document.getElementById("customJsonInput").value = JSON.stringify(templates[kind], null, 2);
}
