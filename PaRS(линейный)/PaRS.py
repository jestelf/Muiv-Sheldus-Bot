from bs4 import BeautifulSoup
from requests import get
from time import sleep
from xlrd import open_workbook, xldate_as_datetime
from datetime import datetime
import json
import os
api_cache = {}
with open('config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)
BASE_URL = config['BASE_URL']
MONTH_TRANSLATION = config['MONTH_TRANSLATION']
SLEEP_DURATION = config['SLEEP_DURATION']
SCHEDULES_DIRECTORY = config['SCHEDULES_DIRECTORY']
TEACHER_PREFIXES = config['TEACHER_PREFIXES']
BASE_FILE_URL = config['BASE_FILE_URL']
FILENAME_PREFIX = config['FILENAME_PREFIX']
while True:
    response = get(BASE_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    current_month = MONTH_TRANSLATION[datetime.now().strftime("%B")]
    schedule_link = soup.find('a', href=True, string=lambda x: x and "очная" in x and current_month in x.upper())
    update_date_element = schedule_link.find_next('p', class_='m-doc__data')
    update_date_text = update_date_element.string if update_date_element else None
    if schedule_link:
        script_dir = os.path.dirname(__file__)
        os.makedirs(os.path.join(script_dir, SCHEDULES_DIRECTORY), exist_ok=True)
        update_date_filepath = os.path.join(script_dir, SCHEDULES_DIRECTORY, 'last_update_date.txt')
        try:
            with open(update_date_filepath, 'r') as file:
                last_update_date = file.read().strip()
        except FileNotFoundError:
            last_update_date = None
        if last_update_date and update_date_text == last_update_date:
            print("Расписание не обновлялось.")
        else:
            print("Расписание обновилось.")
            file_url = BASE_FILE_URL + schedule_link['href']
            file_response = get(file_url)
            filename = os.path.join(script_dir, SCHEDULES_DIRECTORY, FILENAME_PREFIX + ".xls")
            with open(filename, 'wb') as file:
                file.write(file_response.content)
            with open(update_date_filepath, 'w') as file:
                file.write(update_date_text)
            print(f"Файл '{filename}' успешно скачан.")
    else:
        print("Актуальный файл с расписанием не найден.")

    def extract_and_format_schedule(sheet):
        for rowx in range(sheet.nrows):
            row = sheet.row_values(rowx)
            if "День недели" in row:
                schedule_start_row = rowx + 1
                break
        else:
            return None
        group_names = sheet.row_values(schedule_start_row)
        schedule_data = []
        last_valid_day = ""
        last_valid_date = ""
        current_week = ""
        ongoing_event_details = [""] * sheet.ncols
        teacher_prefixes = TEACHER_PREFIXES
        for rowx in range(schedule_start_row + 1, sheet.nrows):
            row = sheet.row_values(rowx)
            day = row[0] if row[0] else last_valid_day
            date = xldate_as_datetime(row[1], xl_workbook.datemode) if (row[1] and isinstance(row[1], (int, float))) else last_valid_date
            time = row[2]
            if isinstance(time, float):
                hours = int(time * 24)
                minutes = int((time * 24 - hours) * 60)
                time = f"{hours:02d}:{minutes:02d}"
            if row[0]:
                last_valid_day = row[0]
            if row[1] and isinstance(row[1], (int, float)):
                last_valid_date = date
            if "НЕДЕЛЯ" in row[0]:
                current_week = row[0]
            for colx in range(3, sheet.ncols):
                group_data = row[colx]
                classification = {
                    "День недели": day,
                    "Дата": date.strftime('%d-%m-%Y') if date else '',
                    "Время": time if time else "Не указано",
                    "Группа": group_names[colx],
                }
                if isinstance(group_data, str) and rowx < sheet.nrows - 1:
                    next_row = sheet.row_values(rowx + 1)
                    if isinstance(next_row[colx], str) and any(prefix in next_row[colx] for prefix in teacher_prefixes) or (isinstance(next_row[colx], str) and 1 <= len(next_row[colx].split()) <= 2):
                        group_data += ', ' + next_row[colx]
                if group_data and not isinstance(group_data, (int, float)) and date and group_data not in group_names:
                    if group_data.startswith("направление"):
                        classification["Направление"] = group_data[len("направление"):].strip()
                        group_data = ""
                    ongoing_event_details[colx] += group_data + "\n"
                if (rowx < sheet.nrows - 1 and xl_workbook.sheet_by_name(sheet_name).row_values(rowx + 1)[2] != row[2]) or rowx == sheet.nrows - 1:
                    if ongoing_event_details[colx].strip() and time not in ["", "Не указано"] and day != "День недели" and time != "Время":
                        schedule_data.append({**classification, "Детали": ongoing_event_details[colx].strip()})
                    ongoing_event_details[colx] = ""
        return schedule_data
    xl_workbook = open_workbook("F:\\git\\Muiv-sheldus\\PaRS(линейный)\\schedules\\raspisanie.xls")
    sheet_names = xl_workbook.sheet_names()
    all_schedule_data = []
    for sheet_name in sheet_names:
        sheet = xl_workbook.sheet_by_name(sheet_name)
        schedule_data = extract_and_format_schedule(sheet)
        if schedule_data:
            all_schedule_data.extend(schedule_data)
    def get_course_by_group_name(group_name, current_year):
        """Определить курс по имени группы."""
        try:
            start_year = 2000 + int(group_name[-2:])
        except ValueError:
            return None
        course = current_year - start_year + 1
        return course
    current_year = datetime.now().year
    while True:
        try:
            selected_course = int(input("Введите курс (1-4 и т.д.): "))
            if 1 <= selected_course <= 6:
                break
            else:
                print("Неверный ввод. Попробуйте еще раз.")
        except ValueError:
            print("Пожалуйста, введите число.")
    filtered_schedule_data = [
        record for record in all_schedule_data if get_course_by_group_name(record["Группа"], current_year) == selected_course
    ]
    available_groups = sorted(set(record["Группа"] for record in filtered_schedule_data))
    for idx, group in enumerate(available_groups, start=1):
        print(f"{idx}. {group}")
    while True:
        try:
            group_choice = int(input(f"Введите номер группы (1-{len(available_groups)}): "))
            if 1 <= group_choice <= len(available_groups):
                selected_group = available_groups[group_choice - 1]
                break
            else:
                print(f"Неверный ввод. Выберите номер от 1 до {len(available_groups)}.")
        except ValueError:
            print("Пожалуйста, введите число.")

    for record in filtered_schedule_data:
        if record["Группа"] == selected_group:
            for key, value in record.items():
                print(f"{key}: {value}")
            print()
    while True:
        date_input = input("Введите дату в формате день-месяц-год (например, 30-09-2023): ")
        try:
            selected_date = datetime.strptime(date_input, "%d-%m-%Y").date()
            break
        except ValueError:
            print("Неверный формат даты. Попробуйте еще раз.")
    for record in filtered_schedule_data:
        if record["Группа"] == selected_group and record["Дата"] == selected_date.strftime("%d-%m-%Y"):
            for key, value in record.items():
                print(f"{key}: {value}")
            print()
    sleep(10800)