from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404



from django.db.models import Avg,Q

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Student, Mark,Teacher,Subject,Semester
from .forms import StudentForm, MarkForm,MarksEntryForm,SubjectForm
from django.contrib.auth.decorators import login_required, user_passes_test

# -------------------------------
# Home (landing page)
# -------------------------------
def home(request):
    return render(request, "home.html")


# -------------------------------
# Teacher login
# -------------------------------
def teacher_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
           # teacher=Teacher.objects.get(name=username)
            return redirect("teacher_dashboard")
        else:
            messages.error(request, "Invalid username or password or unauthorized access")
    return render(request, "teacher_login.html")


# -------------------------------
# Student login
# -------------------------------
def student_login(request):
    if request.method == "POST":
        reg_no = request.POST.get("reg_no")
        dob = request.POST.get("dob")  # format YYYY-MM-DD
        try:
            student = Student.objects.get(reg_no=reg_no, dob=dob)
            request.session["student_id"] = student.id
            return redirect("student_dashboard")
        except Student.DoesNotExist:
            messages.error(request, "Invalid Registration Number or Date of Birth")
    return render(request, "student_login.html")


# -------------------------------
# Teacher Dashboard
# -------------------------------
@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def teacher_dashboard(request):
    return render(request, "teacher_dashboard.html")


# -------------------------------
# Student Dashboard
# -------------------------------
def student_required(view_func):
    """Decorator to ensure a student is logged in via session."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get("student_id"):
            return redirect("student_login")  # Corrected
        return view_func(request, *args, **kwargs)
    return wrapper

@student_required
def student_dashboard(request):
    student_id = request.session.get("student_id")
    student = Student.objects.get(id=student_id)

    marks = Mark.objects.filter(semester__student=student)

    # Pass/fail (40% of max_marks)
    for m in marks:
        m.passed = m.marks_obtained >= 0.4 * m.max_marks

    total_papers = marks.count()
    passed = sum(1 for m in marks if m.passed)
    failed = total_papers - passed

    # SGPA per semester (weighted by credits)
    semesters = marks.values_list('semester__number', flat=True).distinct()
    sgpa_values = []
    sgpa_labels = []

    semester_credit_map = {}  # total credits per semester

    for sem in semesters:
        sem_marks = marks.filter(semester__number=sem)
        total_credits = sum(m.subject.credits for m in sem_marks)
        semester_credit_map[sem] = total_credits

        if total_credits > 0:
            weighted_sum = sum((m.marks_obtained / m.max_marks) * m.subject.credits for m in sem_marks)
            sgpa = round((weighted_sum / total_credits) * 10, 2)
        else:
            sgpa = 0
        sgpa_values.append(sgpa)
        sgpa_labels.append(f"Sem {sem}")

    # CGPA = weighted average of SGPA by semester credits
    total_all_credits = sum(semester_credit_map.values())
    if total_all_credits > 0:
        cgpa = round(sum(sgpa * semester_credit_map[sem] for sem, sgpa in zip(semesters, sgpa_values)) / total_all_credits, 2)
    else:
        cgpa = 0

    # Semester filter
    selected_semester = request.GET.get("semester")
    if selected_semester:
        marks_selected = marks.filter(semester__number=selected_semester)
    else:
        marks_selected = marks

    return render(request, "student_dashboard.html", {
        "student": student,
        "cgpa": cgpa,
        "total_papers": total_papers,
        "passed": passed,
        "failed": failed,
        "sgpa_labels": sgpa_labels,
        "sgpa_values": sgpa_values,
        "marks": marks_selected,
        "semesters": semesters,
        "selected_semester": selected_semester,
    })

# -------------------------------
# Logout
# -------------------------------
@login_required
def user_logout(request):
    logout(request)
    return redirect("home")


# -------------------------------
# Teacher: Add Student
# -------------------------------
from datetime import date

@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)

            # Automatically calculate semester based on academic year
            # Example logic: 1 academic year = 2 semesters
            # Assuming academic_year format is "YYYY-YYYY"
            start_year = int(student.academic_year.split("-")[0])
            current_year = date.today().year
            years_passed = current_year - start_year
            student.semester = (years_passed * 2) + 1  # +1 for first semester of current year

            student.save()  # Save to DB

            return redirect("teacher_dashboard")
    else:
        form = StudentForm()
    return render(request, "add_student.html", {"form": form})



# -------------------------------
# Teacher: Add Marks
# -------------------------------

# -------------------------------
# Teacher: Select Student
# -------------------------------
@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def select_student_semester(request):
    students = Student.objects.all()
    filtered_students = students

    # Filter by course, reg_no, academic year
    course = request.GET.get('course')
    reg_no = request.GET.get('reg_no')
    academic_year = request.GET.get('academic_year')

    if course:
        filtered_students = filtered_students.filter(course=course)
    if reg_no:
        filtered_students = filtered_students.filter(reg_no__icontains=reg_no)
    if academic_year:
        filtered_students = filtered_students.filter(academic_year=academic_year)

    if request.method == "POST":
        student_id = request.POST.get('student')
        semester_number = request.POST.get('semester')
        return redirect('add_marks', student_id=student_id, sem_number=semester_number)

    return render(request, "select_student_semester.html", {
        "students": filtered_students
    })


# -------------------------------
# Teacher: Add Marks
# -------------------------------
@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def add_marks(request, student_id, sem_number):
    student = get_object_or_404(Student, id=student_id)
    semester, created = Semester.objects.get_or_create(student=student, number=sem_number)

    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        form = MarksEntryForm(request.POST, semester=semester)
        if form.is_valid():
            for field_name, value in form.cleaned_data.items():
                if field_name.startswith("subject_"):
                    subject_id = int(field_name.split("_")[1])
                    subject = Subject.objects.get(id=subject_id)
                    Mark.objects.update_or_create(
                        semester=semester,
                        subject=subject,
                        defaults={"marks_obtained": value, "max_marks": 40},
                    )
            return JsonResponse({"success": True, "message": "Marks saved successfully!"})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"error": "Invalid request"})



# -------------------------------
# Teacher: Edit Marks
# -------------------------------
@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def edit_marks(request, mark_id):
    mark = Mark.objects.get(id=mark_id)
    if request.method == "POST":
        form = MarkForm(request.POST, instance=mark)
        if form.is_valid():
            form.save()
            return redirect("teacher_dashboard")
    else:
        form = MarkForm(instance=mark)
    return render(request, "edit_marks.html", {"form": form})


# -------------------------------
# Teacher: Search student details
# -------------------------------




@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def select_student_semester(request):
    if request.method == "POST":
        reg_no = request.POST.get("reg_no")
        semester_number = request.POST.get("semester")
        if reg_no and semester_number:
            try:
                student = Student.objects.get(reg_no__iexact=reg_no)
                return redirect("add_marks", student_id=student.id, sem_number=semester_number)
            except Student.DoesNotExist:
                messages.error(request, "Student not found")
        else:
            messages.error(request, "Please enter registration number and select semester")

    return render(request, "select_student_semester.html")



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def get_student_name_by_regno(request):
    reg_no = request.GET.get('reg_no')
    if reg_no:
        try:
            student = Student.objects.get(reg_no__iexact=reg_no)
            data = {
                "name": student.name,
                "id": student.id   # <-- include student id
            }
        except Student.DoesNotExist:
            data = {"name": "", "id": ""}
    else:
        data = {"name": "", "id": ""}
    return JsonResponse(data)

@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def add_marks_single_page(request):
    student_id = request.GET.get("student_id")
    sem_number = request.GET.get("semester")

    if not student_id or not sem_number:
        return redirect("teacher_dashboard")

    student = get_object_or_404(Student, id=student_id)
    semester, _ = Semester.objects.get_or_create(student=student, number=sem_number)

    # Subjects for this semester & course
    subjects = Subject.objects.filter(course=student.course, semester_number=semester.number)

    # Check if marks already exist
    existing_marks = Mark.objects.filter(semester=semester).exists()
    if existing_marks:
        return render(request, "add_marks_single.html", {
            "student": student,
            "semester": sem_number,
            "already_exists": True
        })

    # Handle AJAX form submission
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        errors = {}
        for subject in subjects:
            try:
                marks_obtained = float(request.POST.get(f"marks_{subject.id}", 0))
                max_marks = float(request.POST.get(f"max_{subject.id}", 40))
                Mark.objects.update_or_create(
                    semester=semester,
                    subject=subject,
                    defaults={"marks_obtained": marks_obtained, "max_marks": max_marks}
                )
            except Exception as e:
                errors[subject.name] = str(e)

        if errors:
            return JsonResponse({"success": False, "errors": errors})
        else:
            return JsonResponse({"success": True, "message": f"Marks for {student.name} saved successfully!"})

    # Render template
    return render(request, "add_marks_single.html", {
        "student": student,
        "semester": sem_number,
        "subjects": subjects,
        "already_exists": False
    })




@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def get_subjects_for_semester(request):
    sem_number = request.GET.get("semester")
    if sem_number:
        subjects = Subject.objects.filter(semester_number=sem_number)
        data = [{"id": s.id, "name": s.name, "code": s.code} for s in subjects]
    else:
        data = []
    return JsonResponse({"subjects": data})

@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def get_subjects_for_semester(request):
    sem_number = request.GET.get("semester")
    subjects = Subject.objects.filter(semester_number=sem_number) if sem_number else []
    data = [{"id": s.id, "name": s.name, "code": s.code, "credits": s.credits} for s in subjects]
    return JsonResponse({"subjects": data})

# Manage Subjects page
from .forms import SubjectForm

@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def manage_subjects(request):
    subjects = Subject.objects.all().order_by("course", "semester_number")

    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("manage_subjects")
    else:
        form = SubjectForm()

    return render(request, "manage_subjects.html", {"subjects": subjects, "form": form})


@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect("manage_subjects")
    else:
        form = SubjectForm(instance=subject)
    return render(request, "edit_subject.html", {"form": form, "subject": subject})


@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    return redirect("manage_subjects")
# Step 1: Course selection page
@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def select_course(request):
    COURSES = [
        "Computer Science",
        "Business Administration",
        "Engineering",
        "Medicine",
        "Law",
    ]
    if request.method == "POST":
        selected_course = request.POST.get("course")
        if selected_course:
            return redirect('manage_subjects_by_course', course=selected_course)
    return render(request, "select_course.html", {"courses": COURSES})


# Step 2: Manage subjects for a course
@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def manage_subjects_by_course(request, course):
    subjects = Subject.objects.filter(course=course).order_by('semester_number')
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_subjects_by_course', course=course)
    else:
        form = SubjectForm(initial={"course": course})
    return render(request, "manage_subjects.html", {
        "subjects": subjects,
        "form": form,
        "course": course
    })


# Optional: Delete subject
@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    course = subject.course
    subject.delete()
    return redirect('manage_subjects_by_course', course=course)



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def student_search(request):
    students = []
    query = request.GET.get("q")
    if query:
        students = Student.objects.filter(reg_no__icontains=query)
    return render(request, "student_search.html", {"students": students})
    


@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # fetch marks via semester → student
    marks = Mark.objects.filter(semester__student=student)

    # add pass/fail attribute to each mark
    for m in marks:
        m.passed = m.marks_obtained >= (0.4 * m.max_marks)  # 40% of max_marks

    # get distinct semesters
    semesters = marks.values_list("semester__number", flat=True).distinct()

    selected_semester = request.GET.get("semester")
    if selected_semester:
        marks = marks.filter(semester__number=selected_semester)

    # SGPA/CGPA calculations
    sgpa_values = []
    sgpa_labels = []
    for sem in semesters:
        sem_marks = Mark.objects.filter(semester__student=student, semester__number=sem)
        if sem_marks.exists():
            total_obt = sum(m.marks_obtained for m in sem_marks)
            total_max = sum(m.max_marks for m in sem_marks)
            sgpa = round((total_obt / total_max) * 10, 2) if total_max > 0 else 0
            sgpa_values.append(sgpa)
            sgpa_labels.append(f"Sem {sem}")

    total_papers = marks.count()
    passed = sum(1 for m in marks if m.passed)
    failed = total_papers - passed
    cgpa = round(sum(sgpa_values) / len(sgpa_values), 2) if sgpa_values else 0

    return render(request, "student_detail.html", {
        "student": student,
        "marks": marks,
        "semesters": semesters,
        "selected_semester": selected_semester,
        "sgpa_values": sgpa_values,
        "sgpa_labels": sgpa_labels,
        "total_papers": total_papers,
        "passed": passed,
        "failed": failed,
        "cgpa": cgpa,
    })
