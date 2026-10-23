# Expense Tracker

A simple expense tracking web application built with Flask and MongoDB.

## Features

- Track and manage expenses
- View expense summaries
- Store expense data in MongoDB
- Clean and user-friendly interface

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python and Flask
- **Database:** MongoDB
- **Version Control:** Git and GitHub

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/anaskhanpathan9898/ExpenceTracker.git
cd ExpenceTracker
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Set up your local `.env` file using the configuration expected by the application. Never upload real credentials or secret keys to GitHub.

### 5. Run the application

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Security

- Keep `.env` private.
- Never publish passwords, database credentials, or secret keys.

## Author

Huzaifa Sheikh
*This project was created for learning and demonstrating web development with Flask and MongoDB.*
