from django.contrib import admin
from .models import Teacher, Student, Semester, Subject, Mark,Department

admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(Semester)
admin.site.register(Subject)
admin.site.register(Mark)
admin.site.register(Department)