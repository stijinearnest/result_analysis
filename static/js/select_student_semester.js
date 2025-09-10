const regInput = document.getElementById('reg_no');
const nameInput = document.getElementById('student_name');
const studentIdInput = document.getElementById('student_id');

regInput.addEventListener('input', () => {
    const reg_no = regInput.value.trim();
    if (!reg_no) {
        nameInput.value = '';
        studentIdInput.value = '';
        return;
    }

    fetch(`/teacher/get-student-name-by-regno/?reg_no=${reg_no}`)
        .then(res => res.json())
        .then(data => {
            nameInput.value = data.name || '';
            studentIdInput.value = data.id || '';
        })
        .catch(err => {
            console.error('Error fetching student:', err);
            nameInput.value = '';
            studentIdInput.value = '';
        });
});
