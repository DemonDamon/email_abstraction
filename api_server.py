# Date    : 2024/9/26 22:22
# File    : api_server.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


import os
import sys
import requests
import argparse

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import uvicorn

from sanic import Sanic
from sanic.response import json
from sanic_cors import CORS
from loguru import logger

from config import load_config
from utils import colorstr
import prompts

parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="config.json", help="config file path")
args = parser.parse_args()

config = load_config(args.config)
template_str = prompts.get_prompt(config.prompts.version)


class CustomFileChangeHandler(FileSystemEventHandler):
    def __init__(self, dont_watch_files_list):
        super().__init__()
        self.files_dont_watch = dont_watch_files_list

    def on_modified(self, event):
        if not any(event.src_path.endswith(file) for file in self.files_dont_watch):
            print(f"File {event.src_path} changed, restarting...")
            restart_program()  # Use exit code 3 to trigger a restart


def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)


def create_app():
    _app = Sanic("email_intelli_abstract_service")
    CORS(_app, origins="*")

    def call_llm_api(prompt):
        """调用大模型API"""
        data = {
            "request_id": "test-jbjsax-89ujwbjdq-dbjdh8",
            "model": "Qwen1.5-32B-Chat-GPTQ-Int4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "top_p": 0.95,
            "stream": False
        }

        response = requests.post(config.llm_api.url, headers=vars(config.llm_api.headers), json=data)

        return response.json()

    def generate_email_summary(email_content):
        """生成邮件摘要"""
        prompt = prompts.format_prompt(config.prompts.version,
                                       user_raw_text_input=email_content)

        return call_llm_api(prompt)

    def llm_output_parser(llm_out_json):
        try:
            # 检查响应是否成功
            if llm_out_json.get('success') and llm_out_json.get('code') == '0000':
                # 获取模型输出的文本内容
                content = llm_out_json.get('data', {}).get('choices', [{}])[0].get('message', {}).get('content')
                return content
            else:
                logger.error(f"Request was not successful. Message: {llm_out_json.get('message')}")
                return ""
        except Exception as e:
            logger.error(f"Error occurred while getting model output: {str(e)}")
            return ""

    @_app.post("/aibox/richMail/v1.0/intelliAbstract")
    async def intelli_abstract(request):
        sid_id = request.args.get("sid")
        if not sid_id:
            logger.error("sid为None")
            return json({"code": 1, "message": "'sid' is None", "text": "", "data": []})

        req_json_body = request.json

        if "email_content" not in req_json_body:
            logger.error(colorstr("{} - {}".format(sid_id, "请求体不包含<'email_content'>字段"), color="red"))
            return json({"code": 1, "message": "Invalid request: 'email_content' missing", "text": ""})

        email_content = req_json_body["email_content"]

        llm_out_json = generate_email_summary(email_content)
        out = llm_output_parser(llm_out_json)

        logger.info(colorstr(f"sid={sid_id}|邮件摘要=\n{out}", color="orange"))

        return json({"code": 0, "message": "", "text": out})

    return _app


if __name__ == "__main__":
    logger.add("email_abstraction.log", rotation="5 MB")

    files_dont_watch = ["requirements.txt", "README.md", "email_abstraction.log"]  # List the files you dont want to watch

    # Set up the watchdog observer
    event_handler = CustomFileChangeHandler(files_dont_watch)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)  # You can specify the directory to watch
    observer.start()

    try:
        app = create_app()
        logger.info(f"host={config.server.host} | port={config.server.port}")
        app.run(host=config.server.host,
                port=config.server.port,
                auto_reload=False,
                debug=True)
    except (KeyboardInterrupt, SystemExit):
        observer.stop()
    observer.join()


