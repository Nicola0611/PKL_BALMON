import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"
RESULT_FOLDER = "results"


def save_history(file1, file2, results):
    os.makedirs(RESULT_FOLDER, exist_ok=True)

    history = []

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except:
                history = []

    new_id = len(history)

    result_path = f"{RESULT_FOLDER}/result_{new_id}.json"

    with open(result_path, "w") as f:json.dump(results, f, indent=4)

    history_entry = {
        "id": new_id,
        "file1": file1,
        "file2": file2,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result_file": result_path
    }

    history.append(history_entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def get_history_detail(id):
    history = load_history()

    for item in history:
        if item["id"] == id:
            with open(item["result_file"]) as f:
                return json.load(f)

    return None