
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
            "reg_no", "name", "dob",
            "course_ref",
            "course",
            "syllabus",
            "academic_year",
            "gender", "caste", "religion",
            "address", "pin_code", "photo"
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Hide old string field
        self.fields["course"].widget = forms.HiddenInput()

        # 🔥 FILTER COURSES BASED ON TEACHER DEPARTMENT
        if user and not user.is_superuser:
            try:
                teacher_dept = user.teacher.department
                self.fields["course_ref"].queryset = Course.objects.filter(
                    department=teacher_dept
                )
            except:
                self.fields["course_ref"].queryset = Course.objects.none()
        else:
            self.fields["course_ref"].queryset = Course.objects.all()

        # Default syllabus empty
        self.fields["syllabus"].queryset = Syllabus.objects.none()

        if "course_ref" in self.data:
            try:
                course_ref_id = int(self.data.get("course_ref"))
                course_obj = Course.objects.get(id=course_ref_id)

                self.fields["syllabus"].queryset = Syllabus.objects.filter(
                    course=course_obj.name
                )
            except:
                pass

    def clean(self):
        cleaned = super().clean()
        course_ref = cleaned.get("course_ref")

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
    class Meta:
        model = Subject
        fields = [
            "name",
            "code",
            "semester_number",
            "credits",
            "max_marks",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter subject name"
            }),
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter subject code"
            }),
            "semester_number": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),
            "credits": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.5",
                "min": 0
            }),
            "max_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0
            }),
        }


