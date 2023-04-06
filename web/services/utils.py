from dateutil.parser import parserinfo


class ParserInfo(parserinfo):
    MONTHS = [
        ('Jan', 'января', 'January'),
        ('Feb', 'февраля', 'February'),
        ('Mar', 'марта', 'March'),
        ('Apr', 'апреля', 'April'),
        ('May', 'мая', 'May'),
        ('Jun', 'июня', 'June'),
        ('Jul', 'июля', 'July'),
        ('Aug', 'августа', 'August'),
        ('Sep', 'сентября', 'Sept', 'September'),
        ('Oct', 'октября', 'October'),
        ('Nov', 'ноября', 'November'),
        ('Dec', 'декабря', 'December'),
    ]
    JUMP = [
        ' ', '.', ',', ';', '-', '/', "'",
        'at', 'on', 'and', 'ad', 'm', 't',
        'of', 'st', 'nd', 'rd', 'th', 'г',
    ]
    WEEKDAYS = [
        ('Mon', 'понедельник', 'Monday'),
        ('Tue', 'вторник', 'Tuesday'),
        ('Wed', 'среда', 'Wednesday'),
        ('Thu', 'четверг', 'Thursday'),
        ('Fri', 'пятница', 'Friday'),
        ('Sat', 'суббота', 'Saturday'),
        ('Sun', 'воскресенье', 'Sunday')
    ]


parser_info = ParserInfo(True, True)
