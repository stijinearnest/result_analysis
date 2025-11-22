// static/js/add_student_steps.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("studentForm");
  const stepperSteps = Array.from(document.querySelectorAll(".step"));
  const stepPanels = Array.from(document.querySelectorAll(".step-panel"));
  const btnNext = document.querySelectorAll(".btn-next");
  const btnPrev = document.querySelectorAll(".btn-prev");
  const photoUpload = document.getElementById("photoUpload");
  const photoInput = document.getElementById("photo");
  const photoPreview = document.getElementById("photoPreview");

  let currentStep = 1;
  const maxStep = stepPanels.length;

  function showStep(step) {
    currentStep = step;
    stepPanels.forEach(panel => {
      panel.style.display = Number(panel.dataset.step) === step ? "" : "none";
    });
    stepperSteps.forEach(s => {
      s.classList.toggle("active", Number(s.dataset.step) === step);
    });
    // scroll to card top
    const top = document.querySelector(".registration-card").offsetTop - 20;
    window.scrollTo({ top, behavior: "smooth" });
  }

  function validateStep(step) {
    const panel = document.querySelector(`.step-panel[data-step="${step}"]`);
    if (!panel) return true;
    const requiredEls = Array.from(panel.querySelectorAll("[required]"));
    for (const el of requiredEls) {
      if (el.type === "file") continue; // skip file unless you require it
      if (el.disabled) continue;
      if (!el.value || (typeof el.value === "string" && el.value.trim() === "")) {
        el.classList.add("invalid");
        el.focus();
        return false;
      } else {
        el.classList.remove("invalid");
      }
    }
    return true;
  }

  btnNext.forEach(btn => {
    btn.addEventListener("click", () => {
      const next = Number(btn.dataset.next);
      if (!validateStep(currentStep)) return;
      showStep(next);
    });
  });

  btnPrev.forEach(btn => {
    btn.addEventListener("click", () => {
      const prev = Number(btn.dataset.prev);
      showStep(prev);
    });
  });

  // Stepper click: allow going back or forward if previous steps valid
  stepperSteps.forEach(el => {
    el.addEventListener("click", () => {
      const step = Number(el.dataset.step);
      if (step === currentStep) return;
      if (step < currentStep) { showStep(step); return; }
      // moving forward: validate all previous steps
      for (let s = 1; s < step; s++) {
        if (!validateStep(s)) return;
      }
      showStep(step);
    });
  });

  // Form submit: validate current step then allow submit
  if (form) {
    form.addEventListener("submit", (e) => {
      if (!validateStep(currentStep)) {
        e.preventDefault();
        return;
      }
      // optionally disable submit button to prevent double submit
      const submitBtn = form.querySelector(".btn-submit-final, .btn-submit");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.7";
        submitBtn.textContent = "Submitting...";
      }
    });
  }

  // Photo upload interactions
  if (photoUpload && photoInput && photoPreview) {
    photoUpload.addEventListener("click", () => photoInput.click());

    photoUpload.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      photoUpload.classList.add("dragover");
    });
    photoUpload.addEventListener("dragleave", (ev) => {
      ev.preventDefault();
      photoUpload.classList.remove("dragover");
    });
    photoUpload.addEventListener("drop", (ev) => {
      ev.preventDefault();
      photoUpload.classList.remove("dragover");
      const file = ev.dataTransfer.files && ev.dataTransfer.files[0];
      if (file) {
        photoInput.files = ev.dataTransfer.files;
        renderPreview(file);
      }
    });

    photoInput.addEventListener("change", () => {
      const file = photoInput.files[0];
      if (file) renderPreview(file);
    });

    function renderPreview(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        photoPreview.src = e.target.result;
        photoPreview.style.display = "block";
        const uploadContent = photoUpload.querySelector(".upload-content");
        if (uploadContent) uploadContent.style.display = "none";
      };
      reader.readAsDataURL(file);
    }
  }

  // initialize
  showStep(1);
});
// static/js/add_student_steps.js
document.addEventListener("DOMContentLoaded", () => {
  // Stepper + panel setup
  const form = document.getElementById("studentForm");
  const stepperSteps = Array.from(document.querySelectorAll(".step"));
  const stepPanels = Array.from(document.querySelectorAll(".step-panel"));
  const btnNext = document.querySelectorAll(".btn-next");
  const btnPrev = document.querySelectorAll(".btn-prev");
  const photoUpload = document.getElementById("photoUpload");
  const photoInput = document.getElementById("photo");
  const photoPreview = document.getElementById("photoPreview");

  let currentStep = 1;

  function showStep(step) {
    currentStep = step;
    stepPanels.forEach(panel => panel.style.display = Number(panel.dataset.step) === step ? "" : "none");
    stepperSteps.forEach(s => s.classList.toggle("active", Number(s.dataset.step) === step));
    // scroll smoothly to card top
    const card = document.querySelector(".registration-card");
    if (card) window.scrollTo({ top: card.offsetTop - 12, behavior: "smooth" });
  }

  function validateStep(step) {
    const panel = document.querySelector(`.step-panel[data-step="${step}"]`);
    if (!panel) return true;
    const requiredEls = Array.from(panel.querySelectorAll("[required]"));
    for (const el of requiredEls) {
      if (el.type === "file") continue; // skip file validation unless required
      if (el.disabled) continue;
      if (!el.value || (typeof el.value === "string" && el.value.trim() === "")) {
        el.classList.add("invalid");
        el.focus();
        return false;
      } else {
        el.classList.remove("invalid");
      }
    }
    return true;
  }

  // navigation listeners
  btnNext.forEach(btn => btn.addEventListener("click", () => {
    const next = Number(btn.dataset.next);
    if (!validateStep(currentStep)) return;
    showStep(next);
  }));

  btnPrev.forEach(btn => btn.addEventListener("click", () => {
    const prev = Number(btn.dataset.prev);
    showStep(prev);
  }));

  stepperSteps.forEach(el => el.addEventListener("click", () => {
    const step = Number(el.dataset.step);
    if (step === currentStep) return;
    if (step < currentStep) { showStep(step); return; }
    for (let s = 1; s < step; s++) if (!validateStep(s)) return;
    showStep(step);
  }));

  // submit guard
  if (form) {
    form.addEventListener("submit", (e) => {
      if (!validateStep(currentStep)) { e.preventDefault(); return; }
      const submitBtn = form.querySelector(".btn-submit-final, .btn-submit");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.7";
        submitBtn.textContent = "Submitting...";
      }
    });
  }

  // ===== Photo upload logic (click, drag/drop, preview) =====
  if (photoUpload && photoInput && photoPreview) {
    // ensure the hidden input has id 'photo' — your template already does that
    // clicking the big upload area opens file chooser
    photoUpload.style.cursor = "pointer";
    photoUpload.addEventListener("click", (e) => {
      e.preventDefault();
      photoInput.click();
    });

    // drag over / drop
    photoUpload.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      photoUpload.classList.add("dragover");
    });
    photoUpload.addEventListener("dragleave", (ev) => {
      ev.preventDefault();
      photoUpload.classList.remove("dragover");
    });
    photoUpload.addEventListener("drop", (ev) => {
      ev.preventDefault();
      photoUpload.classList.remove("dragover");
      const f = ev.dataTransfer.files && ev.dataTransfer.files[0];
      if (f) {
        photoInput.files = ev.dataTransfer.files; // set file input so form will submit file
        showPreviewFile(f);
      }
    });

    // regular file selection
    photoInput.addEventListener("change", () => {
      const file = photoInput.files[0];
      if (file) showPreviewFile(file);
    });

    function showPreviewFile(file) {
      if (!file) return;
      // basic file size/type checks
      const maxMB = 5;
      if (file.size > maxMB * 1024 * 1024) {
        alert(`Image must be ${maxMB}MB or smaller.`);
        photoInput.value = ""; // reset
        return;
      }
      if (!file.type.startsWith("image/")) {
        alert("Please upload an image (jpg / png).");
        photoInput.value = "";
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        photoPreview.src = e.target.result;
        photoPreview.style.display = "block";
        const uploadContent = photoUpload.querySelector(".upload-content");
        if (uploadContent) uploadContent.style.display = "none";
      };
      reader.readAsDataURL(file);
    }
  } else {
    // helpful console warning if elements not found
    console.warn("photoUpload/photoInput/photoPreview element missing — check IDs in template.");
  }

  // initialize first step
  showStep(1);
});
