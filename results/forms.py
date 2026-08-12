
from django import forms
from .models import Student, Semester, Mark, Subject,Syllabus,Teacher,Course


class TeacherCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    full_name = forms.CharField(max_length=100)

    department = forms.ModelChoiceField(
        queryset=Teacher._meta.get_field("department")
        .remote_field.model.objects.all()
    )

    role = forms.ChoiceField(
        choices=[
            ("TEACHER", "Teacher"),
            ("HOD", "HOD"),
        ],
        initial="TEACHER"
    )



class TeacherEditForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    department = forms.ModelChoiceField(queryset=Teacher._meta.get_field("department").remote_field.model.objects.all())
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
    "reg_no",
    "name",
    "dob",
    "gender",
    "course_ref",
    "syllabus",
    "caste",
    "religion",
    "academic_year",
    "address",
    "pin_code",
    "photo",
]


    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Course queryset restriction
        if user and not user.is_superuser:
            self.fields["course_ref"].queryset = Course.objects.filter(
                department=user.teacher.department
            )
        else:
            self.fields["course_ref"].queryset = Course.objects.all()

        # Initially empty syllabus
        self.fields["syllabus"].queryset = Syllabus.objects.none()

        # If course selected in POST
        if "course_ref" in self.data:
            try:
                course_id = int(self.data.get("course_ref"))
                self.fields["syllabus"].queryset = Syllabus.objects.filter(
                    course_id=course_id
                )
            except (ValueError, TypeError):
                pass

        # If editing existing student
        elif self.instance.pk and self.instance.course_ref:
            self.fields["syllabus"].queryset = Syllabus.objects.filter(
                course=self.instance.course_ref
            )

    def clean(self):
        cleaned = super().clean()

        course_ref = cleaned.get("course_ref")
        if course_ref:
            cleaned["course"] = course_ref.name  # Sync old string field

        return cleaned


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ["number", "student"]

class MarkForm(forms.ModelForm):
    class Meta:
        model = Mark
        fields = ["semester", "subject", "marks_obtained", "max_marks"]

class MarksEntryForm(forms.Form):
    def __init__(self, *args, **kwargs):
        semester = kwargs.pop("semester", None)
        super().__init__(*args, **kwargs)

        if semester:
            subjects = Subject.objects.filter( syllabus=semester.student.syllabus,
    semester_number=semester.number)
            for subject in subjects:
               
                self.fields[f"subject_{subject.id}_obtained"] = forms.FloatField(
                    label=f"{subject.name} ({subject.code}) - Marks Obtained",
                    min_value=0,
                    max_value=subject.credits * 10, 
                    required=True,
                    widget=forms.NumberInput(attrs={'step': '0.5'})
                )
               
                self.fields[f"subject_{subject.id}_max"] = forms.FloatField(
                    label=f"{subject.name} ({subject.code}) - Max Marks",
                    initial=40,  
                    required=True,
                    widget=forms.NumberInput(attrs={'step': '0.5'})
                )

class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject
        fields = [
            "name",
            "code",
            "semester_number",
            "credits",
            "max_marks",
            "subject_type",
            "elective_group",
        ]

        widgets = {
            "subject_type": forms.RadioSelect,
        }

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("subject_type") == "ELECTIVE":
            if not cleaned.get("elective_group"):
                raise forms.ValidationError(
                    "Elective subjects must have an elective group."
                )
        else:
            cleaned["elective_group"] = None

        return cleaned


