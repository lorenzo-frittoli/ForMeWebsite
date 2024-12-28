from flask import redirect, render_template, session, g, url_for, send_file, Response, abort
from functools import wraps
import qrcode
from io import BytesIO
import json
from sqlite3 import Connection

from constants import *


def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", message=message), code


def update_session():
    # Query db for id and hash from email
    cur = g.con.cursor()
    query_result = cur.execute("SELECT type, name, surname, email, can_book FROM users WHERE id = ?;", (session["user_id"], )).fetchone()
    # If the user has been deleted (this functionality is not implemented, this should not happen)
    if not query_result:
        session.clear()
        abort(403)

    # Closing cursor
    cur.close()

    # Update all user info (in case something has been changend in the mean time)
    session["user_type"], session["user_name"], session["user_surname"], session["user_email"] , session["can_book"] = query_result


def login_required(f):
    """
    Decorate routes to require login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")

        cur = g.con.cursor()
        id = cur.execute("SELECT id FROM users WHERE id = ?;", (session["user_id"], )).fetchone()
        cur.close()

        if not id:
            session.clear()
            return redirect("/login")

        update_session()

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorate to require admin login. Requires login with `@login_required`.

    Args:
        f (_type_): function to decorate

    Returns:
        _type_: decorated function
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get("user_email") not in ADMIN_EMAILS:
            return apology("Auth failed", 403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def activity_already_booked(user_id: int, activity_id: int, con: Connection) -> bool:
    """Checks wether a course has been booked already by that student.

    Args:
        user_di (int): id of the user
        activity_id (int): id of the activity

    Returns:
        bool: True if already booked, False if not
    """
    
    cur = con.cursor()
    cur.execute("SELECT activity_id FROM registrations WHERE user_id = ? AND activity_id = ?;", (user_id, activity_id))
    
    return bool(cur.fetchall())


def slot_already_booked(user_id: int, day: int, module_start: int, module_end: int, con: Connection) -> bool:
    """Checks if a slot (a day/timespan couple) is already occupied by the user

    Args:
        user_id (int): id of the user
        day (str): day
        timespan (str): timespan (will be decomposed using decompose_timespan)

    Returns:
        bool: True if booked, False if not
    """
    cur = con.cursor()
    # Searches for ranges intersecting (module_start, module_end)
    cur.execute(f"SELECT activity_id FROM registrations WHERE user_id = ? AND day = ? AND module_end >= ? AND module_start <= ?;", (user_id, day, module_start, module_end))
    
    return bool(cur.fetchall())


def make_registration(user_id: int, activity_id: int, day: int, module: int, user_type: str, con: Connection, do_commit: bool=True):
    """Add a registration to the database

    Args:
        user_id (int): id of the user
        activity_id (int): id of the activity
        day (int): day
        module (int): if length = 2, module 0 = timespans 0, 1. Compute with: timespan // lenght
        user_type (str)
        con (sqlite3.Connection)
        do_commit (bool): if the transaction should be immediatly committed. Defaults to True

    Raises:
        ValueError: Activity already booked by the user
        ValueError: Module out of bounds
        ValueError: Occupied slot
        ValueError: Activity not available
    """
    if day < 0 or day >= len(DAYS) or user_type not in PERMISSIONS[day]:
        raise ValueError("Invalid day")
    
    cur = con.cursor()

    length = cur.execute("SELECT length FROM activities WHERE id = ?;", (activity_id,)).fetchone()
    if length is None:
        raise ValueError("Invalid activity id")
    
    length = length[0]
    
    # Check if the user has already booked this activity
    if activity_already_booked(user_id, activity_id, con):
        raise ValueError("Activity already booked")

    # Check if the module is valid
    module_start = module * length
    module_end = module_start + length - 1

    if module_start < 0 or module_end >= len(TIMESPANS):
        raise ValueError("Module out of bounds")

    # Check if the user has already booked this day-timespan combo
    if slot_already_booked(user_id, day, module_start, module_end, con):
        raise ValueError("Occupied slot")
    
    # Update availability (raises ValueError if the availability is already 0)
    update_availability(activity_id, day, module, -1, con, do_commit)
    
    # Update registrations
    cur.execute("INSERT INTO registrations (user_id, activity_id, day, module_start, module_end) VALUES (?, ?, ?, ?, ?);", (user_id, activity_id, day, module_start, module_end))
    if do_commit:
        con.commit()
    
    # Close cursor
    cur.close()


def update_availability(activity_id: int, day: int, module: int, amount: int, con: Connection, do_commit: bool=True) -> None:
    """Updates the availability

    Args:
        activity_id (int): id of the activity
        day (int): day to update
        module (int): if length = 2, module 0 = timespans 0, 1. Compute with: timespan // lenght
        amount (int): amount to change the availability by
        con (sqlite3.Connection)
        do_commit (bool): if the transaction should be immediatly committed. Defaults to True
    
    Raises:
        ValueError if the availability is already 0.
    """
    # SQL setup
    cur = con.cursor()
    
    # Load availability
    availability = cur.execute("SELECT availability FROM activities WHERE id = ?", (activity_id,)).fetchone()[0]
    availability = json.loads(availability)
    
    # Modify availability
    availability[day][module] += amount
    if availability[day][module] < 0:
        raise ValueError()
    availability = json.dumps(availability)
    
    # Update availability
    cur.execute("UPDATE activities SET availability = ? WHERE id = ?;", (availability, activity_id))
    if do_commit:
        con.commit()
    
    # SQL close
    cur.close()
    cur.close()


def get_image_path(image: str) -> str:
    """Gets the path of an image from the name

    Args:
        image (str): name of the image

    Returns:
        str: path of the image.
    """
    return f"{ACTIVITY_IMAGES_DIRECTORY}/{image}"


def fmt_activity_booking(activity_id: int, con: Connection) -> str:
    cur = con.cursor()

    cur.execute("SELECT day, module_start, module_end FROM registrations WHERE user_id = ? AND activity_id = ?", (session["user_id"], activity_id))
    span = cur.fetchone()
    cur.close()

    if span is None:
        return ""
    else:
        return TIMESPANS[span[1]][0] + "-" + TIMESPANS[span[2]][1] + " del " + DAYS[span[0]]


def qr_code_for(url: str) -> Response:
    """
    Args:
        url (str): link to create a qr code for.
    Returns:
        BytesIO: an object to be passed to send_file().
    """
    img_io = BytesIO()
    qrcode.make(url).save(img_io, "PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")


def generate_schedule(user_id: int, user_type: str, con: Connection):
    """Generate the schedule for the me page."""
    cur = con.cursor()
    
    # Fetch all user registrations -> list[tuple[..]]
    result = """
    SELECT activities.id, activities.title, registrations.day, registrations.module_start, registrations.module_end
        FROM registrations JOIN
        activities ON
            registrations.activity_id = activities.id
        WHERE user_id = ?;
    """
    cur.execute(result, (user_id, ))

    user_registrations = cur.fetchall()

    # Make empty schedule
    schedule = {day: {timespan: ("", None) for timespan in TIMESPANS_TEXT}
                for i, day in enumerate(DAYS) if user_type in PERMISSIONS[i]}
    
    # Fill with known data
    for activity_id, title, day, module_start, module_end in user_registrations:
        for timespan in range(module_start, module_end + 1):
            assert DAYS[day] in schedule
            assert schedule[DAYS[day]][TIMESPANS_TEXT[timespan]] == ("", None)
            link = url_for(".activity_page", id=activity_id)
            schedule[DAYS[day]][TIMESPANS_TEXT[timespan]] = (title, link)

    return schedule
