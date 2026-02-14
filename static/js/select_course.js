document.addEventListener("DOMContentLoaded", () => {
    const courseSelect = document.getElementById("course");
    const syllabusBox = document.getElementById("syllabusBox");
    const syllabusSelect = document.getElementById("syllabus");

    const addBox = document.getElementById("addSyllabusBox");
    const saveBtn = document.getElementById("saveSyllabusBtn");
    const yearInput = document.getElementById("new_syllabus_year");

    const form = document.getElementById("selectCourseForm");

    function loadSyllabi(course, autoSelectId = null) {
        syllabusSelect.innerHTML =
            '<option value="">-- Select Syllabus Year --</option>';

        fetch(`/ajax/get-syllabus/?course=${encodeURIComponent(course)}`)
            .then(res => res.json())
            .then(data => {
                syllabusBox.style.display = "block";

                data.syllabi.forEach(s => {
                    const opt = document.createElement("option");
                    opt.value = s.id;
                    opt.textContent = s.year;
                    if (autoSelectId && String(autoSelectId) === String(s.id)) {
                        opt.selected = true;
                    }
                    syllabusSelect.appendChild(opt);
                });

                const addOpt = document.createElement("option");
                addOpt.value = "__add__";
                addOpt.textContent = "➕ Add new syllabus year";
                syllabusSelect.appendChild(addOpt);
            });
    }

    courseSelect.addEventListener("change", () => {
        const course = courseSelect.value;
        if (!course) return;

        addBox.style.display = "none";
        loadSyllabi(course);
    });

    syllabusSelect.addEventListener("change", () => {
        if (syllabusSelect.value === "__add__") {
            addBox.style.display = "block";
        } else {
            addBox.style.display = "none";
        }
    });

    saveBtn.addEventListener("click", () => {
        const year = yearInput.value;
        const course = courseSelect.value;

        if (!year || !course) {
            alert("Enter syllabus year");
            return;
        }

        fetch("/ajax/create-syllabus/", {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: `course=${encodeURIComponent(course)}&year=${year}`
        })
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    alert(data.error || "Failed to create syllabus");
                    return;
                }

                yearInput.value = "";
                addBox.style.display = "none";
                loadSyllabi(course, data.id);
            });
    });

    form.addEventListener("submit", e => {
        e.preventDefault();

        const course = courseSelect.value;
        const syllabus = syllabusSelect.value;

        if (!course || !syllabus || syllabus === "__add__") {
            alert("Please select course and syllabus year");
            return;
        }

        window.location.href =
    `/teacher/manage-subjects/${course}/?syllabus=${syllabus}`;

    });
});
