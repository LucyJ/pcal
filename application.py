import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

import time
import datetime

from helpers import apology, login_required, currentday

# my token = pk_794eb7aa754a4152a361a00516a251fb

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
#app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///pcal.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def today():
    # current day look in helpers.py in the form of the sql id
    current_day = currentday()

    # retrieves the user's id from the current session
    user_id = session["user_id"]

    average()

    # gets the data on the user
    data = db.execute("SELECT * FROM users WHERE id=:userid", userid=user_id)[0]

    # retrieves the average cycle length and the last cycle start date from the data table
    cycle_length = int(data["cycle_length"])
    last_cycle_start = str(data["last_cycle_start"])

    # gets today's symptoms if they already entered sympotoms for today
    symptoms = db.execute("SELECT stress, pain, energy, emotion, notes, bleeding_level FROM symptoms WHERE user_id = :user_id AND day_id = :currentday",
                          user_id=session["user_id"], currentday=int(currentday()))

    #next_cycle = 0

    # gets the current date as a date object using today's day_id format
    current_date = datetime.date(int(current_day[:4]), int(current_day[4:6]), int(current_day[6:]))

    # transforms the last cycle date stored in the database as a date object
    last_cycledate = datetime.date(int(last_cycle_start[:4]), int(last_cycle_start[4:6]), int(last_cycle_start[6:]))

    # finds the number of days until the next predicted cycle using the timedelta function
    next_date = last_cycledate + datetime.timedelta(days=cycle_length) - current_date

    # checks if the period is late
    if (next_date).days < 0:
        late = True
    else:
        late = False

    # sets next_cycle to the number of days calculated in the last part
    next_cycle = abs(next_date.days)

    # ovulation occurs about 14 before the next period, so the next ovulation date should be 14 before the next period date
    ovulation_next = next_cycle - 14

    # if ovulation has passed, then it should use the next period date
    while ovulation_next < 0:
        ovulation_next = ovulation_next + cycle_length

    # renders the page with all the information
    return render_template("today.html", next_cycle=next_cycle, symptoms=symptoms, ovulation=ovulation_next, late=late)


@app.route("/symptoms", methods=["GET", "POST"])
@login_required
def symptoms():
    # If request is to get the website, return the html page
    if request.method == "GET":
        return render_template("symptoms.html")
    # if user submits form, do the following
    else:
        # gets data from the form and checks that the user entered all data
        stress = request.form.get("stress")
        if not stress:
            return apology("Please enter a stress level")
        else:
            stress = int(stress)

        pain = request.form.get("pain")
        if not pain:
            return apology("Please enter a pain level")
        else:
            pain = int(pain)

        energy = request.form.get("energy")
        if not energy:
            return apology("Please enter a energy level")
        else:
            energy = int(energy)

        # thses are fine if they are null
        emotion = request.form.get("emotion")
        notes = request.form.get("notes")

        # defaults bleeding level to 'None' if nothing is entered
        bleeding_level = request.form.get("bleeding_level")
        if not bleeding_level:
            bleeding_level = 'None'

        # inputs data from the form into the SQL table
        if not db.execute("SELECT * FROM symptoms WHERE user_id = :user_id AND day_id = :currentday", user_id=session["user_id"], currentday=int(currentday())):
            db.execute("INSERT INTO symptoms(day_id, user_id, stress, pain, energy, emotion, notes, bleeding_level) VALUES(:day_id, :user_id, :stress, :pain, :energy, :emotion, :notes, :bleeding_level)",
                       day_id=int(currentday()), user_id=session["user_id"], stress=stress, pain=pain, energy=energy, emotion=emotion, notes=notes, bleeding_level=bleeding_level)
        else:
            db.execute("UPDATE symptoms SET stress=:stress, pain=:pain, energy=:energy, emotion=:emotion, notes=:notes, bleeding_level=:bleeding_level WHERE day_id=:day_id AND user_id=:user_id",
                       stress=stress, pain=pain, energy=energy, emotion=emotion, notes=notes, bleeding_level=bleeding_level, day_id=int(currentday()), user_id=session["user_id"])

        # update last cycle date for user; revert to last last date if the symptom is changed to None
        if bleeding_level != 'None' and bleeding_level != 'Spotting':
            # gets yesterday's date
            date = datetime.date.today() - datetime.timedelta(days=1)

            # gets the data in the database for yesterday's date
            yesterday = db.execute("SELECT * FROM symptoms WHERE day_id = :yesterday_id AND user_id = :user_id",
                                   yesterday_id=int(str(date).replace("-", "")), user_id=session["user_id"])

            # determines if the user had their period yesterday, indicating whether today is the first day of their period
            if not yesterday or yesterday[0]["bleeding_level"] == "None":
                # gets the current cycle length
                current_length = calculate_cycle_length()
                day = int(str(datetime.date.today()).replace("-", ""))

                # checks if a data entry is already done for this date
                if not db.execute("SELECT * FROM days WHERE user_id = :user_id AND day_id = :currentday", user_id=session["user_id"], currentday=int(currentday())):
                    db.execute("INSERT INTO days (user_id, day_id, cycle) VALUES(:user_id, :day, :cyclelen)",
                               user_id=session["user_id"], day=int(currentday()), cyclelen=current_length)
                    average()
        # the case where there is no period today
        else:
            today = db.execute("SELECT * FROM days WHERE user_id = :user_id AND day_id = :currentday",
                               user_id=session["user_id"], currentday=int(currentday()))
            # checks if there is data already for a start of period today
            if not today:
                return redirect("/")
            else:
                # removes the entry for a cycle starting today
                db.execute("DELETE FROM days WHERE user_id = :user_id AND day_id = :currentday",
                           user_id=session["user_id"], currentday=int(currentday()))

                # changes the last cycle start day to what is was before today's data was entered
                revert = db.execute("SELECT day_id FROM days WHERE user_id = :user_id ORDER BY day_id DESC LIMIT 1",
                                    user_id=session["user_id"])
                db.execute("UPDATE users SET last_cycle_start = :revert WHERE id = :user_id",
                           revert=int(revert[0]["day_id"]), user_id=session["user_id"])
                average()

        return redirect("/")


def average():
    # calculate average cycles, call cycles from days for users to calculate average
    # update cycle length for user
    cycles = db.execute("SELECT cycle FROM days WHERE user_id = :user_id", user_id=session["user_id"])
    #cycles = cycles[0]["cycle"]
    count = 0
    total = 0
    for i in cycles:
        count += 1
        total += i["cycle"]
    average = round(float(total)/count)
    last_data = db.execute("SELECT * FROM days WHERE user_id=:user_id ORDER BY day_id DESC", user_id=session["user_id"])
    last = last_data[0]["day_id"]

    db.execute("UPDATE users SET cycle_length = :average WHERE id = :user_id", average=int(average), user_id=session["user_id"])
    db.execute("UPDATE users SET last_cycle_start = :last WHERE id = :user_id", last=int(last), user_id=session["user_id"])
    return average


@app.route("/calendar", methods=["GET", "POST"])
@login_required
def calendar():
    # returns an empty form if the get method is returned
    if request.method == "GET":
        return render_template("calendar.html")
    else:
        # retrieves the entered date from the datepicker form, and checks that it is in the correct format
        date = request.form.get("date")
        date_format = '%m/%d/%Y'
        try:
            date_obj = datetime.datetime.strptime(date, date_format)
        except ValueError:
            return apology("Enter correct date format")

        # formats the date according to what is used in the sql database
        date_id = str(date[6:]) + str(date[0:2]) + str(date[3:5])

        # retrieves the symptoms, if any were entered for that day
        symptoms = db.execute("SELECT stress, pain, energy, emotion, notes, bleeding_level FROM symptoms WHERE user_id = :user_id AND day_id = :entered_day",
                              user_id=session["user_id"], entered_day=int(date_id))

        # tells user there's no input for the chosen day
        if not symptoms:
            return render_template("calendarapology.html")

        # returns the information to be displayed on the page
        return render_template("calendar.html", date=date, symptoms=symptoms)


@app.route("/recommendations")
@login_required
def recommendations():
    # gets data from the symptoms database about symptoms on the current day
    symptoms_today = db.execute("SELECT stress, pain, energy, emotion, notes, bleeding_level FROM symptoms WHERE user_id = :user_id AND day_id = :currentday",
                                user_id=session["user_id"], currentday=int(currentday()))
    # gets yesterday's date
    date = datetime.date.today() - datetime.timedelta(days=1)
    # gets the day before yesterday's date
    date2 = datetime.date.today() - datetime.timedelta(days=2)
    # gets the day before the day before yesterday's date
    date3 = datetime.date.today() - datetime.timedelta(days=3)
    # gets data on symptoms from yesterday
    symptoms_yest = db.execute("SELECT stress, pain, energy, emotion, notes, bleeding_level FROM symptoms WHERE user_id = :user_id AND day_id = :yesterday_id",
                               user_id=session["user_id"], yesterday_id=int(str(date).replace("-", "")))
    # gets data on symptoms from the day before yesterday
    symptoms_2yest = db.execute("SELECT stress, pain, energy, emotion, notes, bleeding_level FROM symptoms WHERE user_id = :user_id AND day_id = :yesterday2_id",
                                user_id=session["user_id"], yesterday2_id=int(str(date2).replace("-", "")))
    # gets data on symptoms from the day before the day before yesterday
    symptoms_3yest = db.execute("SELECT stress, pain, energy, emotion, notes, bleeding_level FROM symptoms WHERE user_id = :user_id AND day_id = :yesterday3_id",
                                user_id=session["user_id"], yesterday3_id=int(str(date3).replace("-", "")))
    # Initializes variables that will be used later
    stress_tod = 0
    pain_tod = 0
    energy_tod = 4
    bleeding_level_tod = 0
    stress_y = 0
    pain_y = 0
    energy_y = 4
    bleeding_level_y = 0
    stress_yy = 0
    pain_yy = 0
    energy_yy = 4
    bleeding_level_yy = 0
    stress_yyy = 0
    pain_yyy = 0
    energy_yyy = 4
    bleeding_level_yyy = 0
    # if symptoms were inputted today, puts symptom scores in variables for today
    if symptoms_today:
        stress_tod = symptoms_today[0]["stress"]
        pain_tod = symptoms_today[0]["pain"]
        energy_tod = symptoms_today[0]["energy"]
        bleeding_level_tod = symptoms_today[0]["bleeding_level"]
    # if symptoms were inputted yesterday, puts symptom scores in variables for yesterday
    if symptoms_yest:
        stress_y = symptoms_yest[0]["stress"]
        pain_y = symptoms_yest[0]["pain"]
        energy_y = symptoms_yest[0]["energy"]
        bleeding_level_y = symptoms_yest[0]["bleeding_level"]
    # if symptoms were inputted the day before yesterday, puts symptom scores in variables for the day before yesterday
    if symptoms_2yest:
        stress_yy = symptoms_2yest[0]["stress"]
        pain_yy = symptoms_2yest[0]["pain"]
        energy_yy = symptoms_2yest[0]["energy"]
        bleeding_level_yy = symptoms_2yest[0]["bleeding_level"]
    # if symptoms were inputted the day before yesterday, puts symptom scores in variables for the day before the day before yesterday
    if symptoms_3yest:
        stress_yyy = symptoms_3yest[0]["stress"]
        pain_yyy = symptoms_3yest[0]["pain"]
        energy_yyy = symptoms_3yest[0]["energy"]
        bleeding_level_yyy = symptoms_3yest[0]["bleeding_level"]
    # if statements for stress recommendations taken from https://www.everydayhealth.com/anxiety/why-anxiety-spikes-with-your-period.aspx
    if stress_tod == 4 or stress_tod + stress_y >= 7:
        # strong stress relieving rec
        stress = "Consider taking anti-anxiety medicine"
    elif stress_tod == 3 or stress_tod + stress_y + stress_yy + stress_yyy >= 12:
        # medium stress relieving rec
        stress = "Meditation and Deep-breathing exercises and relax with friends and family"
    elif stress_tod == 2 or stress_tod + stress_y + stress_yy + stress_yyy >= 9:
        # light stress relieving rec
        stress = "Exercise and sleep for at least 8 hours and avoid alcohol, tobacco, and caffeine"
    else:
        # non-stressful reminder
        stress = "Enjoy your day and stay unstressed!"
    # if statements for pain recommendations taken from https://www.plannedparenthood.org/learn/health-and-wellness/menstruation/what-can-i-do-about-cramps-and-pms
    if pain_tod == 4 or pain_tod + pain_y >= 7:
        # strong pain relieving rec
        pain = "Consider taking over-the-counter medicine such as Advil, Aleve, or Tylenol"
    elif pain_tod == 3 or pain_tod + pain_y + pain_yy + pain_yyy >= 12:
        # medium pain relieving rec
        pain = "Use a heating pad on your stomach or back or take a hot bath"
    elif pain_tod == 2 or pain_tod + pain_y + pain_yy + pain_yyy >= 9:
        # light pain relieving rec
        pain = "Rest or exercise lightly"
    else:
        # non-painful reminder
        pain = "Enjoy your painless day!"
    # if statements for energy-boosting recommendations taken from https://www.bustle.com/articles/176636-11-ways-to-feel-energized-happier-during-your-period
    if energy_tod == 1 or energy_tod + energy_y <= 3:
        # strong energy boosting rec
        energy = "Consider taking a melatonin supplement before sleep to be energized tomorrow and drink lots of water"
    elif energy_tod == 2 or energy_tod + energy_y + energy_yy + energy_yyy <= 7:
        # medium energy boosting rec
        energy = "Take a quick nap, drink lots of water, and eat foods high in magnesium such as bananas, nuts, and avocado"
    elif energy_tod == 3 or energy_tod + energy_y + energy_yy + energy_yyy <= 9:
        # light energy boosting rec
        energy = "Exercise a little and eat small meals throughout the day"
    else:
        # non-energy boosting reminder
        energy = "Stay upbeat and enjoy your day!"
    # recommendations for bleeding taken from https://www.everydayhealth.com/womens-health/menstruation/making-sense-menstrual-flow/
    if bleeding_level_tod == "Heavy":
        # strong bleeding relieving rec
        bleeding = "Consider taking oral contraceptives or progesterone to reduce bleeding symptoms and change high-absorbency tampon or pad at least every 3 hours"
    elif bleeding_level_tod == "Medium":
        # medium bleeding relieving rec
        bleeding = "Make sure to change a regular-absorbency tampon or pad at least every 3 hours"
    elif bleeding_level_tod == "Light":
        # light bleeding relieving rec
        bleeding = "Make sure to change low to regular-absorbency tampon or pad at least 2 to 3 times a day"
    elif bleeding_level_tod == "Spotting":
        # spotting bleeding relief rec
        bleeding = "Consider using a tampon or pad although it is not necessary"
    else:
        # insert non-bleeding reminder
        bleeding = "Enjoy your period-free day!"
    # render page displaying recommendations
    return render_template("recommendations.html", stress=stress, pain=pain, energy=energy, bleeding=bleeding)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        # retrieves the input for username on the register page
        username = request.form.get("username")

        # checks if the user input anything into username
        if not username:
            return apology("Must enter a username.")

        # checks if the username already exists in the database
        if db.execute("SELECT username FROM users WHERE username = :username", username=username):
            return apology("Username already taken")

        # retrieves the password and password confirmation from the webpage
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # checks that both the password and confirmation are filled out by the user
        if not password or not confirmation:
            return apology("Please enter both a password and confirmation of password.")

        # checks that the password and confirmation match
        if password != confirmation:
            return apology("Password and confirmation do not match.")

        # generates the password hash using the given function
        passhash = generate_password_hash(password)

        # gets the cycle length from the form and sets the default to 28
        cycle_length = request.form.get("cycle_length")
        if not cycle_length:
            cycle_length = 28

        # gets the last cycle start date and defualts to today if nothing is entered, also checks that the date entered is valid
        last_cycle_start = request.form.get("last_cycle_start")
        date_format = '%m/%d/%Y'
        try:
            date_obj = datetime.datetime.strptime(last_cycle_start, date_format)
        except ValueError:
            return apology("Enter correct date format")

        if not last_cycle_start:
            day_id = currentday()
        else:
            day_id = str(last_cycle_start[6:]) + str(last_cycle_start[0:2]) + str(last_cycle_start[3:5])

        if int(day_id) > int(currentday()):
            return apology("Last cycle start day cannot be in the future")

        # enters the user into the database
        db.execute("INSERT INTO users (username, hash, cycle_length, last_cycle_start) VALUES(:username, :passhash, :cyclelen, :lastcycle)",
                   username=username, passhash=passhash, cyclelen=int(cycle_length), lastcycle=int(day_id))

        user_id = db.execute("SELECT * FROM users WHERE username=:username", username=username)

        # enters the user's cycle data into days
        db.execute("INSERT INTO days (user_id, day_id, cycle) VALUES(:user_id, :day, :cyclelen)",
                   user_id=user_id[0]["id"], day=int(day_id), cyclelen=int(cycle_length))

        # sends the user to the index page
        return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# calculates the last cycle length for the user


def calculate_cycle_length():
    # finds the current cycle length using today as the first day of the cycle
    today = datetime.date.today()
    last_cycle = (db.execute("SELECT last_cycle_start FROM users WHERE id=:user_id",
                             user_id=session["user_id"]))[0]["last_cycle_start"]
    last_cycle_date = datetime.date(int(str(last_cycle)[:4]), int(str(last_cycle)[4:6]), int(str(last_cycle)[6:]))

    return (today - last_cycle_date).days


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

