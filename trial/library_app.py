import customtkinter as ctk
from tkinter import messagebox, ttk
import oracledb
import uuid
from datetime import datetime, timedelta
import logging
import os
import sys
import random
import string

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
        logger.info("DatabaseConnection initialized")
        
    def connect(self, username, password):
        try:
            if self.connection:
                self.connection.close()
            
            self.connection = oracledb.connect(
                user="system",
                password="123RA*ra",
                dsn="localhost:1521/XE"
            )
            self.cursor = self.connection.cursor()
            logger.info("Successfully connected to Oracle Database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
            
    def execute_query(self, query, params=None):
        """Execute a SQL query and return the cursor"""
        try:
            logger.debug(f"Executing query: {query}")
            if params:
                logger.debug(f"With parameters: {params}")
            
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # For non-SELECT queries, commit the transaction
            if not query.strip().upper().startswith("SELECT"):
                self.connection.commit()
            
            return cursor
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            # Rollback in case of error
            self.connection.rollback()
            raise e
            
    def set_auto_commit(self, auto_commit):
        if self.connection:
            self.connection.autocommit = auto_commit
            logger.debug(f"Setting auto-commit to {auto_commit}")
            
    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

class LibraryApp:
    def __init__(self):
        self.db = DatabaseConnection()
        self.setup_ui()
        self.current_user = None
        self.current_user_type = None
        # Enable auto-commit
        self.db.set_auto_commit(True)
        logger.info("Application initialized")
        
    def setup_ui(self):
        # Configure window
        self.window = ctk.CTk()
        self.window.title("Library Management System")
        self.window.geometry("1000x600")
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Create login frame
        self.create_login_frame()
        
    def create_login_frame(self):
        self.login_frame = ctk.CTkFrame(self.main_frame)
        self.login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Title
        title_label = ctk.CTkLabel(self.login_frame, text="Library Management System", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # User type selection
        self.user_type = ctk.CTkOptionMenu(self.login_frame, values=["Librarian", "Member"])
        self.user_type.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Username entry
        username_label = ctk.CTkLabel(self.login_frame, text="Username:")
        username_label.grid(row=2, column=0, padx=10, pady=10)
        self.username_entry = ctk.CTkEntry(self.login_frame)
        self.username_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Password entry
        password_label = ctk.CTkLabel(self.login_frame, text="Password:")
        password_label.grid(row=3, column=0, padx=10, pady=10)
        self.password_entry = ctk.CTkEntry(self.login_frame, show="*")
        self.password_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # Login button
        login_button = ctk.CTkButton(self.login_frame, text="Login", command=self.login)
        login_button.grid(row=4, column=0, columnspan=2, pady=20)
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user_type = self.user_type.get()
        
        try:
            # First connect as system to verify user existence
            if not self.db.connect("system", "123RA*ra"):
                raise Exception("Failed to connect to database")
            
            if user_type == "Librarian":
                # Check if librarian exists
                check_query = "SELECT librarianid FROM LIBRARIAN WHERE librarianid = :1"
                cursor = self.db.execute_query(check_query, (username,))
                if not cursor.fetchone():
                    raise Exception("Invalid librarian ID")
                
                # For librarians, use system credentials
                self.current_user = username
                self.current_user_type = user_type
                self.login_frame.destroy()
                self.create_librarian_dashboard()
            else:  # Member
                # Check if member exists and verify password
                check_query = "SELECT memberid FROM MEMBER WHERE memberid = :1"
                cursor = self.db.execute_query(check_query, (username,))
                if not cursor.fetchone():
                    raise Exception("Invalid member ID")
                
                # For members, just verify they exist in the MEMBER table
                self.current_user = username
                self.current_user_type = user_type
                self.login_frame.destroy()
                self.create_member_dashboard()
                    
        except Exception as e:
            messagebox.showerror("Login Failed", str(e))
            
    def create_librarian_dashboard(self):
        self.dashboard_frame = ctk.CTkFrame(self.main_frame)
        self.dashboard_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Title
        title_label = ctk.CTkLabel(self.dashboard_frame, text="Librarian Dashboard", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Buttons for different operations
        buttons = [
            ("Add Book", self.add_book),
            ("Add Member", self.add_member),
            ("Issue Book", self.issue_book),
            ("Return Book", self.return_book),
            ("View Books", self.view_books),
            ("View Members", self.view_members),
            ("View Fines", self.view_fines),
            ("Logout", self.logout)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = ctk.CTkButton(self.dashboard_frame, text=text, command=command)
            btn.grid(row=i+1, column=0, padx=10, pady=10, sticky="ew")
            
    def create_member_dashboard(self):
        self.dashboard_frame = ctk.CTkFrame(self.main_frame)
        self.dashboard_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Title
        title_label = ctk.CTkLabel(self.dashboard_frame, text="Member Dashboard", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Buttons for different operations
        buttons = [
            ("Search Books", self.search_books),
            ("View Issued Books", self.view_issued_books),
            ("Add Review", self.add_review),
            ("View Fines", self.view_fines),
            ("Logout", self.logout)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = ctk.CTkButton(self.dashboard_frame, text=text, command=command)
            btn.grid(row=i+1, column=0, padx=10, pady=10, sticky="ew")
            
    def add_book(self):
        logger.debug("Starting add_book operation")
        # Create a new window for adding a book
        add_book_window = ctk.CTkToplevel(self.window)
        add_book_window.title("Add New Book")
        add_book_window.geometry("400x500")
        
        # Book details
        ctk.CTkLabel(add_book_window, text="ISBN:").grid(row=0, column=0, padx=10, pady=5)
        isbn_entry = ctk.CTkEntry(add_book_window)
        isbn_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(add_book_window, text="Title:").grid(row=1, column=0, padx=10, pady=5)
        title_entry = ctk.CTkEntry(add_book_window)
        title_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(add_book_window, text="Author:").grid(row=2, column=0, padx=10, pady=5)
        author_entry = ctk.CTkEntry(add_book_window)
        author_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(add_book_window, text="Genre:").grid(row=3, column=0, padx=10, pady=5)
        genre_entry = ctk.CTkEntry(add_book_window)
        genre_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(add_book_window, text="Price:").grid(row=4, column=0, padx=10, pady=5)
        price_entry = ctk.CTkEntry(add_book_window)
        price_entry.grid(row=4, column=1, padx=10, pady=5)
        
        def submit():
            try:
                logger.debug("Submitting new book")
                # First verify the librarian exists
                check_query = "SELECT librarianid FROM LIBRARIAN WHERE librarianid = :1"
                cursor = self.db.execute_query(check_query, (self.current_user,))
                if not cursor.fetchone():
                    raise Exception("Invalid librarian ID")
                
                # Check if ISBN already exists
                check_isbn_query = "SELECT isbn FROM BOOKS WHERE isbn = :1"
                cursor = self.db.execute_query(check_isbn_query, (isbn_entry.get(),))
                if cursor.fetchone():
                    raise Exception("A book with this ISBN already exists")
                
                # Validate inputs
                if not all([isbn_entry.get(), title_entry.get(), author_entry.get(), 
                           genre_entry.get(), price_entry.get()]):
                    raise Exception("All fields are required")
                
                try:
                    price = float(price_entry.get())
                    if price <= 0:
                        raise ValueError
                except ValueError:
                    raise Exception("Price must be a positive number")
                
                query = """
                INSERT INTO BOOKS (isbn, title, author, genre, price, status, librarianid)
                VALUES (:1, :2, :3, :4, :5, 'available', :6)
                """
                params = (
                    isbn_entry.get(),
                    title_entry.get(),
                    author_entry.get(),
                    genre_entry.get(),
                    price,
                    self.current_user
                )
                logger.debug(f"Executing query with params: {params}")
                self.db.execute_query(query, params)
                
                # Verify the book was added
                verify_query = "SELECT * FROM BOOKS WHERE isbn = :1"
                cursor = self.db.execute_query(verify_query, (isbn_entry.get(),))
                if cursor.fetchone():
                    logger.debug("Book successfully added to database")
                    messagebox.showinfo("Success", "Book added successfully!")
                    add_book_window.destroy()
                    # Force refresh of books view if it's open
                    if hasattr(self, 'view_books_window') and self.view_books_window.winfo_exists():
                        for widget in self.view_books_window.winfo_children():
                            if isinstance(widget, ttk.Treeview):
                                self.refresh_view_books(widget)
                                break
                else:
                    raise Exception("Book was not added to database")
            except Exception as e:
                logger.error(f"Error adding book: {str(e)}")
                messagebox.showerror("Error", f"Failed to add book: {str(e)}")
        
        submit_button = ctk.CTkButton(add_book_window, text="Add Book", command=submit)
        submit_button.grid(row=5, column=0, columnspan=2, pady=20)
        
    def issue_book(self):
        """Issue a book to a member"""
        issue_window = ctk.CTkToplevel(self.window)
        issue_window.title("Issue Book")
        issue_window.geometry("400x500")
        
        # Book selection
        ctk.CTkLabel(issue_window, text="Select Book:").grid(row=0, column=0, padx=10, pady=5)
        book_var = ctk.StringVar()
        book_dropdown = ctk.CTkOptionMenu(issue_window, variable=book_var)
        book_dropdown.grid(row=0, column=1, padx=10, pady=5)
        
        # Member selection
        ctk.CTkLabel(issue_window, text="Select Member:").grid(row=1, column=0, padx=10, pady=5)
        member_var = ctk.StringVar()
        member_dropdown = ctk.CTkOptionMenu(issue_window, variable=member_var)
        member_dropdown.grid(row=1, column=1, padx=10, pady=5)
        
        # Issue date input
        ctk.CTkLabel(issue_window, text="Issue Date (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5)
        issue_date_entry = ctk.CTkEntry(issue_window)
        issue_date_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Due date input
        ctk.CTkLabel(issue_window, text="Due Date (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=5)
        due_date_entry = ctk.CTkEntry(issue_window)
        due_date_entry.grid(row=3, column=1, padx=10, pady=5)
        
        def load_books():
            try:
                query = "SELECT isbn, title FROM BOOKS WHERE status = 'available'"
                cursor = self.db.execute_query(query)
                books = [f"{row[0]} - {row[1]}" for row in cursor.fetchall()]
                book_dropdown.configure(values=books)
                if books:
                    book_var.set(books[0])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load books: {str(e)}")
        
        def load_members():
            try:
                query = "SELECT memberid, name FROM MEMBER"
                cursor = self.db.execute_query(query)
                members = [f"{row[0]} - {row[1]}" for row in cursor.fetchall()]
                member_dropdown.configure(values=members)
                if members:
                    member_var.set(members[0])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load members: {str(e)}")
        
        def submit():
            try:
                isbn = book_var.get().split(" - ")[0]
                member_id = member_var.get().split(" - ")[0]
                issue_date = issue_date_entry.get()
                due_date = due_date_entry.get()
                
                # Validate dates
                try:
                    datetime.strptime(issue_date, '%Y-%m-%d')
                    datetime.strptime(due_date, '%Y-%m-%d')
                except ValueError:
                    raise Exception("Invalid date format. Please use YYYY-MM-DD")
                
                # Generate a simple issue ID (current timestamp)
                issue_id = f"ISSUE{int(datetime.now().timestamp())}"
                
                query = """
                BEGIN
                    issue_book(:1, :2, :3, TO_DATE(:4, 'YYYY-MM-DD'), TO_DATE(:5, 'YYYY-MM-DD'));
                END;
                """
                params = (issue_id, member_id, isbn, issue_date, due_date)
                self.db.execute_query(query, params)
                
                messagebox.showinfo("Success", f"Book issued successfully!\nIssue ID: {issue_id}")
                issue_window.destroy()
                self.refresh_database()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to issue book: {str(e)}")
        
        load_books()
        load_members()
        
        submit_button = ctk.CTkButton(issue_window, text="Issue Book", command=submit)
        submit_button.grid(row=4, column=0, columnspan=2, pady=20)
        
    def return_book(self):
        """Return a book to the library"""
        return_window = ctk.CTkToplevel(self.window)
        return_window.title("Return Book")
        return_window.geometry("400x300")
        
        # Get issued books
        query = """
        SELECT i.issueid, b.title, m.name 
        FROM ISSUED_BOOKS i 
        JOIN BOOKS b ON i.isbn = b.isbn 
        JOIN MEMBER m ON i.memberid = m.memberid 
        WHERE i.return_date IS NULL
        """
        cursor = self.db.execute_query(query)
        issued_books = cursor.fetchall()
        
        ctk.CTkLabel(return_window, text="Select Book:").grid(row=0, column=0, padx=10, pady=5)
        book_var = ctk.StringVar()
        book_dropdown = ctk.CTkOptionMenu(return_window, 
            values=[f"{book[0]} - {book[1]} ({book[2]})" for book in issued_books], 
            variable=book_var)
        book_dropdown.grid(row=0, column=1, padx=10, pady=5)
        
        # Return date input
        ctk.CTkLabel(return_window, text="Return Date (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        return_date_entry = ctk.CTkEntry(return_window)
        return_date_entry.grid(row=1, column=1, padx=10, pady=5)
        
        def submit():
            try:
                issue_id = book_var.get().split(" - ")[0]
                return_date = return_date_entry.get()
                
                # Validate date
                try:
                    datetime.strptime(return_date, '%Y-%m-%d')
                except ValueError:
                    raise Exception("Invalid date format. Please use YYYY-MM-DD")
                
                # Call the PL/SQL procedure
                query = """
                BEGIN
                    return_book(:1, TO_DATE(:2, 'YYYY-MM-DD'));
                END;
                """
                self.db.execute_query(query, (issue_id, return_date))
                messagebox.showinfo("Success", "Book returned successfully!")
                return_window.destroy()
                
                # Refresh all open windows
                self.refresh_database()
                
                # If fines window is open, refresh it
                if hasattr(self, 'view_fines_window') and self.view_fines_window.winfo_exists():
                    for widget in self.view_fines_window.winfo_children():
                        if isinstance(widget, ttk.Treeview):
                            self.refresh_view_fines(widget)
                            break
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to return book: {str(e)}")
        
        submit_button = ctk.CTkButton(return_window, text="Return Book", command=submit)
        submit_button.grid(row=2, column=0, columnspan=2, pady=20)
        
    def view_books(self):
        # Create a new window for viewing books
        self.view_books_window = ctk.CTkToplevel(self.window)
        self.view_books_window.title("View Books")
        self.view_books_window.geometry("800x400")
        
        # Create treeview
        tree = ttk.Treeview(self.view_books_window, columns=("ISBN", "Title", "Author", "Genre", "Price", "Status"))
        tree.heading("#0", text="")
        tree.heading("ISBN", text="ISBN")
        tree.heading("Title", text="Title")
        tree.heading("Author", text="Author")
        tree.heading("Genre", text="Genre")
        tree.heading("Price", text="Price")
        tree.heading("Status", text="Status")
        
        # Set column widths
        tree.column("#0", width=0, stretch=False)
        tree.column("ISBN", width=150)
        tree.column("Title", width=200)
        tree.column("Author", width=150)
        tree.column("Genre", width=100)
        tree.column("Price", width=100)
        tree.column("Status", width=100)
        
        # Get books
        query = "SELECT isbn, title, author, genre, price, status FROM BOOKS ORDER BY title"
        cursor = self.db.execute_query(query)
        books = cursor.fetchall()
        
        for book in books:
            tree.insert("", "end", values=book)
        
        tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Add refresh button
        refresh_button = ctk.CTkButton(self.view_books_window, text="Refresh", 
                                     command=lambda: self.refresh_view_books(tree))
        refresh_button.pack(pady=10)
        
    def refresh_view_books(self, tree):
        """Refresh the books view"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
                
            # Get updated books
            query = "SELECT isbn, title, author, genre, price, status FROM BOOKS ORDER BY title"
            cursor = self.db.execute_query(query)
            books = cursor.fetchall()
            
            for book in books:
                tree.insert("", "end", values=book)
                
        except Exception as e:
            logger.error(f"Failed to refresh books view: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh books view: {str(e)}")
            
    def view_members(self):
        # Create a new window for viewing members
        self.view_members_window = ctk.CTkToplevel(self.window)
        self.view_members_window.title("View Members")
        self.view_members_window.geometry("600x400")
        
        # Create treeview
        tree = ttk.Treeview(self.view_members_window, columns=("Member ID", "Name", "Phone"))
        tree.heading("#0", text="")
        tree.heading("Member ID", text="Member ID")
        tree.heading("Name", text="Name")
        tree.heading("Phone", text="Phone")
        
        # Set column widths
        tree.column("#0", width=0, stretch=False)
        tree.column("Member ID", width=150)
        tree.column("Name", width=200)
        tree.column("Phone", width=150)
        
        # Get members
        query = "SELECT memberid, name, phoneno FROM MEMBER ORDER BY name"
        cursor = self.db.execute_query(query)
        members = cursor.fetchall()
        
        for member in members:
            tree.insert("", "end", values=member)
        
        tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Add refresh button
        refresh_button = ctk.CTkButton(self.view_members_window, text="Refresh", 
                                     command=lambda: self.refresh_view_members(tree))
        refresh_button.pack(pady=10)
        
    def refresh_view_members(self, tree):
        """Refresh the members view"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
                
            # Get updated members
            query = "SELECT memberid, name, phoneno FROM MEMBER ORDER BY name"
            cursor = self.db.execute_query(query)
            members = cursor.fetchall()
            
            for member in members:
                tree.insert("", "end", values=member)
                
        except Exception as e:
            logger.error(f"Failed to refresh members view: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh members view: {str(e)}")
        
    def view_fines(self):
        """View and pay fines"""
        self.view_fines_window = ctk.CTkToplevel(self.window)
        self.view_fines_window.title("View Fines")
        self.view_fines_window.geometry("800x400")
        
        # Create treeview
        tree = ttk.Treeview(self.view_fines_window, columns=("Fine ID", "Issue ID", "Amount", "Status", "Payment Date"))
        tree.heading("#0", text="")
        tree.heading("Fine ID", text="Fine ID")
        tree.heading("Issue ID", text="Issue ID")
        tree.heading("Amount", text="Amount")
        tree.heading("Status", text="Status")
        tree.heading("Payment Date", text="Payment Date")
        
        # Set column widths
        tree.column("#0", width=0, stretch=False)
        tree.column("Fine ID", width=150)
        tree.column("Issue ID", width=150)
        tree.column("Amount", width=100)
        tree.column("Status", width=100)
        tree.column("Payment Date", width=150)
        
        # Get fines
        query = """
        SELECT f.fineid, f.issueid, f.fine_amount, f.paid_status, 
               TO_CHAR(f.payment_date, 'YYYY-MM-DD') as payment_date,
               i.memberid
        FROM FINES f 
        JOIN ISSUED_BOOKS i ON f.issueid = i.issueid
        """
        if self.current_user_type == "Member":
            query += " WHERE i.memberid = :1"
            cursor = self.db.execute_query(query, (self.current_user,))
        else:
            cursor = self.db.execute_query(query)
        
        fines = cursor.fetchall()
        
        for fine in fines:
            tree.insert("", "end", values=fine)
        
        tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        def pay_fine():
            try:
                selected_item = tree.selection()
                if not selected_item:
                    raise Exception("Please select a fine to pay")
                
                fine_data = tree.item(selected_item[0])['values']
                fine_id = fine_data[0]
                member_id = fine_data[5]  # Get the member_id from the query result
                
                # Check if fine is already paid
                if fine_data[3] == 'paid':
                    raise Exception("This fine has already been paid")
                
                # Call the pay_fine procedure
                query = """
                BEGIN
                    pay_fine(:1, :2);
                END;
                """
                self.db.execute_query(query, (fine_id, member_id))
                
                messagebox.showinfo("Success", "Fine paid successfully!")
                self.refresh_view_fines(tree)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to pay fine: {str(e)}")
        
        # Add pay button for both members and librarians
        pay_button = ctk.CTkButton(self.view_fines_window, text="Pay Selected Fine", command=pay_fine)
        pay_button.pack(pady=10)
        
        # Add refresh button
        refresh_button = ctk.CTkButton(self.view_fines_window, text="Refresh", 
                                     command=lambda: self.refresh_view_fines(tree))
        refresh_button.pack(pady=10)

    def refresh_view_fines(self, tree):
        """Refresh the fines view"""
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
            
            # Get fines
            query = """
            SELECT f.fineid, f.issueid, f.fine_amount, f.paid_status, 
                   TO_CHAR(f.payment_date, 'YYYY-MM-DD') as payment_date,
                   i.memberid
            FROM FINES f 
            JOIN ISSUED_BOOKS i ON f.issueid = i.issueid
            """
            if self.current_user_type == "Member":
                query += " WHERE i.memberid = :1"
                cursor = self.db.execute_query(query, (self.current_user,))
            else:
                cursor = self.db.execute_query(query)
            
            fines = cursor.fetchall()
            
            for fine in fines:
                tree.insert("", "end", values=fine)
                
        except Exception as e:
            logger.error(f"Error refreshing fines view: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh fines: {str(e)}")
            
    def search_books(self):
        # Create a new window for searching books
        search_window = ctk.CTkToplevel(self.window)
        search_window.title("Search Books")
        search_window.geometry("800x600")
        
        # Create search options frame
        search_frame = ctk.CTkFrame(search_window)
        search_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Search type selection
        ctk.CTkLabel(search_frame, text="Search by:").grid(row=0, column=0, padx=10, pady=5)
        search_type = ctk.CTkOptionMenu(search_frame, values=[
            "Title", "Author", "Genre", "ISBN", 
            "Price (Less than)", "Price (More than)", 
            "Status", "All Books"
        ])
        search_type.grid(row=0, column=1, padx=10, pady=5)
        
        # Search value entry
        ctk.CTkLabel(search_frame, text="Search Value:").grid(row=1, column=0, padx=10, pady=5)
        search_value = ctk.CTkEntry(search_frame)
        search_value.grid(row=1, column=1, padx=10, pady=5)
        
        # Create treeview for results
        tree_frame = ctk.CTkFrame(search_window)
        tree_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        
        tree = ttk.Treeview(tree_frame, columns=(
            "isbn", "title", "author", "genre", "price", "status", "rating", "reviews"
        ), show="headings")
        
        # Configure columns
        tree.heading("isbn", text="ISBN")
        tree.heading("title", text="Title")
        tree.heading("author", text="Author")
        tree.heading("genre", text="Genre")
        tree.heading("price", text="Price")
        tree.heading("status", text="Status")
        tree.heading("rating", text="Avg Rating")
        tree.heading("reviews", text="Reviews")
        
        # Set column widths
        tree.column("isbn", width=100)
        tree.column("title", width=200)
        tree.column("author", width=150)
        tree.column("genre", width=100)
        tree.column("price", width=100)
        tree.column("status", width=100)
        tree.column("rating", width=100)
        tree.column("reviews", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid the treeview and scrollbar
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        def search():
            try:
                # Clear existing items
                for item in tree.get_children():
                    tree.delete(item)
                
                # Map UI search type to PL/SQL search type
                search_type_map = {
                    "Title": "TITLE",
                    "Author": "AUTHOR",
                    "Genre": "GENRE",
                    "ISBN": "ISBN",
                    "Price (Less than)": "PRICE_LESS",
                    "Price (More than)": "PRICE_MORE",
                    "Status": "STATUS",
                    "All Books": "ALL"
                }
                
                # Get search parameters
                search_type_value = search_type_map[search_type.get()]
                search_value_text = search_value.get()
                
                # Call the PL/SQL function
                query = """
                BEGIN
                    :cursor := search_books(:search_type, :search_value);
                END;
                """
                
                # Execute the query
                cursor = self.db.execute_query(query, {
                    "cursor": self.db.cursor,
                    "search_type": search_type_value,
                    "search_value": search_value_text
                })
                
                # Fetch and display results
                while True:
                    row = cursor.fetchone()
                    if not row:
                        break
                    
                    # Format the data
                    formatted_row = (
                        row[0],  # isbn
                        row[1],  # title
                        row[2],  # author
                        row[3],  # genre
                        f"${row[4]:.2f}",  # price
                        row[5],  # status
                        f"{row[6]:.1f}" if row[6] else "N/A",  # avg_rating
                        str(row[7]) if row[7] else "0"  # total_reviews
                    )
                    
                    tree.insert("", "end", values=formatted_row)
                
                if not tree.get_children():
                    messagebox.showinfo("Search Results", "No books found matching your criteria.")
                    
            except Exception as e:
                messagebox.showerror("Search Error", str(e))
        
        # Search button
        search_button = ctk.CTkButton(search_frame, text="Search", command=search)
        search_button.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Configure grid weights
        search_window.grid_columnconfigure(0, weight=1)
        search_window.grid_rowconfigure(1, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
    def view_issued_books(self):
        # Create a new window for viewing issued books
        view_window = ctk.CTkToplevel(self.window)
        view_window.title("View Issued Books")
        view_window.geometry("800x400")
        
        # Create treeview
        tree = ttk.Treeview(view_window, columns=("Issue ID", "Book Title", "Issue Date", "Due Date", "Return Date"))
        tree.heading("#0", text="")
        tree.heading("Issue ID", text="Issue ID")
        tree.heading("Book Title", text="Book Title")
        tree.heading("Issue Date", text="Issue Date")
        tree.heading("Due Date", text="Due Date")
        tree.heading("Return Date", text="Return Date")
        
        # Get issued books
        query = """
        SELECT i.issueid, b.title, i.issued_date, i.due_date, i.return_date 
        FROM ISSUED_BOOKS i 
        JOIN BOOKS b ON i.isbn = b.isbn 
        WHERE i.memberid = :1
        """
        cursor = self.db.execute_query(query, (self.current_user,))
        issued_books = cursor.fetchall()
        
        for book in issued_books:
            tree.insert("", "end", values=book)
        
        tree.pack(expand=True, fill="both", padx=10, pady=10)
        
    def add_review(self):
        # Create a new window for adding a review
        review_window = ctk.CTkToplevel(self.window)
        review_window.title("Add Review")
        review_window.geometry("400x300")
        
        # Get books
        query = "SELECT isbn, title FROM BOOKS ORDER BY title"
        cursor = self.db.execute_query(query)
        books = cursor.fetchall()
        
        if not books:
            messagebox.showerror("Error", "No books available for review")
            review_window.destroy()
            return
        
        ctk.CTkLabel(review_window, text="Select Book:").grid(row=0, column=0, padx=10, pady=5)
        book_var = ctk.StringVar()
        book_dropdown = ctk.CTkOptionMenu(review_window, values=[f"{book[0]} - {book[1]}" for book in books], variable=book_var)
        book_dropdown.grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(review_window, text="Rating (1-5):").grid(row=1, column=0, padx=10, pady=5)
        rating_var = ctk.StringVar(value="5")
        rating_dropdown = ctk.CTkOptionMenu(review_window, values=["1", "2", "3", "4", "5"], variable=rating_var)
        rating_dropdown.grid(row=1, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(review_window, text="Review Text:").grid(row=2, column=0, padx=10, pady=5)
        review_text = ctk.CTkTextbox(review_window, height=100)
        review_text.grid(row=2, column=1, padx=10, pady=5)
        
        def submit():
            try:
                if not book_var.get():
                    raise Exception("Please select a book")
                
                isbn = book_var.get().split(" - ")[0]
                rating = int(rating_var.get())
                review = review_text.get("1.0", "end-1c").strip()
                
                if not review:
                    raise Exception("Please enter a review text")
                
                # Generate a unique review ID
                review_id = f"REV{int(datetime.now().timestamp())}"
                
                query = """
                INSERT INTO REVIEWS (reviewid, memberid, isbn, rating, reviewtxt, reviewdate)
                VALUES (:1, :2, :3, :4, :5, SYSDATE)
                """
                self.db.execute_query(query, (review_id, self.current_user, isbn, rating, review))
                messagebox.showinfo("Success", "Review added successfully!")
                review_window.destroy()
                self.refresh_database()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add review: {str(e)}")
        
        submit_button = ctk.CTkButton(review_window, text="Submit Review", command=submit)
        submit_button.grid(row=3, column=0, columnspan=2, pady=20)
        
    def add_member(self):
        """Add a new member to the database"""
        add_member_window = ctk.CTkToplevel(self.window)
        add_member_window.title("Add New Member")
        add_member_window.geometry("400x400")
        
        # Member details
        ctk.CTkLabel(add_member_window, text="Member ID:").grid(row=0, column=0, padx=10, pady=5)
        member_id_entry = ctk.CTkEntry(add_member_window)
        member_id_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(add_member_window, text="Name:").grid(row=1, column=0, padx=10, pady=5)
        name_entry = ctk.CTkEntry(add_member_window)
        name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(add_member_window, text="Phone Number:").grid(row=2, column=0, padx=10, pady=5)
        phone_entry = ctk.CTkEntry(add_member_window)
        phone_entry.grid(row=2, column=1, padx=10, pady=5)
        
        def submit():
            try:
                # Validate inputs
                if not all([member_id_entry.get(), name_entry.get(), phone_entry.get()]):
                    raise Exception("All fields are required")
                
                # Check if member ID already exists
                cursor = self.db.execute_query("SELECT memberid FROM MEMBER WHERE memberid = :1", (member_id_entry.get(),))
                if cursor.fetchone():
                    raise Exception("Member ID already exists")
                
                # Check if phone number already exists
                cursor = self.db.execute_query("SELECT phoneno FROM MEMBER WHERE phoneno = :1", (phone_entry.get(),))
                if cursor.fetchone():
                    raise Exception("Phone number already registered")
                
                # Insert new member
                query = """
                INSERT INTO MEMBER (memberid, name, phoneno)
                VALUES (:1, :2, :3)
                """
                params = (
                    member_id_entry.get(),
                    name_entry.get(),
                    phone_entry.get()
                )
                self.db.execute_query(query, params)
                
                # Explicitly commit the transaction
                self.db.connection.commit()
                
                messagebox.showinfo("Success", "Member added successfully!")
                add_member_window.destroy()
                # Force refresh of members view if it's open
                if hasattr(self, 'view_members_window') and self.view_members_window.winfo_exists():
                    for widget in self.view_members_window.winfo_children():
                        if isinstance(widget, ttk.Treeview):
                            self.refresh_view_members(widget)
                            break
                
            except Exception as e:
                # Rollback in case of error
                self.db.connection.rollback()
                messagebox.showerror("Error", f"Failed to add member: {str(e)}")
        
        submit_button = ctk.CTkButton(add_member_window, text="Add Member", command=submit)
        submit_button.grid(row=4, column=0, columnspan=2, pady=20)
        
    def logout(self):
        """Logout and return to login screen"""
        self.dashboard_frame.destroy()
        self.create_login_frame()
        self.current_user = None
        self.current_user_type = None
        messagebox.showinfo("Logout", "You have been logged out successfully.")
        
    def refresh_database(self):
        """Refresh the database connection and update UI"""
        try:
            logger.debug("Refreshing database connection")
            # Reconnect using system credentials
            if not self.db.connect("system", "123RA*ra"):
                raise Exception("Failed to reconnect to database")
            
            # Update any open windows with new data
            self.update_open_windows()
            logger.debug("Database refresh completed")
            
        except Exception as e:
            logger.error(f"Failed to refresh database: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh database: {str(e)}")
            
    def update_open_windows(self):
        """Update any open windows with fresh data"""
        logger.debug("Updating open windows")
        try:
            # Store references to existing windows
            books_window = getattr(self, 'view_books_window', None)
            members_window = getattr(self, 'view_members_window', None)
            fines_window = getattr(self, 'view_fines_window', None)
            issued_window = getattr(self, 'view_issued_books_window', None)
            
            # Update only if windows exist and are not destroyed
            if books_window and books_window.winfo_exists():
                for widget in books_window.winfo_children():
                    if isinstance(widget, ttk.Treeview):
                        self.refresh_view_books(widget)
                        break
                        
            if members_window and members_window.winfo_exists():
                for widget in members_window.winfo_children():
                    if isinstance(widget, ttk.Treeview):
                        self.refresh_view_members(widget)
                        break
                        
            if fines_window and fines_window.winfo_exists():
                for widget in fines_window.winfo_children():
                    if isinstance(widget, ttk.Treeview):
                        self.refresh_view_fines(widget)
                        break
                
            if issued_window and issued_window.winfo_exists():
                self.view_issued_books()
                
            logger.debug("Windows update completed")
            
        except Exception as e:
            logger.error(f"Failed to update windows: {str(e)}")
            
    def run(self):
        self.window.mainloop()

def connect_to_db():
    """Connect to the Oracle database"""
    try:
        connection = oracledb.connect(
            user="system",
            password="123RA*ra",
            dsn="localhost:1521/XE"
        )
        print("Connected to Oracle Database")
        return connection
    except oracledb.Error as error:
        print(f"Error connecting to Oracle Database: {error}")
        sys.exit(1)

def execute_sql(connection, sql, params=None):
    """Execute SQL statement and return results"""
    try:
        cursor = connection.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # If it's a SELECT statement, return the results
        if sql.strip().upper().startswith("SELECT"):
            return cursor.fetchall()
        
        # For other statements, commit the transaction
        connection.commit()
        return None
    except oracledb.Error as error:
        print(f"Error executing SQL: {error}")
        connection.rollback()
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()

def run_sqlplus_command(command):
    """Run a command in SQL*Plus and display the output"""
    try:
        # Create a temporary SQL script
        with open("temp_command.sql", "w") as f:
            f.write("SET SERVEROUTPUT ON\n")
            f.write(command + "\n")
            f.write("EXIT;\n")
        
        # Run the SQL script using SQL*Plus
        os.system(f'sqlplus system/123RA*ra @temp_command.sql')
        
        # Clean up
        os.remove("temp_command.sql")
    except Exception as e:
        print(f"Error running SQL*Plus command: {e}")

def add_member(connection, member_id, name, phone):
    """Add a new member to the database"""
    sql = """
    BEGIN
        add_member(:member_id, :name, :phone);
    END;
    """
    params = {
        "member_id": member_id,
        "name": name,
        "phone": phone
    }
    
    execute_sql(connection, sql, params)
    
    # Run the command in SQL*Plus to see the output
    run_sqlplus_command(f"EXEC add_member('{member_id}', '{name}', '{phone}');")

def add_book(connection, isbn, title, author, genre, price, librarian_id):
    """Add a new book to the database"""
    sql = """
    INSERT INTO BOOKS (isbn, title, author, genre, price, status, librarianid)
    VALUES (:isbn, :title, :author, :genre, :price, 'available', :librarian_id)
    """
    params = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "genre": genre,
        "price": price,
        "librarian_id": librarian_id
    }
    
    execute_sql(connection, sql, params)
    
    # Run the command in SQL*Plus to see the output
    run_sqlplus_command(f"""
    INSERT INTO BOOKS (isbn, title, author, genre, price, status, librarianid)
    VALUES ('{isbn}', '{title}', '{author}', '{genre}', {price}, 'available', '{librarian_id}');
    COMMIT;
    EXEC refresh_data;
    """)

def issue_book(connection, issue_id, member_id, isbn, issue_date, due_date):
    """Issue a book to a member"""
    sql = """
    BEGIN
        issue_book(:issue_id, :member_id, :isbn, :issue_date, :due_date);
    END;
    """
    params = {
        "issue_id": issue_id,
        "member_id": member_id,
        "isbn": isbn,
        "issue_date": issue_date,
        "due_date": due_date
    }
    
    execute_sql(connection, sql, params)
    
    # Run the command in SQL*Plus to see the output
    run_sqlplus_command(f"""
    EXEC issue_book('{issue_id}', '{member_id}', '{isbn}', TO_DATE('{issue_date}', 'YYYY-MM-DD'), TO_DATE('{due_date}', 'YYYY-MM-DD'));
    """)

def return_book(connection, issue_id, return_date):
    """Return a book"""
    sql = """
    BEGIN
        return_book(:issue_id, :return_date);
    END;
    """
    params = {
        "issue_id": issue_id,
        "return_date": return_date
    }
    
    execute_sql(connection, sql, params)
    
    # Run the command in SQL*Plus to see the output
    run_sqlplus_command(f"""
    EXEC return_book('{issue_id}', TO_DATE('{return_date}', 'YYYY-MM-DD'));
    """)

def pay_fine(connection, fine_id, member_id):
    """Pay a fine"""
    sql = """
    BEGIN
        pay_fine(:fine_id, :member_id);
    END;
    """
    params = {
        "fine_id": fine_id,
        "member_id": member_id
    }
    
    execute_sql(connection, sql, params)
    
    # Run the command in SQL*Plus to see the output
    run_sqlplus_command(f"""
    EXEC pay_fine('{fine_id}', '{member_id}');
    """)

def add_review(connection, review_id, member_id, isbn, rating, review_text):
    """Add a book review"""
    sql = """
    INSERT INTO REVIEWS (reviewid, memberid, isbn, rating, reviewtxt, reviewdate)
    VALUES (:review_id, :member_id, :isbn, :rating, :review_text, SYSDATE)
    """
    params = {
        "review_id": review_id,
        "member_id": member_id,
        "isbn": isbn,
        "rating": rating,
        "review_text": review_text
    }
    
    execute_sql(connection, sql, params)
    
    # Run the command in SQL*Plus to see the output
    run_sqlplus_command(f"""
    INSERT INTO REVIEWS (reviewid, memberid, isbn, rating, reviewtxt, reviewdate)
    VALUES ('{review_id}', '{member_id}', '{isbn}', {rating}, '{review_text}', SYSDATE);
    COMMIT;
    EXEC refresh_data;
    """)

def generate_random_id(prefix, length=10):
    """Generate a random ID with the given prefix"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}{random_part}"

def main():
    """Main function to demonstrate the library application"""
    app = LibraryApp()
    app.run()

if __name__ == "__main__":
    main() 