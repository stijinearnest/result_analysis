from django.db import models
from django.contrib.auth.models import User


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class Student(models.Model):
    reg_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    dob = models.DateField()
    course = models.CharField(max_length=100, default="B.Sc Computer Science")
    semester = models.IntegerField(default=1)
    academic_year = models.CharField(max_length=20, default="2024-25")
    photo = models.ImageField(upload_to="students/", blank=True, null=True)

    def __str__(self):
        return f"{self.reg_no} - {self.name}"

    def cgpa(self):
        """
        CGPA = Weighted average of all semester SGPAs
        Formula:
        CGPA = Σ(SGPA × Semester Credits) / Σ(Semester Credits)
        """
        semesters = self.semesters.all().order_by("number")
        if not semesters.exists():
            return 0.0

        total_credits_all = 0.0
        weighted_sgpa_sum = 0.0

        for sem in semesters:
            sem_marks = sem.marks.all()
            sem_credits = sum((m.subject.credits or 0) for m in sem_marks)
            if sem_credits == 0:
                continue
            sem_sgpa = sem.sgpa()
            weighted_sgpa_sum += sem_sgpa * sem_credits
            total_credits_all += sem_credits

        if total_credits_all == 0:
            return 0.0

        cgpa = weighted_sgpa_sum / total_credits_all
        return round(cgpa, 3)

    def pass_fail_summary(self):
        """
        Returns a summary of total, passed, and failed subjects.
        A student passes if marks_obtained >= 40% of max_marks.
        """
        total = 0
        passed = 0
        failed = 0
        for sem in self.semesters.all():
            for mark in sem.marks.all():
                total += 1
                if mark.marks_obtained >= (0.4 * mark.max_marks):
                    passed += 1
                else:
                    failed += 1
        return {"total": total, "passed": passed, "failed": failed}


class Semester(models.Model):
    number = models.IntegerField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="semesters")

    def __str__(self):
        return f"Sem {self.number} - {self.student.name}"

    def sgpa(self):
        """
        Official Kannur University Formula:
        Grade Point (GP)  = (marks_obtained / max_marks) × 10
        Credit Point (CP) = GP × Credits
        SGPA = Σ(CP) / Σ(Credits)
        """
        marks = self.marks.all()
        if not marks.exists():
            return 0.0

        total_credits = 0.0
        total_credit_points = 0.0

        for mark in marks:
            credit = mark.subject.credits or 0
            total_credits += credit

            # Calculate Grade Point and Credit Point
            grade_point = (mark.marks_obtained / mark.max_marks) * 10 if mark.max_marks > 0 else 0
            credit_point = grade_point * credit

            total_credit_points += credit_point

        if total_credits == 0:
            return 0.0

        sgpa = total_credit_points / total_credits
        return round(sgpa, 3)


class Subject(models.Model):
    COURSE_CHOICES = [
        ("Computer Science", "Computer Science"),
        ("Business Administration", "Business Administration"),
        ("Engineering", "Engineering"),
        ("Medicine", "Medicine"),
        ("Law", "Law"),
    ]

    course = models.CharField(max_length=50, choices=COURSE_CHOICES)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    semester_number = models.IntegerField(default=1)
    credits = models.FloatField(default=3.0)

    def __str__(self):
        return f"{self.course} | Sem {self.semester_number} | {self.code} - {self.name}"


class Mark(models.Model):
    semester = models.ForeignKey("Semester", on_delete=models.CASCADE, related_name="marks")
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    max_marks = models.FloatField(default=50)

    # Attempt details
    attempt_type = models.CharField(
        max_length=20,
        choices=[
            ("Regular", "Regular"),
            ("Supply/Improvement", "Supply/Improvement"),
        ],
        default="Regular",
    )
    attempt_no = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.subject.name} (Attempt {self.attempt_no} - {self.attempt_type})"

    def grade_point(self):
        
        if self.max_marks > 0:
            return round((self.marks_obtained / self.max_marks) * 10, 2)
        return 0.0

    def credit_point(self):
        
        return round(self.grade_point() * (self.subject.credits or 0), 2)
