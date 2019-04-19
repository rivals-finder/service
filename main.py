from flask import Flask, jsonify

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route("/mock")
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


app.run()
