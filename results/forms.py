
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
    course_ref = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        label="Course"
    )

    class Meta:
        model = Student
        fields = [
            "reg_no", "name", "dob",
            "course_ref",   # ✅ new FK field (shown to user)
            "course",       # ⚠️ old string field (hidden later)
            "syllabus",
            "academic_year",
            "gender", "caste", "religion",
            "address", "pin_code", "photo"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Hide old course field from UI
        self.fields["course"].widget = forms.HiddenInput()

        # default: no syllabus until course is selected
        self.fields["syllabus"].queryset = Syllabus.objects.none()

        # When form is submitted
        if "course_ref" in self.data:
            try:
                course_ref_id = int(self.data.get("course_ref"))
                course_obj = Course.objects.get(id=course_ref_id)

                # 🔁 sync old string field
                self.fields["syllabus"].queryset = Syllabus.objects.filter(
                    course=course_obj.name
                )
            except (ValueError, Course.DoesNotExist):
                pass

        # When editing existing student
        elif self.instance.pk and self.instance.course:
            self.fields["syllabus"].queryset = Syllabus.objects.filter(
                course=self.instance.course
            )

    def clean(self):
        cleaned = super().clean()
        course_ref = cleaned.get("course_ref")

        # 🔁 keep string course in sync
        if course_ref:
            cleaned["course"] = course_ref.name

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
    course_ref = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        label="Course"
    )

    class Meta:
        model = Subject
        fields = [
            "course_ref",   # ✅ shown to user
            "course",       # ⚠️ hidden string
            "syllabus",
            "name",
            "code",
            "semester_number",
            "credits",
            "max_marks",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["course"].widget = forms.HiddenInput()
        self.fields["syllabus"].queryset = Syllabus.objects.none()

        if "course_ref" in self.data:
            try:
                course_ref_id = int(self.data.get("course_ref"))
                course_obj = Course.objects.get(id=course_ref_id)
                self.fields["syllabus"].queryset = Syllabus.objects.filter(
                    course=course_obj.name
                )
            except (ValueError, Course.DoesNotExist):
                pass

        elif self.instance.pk and self.instance.course:
            self.fields["syllabus"].queryset = Syllabus.objects.filter(
                course=self.instance.course
            )

    def clean(self):
        cleaned = super().clean()
        course_ref = cleaned.get("course_ref")

        if course_ref:
            cleaned["course"] = course_ref.name

        return cleaned


