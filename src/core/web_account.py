import os
import subprocess
import time
import fake_useragent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class WebAccount:
    __browser: webdriver.Chrome
    __login: str
    __password: str

    __lessons: dict
    __groups: set

    def __init__(self):
        self.__open_browser()

    def __open_browser(self):
        user_agent = fake_useragent.UserAgent().random

        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument('--disable-gpu')
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--headless=new')
        options.set_capability("browserVersion", "117")
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_experimental_option('detach', True)

        service = webdriver.ChromeService(log_path=os.devnull)
        service.log_output = subprocess.DEVNULL

        self.__browser = webdriver.Chrome(service=service, options=options)
        self.__browser.set_window_size(1920, 1080)
        self.__browser.get('http://web-iais.admin.tstu.ru:7777/zion/f?p=503:LOGIN_DESKTOP:12291765971935')

    def enter_login(self, login, password):
        try:
            available = self.__check_available()
            if not available[0]:
                return False, f'В данный момент сайт недоступен\n{available[1]}'

            login_input = self.__browser.find_element(By.ID, 'P101_USERNAME')
            login_input.clear()
            password_input = self.__browser.find_element(By.ID, 'P101_PASSWORD')
            password_input.clear()
            enter_button = self.__browser.find_element(By.ID, 'P101_LOGIN')

            login_input.send_keys(login)
            password_input.send_keys(password)
            enter_button.click()

            if ('notification_msg' in self.__browser.current_url or
                    self.__browser.current_url == 'http://web-iais.admin.tstu.ru:7777/zion/wwv_flow.accept'):

                error = '# ' + self.__browser.find_element(
                    By.XPATH, '//section[@id="uNotificationMessage"]/p[1]'
                ).text + '\n'

                count_errors = len(self.__browser.find_elements(By.XPATH, '//ul[@class="htmldbUlErr"]/li'))

                for i in range(count_errors):
                    time.sleep(1)
                    error += '\n- ' + self.__browser.find_element(
                        By.XPATH, f'//ul[@class="htmldbUlErr"]/li[{i + 1}]'
                    ).text
                if 'Перейти' in error:
                    error = error.split(' (Перейти)')
                    error = ''.join(error)
                return False, error

            name = self.__browser.find_element(By.XPATH, '//a[@id="uLogo"]/span[1]').text.partition('-')[2].strip()
            self.__login = login
            self.__password = password
            self.__lessons = {}

            self.__groups = set()

            return True, name
        except Exception as e:
            self.__browser.quit()
            self.__open_browser()
            self.enter_login(self.__login, self.__password)
            return False, str(e)

    def personal_data(self):
        try:
            self.__check_main_page()

            self.__browser.find_element(By.LINK_TEXT, 'Личные данные').click()

            data = {
                "Личные данные": list,
                "Финансирование": list,
                "Приказы": list
            }

            # Личные данные
            personal_code = self.__browser.find_element(By.XPATH, '//label[@for="P1_MAN_ID"]/font').text
            code = self.__browser.find_element(By.ID, 'P1_MAN_ID').text

            fio_group_label = self.__browser.find_element(By.XPATH, '//label[@for="P1_STUD"]/font').text
            fio_group_data = self.__browser.find_element(By.ID, 'P1_STUD').text

            data['Личные данные'] = [[personal_code, fio_group_label], [code, fio_group_data]]

            # Финансирование
            # -- тут возможно ошибка, если вдруг в кабинете будет записано несколько факультетов -- #
            faculty = self.__browser.find_element(By.XPATH, '//td[@headers="FACULTY_NAME"]/span').text
            financing = self.__browser.find_element(By.XPATH, '//td[@headers="STUDENT_FINANCING"]/span').text
            data['Финансирование'] = [[faculty], [financing]]

            # Приказы
            # -- в этом разделе возможно ошибка, если вдруг в кабинете будут записаны приказы из разных институтов -- #
            # отдельно 6 элемент, потому что он разделен <br>
            col06_element = self.__browser.find_element(By.ID, 'COL06')
            col06_text = " ".join(col06_element.get_attribute("innerText").split())

            orders_data = [[
                self.__browser.find_element(By.ID, 'COL01').text.upper(),
                self.__browser.find_element(By.ID, 'COL02').text.upper(),
                self.__browser.find_element(By.ID, 'COL05').text.upper(),
                col06_text.upper(),
                self.__browser.find_element(By.ID, 'COL04').text.upper()
            ]]

            # здесь проверка, потому что есть другие элементы с таким же путем
            orders_row = self.__browser.find_elements(By.XPATH, '//table[@class="uReport uReportStandard"]/tbody/tr')
            for order_row in orders_row:
                if order_row.find_elements(By.XPATH, './/td[@headers="COL01"]'):
                    orders_data.append([
                        order_row.find_element(By.XPATH, './/td[@headers="COL01"]').text,
                        order_row.find_element(By.XPATH, './/td[@headers="COL02"]').text,
                        order_row.find_element(By.XPATH, './/td[@headers="COL05"]').text,
                        order_row.find_element(By.XPATH, './/td[@headers="COL06"]').text,
                        order_row.find_element(By.XPATH, './/td[@headers="COL04"]').text
                    ])
            data['Приказы'] = orders_data

            self.__main_page()
            return data
        except Exception as e:
            self.__browser.quit()
            self.__open_browser()
            self.enter_login(self.__login, self.__password)
            return False, str(e)

    def report_card(self):
        try:
            self.__check_main_page()

            self.__browser.find_element(By.LINK_TEXT, 'Успеваемость').click()

            if not self.__groups:
                self.__check_groups()

            self.__browser.find_element(By.XPATH, '//td[@headers="NUM_Z"]/a').click()

            report_card_data = {}

            try:
                long_path = ('//section[@class="uRegion uBorderlessRegion uHideShowRegion  clearfix"]/'
                             'div[@class="uRegionContent clearfix"]/table/tbody/tr')

                long_path_formation = (
                        long_path + '/td[1]/section/div[@class="uRegionContent clearfix"]/table/tbody/tr/td[1]/span'
                )
                formation_date = self.__browser.find_element(By.XPATH, long_path_formation).text

                long_path_number = (
                        long_path + '/td[2]/section/div[@class="uRegionContent clearfix"]/div/p[3]/span[2]'
                )
                number_report_card = self.__browser.find_element(By.XPATH, long_path_number).text

                report_card_data['Дополнительные данные'] = [
                    ['Дата формирования зачетной книжки', 'Номер зачетной книжки'],
                    [formation_date, number_report_card]
                ]
            except NoSuchElementException:
                pass

            # СТРАННО СДЕЛАНО, ТК ЕСТЬ КЛАСС "uRegion uBorderlessRegion uHideShowRegion  clearfix" ПРОБЕЛ В ДРУГОМ МЕСТЕ
            semesters_section = self.__browser.find_elements(
                By.XPATH, '//section[@class="uRegion uBorderlessRegion  uHideShowRegion clearfix"]'
            )

            for semester in semesters_section:
                semester.find_element(By.XPATH, './/div[@class="uRegionHeading"]/h1/a').click()
                time.sleep(.5)

                semester_data = []

                pages = semester.find_element(By.XPATH, './/div[@class="uRegionContent clearfix"]/table/tbody')
                for num in range(2):
                    # ВОЗМОЖНО ПЕРЕСТАНЕТ РАБОТАТЬ, ТК ПОИСК ПО СТРАННОМУ АБСОЛЮТНОМУ ПУТИ
                    long_path = ('.//tr/td[1]/section/div[@class="uRegionContent clearfix"]/'
                                 'section/div[@class="uRegionContent clearfix"]/div/table/tbody/tr')

                    if num == 1:
                        long_path = ('.//tr/td[2]/section/div[@class="uRegionContent clearfix"]/section/'
                                     'div[@class="uRegionContent clearfix"]/div/div/table/tbody/tr')

                    rows_data = []
                    for num_i, i in enumerate(pages.find_elements(By.XPATH, long_path)):
                        if num_i == 1:
                            row = [j.text for j in i.find_elements(By.TAG_NAME, 'th') if j.text]
                        else:
                            row = [j.text for j in i.find_elements(By.TAG_NAME, 'td') if j.text]

                        if row:
                            rows_data.append(row)
                    semester_data.append(rows_data)
                semester_number = semester.find_element(By.XPATH, './/div[@class="uRegionHeading"]/h1/span').text
                report_card_data[semester_number] = semester_data

            self.__main_page()
            return report_card_data
        except Exception as e:
            self.__browser.quit()
            self.__open_browser()
            self.enter_login(self.__login, self.__password)
            return False, str(e)

    def get_lessons(self, search: bool = False):
        if not search:
            return getattr(self, f'_{self.__class__.__name__}__lessons', None)
        else:
            try:
                self.__check_main_page()

                self.__browser.find_element(By.LINK_TEXT, 'Успеваемость').click()
                journals = self.__browser.find_elements(By.LINK_TEXT, 'Журналы')

                for i in range(len(journals)):
                    self.__browser.find_elements(By.LINK_TEXT, 'Журналы')[i].click()
                    self.__lessons[f"{i + 1} журнал"] = [
                        i.text.strip() for i in self.__browser.find_elements(By.XPATH, '//td[@headers="DISC"]')
                    ]
                    self.__browser.back()

                if not self.__groups:
                    self.__check_groups()

                self.__main_page()
                return self.__lessons
            except Exception as e:
                self.__browser.quit()
                self.__open_browser()
                self.enter_login(self.__login, self.__password)
                return False, str(e)

    def check_marks(self, lesson=None, details=False):
        try:
            self.__check_main_page()

            self.__browser.find_element(By.LINK_TEXT, 'Успеваемость').click()
            journals = self.__browser.find_elements(By.LINK_TEXT, 'Журналы')
            marks_data = {}
            marks_data_details = {}

            def extract_marks(lesson_name, all_students=False, student=None):
                if all_students:
                    if student.find_elements(By.XPATH, './/th'):
                        header = student.find_elements(By.XPATH, './/th')
                        marks_data_details[header[0].text] = [i.text for i in header[1:]]
                    else:
                        student_data = student.find_elements(By.XPATH, './/td')
                        student_name = student_data[0].text
                        marks_data_details[student_name] = (
                                [i.text for i in student_data[1:-1]] +
                                [student_data[-1].text.upper()]
                        )

                        """ КРАТКАЯ ИНФОРМАЦИЯ """
                        if 'Дисциплина' not in marks_data:
                            marks_data[lesson_name] = ['Первичный', 'Вторичный', 'Итог']

                        marks_data[student_name] = [
                            student_data[-8].text or '0.0',
                            student_data[-3].text or '0.0',
                            student_data[-1].text.upper()
                        ]

                else:
                    header = self.__browser.find_elements(
                        By.XPATH, '//div[@id="uOneCol"]/div/table[@class="table"]/tbody/tr/th'
                    )
                    lesson_data = [[i.text for i in header]]

                    student_data = self.__browser.find_elements(By.CLASS_NAME, 'tds')
                    student_name = student_data[0].text

                    lesson_data.append(
                            [student_name] +
                            [i.text for i in student_data[1:-1]] + [student_data[-1].text.upper()]
                    )
                    marks_data_details[lesson_name] = lesson_data

                    """ КРАТКАЯ ИНФОРМАЦИЯ """
                    marks_data['Дисциплина'] = ['Первичный', 'Вторичный', 'Итог']
                    marks_data[lesson_name] = [
                        student_data[-8].text or '0.0',
                        student_data[-3].text or '0.0',
                        student_data[-1].text.upper()
                    ]

            if lesson is None:
                for journal in range(len(journals)):
                    self.__browser.find_elements(By.LINK_TEXT, 'Журналы')[journal].click()

                    lessons = [i.text.strip() for i in self.__browser.find_elements(By.XPATH, '//td[@headers="DISC"]')]
                    self.__lessons[f'{journal + 1} журнал'] = lessons

                    new_tabs = []
                    for num in range(len(lessons)):
                        link = self.__browser.find_elements(
                            By.XPATH, '//td[@align="center"][@headers="KT_ALL"]/a[@title="Занятия/Оценки"]'
                        )[num]
                        new_tab = link.get_attribute('href')

                        self.__browser.execute_script(f'window.open("{new_tab}", "_blank")')
                        time.sleep(.75)
                        new_tabs.append(self.__browser.window_handles[-1])

                    for tab in new_tabs:
                        self.__browser.switch_to.window(tab)
                        extract_marks(lessons[new_tabs.index(tab)])
                        self.__browser.close()

                    self.__browser.switch_to.window(self.__browser.window_handles[0])
                    self.__browser.back()
            else:
                lesson = lesson.strip()

                if self.__lessons:
                    for key, value in self.__lessons.items():
                        desired_item = next((i for i in value if lesson in i), None)
                        if desired_item:
                            index_journal = list(self.__lessons.keys()).index(key)
                            index_lesson = value.index(desired_item) if isinstance(value, list) else 0

                            journals[index_journal].click()
                            marks = self.__browser.find_elements(
                                By.XPATH, '//td[@align="center"][@headers="KT_ALL"]/a[@title="Занятия/Оценки"]'
                            )
                            marks[index_lesson].click()

                            students = self.__browser.find_elements(
                                By.XPATH, '//div[@id="uOneCol"]/div/table[@class="table"]/tbody/tr'
                            )

                            for i in students:
                                extract_marks(desired_item, all_students=True, student=i)
                            break
                else:
                    for journal in range(len(journals)):
                        self.__browser.find_elements(By.LINK_TEXT, 'Журналы')[journal].click()

                        lessons = [
                            i.text.strip() for i in self.__browser.find_elements(By.XPATH, '//td[@headers="DISC"]')
                        ]

                        desired_item = next((i for i in lessons if lesson.upper() in i.upper()), None)
                        if desired_item:
                            marks = self.__browser.find_elements(
                                By.XPATH, '//td[@align="center"][@headers="KT_ALL"]/a[@title="Занятия/Оценки"]'
                            )
                            marks[lessons.index(desired_item)].click()

                            students = self.__browser.find_elements(
                                By.XPATH, '//div[@id="uOneCol"]/div/table[@class="table"]/tbody/tr'
                            )

                            for i in students:
                                extract_marks(desired_item, all_students=True, student=i)
                            break
                        self.__browser.back()

            if not marks_data:
                marks_data['ОШИБКА'] = ['Дисциплина не найдена'] * 3
                marks_data_details['ОШИБКА'] = ['Дисциплина не найдена'] * 3

            if not self.__groups:
                self.__check_groups()

            self.__main_page()
            return marks_data, marks_data_details if details else marks_data
        except Exception as e:
            self.__browser.quit()
            self.__open_browser()
            self.enter_login(self.__login, self.__password)
            return False, str(e)

    def get_groups(self, mode='check'):
        if mode not in ['check', 'get']:
            raise ValueError('Mode must be "check" or "get"')

        if mode == 'check':
            return getattr(self, f'_{self.__class__.__name__}__groups', None)
        elif mode == 'get':
            self.__check_groups()
            return self.__groups

    def my_rating(self, group):
        try:
            self.__check_main_page()
            self.__browser.find_element(By.LINK_TEXT, 'Успеваемость').click()

            rating_data = {}

            groups = self.__browser.find_elements(By.XPATH, '//table[@class="uReport uReportStandard"]/tbody/tr')
            for i in groups:
                if group == i.find_element(By.XPATH, './/td[@headers="GROUP_NAME"]').text:
                    link = i.find_elements(By.XPATH, './/td[@headers="RTG"]')
                    if link:
                        link[0].click()
                        break

            # Возможно когда-то тут будет ошибка, потому что сайт выглядит так, как будто тут может быть больше данных
            new_tabs = []
            group = self.__browser.find_element(By.XPATH, './/td[@headers="GROUP_NAME"]/a').get_attribute('href')
            university = self.__browser.find_element(By.XPATH, './/td[@headers="INST"]/a').get_attribute('href')

            for new_page in group, university:
                self.__browser.execute_script(f'window.open("{new_page}", "_blank")')
                time.sleep(.5)
                new_tabs.append(self.__browser.window_handles[-1])

            for tab in new_tabs:
                self.__browser.switch_to.window(tab)

                sections = self.__browser.find_elements(By.XPATH, '//section[@class="uRegion  clearfix"]')
                table_name = ''

                for section in sections:
                    new_section = section.find_element(By.XPATH, './/div[@class="uRegionHeading"]/h1/span')
                    if 'Рейтинг' in new_section.text:
                        sections = section
                        table_name = new_section.text
                        break

                if not next((i for i in sections.find_elements(By.XPATH, './/th[@id="ROWNUM"]')), None):
                    rating_data[table_name] = 'Данных не найдено'
                    self.__browser.close()
                    continue

                scores = [[
                    sections.find_element(By.XPATH, './/th[@id="ROWNUM"]').text,
                    sections.find_element(By.XPATH, './/th[@id="STUDNAME"]').text,
                    sections.find_element(By.XPATH, './/th[@id="STUDRATE"]').text,
                    sections.find_element(By.XPATH, './/th[@id="GROUP_NAME"]').text,
                ]]

                iam_found = False
                rows = sections.find_elements(By.XPATH, './/table[@class="uReport uReportStandard"]/tbody/tr')
                for row in rows:
                    if len(scores) <= 30 or not iam_found:
                        iam = next(
                            (i for i in row.find_elements(By.XPATH, './/td[@headers="STUDNAME"]/font')), None
                        )
                        if iam:
                            iam_found = True
                        else:
                            iam = row.find_element(By.XPATH, './/td[@headers="STUDNAME"]')

                        scores.append([
                            row.find_element(By.XPATH, './/td[@headers="ROWNUM"]').text,
                            iam.text,
                            row.find_element(By.XPATH, './/td[@headers="STUDRATE"]').text,
                            row.find_element(By.XPATH, './/td[@headers="GROUP_NAME"]').text,
                        ])

                rating_data[table_name] = scores
                self.__browser.close()

            self.__browser.switch_to.window(self.__browser.window_handles[0])
            self.__browser.back()

            for key, value in rating_data.items():
                if value == 'Данных не найдено':
                    elements = max(max(len(j) for i in rating_data.values() for j in i), 4)
                    not_found = [
                        ['Данных не найдено'] * elements,
                        ['ПУСТО'] * elements
                    ]
                    rating_data[key] = not_found

            self.__main_page()
            return rating_data
        except Exception as e:
            self.__browser.quit()
            self.__open_browser()
            self.enter_login(self.__login, self.__password)
            return False, str(e)

    def schedule(self):
        try:
            self.__check_main_page()
            self.__browser.find_element(By.LINK_TEXT, 'Расписание').click()

            schedule_data = {
                'Сегодня': self.__browser.find_element(By.XPATH, '//header[@id="uHeader"]/hgroup//div/ul/li/a').text
            }

            schedule_table = self.__browser.find_element(By.XPATH, '//table[@class="uReport uReportStandard"]')

            column_names = []
            for column in schedule_table.find_elements(By.XPATH, './/thead/tr/th'):
                if column.text not in column_names:
                    column_names.append(column.text)

            weeks = [i.text for i in schedule_table.find_elements(By.XPATH, './/tbody/tr[1]/td') if i.text]
            lessons_week1 = []
            lessons_week2 = []

            schedule = schedule_table.find_elements(By.XPATH, './/tbody/tr')
            for lesson in schedule[1:]:
                cells = lesson.find_elements(By.XPATH, './/td')
                lessons_week1.append([cells[i].text for i in range(len(column_names))])
                lessons_week2.append([cells[i].text for i in range(2)] +
                                     [cells[i].text for i in range(len(column_names), len(column_names) * 2 - 2)])

            schedule_data[weeks[0]] = [column_names] + lessons_week1
            schedule_data[weeks[1]] = [column_names] + lessons_week2

            self.__main_page()
            return schedule_data
        except Exception as e:
            self.__browser.quit()
            self.__open_browser()
            self.enter_login(self.__login, self.__password)
            return False, str(e)

    def logout(self):
        self.__browser.find_element(By.LINK_TEXT, 'Выход').click()

    def __check_available(self):
        error = next(
            (i for i in self.__browser.find_elements(By.XPATH, '//section[@class="uRegion uNoHeading uErrorRegion"]/div/p/strong')), None
        )
        return [False, error.text] if error else [True]

    def __check_groups(self):
        if not next(
                (i for i in self.__browser.find_elements(By.XPATH, '//header[@id="uHeader"]/nav/ul/li/a[@class="active"]') if i.text == 'Успеваемость'), None
        ):
            self.__browser.find_element(By.LINK_TEXT, 'Успеваемость').click()

        self.__groups = set(i.text for i in self.__browser.find_elements(By.XPATH, '//td[@headers="GROUP_NAME"]/span'))
        self.__groups = set(list(self.__groups)[::-1])

    def __check_main_page(self):
        if not next(
                (i for i in self.__browser.find_elements(By.XPATH, '//header[@id="uHeader"]/nav/ul/li/a[@class="active"]') if i.text == 'Информация'), None
        ):
            self.__main_page()

    def __main_page(self):
        self.__browser.find_element(By.LINK_TEXT, 'Информация').click()

    def quit(self):
        self.__browser.quit()
