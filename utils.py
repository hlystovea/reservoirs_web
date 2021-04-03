import datetime as dt
import io
import sqlite3
import time

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ONE_DAY = 86400

# Вспомогательный словарь с параметрами водохранилищ: ФПУ, НПУ, УМО
res_param = {
    'sayany': ('Саяно-Шушенское водохранилище', 540.0, 539.0, 500.0),
    'mayna': ('Майнское водохранилище', 326.7, 324.0, 319.0),
    'kras': ('Красноярское водохранилище', 245.0, 243.0, 225.0),
    'bratsk': ('Братское водохранилище', 401.79, 401.73, 394.73),
    'ilimsk': ('Усть-Илимское водохранилище', 296.6, 296.0, 294.5),
    'boguchany': ('Богучанское водохранилище', 209.5, 208.0, 207.0),
}

column_name = {
    1: 'sayany',
    2: 'mayna',
    3: 'kras',
    4: 'bratsk',
    5: 'ilimsk',
    6: 'boguchany',
}

class TimePeriod():
    def __init__(self, date1, date2=None, date_format='%d.%m.%Y'):
        date1 = dt.datetime.strptime(date1, date_format)
        if date2 is not None:
            date2 = dt.datetime.strptime(date2, date_format)
        else:
            date2 = dt.datetime.today()
        if date1 < date2:
            self.date1 = date1.timestamp()
            self.date2 = date2.timestamp()
        else:
            self.date1 = date2.timestamp()
            self.date2 = date1.timestamp()

    def get_statistics(self):
        timestamp1 = self.date1
        timestamp2 = self.date2 + ONE_DAY
        connect = sqlite3.connect('levels.sqlite')
        cursor = connect.cursor()
        sql_query = 'SELECT reservoir, COUNT(timestamp) FROM statistic WHERE timestamp BETWEEN :timestamp1 AND :timestamp2 GROUP BY reservoir'
        cursor.execute(sql_query, {'timestamp1': timestamp1, 'timestamp2': timestamp2})
        data = cursor.fetchall()
        cursor.close()
        connect.close()
        return data
    
    @staticmethod
    def timestamp_to_format(timestamp, format='%d.%m.%Y'):
        return dt.datetime.fromtimestamp(timestamp).strftime(format)

    def __str__(self) -> str:
        return f'Период с {self.date1} по {self.date2}'


class Reservoir():
    def __init__(self, name):
        self.name = name

    def add_statistic(self):
        self.time = int(time.time())
        connect = sqlite3.connect('levels.sqlite')
        cursor = connect.cursor()
        sql_query = 'INSERT INTO statistic VALUES (?, ?)'
        cursor.execute(sql_query, (self.time, self.name))
        connect.commit()
        cursor.close()
        connect.close()

    def get_statistic(self, period):
        timestamp1 = period.date1
        timestamp2 = period.date2 + ONE_DAY
        connect = sqlite3.connect('levels.sqlite')
        cursor = connect.cursor()
        sql_query = 'SELECT timestamp FROM statistic WHERE reservoir=:name AND timestamp BETWEEN :timestamp1 AND :timestamp2 ORDER BY timestamp'
        cursor.execute(sql_query, {'name': self.name, 'timestamp1': timestamp1, 'timestamp2': timestamp2})
        data = cursor.fetchall()
        cursor.close()
        connect.close()
        return data

    def get_levels(self, period):
        date1 = period.date1
        date2 = period.date2
        connect = sqlite3.connect('levels.sqlite')
        cursor = connect.cursor()
        sql_query = f'SELECT date, {self.name} FROM uvb WHERE {self.name} IS NOT NULL AND date BETWEEN :date1 AND :date2 ORDER BY date'
        cursor.execute(sql_query, {'date1': date1, 'date2': date2})
        coordinates = cursor.fetchall()
        cursor.close()
        connect.close()
        return coordinates

    def get_outflows(self, period):
        date1 = period.date1
        date2 = period.date2
        connect = sqlite3.connect('levels.sqlite')
        cursor = connect.cursor()
        sql_query = f'SELECT date, {self.name} FROM outflow WHERE {self.name} IS NOT NULL AND date BETWEEN :date1 AND :date2 ORDER BY date'
        cursor.execute(sql_query, {'date1': date1, 'date2': date2})
        coordinates = cursor.fetchall()
        cursor.close()
        connect.close()
        return coordinates

    def get_inflows(self, period):
        date1 = period.date1
        date2 = period.date2
        connect = sqlite3.connect('levels.sqlite')
        cursor = connect.cursor()
        sql_query = f'SELECT date, {self.name} FROM inflow WHERE {self.name} IS NOT NULL AND date BETWEEN :date1 AND :date2 ORDER BY date'
        cursor.execute(sql_query, {'date1': date1, 'date2': date2})
        coordinates = cursor.fetchall()
        cursor.close()
        connect.close()
        return coordinates

    def __str__(self):
        return self.name


class Plotter():
    @staticmethod
    def plot_levels(reservoir, timeperiod):
        # Формируем списки с координатами
        coordinates = reservoir.get_levels(timeperiod)
        x = [value[0] for value in coordinates]
        y = [value[1] for value in coordinates]
        dates = [dt.datetime.fromtimestamp(d) for d in x]

        # Определяем уровни ФПУ, НПУ, УМО
        FPU = f'{res_param[reservoir.name][1]} м'
        NPU = f'{res_param[reservoir.name][2]} м'
        UMO = f'{res_param[reservoir.name][3]} м'

        # Построение графика
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.plot(dates, y, color=(0, 0.4, 0.9, 0.7), linewidth=0.8)
        ax.set_title(
            f'{res_param[reservoir.name][0]}\nФПУ={FPU}, НПУ={NPU}, УМО={UMO}',
            fontsize=10,
        )
        ax.set_ylabel('Высота над уровнем моря, м', fontsize=9)
        ax.grid(True, 'major', 'both')
        ax.legend(['УВБ (м)'], fontsize=9)
        locator = mdates.AutoDateLocator(
            minticks=7,
            maxticks=12,
            interval_multiples=False,
        )
        formatter = mdates.DateFormatter('%d.%m.%Y')
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.tick_params('x', labelrotation=20, labelsize=8)
        ax.tick_params('y', labelsize=8)

        # Сохранение файла
        pic = io.BytesIO()
        plt.savefig(pic, format='png')
        plt.close
        pic.seek(0)

        try:
            date1 = dt.datetime.fromtimestamp(coordinates[0][0])
            date1 = date1.strftime('%d.%m.%Y')
            date2 = dt.datetime.fromtimestamp(coordinates[-1][0])
            date2 = date2.strftime('%d.%m.%Y')
            text = f'График за период с {date1} по {date2}'
            is_success = True
        except IndexError:
            text = 'Нет данных за указанный период времени'
            is_success = False
        finally:
            return (pic, text, is_success)

    @staticmethod
    def save_csv(reservoir, timeperiod):
        # Формируем списки с координатами
        coordinates = reservoir.get_levels(timeperiod)
        x = [value[0] for value in coordinates]
        y = [value[1] for value in coordinates]
        dates = [TimePeriod.timestamp_to_format(date) for date in x]

        record = ''
        for i in range(len(dates)):
            record += str(dates[i])
            record += ';' + str(y[i])
            record += '\n'
        f = open('level.csv', 'w')
        f.write(record)
        f.close()

    @staticmethod
    def plot_statistics(timeperiod):
        # Формируем списки с координатами
        data = timeperiod.get_statistics()
        names = [value[0] for value in data]
        values = [value[1] for value in data]

        # Построение графика
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.bar(names, values, color=(0, 0.4, 0.9, 0.7))
        ax.set_title(
            f'Статистика запросов',
            fontsize=10,
            )
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.set_ylabel('Количество', fontsize=9)
        ax.tick_params('x', labelsize=8)
        ax.tick_params('y', labelsize=8)

        # Сохранение файла
        pic = io.BytesIO()
        plt.savefig(pic, format='png')
        plt.close
        pic.seek(0)

        return pic

    @staticmethod
    def plot_outflows(reservoir, timeperiod):
        # Формируем списки с координатами
        coordinates = reservoir.get_outflows(timeperiod)
        x = [value[0] for value in coordinates]
        y = [value[1] for value in coordinates]
        dates = [dt.datetime.fromtimestamp(d) for d in x]
        print(y)

        # Построение графика
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.plot(dates, y, color=(0, 0.4, 0.9, 0.7), linewidth=0.8)
        ax.set_title(f'{res_param[reservoir.name][0]}', fontsize=10)
        ax.set_ylabel('Q, м\u00b3/с', fontsize=9)
        ax.grid(True, 'major', 'both')
        ax.legend(['Сброс (м\u00b3/c)'], fontsize=9)
        locator = mdates.AutoDateLocator(
            minticks=7,
            maxticks=12,
            interval_multiples=False,
        )
        formatter = mdates.DateFormatter('%d.%m.%Y')
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.tick_params('x', labelrotation=20, labelsize=8)
        ax.tick_params('y', labelsize=8)

        # Сохранение файла
        pic = io.BytesIO()
        plt.savefig(pic, format='png')
        plt.close
        pic.seek(0)

        try:
            date1 = dt.datetime.fromtimestamp(coordinates[0][0])
            date1 = date1.strftime('%d.%m.%Y')
            date2 = dt.datetime.fromtimestamp(coordinates[-1][0])
            date2 = date2.strftime('%d.%m.%Y')
            text = f'График за период с {date1} по {date2}'
            is_success = True
        except IndexError:
            text = 'Нет данных за указанный период времени'
            is_success = False
        finally:
            return (pic, text, is_success)

    @staticmethod
    def plot_inflows(reservoir, timeperiod):
        # Формируем списки с координатами
        coordinates = reservoir.get_inflows(timeperiod)
        x = [value[0] for value in coordinates]
        y = [value[1] for value in coordinates]
        dates = [dt.datetime.fromtimestamp(d) for d in x]
        print(y)

        # Построение графика
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        ax.plot(dates, y, color=(0, 0.4, 0.9, 0.7), linewidth=0.8)
        ax.set_title(f'{res_param[reservoir.name][0]}', fontsize=10)
        ax.set_ylabel('Q, м\u00b3/с', fontsize=9)
        ax.grid(True, 'major', 'both')
        ax.legend(['Приток (м\u00b3/c)'], fontsize=9)
        locator = mdates.AutoDateLocator(
            minticks=7,
            maxticks=12,
            interval_multiples=False,
        )
        formatter = mdates.DateFormatter('%d.%m.%Y')
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.tick_params('x', labelrotation=20, labelsize=8)
        ax.tick_params('y', labelsize=8)

        # Сохранение файла
        pic = io.BytesIO()
        plt.savefig(pic, format='png')
        plt.close
        pic.seek(0)

        try:
            date1 = dt.datetime.fromtimestamp(coordinates[0][0])
            date1 = date1.strftime('%d.%m.%Y')
            date2 = dt.datetime.fromtimestamp(coordinates[-1][0])
            date2 = date2.strftime('%d.%m.%Y')
            text = f'График за период с {date1} по {date2}'
            is_success = True
        except IndexError:
            text = 'Нет данных за указанный период времени'
            is_success = False
        finally:
            return (pic, text, is_success)

if __name__ == '__main__':
    period = TimePeriod(date1='01.03.2021')
    res = Reservoir(name='sayany')
    Plotter.plot_inflows(res, period)
    Plotter.plot_levels(res, period)
    Plotter.save_csv(res, period)
    Plotter.plot_statistics(period)
