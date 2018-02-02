# -*- coding: utf-8 -*-

"""
@purpose: 
@version: 1.0
@author: Roarain
@time: 2018/2/1 13:44
@contact: welovewxy@126.com
@file: conversation.py
@license: Apache Licence
@site: 
@software: PyCharm
"""

from aip import AipSpeech
from aip import AipNlp
import playsound
import os
import time
from urllib.request import *
import sys
import json
import subprocess
from collections import deque
import collections
import requests
import playsound
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import logging

logging.basicConfig(filename='dialogue.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# logging.disable(level=logging.DEBUG)


class RegisterConversation(object):
    def __init__(self):
        self.app_id_aip = '10764026'
        self.api_key_aip = 'eOeDzQSnqFmX6CEhpYFkpTrR'
        self.secret_key_aip = 'ohE7z6RlG33EP2ikRq6iOwlcmq6hGVba'
        self.url_aip = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}'.format(
            self.api_key_aip, self.secret_key_aip)

        self.app_id_unit = '10764026'
        self.api_key_unit = 'eOeDzQSnqFmX6CEhpYFkpTrR'
        self.secret_key_unit = 'ohE7z6RlG33EP2ikRq6iOwlcmq6hGVba'
        self.url_unit = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}'.format(
            self.api_key_unit, self.secret_key_unit)

        self.headers = ('Content-Type', 'application/json; charset=UTF-8')

        self.access_token_aip = self.get_url_access_token(self.url_aip, self.headers)
        self.access_token_unit = self.get_url_access_token(self.url_unit, self.headers)
        self.access_token_unit = '24.85b3f9a3b39067f9080e1d297c4f57c1.2592000.1519893495.282335-10770461'

        self.client_aip = AipSpeech(self.app_id_aip, self.api_key_aip, self.secret_key_aip)
        self.client_nlp = AipNlp(self.app_id_aip, self.api_key_aip, self.secret_key_aip)

        self.speech_recognition_queue = collections.deque()
        self.speech_2_text_queue = collections.deque()
        self.speech_synthesis_queue = collections.deque()
        self.text_2_speech_queue = collections.deque()

        self.scene_id = 17179
        self.url_unit_conversation = 'https://aip.baidubce.com/rpc/2.0/solution/v1/unit_utterance'
        self.session_id = ''

    def get_url_access_token(self, url, headers):
        content = self.get_url_content(url, headers)
        content_json = json.loads(content)
        access_token = content_json['access_token']
        return access_token

    def get_url_content(self, url, headers, args=None):
        req = Request(url)
        req.add_header(headers[0], headers[1])
        res = urlopen(req)
        content = res.read()
        return content

    def get_file_content(self, file_path):
        with open(file_path, 'rb') as fp:
            return fp.read()

    def speech_recognition(self, file_path):
        self.speech_recognition_queue.append(file_path)
        file_content = self.get_file_content(file_path)
        logging.info('语音识别时正在读取文件{}内容'.format(file_path))
        content = self.client_aip.asr(file_content,
                                 format='pcm',
                                 rate=16000,
                                 options={'lan': 'zh'}
                                 )
        text = content['result'][0][:-1]
        if text:
            logging.info('恭喜，语音文件{}识别成功，内容是:{}'.format(file_path, text))
            self.speech_2_text_queue.append(text)
            return text

    def speech_synthesis(self, text, file_path=str(time.time())+'.mp3'):
        self.text_2_speech_queue.append(text)
        result = self.client_aip.synthesis(text, 'zh', 1, {'vol': 5, 'per': 0})

        if not isinstance(result, dict):
            logging.info('音频合成成功，正在写入文件: {}'.format(file_path))
            with open(file_path, 'wb') as fp:
                fp.write(result)
            logging.info('恭喜，音频文件{}写入成功！'.format(file_path))
            fp.close()
        else:
            logging.info('音频合成失败，错误是： {}'.format(result))
        logging.info('正在播放合成的语音文件{}'.format(file_path))
        playsound.playsound(file_path)
        logging.info('完成播放合成的语音文件{}'.format(file_path))

        if os.path.exists(file_path):
            return file_path

    def get_session_id(self):
        url_conversation = 'https://aip.baidubce.com/rpc/2.0/solution/v1/unit_utterance?access_token={}'.format(
            self.access_token)
        pass

    def mp3_to_pcm(self, filename):
        filename_pre = filename.split('.')[0]
        filename_post = filename.split('.')[1]
        filename_conversed = filename_pre + '.pcm'
        if os.path.exists(filename_conversed):
            logging.info('文件{}已存在，正在重命名'.format(filename_conversed))
            filename_rename = filename_conversed + str(time.time())
            os.rename(filename_conversed, filename_rename)
            logging.info('将文件{}重命名为{}'.format(filename_conversed, filename_rename))

        if filename_post in ['mp3', 'wav', 'amr']:
            args = 'ffmpeg.exe -i {} -f s16le -ac 1 -ar 16000 {}.pcm'.format(filename, filename_pre)
            process = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            process.wait()
            logging.info('音频文件{}已成功转换为{}'.format(filename, filename_conversed))
            # logging.info(process.stdout.read().decode('utf-8'))
        elif filename_post == 'pcm':
            pass
        else:
            logging.error('音频格式不是mp3、pcm、wav、amr中的一种，无法识别，请找百度...')
            return

        if os.path.exists(filename_conversed):
            return filename_conversed

    def make_conversation(self, asked_speech):
        logging.info('正在播放用户输入的语音')
        playsound.playsound(asked_speech)
        logging.info('完成播放用户输入的语音')
        asked_speech_pcm = self.mp3_to_pcm(asked_speech)
        asked_text = self.speech_recognition(asked_speech_pcm)
        post_dict = {
            "scene_id": self.scene_id,
            "query": asked_text,
            "session_id": self.session_id,
        }

        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
        }
        params = (
            ('access_token', self.access_token_unit),
        )
        response = self.post_param_data_headers(
            self.url_unit_conversation,
            headers=headers,
            params=params,
            data=post_dict,
        )

        if not self.session_id:
            self.session_id = response['result']['session_id']

        result = response['result']['action_list'][0]['say']
        return result

    def post_param_data_headers(self, url, params=None, data=None, headers=None):
        data = json.dumps(data).encode(encoding='utf-8')
        result = requests.post(url, headers=headers, params=params, data=data, verify=False).json()
        return result


if __name__ == '__main__':
    rc = RegisterConversation()
    # ask_text = rc.make_conversation('start.mp3')
    answer_list = ['start.mp3', 'answer_hospital.mp3', 'answer_department.mp3', 'answer_time.mp3', 'answer_doctor.mp3', 'answer_name.mp3', 'answer_gender.mp3', 'answer_phone.mp3', ]
    answer_deque = deque()
    answer_deque.extend(answer_list)
    ask_deque = deque()
    while answer_deque:
        answers = answer_deque.popleft()
        ask_text = rc.make_conversation(answers)
        rc.speech_synthesis(ask_text, file_path=str(time.time())+'.mp3')
        ask_deque.append(ask_text)
        # time.sleep(3)
    logging.info('ask_deque: {}'.format(ask_deque))
    logging.info('speech_2_text_queue: {}'.format(rc.speech_2_text_queue))
