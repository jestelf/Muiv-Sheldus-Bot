import json
import re
import datetime
import os

class ConfigEditor:
    def __init__(self):
        with open('config.json', 'r', encoding='utf-8') as file:
            self.config = json.load(file)
        self.actions = {
            "1": {"text": "BASE_URL", "action": self.edit_base_url},
            "2": {"text": "MONTH_TRANSLATION", "action": self.edit_month_translation},
            "3": {"text": "SLEEP_DURATION", "action": self.edit_sleep_duration},
            "4": {"text": "BASE_FILE_URL", "action": self.edit_base_file_url},
            "5": {"text": "SCHEDULE_DIRECTORY", "action": self.edit_schedule_directory},
            "6": {"text": "FILENAME_PREFIX", "action": self.edit_filename_prefix},
            "7": {"text": "TEACHER_PREFIX", "action": self.edit_teacher_prefix},
            "8": {"text": "Сохранить и выйти", "action": self.save_and_exit},
            "9": {"text": "Выйти без сохранения", "action": self.exit_without_saving},
        }

    def show_menu(self):
        print("\nВыберите параметр для редактирования:")
        for key, value in self.actions.items():
            print(f"{key}. {value['text']}")

    def run(self):
        while True:
            self.show_menu()
            choice = input("> ")
            if choice in self.actions:
                self.actions[choice]['action']()
            else:
                print("Неизвестный выбор. Пожалуйста, попробуйте еще раз.")

    def is_valid_url(self, url):
        regex = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        return re.match(regex, url) is not None

    def is_valid_positive_number(self, number_str):
        try:
            number = float(number_str)
            return number > 0
        except ValueError:
            return False

    def is_valid_filename(self, filename):
        invalid_chars = set(r'<>:"/\|?*')
        return not any((char in invalid_chars) for char in filename)

    def is_valid_month_language(self, lang):
        return isinstance(lang, str) and len(lang) > 0

    def edit_base_url(self):
        url = input("Введите новый BASE_URL: ")
        if self.is_valid_url(url):
            self.config['BASE_URL'] = url
        else:
            print("Введен недопустимый URL.")

    def edit_month_translation(self):
        print("Текущие переводы месяцев:")
        for key, value in self.config['MONTH_TRANSLATION'].items():
            print(f"{key}: {value}")
        lang = input("Введите язык месяца для добавления/изменения: ")
        if self.is_valid_month_language(lang):
            translation = input(f"Введите перевод для {lang}: ")
            self.config['MONTH_TRANSLATION'][lang] = translation
        else:
            print("Недопустимый язык месяца.")

    def edit_sleep_duration(self):
        duration = input("Введите новое значение для SLEEP_DURATION (в секундах): ")
        if self.is_valid_positive_number(duration):
            self.config['SLEEP_DURATION'] = float(duration)
        else:
            print("Введите допустимое положительное число.")

    def edit_base_file_url(self):
        url = input("Введите новый BASE_FILE_URL: ")
        if self.is_valid_url(url):
            self.config['BASE_FILE_URL'] = url
        else:
            print("Введен недопустимый URL.")

    def edit_schedule_directory(self):
        directory = input("Введите новое имя для директории SCHEDULE_DIRECTORY: ")
        if self.is_valid_filename(directory):
            self.config['SCHEDULE_DIRECTORY'] = directory
        else:
            print("Введено недопустимое имя директории.")

    def edit_filename_prefix(self):
        prefix = input("Введите новый префикс для FILENAME_PREFIX: ")
        if self.is_valid_filename(prefix):
            self.config['FILENAME_PREFIX'] = prefix
        else:
            print("Введен недопустимый префикс.")

    def edit_teacher_prefix(self):
        print("Текущие префиксы учителей:")
        for prefix in self.config['TEACHER_PREFIX']:
            print(prefix)
        action = input("Добавить новый префикс или удалить существующий? (add/remove): ").lower()
        if action == "add":
            new_prefix = input("Введите новый префикс учителя: ")
            self.config['TEACHER_PREFIX'].append(new_prefix)
        elif action == "remove":
            prefix = input("Введите префикс учителя для удаления: ")
            if prefix in self.config['TEACHER_PREFIX']:
                self.config['TEACHER_PREFIX'].remove(prefix)
            else:
                print("Префикс не найден.")
        else:
            print("Неизвестное действие.")

    def save_and_exit(self):

        backup_filename = 'config_backup_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.json'
        backup_folder = 'backup'
        if not os.path.exists(backup_folder):
            os.mkdir(backup_folder)
        with open(os.path.join(backup_folder, backup_filename), 'w', encoding='utf-8') as backup_file:
            json.dump(self.config, backup_file, ensure_ascii=False, indent=4)

        with open('config.json', 'w', encoding='utf-8') as file:
            json.dump(self.config, file, ensure_ascii=False, indent=4)
        print("Конфигурация сохранена. Выход.")
        exit()

    def exit_without_saving(self):
        print("Выход без сохранения.")
        exit()

editor = ConfigEditor()
editor.run()
