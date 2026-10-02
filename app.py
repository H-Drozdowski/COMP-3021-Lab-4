import sqlite3
import os
from datetime import datetime
from abc import ABC, abstractmethod
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'wardial-secret-1983'

DB_PATH  = 'data.db'
LOG_PATH = 'scan.log'


# -- Database initialisation -------------------------------------------------

def initialise_database():
    """
    Create the database tables and seed data if they do not already exist.

    Connects to the SQLite database file, checks whether the findings table
    exists, and returns immediately if it does. Otherwise creates all three
    tables and inserts the default seed records for operators and findings.

    This function is called once at startup when running the app directly.
    Students receive a pre-built data.db file and this function will return
    early without making any changes.
    """
    conn = sqlite3.connect(DB_PATH)
    if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='findings'").fetchone():
        conn.close()
        return
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE operators (
            id INTEGER PRIMARY KEY,
            handle TEXT NOT NULL,
            password TEXT NOT NULL,
            region TEXT,
            joined INTEGER
        );
        CREATE TABLE findings (
            id INTEGER PRIMARY KEY,
            phone_number TEXT,
            system_type TEXT,
            notes TEXT,
            submitted_by TEXT,
            scan_year INTEGER
        );
        CREATE TABLE scan_log (
            id INTEGER PRIMARY KEY,
            event TEXT,
            detail TEXT,
            timestamp TEXT
        );
        INSERT INTO operators VALUES (1,'capn_static','tone99','midwest',1983);
        INSERT INTO operators VALUES (2,'bluebox_88','bell123','west_coast',1982);
        INSERT INTO operators VALUES (3,'ringmaster','pbx456','east_coast',1981);
        INSERT INTO operators VALUES (4,'dial_ghost','trunk77','south',1984);
        INSERT INTO findings VALUES (1,'555-3841','unix_host','Login banner: SunOS 3.2. No password prompt.','capn_static',1983);
        INSERT INTO findings VALUES (2,'555-9274','pbx','Rolm CBX. Default maintenance extension active.','bluebox_88',1982);
        INSERT INTO findings VALUES (3,'555-1100','voicemail','Octel system. Default admin PIN not changed.','ringmaster',1981);
        INSERT INTO findings VALUES (4,'555-4422','modem_bank','USRobotics rack. Answers on first ring.','dial_ghost',1984);
        INSERT INTO findings VALUES (5,'555-7731','unix_host','VAX/VMS. Guest account enabled.','capn_static',1983);
        INSERT INTO findings VALUES (6,'555-8823','unknown','Carrier detected. No response to commands.','bluebox_88',1982);
        INSERT INTO findings VALUES (7,'555-2266','pbx','NEC system. Transfer to outside line possible.','ringmaster',1983);
        INSERT INTO findings VALUES (8,'555-6610','modem_bank','Dialup pool for local university.','dial_ghost',1984);
    """)
    conn.commit()
    conn.close()


# -- Singleton DB connection -------------------------------------------------

class DatabaseConnection:
    """
    Manages a single shared connection to the SQLite database.

    Uses the Singleton pattern so only one connection is created for the
    lifetime of the application.
    """
    _instance = None

    def __new__(cls):
        """
        Return the existing instance if one exists, otherwise create a new one
        and open the database connection.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cls._instance._conn.row_factory = sqlite3.Row
        return cls._instance

    def execute(self, query, params=()):
        """
        Run an INSERT, UPDATE, or DELETE query and commit the change.

        Parameters:
            query  -- the SQL query string, using ? placeholders for values
            params -- a tuple of values to substitute into the query
        """
        cursor = self._conn.cursor()
        cursor.execute(query, params)
        self._conn.commit()

    def fetchall(self, query, params=()):
        """
        Run a SELECT query and return all matching rows.

        Returns a list of Row objects that can be accessed like dicts.

        Parameters:
            query  -- the SQL query string, using ? placeholders for values
            params -- a tuple of values to substitute into the query
        """
        cursor = self._conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetchone(self, query, params=()):
        """
        Run a SELECT query and return the first matching row.

        Returns a Row object, or None if no rows match.

        Parameters:
            query  -- the SQL query string, using ? placeholders for values
            params -- a tuple of values to substitute into the query
        """
        cursor = self._conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()


# -- Abstract repository -----------------------------------------------------

class Repository(ABC):
    """
    Base class for all repository classes.

    Provides a shared database connection and defines the interface that all
    repositories must implement.
    """
    def __init__(self, db):
        """
        Store the database connection for use by subclass methods.

        Parameters:
            db -- a DatabaseConnection instance
        """
        self._db = db

    @abstractmethod
    def find_by_id(self, record_id):
        """Look up and return a single record by its primary key."""
        pass

    @abstractmethod
    def search(self, term):
        """Search records by a given term and return matching results."""
        pass


# -- OperatorRepository ------------------------------------------------------

class OperatorRepository(Repository):
    """Handles all database operations for the operators table."""

    def login(self, handle, password):
        """
        Look up an operator by handle and password and return the matching row.

        Returns the operator row as a Row object if credentials match,
        or None if no match is found or a database error occurs.

        Parameters:
            handle   -- the submitted handle string
            password -- the submitted plain text password string
        """
        query = ("SELECT * FROM operators WHERE handle = '"
                 + handle + "' AND password = '" + password + "'")
        try:
            return self._db.fetchone(query, ())
        except Exception:
            return None

    def find_by_id(self, record_id):
        """
        Return the operator with the given ID, or None if not found.

        Parameters:
            record_id -- the integer primary key of the operator
        """
        return self._db.fetchone("SELECT * FROM operators WHERE id = ?", (record_id,))

    def find_by_handle(self, handle):
        """
        Return the operator with the given handle, or None if not found.

        Parameters:
            handle -- the handle string to look up
        """
        query = f"SELECT * FROM operators WHERE handle = '{handle}'"
        return self._db.fetchone(query, ())

    def search(self, term):
        """
        Return all operators whose handle contains the given term.

        Parameters:
            term -- the search string to match against operator handles
        """
        return self._db.fetchall(
            "SELECT * FROM operators WHERE handle LIKE ?", ("%" + term + "%",)
        )


# -- FindingRepository -------------------------------------------------------

class FindingRepository(Repository):
    """Handles all database operations for the findings table."""

    def find_by_id(self, record_id):
        """
        Return the finding with the given ID, or None if not found.

        Parameters:
            record_id -- the integer primary key of the finding
        """
        return self._db.fetchone("SELECT * FROM findings WHERE id = ?", (record_id,))

    def get_all(self):
        """Return all findings ordered by most recent first."""
        return self._db.fetchall(
            "SELECT * FROM findings ORDER BY id DESC", ()
        )

    def find_by_operator(self, handle):
        """
        Return all findings submitted by the operator with the given handle.

        Results are ordered by most recent first.

        Parameters:
            handle -- the handle string of the submitting operator
        """
        return self._db.fetchall(
            "SELECT * FROM findings WHERE submitted_by = ? ORDER BY id DESC", (handle,)
        )

    def search(self, keyword, system_type):
        """
        Search findings by keyword and optional system type filter.

        Returns a tuple of (results, error). On success, results is a list of
        matching finding rows and error is None. On failure, results is None
        and error contains the database error message.

        Parameters:
            keyword     -- a string to search for within finding notes
            system_type -- a system type string to filter by, or empty string for no filter
        """
        error = None
        results = None
        try:
            if system_type:
                results = self._db.fetchall(
                    "SELECT * FROM findings WHERE notes LIKE ? AND system_type = ?",
                    ("%" + keyword + "%", system_type)
                )
            else:
                results = self._db.fetchall(
                    "SELECT * FROM findings WHERE notes LIKE ?",
                    ("%" + keyword + "%",)
                )
        except Exception as e:
            error = str(e)
        return results, error

    def get_related_by_system(self, system_type):
        """
        Return findings related to a given system type.

        Reads the most recently stored entry for that system type, then
        searches for other findings with the same system type using a second
        query. Returns an empty list if no matching findings exist or if the
        second query fails.

        Parameters:
            system_type -- the system type string to look up and search by
        """
        row = self._db.fetchone(
            "SELECT system_type FROM findings WHERE system_type = ? ORDER BY id DESC LIMIT 1",
            (system_type,)
        )
        if not row:
            return []
        stored_type = row['system_type']
        query = f"SELECT * FROM findings WHERE system_type = '{stored_type}'"
        try:
            return self._db.fetchall(query, ())
        except Exception:
            return []

    def get_latest_note(self, handle):
        """
        Return the notes text from the most recent finding submitted by the given operator.

        Returns None if the operator has no findings.

        Parameters:
            handle -- the handle string of the operator
        """
        row = self._db.fetchone(
            "SELECT notes FROM findings WHERE submitted_by = ? ORDER BY id DESC LIMIT 1",
            (handle,)
        )
        return row['notes'] if row else None

    def insert(self, phone_number, system_type, notes, submitted_by, scan_year):
        """
        Insert a new finding record into the database.

        Parameters:
            phone_number -- the phone number string that was dialled
            system_type  -- the category of system found (e.g. unix_host, pbx)
            notes        -- plain text description of the finding
            submitted_by -- the handle of the operator submitting the finding
            scan_year    -- the year the scan was conducted
        """
        self._db.execute(
            "INSERT INTO findings (phone_number, system_type, notes, submitted_by, scan_year) VALUES (?,?,?,?,?)",
            (phone_number, system_type, notes, submitted_by, scan_year)
        )


# -- ScanLogger --------------------------------------------------------------

class ScanLogger:
    """
    Writes operational events to the scan log file.

    Each method appends a single line to scan.log with a timestamp and
    relevant event details.
    """

    def log_submission(self, handle, phone_number, notes):
        """
        Write a finding submission event to the log.

        Parameters:
            handle       -- the handle of the operator submitting the finding
            phone_number -- the phone number submitted
            notes        -- the notes text submitted with the finding
        """
        with open(LOG_PATH, 'a') as log_file:
            log_file.write(f"[{datetime.now()}] SUBMISSION | operator={handle} | phone={phone_number} | notes={notes}\n")

    def log_failed_login(self, handle, password):
        """
        Write a failed login attempt to the log.

        Parameters:
            handle   -- the handle that was submitted
            password -- the password that was submitted
        """
        with open(LOG_PATH, 'a') as log_file:
            log_file.write(f"[{datetime.now()}] LOGIN_FAIL | handle={handle} | attempted_password={password}\n")

    def log_search(self, keyword):
        """
        Write a search event to the log.

        Parameters:
            keyword -- the search keyword that was submitted
        """
        with open(LOG_PATH, 'a') as log_file:
            log_file.write(f"[{datetime.now()}] SEARCH | keyword={keyword}\n")


# -- App setup ---------------------------------------------------------------

database      = DatabaseConnection()
operator_repo = OperatorRepository(database)
finding_repo  = FindingRepository(database)
scan_logger   = ScanLogger()


# -- Routes ------------------------------------------------------------------

@app.route('/')
def index():
    """
    Render the home page.

    Passes all findings ordered by most recent first to the template.
    """
    all_findings = finding_repo.get_all()
    return render_template('index.html', findings=all_findings)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle the login page.

    GET  -- render the login form.
    POST -- attempt to authenticate with the submitted handle and password.
            On success, store the handle and operator ID in the session and
            redirect to the home page. On failure, log the attempt and flash
            an error message.
    """
    if request.method == 'POST':
        handle   = request.form.get('handle', '')
        password = request.form.get('password', '')
        operator = operator_repo.login(handle, password)
        if operator:
            session['handle']      = operator['handle']
            session['operator_id'] = operator['id']
        else:
            scan_logger.log_failed_login(handle, password)
            flash('Invalid credentials.', 'error')
    return redirect(url_for('index')) if session.get('handle') else render_template('login.html')


@app.route('/logout')
def logout():
    """Clear the session and redirect to the home page."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    """
    Handle the finding submission form.

    Redirects to login if the user is not logged in.

    GET  -- render the submission form.
    POST -- insert the submitted finding, log the submission, flash a
            confirmation, and redirect to the home page.
    """
    if not session.get('handle'):
        flash('You must be logged in to submit findings.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        phone_number = request.form.get('phone_number', '')
        system_type  = request.form.get('system_type', '')
        notes        = request.form.get('notes', '')
        scan_year    = request.form.get('scan_year', '')
        finding_repo.insert(phone_number, system_type, notes, session['handle'], scan_year)
        scan_logger.log_submission(session['handle'], phone_number, notes)
        flash('Finding submitted.', '')
        return redirect(url_for('index'))
    return render_template('submit.html')


@app.route('/search')
def search():
    """
    Render the findings search page.

    Accepts optional query parameters:
        keyword     -- a string to search finding notes
        system_type -- a system type to filter results

    If either parameter is provided, runs the search and passes results
    and any database error to the template. When a system type is given,
    also loads related findings for that system type.
    """
    keyword     = request.args.get('keyword', '')
    system_type = request.args.get('system_type', '')
    results     = None
    related     = None
    db_error    = None
    if keyword or system_type:
        scan_logger.log_search(keyword)
        results, db_error = finding_repo.search(keyword, system_type)
        if system_type:
            related = finding_repo.get_related_by_system(system_type)
    return render_template('search.html',
                           results=results,
                           db_error=db_error,
                           related=related,
                           keyword=keyword,
                           system_type=system_type)


@app.route('/profile/<handle>')
def profile(handle):
    """
    Render the profile page for an operator.

    Looks up the operator by handle and fetches their submitted findings.
    Passes both to the template along with the handle string.

    Parameters:
        handle -- the operator handle from the URL
    """
    operator          = operator_repo.find_by_handle(handle)
    operator_findings = finding_repo.find_by_operator(handle)
    return render_template('profile.html',
                           handle=handle,
                           operator=operator,
                           findings=operator_findings)


if __name__ == '__main__':
    initialise_database()
    app.run(debug=True, port=5000)