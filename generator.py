import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import string
from bs4 import BeautifulSoup
from ics import Calendar, Event

if len(sys.argv) == 1:
    print(f"Jak używać: python generator.py [url]|[url,nazwa_grupy] ([url2]|[url2,nazwa_grupy], ...) ")
    print(f"  [url] - link do strony kursu na UO UW, np. https://www.uo.uw.edu.pl/kurs/12345")
    print(f"  [group_name] - numer grupy, jeśli jest więcej niż jedna, np. K/0805/29 . Domyślnie brana jest pierwsza")
    sys.exit()

print("UO UW Generator Kalendarzy 0.1 by Marcin Stefański; m_stefanski@icloud.com")

for task in sys.argv[1:]:
    print(f"Przetwarzanie {task}")

    tokens = task.split(",")
    if len(tokens) == 2:
        url = tokens[0]
        searched_group = tokens[1]
    elif len(tokens) == 1:
        url = tokens[0]
        searched_group = None
    else:
        print(f"Błąd podczas parsowania {task}. Pomijanie kursu.")
        continue

    page = requests.get(url)
    if page.status_code != 200:
        print(f"Nie udało się pobrać strony {url}. Pomijanie kursu.")
        continue
    html = page.content
    
    soup = BeautifulSoup(html, 'html.parser')

    course_name = soup.find_all("div", class_="modal-body")[0].text.strip()
    print(f"Znaleziono kurs: {course_name}")

    timetables = soup.find_all("div", class_="courses-timetable")

    if len(timetables) == 0:
        print(f"Nie znaleziono tabeli z terminami zajęć. Pomijanie kursu.")
        continue
    
    timetable = timetables[0]
    timetable_index = None

    if searched_group == None:
        print("Nie podano nazwy grupy, używam pierwszej")
        timetable_index = 0
    else:
        print(f"Szukam grupy {searched_group}")
        group_names = timetable.find_all("h4")
        for group_index, group_name in enumerate(group_names):
            if searched_group in group_name.text:
                timetable_index = group_index
                break

    if timetable_index is None:
        print(f"Nie znaleziono podanej grupy. Pomijanie kursu.")
        continue

    used_group = timetable.find_all("h4")[timetable_index].text
    plan_table = timetable.find_all("table")[timetable_index]
    print(f"Generowanie wydarzeń: {used_group}")

    c = Calendar()

    for row in plan_table.find('tbody').find_all('tr'):
        lesson = row.find_all('td')[0].text 
        date = row.find_all('td')[1].find_all('b')[0].text.partition('\n')[0].strip()
        hour_start = row.find_all('td')[2].text
        hour_end = row.find_all('td')[3].text

        start_datetime = datetime.strptime(f"{date} {hour_start}", "%d.%m.%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Warsaw"))
        end_datetime = datetime.strptime(f"{date} {hour_end}", "%d.%m.%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Warsaw"))

        converted_date = datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")
        e = Event()
        e.name = f"{course_name}, {used_group}, zajęcia {lesson}"
        e.begin = start_datetime.isoformat()
        e.end = end_datetime.isoformat()
        e.url = url
        print(f"Zajęcia {lesson} - {converted_date}, {hour_start}-{hour_end}")
        c.events.add(e)

    
    valid_chars = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ-–_.,() %s%s" % (string.ascii_letters, string.digits)
    ics_filename = f"{course_name}, {used_group.replace('/', '-')}.ics"
    sanitized_ics_filename = ''.join(c for c in ics_filename if c in valid_chars)

    print(f"Zapisywanie: {sanitized_ics_filename}")
    with open(sanitized_ics_filename, 'w', encoding="utf-8") as output_file:
        output_file.writelines(c.serialize_iter())

print("Zakończono.")
