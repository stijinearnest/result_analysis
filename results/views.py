from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from django.http import HttpResponse

from collections import defaultdict
from django.db.models import Max
from django.views.decorators.http import require_GET
from datetime import date
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg,Q
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Department, Student, Mark,Teacher,Subject,Semester,Syllabus,Course
from .forms import StudentForm, MarkForm,MarksEntryForm,SubjectForm,TeacherCreateForm,TeacherEditForm
from django.contrib.auth.decorators import login_required, user_passes_test
from collections import defaultdict
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponseRedirect


def is_hod(user):
    return (
        hasattr(user, "teacher") and
        user.teacher.role == "HOD"
    )


def home(request):
    return render(request, "home.html")


def teacher_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            if user.is_superuser:
                return redirect("admin_dashboard")
            else:
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

    is_hod_user = (
        request.user.is_superuser or
        (hasattr(request.user, "teacher") and request.user.teacher.role == "HOD")
    )

    return render(request, "teacher_dashboard.html", {
        "teacher_name": teacher_name,
        "is_hod_user": is_hod_user
    })



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")

def student_required(view_func):
    
    def wrapper(request, *args, **kwargs):
        if not request.session.get("student_id"):
            return redirect("student_login") 
        return view_func(request, *args, **kwargs)
    return wrapper


@student_required
def student_dashboard(request):
    student_id = request.session.get("student_id")
    student = get_object_or_404(Student, id=student_id)

    #best marks selecting
    all_marks = Mark.objects.filter(semester__student=student).select_related("subject", "semester")
    subject_best_map = defaultdict(lambda: None)
    for mark in all_marks:
        current_best = subject_best_map[mark.subject]
        if current_best is None or mark.marks_obtained > current_best.marks_obtained:
            subject_best_map[mark.subject] = mark

    best_marks = list(subject_best_map.values())

    
    for m in best_marks:
        m.passed = (m.marks_obtained >= (0.4 * m.max_marks)) if m.max_marks is not None else False
        # attempt count 
        m.attempt_count = Mark.objects.filter(semester__student=student, subject=m.subject).count()

    # Totals based on best_marks
    total_papers = len(best_marks)
    passed = sum(1 for m in best_marks if m.passed)
    failed = total_papers - passed

    # 
    semesters = sorted({m.semester.number for m in best_marks})

    # Compute SGPA per semester and CGPA using credit-weighted GPA (same approach as student_detail)
    sgpa_values = []
    sgpa_labels = []
    semester_credit_map = {}

    for sem in semesters:
        # marks belonging to this semester (from best_marks)
        sem_marks = [m for m in best_marks if m.semester.number == sem]
        if sem_marks:
            total_credits = sum((m.subject.credits or 0) for m in sem_marks)
            semester_credit_map[sem] = total_credits
            total_credit_points = 0.0
            for m in sem_marks:
                # grade point scaled to 10 (same as student_detail)
                gp = (m.marks_obtained / m.max_marks) * 10 if (m.max_marks and m.max_marks > 0) else 0
                total_credit_points += gp * (m.subject.credits or 0)
            sgpa = round(total_credit_points / total_credits, 3) if total_credits > 0 else 0
        else:
            sgpa = 0
            semester_credit_map[sem] = 0
        sgpa_values.append(sgpa)
        sgpa_labels.append(f"Sem {sem}")

    total_all_credits = sum(semester_credit_map.values())
    if total_all_credits > 0:
        # Weighted average of semester SGPAs using semester credits (same method as student_detail)
        cgpa = round(
            sum(
                sgpa * semester_credit_map.get(sem, 0)
                for sgpa, sem in zip(sgpa_values, semesters)
            ) / total_all_credits,
            3,
        )
    else:
        cgpa = 0.0

    # Semester selection for display: pick requested semester or latest available
    selected_semester = request.GET.get("semester")
    if selected_semester:
        selected_semester = int(selected_semester)
        marks_selected = [m for m in best_marks if m.semester.number == selected_semester]
    else:
        # choose latest semester present in best_marks; fallback to student's semester if none
        if best_marks:
            latest_sem = max(m.semester.number for m in best_marks)
        else:
            latest_sem = getattr(student, "semester", None) or 0
        selected_semester = latest_sem
        marks_selected = [m for m in best_marks if m.semester.number == selected_semester]

    # Render using the same template variables as before
    return render(request, "student_dashboard.html", {
        "student": student,
        "cgpa": cgpa,
        "total_papers": total_papers,
        "passed": passed,
        "failed": failed,
        "sgpa_labels": sgpa_labels,
        "sgpa_values": sgpa_values,
        "marks": marks_selected,          # only best marks for the chosen semester
        "semesters": semesters,
        "selected_semester": selected_semester,
    })



@login_required
def user_logout(request):
    logout(request)
    return redirect("home")

@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def get_syllabus_by_course(request):

    course_id = request.GET.get("course")

    if not course_id:
        return JsonResponse({"syllabi": []})

    try:
        course_id = int(course_id)
    except ValueError:
        return JsonResponse({"syllabi": []})

    syllabi = Syllabus.objects.filter(
        course_id=course_id
    ).order_by("year")

    return JsonResponse({
        "syllabi": [
            {"id": s.id, "year": s.year}
            for s in syllabi
        ]
    })



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def add_student(request):

    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            student = form.save(commit=False)
            student.course = student.course_ref.name


            # Semester calculation
            start_year = int(student.academic_year.split("-")[0])
            current_year = date.today().year
            years_passed = current_year - start_year
            student.semester = (years_passed * 2) + 1

            # Restrict department automatically
            if not request.user.is_superuser:
                student.department = request.user.teacher.department

            student.save()
            return redirect("student_success", student_name=student.name)

    else:
        form = StudentForm(user=request.user)

    return render(request, "add_student.html", {"form": form})






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
                if request.user.is_superuser:
                    student = Student.objects.get(reg_no__iexact=reg_no)
                else:
                    student = Student.objects.get(
        reg_no__iexact=reg_no,
        department=request.user.teacher.department
    )


                
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
            if request.user.is_superuser:
                student = Student.objects.get(reg_no__iexact=reg_no)
            else:
                student = Student.objects.get(
        reg_no__iexact=reg_no,
        department=request.user.teacher.department
    )

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

    if not request.user.is_superuser:
        if student.department != request.user.teacher.department:
            return redirect("teacher_dashboard")

    try:
        sem_num_int = int(sem_number)
    except (TypeError, ValueError):
        sem_num_int = sem_number

    semester, _ = Semester.objects.get_or_create(
        student=student,
        number=sem_num_int
    )

    # ---------------------------------------------------------
    # GET ALL SUBJECTS FOR THIS SYLLABUS + SEMESTER
    # ---------------------------------------------------------
    all_subjects = Subject.objects.filter(
        syllabus=student.syllabus,
        semester_number=semester.number
    ).order_by("code")

    # ---------------------------------------------------------
# STEP 1: Supply → Show subject selection page first
# ---------------------------------------------------------
    if attempt_type == "Supply/Improvement":
        selected_subject_ids = request.GET.getlist("subjects")

    # If no subjects selected yet → show selection page
    if not selected_subject_ids:
        # Only show subjects that already have marks (attempted before)
        previous_subject_ids = Mark.objects.filter(
            semester=semester
        ).values_list("subject_id", flat=True)

        supply_subjects = all_subjects.filter(id__in=previous_subject_ids)

        return render(request, "select_supply_subjects.html", {
            "student": student,
            "semester": sem_num_int,
            "subjects": supply_subjects
        })

    # If subjects selected → filter them
    selected_subject_ids = [int(s) for s in selected_subject_ids]
    all_subjects = all_subjects.filter(id__in=selected_subject_ids)

    if not all_subjects.exists():
        return render(request, "add_marks_no_subjects.html", {
            "student": student,
            "semester": sem_num_int,
            "message": "No subjects found for this syllabus and semester."
        })

    # ---------------------------------------------------------
    # SPLIT CORE & ELECTIVES
    # ---------------------------------------------------------
    core_subjects = all_subjects.filter(
        elective_group__isnull=True
    ) | all_subjects.filter(
        elective_group=""
    )

    elective_subjects = all_subjects.exclude(
        elective_group__isnull=True
    ).exclude(
        elective_group=""
    )

    elective_groups = defaultdict(list)

    for subject in elective_subjects:
        elective_groups[subject.elective_group].append(subject)

    # ---------------------------------------------------------
    # PREVENT DUPLICATE REGULAR ENTRY
    # ---------------------------------------------------------
    if attempt_type == "Regular":
        existing = Mark.objects.filter(semester=semester).exists()
        if existing:
            return render(request, "add_marks_already_exists.html", {
                "student": student,
                "semester": sem_num_int,
                "attempt_type": attempt_type
            })

    # ---------------------------------------------------------
    # HANDLE AJAX POST
    # ---------------------------------------------------------
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":

        errors = {}
        saved_count = 0

        # Subjects that will actually be saved
        subjects_to_save = list(core_subjects)

        # Add selected electives
        for group in elective_groups.keys():
            selected_subject_id = request.POST.get(f"elective_{group}")
            if selected_subject_id:
                try:
                    selected_subject = Subject.objects.get(id=int(selected_subject_id))
                    subjects_to_save.append(selected_subject)
                except Subject.DoesNotExist:
                    pass

        for subject in subjects_to_save:
            try:
                marks_str = request.POST.get(f"marks_{subject.id}") or request.POST.get(f"new_marks_{subject.id}")

                if marks_str is None:
                    continue

                new_mark = float(marks_str)
                max_marks = float(getattr(subject, "max_marks", 0) or 0)

                if attempt_type == "Supply/Improvement":
                    last_attempt = Mark.objects.filter(
                        semester=semester,
                        subject=subject
                    ).order_by("-attempt_no").first()

                    attempt_no = (last_attempt.attempt_no + 1) if last_attempt else 1

                    Mark.objects.create(
                        semester=semester,
                        subject=subject,
                        marks_obtained=new_mark,
                        max_marks=max_marks,
                        attempt_type=attempt_type,
                        attempt_no=attempt_no,
                    )
                else:
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

                    if not created:
                        mark.marks_obtained = new_mark
                        mark.max_marks = max_marks
                        mark.attempt_type = attempt_type
                        mark.save()

                saved_count += 1

            except Exception as e:
                errors[subject.name] = str(e)

        if errors:
            return JsonResponse({
                "success": False,
                "message": "Some marks failed to save.",
                "errors": errors
            })

        return JsonResponse({
    "success": True,
    "redirect_url": reverse("marks_success", args=[student.name])
})
    # ---------------------------------------------------------
    # PRELOAD EXISTING MARKS
    # ---------------------------------------------------------
    existing_marks = {
        m.subject.id: m
        for m in Mark.objects.filter(
            semester=semester,
            subject__in=all_subjects
        )
    }

    template = "add_marks_supply.html" if attempt_type == "Supply/Improvement" else "add_marks_single.html"

    return render(request, template, {
    "student": student,
    "semester": sem_num_int,
    "subjects": all_subjects,   # ✅ ADD THIS
    "core_subjects": core_subjects,
    "elective_groups": dict(elective_groups),
    "existing_marks": existing_marks,
    "attempt_type": attempt_type
})


@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def marks_success(request, student_name):
    return render(request, "marks_success.html", {"student_name": student_name})




@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def get_subjects_for_semester(request):
    sem_number = request.GET.get("semester")
    course = request.GET.get("course")
    subjects = Subject.objects.all()
    if sem_number:
        try:
            sem_int = int(sem_number)
            subjects = subjects.filter(semester_number=sem_int)
        except ValueError:
            subjects = subjects.none()

    if course:
        subjects = subjects.filter(course__iexact=course)

    subjects = subjects.order_by("name")
    data = [{"id": s.id, "name": s.name, "code": s.code} for s in subjects]
    return JsonResponse({"subjects": data})



@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser or is_hod(u))

def manage_subjects(request):
    subjects = Subject.objects.select_related("syllabus")

    if is_hod(request.user):
        subjects = subjects.filter(
        course_ref__department=request.user.teacher.department
    )

    subjects = subjects.order_by("course", "syllabus__year", "semester_number")



    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("manage_subjects")
    else:
        form = SubjectForm()

    return render(request, "manage_subjects.html", {"subjects": subjects, "form": form})



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_superuser or is_hod(u))
def edit_subject(request, subject_id):

    subject = get_object_or_404(Subject, id=subject_id)

    if not request.user.is_superuser:
        if subject.course_ref.department != request.user.teacher.department:
            return redirect("teacher_dashboard")

    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()

            url = reverse("manage_subjects_by_course",
                          args=[subject.course_ref.name])
            return HttpResponseRedirect(
                f"{url}?syllabus={subject.syllabus_id}"
            )
    else:
        form = SubjectForm(instance=subject)

    return render(request, "edit_subject.html", {
        "form": form,
        "subject": subject
    })




@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_superuser or is_hod(u))
def delete_subject(request, subject_id):

    subject = get_object_or_404(Subject, id=subject_id)

    if not request.user.is_superuser:
        if subject.course_ref.department != request.user.teacher.department:
            return redirect("teacher_dashboard")

    course_name = subject.course_ref.name
    syllabus_id = subject.syllabus_id

    subject.delete()

    url = reverse("manage_subjects_by_course",
                  args=[course_name])

    return HttpResponseRedirect(
        f"{url}?syllabus={syllabus_id}"
    )




@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser or is_hod(u))
def select_course(request):
    # Admin → all courses
    if request.user.is_superuser:
        courses = Course.objects.all().order_by("name")

    # HOD → only own department courses
    else:
        courses = Course.objects.filter(
            department=request.user.teacher.department
        ).order_by("name")

    if request.method == "POST":
        selected_course = request.POST.get("course")
        if selected_course:
            return redirect(
                "manage_subjects_by_course",
                course=selected_course
            )

    return render(request, "select_course.html", {
        "courses": courses
    })




@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser or is_hod(u))
def manage_subjects_by_course(request, course_id):


    # Get actual Course object
    course_obj = get_object_or_404(Course, id=course_id)

    # HOD safety check
    if is_hod(request.user):
        if course_obj.department != request.user.teacher.department:
            return redirect("teacher_dashboard")

    syllabus_id = request.GET.get("syllabus")

    if not syllabus_id:
        messages.error(request, "Please select syllabus year")
        return redirect("select_course")

    subjects = Subject.objects.filter(
    course_ref=course_obj,
    syllabus_id=syllabus_id
).order_by("semester_number", "code")

    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)

            # 🔥 FORCE COURSE FK
            subject.course_ref = course_obj
            subject.course = course_obj.name  # keep string field in sync
            subject.syllabus_id = syllabus_id

            subject.save()

        return redirect(
    reverse("manage_subjects_by_course", args=[course_obj.id]) +
    f"?syllabus={syllabus_id}"
)

    else:
        form = SubjectForm(initial={
            "course_ref": course_obj
        })

    return render(request, "manage_subjects.html", {
        "subjects": subjects,
        "form": form,
        "selected_course": course_obj,
        "syllabus_id": syllabus_id,
    })





@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def student_search(request):
    students = []
    query = request.GET.get("q")
    if query:
        if request.user.is_superuser:
            students = Student.objects.filter(reg_no__icontains=query)
        else:
            students = Student.objects.filter(
        reg_no__icontains=query,
        department=request.user.teacher.department
    )

    return render(request, "student_search.html", {"students": students})
    

@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if not request.user.is_superuser:
        if student.department != request.user.teacher.department:
            return redirect("teacher_dashboard")


    # ✅ Get all marks for the student
    all_marks = Mark.objects.filter(semester__student=student).select_related("subject", "semester")

    # ✅ Group marks by subject and pick the highest marks_obtained
    best_marks = []
    subject_best_map = defaultdict(lambda: None)

    for mark in all_marks:
        current_best = subject_best_map[mark.subject]
        if current_best is None or mark.marks_obtained > current_best.marks_obtained:
            subject_best_map[mark.subject] = mark

    best_marks = list(subject_best_map.values())

    # Compute pass/fail for display
    for m in best_marks:
        m.passed = m.marks_obtained >= (0.4 * m.max_marks)
        m.attempt_count = Mark.objects.filter(semester__student=student, subject=m.subject).count()

    total_papers = len(best_marks)
    passed = sum(1 for m in best_marks if m.passed)
    failed = total_papers - passed

    # ✅ SGPA and CGPA using best marks only
    semesters = sorted({m.semester.number for m in best_marks})
    sgpa_values, sgpa_labels = [], []
    semester_credit_map = {}

    for sem in semesters:
        sem_marks = [m for m in best_marks if m.semester.number == sem]
        if sem_marks:
            total_credits = sum((m.subject.credits or 0) for m in sem_marks)
            total_credit_points = 0
            for m in sem_marks:
                gp = (m.marks_obtained / m.max_marks) * 10 if m.max_marks > 0 else 0
                total_credit_points += gp * (m.subject.credits or 0)
            sgpa = round(total_credit_points / total_credits, 3) if total_credits > 0 else 0
            sgpa_values.append(sgpa)
            sgpa_labels.append(f"Sem {sem}")
            semester_credit_map[sem] = total_credits
        else:
            sgpa_values.append(0)
            sgpa_labels.append(f"Sem {sem}")
            semester_credit_map[sem] = 0

    total_all_credits = sum(semester_credit_map.values())
    if total_all_credits > 0:
        cgpa = round(
            sum(
                sgpa * semester_credit_map.get(sem, 0)
                for sgpa, sem in zip(sgpa_values, semesters)
            ) / total_all_credits,
            3,
        )
    else:
        cgpa = 0.0

    # ✅ Semester filter for display
    selected_semester = request.GET.get("semester")
    if selected_semester:
        selected_semester = int(selected_semester)
        marks = [m for m in best_marks if m.semester.number == selected_semester]
    else:
        marks = best_marks

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


@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def view_all_attempts(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if not request.user.is_superuser:
        if student.department != request.user.teacher.department:
            return redirect("teacher_dashboard")


    # Get all marks for that student, ordered by subject then attempt_no
    all_marks = (
        Mark.objects.filter(semester__student=student)
        .select_related("subject", "semester")
        .order_by("subject__name", "attempt_no")
    )

    # Group marks by subject and add computed fields
    subject_attempts = defaultdict(list)
    for mark in all_marks:
        # compute pass/fail (40% of max_marks). guard against zero max_marks.
        try:
            max_m = float(mark.max_marks or 0)
            obtained = float(mark.marks_obtained or 0)
            mark.passed = (max_m > 0) and (obtained >= 0.4 * max_m)
        except Exception:
            mark.passed = False

        # optional: format values for display if you want strings:
        # mark.marks_display = f"{obtained:.2f}"
        # mark.max_display = f"{max_m:.2f}"

        subject_attempts[mark.subject].append(mark)

    return render(request, "view_all_attempts.html", {
        "student": student,
        "subject_attempts": dict(subject_attempts)
    })

@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def subject_attempt_history(request, student_id, subject_id):
    student = get_object_or_404(Student, id=student_id)
    subject = get_object_or_404(Subject, id=subject_id)

    if not request.user.is_superuser:
        if student.department != request.user.teacher.department:
            return redirect("teacher_dashboard")


    # Get all attempts for that student and subject
    attempts = (
        Mark.objects.filter(semester__student=student, subject=subject)
        .select_related("semester", "subject")
        .order_by("attempt_no")
    )

    # Compute pass/fail for each attempt
    for mark in attempts:
        try:
            mark.passed = (mark.max_marks > 0) and (mark.marks_obtained >= 0.4 * mark.max_marks)
        except Exception:
            mark.passed = False

    return render(request, "subject_attempt_history.html", {
        "student": student,
        "subject": subject,
        "attempts": attempts
    })



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def teacher_students_filter(request):
    """
    Teacher dashboard — student filtering:
      - by syllabus year (NEW)
      - by semester
      - subjects shown change to only those for selected syllabus + semester
      - filter students by pass/fail in a specific subject
      - plus other student-level filters
    """

    # ==========================
    # Dropdown / filter options
    # ==========================
    semesters_numbers = (
        Semester.objects.values_list("number", flat=True)
        .distinct()
        .order_by("number")
    )

    academic_years = Student.objects.values_list(
        "academic_year", flat=True
    ).distinct().order_by("academic_year")

    genders = Student.objects.values_list("gender", flat=True).distinct()
    castes = Student.objects.values_list("caste", flat=True).distinct()
    religions = Student.objects.values_list("religion", flat=True).distinct()
    courses = Student.objects.values_list("course", flat=True).distinct()

    syllabi = Syllabus.objects.all().order_by("course", "year")

    # ==========================
    # GET parameters
    # ==========================
    semester_number = request.GET.get("semester")
    subject_id = request.GET.get("subject")
    subject_status = request.GET.get("subject_status")
    academic_year = request.GET.get("academic_year")
    gender = request.GET.get("gender")
    caste = request.GET.get("caste")
    religion = request.GET.get("religion")
    course = request.GET.get("course")
    syllabus_id = request.GET.get("syllabus")
    reg_no = request.GET.get("reg_no")
    pass_status = request.GET.get("pass_status")

    # ==========================
    # Base student queryset
    # ==========================
    students_qs = Student.objects.select_related("syllabus")

    if not request.user.is_superuser:
        students_qs = students_qs.filter(
        department=request.user.teacher.department
    )

    students_qs = students_qs.order_by("name")

    

    # ==========================
    # Student-level filters
    # ==========================
    if syllabus_id:
        students_qs = students_qs.filter(syllabus_id=syllabus_id)

    if academic_year:
        students_qs = students_qs.filter(academic_year=academic_year)

    if gender:
        students_qs = students_qs.filter(gender__iexact=gender)

    if caste:
        students_qs = students_qs.filter(caste__iexact=caste)

    if religion:
        students_qs = students_qs.filter(religion__iexact=religion)

    if course:
        students_qs = students_qs.filter(
        Q(course__iexact=course) |
        Q(course_ref__name__iexact=course)
    )


    if reg_no:
        students_qs = students_qs.filter(reg_no__icontains=reg_no)

    # ==========================
    # Subject dropdown (syllabus-safe)
    # ==========================
    subjects_for_sem = Subject.objects.none()

    if semester_number and syllabus_id:
        try:
            sem_int = int(semester_number)
            subjects_for_sem = Subject.objects.filter(
    semester_number=sem_int,
    syllabus_id=syllabus_id
).filter(
    Q(course_ref__isnull=False) | Q(course__isnull=False)
).order_by("name")

        except ValueError:
            subjects_for_sem = Subject.objects.none()

    # ==========================
    # Subject-level pass/fail filter
    # ==========================
    subject_student_ids_to_keep = None

    if subject_id:
        try:
            subject_id = int(subject_id)
        except ValueError:
            subject_id = None

    if subject_id and semester_number and syllabus_id:
        marks_qs = Mark.objects.filter(
            semester__number=sem_int,
            semester__student__syllabus_id=syllabus_id,
            subject_id=subject_id
        )

        passed_ids = set()
        failed_ids = set()

        for m in marks_qs:
            try:
                if m.max_marks and m.marks_obtained >= 0.4 * m.max_marks:
                    passed_ids.add(m.semester.student_id)
                else:
                    failed_ids.add(m.semester.student_id)
            except Exception:
                failed_ids.add(m.semester.student_id)

        if subject_status == "passed":
            subject_student_ids_to_keep = passed_ids
        elif subject_status == "failed":
            subject_student_ids_to_keep = failed_ids
        else:
            subject_student_ids_to_keep = set(
                m.semester.student_id for m in marks_qs
            )

        students_qs = students_qs.filter(
            id__in=list(subject_student_ids_to_keep)
        )

    # ==========================
    # Build final student list
    # ==========================
    students = []

    for s in students_qs:
        marks = Mark.objects.filter(
            semester__student=s
        )

        if marks.exists():
            total_max = sum(m.max_marks for m in marks)
            total_obt = sum(m.marks_obtained for m in marks)
            avg_percent = (
                round((total_obt / total_max) * 100, 2)
                if total_max > 0 else None
            )
            overall_pass = all(
                m.marks_obtained >= 0.4 * m.max_marks
                for m in marks
            )
        else:
            avg_percent = None
            overall_pass = False

        if pass_status == "passed" and not overall_pass:
            continue
        if pass_status == "failed" and overall_pass:
            continue

        # Subject-specific info (for table display)
        subject_pass_info = None

        if subject_id and semester_number and syllabus_id:
            subj_mark = Mark.objects.filter(
                semester__student=s,
                semester__student__syllabus_id=syllabus_id,
                semester__number=sem_int,
                subject_id=subject_id
            ).order_by("-id").first()

            if subj_mark:
                maxm = subj_mark.max_marks or 0
                got = subj_mark.marks_obtained or 0
                subject_pass_info = (
                    got >= 0.4 * maxm if maxm > 0 else False
                )

                s.subject_marks = got
                s.subject_max = maxm
            else:
                s.subject_marks = None
                s.subject_max = None

        s.total_papers = marks.count()
        s.avg_percent = avg_percent
        s.overall_pass = overall_pass
        s.subject_pass_info = subject_pass_info

        students.append(s)

    # ==========================
    # Context
    # ==========================
    context = {
        "students": students,
        "semesters_numbers": semesters_numbers,
        "subjects_for_sem": subjects_for_sem,
        "academic_years": academic_years,
        "genders": [g for g in genders if g],
        "castes": [c for c in castes if c],
        "religions": [r for r in religions if r],
        "courses": [c for c in courses if c],
        "syllabi": syllabi,
        "filter_values": {
            "semester": semester_number,
            "subject": subject_id,
            "subject_status": subject_status,
            "academic_year": academic_year,
            "gender": gender,
            "caste": caste,
            "religion": religion,
            "course": course,
            "syllabus": syllabus_id,
            "reg_no": reg_no,
            "pass_status": pass_status,
        }
    }

    return render(request, "teacher_students_filter.html", context)



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def grace_marks(request):
    if request.method == "POST":
        reg_no = request.POST.get("reg_no")
        sem_number = request.POST.get("semester")

        try:
            student = Student.objects.get(reg_no__iexact=reg_no)
        except Student.DoesNotExist:
            messages.error(request, "Student not found")
            return redirect("grace_marks")

        return redirect("apply_grace_marks", student_id=student.id, sem_number=sem_number)

    return render(request, "grace_marks_select.html")

@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def apply_grace_marks(request, student_id, sem_number):
    """
    Load only the latest mark record per subject for the given student's semester,
    then allow per-subject percentage-of-semester-total grace addition.
    """
    student = get_object_or_404(Student, id=student_id)
    semester = get_object_or_404(Semester, student=student, number=sem_number)

    # All mark rows for the semester (we'll pick the latest per subject)
    all_marks_qs = Mark.objects.filter(semester=semester).select_related("subject")

    # Get distinct subject ids present in marks for this semester
    subject_ids = list(all_marks_qs.values_list('subject_id', flat=True).distinct())

    latest_marks = []
    for sid in subject_ids:
        # Prefer ordering by a timestamp if available, otherwise fall back to id
        # This is robust across DB backends (no DISTINCT ON).
        if hasattr(Mark, 'created_at'):  # use created_at if your model has it
            latest = all_marks_qs.filter(subject_id=sid).order_by('-created_at').first()
        elif hasattr(Mark, 'updated_at'):
            latest = all_marks_qs.filter(subject_id=sid).order_by('-updated_at').first()
        else:
            # fallback: use id as proxy for "latest"
            latest = all_marks_qs.filter(subject_id=sid).order_by('-id').first()

        if latest:
            latest_marks.append(latest)

    # compute semester total max using only the latest marks (per subject)
    total_sem_max = sum((m.max_marks or 0) for m in latest_marks)

    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            updated = []
            for m in latest_marks:
                raw_percent = request.POST.get(f"percent_{m.id}", "").strip()
                if raw_percent == "":
                    continue
                try:
                    percent = float(raw_percent)
                except ValueError:
                    percent = 0.0

                # Grace added is percent% of semester total max (as you requested)
                grace_to_add = (total_sem_max * percent) / 100.0
                grace_to_add = round(grace_to_add, 2)

                new_marks = m.marks_obtained + grace_to_add
                # Optional: cap at subject max
                # new_marks = min(new_marks, m.max_marks)

                old_marks = float(m.marks_obtained)
                m.marks_obtained = new_marks
                m.save()

                updated.append({
                    "mark_id": m.id,
                    "subject": m.subject.name,
                    "old_marks": old_marks,
                    "percent": percent,
                    "grace_added": grace_to_add,
                    "new_marks": new_marks
                })

            return JsonResponse({"success": True, "updated": updated})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # GET: render page using only latest_marks
    return render(request, "apply_grace_marks.html", {
        "student": student,
        "semester": semester,
        "marks": latest_marks,
        "total_sem_max": total_sem_max,
    })



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def ajax_get_student(request):
    reg_no = request.GET.get('reg_no', '').strip()

    if not reg_no:
        return JsonResponse({'success': False, 'message': 'Provide registration number.'})

    try:
        if request.user.is_superuser:
            student = Student.objects.get(reg_no__iexact=reg_no)
        else:
            student = Student.objects.get(
                reg_no__iexact=reg_no,
                department=request.user.teacher.department
            )

        return JsonResponse({
            'success': True,
            'student': {
                'id': student.id,
                'name': student.name
            }
        })

    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student not found.'})

@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def ajax_create_syllabus(request):

    if request.method != "POST":
        return JsonResponse({"success": False})

    course_id = request.POST.get("course")  # this must now be ID
    year = request.POST.get("year")

    if not course_id or not year:
        return JsonResponse({"success": False, "error": "Missing data"})

    try:
        course_obj = Course.objects.get(id=int(course_id))
        year = int(year)
    except (ValueError, Course.DoesNotExist):
        return JsonResponse({"success": False, "error": "Invalid data"})

    syllabus, created = Syllabus.objects.get_or_create(
        course=course_obj,
        year=year
    )

    return JsonResponse({
        "success": True,
        "id": syllabus.id,
        "year": syllabus.year,
        "created": created,
    })



@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_superuser)
def admin_department_analysis(request):
    from .models import Department

    departments = Department.objects.all()
    data = []

    for dept in departments:
        students = Student.objects.filter(department=dept)
        marks = Mark.objects.filter(semester__student__department=dept)

        total_students = students.count()

        if marks.exists():
            avg_percent = round(
                sum(m.marks_obtained for m in marks) /
                sum(m.max_marks for m in marks) * 100,
                2
            )
            passed_students = 0

        for student in students:
            student_marks = Mark.objects.filter(semester__student=student)

            if student_marks.exists() and all(
                m.marks_obtained >= 0.4 * m.max_marks for m in student_marks
    ):
                passed_students += 1

                pass_rate = round(
    (passed_students / total_students) * 100,
    2
) if total_students > 0 else 0

        else:
            avg_percent = 0
            pass_rate = 0

        data.append({
            "department": dept.name,
             "department_id": dept.id,
            "students": total_students,
            "avg_percent": avg_percent,
            "pass_rate": pass_rate
        })

    return render(request, "admin_department_analysis.html", {
        "data": data
    })


@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def admin_department_students(request, department_id):
    department = get_object_or_404(Department, id=department_id)

    students = (
        Student.objects
        .filter(department=department)
        .select_related("syllabus")
        .order_by("name")
    )

    student_data = []

    for s in students:
        marks = Mark.objects.filter(semester__student=s)

        if marks.exists():
            overall_pass = all(
                m.marks_obtained >= 0.4 * m.max_marks
                for m in marks
            )
        else:
            overall_pass = False

        student_data.append({
            "student": s,
            "cgpa": s.cgpa(),
            "overall_pass": overall_pass,
        })

    return render(request, "admin_department_students.html", {
        "department": department,
        "students": student_data
    })

@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def add_teacher(request):
    if request.method == "POST":
        form = TeacherCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                is_staff=True
            )

            Teacher.objects.create(
    user=user,
    full_name=form.cleaned_data["full_name"],
    department=form.cleaned_data["department"],
    role=form.cleaned_data["role"]   # ✅ NEW
)


            messages.success(request, "Teacher added successfully")
            return redirect("admin_dashboard")
    else:
        form = TeacherCreateForm()

    return render(request, "add_teacher.html", {"form": form})


@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == "POST":
        form = TeacherEditForm(request.POST)
        if form.is_valid():
            teacher.full_name = form.cleaned_data["full_name"]
            teacher.department = form.cleaned_data["department"]
            teacher.save()

            messages.success(request, "Teacher updated successfully")
            return redirect("admin_dashboard")
    else:
        form = TeacherEditForm(initial={
            "full_name": teacher.full_name,
            "department": teacher.department
        })

    return render(request, "edit_teacher.html", {
        "form": form,
        "teacher": teacher
    })

@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def manage_departments(request):
    departments = Department.objects.all().order_by("name")
    return render(request, "manage_departments.html", {
        "departments": departments
    })

@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def add_department(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Department.objects.create(name=name)
            messages.success(request, "Department added successfully")
            return redirect("manage_departments")
        messages.error(request, "Department name is required")

    return render(request, "add_department.html")

@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def edit_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            department.name = name
            department.save()
            messages.success(request, "Department updated successfully")
            return redirect("manage_departments")
        messages.error(request, "Department name is required")

    return render(request, "edit_department.html", {
        "department": department
    })

@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def manage_department_courses(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    courses = department.courses.all().order_by("name")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Course.objects.get_or_create(
                department=department,
                name=name
            )
            messages.success(request, "Course added successfully")
            return redirect("manage_department_courses", department_id=department.id)
        messages.error(request, "Course name is required")

    return render(request, "manage_department_courses.html", {
        "department": department,
        "courses": courses
    })

@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            course.name = name
            course.save()
            messages.success(request, "Course updated successfully")
            return redirect(
                "manage_department_courses",
                department_id=course.department.id
            )
        messages.error(request, "Course name is required")

    return render(request, "edit_course.html", {
        "course": course
    })


@login_required(login_url="teacher_login")
@user_passes_test(lambda u: u.is_superuser)
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    department_id = course.department.id

    if request.method == "POST":
        course.delete()
        messages.success(request, "Course deleted successfully")
        return redirect(
            "manage_department_courses",
            department_id=department_id
        )

    return render(request, "delete_course.html", {
        "course": course
    })



@student_required
def download_student_report(request):
    student_id = request.session.get("student_id")
    student = get_object_or_404(Student, id=student_id)

    marks = Mark.objects.filter(semester__student=student).order_by("semester__number")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.name}_Marks_Report.pdf"'

    doc = SimpleDocTemplate(response)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]

    elements.append(Paragraph("Student Marks Report", title_style))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Name: {student.name}", styles["Normal"]))
    elements.append(Paragraph(f"Registration No: {student.reg_no}", styles["Normal"]))
    elements.append(Paragraph(f"Course: {student.course}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    # Table data
    data = [["Semester", "Subject", "Marks Obtained", "Max Marks", "Status"]]

    for m in marks:
        passed = "Pass" if m.marks_obtained >= (0.4 * m.max_marks) else "Fail"
        data.append([
            m.semester.number,
            m.subject.name,
            m.marks_obtained,
            m.max_marks,
            passed
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (2,1), (-2,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
    ]))

    elements.append(table)

    doc.build(elements)
    return response