// static/js/add_student.js

document.addEventListener("DOMContentLoaded", () => {
  // ===== Elements =====
  const form = document.getElementById("studentForm");

  const stepperSteps = Array.from(document.querySelectorAll(".step"));
  const stepPanels = Array.from(document.querySelectorAll(".step-panel"));
  const btnNext = document.querySelectorAll(".btn-next");
  const btnPrev = document.querySelectorAll(".btn-prev");

  const courseSelect = document.getElementById("course");
  const syllabusSelect = document.getElementById("syllabus");

  const photoUpload = document.getElementById("photoUpload");
  const photoInput = document.getElementById("photo");
  const photoPreview = document.getElementById("photoPreview");

  let currentStep = 1;

  // ===== Stepper Logic =====
  function showStep(step) {
    currentStep = step;

    stepPanels.forEach(panel => {
      panel.style.display =
        Number(panel.dataset.step) === step ? "" : "none";
    });

    stepperSteps.forEach(s => {
      s.classList.toggle("active", Number(s.dataset.step) === step);
    });

    const card = document.querySelector(".registration-card");
    if (card) {
      window.scrollTo({
        top: card.offsetTop - 20,
        behavior: "smooth",
      });
    }
  }

  function validateStep(step) {
    const panel = document.querySelector(
      `.step-panel[data-step="${step}"]`
    );
    if (!panel) return true;

    const requiredEls = Array.from(
      panel.querySelectorAll("[required]")
    );

    for (const el of requiredEls) {
      if (el.type === "file" || el.disabled) continue;

      if (!el.value || el.value.trim() === "") {
        el.classList.add("invalid");
        el.focus();
        return false;
      } else {
        el.classList.remove("invalid");
      }
    }
    return true;
  }

  // Next / Prev buttons
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

  // Stepper click navigation
  stepperSteps.forEach(el => {
    el.addEventListener("click", () => {
      const step = Number(el.dataset.step);
      if (step === currentStep) return;

      if (step < currentStep) {
        showStep(step);
        return;
      }

      for (let s = 1; s < step; s++) {
        if (!validateStep(s)) return;
      }
      showStep(step);
    });
  });

  // ===== Form Submit Guard =====
  if (form) {
    form.addEventListener("submit", e => {
      if (!validateStep(currentStep)) {
        e.preventDefault();
        return;
      }

      const submitBtn = form.querySelector(".btn-submit-final");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Submitting...";
        submitBtn.style.opacity = "0.7";
      }
    });
  }

  // ===== Course → Syllabus AJAX =====
  if (courseSelect && syllabusSelect) {
    courseSelect.addEventListener("change", () => {
      const course = courseSelect.value;

      syllabusSelect.innerHTML =
        '<option value="">Loading syllabus...</option>';

      if (!course) {
        syllabusSelect.innerHTML =
          '<option value="">Select syllabus year</option>';
        return;
      }

      fetch(`/ajax/get-syllabus/?course=${encodeURIComponent(course)}`)
        .then(res => res.json())
        .then(data => {
          syllabusSelect.innerHTML =
            '<option value="">Select syllabus year</option>';

          data.syllabi.forEach(s => {
            const option = document.createElement("option");
            option.value = s.id;
            option.textContent = s.year;
            syllabusSelect.appendChild(option);
          });
        })
        .catch(() => {
          syllabusSelect.innerHTML =
            '<option value="">Failed to load syllabus</option>';
        });
    });
  }

  // ===== Photo Upload (Click + Drag/Drop + Preview) =====
  if (photoUpload && photoInput && photoPreview) {
    photoUpload.style.cursor = "pointer";

    photoUpload.addEventListener("click", e => {
      e.preventDefault();
      photoInput.click();
    });

    photoUpload.addEventListener("dragover", e => {
      e.preventDefault();
      photoUpload.classList.add("dragover");
    });

    photoUpload.addEventListener("dragleave", e => {
      e.preventDefault();
      photoUpload.classList.remove("dragover");
    });

    photoUpload.addEventListener("drop", e => {
      e.preventDefault();
      photoUpload.classList.remove("dragover");
      const file = e.dataTransfer.files[0];
      if (file) {
        photoInput.files = e.dataTransfer.files;
        showPreview(file);
      }
    });

    photoInput.addEventListener("change", () => {
      const file = photoInput.files[0];
      if (file) showPreview(file);
    });

    function showPreview(file) {
      const maxMB = 5;
      if (file.size > maxMB * 1024 * 1024) {
        alert(`Image must be ${maxMB}MB or smaller.`);
        photoInput.value = "";
        return;
      }

      if (!file.type.startsWith("image/")) {
        alert("Please upload a valid image.");
        photoInput.value = "";
        return;
      }

      const reader = new FileReader();
      reader.onload = e => {
        photoPreview.src = e.target.result;
        photoPreview.style.display = "block";

        const uploadContent =
          photoUpload.querySelector(".upload-content");
        if (uploadContent) uploadContent.style.display = "none";
      };
      reader.readAsDataURL(file);
    }
  }

  // ===== Init =====
  showStep(1);
});
