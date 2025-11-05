
from datetime import date
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg,Q
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Student, Mark,Teacher,Subject,Semester
from .forms import StudentForm, MarkForm,MarksEntryForm,SubjectForm
from django.contrib.auth.decorators import login_required, user_passes_test



def home(request):
    return render(request, "home.html")




def teacher_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect("teacher_dashboard")
        else:
            messages.error(request, "Invalid username or password or unauthorized access")
    return render(request, "teacher_login.html")




def student_login(request):
    if request.method == "POST":
        reg_no = request.POST.get("reg_no")
        dob = request.POST.get("dob") 
        try:
            student = Student.objects.get(reg_no=reg_no, dob=dob)
            request.session["student_id"] = student.id
            return redirect("student_dashboard")
        except Student.DoesNotExist:
            messages.error(request, "Invalid Registration Number or Date of Birth")
    return render(request, "student_login.html")




@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def teacher_dashboard(request):
    teacher_name = request.user.first_name or request.user.username
    return render(request, "teacher_dashboard.html",{"teacher_name": teacher_name})




def student_required(view_func):
    
    def wrapper(request, *args, **kwargs):
        if not request.session.get("student_id"):
            return redirect("student_login") 
        return view_func(request, *args, **kwargs)
    return wrapper


@student_required
def student_dashboard(request):
    student_id = request.session.get("student_id")
    student = Student.objects.get(id=student_id)

    marks = Mark.objects.filter(semester__student=student)

    for m in marks:
        m.passed = m.marks_obtained >= 0.4 * m.max_marks

    total_papers = marks.count()
    passed = sum(1 for m in marks if m.passed)
    failed = total_papers - passed

   
    semesters = marks.values_list('semester__number', flat=True).distinct()
    sgpa_values = []
    sgpa_labels = []

    semester_credit_map = {}  

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

   
    total_all_credits = sum(semester_credit_map.values())
    if total_all_credits > 0:
        cgpa = round(sum(sgpa * semester_credit_map[sem] for sem, sgpa in zip(semesters, sgpa_values)) / total_all_credits, 2)
    else:
        cgpa = 0


    selected_semester = request.GET.get("semester")
    if selected_semester:
        selected_semester = int(selected_semester)
        marks_selected = marks.filter(semester__number=selected_semester)
    else:
      
        latest_sem = marks.order_by('-semester__number').first().semester.number if marks.exists() else student.semester
        selected_semester = latest_sem
        marks_selected = marks.filter(semester__number=latest_sem)


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



@login_required
def user_logout(request):
    logout(request)
    return redirect("home")




@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)

          
            start_year = int(student.academic_year.split("-")[0])
            current_year = date.today().year
            years_passed = current_year - start_year
            student.semester = (years_passed * 2) + 1 

            student.save() 

            
            return redirect("student_success", student_name=student.name)
    else:
        form = StudentForm()
    return render(request, "add_student.html", {"form": form})




@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def select_student_semester(request):
    students = Student.objects.all()
    filtered_students = students

   
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



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def select_student_semester(request):
    if request.method == "POST":
        reg_no = request.POST.get("reg_no")
        semester_number = request.POST.get("semester")
        attempt_type = request.POST.get("attempt_type")

        if reg_no and semester_number and attempt_type:
            try:
                student = Student.objects.get(reg_no__iexact=reg_no)

                
                if attempt_type == "Regular":
                    
                    existing = Mark.objects.filter(
                        semester__student=student,
                        semester__number=semester_number
                    ).exists()

                    if existing:
                        messages.warning(
                            request,
                            f"Regular marks for {student.name} (Semester {semester_number}) are already entered."
                        )
                        return redirect("teacher_dashboard")

              
                return redirect(
                    f"/add-marks-single/?student_id={student.id}&semester={semester_number}&attempt_type={attempt_type}"
                )

            except Student.DoesNotExist:
                messages.error(request, "Student not found")

        else:
            messages.error(request, "Please fill all fields")

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
                "id": student.id  
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
    attempt_type = request.GET.get("attempt_type", "Regular")

    if not student_id or not sem_number:
        return redirect("teacher_dashboard")

    student = get_object_or_404(Student, id=student_id)
    semester, _ = Semester.objects.get_or_create(student=student, number=sem_number)

    # Get all subjects in semester
    subjects = Subject.objects.filter(course=student.course, semester_number=semester.number)
    

    # ✅ 1️⃣ Regular Attempt: Check if already entered
    if attempt_type == "Regular":
        existing = Mark.objects.filter(semester=semester).exists()
        if existing:
            return render(request, "add_marks_already_exists.html", {
                "student": student,
                "semester": sem_number,
                "attempt_type": attempt_type
            })

    # ✅ 2️⃣ Supply/Improvement Step 1: Subject selection page
    if attempt_type == "Supply/Improvement" and request.method != "POST" and not request.GET.getlist("subjects"):
        return render(request, "select_supply_subjects.html", {
            "student": student,
            "semester": sem_number,
            "subjects": subjects
        })

    # ✅ 3️⃣ Handle selected subjects (Supply flow or Regular flow)
    selected_subject_ids = request.GET.getlist("subjects") or request.POST.getlist("selected_subjects")
    selected_subjects = Subject.objects.filter(id__in=selected_subject_ids) if selected_subject_ids else subjects

    # ✅ 4️⃣ Handle marks submission (AJAX)
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        errors = {}
        for subject in selected_subjects:
            try:
                new_mark = float(request.POST.get(f"marks_{subject.id}", 0))
                max_marks = float(request.POST.get(f"max_{subject.id}", 50))

                mark, created = Mark.objects.get_or_create(
                    semester=semester,
                    subject=subject,
                    defaults={
                        "marks_obtained": new_mark,
                        "max_marks": max_marks,
                        "attempt_type": attempt_type,
                        "attempt_no": 1
                    }
                )

                if not created and attempt_type == "Supply/Improvement":
                    # Compare old vs new marks → Save highest
                    highest = max(mark.marks_obtained, new_mark)
                    mark.marks_obtained = highest
                    mark.max_marks = max_marks
                    mark.attempt_no += 1
                    mark.attempt_type = attempt_type
                    mark.save()

            except Exception as e:
                errors[subject.name] = str(e)

        if errors:
            return JsonResponse({"success": False, "errors": errors})
        else:
            return JsonResponse({"success": True, "message": f"{attempt_type} marks saved successfully!"})

    # ✅ 5️⃣ Preload existing marks for display
    existing_marks = {m.subject.id: m for m in Mark.objects.filter(semester=semester, subject__in=selected_subjects)}

    # ✅ 6️⃣ Render correct template
    return render(
        request,
        "add_marks_supply.html" if attempt_type == "Supply/Improvement" else "add_marks_single.html",
        {
            "student": student,
            "semester": sem_number,
            "subjects": selected_subjects,
            "existing_marks": existing_marks,
            "attempt_type": attempt_type
        }
    )






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

    all_marks = Mark.objects.filter(semester__student=student).select_related("subject", "semester")

    # Pass/fail calculation
    for m in all_marks:
        m.passed = m.marks_obtained >= (0.4 * m.max_marks)

    total_papers = all_marks.count()
    passed = sum(1 for m in all_marks if m.passed)
    failed = total_papers - passed

    # --- ✅ Correct Kannur University SGPA / CGPA Calculation ---
    semesters = all_marks.values_list("semester__number", flat=True).distinct()
    sgpa_values, sgpa_labels = [], []
    semester_credit_map = {}

    for sem in semesters:
        sem_marks = all_marks.filter(semester__number=sem)
        if sem_marks.exists():
            total_credits = sum((m.subject.credits or 0) for m in sem_marks)
            total_credit_points = 0

            for m in sem_marks:
                # Grade Point = (marks_obtained / max_marks) × 10
                gp = (m.marks_obtained / m.max_marks) * 10 if m.max_marks > 0 else 0
                # Credit Point = Grade Point × Credits
                total_credit_points += gp * (m.subject.credits or 0)

            sgpa = round(total_credit_points / total_credits, 3) if total_credits > 0 else 0
            sgpa_values.append(sgpa)
            sgpa_labels.append(f"Sem {sem}")
            semester_credit_map[sem] = total_credits
        else:
            sgpa_values.append(0)
            sgpa_labels.append(f"Sem {sem}")
            semester_credit_map[sem] = 0

    # CGPA = Weighted average of SGPAs by credits
    total_all_credits = sum(semester_credit_map.values())
    if total_all_credits > 0:
        cgpa = round(
            sum(
                sgpa * semester_credit_map.get(sem, 0)
                for sgpa, sem in zip(sgpa_values, semesters)
            )
            / total_all_credits,
            3,
        )
    else:
        cgpa = 0.0

    # Semester filter for table display
    selected_semester = request.GET.get("semester")
    if selected_semester:
        marks = all_marks.filter(semester__number=selected_semester)
    else:
        marks = all_marks

    # Pass/fail + attempt count
    for m in marks:
        m.passed = m.marks_obtained >= (0.4 * m.max_marks)
        m.attempt_count = m.attempt_no

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
        "cgpa": cgpa
    })


@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def student_success(request, student_name):
    return render(request, "student_success.html", {"student_name": student_name})

