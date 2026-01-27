// static/js/manage_subjects.js
// Responsibilities:
// 1. Delete confirmation
// 2. Course → Syllabus filtering
// 3. Inline syllabus creation
// 4. Sync syllabus filter with SubjectForm

document.addEventListener("DOMContentLoaded", () => {
  /* ===============================
     Delete confirmation
     =============================== */
  document.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      if (!confirm("Are you sure you want to delete this subject?")) {
        e.preventDefault();
      }
    });
  });

  /* ===============================
     Elements
     =============================== */
  const courseSelect = document.getElementById("id_course");
  const syllabusFilter = document.getElementById("syllabus_select"); // filter dropdown
  const syllabusFormField = document.getElementById("id_syllabus"); // form field
  const addBox = document.getElementById("add_syllabus_box");
  const saveBtn = document.getElementById("save_syllabus_btn");
  const yearInput = document.getElementById("new_syllabus_year");

  if (!courseSelect || !syllabusFilter) return;

  /* ===============================
     Load syllabi for course
     =============================== */
  function loadSyllabi(course, selectedId = null) {
    syllabusFilter.innerHTML = `<option value="">Loading syllabus...</option>`;

    fetch(`/ajax/get-syllabus/?course=${encodeURIComponent(course)}`)
      .then(res => res.json())
      .then(data => {
        syllabusFilter.innerHTML =
          `<option value="">Select syllabus year</option>`;

        data.syllabi.forEach(s => {
          const opt = document.createElement("option");
          opt.value = s.id;
          opt.textContent = s.year;
          if (selectedId && String(selectedId) === String(s.id)) {
            opt.selected = true;
          }
          syllabusFilter.appendChild(opt);
        });

        syllabusFilter.innerHTML +=
          `<option value="__add__">➕ Add new syllabus year</option>`;
      });
  }

  /* ===============================
     Course change
     =============================== */
  courseSelect.addEventListener("change", () => {
    const course = courseSelect.value;
    if (!course) return;

    loadSyllabi(course);

    // reset form syllabus
    if (syllabusFormField) {
      syllabusFormField.innerHTML = `<option value="">Select syllabus</option>`;
    }
  });

  /* ===============================
     Syllabus filter change
     =============================== */
  syllabusFilter.addEventListener("change", () => {
    const val = syllabusFilter.value;

    if (val === "__add__") {
      addBox.style.display = "block";
      return;
    }

    addBox.style.display = "none";

    // sync with form field
    if (syllabusFormField) {
      syllabusFormField.value = val;
    }

    // reload page with syllabus filter
    if (val) {
      window.location.search = `?syllabus=${val}`;
    }
  });

  /* ===============================
     Create syllabus
     =============================== */
  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      const year = yearInput.value;
      const course = courseSelect.value;

      if (!year || !course) {
        alert("Please enter syllabus year");
        return;
      }

      fetch("/ajax/create-syllabus/", {
        method: "POST",
        headers: {
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `course=${encodeURIComponent(course)}&year=${year}`,
      })
        .then(res => res.json())
        .then(data => {
          if (!data.success) {
            alert(data.error);
            return;
          }

          // reload syllabi and auto-select new one
          loadSyllabi(course, data.id);

          if (syllabusFormField) {
            syllabusFormField.value = data.id;
          }

          addBox.style.display = "none";
          yearInput.value = "";
        });
    });
  }

  /* ===============================
     Initial load (if syllabus in URL)
     =============================== */
  const params = new URLSearchParams(window.location.search);
  const selectedSyllabus = params.get("syllabus");

  if (courseSelect.value) {
    loadSyllabi(courseSelect.value, selectedSyllabus);
  }
});
