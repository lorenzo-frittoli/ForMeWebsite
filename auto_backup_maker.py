import time

from constants import TIMED_BACKUPS_DIR, BACKUP_FREQ
from manage_helpers import make_backup


def main():
    """Automatically creates backups of the db
    """        
    while True:
        make_backup(TIMED_BACKUPS_DIR)
        time.sleep(BACKUP_FREQ)


if __name__ == "__main__":
    print("Ctrl-C to kill")
    main()
