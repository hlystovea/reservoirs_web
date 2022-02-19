from db.schemas import Reservoir


def reservoir_info(reservoir: Reservoir):
    return (
        f'*{reservoir.name} водохранилище:*\n'
        f'НПУ {reservoir.normal_level} м\n'
        f'ФПУ {reservoir.force_level} м\n'
        f'УМО {reservoir.dead_level} м\n'
    )
