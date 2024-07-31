from flask import Flask, request, jsonify, send_file, make_response
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DATA_FILE = 'paoku_data.json'
SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')

# 初始化数据
def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"users": []}, f)

init_data()

# 读取数据
def read_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# 写入数据
def write_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def home():
    return send_file('paoku.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '缺少用户名或密码', 'success': False}), 400

    game_data = read_data()
    if any(user['username'] == username for user in game_data['users']):
        return jsonify({'message': '用户名已存在', 'success': False}), 400

    hashed_password = generate_password_hash(password)
    game_data['users'].append({
        'username': username,
        'password': hashed_password,
        'high_score': 0
    })
    write_data(game_data)

    return jsonify({'message': '注册成功', 'success': True}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '缺少用户名或密码', 'success': False}), 400

    game_data = read_data()
    user = next((user for user in game_data['users'] if user['username'] == username), None)

    if not user:
        return jsonify({'message': '用户不存在', 'success': False, 'reason': 'user_not_exist'}), 404

    if not check_password_hash(user['password'], password):
        return jsonify({'message': '密码错误', 'success': False, 'reason': 'wrong_password'}), 401

    response = make_response(jsonify({'message': '登录成功', 'success': True}))
    response.set_cookie('username', username, secure=True, httponly=True)
    return response

@app.route('/change_username', methods=['POST'])
def change_username():
    data = request.get_json()
    old_username = data.get('old_username')
    new_username = data.get('new_username')

    if not old_username or not new_username:
        return jsonify({'message': '缺少旧用户名或新用户名', 'success': False}), 400

    game_data = read_data()
    if any(user['username'] == new_username for user in game_data['users']):
        return jsonify({'message': '新用户名已存在', 'success': False}), 400

    for user in game_data['users']:
        if user['username'] == old_username:
            user['username'] = new_username
            break
    write_data(game_data)

    response = make_response(jsonify({'message': '用户名更改成功', 'success': True}))
    response.set_cookie('username', new_username, secure=True, httponly=True)
    return response

@app.route('/update_score', methods=['POST'])
def update_score():
    data = request.get_json()
    username = data.get('username')
    score = data.get('score')

    if not username or score is None:
        return jsonify({'message': '缺少用户名或分数', 'success': False}), 400

    game_data = read_data()
    for user in game_data['users']:
        if user['username'] == username:
            user['high_score'] = max(user['high_score'], score)
            break
    write_data(game_data)

    return jsonify({'message': '分数更新成功', 'success': True})

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    game_data = read_data()
    leaderboard = sorted(
        [{'username': user['username'], 'score': user['high_score']} for user in game_data['users']],
        key=lambda x: x['score'],
        reverse=True
    )

    return jsonify(leaderboard)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))