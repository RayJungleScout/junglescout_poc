from os import stat
import re
import xmltodict
from flask import Flask, json, request, jsonify
from flask_redis import FlaskRedis
from flask_cors import CORS
from config import Config
from external.wx.WXBizMsgCrypt import WXBizMsgCrypt

app = Flask(__name__)
cors = CORS(app)
config = Config()
app.config.from_object(config)
redis = FlaskRedis()
redis.init_app(app)

@app.route("/api/membership", methods=['POST'])
def membership_buy():
    params = request.json or {}
    phone = params.get("email")
    if not phone:
        return error_response(400, "email is required")
    if check_membership(phone):
        return error_response(403, "email exists")
    res = set_membership(phone)
    if res:
        return success_response()
    return error_response(500, "operation error")

@app.route("/api/membership", methods=['DELETE'])
def membership_cancel():
    params = request.args or {}
    phone = params.get("email")
    if not phone:
        return error_response(400, "email is required")
    if not check_membership(phone):
        return error_response(404, "email not found")
    res = cancel_membership(phone)
    if res:
        return success_response()
    return error_response(500, "operation error")

@app.route("/api/membership/check", methods=['GET'])
def membership_check():
    params = request.args or {}
    phone = params.get("email")
    if phone:
        res = check_membership(phone=phone)
        if res:
            return success_response()
        return error_response(403, "email exists")
    return error_response(400, "email is required")

@app.route("/api/user", methods=["POST"])
def create_user():
    params = request.json or {}
    phone = params.get("email")
    if not phone:
        return error_response(400, "email is required")
    if check_user(phone):
        return error_response(403, "user exists")
    res = add_user(phone)
    if res:
        return success_response({"email": phone})
    return error_response(500, "operation error")

@app.route("/api/user", methods=['DELETE'])
def delete_user():
    params = request.args or {}
    phone = params.get("email")
    if not phone:
        return error_response(400, "email is required")
    if not check_user(phone):
        return error_response(404, "user not found")
    res = delete_user(phone)
    if res:
        return success_response()
    return error_response(500, "operation error")

@app.route("/api/user", methods=['GET'])
def user_check():
    params = request.args or {}
    phone = params.get("email")
    if not phone:
        return error_response(401)
    if check_user(phone):
        return success_response()
    return error_response(401)

@app.route("/api/ww/feedback", methods=['GET'])
def wechat_work_feedback_test():
    query_params = request.args
    token = app.config.get("WECHAT_WORK_TOKEN")
    aes_key = app.config.get("WECHAT_WORK_AES_KEY")
    corp_id = app.config.get("WECHAT_WORK_CORP_ID")

    query_sign = query_params.get("msg_signature")
    query_ts = query_params.get("timestamp")
    query_nonce = query_params.get("nonce")
    query_echo = query_params.get("echostr")

    wxcpt = WXBizMsgCrypt(token, aes_key, corp_id)
    ret,sEchoStr = wxcpt.VerifyURL(query_sign, query_ts, query_nonce, query_echo)
    if ret != 0:
        return error_response(400)
    return success_response_raw(sEchoStr)

@app.route("/api/ww/feedback", methods=["POST"])
def wechat_work_feedback():
    query_params = request.args
    token = app.config.get("WECHAT_WORK_TOKEN")
    aes_key = app.config.get("WECHAT_WORK_AES_KEY")
    corp_id = app.config.get("WECHAT_WORK_CORP_ID")
    wxcpt = WXBizMsgCrypt(token, aes_key, corp_id)

    query_sign = query_params.get("msg_signature")
    query_ts = query_params.get("timestamp")
    query_nonce = query_params.get("nonce")
    body_data = request.data.decode('utf-8')
    ret,sMsg = wxcpt.DecryptMsg(body_data, query_sign, query_ts, query_nonce)
    if ret != 0:
        return error_response(400)
    app.logger.info("wechat work feedback msg is:%s"%(sMsg))
    return success_response()

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
    user_info = json.dumps({"email": phone})
    res = redis.hset(redis_key, phone, user_info)
    return res

def delete_user(phone: str):
    redis_key = get_user_key()
    res = redis.hdel(redis_key, phone)
    return res

def get_user_key():
    return "poc:user"

def error_response(status_code, msg=""):
    res = jsonify({
        "msg": msg
    })
    res.status_code = status_code
    return res

def success_response(data = {}):
    return jsonify({
        "data": data
    })

def success_response_raw(message: str = ""):
    return message

if __name__ == "__main__":
    app.run()


