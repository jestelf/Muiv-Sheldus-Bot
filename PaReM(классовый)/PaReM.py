
from bs4 import BeautifulSoup
from requests import get
from xlrd import open_workbook, xldate_as_datetime
from datetime import datetime, timedelta
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

class WebScheduleManager:
    def __init__(self, config):
        pass

    def get_schedule_link(self):
        """Получает ссылку на текущее месячное расписание и дату его последнего обновления."""
        response = get(BASE_URL)
        soup = BeautifulSoup(response.content, 'html.parser')
        current_month = MONTH_TRANSLATION[datetime.now().strftime("%B")]
        schedule_link = soup.find('a', href=True, string=lambda x: x and "очная" in x and current_month in x.upper())
        update_date_element = schedule_link.find_next('p', class_='m-doc__data') if schedule_link else None
        update_date_text = update_date_element.string if update_date_element else None
        return schedule_link, update_date_text
    
    def check_and_download_updated_schedule(self):
        """Checks if the schedule has been updated and downloads it if needed."""
        schedule_link, update_date_text = self.get_schedule_link()
        script_dir = os.path.dirname(__file__)
        update_date_filepath = os.path.join(script_dir, SCHEDULES_DIRECTORY, 'last_update_date.txt')
        try:
            with open(update_date_filepath, 'r') as file:
                last_update_date = file.read().strip()
        except FileNotFoundError:
            last_update_date = None
        if update_date_text != last_update_date:
            print("Расписание обновилось.")
            file_url = self.BASE_FILE_URL + schedule_link['href']
            file_response = get(file_url)
            filename = os.path.join(script_dir, SCHEDULES_DIRECTORY, self.FILENAME_PREFIX + ".xls")
            with open(filename, 'wb') as file:
                file.write(file_response.content)
            with open(update_date_filepath, 'w') as file:
                file.write(update_date_text)
        else:
            print("Расписание не обновлялось.")

class DataFilter:
    def __init__(self, config):
        pass

    def get_course_by_group_name(group_name, current_year=None):
        """Определяет курс студента на основе названия его группы."""
        try:
            start_year = int(group_name.split("-")[-1])
        except ValueError:
            return None
        if not current_year:
            current_year = datetime.now().year
        course = current_year - start_year + 1
        return course
    
    def filter_schedule_by_course(all_schedule_data, selected_course):
        """Фильтрует расписание по выбранному курсу."""
        current_year = datetime.now().year
        filtered_schedule_data = [
            record for record in all_schedule_data if get_course_by_group_name(record["Группа"], current_year) == selected_course
        ]
        return filtered_schedule_data
    
    def filter_schedule(self, data, group=None, date=None, day=None, week=False):
        """Filters the schedule based on the given parameters."""
        filtered_data = data
        if group:
            filtered_data = [entry for entry in filtered_data if entry['Группа'] == group]
        if date:
            filtered_data = [entry for entry in filtered_data if entry['Дата'] == date.strftime('%d-%m-%Y')]
        if day:
            filtered_data = [entry for entry in filtered_data if entry['Дата'] == day]
        if week:
            today = datetime.now()
            start_of_week = (today - timedelta(days=today.weekday())).strftime('%d-%m-%Y')
            end_of_week = (today + timedelta(days=(6-today.weekday()))).strftime('%d-%m-%Y')
            filtered_data = [entry for entry in filtered_data if start_of_week <= entry['Дата'] <= end_of_week]
        return filtered_data


class UserInterface:
    def __init__(self, config):
        pass

    
    def user_input(self, prompt, input_type=int, validation_func=None):
        """Generic user input function with validation."""
        while True:
            user_response = input(prompt)
            try:
                value = input_type(user_response)
                if validation_func and validation_func(value):
                    return value
                elif not validation_func:
                    return value
            except ValueError:
                pass

    def user_input(self, prompt, input_type, validation_func=None, validation_message="Invalid input. Try again."):
        """Handles user input with different input types and validations."""
        while True:
            try:
                user_input = input(prompt)
                if input_type == "int":
                    value = int(user_input)
                elif input_type == "date":
                    value = datetime.strptime(user_input, "%d-%m-%Y").date()
                else:
                    value = user_input
                if validation_func and not validation_func(value):
                    raise ValueError
                return value
            except ValueError:
                print(validation_message)


class UtilityFunctions:
    def __init__(self, config):
        pass

    def load_cached_api_data():
        """Загружает кэшированные данные API, если они существуют."""
        if "api_data" in api_cache:
            return api_cache["api_data"]
        else:
            return None
    
    def get_schedule_data_from_api():
        """Получает данные расписания из API или из кэша."""
        cached_data = load_cached_api_data()
        if cached_data:
            return cached_data
        api_data = []
        api_cache["api_data"] = api_data
        return api_data
    
    def ensure_schedules_directory_exists():
        """Убеждается, что директория для сохранения расписания существует."""
        script_dir = os.path.dirname(__file__)
        os.makedirs(os.path.join(script_dir, SCHEDULES_DIRECTORY), exist_ok=True)
    
    def extract_and_format_schedule(xl_workbook):
        """Извлекает и форматирует данные расписания из эксель-таблицы."""
        all_schedule_data = []
        for sheet_name in xl_workbook.sheet_names():
            sheet = xl_workbook.sheet_by_name(sheet_name)
    
            for rowx in range(sheet.nrows):
                row = sheet.row_values(rowx)
                if "День недели" in row:
                    schedule_start_row = rowx + 1
                    break
            else:
                continue
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
                        ongoing_event_details[colx] += group_data + ""
                    if (rowx < sheet.nrows - 1 and xl_workbook.sheet_by_name(sheet_name).row_values(rowx + 1)[2] != row[2]) or rowx == sheet.nrows - 1:
                        if ongoing_event_details[colx].strip() and time not in ["", "Не указано"] and day != "День недели" and time != "Время":
                            schedule_data.append({**classification, "Детали": ongoing_event_details[colx].strip()})
                        ongoing_event_details[colx] = ""
            all_schedule_data.extend(schedule_data)
        return all_schedule_data
    
    def read_xls_file(self, filename):
        return self.read_xls_file(filename)

    def ensure_and_extract_schedule(self):
        """Ensures the schedules directory exists and then extracts and formats the schedule."""
        script_dir = os.path.dirname(__file__)
        schedules_directory = os.path.join(script_dir, self.SCHEDULES_DIRECTORY)
        if not os.path.exists(schedules_directory):
            os.makedirs(schedules_directory)
        filename = os.path.join(script_dir, self.SCHEDULES_DIRECTORY, self.FILENAME_PREFIX + ".xls")
        if not os.path.exists(filename):
            print(f"File {filename} not found!")
            return None
        workbook = self.read_xls_file(filename)
        for sheet in workbook.sheets():
            if sheet.name == 'Raspisanie':
                return sheet
        return None