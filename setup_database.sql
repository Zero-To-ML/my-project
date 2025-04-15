-- First, disable all triggers
ALTER TABLE ISSUED_BOOKS DISABLE ALL TRIGGERS;

-- Drop existing tables if they exist
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE REVIEWS';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE FINES';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE ISSUED_BOOKS';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE BOOKS';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE MEMBER';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE LIBRARIAN';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
/

-- Create tables
CREATE TABLE LIBRARIAN (
    librarianid   VARCHAR(10) PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    contact       VARCHAR(15) UNIQUE NOT NULL,
    salary        DECIMAL(10,2) NOT NULL
);

CREATE TABLE MEMBER (
    memberid   VARCHAR(10) PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    phoneno    VARCHAR(15) UNIQUE NOT NULL
);

CREATE TABLE BOOKS (
    isbn          VARCHAR(20) PRIMARY KEY,
    title         VARCHAR(255) NOT NULL,
    author        VARCHAR(255) NOT NULL,
    genre         VARCHAR(100) NOT NULL,
    price         DECIMAL(10,2) NOT NULL,
    status        VARCHAR(20) CHECK (status IN ('available', 'issued', 'reserved')),
    librarianid   VARCHAR(10) NOT NULL,
    FOREIGN KEY (librarianid) REFERENCES LIBRARIAN(librarianid) ON DELETE SET NULL
);

CREATE TABLE ISSUED_BOOKS (
    issueid      VARCHAR(20) PRIMARY KEY,
    memberid     VARCHAR(10) NOT NULL,
    isbn         VARCHAR(20) NOT NULL,
    issued_date  DATE NOT NULL,
    due_date     DATE NOT NULL,
    return_date  DATE,
    FOREIGN KEY (memberid) REFERENCES MEMBER(memberid) ON DELETE CASCADE,
    FOREIGN KEY (isbn) REFERENCES BOOKS(isbn) ON DELETE CASCADE
);

CREATE TABLE FINES (
    fineid       VARCHAR(20) PRIMARY KEY,
    issueid      VARCHAR(20) NOT NULL,
    fine_amount  DECIMAL(10,2) NOT NULL,
    paid_status  VARCHAR(10) CHECK (paid_status IN ('paid', 'unpaid')) NOT NULL,
    payment_date DATE,
    FOREIGN KEY (issueid) REFERENCES ISSUED_BOOKS(issueid) ON DELETE CASCADE
);

CREATE TABLE REVIEWS (
    reviewid     VARCHAR(20) PRIMARY KEY,
    memberid     VARCHAR(10) NOT NULL,
    isbn         VARCHAR(20) NOT NULL,
    rating       INT CHECK (rating BETWEEN 1 AND 5) NOT NULL,
    reviewtxt    VARCHAR(250),
    reviewdate   DATE NOT NULL,
    FOREIGN KEY (memberid) REFERENCES MEMBER(memberid) ON DELETE CASCADE,
    FOREIGN KEY (isbn) REFERENCES BOOKS(isbn) ON DELETE CASCADE
);

-- Insert sample librarian
INSERT INTO LIBRARIAN (librarianid, name, email, contact, salary)
VALUES ('L001', 'Admin Librarian', 'admin@library.com', '1234567890', 50000.00);

-- Create procedure to refresh SQL*Plus session data
CREATE OR REPLACE PROCEDURE refresh_data AS
BEGIN
    -- Enable DBMS_OUTPUT
    DBMS_OUTPUT.ENABLE;
    
    -- Display current data
    DBMS_OUTPUT.PUT_LINE('=== CURRENT LIBRARY DATA ===');
    
    -- Display members
    DBMS_OUTPUT.PUT_LINE('MEMBERS:');
    FOR m IN (SELECT * FROM MEMBER ORDER BY memberid) LOOP
        DBMS_OUTPUT.PUT_LINE('  ' || m.memberid || ' - ' || m.name || ' (' || m.phoneno || ')');
    END LOOP;
    
    -- Display books
    DBMS_OUTPUT.PUT_LINE('BOOKS:');
    FOR b IN (SELECT * FROM BOOKS ORDER BY isbn) LOOP
        DBMS_OUTPUT.PUT_LINE('  ' || b.isbn || ' - ' || b.title || ' by ' || b.author || ' (' || b.status || ')');
    END LOOP;
    
    -- Display issued books
    DBMS_OUTPUT.PUT_LINE('ISSUED BOOKS:');
    FOR i IN (SELECT ib.*, m.name as member_name, b.title as book_title 
              FROM ISSUED_BOOKS ib 
              JOIN MEMBER m ON ib.memberid = m.memberid
              JOIN BOOKS b ON ib.isbn = b.isbn
              ORDER BY ib.issueid) LOOP
        DBMS_OUTPUT.PUT_LINE('  ' || i.issueid || ' - ' || i.book_title || ' issued to ' || i.member_name || 
                            ' (Due: ' || TO_CHAR(i.due_date, 'DD-MON-YYYY') || 
                            CASE WHEN i.return_date IS NOT NULL THEN ', Returned: ' || TO_CHAR(i.return_date, 'DD-MON-YYYY') ELSE '' END || ')');
    END LOOP;
    
    -- Display fines
    DBMS_OUTPUT.PUT_LINE('FINES:');
    FOR f IN (SELECT f.*, ib.memberid, m.name as member_name
              FROM FINES f
              JOIN ISSUED_BOOKS ib ON f.issueid = ib.issueid
              JOIN MEMBER m ON ib.memberid = m.memberid
              ORDER BY f.fineid) LOOP
        DBMS_OUTPUT.PUT_LINE('  ' || f.fineid || ' - Rs.' || f.fine_amount || ' (' || f.paid_status || 
                            CASE WHEN f.payment_date IS NOT NULL THEN ', Paid: ' || TO_CHAR(f.payment_date, 'DD-MON-YYYY') ELSE '' END || 
                            ') for member ' || f.member_name);
    END LOOP;
    
    -- Display reviews
    DBMS_OUTPUT.PUT_LINE('REVIEWS:');
    FOR r IN (SELECT r.*, m.name as member_name, b.title as book_title
              FROM REVIEWS r
              JOIN MEMBER m ON r.memberid = m.memberid
              JOIN BOOKS b ON r.isbn = b.isbn
              ORDER BY r.reviewid) LOOP
        DBMS_OUTPUT.PUT_LINE('  ' || r.reviewid || ' - ' || r.book_title || ' rated ' || r.rating || '/5 by ' || r.member_name);
    END LOOP;
    
    DBMS_OUTPUT.PUT_LINE('=== END OF DATA ===');
END;
/

-- Create procedure to pay fine
CREATE OR REPLACE PROCEDURE pay_fine(
    p_fine_id IN VARCHAR2,
    p_member_id IN VARCHAR2
) AS
    v_member_exists NUMBER;
BEGIN
    -- Check if member exists
    SELECT COUNT(*) INTO v_member_exists
    FROM MEMBER
    WHERE memberid = p_member_id;
    
    IF v_member_exists = 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Only registered members can pay fines.');
    END IF;
    
    -- Check if fine exists and belongs to this member
    SELECT COUNT(*) INTO v_member_exists
    FROM FINES f
    JOIN ISSUED_BOOKS ib ON f.issueid = ib.issueid
    WHERE f.fineid = p_fine_id
    AND ib.memberid = p_member_id;
    
    IF v_member_exists = 0 THEN
        RAISE_APPLICATION_ERROR(-20002, 'Fine does not exist or does not belong to this member.');
    END IF;
    
    -- Update fine status
    UPDATE FINES 
    SET paid_status = 'paid',
        payment_date = SYSDATE
    WHERE fineid = p_fine_id;
    
    -- Refresh data
    refresh_data;
    
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
/

-- Drop all triggers
BEGIN
    EXECUTE IMMEDIATE 'DROP TRIGGER calculate_fine';
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TRIGGER track_defaulters';
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/

-- Create procedure to return a book
CREATE OR REPLACE PROCEDURE return_book(
    p_issue_id IN VARCHAR2,
    p_return_date IN DATE
) AS
    v_days_late NUMBER;
    v_fine_amount NUMBER(10,2);
    v_fine_id VARCHAR(20);
    v_isbn VARCHAR(20);
    v_due_date DATE;
    v_member_id VARCHAR(10);
BEGIN
    -- Get book and issue details
    SELECT i.isbn, i.due_date, i.memberid 
    INTO v_isbn, v_due_date, v_member_id
    FROM ISSUED_BOOKS i
    WHERE i.issueid = p_issue_id
    AND i.return_date IS NULL;
    
    -- Calculate days late
    v_days_late := GREATEST(0, p_return_date - v_due_date);
    
    -- Start transaction
    SAVEPOINT before_return;
    
    BEGIN
        -- Update return date first
        UPDATE ISSUED_BOOKS
        SET return_date = p_return_date
        WHERE issueid = p_issue_id;
        
        -- Calculate and insert fine if late
        IF v_days_late > 0 THEN
            v_fine_amount := v_days_late * 10;
            v_fine_id := DBMS_RANDOM.STRING('X', 20);
            
            INSERT INTO FINES (fineid, issueid, fine_amount, paid_status)
            VALUES (v_fine_id, p_issue_id, v_fine_amount, 'unpaid');
        END IF;
        
        -- Update book status
        UPDATE BOOKS
        SET status = 'available'
        WHERE isbn = v_isbn;
        
        COMMIT;
        
        -- Display success message
        DBMS_OUTPUT.PUT_LINE('Book returned successfully.');
        IF v_days_late > 0 THEN
            DBMS_OUTPUT.PUT_LINE('Fine of Rs.' || v_fine_amount || ' has been charged for ' || v_days_late || ' days late.');
        END IF;
        
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK TO before_return;
            DBMS_OUTPUT.PUT_LINE('Error returning book: ' || SQLERRM);
            RAISE;
    END;
    
    -- Refresh data
    refresh_data;
END;
/

-- Example usage:
-- EXEC return_book('ISSUE123', TO_DATE('2024-04-15', 'YYYY-MM-DD'));

-- Create procedure to add a new member
CREATE OR REPLACE PROCEDURE add_member(
    p_member_id IN VARCHAR2,
    p_name IN VARCHAR2,
    p_phone IN VARCHAR2
) AS
    v_member_exists NUMBER;
BEGIN
    -- Check if member already exists
    SELECT COUNT(*) INTO v_member_exists
    FROM MEMBER
    WHERE memberid = p_member_id;
    
    IF v_member_exists > 0 THEN
        RAISE_APPLICATION_ERROR(-20003, 'Member ID already exists.');
    END IF;
    
    -- Check if phone number is already used
    SELECT COUNT(*) INTO v_member_exists
    FROM MEMBER
    WHERE phoneno = p_phone;
    
    IF v_member_exists > 0 THEN
        RAISE_APPLICATION_ERROR(-20004, 'Phone number already registered with another member.');
    END IF;
    
    -- Insert new member
    INSERT INTO MEMBER (memberid, name, phoneno)
    VALUES (p_member_id, p_name, p_phone);
    
    -- Display confirmation in SQL*Plus
    DBMS_OUTPUT.PUT_LINE('Member added successfully:');
    DBMS_OUTPUT.PUT_LINE('Member ID: ' || p_member_id);
    DBMS_OUTPUT.PUT_LINE('Name: ' || p_name);
    DBMS_OUTPUT.PUT_LINE('Phone: ' || p_phone);
    
    -- Refresh data
    refresh_data;
    
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
/

-- Enable DBMS_OUTPUT for SQL*Plus
BEGIN
    DBMS_OUTPUT.ENABLE;
END;
/

COMMIT;

-- Create function to display average rating of each book
CREATE OR REPLACE FUNCTION get_book_ratings
RETURN SYS_REFCURSOR AS
    v_result SYS_REFCURSOR;
BEGIN
    OPEN v_result FOR
        SELECT 
            b.isbn,
            b.title,
            b.author,
            ROUND(AVG(r.rating), 2) as average_rating,
            COUNT(r.reviewid) as total_reviews,
            LISTAGG(r.rating || '★', ', ') WITHIN GROUP (ORDER BY r.reviewdate) as all_ratings
        FROM BOOKS b
        LEFT JOIN REVIEWS r ON b.isbn = r.isbn
        GROUP BY b.isbn, b.title, b.author
        ORDER BY average_rating DESC NULLS LAST;
    
    RETURN v_result;
END;
/

-- Create procedure to display book ratings in a formatted way
CREATE OR REPLACE PROCEDURE display_book_ratings AS
    v_book_record SYS_REFCURSOR;
    v_isbn VARCHAR(20);
    v_title VARCHAR(255);
    v_author VARCHAR(255);
    v_avg_rating NUMBER;
    v_total_reviews NUMBER;
    v_all_ratings VARCHAR(4000);
BEGIN
    -- Enable DBMS_OUTPUT
    DBMS_OUTPUT.ENABLE;
    
    -- Get the cursor from the function
    v_book_record := get_book_ratings();
    
    -- Display header
    DBMS_OUTPUT.PUT_LINE('=== BOOK RATINGS ===');
    DBMS_OUTPUT.PUT_LINE('ISBN' || CHR(9) || 'Title' || CHR(9) || 'Author' || CHR(9) || 'Avg Rating' || CHR(9) || 'Total Reviews' || CHR(9) || 'All Ratings');
    DBMS_OUTPUT.PUT_LINE('--------------------------------------------------------------------------------');
    
    -- Loop through results
    LOOP
        FETCH v_book_record INTO v_isbn, v_title, v_author, v_avg_rating, v_total_reviews, v_all_ratings;
        EXIT WHEN v_book_record%NOTFOUND;
        
        -- Format and display each book's rating
        DBMS_OUTPUT.PUT_LINE(
            v_isbn || CHR(9) ||
            SUBSTR(v_title, 1, 30) || CHR(9) ||
            SUBSTR(v_author, 1, 20) || CHR(9) ||
            NVL(TO_CHAR(v_avg_rating), 'No ratings') || CHR(9) ||
            NVL(TO_CHAR(v_total_reviews), '0') || CHR(9) ||
            NVL(v_all_ratings, 'No ratings')
        );
    END LOOP;
    
    -- Close the cursor
    CLOSE v_book_record;
    
    DBMS_OUTPUT.PUT_LINE('=== END OF RATINGS ===');
END;
/

-- Example usage:
-- EXEC display_book_ratings;

-- Create function to search books based on different criteria
CREATE OR REPLACE FUNCTION search_books(
    p_search_type IN VARCHAR2,
    p_search_value IN VARCHAR2
) RETURN SYS_REFCURSOR AS
    v_result SYS_REFCURSOR;
BEGIN
    OPEN v_result FOR
        SELECT 
            b.isbn,
            b.title,
            b.author,
            b.genre,
            b.price,
            b.status,
            ROUND(AVG(r.rating), 2) as avg_rating,
            COUNT(r.reviewid) as total_reviews
        FROM BOOKS b
        LEFT JOIN REVIEWS r ON b.isbn = r.isbn
        WHERE CASE p_search_type
                WHEN 'TITLE' THEN UPPER(b.title) LIKE '%' || UPPER(p_search_value) || '%'
                WHEN 'AUTHOR' THEN UPPER(b.author) LIKE '%' || UPPER(p_search_value) || '%'
                WHEN 'GENRE' THEN UPPER(b.genre) LIKE '%' || UPPER(p_search_value) || '%'
                WHEN 'ISBN' THEN b.isbn = p_search_value
                WHEN 'PRICE_LESS' THEN b.price <= TO_NUMBER(p_search_value)
                WHEN 'PRICE_MORE' THEN b.price >= TO_NUMBER(p_search_value)
                WHEN 'STATUS' THEN UPPER(b.status) = UPPER(p_search_value)
                ELSE 1=1
              END
        GROUP BY b.isbn, b.title, b.author, b.genre, b.price, b.status
        ORDER BY b.title;
    
    RETURN v_result;
END;
/

-- Create procedure to display search menu and results
CREATE OR REPLACE PROCEDURE search_book_menu AS
    v_search_type VARCHAR2(20);
    v_search_value VARCHAR2(100);
    v_book_record SYS_REFCURSOR;
    v_isbn VARCHAR(20);
    v_title VARCHAR(255);
    v_author VARCHAR(255);
    v_genre VARCHAR(100);
    v_price NUMBER;
    v_status VARCHAR(20);
    v_avg_rating NUMBER;
    v_total_reviews NUMBER;
    v_found BOOLEAN := FALSE;
BEGIN
    -- Enable DBMS_OUTPUT
    DBMS_OUTPUT.ENABLE;
    
    -- Display search menu
    DBMS_OUTPUT.PUT_LINE('=== BOOK SEARCH MENU ===');
    DBMS_OUTPUT.PUT_LINE('1. Search by Title');
    DBMS_OUTPUT.PUT_LINE('2. Search by Author');
    DBMS_OUTPUT.PUT_LINE('3. Search by Genre');
    DBMS_OUTPUT.PUT_LINE('4. Search by ISBN');
    DBMS_OUTPUT.PUT_LINE('5. Search by Price (Less than or equal to)');
    DBMS_OUTPUT.PUT_LINE('6. Search by Price (Greater than or equal to)');
    DBMS_OUTPUT.PUT_LINE('7. Search by Status (available/issued/reserved)');
    DBMS_OUTPUT.PUT_LINE('8. Show All Books');
    DBMS_OUTPUT.PUT_LINE('9. Exit Search');
    
    -- Get search type from user
    v_search_type := '&search_type';
    
    -- Get search value based on type
    CASE v_search_type
        WHEN '1' THEN 
            v_search_type := 'TITLE';
            v_search_value := '&Enter_title_to_search';
        WHEN '2' THEN 
            v_search_type := 'AUTHOR';
            v_search_value := '&Enter_author_to_search';
        WHEN '3' THEN 
            v_search_type := 'GENRE';
            v_search_value := '&Enter_genre_to_search';
        WHEN '4' THEN 
            v_search_type := 'ISBN';
            v_search_value := '&Enter_ISBN_to_search';
        WHEN '5' THEN 
            v_search_type := 'PRICE_LESS';
            v_search_value := '&Enter_maximum_price';
        WHEN '6' THEN 
            v_search_type := 'PRICE_MORE';
            v_search_value := '&Enter_minimum_price';
        WHEN '7' THEN 
            v_search_type := 'STATUS';
            v_search_value := '&Enter_status_to_search';
        WHEN '8' THEN 
            v_search_type := 'ALL';
            v_search_value := NULL;
        WHEN '9' THEN
            RETURN;
        ELSE
            DBMS_OUTPUT.PUT_LINE('Invalid choice!');
            RETURN;
    END CASE;
    
    -- Get the cursor from the function
    v_book_record := search_books(v_search_type, v_search_value);
    
    -- Display header
    DBMS_OUTPUT.PUT_LINE(CHR(10) || '=== SEARCH RESULTS ===');
    DBMS_OUTPUT.PUT_LINE('ISBN' || CHR(9) || 'Title' || CHR(9) || 'Author' || CHR(9) || 'Genre' || 
                        CHR(9) || 'Price' || CHR(9) || 'Status' || CHR(9) || 'Avg Rating' || CHR(9) || 'Reviews');
    DBMS_OUTPUT.PUT_LINE('--------------------------------------------------------------------------------');
    
    -- Loop through results
    LOOP
        FETCH v_book_record INTO v_isbn, v_title, v_author, v_genre, v_price, v_status, v_avg_rating, v_total_reviews;
        EXIT WHEN v_book_record%NOTFOUND;
        
        v_found := TRUE;
        
        -- Format and display each book
        DBMS_OUTPUT.PUT_LINE(
            v_isbn || CHR(9) ||
            SUBSTR(v_title, 1, 20) || CHR(9) ||
            SUBSTR(v_author, 1, 15) || CHR(9) ||
            SUBSTR(v_genre, 1, 10) || CHR(9) ||
            TO_CHAR(v_price, '999.99') || CHR(9) ||
            v_status || CHR(9) ||
            NVL(TO_CHAR(v_avg_rating), 'N/A') || CHR(9) ||
            NVL(TO_CHAR(v_total_reviews), '0')
        );
    END LOOP;
    
    -- Close the cursor
    CLOSE v_book_record;
    
    IF NOT v_found THEN
        DBMS_OUTPUT.PUT_LINE('No books found matching your criteria.');
    END IF;
    
    DBMS_OUTPUT.PUT_LINE('=== END OF SEARCH RESULTS ===');
END;
/

-- Example usage:
-- EXEC search_book_menu; 