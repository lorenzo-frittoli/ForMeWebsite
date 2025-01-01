import os

# Hosting
LINK = "https://formecassini.eu.pythonanywhere.com"


# Event details
DAYS = ("09/10", "10/10", "11/10")
TIMESPANS = (("08:00", "09:00"), ("09:00", "10:00"), ("10:00", "11:00"), ("11:00", "12:00"))
TIMESPANS_TEXT = tuple("-".join(timespan) for timespan in TIMESPANS)
PERMISSIONS = (("student", ), ("student", "guest"), ("guest", ))

assert len(set(DAYS)) == len(DAYS)
assert len(PERMISSIONS) == len(DAYS)


# Database
DATABASE = "database.db"
MAKE_DATABASE_COMMAND_FILE = "make_database.sql"


# Accounts
MAX_FIELD_LENGTH = 50
VERIFICATION_CODE_LENGTH = 20
ALLOWED_CLASSES = ("345", "ABCDEIFGHIL") # Classes are strings like '3A', '4F'


# Backups
BACKUP_FREQ = 24*60*60 # Each day
MAX_BACKUPS = 100

DIR_SEP = "\\" if os.name == "nt" else "/"

BACKUPS_DIR = "backups"
MANUAL_BACKUPS_DIR = BACKUPS_DIR + DIR_SEP + "manual"
TIMED_BACKUPS_DIR = BACKUPS_DIR + DIR_SEP + "timed"
AUTO_BACKUPS_DIR = BACKUPS_DIR + DIR_SEP + "auto"


# Admins (list of emails)
ADMIN_EMAILS = [
    "j@j.j"
]

# The admin password is "abcd"
ADMIN_PASSWORD = "pbkdf2:sha256:600000$XMc76EeQ2aZvB1gB$b56d9e43481a1baf0f18ff04cca361cb9755b69a27d2dee12e5e002315fddf13"

# Activity images
ACTIVITY_IMAGES_DIRECTORY = "static/activity_images"


# Autogenerated passwords
GENERATED_PASSWORD_LENGTH = 8
GENERATE_PASSWORD_METHOD = "pbkdf2:sha256:100000"


# Util
EMAIL_REGEX = r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
