import json
import os
from datetime import datetime
from requests import get
from bs4 import BeautifulSoup
from xlrd import open_workbook, xldate_as_datetime

class ConfigLoader:
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = json.load(file)
            
    def get(self, key, default=None):
        return self.config.get(key, default)

class WebScraper:
    def __init__(self, base_url, month_translation):
        self.base_url = base_url
        self.month_translation = month_translation
        
    def fetch_page_content(self):
        response = get(self.base_url)
        return BeautifulSoup(response.content, 'html.parser')
    
    def find_schedule_link(self, soup):
        current_month = self.month_translation[datetime.now().strftime("%B")]
        return soup.find('a', href=True, string=lambda x: x and "очная" in x and current_month in x.upper())
    
    def get_update_date(self, schedule_link):
        update_date_element = schedule_link.find_next('p', class_='m-doc__data')
        return update_date_element.string if update_date_element else None

class ScheduleManager:
    def __init__(self, schedules_directory, filename_prefix, base_file_url, last_update_check_file):
        self.schedules_directory = schedules_directory
        self.filename_prefix = filename_prefix
        self.base_file_url = base_file_url
        self.last_update_check_file = last_update_check_file

    def download_schedule(self) -> bool:
        response = get(self.update_url, stream=True)
        response.raise_for_status()
        if not os.path.exists(os.path.dirname(self.download_path)):
            os.makedirs(os.path.dirname(self.download_path))
        
        with open(self.download_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True

    def last_update_date(self):
        update_date_filepath = os.path.join(self.schedules_directory, 'last_update_date.txt')
        try:
            with open(update_date_filepath, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            return None

    def save_last_update_date(self, update_date):
        update_date_filepath = os.path.join(self.schedules_directory, 'last_update_date.txt')
        with open(update_date_filepath, 'w') as file:
            file.write(update_date)

class ScheduleProcessor:
    TEACHER_PREFIXES = ["проф.", "доц.", "ст.пр.", "асс."]

    @staticmethod
    def open_excel_file(filepath):
        try:
            workbook = open_workbook(filepath)
            return workbook
        except FileNotFoundError:
            print(f"Файл {filepath} не найден.")
            return None

    @staticmethod
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
        ongoing_event_details = [""] * sheet.ncols
        for rowx in range(schedule_start_row + 1, sheet.nrows):
            row = sheet.row_values(rowx)
            day = row[0] if row[0] else last_valid_day
            date = xldate_as_datetime(row[1], sheet.book.datemode) if (row[1] and isinstance(row[1], (int, float))) else last_valid_date
            time = row[2]
            if isinstance(time, float):
                hours = int(time * 24)
                minutes = int((time * 24 - hours) * 60)
                time = f"{hours:02d}:{minutes:02d}"
            if row[0]:
                last_valid_day = row[0]
            if row[1] and isinstance(row[1], (int, float)):
                last_valid_date = date
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
                    if isinstance(next_row[colx], str) and any(prefix in next_row[colx] for prefix in ScheduleProcessor.TEACHER_PREFIXES) or (isinstance(next_row[colx], str) and 1 <= len(next_row[colx].split()) <= 2):
                        group_data += ', ' + next_row[colx]
                if group_data and not isinstance(group_data, (int, float)) and date and group_data not in group_names:
                    if group_data.startswith("направление"):
                        classification["Направление"] = group_data[len("направление"):].strip()
                        group_data = ""
                    ongoing_event_details[colx] += group_data + "\\n"
                if (rowx < sheet.nrows - 1 and sheet.row_values(rowx + 1)[2] != row[2]) or rowx == sheet.nrows - 1:
                    if ongoing_event_details[colx].strip() and time not in ["", "Не указано"] and day != "День недели" and time != "Время":
                        schedule_data.append({**classification, "Детали": ongoing_event_details[colx].strip()})
                    ongoing_event_details[colx] = ""
        return schedule_data

    @staticmethod
    def get_course_by_group_name(group_name):
        current_year = datetime.now().year
        try:
            start_year = 2000 + int(group_name[-2:])
        except ValueError:
            return None
        course = current_year - start_year + 1
        return course

    def filter_schedule_by_course(self, all_schedule_data, selected_course):
        current_year = datetime.now().year
        return [
            record for record in all_schedule_data if self.get_course_by_group_name(record["Группа"]) == selected_course
        ]

    def filter_schedule_by_group(self, filtered_schedule_data, selected_group):
        return [
            record for record in filtered_schedule_data if record["Группа"] == selected_group
        ]

    def filter_schedule_by_date(self, group_schedule_data, selected_date):
        return [
            record for record in group_schedule_data if record["Дата"] == selected_date.strftime("%d-%m-%Y")
        ]

class ScheduleBot:
    def __init__(self):
        self.config_loader = ConfigLoader()
        config = self.config_loader.config
        self.base_url = config['BASE_URL']
        self.month_translation = config['MONTH_TRANSLATION']
        self.schedules_directory = config['SCHEDULES_DIRECTORY']
        self.filename_prefix = config['FILENAME_PREFIX']
        self.base_file_url = config['BASE_FILE_URL']
        self.last_update_check_file = config['LAST_UPDATE_CHECK_FILE']
        self.scraper = WebScraper(self.base_url, self.month_translation)
        self.schedule_manager = ScheduleManager(
            self.schedules_directory, 
            self.filename_prefix, 
            self.base_file_url,
            self.last_update_check_file
        )
        self.schedule_processor = ScheduleProcessor()

    def check_and_update_schedule(self):
        soup = self.scraper.fetch_page_content()
        schedule_link = self.scraper.find_schedule_link(soup)
        if not schedule_link:
            print("Расписание не найдено.")
            return
        update_date = self.scraper.get_update_date(schedule_link)
        last_update_date = self.schedule_manager.last_update_date()
        if last_update_date and update_date == last_update_date:
            print("Расписание не обновлялось.")
        else:
            print("Расписание обновилось.")
            self.schedule_manager.download_schedule(schedule_link)
            self.schedule_manager.save_last_update_date(update_date)
