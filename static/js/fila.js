/* Processa a fila de enriquecimento ReceitaWS respeitando 3 consultas/min. */
(function () {
  "use strict";
  const btn = document.getElementById("btn-fila");
  if (!btn) return;

  const url = btn.dataset.url;
  const log = document.getElementById("fila-log");
  const barra = document.getElementById("fila-barra");
  const restanteEl = document.getElementById("fila-restante");
  const total = parseInt(btn.dataset.total || "0", 10);
  let rodando = false;

  function escreve(txt, cls) {
    if (!log) return;
    const linha = document.createElement("div");
    linha.className = "fila-item " + (cls || "");
    linha.textContent = txt;
    log.prepend(linha);
  }

  function atualizaBarra(restantes) {
    if (restanteEl) restanteEl.textContent = restantes;
    if (barra && total > 0) {
      const feito = Math.max(0, total - restantes);
      barra.style.width = Math.round((feito / total) * 100) + "%";
    }
  }

  async function rodada() {
    const resp = await window.postJSON(url, {});
    const data = await resp.json();
    (data.processadas || []).forEach((e) =>
      escreve(`✓ ${e.id_sistema} — ${e.razao_social || "sem razão social"}`, "ok")
    );
    (data.erros || []).forEach((e) =>
      escreve(`✗ ${e.id_sistema}: ${e.mensagem}`, "erro")
    );
    atualizaBarra(data.restantes);

    if (data.restantes > 0) {
      const espera = Math.max(data.espera || 1, 1);
      escreve(`Aguardando ${espera}s para respeitar o limite (3/min)…`, "info");
      btn.textContent = `Aguardando ${espera}s…`;
      let restante = espera;
      const timer = setInterval(() => {
        restante -= 1;
        btn.textContent = restante > 0 ? `Aguardando ${restante}s…` : "Processando…";
        if (restante <= 0) clearInterval(timer);
      }, 1000);
      setTimeout(rodada, espera * 1000);
    } else {
      escreve("Fila concluída! 🎉", "ok");
      btn.textContent = "Fila concluída";
      btn.disabled = true;
      setTimeout(() => window.location.reload(), 1500);
    }
  }

  btn.addEventListener("click", () => {
    if (rodando) return;
    rodando = true;
    btn.disabled = true;
    btn.textContent = "Processando…";
    escreve("Iniciando processamento da fila…", "info");
    rodada();
  });
})();
