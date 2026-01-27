
from django import forms
from .models import Student, Semester, Mark, Subject,Syllabus



class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "reg_no", "name", "dob",
            "course", "syllabus",
            "academic_year",
            "gender", "caste", "religion",
            "address", "pin_code", "photo"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # default: no syllabus until course is selected
        self.fields["syllabus"].queryset = Syllabus.objects.none()

        if "course" in self.data:
            course = self.data.get("course")
            self.fields["syllabus"].queryset = Syllabus.objects.filter(course=course)

        elif self.instance.pk:
            self.fields["syllabus"].queryset = Syllabus.objects.filter(
                course=self.instance.course
            )


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
            "course",
            "syllabus",
            "name",
            "code",
            "semester_number",
            "credits",
            "max_marks",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # do not show all syllabi by default
        self.fields["syllabus"].queryset = Syllabus.objects.none()

        if "course" in self.data:
            course = self.data.get("course")
            self.fields["syllabus"].queryset = Syllabus.objects.filter(course=course)

        elif self.instance.pk:
            self.fields["syllabus"].queryset = Syllabus.objects.filter(
                course=self.instance.course
            )

