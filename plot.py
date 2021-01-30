import io
import sqlite3
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Вспомогательный словарь с параметрами водохранилищ: ФПУ, НПУ, УМО
res_param = {
    1: ('Саяно-Шушенское водохранилище', 540.0, 539.0, 500.0),
    2: ('Майнское водохранилище', 326.7, 324.0, 319.0),
    3: ('Красноярское водохранилище', 245.0, 243.0, 225.0),
    4: ('Братское водохранилище', 401.79, 401.73, 394.73),
    5: ('Усть-Илимское водохранилище', 296.6, 296.0, 294.5),
    6: ('Богучанское водохранилище', 209.5, 208.0, 207.0),
}

column_name = {
    1: 'sayany',
    2: 'mayna',
    3: 'kras',
    4: 'bratsk',
    5: 'ilimsk',
    6: 'boguchany',
}


def plot(res, date1, date2):
    conn = sqlite3.connect('levels.sqlite')
    cursor = conn.cursor()
    sql_query = f'SELECT date, {column_name[res]} FROM uvb WHERE {column_name[res]} IS NOT NULL AND date BETWEEN :date1 AND :date2 ORDER BY date'
    cursor.execute(sql_query, {'date1': date1, 'date2': date2})
    sample = cursor.fetchall()

    # Формируем списки с координатами
    x = [value[0] for value in sample]
    y = [value[1] for value in sample]
    dates = [datetime.strptime(d, '%Y-%m-%d') for d in x]

    # Определяем уровни ФПУ, НПУ, УМО
    FPU = f'{res_param[res][1]} м'
    NPU = f'{res_param[res][2]} м'
    UMO = f'{res_param[res][3]} м'

    # Определяем цену делений оси x
    major_ticker = 1
    try:
        d = dates[-1] - dates[0]
        if d.days > 7:
            major_ticker = int(d.days/7)
    except IndexError:
        pass

    # Построение графика
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot(dates, y, color=(0, 0.4, 0.9, 0.7), linewidth=0.8)
    ax.set_title(
        f'{res_param[res][0]}\nФПУ={FPU}, НПУ={NPU}, УМО={UMO}',
        fontsize=10,
        )
    ax.set_ylabel('Высота над уровнем моря, м', fontsize=9)
    ax.grid(True, 'major', 'both')
    ax.legend(['УВБ (м)'], fontsize=9)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(major_ticker))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
    ax.tick_params('x', labelrotation=20, labelsize=8)
    ax.tick_params('y', labelsize=8)

    # Сохранение файла
    pic = io.BytesIO()
    plt.savefig(pic, format='png')
    plt.close
    pic.seek(0)

    save_csv(x, y)

    try:
        date1 = datetime.strptime(sample[0][0], '%Y-%m-%d')
        date1 = date1.strftime('%d.%m.%Y')
        date2 = datetime.strptime(sample[-1][0], '%Y-%m-%d')
        date2 = date2.strftime('%d.%m.%Y')
        text = f'График за период с {date1} по {date2}'
        is_success = True
    except IndexError:
        text = 'Нет данных за указанный период времени'
        is_success = False
    finally:
        return (pic, text, is_success)


def save_csv(x, y):
    record = ''
    for d in range(len(x)):
        record += x[d]
        record += ';' + str(y[d])
        record += '\n'
    f = open('level.csv', 'w')
    f.write(record)
    f.close()


if __name__ == '__main__':
    plot(3, '2014-05-12', '2020-12-31')
