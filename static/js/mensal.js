/* Atualiza o status das execuções mensais inline, sem recarregar a página. */
(function () {
  "use strict";
  const cores = {
    PENDENTE: "#64748b",
    ANDAMENTO: "#2563eb",
    CONCLUIDA: "#16a34a",
    ATRASADA: "#dc2626",
    DISPENSADA: "#94a3b8",
  };

  function pinta(sel) {
    sel.style.color = cores[sel.value] || "#1b2438";
    sel.style.borderColor = (cores[sel.value] || "#cbd5e1") + "66";
  }

  document.querySelectorAll(".status-select[data-url]").forEach((sel) => {
    pinta(sel);
    sel.addEventListener("change", async () => {
      const original = sel.dataset.atual;
      sel.disabled = true;
      try {
        const resp = await window.postJSON(sel.dataset.url, { status: sel.value });
        const data = await resp.json();
        if (data.ok) {
          sel.dataset.atual = sel.value;
          pinta(sel);
          const respCell = document.getElementById("resp-" + sel.dataset.id);
          if (respCell && data.responsavel) respCell.textContent = data.responsavel;
        } else {
          sel.value = original;
          alert(data.mensagem || "Não foi possível atualizar.");
        }
      } catch (e) {
        sel.value = original;
        alert("Erro de conexão.");
      } finally {
        sel.disabled = false;
      }
    });
  });
})();
