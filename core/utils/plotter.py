import io
from typing import List

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


ylabel = {
    'level': 'Высота над уровнем моря, м',
    'inflow': 'Q, м\u00b3/с',
    'outflow': 'Q, м\u00b3/с',
    'spillway': 'Q, м\u00b3/с',
}

legend = {
    'level': 'УВБ (м)',
    'inflow': 'Приток (м\u00b3/c)',
    'outflow': 'Средний сброс (м\u00b3/c)',
    'spillway': 'Холостой сброс (м\u00b3/с)',
}


async def plotter(
    x: List[float], y: List[float], title: str, command: str
) -> io.BytesIO:
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot(x, y, color=(0, 0.4, 0.9, 0.7), linewidth=0.8)

    ax.legend([legend.get(command)], fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(ylabel.get(command), fontsize=9)

    ax.grid(True, 'major', 'both')
    ax.xaxis.set_major_locator(
        MultipleLocator(len(x) // 6 if len(x) > 6 else 1)
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))

    ax.tick_params('x', labelrotation=20, labelsize=8)
    ax.tick_params('y', labelrotation=0, labelsize=8)

    pic = io.BytesIO()
    plt.savefig(pic, format='png')
    plt.close
    pic.seek(0)
    return pic


def save_csv(reservoir, timeperiod):
    # Формируем списки с координатами
    coordinates = reservoir.get_levels(timeperiod)
    x = [value[0] for value in coordinates]
    y = [value[1] for value in coordinates]
    record = ''
    for i in range(len(x)):
        record += str(x[i])
        record += ';' + str(y[i])
        record += '\n'
    f = open('level.csv', 'w')
    f.write(record)
    f.close()
