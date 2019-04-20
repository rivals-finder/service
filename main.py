import requests
from flask import Flask, jsonify

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/mock')
def mocks():
    """
    Метод для MOCK-данных
    :return: MOCK
    """
    news_list = [
        {
            'id': 1,
            'title': "UNIX родился!",
            'text': 'Наша жизнь кардинально изменится',
            'date': '01.01.1980',
            'link': ''
        },
        {
            'id': 2,
            'title': "Офигенная новость",
            'text': 'Ура! У меня получилось сделать моки',
            'date': '19.04.2019',
            'link': ''
        },
    ]

    return jsonify(items=news_list)


@app.route('/')
@app.route('/index')
def hello():
    """ hello world
    """
    return 'hello world'


# Констранта с идентификатором группы, из которой мы будем получать новости
GROUP_ID = '8773c70e-34b6-4532-894a-45986357678c'


class NewsInfoParser:
    """ Класс, забирающий из информации с облака только необходимое для отрисовки
    """
    # Константа для формирования ссылки
    LINK_PREFIX = 'https://fix-online.sbis.ru/news/{}'

    # TODO: Написать код, который из данных с облака забирает только необходимое
    # 1) безопасно забирает данные, делая из html-верстки plain-text
    # 2) собирает из списка данных JSON объект в формате оговоренного API
    # 3) Ссылка клеится как LINK_PREFIX.format(news_guid), где news_guid - из поля Object
    pass


class Platform:

    session = requests.Session()

    # Соответствие типов описания и типов rpc-вызовов
    type_conformity = {
        'int': 'Число целое',
        'int[]': {
            'n': "Массив",
            't': "Число целое"
        },
        'string': 'Строка',
        'string[]': {
            'n': "Массив",
            't': "Строка"
        },
        'bool': 'Логическое',
        'uuid': 'UUID',
        'uuid[]': {
            'n': "Массив",
            't': "UUID"
        },
        'date-time': 'Дата и время',
        'date': 'Дата',
        'time': 'Время'
    }

    def __init__(self, login='Демо_тензор', password='Демо123'):
        """ Залогинимся под системным пользователем для обращения к сервису
        """
        self.rpc(
            'САП.АутентифицироватьРасш',
            {'login': login, 'password': password},
            service='auth/service'
        )

    def rpc(self, method, params, service='service'):
        """
        Реализация Remote Procedure Call
        :param method: Имя метода
        :param params: Параметры
        :param service: Сервис, на который производится вызов (service по умолчанию)
        :return: response result
        """

        response = self.session.post(
            'https://fix-online.sbis.ru/{}/'.format(service),
            headers={"Content-Type": "application/json; charset=utf-8", "Accept": "application/json"},
            json={"jsonrpc": "2.0", "protocol": 4, "method": method, "params": params}
        ).json()

        # TODO: Нужна обработка результата, на случаи отказа ответа от облака и других исключений
        # Результат обернуть в вызов self.parse_result и вернуть
        return self.parse_result(response.result)

    def record(self, list_with_info):
        """
        Метод для формирование Record'а из данных в формате
        :param list_with_info: лист словарей формата [{value: (name, type)}, ..]
        :return: rpc-record в формате
        """
        scheme_list, value_list = [], []
        for item in list_with_info:
            item = dict(item)
            value, scheme_info = item.popitem()
            value_list.append(value)
            scheme_list.append({
                'n': scheme_info[0],
                't': self.type_conformity[scheme_info[1]]
            })

        return {
            's': scheme_list,
            'd': value_list
        }

    def navigation(self, page, page_size, has_more):
        """
        Метод для создания параметров навигации
        :param page: Номер страницы
        :param page_size: Размер страницы
        :param has_more: Параметр наличия данных кроме возвращаемых
        :return: rpc-record с навигацией
        """
        # TODO: Написать реализацию navigaion (используйте record)
        return None

    def parse_result(self, raw_data):
        """
        Обработчик возвращаемого результата
        :param raw_data: ответ вызова rpc
        :return: обработанные данные
        """
        _parse_data = lambda names, data: {name: self.parse_result(data[names.index(name)]) for name in names}

        if not raw_data:
            return None
        elif isinstance(raw_data, dict):
            raw_type = raw_data.get('_type')
            scheme_names = [scheme['n'] for scheme in raw_data.get('s', [])]
            if raw_type == 'record':
                return _parse_data(scheme_names, raw_data['d'])
            elif raw_type == 'recordset':
                return [_parse_data(scheme_names, data) for data in raw_data['d']]
        return raw_data


# TODO: Написть реализацию получения новостей через класс Platform
# прогонять результат через парсер (который так же нужно реализовать)
# возвращать все по роутингу /news
# хорошо было бы разобраться с роутингом вида /news/{batch_size},
# чтобы возвращать запрошенное количество новостей

platform = Platform()
print(dir(platform))