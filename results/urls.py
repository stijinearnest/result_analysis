from django.urls import path
from django.shortcuts import redirect
from . import views

def add_marks_redirect(request):
    return redirect("select_student_semester")

urlpatterns = [
    path("", views.home, name="home"),

    # Auth
    path("teacher/login/", views.teacher_login, name="teacher_login"),
    path("student/login/", views.student_login, name="student_login"),
    path("logout/", views.user_logout, name="logout"),

    # Dashboards
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),

    # Students & Marks
    path("teacher/add-student/", views.add_student, name="add_student"),
    path("teacher/select-student-semester/", views.select_student_semester, name="select_student_semester"),
    path("teacher/add-marks/", add_marks_redirect, name="add_marks_redirect"),
    path("teacher/add-marks-single/", views.add_marks_single_page, name="add_marks_single"),

    # Edit marks
    path("teacher/edit-marks/<int:mark_id>/", views.edit_marks, name="edit_marks"),

    # Student detail
    path("teacher/student-detail/", views.student_detail, name="student_detail"),

    # AJAX
    path("teacher/get-student-name-by-regno/", views.get_student_name_by_regno, name="get_student_name_by_regno"),
    path("teacher/get-subjects/", views.get_subjects_for_semester, name="get_subjects_for_semester"),

    # Manage Subjects
   
     path("teacher/manage-subjects/", views.manage_subjects, name="manage_subjects"),
    path("teacher/edit-subject/<int:subject_id>/", views.edit_subject, name="edit_subject"),
    path("teacher/delete-subject/<int:subject_id>/", views.delete_subject, name="delete_subject"),
]
