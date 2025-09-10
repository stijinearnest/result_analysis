// JS for Manage Subjects (optional confirmation dialogs)
document.addEventListener("DOMContentLoaded", () => {
    const deleteLinks = document.querySelectorAll(".delete-btn");

    deleteLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            if (!confirm("Are you sure you want to delete this subject?")) {
                e.preventDefault();
            }
        });
    });
});
