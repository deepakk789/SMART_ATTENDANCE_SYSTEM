import csv
import os
from datetime import datetime

def mark_attendance(names, output_folder="attendance_records"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(output_folder, f"attendance_{date_str}.csv")

    unique_names = set([name for name in names if name != "Unknown"])

    file_exists = os.path.isfile(file_path)

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["Name", "Status", "Time"])

        for name in unique_names:
            writer.writerow([name, "Present", datetime.now().strftime("%H:%M:%S")])

    print("[INFO] Attendance marked successfully!")