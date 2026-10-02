# Wardial

Wardial is a small web app written in Python with Flask. It is an operation log
for a war dialing crew. War dialing was the practice of dialing many phone
numbers to find modems and computers on the other end. It spread in the early
1980s.

Crew members log in, submit what they found, browse the findings, and search
them.

This app is for Lab 4.

## A note before you start

This app has security flaws. They are there on purpose, for the lab. The code is
for learning here. It is not a pattern to reuse in other projects.

Run the app only on your own computer. Use only the accounts below. Keep real
passwords out of it.

## What you need

- Python 3
- VSCode, or another editor with a terminal
- A web browser

## Files

The project folder holds these files:

```
.gitignore
README.md
app.py
requirements.txt
static/css/style.css
templates/base.html
templates/index.html
templates/login.html
templates/profile.html
templates/search.html
templates/submit.html
```

Keep this layout. Flask looks for pages in `templates` and for the style sheet
in `static`.

## Install Flask

1. Open the project folder in VSCode.
2. Open the integrated terminal.
3. Run this command:

```
pip install -r requirements.txt
```

This installs Flask. It only needs to happen once.

## Start the app

In the same terminal, run this command:

```
python app.py
```

On macOS and Linux, the command is sometimes `python3` instead.

Open a browser and go to `http://localhost:5000`.

The terminal stays busy while the app runs. To stop the app, click in the
terminal and press Ctrl+C.

Flask restarts the app when you save a change.

## Accounts

Each account has a handle and a password. A handle is the name a crew member
went by.

- Handle `capn_static`, password `tone99`
- Handle `bluebox_88`, password `bell123`
- Handle `ringmaster`, password `pbx456`
- Handle `dial_ghost`, password `trunk77`

## Using the app

The links at the top of the page change when you log in.

Before you log in:

- **FINDINGS** lists every finding.
- **LOGIN** opens the login form.
- **SEARCH** finds findings by keyword and system type.

After you log in, three more links show:

- **SUBMIT** adds a new finding.
- **MY PROFILE** shows your own findings.
- **LOGOUT** ends your session.

Click a handle in the findings list to see that crew member's profile.

## The database

The app keeps its data in a file named `data.db`. The app makes this file the
first time it runs.

The file is made in whatever folder the terminal is in. Run the app from the
project folder. Then there is only one `data.db`.

Sometimes the data changes while you work. A reset brings back the starting
accounts and findings.

To reset:

1. Stop the app with Ctrl+C.
2. Delete `data.db`.
3. Run the app again.

## The log file

The app writes a log file named `scan.log`. Like the database, it is made in the
folder the terminal is in. It grows as you use the app.

It is a plain text file. Any text editor opens it.

To start the log fresh, delete `scan.log`. The app makes a new one the next time
it writes.

## Version control

The `.gitignore` file is part of the zip. The lab instructions in LEARN explain
the git steps.

## If something goes wrong

**The terminal says No module named flask.** Flask is not installed for the
Python that ran the app. Run this command, then start the app again:

```
python -m pip install -r requirements.txt
```

**The terminal says `python` is not recognized, or command not found.** The
terminal cannot find Python. Try `python3`. If that does not work, check that
Python is installed.

**The terminal says the address is already in use.** Another program has
port 5000. On a Mac, AirPlay Receiver often uses this port. Turn it off in
System Settings, under General, then AirDrop & Handoff.

**The browser says it cannot reach the site.** The app is not running. Look at
the terminal. Start the app again if it stopped.

**The app says Invalid credentials.** Check the handle and password against the
list above. Every handle is lowercase.

Your instructor can help if the app still will not start.
