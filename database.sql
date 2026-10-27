-- Student Record Management System
-- Run this file in MySQL Workbench or the MySQL command line.

CREATE DATABASE IF NOT EXISTS student_db;
USE student_db;

CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    course VARCHAR(60) NOT NULL,
    semester TINYINT UNSIGNED NOT NULL,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (semester BETWEEN 1 AND 8)
);

-- Optional sample data. These records are only examples.
INSERT IGNORE INTO students (name, email, course, semester, phone) VALUES
('Ananya Rao', 'ananya.demo@example.com', 'BCA', 3, '9876543210'),
('Rahul Kumar', 'rahul.demo@example.com', 'BCA', 2, '9123456780'),
('Meghana S', 'meghana.demo@example.com', 'BSc', 4, '9988776655');

-- Verify stored data:
SELECT * FROM students;
