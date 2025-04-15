# Library Management System

A comprehensive library management system built with Python and Oracle Database.

## Features

- User Authentication (Librarian and Member login)
- Book Management
  - Add new books
  - Search books
  - View book details
  - Update book information
- Member Management
  - Add new members
  - View member details
  - Track member history
- Book Transactions
  - Issue books
  - Return books
  - Track due dates
- Fine Management
  - Automatic fine calculation
  - Fine payment processing
  - Fine history tracking
- Reports and Statistics
  - Book availability
  - Member activity
  - Fine collection

## Prerequisites

- Python 3.x
- Oracle Database 21c Express Edition
- cx_Oracle Python package
- tkinter (usually comes with Python)

## Installation

1. Install Oracle Database 21c Express Edition
   - Download from Oracle's website
   - Follow installation instructions

2. Install required Python packages:
   ```bash
   pip install cx_Oracle
   ```

3. Set up the database:
   - Open SQL*Plus
   - Connect as SYSTEM user
   - Run the setup script:
     ```sql
     @setup_database.sql
     ```

## Configuration

1. Database Connection:
   - Default connection details:
     - Username: system
     - Password: 123RA*ra
     - Host: localhost
     - Port: 1521
     - Service: xe

2. Update connection details in `library_app.py` if needed:
   ```python
   conn = cx_Oracle.connect('system/123RA*ra@localhost:1521/xe')
   ```

## Usage

1. Start the application:
   ```bash
   python library_app.py
   ```

2. Login:
   - Librarian Login:
     - Username: L001
     - Password: password123
   - Member Login:
     - Use your member ID and password

3. Main Features:
   - Librarian View:
     - Manage books
     - Manage members
     - Process book issues and returns
     - View and manage fines
   - Member View:
     - View available books
     - Check issued books
     - View and pay fines
     - View personal history

## Database Schema

The system uses the following main tables:
- BOOKS: Stores book information
- MEMBER: Stores member details
- LIBRARIAN: Stores librarian information
- ISSUED_BOOKS: Tracks book issues
- FINES: Manages fine records

## Troubleshooting

1. Database Connection Issues:
   - Verify Oracle Database is running
   - Check connection credentials
   - Ensure Oracle client is properly installed

2. Application Errors:
   - Check Python version compatibility
   - Verify all required packages are installed
   - Check database schema integrity

## Support

For issues and support, please check the explanations directory for detailed documentation.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 