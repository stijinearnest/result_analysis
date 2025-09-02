from django.contrib import admin
from .models import Teacher, Student, Semester, Subject, Mark

admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(Semester)
admin.site.register(Subject)
admin.site.register(Mark)
