from db.schemas import Reservoir


def reservoir_info(reservoir: Reservoir):
    return (
        f'*{reservoir.name} водохранилище:*\n'
        f'НПУ {reservoir.normal_level} м\n'
        f'ФПУ {reservoir.force_level} м\n'
        f'УМО {reservoir.dead_level} м\n'
        f'Полезный объем {reservoir.useful_volume + " куб.км" if reservoir.useful_volume else "н/д"}\n'  # noqa (E501)
        f'Полный объем {reservoir.full_volume + " куб.км" if reservoir.full_volume else "н/д"}\n'  # noqa (E501)
        f'Площадь {reservoir.area + " кв.км" if reservoir.area else "н/д"}\n'
    )
