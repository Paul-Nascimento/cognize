/* Cognize — utilidades de frontend (sem framework) */
(function () {
  "use strict";

  // CSRF para requisições AJAX
  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }
  window.CSRF = getCookie("csrftoken");

  window.postJSON = function (url, data) {
    const body = new URLSearchParams(data || {});
    return fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": window.CSRF,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
    });
  };

  // Menu lateral (mobile)
  const toggle = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  }

  // Auto-dismiss de mensagens
  document.querySelectorAll(".messages .msg").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 6000);
  });

  // Confirmação de exclusão
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
})();
