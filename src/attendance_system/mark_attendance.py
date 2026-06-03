import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def mark_attendance(names_data, output_folder=os.path.join(BASE_DIR, "attendance_records")):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(output_folder, f"attendance_{date_str}.csv")

    # Handle both list and dict for backward compatibility
    if isinstance(names_data, dict):
        unique_entries = {name: img for name, img in names_data.items() if name != "Unknown"}
    else:
        unique_entries = {name: "Unknown Image" for name in names_data if name != "Unknown"}

    file_exists = os.path.isfile(file_path)

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["Name", "Status", "Time", "ImageName"])

        for name, image_name in unique_entries.items():
            writer.writerow([name, "Present", datetime.now().strftime("%H:%M:%S"), image_name])

    print("[INFO] Attendance marked successfully!")