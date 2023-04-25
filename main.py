import asyncio
from bs4 import BeautifulSoup
from dataclasses import dataclass
import time
import re
from typing import Optional
from PIL import Image
from io import BytesIO
import socket
import ssenv
#from app.exceptions.common import *
from aiohttp import ClientSession

env = ssenv.Environment()
env.load_dotenv()

@dataclass
class Subject:
    id: int
    name: str

@dataclass
class Assignment:
    start_date: str
    end_date: str
    name: str
    subject: Subject

@dataclass
class User:
    name: str
    id: str

class Parser:
    def __init__(self):
        self.subjects: list[Subject] = []
        self.assignments: list[Assignment] = []
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
        self.session = ClientSession(headers=self.headers)
        self.user: User = None


    async def close(self):
        await self.session.close()

    
    async def post_login(self) -> bool:
        url = 'https://smartid.ssu.ac.kr/Symtra_sso/smln_pcs.asp'
        data = {
            'content_type': 'application/x-www-form-urlencoded',
            'in_tp_bit': '0',
            'rqst_caus_cd': '03',
            'userid': env.get('USER_ID'),
            'pwd': env.get('USER_PASSWORD'),
        }
        
        async with self.session.get(url) as res:
            async with self.session.post(url, data=data) as res:
                html = await res.text()
                print(res.url)
                if 'smartid.ssu.ac.kr' in res.url.host:
                    html = await res.text()
                    url = html.split("location.href = '")[1].split("'")[0]
                    async with self.session.get(url) as res:
                        html = await res.text()
                        url = html.split('iframe.src="')[1].split('"')[0]
                        async with self.session.get(url) as res:
                            html = await res.text()
                            return True if 'canvas.ssu.ac.kr' in res.url.host else False
                            
                else:
                    return True
                
    async def get_username(self) -> str:
        url = 'https://lms.ssu.ac.kr/mypage'

        async with self.session.get(url) as res:
            if 'lms.ssu.ac.kr' not in res.url.host:
                raise Exception('로그인이 필요합니다.')

            html = await res.text()
            soup = BeautifulSoup(html, 'html.parser')
            name = soup.find('span', {'class': 'xn-header-member-btn-text xn-common-title'}).get_text().split('(')[0]
            return name



    async def login_portal(self):
        url = 'https://lms.ssu.ac.kr/mypage'
        async with self.session.get(url) as res:
            if 'lms.ssu.ac.kr' not in res.url.host:
                isLoggedin = await self.post_login()
                
                if not isLoggedin:
                    raise Exception('로그인 실패')
                else:
                    print("로그인 성공!")

        self.user = User(name= await self.get_username(), id= env.get('USER_ID'))


        url = f'https://canvas.ssu.ac.kr/learningx/dashboard?user_login={self.user.id}&locale=ko'
        async with self.session.get(url) as res:
            html = await res.text()

            soup = BeautifulSoup(html, 'html.parser')
            print(soup)

            print("성공!")
            
                    




async def main():
    parser = Parser()
    await parser.login_portal()
    await parser.close()

if __name__ == '__main__':
    print("start time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    asyncio.run(main())
    print("end time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))