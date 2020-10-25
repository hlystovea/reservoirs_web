import matplotlib.pyplot as plt


def plot(res, days):
    x = []
    y = []
    m = int(res)
    with open('level.csv', 'r') as f:
        str = f.readlines()
    n = len(str) - 1
    if int(days) > (len(str) - 1):
        n = len(str) - 1
    else:
        n = int(days)
    
    for i in range((-1*n), 0, 1):
        str_split = str[i].split(';')
        x.append(str_split[0])
        y.append(float(str_split[m].replace(',', '.')))

    res_name = {
        1: 'Саяно-Шушенское',
        2: 'Майнское',
        3: 'Красноярское',
        4: 'Братское',
        5: 'Усть-Илимское',
        6: 'Богучанское'
    }
    
    plt.figure(figsize=(6, 4))
    plt.plot(x, y)
    #graph2 = plt.plot(x, 539, 'r+')
    #text1 = plt.text(x[int(len(x)/2)], y[int(len(y)*0.25)], f'{reservoir} vdhr')
    text = f'{res_name[m]} водохранилище'
    plt.title(text)
    plt.grid(True, 'major', 'both')   # линии вспомогательной сетки
    plt.legend(['УВБ (м)'])
    plt.tick_params('x', labelrotation=20, labelsize=8)
    plt.xticks(x)
    name = 'pic'
    fmt = 'png'
    plt.savefig('{}.{}'.format(name, fmt))


plot(1, 12)
