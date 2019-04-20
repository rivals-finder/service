import json
import requests
import re
from flask import Flask, jsonify

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/mock', methods=['GET'])
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

    return jsonify(items=news_list), 200, {'Content-Type': 'application/json; charset=utf-8'}


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

    # Тут нужно описать поля класса

    def __init__(self, news):
        self.title = self.get_str(news['RecordNews'], 'Title')
        self.brief = self.get_str(news['RecordNews'], 'Brief')
        self.date_time = self.get_str(news, 'LentaDateTime')[:10]
        self.news_guid = self.get_str(news, 'Object')

    @staticmethod
    def get_str(event, key):
        return re.sub(r'<.*?>', r'', str(event[key])) if key in event and event[key] is not None else ''

    def get_json(self):
        return json.loads(json.dumps({
            'id'   : self.news_guid,
            'title': self.title,
            'text' : self.brief,
            'date' : self.date_time,
            'link' : self.LINK_PREFIX.format(self.news_guid)
        }, ensure_ascii=False))


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
        )
        try:
            response = response.json()
            result = self.parse_result(response['result'])
        except Exception as ex:
            print('Произошла ошибка. Exception: {}'.format(ex))
            raise response
        return result

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
        return self.record(
            [
                {page: ('Страница', 'int')},
                {page_size: ('РазмерСтраницы', 'int')},
                {has_more: ('has_more', 'bool')}
            ]
        )

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


@app.route('/news/')
@app.route('/news/<batch_size>')
def news_size(batch_size=10):
    platform = Platform()
    news_list = platform.rpc('Event.ListWallWithPosition', {
                             'ДопПоля': [],
                             'Фильтр': platform.record([{GROUP_ID: ('Channel', 'string')}]),
                             'Сортировка': None,
                             'Навигация': platform.navigation(0, batch_size, 'true')
                             })
    return jsonify(items=[NewsInfoParser(item).get_json() for item in news_list])
