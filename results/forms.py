from django import forms
from .models import Student, Semester, Mark,Subject

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["reg_no", "name", "dob", "course", "semester", "academic_year", "photo"]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
        }

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
            # Only subjects of this semester
            subjects = Subject.objects.filter(semester_number=semester.number)
            for subject in subjects:
                self.fields[f"subject_{subject.id}"] = forms.FloatField(
                    label=f"{subject.name} ({subject.code})",
                    min_value=0,
                    max_value=40,  # max marks
                    required=True,
                    widget=forms.NumberInput(attrs={'step': '0.5'})
                )
