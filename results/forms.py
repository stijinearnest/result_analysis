from django import forms
from .models import Student, Semester, Mark, Subject

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["reg_no", "name", "dob", "course", "academic_year", "photo"]
        widgets = {"dob": forms.DateInput(attrs={"type": "date"})}

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
            subjects = Subject.objects.filter(course=semester.student.course, semester_number=semester.number)
            for subject in subjects:
                # Marks obtained
                self.fields[f"subject_{subject.id}_obtained"] = forms.FloatField(
                    label=f"{subject.name} ({subject.code}) - Marks Obtained",
                    min_value=0,
                    max_value=subject.credits * 10,  # optional, or set fixed max 40
                    required=True,
                    widget=forms.NumberInput(attrs={'step': '0.5'})
                )
                # Max marks
                self.fields[f"subject_{subject.id}_max"] = forms.FloatField(
                    label=f"{subject.name} ({subject.code}) - Max Marks",
                    initial=40,  # default max marks
                    required=True,
                    widget=forms.NumberInput(attrs={'step': '0.5'})
                )


# Subject Form for adding subjects


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["course", "name", "code", "semester_number", "credits"]
        widgets = {
            "course": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Subject Name"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Subject Code"}),
            "semester_number": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "credits": forms.NumberInput(attrs={"class": "form-control", "min": 0.5, "step": 0.5}),
        }

