"""
Student Record Management System
Python + Tkinter + MySQL
Run: python app.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
import re
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",  # Change this to your MySQL password
    "database": "student_db",
    "port": 3306,
}

def connect_server():
    """Connect to MySQL server and create the database if it does not exist."""
    cfg = DB_CONFIG.copy()
    cfg.pop("database")
    return mysql.connector.connect(**cfg)

def initialize_database():
    server = connect_server()
    cur = server.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS student_db")
    cur.close()
    server.close()

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(80) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            course VARCHAR(60) NOT NULL,
            semester TINYINT UNSIGNED NOT NULL,
            phone VARCHAR(15),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (semester BETWEEN 1 AND 8)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Record Management System")
        self.root.geometry("1050x650")
        self.root.minsize(900, 580)
        self.selected_id = None

        title = tk.Label(root, text="STUDENT RECORD MANAGEMENT SYSTEM",
                         font=("Arial", 18, "bold"), pady=12)
        title.pack(fill="x")

        form = ttk.LabelFrame(root, text="Student Details", padding=12)
        form.pack(fill="x", padx=14, pady=6)

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.course_var = tk.StringVar()
        self.semester_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.search_var = tk.StringVar()

        fields = [
            ("Full Name", self.name_var, 0, 0),
            ("Email", self.email_var, 0, 2),
            ("Course", self.course_var, 1, 0),
            ("Semester (1-8)", self.semester_var, 1, 2),
            ("Phone (optional)", self.phone_var, 2, 0),
        ]
        for label, var, row, col in fields:
            ttk.Label(form, text=label).grid(row=row, column=col, sticky="w", padx=5, pady=7)
            width = 30 if col == 0 else 32
            if label == "Course":
                widget = ttk.Combobox(form, textvariable=var, width=width,
                                      values=("BCA", "BSc", "BCom", "BA", "BBA", "BE", "Other"))
                widget.state(["!readonly"])
            else:
                widget = ttk.Entry(form, textvariable=var, width=width)
            widget.grid(row=row, column=col+1, sticky="w", padx=5, pady=7)

        actions = ttk.Frame(form)
        actions.grid(row=0, column=4, rowspan=3, padx=18, sticky="ns")
        ttk.Button(actions, text="Add Student", command=self.add_student).pack(fill="x", pady=4)
        ttk.Button(actions, text="Update Selected", command=self.update_student).pack(fill="x", pady=4)
        ttk.Button(actions, text="Delete Selected", command=self.delete_student).pack(fill="x", pady=4)
        ttk.Button(actions, text="Clear Form", command=self.clear_form).pack(fill="x", pady=4)

        search_frame = ttk.Frame(root, padding=(14, 8))
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search by name, email, or course:").pack(side="left")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=35)
        search_entry.pack(side="left", padx=8)
        search_entry.bind("<KeyRelease>", lambda _event: self.load_students())
        ttk.Button(search_frame, text="Refresh", command=self.load_students).pack(side="left", padx=5)

        table_frame = ttk.Frame(root, padding=(14, 4))
        table_frame.pack(fill="both", expand=True)
        columns = ("student_id", "name", "email", "course", "semester", "phone")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        headings = {
            "student_id": "ID", "name": "Full Name", "email": "Email",
            "course": "Course", "semester": "Semester", "phone": "Phone"
        }
        widths = {"student_id": 55, "name": 190, "email": 240, "course": 110, "semester": 85, "phone": 130}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center" if col in ("student_id","semester") else "w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.status = tk.StringVar(value="Ready — connect to MySQL to begin.")
        ttk.Label(root, textvariable=self.status, relief="sunken", anchor="w", padding=6).pack(fill="x", side="bottom")
        self.load_students()

    def db(self):
        return mysql.connector.connect(**DB_CONFIG)

    def validate(self):
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        course = self.course_var.get().strip()
        semester = self.semester_var.get().strip()
        phone = self.phone_var.get().strip()
        if not name or not email or not course or not semester:
            messagebox.showwarning("Missing details", "Name, email, course, and semester are required.")
            return None
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            messagebox.showwarning("Invalid email", "Enter a valid email address.")
            return None
        try:
            sem = int(semester)
            if not 1 <= sem <= 8:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid semester", "Semester must be a whole number from 1 to 8.")
            return None
        if phone and not re.fullmatch(r"[0-9+\-\s()]{7,15}", phone):
            messagebox.showwarning("Invalid phone", "Phone can contain digits, +, -, spaces, and brackets (7–15 characters).")
            return None
        return (name, email, course, sem, phone or None)

    def add_student(self):
        values = self.validate()
        if not values:
            return
        conn = None
        try:
            conn = self.db()
            cur = conn.cursor()
            cur.execute("INSERT INTO students (name,email,course,semester,phone) VALUES (%s,%s,%s,%s,%s)", values)
            conn.commit()
            self.status.set(f"Student added successfully. New ID: {cur.lastrowid}")
            messagebox.showinfo("Success", "Student record inserted into MySQL.")
            self.clear_form()
            self.load_students()
        except Error as e:
            if conn: conn.rollback()
            if getattr(e, "errno", None) == 1062:
                messagebox.showerror("Duplicate email", "That email already exists. Use a unique email address.")
            else:
                messagebox.showerror("Database error", f"Could not add student.\n{e}")
        finally:
            if conn and conn.is_connected(): conn.close()

    def update_student(self):
        if self.selected_id is None:
            messagebox.showwarning("Select record", "Select a student row in the table before updating.")
            return
        values = self.validate()
        if not values:
            return
        conn = None
        try:
            conn = self.db()
            cur = conn.cursor()
            cur.execute("""UPDATE students SET name=%s,email=%s,course=%s,semester=%s,phone=%s
                           WHERE student_id=%s""", (*values, self.selected_id))
            conn.commit()
            if cur.rowcount == 0:
                messagebox.showinfo("No changes", "No data changed.")
            else:
                messagebox.showinfo("Success", "Student record updated in MySQL.")
            self.status.set(f"Updated student ID {self.selected_id}.")
            self.clear_form()
            self.load_students()
        except Error as e:
            if conn: conn.rollback()
            if getattr(e, "errno", None) == 1062:
                messagebox.showerror("Duplicate email", "That email belongs to another student.")
            else:
                messagebox.showerror("Database error", f"Could not update student.\n{e}")
        finally:
            if conn and conn.is_connected(): conn.close()

    def delete_student(self):
        if self.selected_id is None:
            messagebox.showwarning("Select record", "Select a student row in the table before deleting.")
            return
        if not messagebox.askyesno("Confirm delete", f"Delete student ID {self.selected_id}? This cannot be undone."):
            return
        conn = None
        try:
            conn = self.db()
            cur = conn.cursor()
            cur.execute("DELETE FROM students WHERE student_id=%s", (self.selected_id,))
            conn.commit()
            self.status.set(f"Deleted student ID {self.selected_id}.")
            messagebox.showinfo("Success", "Student record deleted from MySQL.")
            self.clear_form()
            self.load_students()
        except Error as e:
            if conn: conn.rollback()
            messagebox.showerror("Database error", f"Could not delete student.\n{e}")
        finally:
            if conn and conn.is_connected(): conn.close()

    def load_students(self):
        query = self.search_var.get().strip()
        conn = None
        try:
            conn = self.db()
            cur = conn.cursor()
            if query:
                pattern = f"%{query}%"
                cur.execute("""SELECT student_id,name,email,course,semester,phone FROM students
                               WHERE name LIKE %s OR email LIKE %s OR course LIKE %s
                               ORDER BY student_id DESC""", (pattern, pattern, pattern))
            else:
                cur.execute("SELECT student_id,name,email,course,semester,phone FROM students ORDER BY student_id DESC")
            rows = cur.fetchall()
            for item in self.tree.get_children():
                self.tree.delete(item)
            for row in rows:
                self.tree.insert("", "end", values=tuple("" if x is None else x for x in row))
            self.status.set(f"Connected to MySQL | Records shown: {len(rows)}")
        except Error as e:
            self.status.set("MySQL connection failed. Check credentials and make sure MySQL is running.")
            # Avoid a popup on every key press while search is being typed.
            if not getattr(self, "_connection_error_shown", False):
                messagebox.showerror("MySQL connection error",
                    "Cannot connect to MySQL.\n\n1. Start MySQL.\n2. Check DB_CONFIG password in app.py.\n3. Run database.sql or restart the app.\n\nDetails: " + str(e))
                self._connection_error_shown = True
        finally:
            if conn and conn.is_connected(): conn.close()

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_id = int(values[0])
        self.name_var.set(values[1])
        self.email_var.set(values[2])
        self.course_var.set(values[3])
        self.semester_var.set(values[4])
        self.phone_var.set(values[5])

    def clear_form(self):
        self.selected_id = None
        for var in (self.name_var, self.email_var, self.course_var, self.semester_var, self.phone_var):
            var.set("")
        for item in self.tree.selection():
            self.tree.selection_remove(item)

if __name__ == "__main__":
    try:
        initialize_database()
        root = tk.Tk()
        app = StudentApp(root)
        root.mainloop()
    except Error as e:
        messagebox.showerror("Startup error", f"Could not initialize MySQL database.\n\nCheck DB_CONFIG in app.py.\n\n{e}")
    except Exception as e:
        print("Startup error:", e)
        raise
