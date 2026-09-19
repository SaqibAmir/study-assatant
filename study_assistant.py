import sqlite3
from datetime import datetime, timedelta


class Database:
    def __init__(self, db_name="study_assistant.db"):
        self.connection = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                total_topics INTEGER DEFAULT 0,
                completed_topics INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                title TEXT NOT NULL,
                deadline TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )
        """)

        self.connection.commit()

    def close(self):
        self.connection.close()


class StudyAssistant:
    def __init__(self):
        self.db = Database()

    # ---------- SUBJECTS ----------

    def add_subject(self):
        name = input("Subject name: ")

        try:
            topics = int(input("Number of topics: "))

            if topics < 0:
                print("Number of topics cannot be negative.")
                return

            cursor = self.db.connection.cursor()

            cursor.execute(
                "INSERT INTO subjects (name, total_topics) VALUES (?, ?)",
                (name, topics)
            )

            self.db.connection.commit()

            print("Subject added successfully.")

        except ValueError:
            print("Please enter a valid number.")

    def view_subjects(self):
        cursor = self.db.connection.cursor()

        cursor.execute("""
            SELECT id, name, total_topics, completed_topics
            FROM subjects
        """)

        subjects = cursor.fetchall()

        if not subjects:
            print("No subjects found.")
            return

        print("\n--- Subjects ---")

        for subject in subjects:
            subject_id, name, total, completed = subject

            if total > 0:
                progress = (completed / total) * 100
            else:
                progress = 0

            print(
                f"{subject_id}. {name} | "
                f"Progress: {completed}/{total} "
                f"({progress:.1f}%)"
            )

    def update_progress(self):
        self.view_subjects()

        try:
            subject_id = int(input("\nSubject ID: "))
            completed = int(input("Completed topics: "))

            cursor = self.db.connection.cursor()

            cursor.execute("""
                SELECT total_topics
                FROM subjects
                WHERE id = ?
            """, (subject_id,))

            result = cursor.fetchone()

            if result is None:
                print("Subject not found.")
                return

            total_topics = result[0]

            if completed < 0 or completed > total_topics:
                print("Invalid progress.")
                return

            cursor.execute("""
                UPDATE subjects
                SET completed_topics = ?
                WHERE id = ?
            """, (completed, subject_id))

            self.db.connection.commit()

            print("Progress updated.")

        except ValueError:
            print("Please enter valid numbers.")

    # ---------- TASKS ----------

    def add_task(self):
        self.view_subjects()

        try:
            subject_id = int(input("\nSubject ID: "))
            title = input("Task title: ")
            deadline = input("Deadline (YYYY-MM-DD): ")

            datetime.strptime(deadline, "%Y-%m-%d")

            cursor = self.db.connection.cursor()

            cursor.execute("""
                SELECT id
                FROM subjects
                WHERE id = ?
            """, (subject_id,))

            if cursor.fetchone() is None:
                print("Subject not found.")
                return

            cursor.execute("""
                INSERT INTO tasks
                (subject_id, title, deadline)
                VALUES (?, ?, ?)
            """, (subject_id, title, deadline))

            self.db.connection.commit()

            print("Task added successfully.")

        except ValueError:
            print("Invalid date or number.")

    def view_tasks(self):
        cursor = self.db.connection.cursor()

        cursor.execute("""
            SELECT
                tasks.id,
                subjects.name,
                tasks.title,
                tasks.deadline,
                tasks.completed
            FROM tasks
            JOIN subjects
            ON tasks.subject_id = subjects.id
            ORDER BY tasks.deadline
        """)

        tasks = cursor.fetchall()

        if not tasks:
            print("No tasks found.")
            return

        print("\n--- Tasks ---")

        for task in tasks:
            task_id, subject, title, deadline, completed = task

            status = "Completed" if completed else "Pending"

            print(
                f"{task_id}. {subject} | "
                f"{title} | {deadline} | {status}"
            )

    def complete_task(self):
        self.view_tasks()

        try:
            task_id = int(input("\nTask ID: "))

            cursor = self.db.connection.cursor()

            cursor.execute("""
                UPDATE tasks
                SET completed = 1
                WHERE id = ?
            """, (task_id,))

            if cursor.rowcount == 0:
                print("Task not found.")
                return

            self.db.connection.commit()

            print("Task marked as completed.")

        except ValueError:
            print("Please enter a valid ID.")

    # ---------- NOTES ----------

    def add_note(self):
        self.view_subjects()

        try:
            subject_id = int(input("\nSubject ID: "))
            title = input("Note title: ")
            content = input("Note content: ")

            cursor = self.db.connection.cursor()

            cursor.execute("""
                SELECT id
                FROM subjects
                WHERE id = ?
            """, (subject_id,))

            if cursor.fetchone() is None:
                print("Subject not found.")
                return

            cursor.execute("""
                INSERT INTO notes
                (subject_id, title, content)
                VALUES (?, ?, ?)
            """, (subject_id, title, content))

            self.db.connection.commit()

            print("Note saved successfully.")

        except ValueError:
            print("Invalid input.")

    def search_notes(self):
        keyword = input("Search notes: ")

        cursor = self.db.connection.cursor()

        cursor.execute("""
            SELECT
                subjects.name,
                notes.title,
                notes.content
            FROM notes
            JOIN subjects
            ON notes.subject_id = subjects.id
            WHERE notes.title LIKE ?
               OR notes.content LIKE ?
        """, (f"%{keyword}%", f"%{keyword}%"))

        results = cursor.fetchall()

        if not results:
            print("No matching notes.")
            return

        print("\n--- Search Results ---")

        for subject, title, content in results:
            print(f"\nSubject: {subject}")
            print(f"Title: {title}")
            print(f"Note: {content}")

    # ---------- STUDY PLAN ----------

    def generate_study_plan(self):
        cursor = self.db.connection.cursor()

        cursor.execute("""
            SELECT
                subjects.name,
                subjects.total_topics,
                subjects.completed_topics,
                tasks.title,
                tasks.deadline
            FROM subjects
            LEFT JOIN tasks
            ON subjects.id = tasks.subject_id
            WHERE tasks.completed = 0
            ORDER BY tasks.deadline
        """)

        tasks = cursor.fetchall()

        if not tasks:
            print("No pending tasks.")
            return

        print("\n===== STUDY PLAN =====")

        today = datetime.today().date()

        for subject, total, completed, title, deadline in tasks:

            deadline_date = datetime.strptime(
                deadline, "%Y-%m-%d"
            ).date()

            days_left = (deadline_date - today).days

            remaining_topics = total - completed

            if days_left <= 0:
                priority = "URGENT"
            elif days_left <= 3:
                priority = "HIGH"
            elif days_left <= 7:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            if days_left > 0:
                topics_per_day = remaining_topics / days_left
            else:
                topics_per_day = remaining_topics

            print(f"\nSubject: {subject}")
            print(f"Task: {title}")
            print(f"Deadline: {deadline}")
            print(f"Days remaining: {days_left}")
            print(f"Priority: {priority}")
            print(
                f"Recommended topics/day: "
                f"{topics_per_day:.1f}"
            )

    # ---------- DASHBOARD ----------

    def dashboard(self):
        cursor = self.db.connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*),
                SUM(total_topics),
                SUM(completed_topics)
            FROM subjects
        """)

        result = cursor.fetchone()

        subjects = result[0] or 0
        total_topics = result[1] or 0
        completed_topics = result[2] or 0

        if total_topics > 0:
            progress = (
                completed_topics /
                total_topics
            ) * 100
        else:
            progress = 0

        cursor.execute("""
            SELECT COUNT(*)
            FROM tasks
            WHERE completed = 0
        """)

        pending_tasks = cursor.fetchone()[0]

        print("\n===== STUDY DASHBOARD =====")
        print(f"Subjects: {subjects}")
        print(f"Topics completed: {completed_topics}/{total_topics}")
        print(f"Overall progress: {progress:.1f}%")
        print(f"Pending tasks: {pending_tasks}")

    # ---------- MENU ----------

    def run(self):

        while True:

            print("""
=================================
       AI STUDY ASSISTANT
=================================

1. Add Subject
2. View Subjects
3. Update Study Progress

4. Add Task
5. View Tasks
6. Complete Task

7. Add Note
8. Search Notes

9. Generate Study Plan
10. Dashboard

0. Exit
""")

            choice = input("Choose an option: ")

            if choice == "1":
                self.add_subject()

            elif choice == "2":
                self.view_subjects()

            elif choice == "3":
                self.update_progress()

            elif choice == "4":
                self.add_task()

            elif choice == "5":
                self.view_tasks()

            elif choice == "6":
                self.complete_task()

            elif choice == "7":
                self.add_note()

            elif choice == "8":
                self.search_notes()

            elif choice == "9":
                self.generate_study_plan()

            elif choice == "10":
                self.dashboard()

            elif choice == "0":
                self.db.close()
                print("Goodbye!")
                break

            else:
                print("Invalid choice.")


if __name__ == "__main__":
    app = StudyAssistant()
    app.run()
