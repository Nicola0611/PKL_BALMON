import pandas as pd
from datetime import datetime
from utils.config import Config
from utils.notifier import send_telegram

def read_file(path):
    if path.endswith(".csv"):
        df = pd.read_csv(path)
    elif path.endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        raise ValueError("Format file tidak didukung")
    df.columns = df.columns.astype(str).str.strip()
    return df

def format_date(date_value):
    try:
        dt = pd.to_datetime(
            date_value,
            errors="coerce"
        )
        if pd.isna(dt):
            return "-"
        return dt.strftime("%d-%m-%Y")
    except Exception:
        return "-"

def compare_data(file1_path, file2_path):
    df1 = read_file(file1_path)
    df2 = read_file(file2_path)

    KEY_COLUMN = Config.KEY_COLUMN
    if KEY_COLUMN not in df1.columns:
        raise ValueError(
            f"Kolom '{KEY_COLUMN}' tidak ditemukan "
            f"di file pertama!"
        )
    if KEY_COLUMN not in df2.columns:
        raise ValueError(
            f"Kolom '{KEY_COLUMN}' tidak ditemukan "
            f"di file kedua!"
        )
    if "MASA_LAKU" not in df2.columns:
        raise ValueError(
            "Kolom 'MASA_LAKU' tidak ditemukan "
            "di file baru!"
        )
    df1 = df1.drop_duplicates(
        subset=[KEY_COLUMN]
    )
    df2 = df2.drop_duplicates(
        subset=[KEY_COLUMN]
    )
    df1.set_index(
        KEY_COLUMN,
        inplace=True
    )
    df2.set_index(
        KEY_COLUMN,
        inplace=True
    )
    compare_columns = [
        col
        for col in df1.columns
        if col in df2.columns
        and col not in Config.EXCLUDED_COMPARE_COLUMNS
    ]

    added_ids = df2.index.difference(
        df1.index
    )
    added = (
        df2
        .loc[added_ids]
        .reset_index()
        .to_dict(
            orient="records"
        )
    )

    removed_ids = df1.index.difference(df2.index)
    removed = (df1.loc[removed_ids].reset_index().to_dict(orient="records"))

    common_ids = df1.index.intersection(df2.index)

    changed = []
    for appl_id in common_ids:
        old = df1.loc[appl_id]
        new = df2.loc[appl_id]
        for col in compare_columns:
            old_value = old[col]
            new_value = new[col]
            if pd.isna(old_value) and pd.isna(new_value):
                continue
            if pd.isna(old_value) != pd.isna(new_value):
                changed.append({
                    "APPL_ID": appl_id,
                    "kolom": col,
                    "old": old_value,
                    "new": new_value
                })
                continue

            if str(old_value) != str(new_value):
                changed.append({
                    "APPL_ID": appl_id,
                    "kolom": col,
                    "old": old_value,
                    "new": new_value
                })

    today = datetime.now()
    expiring = []
    alerts = []

    for idx, row in df2.iterrows():
        exp_date = pd.to_datetime(row["MASA_LAKU"],errors="coerce")
        if pd.isna(exp_date):
            continue
        diff = (exp_date - today).days
        if diff <= Config.ALERT_DAYS:
            data = {
                "APPL_ID": idx,"CLNT_NAME":
                    row.get("CLNT_NAME","-"),"LICENCE_DATE":
                    format_date(exp_date),"SISA_HARI":diff}
            expiring.append(data)
            alerts.append(data)

    message = ("<b>📊 HASIL COMPARE DATA</b>\n\n")

    if added:
        message += (
            f"<b>🟢 DATA BARU "
            f"({len(added)})</b>\n"
        )
        for a in added[:10]:
            message += (
                f"{a.get('APPL_ID', '-')}"
                f" | "
                f"{a.get('CLNT_NAME', '-')}\n"
            )
        message += "\n"

    if removed:
        message += (
            f"<b>🔴 DATA DIHAPUS "
            f"({len(removed)})</b>\n"
        )
        for r in removed[:10]:
            message += (
                f"{r.get('APPL_ID', '-')}"
                f" | "
                f"{r.get('CLNT_NAME', '-')}\n"
            )
        message += "\n"

    if changed:
        message += (
            f"<b>🟡 DATA BERUBAH "
            f"({len(changed)})</b>\n"
        )

        for c in changed[:10]:
            old_value = c["old"]
            new_value = c["new"]

            if c["kolom"] in [
                "MASA_LAKU",
                "LICENCE_DATE",
                "VALIDITY_DATE",
                "APPL_DATE",
                "ARCHIV_DATE"
            ]:
                old_value = format_date(old_value)
                new_value = format_date(new_value)
            message += (
                f"{c['APPL_ID']} | "
                f"{c['kolom']} → "
                f"{old_value} ➝ "
                f"{new_value}\n"
            )

        message += "\n"

    if expiring:
        message += (
            f"<b>⚠️ LICENCE EXPIRING "
            f"({len(expiring)})</b>\n"
        )

        for e in expiring[:10]:
            message += (
                f"{e['APPL_ID']} | "
                f"{e['CLNT_NAME']} | "
                f"{e['LICENCE_DATE']} "
                f"({e['SISA_HARI']} hari)\n"
            )

        message += "\n"

    if (
        added
        or removed
        or changed
        or expiring
    ):
        try:
            send_telegram(message)
        except Exception as e:
            print("Gagal kirim Telegram:",e)

    for row in added:
        if "MASA_LAKU" in row:
            row["MASA_LAKU"] = format_date(
                row["MASA_LAKU"]
            )

    for row in removed:
        if "MASA_LAKU" in row:
            row["MASA_LAKU"] = format_date(
                row["MASA_LAKU"]
            )

    for row in changed:
        if row["kolom"] in [
            "MASA_LAKU",
            "LICENCE_DATE",
            "VALIDITY_DATE",
            "APPL_DATE",
            "ARCHIV_DATE"
        ]:
            row["old"] = format_date(row["old"])
            row["new"] = format_date(row["new"])

    all_columns = [KEY_COLUMN] + compare_columns

    return {
        "columns": all_columns,
        "added": added,
        "removed": removed,
        "changed": changed,
        "expiring": expiring
    }