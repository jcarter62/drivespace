from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
# import win32api, win32file, win32con
from datetime import datetime
from decouple import config
import sqlite3
from createdb import create_db
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

app = FastAPI()

# create DB if does not exist
create_db()


# clients will report their disk status to this endpoint
@app.post("/client-disk-status/")
async def client_disk_status(systeminfo: dict):
    systeminfo["sysid"] = systeminfo["name"] + "-" + systeminfo["domain"]
    systeminfo["timestamp"] = datetime.now().isoformat()
    systeminfo["key"] = systeminfo["sysid"] + "-" + systeminfo["timestamp"]
    save_fixed_drives_to_db(systeminfo)
    return {"message": "ok"}, 200


def enumerate_fixed_drives(sysinfo: dict) -> list:
    drives = []
    for drive in sysinfo["drives"]:
        if drive["drivetype"] == "Fixed":
            drives.append(drive)
    return drives

def save_fixed_drives_to_db(sysinfo: dict):
    dbfile = config("DBFILE")
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    for drive in sysinfo["drives"]:
        # remove \ from drive
        drive["drive"] = drive["drive"].replace("\\", "")
        drivekey = sysinfo["sysid"] + "-" + drive["drive"]
        # delete any existing records for this drivekey
        c.execute(
            """DELETE FROM client_disk_status WHERE key = :key""",
            {"key": drivekey}
        )

        c.execute(
            """INSERT INTO client_disk_status (
                sysid,
                timestamp,
                drive,
                drivetype,
                drivename,
                driveserial,
                drivefilesystem,
                totalGB,
                usedGB,
                freeGB,
                freepct,
                usedpct,
                key
            ) VALUES (
                :sysid,
                :timestamp,
                :drive,
                :drivetype,
                :drivename,
                :driveserial,
                :drivefilesystem,
                :totalGB,
                :usedGB,
                :freeGB,
                :freepct,
                :usedpct,
                :key
            )""",
            {
                "sysid": sysinfo["sysid"],
                "timestamp": sysinfo["timestamp"],
                "drive": drive["drive"],
                "drivetype": drive["type"],
                "drivename": drive["name"],
                "driveserial": drive["serial"],
                "drivefilesystem": drive["format"],
                "totalGB": round(drive["total"],2),
                "usedGB": round(drive["used"],2),
                "freeGB": round(drive["free"],2),
                "freepct": round(drive["freepct"],2),
                "usedpct": round(drive["usedpct"],2),
                "key": drivekey
            }
        )
    conn.commit()
    conn.close()


# display all records in the database to the browser
@app.get("/db/", response_class=HTMLResponse)
async def db(request: Request):
    dbfile = config("DBFILE")
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    c.execute(
        """SELECT * FROM client_disk_status order by sysid, drive"""
    )
    rows = c.fetchall()
    conn.close()

    # Add a column to display problems when free space is less than MINFREE
    minfree = float(config("MINFREE"))
    minpct = float(config("MINPCT"))
    sysname = ""
    systems = []
    for r in rows:
        one = {}
        if r[0] != sysname:
            sysname = r[0]
            one["sysname"] = sysname
        else:
            one["sysname"] = ""

        one["timestamp"] = r[1]
        one["drive"] = r[2]
        one["totalGB"] = r[7]
        one["usedGB"] = r[8]
        one["freeGB"] = r[9]
        one["freepct"] = r[10]

        one["msg"] = ""

        if r[9] < minfree:
            one["msg"] += "<MinFree"

        if r[10] < minpct:
            one["msg"] += "<MinPct"

        systems.append(one)


    return templates.TemplateResponse(
        "index.html",
        {"request": request, "systems": systems})

