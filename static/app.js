const state = {
  target: "all",
  status: "all",
};

const fmtInt = new Intl.NumberFormat("fr-FR");
const fmtPct = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

async function loadDashboard() {
  const query = new URLSearchParams(state);
  const response = await fetch(`/api/dashboard?${query.toString()}`);
  const data = await response.json();
  renderFilters(data);
  renderKpis(data.kpis);
  renderTemplates(data.template_summary);
  renderCampaigns(data.campaigns);
}

function renderFilters(data) {
  hydrateSelect(
    document.querySelector("#targetFilter"),
    ["all", ...data.targets],
    state.target
  );
  hydrateSelect(
    document.querySelector("#statusFilter"),
    data.statuses,
    state.status
  );
}

function hydrateSelect(select, values, currentValue) {
  const options = values
    .map(
      (value) =>
        `<option value="${value}" ${
          value === currentValue ? "selected" : ""
        }>${value === "all" ? "Toutes" : value}</option>`
    )
    .join("");
  select.innerHTML = options;
}

function renderKpis(kpis) {
  const items = [
    ["Campagnes", kpis.campaign_count],
    ["Emails envoyes", fmtInt.format(kpis.total_sent)],
    ["Deliverability", `${fmtPct.format(kpis.delivery_rate)} %`],
    ["Open rate", `${fmtPct.format(kpis.open_rate)} %`],
    ["Click rate", `${fmtPct.format(kpis.click_rate)} %`],
    ["Bounce rate", `${fmtPct.format(kpis.bounce_rate)} %`],
    ["Unsubscribe", `${fmtPct.format(kpis.unsubscribe_rate)} %`],
    ["Cadence moyenne/h", fmtInt.format(kpis.avg_send_per_hour)],
  ];

  document.querySelector("#kpiGrid").innerHTML = items
    .map(
      ([label, value]) => `
        <article class="kpi-card">
          <p>${label}</p>
          <strong>${value}</strong>
        </article>
      `
    )
    .join("");
}

function renderTemplates(templates) {
  if (!templates.length) {
    document.querySelector("#templateList").innerHTML =
      '<p class="empty-state">Aucune donnee disponible pour cette combinaison de filtres.</p>';
    return;
  }

  document.querySelector("#templateList").innerHTML = templates
    .map(
      (template) => `
        <article class="template-card">
          <div class="template-header">
            <div>
              <h3>${template.template}</h3>
              <p>${template.visual_style}</p>
            </div>
            <span>${fmtInt.format(template.sent)} env.</span>
          </div>
          <div class="meter">
            <div class="meter-bar" style="width:${Math.min(
              template.open_rate,
              100
            )}%"></div>
          </div>
          <div class="template-metrics">
            <span>Open ${fmtPct.format(template.open_rate)} %</span>
            <span>Click ${fmtPct.format(template.click_rate)} %</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderCampaigns(campaigns) {
  if (!campaigns.length) {
    document.querySelector("#campaignRows").innerHTML = `
      <tr>
        <td colspan="8" class="empty-row">Aucune campagne ne correspond aux filtres actifs.</td>
      </tr>
    `;
    return;
  }

  document.querySelector("#campaignRows").innerHTML = campaigns
    .map(
      (campaign) => `
        <tr>
          <td>
            <strong>${campaign.name}</strong>
          </td>
          <td>${campaign.target}</td>
          <td>
            <span>${campaign.template}</span>
            <small>${campaign.visual_style}</small>
          </td>
          <td>${fmtInt.format(campaign.send_per_hour)}</td>
          <td>${fmtPct.format(campaign.open_rate)} %</td>
          <td>${fmtPct.format(campaign.click_rate)} %</td>
          <td>${fmtPct.format(campaign.bounce_rate)} %</td>
          <td><span class="status ${campaign.status}">${campaign.status}</span></td>
        </tr>
      `
    )
    .join("");
}

document.querySelector("#targetFilter").addEventListener("change", (event) => {
  state.target = event.target.value;
  loadDashboard();
});

document.querySelector("#statusFilter").addEventListener("change", (event) => {
  state.status = event.target.value;
  loadDashboard();
});

loadDashboard();
