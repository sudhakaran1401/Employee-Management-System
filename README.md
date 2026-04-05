# 🧑‍💼 Employee Management System (EMS)

A Django-based web application used to manage employee-related records including employees, attendance, leaves, and payroll. This project demonstrates CRUD operations, modular Django architecture, and core backend development concepts.

---

## 🚀 Features

* 🔐 User Login & Authentication
* 👥 Role-Based Access (Admin / HR / Employee)
* 📊 Interactive Dashboards with Charts
* 👤 Employee Management (Add / Update / Delete)
* 📅 Attendance Management
* 📝 Leave Management
* 💰 Payroll Management
* 🔍 Live Search & Pagination
* 📄 Report Generation
* 📂 Bulk Upload (Excel Support)

---

## 🛠️ Tech Stack

* **Backend:** Python, Django
* **Frontend:** HTML, CSS, JavaScript, Bootstrap, Django Templates
* **Database:** SQLite
* **Version Control:** Git & GitHub

---

## 📁 Project Structure

```
EMS/
│
├── config/                 # Main project configuration (settings, URLs)
├── employees/              # Employee management module
├── attendance/             # Attendance management module
├── leave/                  # Leave management module
├── payroll/                # Payroll management module
├── utils/                  # Helper functions and reusable logic
│
├── templates/              # HTML templates
├── static/                 # CSS, JavaScript, Images
│
├── manage.py               # Django entry point
├── requirements.txt        # Project dependencies
├── db.sqlite3              # Database (ignored in production)
├── employee_credentials.xlsx  # Sample employee data
```

---

## ⚙️ Setup Instructions

### 🪟 Windows

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/sudhakaran1401/Employee-Management-System.git
cd Employee-Management-System
```

#### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

#### 3️⃣ Activate Environment

```bash
venv\Scripts\activate
```

#### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

#### 5️⃣ Apply Migrations

```bash
python manage.py migrate
```

#### 6️⃣ Run Server

```bash
python manage.py runserver
```

---

### 🍎 Mac / 🐧 Linux

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/sudhakaran1401/Employee-Management-System.git
cd Employee-Management-System
```

#### 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
```

#### 3️⃣ Activate Virtual Environment

```bash
source venv/bin/activate
```

#### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

#### 5️⃣ Apply Migrations

```bash
python manage.py migrate
```

#### 6️⃣ Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

#### 7️⃣ Run Development Server

```bash
python manage.py runserver
```

---

### 🌐 Open in Browser

```
http://127.0.0.1:8000/
```

Admin Panel:

```
http://127.0.0.1:8000/admin/
```

---

## 🔐 Notes

* Uses SQLite database by default
* Authentication system implemented
* Superuser required for admin access

---

## 📌 Future Improvements

* 🌐 Deployment (Render / Heroku)
* 🔌 REST API (Django REST Framework)
* 📱 Responsive UI Enhancements
---

## 🎯 Learning Outcomes

* Django MVT Architecture
* CRUD Operations
* ORM (Database Handling)
* Form Handling & Validation
* Modular App Design

---

## 👨‍💻 Author

**Sudha Karan**
Aspiring Python Developer

---

## ⭐ Support

If you found this project helpful, give it a ⭐ on GitHub!
