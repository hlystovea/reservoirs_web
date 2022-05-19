from db.models import ReservoirModel


def reservoir_info(reservoir: ReservoirModel):
    return (
        f'*{reservoir.name} водохранилище:*\n'
        f'НПУ {reservoir.normal_level} м\n'
        f'ФПУ {reservoir.force_level} м\n'
        f'УМО {reservoir.dead_level} м\n'
        f'Полезный объем {str(reservoir.useful_volume) + " куб.км" if reservoir.useful_volume else "н/д"}\n'  # noqa (E501)
        f'Полный объем {str(reservoir.full_volume) + " куб.км" if reservoir.full_volume else "н/д"}\n'  # noqa (E501)
        f'Площадь {str(reservoir.area) + " кв.км" if reservoir.area else "н/д"}\n'  # noqa (E501)
        f'Максимальная глубина {str(reservoir.max_depth) + " м" if reservoir.max_depth else "н/д"}\n'  # noqa (E501)
    )
