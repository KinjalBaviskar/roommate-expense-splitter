# Roommate Expense Splitter

A simple web application that helps roommates manage shared expenses, calculate individual balances, and determine who needs to pay whom.

## 📌 Overview

Managing shared expenses among roommates can become confusing when multiple people pay for groceries, rent, utilities, food, and other common expenses.

**Roommate Expense Splitter** simplifies this process by allowing users to:

* Add and manage roommates
* Record shared expenses
* Automatically calculate each person's balance
* Track who owes money and who should receive money
* Generate a settlement plan to minimize unnecessary payments
* Manage expenses through a simple web interface

## ✨ Features

### 👥 Roommate Management

* Add roommates
* View all roommates
* Delete roommates when required

### 💰 Expense Management

* Add expenses with payer, amount, description, and date
* View recorded expenses
* Delete expenses
* Automatically distribute expenses among roommates

### 📊 Balance Calculation

The application calculates the net balance for every roommate.

* **Positive balance** → The person should receive money
* **Negative balance** → The person needs to pay money
* **Zero balance** → The person's expenses are settled

### 🔄 Settlement Plan

The application generates a settlement plan that determines who should pay whom, making expense settlement easier and reducing unnecessary transactions.

## 🛠️ Technologies Used

* **Python**
* **Flask**
* **SQLite**
* **HTML**
* **CSS**
* **Jinja2**
* **Python Virtual Environment (venv)**

## 📁 Project Structure

```text
Roommate-Expense-Splitter/
│
├── app.py
├── database.py
├── templates/
│   └── ...
├── static/
│   └── ...
├── requirements.txt
├── README.md
└── .gitignore
```

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/KinjalBaviskar/roommate-expense-splitter.git
```

### 2. Navigate to the project

```bash
cd roommate-expense-splitter
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

**Windows PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the application

```bash
python app.py
```

The application will start locally. Open the URL displayed in the terminal, usually:

```text
http://127.0.0.1:5000
```

## 🧮 How It Works

Suppose three roommates share expenses:

| Roommate | Paid |
| -------- | ---: |
| Alice    | ₹900 |
| Bob      | ₹300 |
| Charlie  |   ₹0 |

Total expense:

```text
₹900 + ₹300 + ₹0 = ₹1200
```

Each roommate's share:

```text
₹1200 / 3 = ₹400
```

Net balances:

```text
Alice   → +₹500
Bob     → -₹100
Charlie → -₹400
```

The settlement algorithm can therefore determine that Bob and Charlie should pay Alice the required amounts.

## 🎯 Purpose

This project was developed to practice and demonstrate:

* Python programming
* Flask web development
* Database management with SQLite
* CRUD operations
* Financial/balance calculations
* Algorithmic settlement logic
* Backend and frontend integration

## 🚀 Future Improvements

Possible enhancements include:

* User authentication
* Multiple groups/households
* Monthly expense reports
* Expense categories
* Charts and visual analytics
* Export expenses to CSV/PDF
* Mobile-responsive improvements
* Persistent cloud database
* Notifications for pending settlements

## 👩‍💻 Author

**Kinjal Baviskar**

GitHub: [KinjalBaviskar](https://github.com/KinjalBaviskar)

---

⭐ If you find this project useful, consider giving it a star!
