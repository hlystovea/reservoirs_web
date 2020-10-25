from bs4 import BeautifulSoup
import requests
import re
import time

def parcing_bwu():
    # парсинг сайта Енисейского БВУ
    url = 'http://enbvu.ru/i03_deyatelnost/i03.07_vdho.php'

    page = requests.get(url)

    soup = BeautifulSoup(page.text, 'html.parser')
    data_level = soup.find_all(string=re.compile('верхний бьеф'))
    data_date = soup.find_all(string=re.compile('Изменено:'))

    # добавление данных об уровнях водохранилищ в файл
    try:
        # чтение последней даты в файле
        f = open('level.csv', 'r')
        last_date = f.readlines()[-1].split(';')[0]
        f.close()

        for i in range(0, 5): # итерации по 5 строкам парсинга
            date = data_date[i].split()[1]
            if date > last_date: # проверка "свежести" данных
                f_str = date
                for n in range(0, 6): # подготовка строки для записи в файл
                    level = data_level[i*6+n].split()[3]
                    f_str = f_str + ';' + level
                f_str = f_str + '\n' 
                f = open('level.csv', 'a')
                f.write(f_str) # запись в файл
        f.close()

    except:
        print('Ошибка в содержании файла или файл не найден')