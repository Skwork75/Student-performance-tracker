# Student Performance Tracker

## Overview
The Student Performance Tracker is a Python and Flask-based web application that allows teachers to manage students, assign grades, calculate averages, and track performance. The application uses an SQLite database for storing student records and provides a simple web interface for interaction. The project is deployed on PythonAnywhere for online access. Final project of (VaultofCodes internship).

**Live Demo:** [Student Performance Tracker](https://sk175.pythonanywhere.com/)

## Features
- Add students with name and roll number  
- Assign and update grades for multiple subjects  
- View student details including individual grades and average performance  
- Calculate subject-wise averages and identify toppers  
- Store data persistently using SQLite  
- User-friendly web interface built with Flask, HTML, and CSS  

## Project Structure
```
student-performance-tracker/
│── app.py                # Main Flask application
│── requirements.txt      # Dependencies
│── students.db           # SQLite database file
│── templates/            # HTML templates
│── static/               # CSS/JS files
```

## Installation (Local Setup)
1. Clone the repository:
   ```bash
   git clone <repository-link>
   cd student-performance-tracker
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open the application in your browser:
   ```
   http://127.0.0.1:5000/
   ```

## Deployment on PythonAnywhere
1. Create a free PythonAnywhere account.  
2. Upload the project files (`app.py`, `templates/`, `static/`, `students.db`).  
3. Set up a Flask web app on PythonAnywhere, pointing to `app.py`.  
4. Install dependencies using the `requirements.txt` file in the PythonAnywhere console.  
5. Reload the web app from the PythonAnywhere dashboard.  

Your application is now live at:  
**https://sk175.pythonanywhere.com/**
