from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import pandas as pd
from utils.daily_compare import run_daily_compare
from utils.compare import compare_data
from utils.config import Config

app = Flask(__name__)

app.secret_key = "secretkey123"

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
HISTORY_FOLDER = Config.HISTORY_FOLDER

DAILY_FOLDER = os.path.join("data", "daily")
DAILY_RESULTS_FOLDER = os.path.join("data", "daily_results")

HISTORY_FILE = "history.json"
DAILY_HISTORY_FILE = os.path.join(
    "data",
    "history_daily.json"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HISTORY_FOLDER, exist_ok=True)
os.makedirs(DAILY_FOLDER, exist_ok=True)
os.makedirs(DAILY_RESULTS_FOLDER, exist_ok=True)
os.makedirs("data", exist_ok=True)

def init_json(path):
    if not os.path.exists(path):
        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump([], f, indent=4)

init_json(HISTORY_FILE)
init_json(DAILY_HISTORY_FILE)

def safe_result(result):
    if not isinstance(result, dict):
        result = {}

    columns = result.get("columns",[])
    added = result.get("added",[])
    removed = result.get("removed",[])
    changed = result.get("changed",[])
    expiring = result.get("expiring",[])

    return {
        "status": result.get(
            "status",
            "SUCCESS"
        ),
        "message": result.get(
            "message",
            ""
        ),
        "date": result.get(
            "date",
            ""
        ),
        "previous_file": result.get(
            "previous_file"
        ),
        "today_file": result.get(
            "today_file"
        ),
        "columns": columns,
        "added": added,
        "removed": removed,
        "changed": changed,
        "expiring": expiring,
        "total": (
            len(added)
            + len(removed)
            + len(changed)
        )
    }

def allowed_file(filename):
    return (
        "."
        in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in Config.ALLOWED_EXTENSIONS
    )

@app.route("/")
def home():
    return render_template("compare.html")

@app.route("/compare")
def compare():
    result = safe_result({})

    return render_template("compare.html",**result)

@app.route("/upload_compare",methods=["POST"])
def upload_compare():

    file1 = request.files.get("file1")
    file2 = request.files.get("file2")

    if not file1 or not file2:
        flash("Harap upload kedua file!")
        return redirect(url_for("compare"))

    if (
        not allowed_file(
            file1.filename
        )
        or
        not allowed_file(
            file2.filename
        )
    ):
        flash("Format file harus CSV/XLSX!")
        return redirect(url_for("compare"))
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename1 = secure_filename(
            f"{timestamp}_old_{file1.filename}"
        )
        filename2 = secure_filename(
            f"{timestamp}_new_{file2.filename}"
        )
        path1 = os.path.join(
            UPLOAD_FOLDER,
            filename1
        )
        path2 = os.path.join(
            UPLOAD_FOLDER,
            filename2
        )
        file1.save(path1)
        file2.save(path2)

        result = compare_data(path1,path2)
        result = safe_result(result)

        result_filename = (
            f"{timestamp}_result.json"
        )

        result_path = os.path.join(
            HISTORY_FOLDER,
            result_filename
        )

        with open(
            result_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                result,
                f,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)

        history.append({
            "id":
                timestamp,
            "date":
                datetime.now().strftime(
                    "%d-%m-%Y %H:%M"
                ),
            "file1":
                filename1,
            "file2":
                filename2,
            "result_file":
                result_filename
        })

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                history,
                f,
                indent=4,
                ensure_ascii=False
            )
        return render_template(
            "compare.html",
            **result
        )
    except Exception as e:
        flash(
            f"Error: {str(e)}"
        )
        return redirect(url_for("compare"))

@app.route("/daily_compare")
def daily_compare():

    try:
        print("RUN WEEKLY SIMULATION...")
        result = run_daily_compare()

        if result.get("status") == "ERROR":
            flash(
                result.get(
                    "message",
                    "Simulasi gagal."
                )
            )

        return render_template("daily_compare.html", data=result)

    except Exception as e:
        print("SIMULATION ERROR:",e)

        flash(f"Simulation error: {str(e)}")
        return redirect(url_for("home"))

@app.route("/history")
def history():
    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)

        return render_template(
            "history.html",
            history=list(
                reversed(history)
            )
        )

    except Exception as e:
        flash(
            f"Gagal membaca history: {str(e)}"
        )
        return render_template(
            "history.html",
            history=[]
        )

@app.route("/history_daily")
def history_daily():
    try:
        with open(
            DAILY_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)
        return render_template(
            "history_daily.html",
            history=list(
                reversed(history)
            )
        )

    except Exception as e:
        flash(
            f"Gagal membaca history daily: {str(e)}"
        )
        return render_template(
            "history_daily.html",
            history=[]
        )

@app.route("/history/<id>")

@app.route("/download_history/<id>")
def download_history(id):
    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)

        selected = next(
            (
                h for h in history
                if str(h.get("id")) == str(id)
            ),
            None
        )

        if not selected:
            flash("Data history compare tidak ditemukan.")
            return redirect( url_for("history"))

        result_file = selected.get("result_file")
        if not result_file:
            flash("File hasil compare tidak ditemukan.")
            return redirect(url_for("history"))

        result_path = os.path.join(
            HISTORY_FOLDER,
            result_file
        )

        if not os.path.exists(result_path):

            flash("File hasil compare sudah tidak tersedia.")
            return redirect(
                url_for("history")
            )

        with open(
            result_path,
            "r",
            encoding="utf-8"
        ) as f:
            result = json.load(f)

        added = result.get("added",[])
        removed = result.get("removed",[])
        changed = result.get("changed",[])
        expiring = result.get("expiring",[])

        file1 = selected.get(
            "file1",
            "old"
        )
        file2 = selected.get(
            "file2",
            "new"
        )
        old_name = os.path.splitext(
            file1
        )[0]
        new_name = os.path.splitext(
            file2
        )[0]
        download_filename = (
            f"{old_name}_vs_{new_name}.xlsx"
        )
        output_path = os.path.join(
            DAILY_RESULTS_FOLDER,
            download_filename
        )

        with pd.ExcelWriter(
            output_path,
            engine="openpyxl"
        ) as writer:
            df_added = pd.DataFrame(
                added
            )
            if df_added.empty:
                df_added = pd.DataFrame({
                    "Information": ["Tidak ada data Added"]
                })

            df_added.to_excel(
                writer,
                sheet_name="Added",
                index=False
            )

            df_removed = pd.DataFrame(removed)
            if df_removed.empty:
                df_removed = pd.DataFrame({
                    "Information": ["Tidak ada data Removed"]
                })

            df_removed.to_excel(
                writer,
                sheet_name="Removed",
                index=False
            )

            df_changed = pd.DataFrame(changed)
            if df_changed.empty:
                df_changed = pd.DataFrame({
                    "Information": ["Tidak ada data Changed"]
                })

            df_changed.to_excel(
                writer,
                sheet_name="Changed",
                index=False
            )

            df_expiring = pd.DataFrame(expiring)
            if df_expiring.empty:
                df_expiring = pd.DataFrame({
                    "Information": ["Tidak ada license expiring"]
                })

            df_expiring.to_excel(
                writer,
                sheet_name="Expiring",
                index=False
            )

        return send_file(
            output_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            )
        )

    except Exception as e:
        print(
            "DOWNLOAD HISTORY ERROR:",
            str(e)
        )
        flash(
            f"Gagal download history: {str(e)}"
        )
        return redirect(
            url_for("history")
        )

@app.route("/download_history_daily/<id>")
def download_history_daily(id):
    try:
        with open(
            DAILY_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)

        selected = next(
            (
                h for h in history
                if str(
                    h.get("id")
                )
                == str(id)
            ),
            None
        )

        if not selected:
            flash("History simulasi tidak ditemukan.")
            return redirect(url_for("history_daily"))

        simulation = selected.get("result",{})
        simulation_results = simulation.get("results",[])
        start_name = os.path.splitext(
            selected.get(
                "start_file",
                "start"
            )
        )[0]

        end_name = os.path.splitext(
            selected.get(
                "end_file",
                "end"
            )
        )[0]

        download_filename = (
            f"simulation_"
            f"{start_name}_to_{end_name}.xlsx"
        )

        output_path = os.path.join(
            DAILY_RESULTS_FOLDER,
            download_filename
        )

        with pd.ExcelWriter(
            output_path,
            engine="openpyxl"
        ) as writer:
            summary_rows = []
            summary_rows.append({
                "Hari": 1,
                "File Lama": "-",
                "File Baru":
                    selected.get(
                        "baseline",
                        "-"
                    ),
                "Status":
                    "BASELINE",
                "Added": 0,
                "Removed": 0,
                "Changed": 0,
                "Expiring": 0
            })
            for item in simulation_results:
                summary_rows.append({
                    "Hari":
                        item.get(
                            "day"
                        ),
                    "File Lama":
                        item.get(
                            "previous_file"
                        ),
                    "File Baru":
                        item.get(
                            "today_file"
                        ),
                    "Status":
                        "COMPARE",
                    "Added":
                        len(
                            item.get(
                                "added",
                                []
                            )
                        ),
                    "Removed":
                        len(
                            item.get(
                                "removed",
                                []
                            )
                        ),
                    "Changed":
                        len(
                            item.get(
                                "changed",
                                []
                            )
                        ),
                    "Expiring":
                        len(
                            item.get(
                                "expiring",
                                []
                            )
                        )
                })

            pd.DataFrame(summary_rows).to_excel(
                writer,
                sheet_name="Summary",
                index=False
            )

            for item in simulation_results:
                day = item.get("day")
                df_added = pd.DataFrame(
                    item.get(
                        "added",
                        []
                    )
                )

                if df_added.empty:
                    df_added = pd.DataFrame({
                        "Information": ["Tidak ada data Added"]
                    })

                df_added.to_excel(
                    writer,
                    sheet_name=f"Added_H{day}",
                    index=False
                )

                df_removed = pd.DataFrame(
                    item.get(
                        "removed",
                        []
                    )
                )

                if df_removed.empty:
                    df_removed = pd.DataFrame({
                        "Information": ["Tidak ada data Removed"]
                    })

                df_removed.to_excel(
                    writer,
                    sheet_name=f"Removed_H{day}",
                    index=False
                )

                df_changed = pd.DataFrame(
                    item.get(
                        "changed",
                        []
                    )
                )

                if df_changed.empty:
                    df_changed = pd.DataFrame({
                        "Information": ["Tidak ada data Changed"]
                    })

                df_changed.to_excel(
                    writer,
                    sheet_name=f"Changed_H{day}",
                    index=False
                )

                df_expiring = pd.DataFrame(
                    item.get(
                        "expiring",
                        []
                    )
                )

                if df_expiring.empty:
                    df_expiring = pd.DataFrame({
                        "Information": ["Tidak ada licence expiring"]
                    })

                df_expiring.to_excel(
                    writer,
                    sheet_name=f"Expiry_H{day}",
                    index=False
                )

        return send_file(
            output_path,
            as_attachment=True,
            download_name=
                download_filename,
            mimetype=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            )
        )

    except Exception as e:
        print("DOWNLOAD SIMULATION ERROR:",str(e))
        flash(f"Gagal membuat hasil simulasi: {str(e)}")
        return redirect(
            url_for("history_daily")
        )

@app.route("/delete_history/<id>")
def delete_history(id):
    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)

        new_history = []

        for item in history:
            if str(item.get("id")) == str(id):
                result_file = item.get("result_file")
                if result_file:
                    result_path = os.path.join(
                        HISTORY_FOLDER,
                        result_file
                    )
                    if os.path.exists(result_path):
                        os.remove(result_path)
            else:
                new_history.append(item)

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                new_history,
                f,
                indent=4,
                ensure_ascii=False
            )
        flash("History compare berhasil dihapus.")

    except Exception as e:
        flash(
            f"Gagal hapus history compare: {str(e)}"
        )

    return redirect(
        url_for("history")
    )

@app.route("/delete_history_daily/<id>")
def delete_history_daily(id):
    try:
        with open(
            DAILY_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)

        new_history = [
            item
            for item in history
            if str(
                item.get("id")
            )
            != str(id)
        ]

        if len(new_history) == len(history):
            flash("Data history daily tidak ditemukan.")
        else:
            flash("History daily berhasil dihapus.")
        with open(
            DAILY_HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                new_history,
                f,
                indent=4,
                ensure_ascii=False,
                default=str
            )

    except Exception as e:
        flash(
            f"Gagal hapus history daily: {str(e)}"
        )

    return redirect(
        url_for("history_daily")
    )

if __name__ == "__main__":
    app.run(
        debug=True
    )