from django.urls import path
from django.shortcuts import redirect
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path("", views.home, name="home"),

   
    path("teacher/login/", views.teacher_login, name="teacher_login"),
    path("student/login/", views.student_login, name="student_login"),
    path("logout/", views.user_logout, name="logout"),

   
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("control/dashboard/", views.admin_dashboard, name="admin_dashboard"),


  
    path("teacher/add-student/", views.add_student, name="add_student"),
    path('student-success/<str:student_name>/', views.student_success, name='student_success'),
    path("teacher/select-student-semester/", views.select_student_semester, name="select_student_semester"),
    path("teacher/add-marks-single/", views.add_marks_single_page, name="add_marks_single"),

  
    path("teacher/edit-marks/<int:mark_id>/", views.edit_marks, name="edit_marks"),

 
    path("teacher/get-student-name-by-regno/", views.get_student_name_by_regno, name="get_student_name_by_regno"),
    path("teacher/get-subjects/", views.get_subjects_for_semester, name="get_subjects_for_semester"),

    
    path("teacher/manage-subjects/", views.manage_subjects, name="manage_subjects"),
    path("teacher/edit-subject/<int:subject_id>/", views.edit_subject, name="edit_subject"),
    path("teacher/delete-subject/<int:subject_id>/", views.delete_subject, name="delete_subject"),
  
path("teacher/select-course/", views.select_course, name="select_course"),


path("teacher/manage-subjects/<str:course>/", views.manage_subjects_by_course, name="manage_subjects_by_course"),

path("teacher/student-search/", views.student_search, name="student_search"),
path("teacher/student-detail/<int:student_id>/", views.student_detail, name="student_detail"),


    path("password_reset/", 
         auth_views.PasswordResetView.as_view(template_name="password_reset.html"), 
         name="password_reset"),
    path("password_reset_done/", 
         auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"), 
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/", 
         auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), 
         name="password_reset_confirm"),
    path("reset/done/", 
         auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), 
         name="password_reset_complete"),

path("student/<int:student_id>/attempts/", views.view_all_attempts, name="view_all_attempts"),
path("student/<int:student_id>/subject/<int:subject_id>/attempts/", views.subject_attempt_history, name="subject_attempt_history"),

path('ajax/get-subjects/', views.get_subjects_for_semester, name='get_subjects_for_semester'),
 path('teacher/students-filter/', views.teacher_students_filter, name='teacher_students_filter'),

 # example
path('teacher/grace/', views.grace_marks, name='grace_marks'),
path('teacher/grace/<int:student_id>/<int:sem_number>/', views.apply_grace_marks, name='apply_grace_marks'),

 path('ajax/get-student/', views.ajax_get_student, name='ajax_get_student'),
 path("ajax/get-syllabus/", views.get_syllabus_by_course, name="get_syllabus_by_course"),
path("ajax/create-syllabus/", views.ajax_create_syllabus, name="ajax_create_syllabus"),

 path(
  "control/department-analysis/",
  views.admin_department_analysis,
  name="admin_department_analysis"
),

path(
    "control/departments/<int:department_id>/students/",
    views.admin_department_students,
    name="admin_department_students"
),

path("control/teachers/add/", views.add_teacher, name="add_teacher"),
path("control/teachers/<int:teacher_id>/edit/", views.edit_teacher, name="edit_teacher"),


path("control/departments/", views.manage_departments, name="manage_departments"),
path("control/departments/add/", views.add_department, name="add_department"),
path("control/departments/<int:department_id>/edit/", views.edit_department, name="edit_department"),
path(
    "control/departments/<int:department_id>/courses/",
    views.manage_department_courses,
    name="manage_department_courses"
),

path(
    "control/courses/<int:course_id>/edit/",
    views.edit_course,
    name="edit_course"
),
path(
    "control/courses/<int:course_id>/delete/",
    views.delete_course,
    name="delete_course"
),



]
