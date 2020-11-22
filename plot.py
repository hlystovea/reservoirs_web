import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import sqlite3

from datetime import datetime


# Вспомогательный словарь с параметрами водохранилищ: ФПУ, НПУ, УМО
res_param = {
    1: ('Саяно-Шушенское водохранилище', 540.0, 539.0, 500.0),
    2: ('Майнское водохранилище', 326.7, 324.0, 319.0),
    3: ('Красноярское водохранилище', 245.0, 243.0, 225.0),
    4: ('Братское водохранилище', 401.79, 401.73, 394.73),
    5: ('Усть-Илимское водохранилище', 296.6, 296.0, 294.5),
    6: ('Богучанское водохранилище', 209.5, 208.0, 207.0),
}


def plot(res, time1, time2):
    x = []
    y = []
    conn = sqlite3.connect('levels.sqlite')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM uvb WHERE date BETWEEN :time1 AND :time2 ORDER BY date",
        {"time1": time1, "time2": time2}
        )
    sample = cursor.fetchall()

    # Формируем списки с координатами
    x = [value[0] for value in sample]
    y = [value[res] for value in sample]
    dates = [datetime.strptime(d, '%Y-%m-%d') for d in x]

    # Определяем уровни ФПУ, НПУ, УМО
    FPU = f'{res_param[res][1]} м'
    NPU = f'{res_param[res][2]} м'
    UMO = f'{res_param[res][3]} м'

    # Определяем цену делений оси x
    major_ticker = 1
    if len(x) > 5:
        major_ticker = int(len(x)/5)

    # Построение графика
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot(dates, y, color=(0, 0.4, 0.9, 0.7), linewidth=0.8)
    ax.set_title(
        f'{res_param[res][0]}\nФПУ={FPU}, НПУ={NPU}, УМО={UMO}',
        fontsize=10
        )
    ax.set_ylabel('Высота над уровнем моря, м', fontsize=9)
    ax.grid(True, 'major', 'both')
    ax.legend(['УВБ (м)'], fontsize=9)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(major_ticker))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
    ax.tick_params('x', labelrotation=20, labelsize=8)
    ax.tick_params('y', labelsize=8)

    # Сохранение файла
    name = 'pic'
    fmt = 'png'
    plt.savefig('{}.{}'.format(name, fmt))

    try:
        date1 = datetime.strptime(sample[0][0], '%Y-%m-%d')
        date1 = date1.strftime('%d.%m.%Y')
        date2 = datetime.strptime(sample[-1][0], '%Y-%m-%d')
        date2 = date2.strftime('%d.%m.%Y')
        text = f'График за период с {date1} по {date2}'
        result = 'succed'
    except IndexError:
        text = 'Нет данных за указанный период времени'
        result = 'failed'
    finally:
        return (text, result)


if __name__ == '__main__':
    plot(1, '2020-01-01', '2020-12-31')
