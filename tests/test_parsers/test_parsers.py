import pytest


from reservoirs.models import Reservoir
from services.parsers import RushydroParser


@pytest.mark.parametrize(
    'name',
    [
        'Богучанская',
        'Братская',
        'Бурейская',
        'Вилюйская',
        'Волжская',
        'Воткинская',
        'Жигулевская',
        'Зейская',
        'Ирганайская',
        'Иркутская',
        'Камская',
        'Колымская',
        'Майнская',
        'Нижегородская',
        'Нижне-Бурейская',
        'Нижнекамская',
        'Новосибирская',
        'Рыбинская',
        'Саратовская',
        'Саяно-Шушенская',
        'Угличская',
        'Усть-Илимская',
        'Усть-Среднеканская',
        'Чебоксарская',
        'Чиркейская',
    ]
)
def test_rushydro_parser(name, rushydro_informer):
    reservoir = Reservoir(station_name=name, name=name)
    parser = RushydroParser()
    assert parser.parse(page=rushydro_informer, reservoir=reservoir)
