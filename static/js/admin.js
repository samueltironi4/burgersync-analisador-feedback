/* ==========================================================================
   BurgerSync Ourinhos - Admin Dashboard Logic
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // Elementos de UI
  const kpiTotal = document.getElementById("kpiTotal");
  const kpiPositivos = document.getElementById("kpiPositivos");
  const kpiNeutros = document.getElementById("kpiNeutros");
  const kpiCriticos = document.getElementById("kpiCriticos");
  const kpiPendentes = document.getElementById("kpiPendentes");
  const kpiRating = document.getElementById("kpiRating");

  const crisisBanner = document.getElementById("crisisBanner");
  const filterCriticalPendingBtn = document.getElementById("filterCriticalPendingBtn");

  const searchInput = document.getElementById("searchInput");
  const filterSentimento = document.getElementById("filterSentimento");
  const filterStatus = document.getElementById("filterStatus");
  const filterTag = document.getElementById("filterTag");
  const filterSort = document.getElementById("filterSort");

  const feedbacksBody = document.getElementById("feedbacksBody");
  const emptyState = document.getElementById("emptyState");
  const resultsCount = document.getElementById("resultsCount");
  const refreshBtn = document.getElementById("refreshBtn");
  const exportBtn = document.getElementById("exportBtn");

  const detailModal = document.getElementById("detailModal");
  const detailModalContent = document.getElementById("detailModalContent");
  const closeDetailModalBtn = document.getElementById("closeDetailModalBtn");

  let currentFeedbacks = [];

  // Inicialização
  loadDashboardData();

  // Listeners de Filtro
  let searchTimeout = null;
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(fetchFeedbacks, 250);
  });

  filterSentimento.addEventListener("change", fetchFeedbacks);
  filterStatus.addEventListener("change", fetchFeedbacks);
  filterTag.addEventListener("change", fetchFeedbacks);
  filterSort.addEventListener("change", fetchFeedbacks);

  refreshBtn.addEventListener("click", () => {
    loadDashboardData();
  });

  exportBtn.addEventListener("click", exportToJson);

  filterCriticalPendingBtn.addEventListener("click", () => {
    filterSentimento.value = "Crítico";
    filterStatus.value = "Pendente";
    fetchFeedbacks();
    window.scrollTo({ top: 380, behavior: "smooth" });
  });

  // Funções de Carga
  async function loadDashboardData() {
    await Promise.all([fetchStats(), fetchFeedbacks()]);
  }

  async function fetchStats() {
    try {
      const res = await fetch("/api/stats");
      const data = await res.json();
      if (res.ok && data.success) {
        const s = data.stats;
        kpiTotal.textContent = s.total;
        kpiPositivos.textContent = s.positivos;
        kpiNeutros.textContent = s.neutros;
        kpiCriticos.textContent = s.criticos;
        kpiPendentes.textContent = s.pendentes;
        kpiRating.textContent = s.media_nota ? s.media_nota.toFixed(1) : "5.0";

        // Verifica crise pendente
        checkCrisisAlert(s);
      }
    } catch (err) {
      console.error("Erro ao carregar estatísticas:", err);
    }
  }

  function checkCrisisAlert(stats) {
    // Alerta ativo se houver ao menos 1 feedback crítico pendente
    const hasCriticalPending = currentFeedbacks.some(
      (f) => f.sentimento === "Crítico" && f.status === "Pendente"
    );
    crisisBanner.style.display = hasCriticalPending ? "block" : "none";
  }

  async function fetchFeedbacks() {
    const params = new URLSearchParams({
      sentimento: filterSentimento.value,
      status: filterStatus.value,
      tag: filterTag.value,
      sort: filterSort.value,
      search: searchInput.value.trim()
    });

    try {
      const res = await fetch(`/api/feedbacks?${params.toString()}`);
      const data = await res.json();
      if (res.ok && data.success) {
        currentFeedbacks = data.feedbacks;
        renderFeedbacks(currentFeedbacks);
        resultsCount.textContent = currentFeedbacks.length;

        // Atualiza verificação de banner com base na lista
        const hasCriticalPending = currentFeedbacks.some(
          (f) => f.sentimento === "Crítico" && f.status === "Pendente"
        );
        crisisBanner.style.display = hasCriticalPending ? "block" : "none";
      }
    } catch (err) {
      console.error("Erro ao carregar feedbacks:", err);
    }
  }

  function renderFeedbacks(items) {
    feedbacksBody.innerHTML = "";

    if (!items || items.length === 0) {
      emptyState.style.display = "block";
      return;
    }
    emptyState.style.display = "none";

    items.forEach((item) => {
      const tr = document.createElement("tr");
      if (item.sentimento === "Crítico" && item.status === "Pendente") {
        tr.classList.add("row-critical");
      }

      // Checkbox de status
      const isTratado = item.status === "Tratado";
      const statusBadgeClass = isTratado ? "badge-tratado" : "badge-pendente";
      const sentimentoBadgeClass = `badge-${(item.sentimento || "neutro").toLowerCase()}`;

      // Estrelas
      const starsDisplay = "⭐".repeat(Math.max(1, Math.min(5, item.nota || 5)));

      // Tags
      const tagsHtml = (item.tags || [])
        .map((t) => `<span class="tag-chip">${escapeHtml(t)}</span>`)
        .join(" ");

      tr.innerHTML = `
        <td>
          <div class="status-toggle-wrapper" title="Clique para alternar status (Pendente / Tratado)">
            <input type="checkbox" class="status-checkbox" data-id="${item.id}" ${isTratado ? "checked" : ""}>
          </div>
        </td>
        <td style="white-space: nowrap; color: var(--text-dim); font-size: 12px;">${escapeHtml(item.timestamp || "")}</td>
        <td><strong>#${escapeHtml(item.pedido_id || "S/N")}</strong></td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(item.nome || "Anônimo")}</div>
          <div style="font-size: 11px; color: var(--text-dim);">${escapeHtml(item.contato || "")}</div>
        </td>
        <td style="white-space: nowrap;" title="Nota: ${item.nota}/5">${starsDisplay}</td>
        <td>
          <span class="badge ${sentimentoBadgeClass}">${escapeHtml(item.sentimento || "Neutro")}</span>
        </td>
        <td>
          <div class="tags-container">${tagsHtml}</div>
        </td>
        <td>
          <div style="font-weight: 600; color: #fff; margin-bottom: 2px;">${escapeHtml(item.resumo || "")}</div>
          <div style="color: var(--text-muted); font-size: 12px; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            "${escapeHtml(item.comentario || "")}"
          </div>
        </td>
        <td>
          <button class="btn-tool btn-view-detail" data-id="${item.id}" style="padding: 4px 8px; font-size: 11px;">🔍 Detalhes</button>
        </td>
      `;

      feedbacksBody.appendChild(tr);
    });

    // Listeners nos checkboxes
    feedbacksBody.querySelectorAll(".status-checkbox").forEach((cb) => {
      cb.addEventListener("change", async (e) => {
        const id = e.target.getAttribute("data-id");
        const newStatus = e.target.checked ? "Tratado" : "Pendente";
        await updateStatus(id, newStatus);
      });
    });

    // Listeners no botão de detalhes
    feedbacksBody.querySelectorAll(".btn-view-detail").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const id = e.target.getAttribute("data-id");
        const found = currentFeedbacks.find((f) => f.id === id);
        if (found) {
          showDetailModal(found);
        }
      });
    });
  }

  async function updateStatus(id, newStatus) {
    try {
      const res = await fetch(`/api/feedback/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        // Atualiza estatísticas e interface
        await fetchStats();
        // Atualiza item em memória
        const item = currentFeedbacks.find((f) => f.id === id);
        if (item) {
          item.status = newStatus;
        }
      } else {
        alert("Erro ao atualizar status.");
        fetchFeedbacks();
      }
    } catch (err) {
      console.error("Erro na atualização de status:", err);
      fetchFeedbacks();
    }
  }

  function showDetailModal(item) {
    const isCritical = item.sentimento === "Crítico";
    const tagsHtml = (item.tags || []).map((t) => `<span class="tag-chip">${escapeHtml(t)}</span>`).join(" ");

    detailModalContent.innerHTML = `
      <table class="detail-table">
        <tr>
          <td>Status:</td>
          <td>
            <span class="badge ${item.status === 'Tratado' ? 'badge-tratado' : 'badge-pendente'}">${escapeHtml(item.status)}</span>
          </td>
        </tr>
        <tr>
          <td>Data/Hora:</td>
          <td>${escapeHtml(item.timestamp || "")}</td>
        </tr>
        <tr>
          <td>Pedido ID:</td>
          <td><strong>#${escapeHtml(item.pedido_id || "S/N")}</strong></td>
        </tr>
        <tr>
          <td>Cliente:</td>
          <td><strong>${escapeHtml(item.nome || "Anônimo")}</strong></td>
        </tr>
        <tr>
          <td>Contato:</td>
          <td>${escapeHtml(item.contato || "Não informado")}</td>
        </tr>
        <tr>
          <td>Nota:</td>
          <td>⭐ ${item.nota}/5</td>
        </tr>
        <tr>
          <td>Sentimento IA:</td>
          <td>
            <span class="badge badge-${(item.sentimento || '').toLowerCase()}">${escapeHtml(item.sentimento)}</span>
            <span style="font-size: 11px; color: var(--text-dim); margin-left: 8px;">(Origem: ${escapeHtml(item.origem_analise || "local")})</span>
          </td>
        </tr>
        <tr>
          <td>Tópicos (Tags):</td>
          <td>${tagsHtml}</td>
        </tr>
        <tr>
          <td>Diagnóstico IA:</td>
          <td style="color: #f59e0b; font-weight: 600;">${escapeHtml(item.resumo || "")}</td>
        </tr>
        <tr>
          <td>Alerta Crítico:</td>
          <td>${item.alerta_disparado ? '<span style="color:#ef4444; font-weight:bold;">🚨 Disparado via Notifier</span>' : '<span style="color:#10b981;">Não necessário</span>'}</td>
        </tr>
      </table>

      <div class="comment-quote">
        "${escapeHtml(item.comentario || "")}"
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
        <button id="toggleModalStatusBtn" class="btn-tool btn-tool-accent">
          ${item.status === "Pendente" ? "Marcar como Tratado ✅" : "Reabrir como Pendente ⏳"}
        </button>
      </div>
    `;

    document.getElementById("toggleModalStatusBtn").addEventListener("click", async () => {
      const newStatus = item.status === "Pendente" ? "Tratado" : "Pendente";
      await updateStatus(item.id, newStatus);
      detailModal.style.display = "none";
      await fetchFeedbacks();
    });

    detailModal.style.display = "flex";
  }

  closeDetailModalBtn.addEventListener("click", () => {
    detailModal.style.display = "none";
  });

  detailModal.addEventListener("click", (e) => {
    if (e.target === detailModal) {
      detailModal.style.display = "none";
    }
  });

  function exportToJson() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentFeedbacks, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `burgersync_feedbacks_${new Date().toISOString().slice(0,10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Atualização periódica a cada 30 segundos
  setInterval(() => {
    loadDashboardData();
  }, 30000);
});
