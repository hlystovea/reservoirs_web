import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from datetime import datetime


def plot(res, days):
    x = []
    y = []
    m = int(res) # номер водохранилища
    with open('/tmp/level.csv', 'r') as f:
        str = f.readlines()

    if int(days) > (len(str) - 1): # сравнение кол-ва дней с кол-ом записей
        n = len(str) - 1 # записей мало, показываем всё что есть
    else:
        n = int(days) # записей достаточно, показываем по запросу
    
    # формируем списки с координатами
    for i in range((-1*n), 0, 1):
        str_split = str[i].split(';')
        x.append(str_split[0])
        y.append(float(str_split[m].replace(',', '.')))

    # приводим список x к формату strtime
    dates = [datetime.strptime(d, '%d.%m.%Y') for d in x]

    # вспомогательный словарь с параметрами водохранилищ
    res_param = {
        1: ['Саяно-Шушенское', 540, 539, 500],
        2: ['Майнское', 326.7, 324.0, 319.0],
        3: ['Красноярское', 245, 243, 225],
        4: ['Братское', 401.79, 401.73, 394.73],
        5: ['Усть-Илимское', 296.6, 296.0, 294.5],
        6: ['Богучанское', 209.5, 207.0, 207.0],
    }
    # определяем уровни ФПУ, НПУ, УМО
    FPU = f'{res_param[m][1]} м'
    NPU = f'{res_param[m][2]} м'
    UMO = f'{res_param[m][3]} м'

    # определяем цену делений оси x
    major_ticker = 1
    if n > 6:
        major_ticker = int(n/6)

    # построение графика
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot(dates, y, color=(0, 0.4, 0.9, 0.7), linewidth=0.8)
    ax.set_title(f'{res_param[m][0]} водохранилище\nФПУ={FPU}, НПУ={NPU}, УМО={UMO}', fontsize=10)
    ax.set_ylabel('Высота над уровнем моря, м', fontsize=9)
    ax.grid(True, 'major', 'both')
    ax.legend([f'УВБ (м)'], fontsize=9)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(major_ticker))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
    ax.tick_params('x', labelrotation=20, labelsize=8)
    ax.tick_params('y', labelsize=8)
    
    # сохранение файла
    name = 'pic'
    fmt = 'png'
    plt.savefig('{}.{}'.format(name, fmt))


plot(5, 30)
