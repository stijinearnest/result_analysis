from django.db import models
from django.contrib.auth.models import User

# Extend User for teacher role
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


# Student model
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
        semesters = self.semesters.all()
        if not semesters:
            return 0
        sgpas = [sem.sgpa() for sem in semesters if sem.sgpa() > 0]
        return round(sum(sgpas) / len(sgpas), 2) if sgpas else 0

    def pass_fail_summary(self):
        total = 0
        passed = 0
        failed = 0
        for sem in self.semesters.all():
            for mark in sem.marks.all():
                total += 1
                if mark.marks_obtained >= (0.4 * mark.max_marks):  # 40% passing rule
                    passed += 1
                else:
                    failed += 1
        return {"total": total, "passed": passed, "failed": failed}



# Semester
class Semester(models.Model):
    number = models.IntegerField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="semesters")

    def __str__(self):
        return f"Sem {self.number} - {self.student.name}"

    def sgpa(self):
        marks = self.marks.all()
        if not marks:
            return 0
        total = sum(m.marks_obtained for m in marks)
        max_total = sum(m.max_marks for m in marks)
        return round((total / max_total) * 10, 2)   # scale to 10



class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    semester_number = models.IntegerField(default=1)  # <--- add this

    def __str__(self):
        return f"Sem {self.semester_number} | {self.code} - {self.name}"
  




# Marks
class Mark(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="marks")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    max_marks = models.FloatField(default=40)

    def __str__(self):
        return f"{self.semester.student.name} - {self.subject.name}: {self.marks_obtained}/{self.max_marks}"
