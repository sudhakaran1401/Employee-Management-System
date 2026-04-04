# 🧑‍💼 Employee Management System (EMS)

A django based application used to handle Employee related records including employee, attendances, leaves and payrolls. This project demonstrates CRUD operations, modular Django architecture, and basic backend development concepts.  

---

## 🚀 Features
* User Login & Authentication
* Role-Based Access (Admin/HR/Employee)
* Interactive dashboards with Charts based on Roles 
* Employee management 
* Attendance management 
* Leave Management 
* Payroll Management
* Live searches and paginations
* Report Generation
* File uploading for bulk data create instant
---

## 🛠️ Tech Stack

* **Backend:** Python, Django
* **Frontend:** HTML, CSS, JS, Bootstrap, Django Templates
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

## ⚙️ Setup Instructions (Run Locally)

### 1️⃣ Clone the Repository

```
git clone https://github.com/sudhakaran1401/Employee-Management-System.git
cd Employee-Management-System
```

---

### 2️⃣ Create Virtual Environment

```
python -m venv venv
```

#### Activate Environment

**Windows:**

```
venv\Scripts\activate
```

**Mac/Linux:**

```
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

### 4️⃣ Apply Migrations

```
python manage.py migrate
```

---

### 5️⃣ Run the Server

```
python manage.py runserver
```

---

### 6️⃣ Open in Browser

```
http://127.0.0.1:8000/
```

---

## 🔐 Default Notes

* Uses SQLite database by default
* No authentication system implemented yet (can be added)

---

## 📌 Future Improvements

* 🌐 Deployment (Render / Heroku)
* 🔌 REST API (Django REST Framework)

---

## 🎯 Learning Outcomes

* Django MVT Architecture
* CRUD Operations
* ORM (Database Handling)
* Form Handling & Validation

---

## 👨‍💻 Author

**Sudha Karan**
Aspiring Python Developer

---

## ⭐ Support

If you found this project helpful, give it a ⭐ on GitHub!
