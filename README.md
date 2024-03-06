# Reservoirs Web
Веб-версия проекта [reservoirs_bot](https://github.com/hlystovea/reservoirs_bot)

![Static Badge](https://img.shields.io/badge/hlystovea-reservoirs_web-reservoirs_web)
![GitHub top language](https://img.shields.io/github/languages/top/hlystovea/reservoirs_web)
![GitHub](https://img.shields.io/github/license/hlystovea/reservoirs_web)
![GitHub Repo stars](https://img.shields.io/github/stars/hlystovea/reservoirs_web)
![GitHub issues](https://img.shields.io/github/issues/hlystovea/reservoirs_web)

[Сайт](https://reservoirs.hlystovea.ru) отображает в виде графиков информацию о гидрологической обстановке на крупнейших водохранилищах ГЭС России.

![Водохранилища ГЭС России!](https://ucarecdn.com/bd418df3-7058-4759-8064-ff6c055adabb/-/preview/794x720/ "Водохранилища ГЭС России")

## Установка (Linux)
У вас должен быть установлен [Docker Compose](https://docs.docker.com/compose/)

1. Клонирование репозитория 

```git clone https://github.com/hlystovea/reservoirs_web.git```

2. Переход в директорию reservoirs_web

```cd reservoirs_web```

3. Создание файла с переменными окружения

```cp env.example .env```

4. Заполнение файла .env своими переменными

```nano .env```

6. Запуск проекта

```sudo docker compose up -d```

## Документация
Пользовательскую документацию можно получить по [этой ссылке](./docs/ru/index.md).

[Релизы программы]: https://github.com/hlystovea/reservoirs_web/releases

## Поддержка
Если у вас возникли сложности или вопросы по использованию проекта, создайте 
[обсуждение](https://github.com/hlystovea/reservoirs_web/issues/new/choose) в данном репозитории или напишите в [Telegram](https://t.me/hlystovea).