from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404



from django.db.models import Avg

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Student, Mark,Teacher,Subject,Semester
from .forms import StudentForm, MarkForm,MarksEntryForm
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

    # All marks (via semester → student)
    marks = Mark.objects.filter(semester__student=student)

    total_papers = marks.count()
    passed = marks.filter(marks_obtained__gte=18).count()
    failed = total_papers - passed

    # SGPA chart
    sgpa_data = marks.values('semester__number').annotate(avg=Avg('marks_obtained')).order_by('semester__number')
    sgpa_labels = [f"Sem {d['semester__number']}" for d in sgpa_data]
    sgpa_values = [round(d['avg'] / 10, 2) for d in sgpa_data]

    # CGPA
    cgpa = round(marks.aggregate(Avg('marks_obtained'))['marks_obtained__avg'] / 10, 2) if marks.exists() else 0

    # Semester filter
    selected_semester = request.GET.get("semester")
    if not selected_semester and sgpa_data:
        selected_semester = sgpa_data.last()['semester__number']
    elif not selected_semester:
        selected_semester = student.semester

    marks_selected = marks.filter(semester__number=selected_semester)
    semesters = sgpa_data.values_list("semester__number", flat=True)

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
        "selected_semester": int(selected_semester),
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
@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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

    if request.method == "POST":
        form = MarksEntryForm(request.POST, semester=semester)
        if form.is_valid():
            for field_name, value in form.cleaned_data.items():
                if field_name.startswith("subject_"):
                    subject_id = int(field_name.split("_")[1])
                    subject = Subject.objects.get(id=subject_id)

                    # Save or update mark
                    Mark.objects.update_or_create(
                        semester=semester,
                        subject=subject,
                        defaults={"marks_obtained": value, "max_marks": 40},
                    )
            return redirect("teacher_dashboard")
    else:
        form = MarksEntryForm(semester=semester)

    return render(request, "add_marks.html", {
        "form": form,
        "student": student,
        "semester": semester,
    })


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
def student_detail(request):
    student = None
    if request.method == "POST":
        reg_no = request.POST.get("reg_no")
        try:
            student = Student.objects.get(reg_no=reg_no)
        except Student.DoesNotExist:
            student = None
        
    return render(request, "student_detail.html", {"student": student})



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
            data = {"name": student.name}
        except Student.DoesNotExist:
            data = {"name": ""}
    else:
        data = {"name": ""}
    return JsonResponse(data)


@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def add_marks_single_page(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        sem_number = request.POST.get("semester")
        student = get_object_or_404(Student, id=student_id)
        semester, created = Semester.objects.get_or_create(student=student, number=sem_number)
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
    return render(request, "add_marks_single.html")

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
