import os
import re
import json
from datetime import datetime

from utils.compare import compare_data

DAILY_FOLDER = os.path.join("data","daily")

DAILY_HISTORY_FILE = os.path.join("data","history_daily.json")

os.makedirs(DAILY_FOLDER,exist_ok=True)
os.makedirs("data",exist_ok=True)

if not os.path.exists(DAILY_HISTORY_FILE):
    with open(DAILY_HISTORY_FILE,"w",encoding="utf-8") as f:
        json.dump([],f,indent=4)

def get_file_date(filename):
    pattern = r"^(\d{4}-\d{2}-\d{2})\.xlsx$"
    match = re.match(pattern,filename)

    if not match:
        return None

    try:
        return datetime.strptime(
            match.group(1),
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return None

def get_daily_files():
    files = []
    for filename in os.listdir(DAILY_FOLDER):
        file_date = get_file_date(filename)

        if file_date is not None:
            files.append({
                "filename": filename,
                "date": file_date,
                "path": os.path.join(DAILY_FOLDER, filename)
            })

    files.sort(key=lambda x: x["date"])
    return files

def run_daily_compare():
    files = get_daily_files()

    if len(files) < 7:
        return {
            "status": "ERROR",
            "message": (
                f"Simulasi membutuhkan 7 file. "
                f"Saat ini hanya tersedia {len(files)} file."
            ),
            "total_files": len(files),
            "total_compares": 0,
            "baseline": None,
            "results": []
        }

    simulation_files = files[-7:]
    baseline = simulation_files[0]
    results = []

    for i in range(1,len(simulation_files)):
        previous_file = simulation_files[i - 1]
        current_file = simulation_files[i]

        try:
            compare_result = compare_data(
                previous_file["path"],
                current_file["path"]
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "message": (
                    f"Gagal compare "
                    f"{previous_file['filename']} "
                    f"dengan "
                    f"{current_file['filename']}: "
                    f"{str(e)}"
                ),
                "total_files": 7,
                "total_compares": len(results),
                "baseline": baseline["filename"],
                "results": results
            }

        added = compare_result.get("added",[])
        removed = compare_result.get("removed",[])
        changed = compare_result.get("changed",[])
        expiring = compare_result.get("expiring",[])

        total_changes = (
            len(added)
            + len(removed)
            + len(changed)
        )

        results.append({
            "day": i + 1,
            "previous_file":previous_file["filename"],
            "today_file":current_file["filename"],
            "columns":compare_result.get("columns",[]),
            "added":added,
            "removed":removed,
            "changed":changed,
            "expiring":expiring,
            "total":total_changes
        })

    simulation_result = {
        "status": "SUCCESS",
        "message": "Simulasi 1 minggu berhasil.",
        "date":
            datetime.now().strftime(
                "%d-%m-%Y %H:%M:%S"
            ),
        "start_file":
            simulation_files[0]["filename"],
        "end_file":
            simulation_files[-1]["filename"],
        "baseline":
            baseline["filename"],
        "total_files":7,
        "total_compares":6,

        "results":
            results
    }

    history_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        with open(
            DAILY_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)
    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):
        history = []

    history.append({
        "id":history_id,
        "date":simulation_result["date"],
        "type":"weekly_simulation",
        "start_file":simulation_result["start_file"],
        "end_file":simulation_result["end_file"],
        "baseline":simulation_result["baseline"],
        "total_files":7,
        "total_compares":6,
        "result":
            simulation_result
    })

    with open(
        DAILY_HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    return simulation_result