from typing import Union, Any, Optional, List
from flask import Flask, render_template, jsonify, request, json, Response
from pymongo import MongoClient
import requests

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client.dbStock


@app.route('/')
def index() -> str:
    return render_template('index.html')


@app.route('/base/codes', methods=['GET'])
def get_base_codes() -> Response:
    """
    find({}) 전체 stock 을 가져온다.\n
    distinct group 컬럼 중복 데이터  제거해서 가져온다.\n
    :return: flask.json
    """
    codes = list(db.codes.find({}).distinct("group"))
    return jsonify(codes)


@app.route('/codes', methods=['GET'])
def get_codes() -> Response:
    """
    request 로 받는 코드로 db 에서 데이터를 불러온다.\n
    :return: flask.json
    """
    group: Union[Optional[str], Any] = request.args.get('group')
    codes: List[json] = list(db.codes.find({'group': group}, {'_id': False}))
    return jsonify(codes)


@app.route('/stocks', methods=['POST'])
def save_info() -> Response:
    """
    사용자가 선택한 market, sector, tags 를 통해 결과물
    리턴 + 검사 데이터 DB 저장\n
    :return: flask.json
    """
    info = request.json
    stocks = list(db.stocks.find(info, {'_id': False}))
    db.searchs.insert_one(info)
    return jsonify(stocks)


@app.route('/stock/like', methods=['PUT'])
def set_like() -> str:
    """
    사용자가 특정 스톡의 코드를 보내오면 DB 데이터 isLike 수정\n
    :return: str
    """
    info = request.json
    db.stocks.update_one({"code": info['code']}, {"$set": {"isLike": True}})
    return "success"


@app.route('/stock/unlike', methods=['PUT'])
def set_unlike() -> str:
    """
    사용자가 특정 스톡의 코드를 보내오면 DB 데이터 isLike 수정\n
    :return: str
    """
    info = request.json
    db.stocks.update_one({"code": info['code']}, {"$set": {"isLike": False}})
    return "success"


@app.route('/stocks/like', methods=['GET'])
def get_stocks() -> Response:
    """
    즐겨찾기 탭을 클릭하면, like 값이 True 인 stock list 반환\n
    :return: flask.json
    """
    stocks = list(db.stocks.find({"isLike": True}, {'_id': False}))
    return jsonify(stocks)


@app.route('/stock', methods=['GET'])
def get_info() -> Response:
    """
    결과로 받은 stock 의 코드를 api 를 통해 조회한 후 DB 수정 및 리턴\n
    :return: flask.json
    """
    code = request.args.get('code')
    url = f'https://m.stock.naver.com/api/stock/{code}/integration'
    headers = {'accept': 'application/json', 'accept-encoding': 'gzip, deflate, br',
               'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7', 'origin': 'https://m.stock.naver.com',
               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/93.0.4577.82 Safari/537.36'}

    req = requests.get(url, headers=headers)
    data = req.json()['totalInfos']
    price = data[2]["value"]
    trading_vol = data[4]["value"]
    amount = data[6]["value"]
    per = data[10]["value"]
    set_query = {
        "price": price,
        "trading_volume": trading_vol,
        "amount": amount,
        "PER": per
    }
    db.stocks.update_one({"code": code}, {"$set": set_query})
    return jsonify({'amount': amount, 'per': per, 'price': price})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
