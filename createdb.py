from decouple import config
import sqlite3


# create database if does not exist
def create_db():
    dbfile = config("DBFILE")
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS client_disk_status (
            sysid text,
            timestamp text,
            drive text,
            drivetype text,
            drivename text,
            driveserial text,
            drivefilesystem text,
            totalGB float,
            usedGB float,
            freeGB float,
            freepct float,
            usedpct float,
            key text
        )"""
    )
    conn.commit()
    conn.close()
