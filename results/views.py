from collections import defaultdict
from django.db.models import Max

from datetime import date
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg,Q
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Student, Mark,Teacher,Subject,Semester
from .forms import StudentForm, MarkForm,MarksEntryForm,SubjectForm
from django.contrib.auth.decorators import login_required, user_passes_test
from collections import defaultdict



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

@login_required(login_url='teacher_login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def add_marks_single_page(request):
    """
    Full view supporting:
     - Regular attempts (prevent duplicate entries)
     - Supply/Improvement attempts with a subject-selection step (GET -> select_supply_subjects.html)
     - Robust subject lookup (course fk or string), and semester-only fallback
     - AJAX POST handler returning JSON
    """
    student_id = request.GET.get("student_id")
    sem_number = request.GET.get("semester")
    attempt_type = request.GET.get("attempt_type", "Regular")

    if not student_id or not sem_number:
        return redirect("teacher_dashboard")

    student = get_object_or_404(Student, id=student_id)

    # Normalize semester number to int if possible (keeps behavior consistent)
    try:
        sem_num_int = int(sem_number)
    except (TypeError, ValueError):
        sem_num_int = sem_number

    semester, _ = Semester.objects.get_or_create(student=student, number=sem_num_int)

    # ---------- Supply/Improvement selection step (GET) ----------
    # If teacher is attempting Supply/Improvement and no subjects are provided in querystring,
    # show the selection page so they can pick which subjects to attempt.
    if attempt_type == "Supply/Improvement" and request.method != "POST":
        selected_subject_ids = request.GET.getlist("subjects")
        if not selected_subject_ids:
            # Build candidate list using same robust logic as below
            candidate_qs = Subject.objects.none()
            student_course = getattr(student, "course", None)
            if student_course is not None:
                if hasattr(student_course, "id"):
                    candidate_qs = Subject.objects.filter(course__id=student_course.id, semester_number=semester.number)
                else:
                    candidate_qs = Subject.objects.filter(course__iexact=str(student_course), semester_number=semester.number)

            if not candidate_qs.exists():
                candidate_qs = Subject.objects.filter(semester_number=semester.number)

            return render(request, "select_supply_subjects.html", {
                "student": student,
                "semester": sem_num_int,
                "subjects": candidate_qs,
                "attempt_type": attempt_type,
            })

    # ---------- Determine selected subjects (GET or POST) ----------
    selected_subject_ids = request.GET.getlist("subjects") or request.POST.getlist("selected_subjects")

    # If specific subjects were selected, use them (preserves teacher choice)
    if selected_subject_ids:
        subjects_qs = Subject.objects.filter(id__in=selected_subject_ids).order_by('id')
    else:
        # Robust subject lookup: try course FK -> course string (iexact) -> fallback to semester-only
        student_course = getattr(student, "course", None)
        subjects_qs = Subject.objects.none()

        if student_course is not None:
            if hasattr(student_course, "id"):
                subjects_qs = Subject.objects.filter(course__id=student_course.id, semester_number=semester.number)
            else:
                subjects_qs = Subject.objects.filter(course__iexact=str(student_course), semester_number=semester.number)

        if not subjects_qs.exists():
            subjects_qs = Subject.objects.filter(semester_number=semester.number)

    # Debug print (optional) - replace with logger.debug in production
    print(f"[add_marks_single_page] student={student.id} course={repr(getattr(student, 'course', None))} sem={semester.number} subjects_count={subjects_qs.count()}")

    # If still no subjects, show a friendly page explaining next steps
    if not subjects_qs.exists():
        return render(request, "add_marks_no_subjects.html", {
            "student": student,
            "semester": sem_num_int,
            "message": "No subjects found for this student & semester. Ensure student's course is set and subjects are created for that course/semester."
        })

    # ---------- Prevent duplicate entries for Regular attempt ----------
    if attempt_type == "Regular":
        existing = Mark.objects.filter(semester=semester).exists()
        if existing:
            return render(request, "add_marks_already_exists.html", {
                "student": student,
                "semester": sem_num_int,
                "attempt_type": attempt_type
            })

    # ---------- Handle AJAX POST submission ----------
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        errors = {}
        saved_count = 0

        for subject in subjects_qs:
            try:
                # Accept either marks_<id> (add form) or new_marks_<id> (alternate naming)
                marks_str = request.POST.get(f"marks_{subject.id}") or request.POST.get(f"new_marks_{subject.id}")
                max_str = request.POST.get(f"max_{subject.id}")

                if marks_str is None or max_str is None:
                    raise ValueError("Missing marks or max marks")

                new_mark = float(marks_str)
                max_marks = float(max_str)

                if attempt_type == "Supply/Improvement":
                    # Always create a new record for supply/improvement with incremented attempt_no
                    last_attempt = Mark.objects.filter(semester=semester, subject=subject).order_by("-attempt_no").first()
                    attempt_no = (last_attempt.attempt_no + 1) if last_attempt else 1
                    Mark.objects.create(
                        semester=semester,
                        subject=subject,
                        marks_obtained=new_mark,
                        max_marks=max_marks,
                        attempt_type=attempt_type,
                        attempt_no=attempt_no,
                    )
                    saved_count += 1
                else:
                    # Regular: create or update existing single record
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

        # Return JSON response matching prior behavior
        if errors:
            return JsonResponse({
                "success": False,
                "message": "Some marks failed to save.",
                "errors": errors
            })
        else:
            return JsonResponse({
                "success": True,
                "message": f"{attempt_type} marks saved successfully for {saved_count} subjects!"
            })

    # Preload existing marks for display (if any) so template can show them
    existing_marks = {m.subject.id: m for m in Mark.objects.filter(semester=semester, subject__in=subjects_qs)}

    template = "add_marks_supply.html" if attempt_type == "Supply/Improvement" else "add_marks_single.html"
    return render(request, template, {
        "student": student,
        "semester": sem_num_int,
        "subjects": subjects_qs,
        "existing_marks": existing_marks,
        "attempt_type": attempt_type
    })





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
      - by semester (select semester)
      - subjects shown change to only those for selected semester
      - filter students by pass/fail in a specific subject of that semester
      - plus other student-level filters (academic_year, gender, caste, religion, course, reg_no)
    """
    # Filter option data for form selects
    semesters_numbers = Semester.objects.values_list('number', flat=True).distinct().order_by('number')
    academic_years = Student.objects.values_list('academic_year', flat=True).distinct().order_by('academic_year')
    genders = Student.objects.values_list('gender', flat=True).distinct()
    castes = Student.objects.values_list('caste', flat=True).distinct()
    religions = Student.objects.values_list('religion', flat=True).distinct()
    courses = Student.objects.values_list('course', flat=True).distinct()

    # GET params
    semester_number = request.GET.get('semester')         # expected as string or None
    subject_id = request.GET.get('subject')               # subject id (from selected semester)
    subject_status = request.GET.get('subject_status')    # 'passed', 'failed', or None
    academic_year = request.GET.get('academic_year')
    gender = request.GET.get('gender')
    caste = request.GET.get('caste')
    religion = request.GET.get('religion')
    course = request.GET.get('course')
    reg_no = request.GET.get('reg_no')
    pass_status = request.GET.get('pass_status')          # existing overall pass/fail for all papers (optional)

    # Base student queryset
    students_qs = Student.objects.all().order_by('name')

    # apply simple student-level filters
    if academic_year:
        students_qs = students_qs.filter(academic_year=academic_year)
    if gender:
        students_qs = students_qs.filter(gender__iexact=gender)
    if caste:
        students_qs = students_qs.filter(caste__iexact=caste)
    if religion:
        students_qs = students_qs.filter(religion__iexact=religion)
    if course:
        students_qs = students_qs.filter(course__iexact=course)
    if reg_no:
        students_qs = students_qs.filter(reg_no__icontains=reg_no)

    # Prepare subjects list for the selected semester (for the template)
    if semester_number:
        try:
            sem_int = int(semester_number)
            if course:
                subjects_for_sem = Subject.objects.filter(semester_number=sem_int, course__iexact=course).order_by('name')
            else:
                subjects_for_sem = Subject.objects.filter(semester_number=sem_int).order_by('name')
        except ValueError:
            subjects_for_sem = Subject.objects.none()
    else:
    # if no semester selected, but course selected we can optionally show all subjects for course
        if course:
            subjects_for_sem = Subject.objects.filter(course__iexact=course).order_by('semester_number', 'name')
        else:
            subjects_for_sem = Subject.objects.none()

    # If subject filter is present, compute pass/fail sets for that subject in that semester
    # We'll identify student ids to keep depending on subject_status.
    subject_student_ids_to_keep = None  # None => don't apply subject-level filtering
    if subject_id:
        try:
            subject_id = int(subject_id)
        except ValueError:
            subject_id = None

    if subject_id and semester_number:
        # marks for that subject in that semester
        marks_qs = Mark.objects.filter(semester__number=sem_int, subject_id=subject_id)

        # Build sets of student ids who passed / failed this subject
        passed_ids = set()
        failed_ids = set()
        for m in marks_qs:
            try:
                # treat pass >= 40% of max_marks
                if m.max_marks and (m.marks_obtained >= 0.4 * m.max_marks):
                    passed_ids.add(m.semester.student_id)
                else:
                    failed_ids.add(m.semester.student_id)
            except Exception:
                failed_ids.add(m.semester.student_id)

        if subject_status == 'passed':
            subject_student_ids_to_keep = passed_ids
        elif subject_status == 'failed':
            subject_student_ids_to_keep = failed_ids
        else:
            # If no subject_status requested, keep all students who have marks for that subject
            subject_student_ids_to_keep = set(m.semester.student_id for m in marks_qs)

        # Intersect with current queryset
        if subject_student_ids_to_keep is not None:
            students_qs = students_qs.filter(id__in=list(subject_student_ids_to_keep))

    # If subject not specified but semester specified and pass_status (overall) filtering is requested,
    # we keep the earlier behavior where we compute pass/fail across all marks (optional)
    # (existing 'pass_status' param applies to whole student result, not subject-specific)
    students = []
    for s in students_qs:
        # Compute overall stats (useful for display)
        marks = Mark.objects.filter(semester__student=s)
        if marks.exists():
            total_max = sum(m.max_marks for m in marks)
            total_obt = sum(m.marks_obtained for m in marks)
            avg_percent = round((total_obt / total_max * 100), 2) if total_max > 0 else None
            overall_pass = all(m.marks_obtained >= 0.4 * m.max_marks for m in marks)
        else:
            avg_percent = None
            overall_pass = False

        # Apply overall pass_status filter if provided (this is separate from subject-specific filter)
        if pass_status == 'passed' and not overall_pass:
            continue
        if pass_status == 'failed' and overall_pass:
            continue

        # For convenience in template show whether the student passed/failed the selected subject (if any)
        subject_pass_info = None
        if subject_id and semester_number:
            # try to get the mark record for this student for that semester & subject
            subj_mark = Mark.objects.filter(semester__student=s, semester__number=sem_int, subject_id=subject_id).first()
            if subj_mark:
                try:
                    subject_pass_info = (subj_mark.marks_obtained >= 0.4 * subj_mark.max_marks)
                except Exception:
                    subject_pass_info = False
            else:
                subject_pass_info = None  # student had no mark record for this subject in that semester

        # attach safe attributes for template
        s.total_papers = marks.count()
        s.avg_percent = avg_percent
        s.overall_pass = overall_pass
        s.subject_pass_info = subject_pass_info  # True/False/None
        

        students.append(s)

    context = {
        'students': students,
        'semesters_numbers': semesters_numbers,
        'subjects_for_sem': subjects_for_sem,
        'academic_years': academic_years,
        'genders': [g for g in genders if g],
        'castes': [c for c in castes if c],
        'religions': [r for r in religions if r],
        'courses': [c for c in courses if c],
        'filter_values': {
            'semester': semester_number,
            'subject': subject_id,
            'subject_status': subject_status,
            'academic_year': academic_year,
            'gender': gender,
            'caste': caste,
            'religion': religion,
            'course': course,
            'reg_no': reg_no,
            'pass_status': pass_status,
        }
    }
    return render(request, "teacher_students_filter.html", context)
