from distutils.log import log
import json
from json.tool import main
from logging import Logger
import re

from jdmaotai.httpSession import session
from jdmaotai.config import global_config
import time
from urllib.parse import urlencode
from jdmaotai.sign.jdSign import getSignWithstv
from loguru import logger

logger.add('./log/api_info_{time}.log', rotation="50 MB", encoding='utf-8')
logger.add('./log/api_error_{time}.log', rotation="50 MB", encoding='utf-8',
           filter=lambda record: "ERROR" in record['level'].name)


class JDAPi():
    def __init__(self) -> None:
        self.session_obj = session().session
        self.appVersion = global_config.get('config',"appVersion")
        self.eid = global_config.get('config',"eid")
        self.fp = global_config.get('config', "fp")
        self.M_JD_URL = "https://api.m.jd.com/client.action?"
        self.uuid = global_config.get('config',"uuid")

    def _getTokenEP(self):
        t = time.time()
        st = str(int(round(t * 1000) - 330))
        return {"hdid": "JM9F1ywUPwflvMIpYPok0tt5k9kW4ArJEU3lfLhxBqw=", "ts": st, "ridx": -1,
                "cipher": {"area": "CJDpCJOnCv80DtY2DV80DtY5EK==", "d_model": "UwVubWvBCtLGcw8=",
                           "wifiBssid": "YJuzDwTrDWPvZJCyCQG4YJGmCtKzC2Y3DwO5CwTuZNG=", "osVersion": "CJO=",
                           "d_brand": "WQvrb21f", "screen": "CtS5DsenCNqm", "uuid": "DJczEWU2DwPuDwDwYJOyDG==",
                           "aid": "DJczEWU2DwPuDwDwYJOyDG==", "openudid": "DJczEWU2DwPuDwDwYJOyDG=="}, "ciphertype": 5,
                "version": "1.2.0", "appname": "com.jingdong.app.mall"}

    def _getTokenQuery(self):
        ep = self._getTokenEP()
        QueryString = {
            "functionId": "genToken",
            "clientVersion": self.appVersion,
            "build": 98990,
            "client": "android",
            "eid": self.eid,
            "ef": "1",
            "ep": ep,
            "fp": self.fp
        }
        return QueryString

    def _getIsAppointQuery(self):
        ep = self._getTokenEP()
        QueryString = {
            "functionId": "isAppoint",
            "clientVersion": self.appVersion,
            "build": 98990,
            "client": "android",
            "eid": self.eid,
            "ef": "1",
            "ep": ep
        }
        return QueryString

    def _getAppointQuery(self):
        ep = self._getTokenEP()
        QueryString = {
            "functionId": "appoint",
            "clientVersion": self.appVersion,
            "build": 98990,
            "client": "android",
            "eid": self.eid,
            "ef": "1",
            "ep": ep
        }
        return QueryString

    def _getTokenBody(self):
        return {
            "body": '{"action":"to","to":"https%3A%2F%2Fdivide.jd.com%2Fuser_routing%3FskuId%3D100012043978%26from%3Dapp"}'}

    def _getIsAppointBody(self):
        return {"body": '{"isShowCode":"0","skuId":"100012043978","sr":"1"}'}

    def _getAppointBody(self):
        return {
            "body": '{"autoAddCart":"0","bsid":"","check":"0","ctext":"","isShowCode":"0","mad":"0","skuId":"100012043978","type":"1"}'}

    def _parseTokenUrl(self, inData: dict, body: dict):
        return self.M_JD_URL + urlencode(inData) + "&" + getSignWithstv(inData["functionId"], body["body"], self.uuid,
                                                                        inData["client"], inData["clientVersion"])

    def getToken(self):
        inData = self._getTokenQuery()
        body = self._getTokenBody()
        url = self._parseTokenUrl(inData, body)
        body = self._getTokenBody()
        r = self.session_obj.post(url, data=body)
        if r.status_code == 200:
            text = r.text
            result = json.loads(text)
            logger.info(f"getTokenResult{result}")
            return result["url"], result["tokenKey"]
        else:
            return None, None

    def getdivideUrlbyUNJump(self, jumpUrl, tokenkey):
        toUrl = "https%3A%2F%2Fdivide.jd.com%2Fuser_routing%3FskuId%3D100012043978%26from%3Dapp"
        jumpURL = f"{jumpUrl}?tokenKey={tokenkey}&to={toUrl}"
        self.session_obj.headers.clear()
        logger.info(f"do=jumpUrl====>{jumpURL}")
        appjump = self.session_obj.get(url=jumpURL, allow_redirects=False)
        if appjump.status_code == 302:
            locationUrl = appjump.headers["Location"]
            logger.info(f"get=divideUrl====>{locationUrl}")
            return locationUrl
        else:
            logger.error(f"获取divideUrl出错:{appjump.text}")
            return None

    def getCaptchaUrlbyDivide(self, divideURl):
        logger.info(f"do=divideUrl====>{divideURl}")

        captchaResult = self.session_obj.get(divideURl, allow_redirects=False)
        if captchaResult.status_code == 302:
            locationUrl = captchaResult.headers["Location"]
            logger.info(f"get=captchaUrl====>{locationUrl}")
            return locationUrl
        else:
            logger.error(f"获取captchaUrl出错:{captchaResult.text}")
            return None

    def getSkillActionUrlbyCaptcha(self, catpchaUrl):
        logger.info(f"do=captchaUrl====>{catpchaUrl}")

        skillReslut = self.session_obj.get(catpchaUrl, allow_redirects=False)
        if skillReslut.status_code == 302:
            skillUrl = skillReslut.headers["Location"]
            logger.info(f"get=skillUrl====>{skillUrl}")
            return skillUrl
        else:
            logger.error(f"获取skillUrl出错:{skillReslut.text}")
            return None

    # 提交订单，不用处理
    def doSkillAction(self, skillUrl):
        logger.info("do=skillUrl=====>", skillUrl)
        actionResult = self.session_obj.get(skillUrl, allow_redirects=False)
        logger.info(actionResult.status_code)
        logger.info(actionResult.text)

    def doOrderSumit(self):
        orderUrl = "https://marathon.jd.com/seckillnew/orderService/submitOrder.action?skuId=100012043978"
        payload = 'num%3D1%26addressId%3D1419077721%26name%3D%E4%BB%98%E6%B4%AA%E5%BD%AC%26provinceId%3D13%26provinceName%3D%E5%B1%B1%E4%B8%9C%26cityId%3D1112%26cityName%3D%E6%B3%B0%E5%AE%89%E5%B8%82%26countyId%3D46665%26countyName%3D%E5%B2%B1%E5%B2%B3%E5%8C%BA%26townId%3D46698%26townName%3D%E5%8C%97%E9%9B%86%E5%9D%A1%E8%A1%97%E9%81%93%26addressDetail%3D%E9%95%BF%E5%9F%8E%E8%B7%AF%E5%98%89%E5%92%8C%E6%96%B0%E5%9F%8E%E4%BA%8C%E6%9C%9FA6-3-302%26mobile%3D155****3751%26mobileKey%3D0df68e829a3bd20c8c95768965acc88b%26email%3D%26invoiceTitle%3D4%26invoiceContent%3D1%26invoiceTaxpayerNO%3D%26invoicePhone%3D155****3751%26invoicePhoneKey%3D0df68e829a3bd20c8c95768965acc88b%26invoice%3Dtrue%26password%3D%26codTimeType%3D3%26paymentType%3D4%26overseas%3D0%26phone%3D%26areaCode%3D86%26token%3D53a0abb5148aea25e7b8da23b3791514%26skuId%3D100012043978%26eid%3Djdd03E6QGGS3M6CMP3QLLK4CMMI5D42RFEYRWN4BSV2YZMAWX5HQLNIYYLSSCIL54VNC76LC6D4CVVXNLOWYX5T7HDVBGNYAAAAMLDTSEOKAAAAAACR5JCEBZRSHNPUX'
        logger.info("finalHeader======>", self.session_obj.headers)
        orderRersilt = self.session_obj.post(orderUrl, data=payload)
        # logger.info(orderRersilt.text)
        if orderRersilt.status_code == 200:
            try:
                result = json.loads(orderRersilt.text)
                return result
            except Exception as e:
                logger.error(f"发起订单错误:{orderRersilt.text}")
                return None
        else:
            return None

    def isAppoint(self):
        inData = self._getIsAppointQuery()
        body = self._getIsAppointBody()
        url = self._parseTokenUrl(inData, body)
        r = self.session_obj.post(url, data=body)
        if r.status_code == 200:
            text = r.text
            result = json.loads(text)
            logger.info(result)
            return result.get("isAppoint")
        else:
            logger.error("查询预约状态失败")
            return False

    def doAppoint(self):
        inData = self._getAppointQuery()
        body = self._getAppointBody()
        url = self._parseTokenUrl(inData, body)
        r = self.session_obj.post(url, data=body)
        if r.status_code == 200:
            text = r.text
            result = json.loads(text)
            return result
        else:
            logger.error("预约失败")



# =======================================================================

import json
from jd_logger import logger
from urllib import parse
from urllib.parse import urlparse, parse_qs
import sys
import requests
from sign.jdSign import getSignWithstv
import util


def url_params_to_json():
    # 期望的参数列表
    expected_params = ['functionId', 'clientVersion', 'build', 'client', 'partner', 'oaid', 'sdkVersion', 'lang',
                       'harmonyOs', 'networkType', 'uts', 'uemps', 'ext', 'eid', 'x-api-eid-token', 'ef', 'ep']

    api_jd_url = global_config.getRaw('config', 'api_jd_url')
    tmp_url = urlparse(api_jd_url)
    parad = parse_qs(tmp_url.query)

    # 获取 URL 中的参数名
    url_params = list(parad.keys())

    # 检查参数是否匹配
    if set(url_params) == set(expected_params):
        logger.info("api_jd_url参数校验正确")
    elif set(expected_params) - set(url_params):
        missing_params = set(expected_params) - set(url_params)
        logger.error("api_jd_url缺少以下参数:" + str(missing_params))
        input("api_jd_url错误，按 Enter 键退出...")
        sys.exit()
    else:
        unnecessary_params = set(url_params) - set(expected_params)
        logger.info("删除api_jd_url中多余的参数:" + str(unnecessary_params))
        for extra_param in unnecessary_params:
            del parad[extra_param]

    params_dict = {key: value[0] if len(value) == 1 else value for key, value in parad.items()}
    return params_dict
class SpiderSession:

    def __init__(self):
        self.ep_json = None
        self.client_version = None
        self.client = None
        self.user_agent = None
        self.payload = None
        self.uuid = None
        self.local_cookie = global_config.getRaw('config', 'local_cookies')
        self.local_jec = global_config.getRaw('config', 'local_jec')
        self.local_jeh = global_config.getRaw('config', 'local_jeh')
        self.local_jdgs = global_config.getRaw('config', 'local_jdgs')
        if self.local_cookie == '' or self.local_jec == '' or self.local_jdgs == '' or self.local_jdgs == '':
            logger.error('配置文件不完整，请补充cookie，jec，jdgs，jd_url等参数')
            input("配置文件不完整，按 Enter 键退出...")
        self.init_param()
        self.session = self._init_session()

    def init_param(self):
        result = url_params_to_json()
        try:
            self.payload = result
            self.client = result['client']
            self.client_version = result['clientVersion']
            self.ep_json = json.loads(self.payload['ep'])
            self.uuid = util.decode_base64(self.ep_json['cipher']['uuid'])
            self.user_agent = 'okhttp/3.12.16;jdmall;' + self.client + ';version/' + self.client_version + ';build/' + \
                              result['build'] + ';'
        except Exception as e:
            logger.error('api_jd_url参数中应包含client，clientVersion，build，ep等参数')
            input("配置文件错误，按 Enter 键退出...")
            sys.exit()

    def _init_session(self):
        session = requests.session()
        session.headers = self.get_headers()
        session.cookies = self.init_cookies()
        return session

    def get_headers(self):
        return {"User-Agent": self.user_agent,
                "x-rp-client": "android_3.0.0",
                "J-E-C": self.local_jec,
                "jdgs": self.local_jdgs,
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Connection": "keep-alive"}

    def get_user_agent(self):
        return self.user_agent

    def get_session(self):
        return self.session

    def get(self, url, **kwargs):
        """封装get方法"""
        # 获取请求参数
        params = kwargs.get("params")
        allow_redirects = kwargs.get("allow_redirects")
        try:
            result = self.session.get(url, params=params, allow_redirects=allow_redirects)
            return result
        except Exception as e:
            logger.error("get请求错误: %s" % e)
            input("网络请求错误，按 Enter 键退出...")
            sys.exit()

    def post(self, url, **kwargs):
        """封装post方法"""
        # 获取请求参数
        params = kwargs.get("params")
        data = kwargs.get("data")
        allow_redirects = kwargs.get("allow_redirects")
        try:
            result = self.session.post(url, params=params, data=data, allow_redirects=allow_redirects)
            return result
        except Exception as e:
            logger.error("post请求错误: %s" % e)
            input("网络请求错误，按 Enter 键退出...")
            sys.exit()

    def init_cookies(self):
        cookie_jar = requests.cookies.RequestsCookieJar()
        for cookie in self.local_cookie.split(';'):
            cookie_jar.set(cookie.split('=')[0], cookie.split('=')[-1])
        return cookie_jar

    def update_cookies(self, cookie_str):
        # print('更新cookie：'+ cookie_str)
        cookie_jar = self.session.cookies
        for cookie in cookie_str.split(';'):
            cookie_jar.set(cookie.split('=')[0], cookie.split('=')[-1])
        self.session.cookies.update(cookie_jar)
        # print (self.session.cookies.get_dict())

    def requestWithSign(self, function_id, body, data):
        url = 'https://api.m.jd.com/client.action?'
        sign_str = getSignWithstv(function_id, json.dumps(body, separators=(',', ':')), self.uuid, self.client,
                                  self.client_version)
        self.payload['functionId'] = function_id
        ts = util.local_time()
        self.payload['ep'] = self.gen_cipher_ep()

        url = url + parse.urlencode(self.payload) + '&' + sign_str
        resp = self.session.post(url=url, data=data)
        return resp

    def gen_cipher_ep(self):
        ts = util.local_time()
        self.ep_json['ts'] = ts
        return json.dumps(self.ep_json, separators=(',', ':'))