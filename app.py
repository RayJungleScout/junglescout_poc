from os import stat
from flask import Flask, json, request, jsonify
from flask_redis import FlaskRedis
from config import Config

app = Flask(__name__)
config = Config()
app.config.from_object(config)
redis = FlaskRedis()
redis.init_app(app)

@app.route("/api/membership", methods=['POST'])
def membership_buy():
    params = request.json or {}
    phone = params.get("phone")
    if not phone:
        return error_response(400, "phone is required")
    if check_membership(phone):
        return error_response(403, "phone exists")
    res = set_membership(phone)
    if res:
        return success_response()
    return error_response(500, "operation error")

@app.route("/api/membership", methods=['DELETE'])
def membership_cancel():
    params = request.json or {}
    phone = params.get("phone")
    if not phone:
        return error_response(400, "phone is required")
    if not check_membership(phone):
        return error_response(404, "phone not found")
    res = cancel_membership(phone)
    if res:
        return success_response()
    return error_response(500, "operation error")

@app.route("/api/membership/check", methods=['GET'])
def membership_check():
    params = request.json or {}
    phone = params.get("phone")
    if phone:
        res = check_membership(phone=phone)
        if res:
            return success_response()
        return error_response(403, "phone exists")
    return error_response(400, "phone is required")

@app.route("/api/user", methods=["POST"])
def create_user():
    params = request.json or {}
    phone = params.get("phone")
    if not phone:
        return error_response(400, "phone is required")
    if check_user(phone):
        return error_response(403, "user exists")
    res = add_user(phone)
    if res:
        return success_response({"phone": phone})
    return error_response(500, "operation error")

@app.route("/api/user", methods=['DELETE'])
def delete_user():
    params = request.json or {}
    phone = params.get("phone")
    if not phone:
        return error_response(400, "phone is required")
    if not check_user(phone):
        return error_response(404, "user not found")
    res = delete_user(phone)
    if res:
        return success_response()
    return error_response(500, "operation error")

@app.route("/api/user", methods=['GET'])
def user_check():
    params = request.json or {}
    phone = params.get("phone")
    if not phone:
        return error_response(401)
    if check_user(phone):
        return success_response()
    return error_response(401)

def set_membership(phone: str):
    redis_key = get_membership_key()
    res = redis.sadd(redis_key, phone)
    return res

def cancel_membership(phone: str):
    redis_key = get_membership_key()
    res = redis.srem(redis_key, phone)
    return res

def check_membership(phone: str):
    redis_key = get_membership_key()
    res = redis.sismember(redis_key, phone)
    return True if res else False

def get_membership_key():
    return "poc:membership"


def check_user(phone: str):
    redis_key = get_user_key()
    res = redis.hexists(redis_key, phone)
    return res

def add_user(phone: str):
    redis_key = get_user_key()
    user_info = json.dumps({"phone": phone})
    res = redis.hset(redis_key, phone, user_info)
    return res

def delete_user(phone: str):
    redis_key = get_user_key()
    res = redis.hdel(redis_key, phone)
    return res

def get_user_key():
    return "poc:user"

def error_response(status_code, msg):
    res = jsonify({
        "msg": msg
    })
    res.status_code = status_code
    return res

def success_response(data = {}):
    return jsonify({
        "data": data
    })

if __name__ == "__main__":
    app.run()


