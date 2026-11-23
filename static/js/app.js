/* ==========================================================================
   BurgerSync Ourinhos - Client Feedback Form Logic
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("feedbackForm");
  const submitBtn = document.getElementById("submitBtn");
  const btnText = submitBtn.querySelector(".btn-text");
  const btnSpinner = submitBtn.querySelector(".btn-spinner");
  const starContainer = document.getElementById("starRating");
  const notaInput = document.getElementById("nota");
  const resultModal = document.getElementById("resultModal");
  const closeModalBtn = document.getElementById("closeModalBtn");

  // Controle de Estrelas
  const stars = starContainer.querySelectorAll(".star");
  stars.forEach((star) => {
    star.addEventListener("click", () => {
      const val = parseInt(star.getAttribute("data-value"), 10);
      notaInput.value = val;
      updateStars(val);
    });
  });

  function updateStars(val) {
    stars.forEach((star) => {
      const starVal = parseInt(star.getAttribute("data-value"), 10);
      if (starVal <= val) {
        star.classList.add("active");
      } else {
        star.classList.remove("active");
      }
    });
  }

  // Envio do Formulário
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      nome: document.getElementById("nome").value.trim(),
      contato: document.getElementById("contato").value.trim(),
      pedido_id: document.getElementById("pedido_id").value.trim(),
      nota: parseInt(notaInput.value, 10) || 5,
      comentario: document.getElementById("comentario").value.trim()
    };

    if (!payload.comentario) {
      alert("Por favor, preencha o seu comentário sobre a experiência.");
      return;
    }

    // Estado de carregamento
    submitBtn.disabled = true;
    btnText.style.display = "none";
    btnSpinner.style.display = "inline";

    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showResultModal(result.feedback);
        form.reset();
        notaInput.value = "5";
        updateStars(5);
      } else {
        alert(result.error || "Ocorreu um erro ao processar seu feedback. Tente novamente.");
      }
    } catch (err) {
      console.error("Erro na requisição:", err);
      alert("Erro ao conectar ao servidor. Verifique se o backend está em execução.");
    } finally {
      submitBtn.disabled = false;
      btnText.style.display = "inline";
      btnSpinner.style.display = "none";
    }
  });

  function showResultModal(feedback) {
    const resSentimento = document.getElementById("resSentimento");
    const resTags = document.getElementById("resTags");
    const resResumo = document.getElementById("resResumo");
    const modalIcon = document.getElementById("modalIcon");
    const modalTitle = document.getElementById("modalTitle");

    resSentimento.textContent = feedback.sentimento;
    resSentimento.className = `badge badge-${feedback.sentimento.toLowerCase()}`;

    if (feedback.sentimento === "Positivo") {
      modalIcon.textContent = "⭐";
      modalTitle.textContent = "Muito Obrigado pelo Elogio!";
    } else if (feedback.sentimento === "Crítico") {
      modalIcon.textContent = "🚨";
      modalTitle.textContent = "Sentimos Muito Pelo Ocorrido!";
    } else {
      modalIcon.textContent = "🍔";
      modalTitle.textContent = "Agradecemos sua Avaliação!";
    }

    resTags.innerHTML = "";
    (feedback.tags || []).forEach((t) => {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = t;
      resTags.appendChild(chip);
    });

    resResumo.textContent = feedback.resumo || "Diagnóstico registrado pela IA.";
    resultModal.style.display = "flex";
  }

  closeModalBtn.addEventListener("click", () => {
    resultModal.style.display = "none";
  });

  resultModal.addEventListener("click", (e) => {
    if (e.target === resultModal) {
      resultModal.style.display = "none";
    }
  });
});
