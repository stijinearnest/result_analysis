# SRMS | Student Result Management System

> A modern web-based Student Result Management System built with Django to simplify student result management, marks entry, academic performance tracking, and result visualization.

![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge\&logo=django\&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge\&logo=sqlite\&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge\&logo=bootstrap\&logoColor=white)
![Chart.js](https://img.shields.io/badge/Charts-Chart.js-FF6384?style=for-the-badge\&logo=chartdotjs\&logoColor=white)

---

## 📌 Overview

**SRMS** is a web-based Student Result Management System designed to make academic result management easier for teachers and students.

The system provides separate access for **teachers and students**. Teachers can manage student information, subjects, semesters, and marks, while students can securely access their academic performance and view important result statistics.

The application also calculates and displays **SGPA, CGPA, pass/fail statistics, semester-wise marks, and academic performance trends**.

---

## ✨ Features

### 👨‍🏫 Teacher Module

* Secure teacher authentication
* Add and manage students
* Search students by registration number
* Manage subjects and semester-wise subjects
* Add student marks
* Edit existing marks
* View detailed student results
* Filter results by semester
* Manage courses and subjects
* View student academic performance

### 🎓 Student Module

* Student login using registration number and date of birth
* Personal result dashboard
* Semester-wise marks
* SGPA calculation
* Overall CGPA
* Total papers
* Passed and failed papers
* Academic performance visualization
* Semester filtering

### 📊 Result Analytics

* Automatic SGPA calculation
* Automatic CGPA calculation
* Credit-based performance calculation
* Pass/fail analysis
* Semester-wise performance tracking
* Visual representation of academic performance

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │       SRMS          │
                    │  Student Result     │
                    │ Management System   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
       ┌──────▼──────┐                   ┌──────▼──────┐
       │   Teacher   │                   │   Student   │
       │    Module   │                   │    Module   │
       └──────┬──────┘                   └──────┬──────┘
              │                                 │
       ┌──────▼─────────────┐            ┌──────▼──────────┐
       │ Student Management │            │ Result Dashboard │
       │ Marks Management   │            │ SGPA / CGPA      │
       │ Subject Management │            │ Semester Results │
       └──────────┬─────────┘            └────────┬─────────┘
                  │                               │
                  └──────────────┬────────────────┘
                                 │
                         ┌───────▼────────┐
                         │    Database    │
                         │     SQLite     │
                         └────────────────┘
```

---

## 🛠️ Tech Stack

| Technology       | Purpose                   |
| ---------------- | ------------------------- |
| **Python**       | Backend programming       |
| **Django**       | Web framework             |
| **SQLite**       | Database                  |
| **HTML5**        | Page structure            |
| **CSS3**         | Styling                   |
| **Bootstrap 5**  | Responsive UI             |
| **JavaScript**   | Client-side functionality |
| **AJAX**         | Asynchronous requests     |
| **Chart.js**     | Result visualization      |
| **Git & GitHub** | Version control           |

---

## 🗄️ Database Design

The system uses a relational database structure to organize academic information.

### Main Entities

```text
Student
   │
   ├── Semester
   │      │
   │      └── Mark
   │              │
   │              └── Subject
   │
   └── Academic Information

Teacher
   │
   └── Course / Subject Management
```

### Core Data Relationships

* One **Student** can have multiple **Semesters**
* One **Semester** can contain multiple **Marks**
* Each **Mark** belongs to a **Subject**
* Teachers manage students, subjects, and marks

---

## 🔐 Authentication & Authorization

SRMS provides separate access mechanisms for teachers and students.

### Teacher Authentication

Teachers authenticate using Django's built-in authentication system.

Only authorized staff or superusers can access teacher functionality.

### Student Authentication

Students log in using:

```text
Registration Number
        +
Date of Birth
```

Student login information is stored in a Django session to maintain the authenticated student state.

---

## 📈 SGPA & CGPA

SRMS automatically calculates academic performance based on semester marks and subject credits.

### SGPA

The system calculates semester performance using the marks obtained and the credits associated with each subject.

### CGPA

The overall CGPA is calculated from the student's semester performance.

This removes the need for teachers or students to manually calculate academic performance.

---

## 🔄 Application Flow

### Teacher Flow

```text
Teacher Login
     ↓
Teacher Dashboard
     ↓
Manage Students
     ↓
Select Student
     ↓
Select Semester
     ↓
Enter / Edit Marks
     ↓
Save Result
     ↓
View Student Performance
```

### Student Flow

```text
Student Login
     ↓
Enter Registration Number + DOB
     ↓
Student Dashboard
     ↓
View SGPA / CGPA
     ↓
View Semester Results
     ↓
Analyze Academic Performance
```

---

## 📂 Project Structure

```text
SRMS/
│
├── manage.py
│
├── project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── app/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   └── migrations/
│
├── templates/
│   ├── home.html
│   ├── teacher_login.html
│   ├── student_login.html
│   ├── teacher_dashboard.html
│   ├── student_dashboard.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/
│
├── db.sqlite3
├── requirements.txt
└── README.md
```

> Replace `project/` and `app/` with the actual names used in your repository.

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/SRMS.git
cd SRMS
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

#### Linux / macOS

```bash
source venv/bin/activate
```

#### Windows

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create your administrator account.

### 7. Run the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## 🔑 Admin Panel

Django's built-in admin panel can be accessed through:

```text
http://127.0.0.1:8000/admin/
```

Use the superuser credentials created during setup.

---

## 🧪 Testing

The system can be tested through different user flows:

### Teacher Testing

* Teacher login
* Student creation
* Subject management
* Marks entry
* Marks editing
* Student search
* Semester filtering
* Student result viewing

### Student Testing

* Student authentication
* Dashboard access
* Semester filtering
* SGPA verification
* CGPA verification
* Pass/fail verification

---

## 🔒 Security

The project uses Django's built-in security mechanisms, including:

* Authentication
* Session management
* Login protection
* Role-based access restrictions
* CSRF protection
* ORM-based database queries

Teacher-only views are protected using Django authentication and authorization decorators.

---

## 🎯 Project Objectives

The main objectives of SRMS are to:

* Reduce manual result management
* Minimize calculation errors
* Centralize student academic records
* Provide quick access to results
* Simplify marks management for teachers
* Help students understand their academic performance
* Provide a clean and user-friendly result dashboard

---

## 🔮 Future Improvements

Possible future enhancements include:

* 📄 Download results as PDF
* 📧 Email result notifications
* 📱 Progressive Web App support
* 📊 Advanced academic analytics
* 🏆 Student ranking and leaderboard
* 📈 More detailed performance charts
* 🔐 Password-based student authentication
* ☁️ Cloud deployment
* 🗃️ PostgreSQL production database
* 👥 More granular role-based permissions

---

## 📸 Screenshots

Add screenshots of your application here:

```text
screenshots/
├── home.png
├── teacher-login.png
├── teacher-dashboard.png
├── student-login.png
├── student-dashboard.png
├── marks-entry.png
└── student-result.png
```

Then add them to the README:

```markdown
![Home](screenshots/home.png)

![Student Dashboard](screenshots/student-dashboard.png)
```

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository
2. Create a new branch

```bash
git checkout -b feature/new-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push the branch

```bash
git push origin feature/new-feature
```

5. Open a Pull Request

---

## 📄 License

This project is developed for educational and academic purposes.

---

## 👨‍💻 Developer

**Stijin Earnest Abraham**

Built with **Python + Django** ❤️

---

## ⭐ Support

If you find this project useful or interesting, consider giving the repository a **⭐ star** on GitHub.

---

> **SRMS** — Making student result management simpler, faster, and more organized.
