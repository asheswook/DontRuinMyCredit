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
from aiohttp import ClientSession, CookieJar

env = ssenv.Environment()
env.load_dotenv()

@dataclass
class Subject:
    subject_id: int
    subject_name: str

@dataclass
class Assignment(Subject):
    asi_name: str
    start_date: str
    end_date: str
    asi_type: str

@dataclass
class User:
    name: str
    id: str

class Parser:
    def __init__(self):
        self.subjects: list[Subject] = []
        self.assignments: list[Assignment] = []
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
        self.cookieJar = CookieJar(unsafe=True)
        self.session = ClientSession(headers=self.headers, cookie_jar=self.cookieJar)
        self.user: User = None
        


    async def close(self):
        await self.session.close()

    
    async def post_login(self) -> bool:
        url = '''https://smartid.ssu.ac.kr/Symtra_sso/smln_pcs.asp?apiReturnUrl=https%3A%2F%2Flms.ssu.ac.kr%2Fxn-sso%2Fgw-cb.php'''
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
                            soup = BeautifulSoup(html, 'html.parser')
                            print(soup)

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
        print(self.user.name)


        url = f'https://canvas.ssu.ac.kr/learningx/dashboard?user_login={self.user.id}&locale=ko'
        async with self.session.get(url) as res:
            html = await res.text()
            print(res)

            soup = BeautifulSoup(html, 'html.parser')
            print(soup)
            
            await self.close()
            self.headers['Authorization'] = "Bearer " + self.get_ready_for_cookies()['xn_api_token']
            print(self.headers)
            self.session = ClientSession(headers=self.headers, cookie_jar=self.cookieJar)



            url = 'https://canvas.ssu.ac.kr/learningx/version'
            async with self.session.get(url) as res:
                html = await res.text()
                print(html)
            
                url = 'https://canvas.ssu.ac.kr/learningx/api/v1/users/20232080/terms?include_invited_course_contained=true'

                async with self.session.get(url) as res:
                    html = await res.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    print(soup)

            await self.get_subjects()
            

            print("성공!")
    
    async def get_subjects(self):
        # await self.session.close()
        # self.session = ClientSession(headers=self.headers, cookies=self.get_ready_for_cookies())

        url = "https://canvas.ssu.ac.kr/"
        async with self.session.post(url) as res:
            print(res)

            url = "https://canvas.ssu.ac.kr/"
            async with self.session.get(url) as res:
                html = await res.text()
                soup = BeautifulSoup(html, 'html.parser')
                print(soup)

                url = "https://canvas.ssu.ac.kr/api/v1/dashboard/dashboard_cards"
                async with self.session.get(url) as res:
                    pass


        

    async def get_assignments(self, subject_id: int):
        url = f"https://canvas.ssu.ac.kr/learningx/api/v1/courses/{subject_id}/modules?include_detail=true"

    def get_ready_for_cookies(self):
        cookies1 = self.cookieJar.filter_cookies('https://lms.ssu.ac.kr')
        cookies2 = self.cookieJar.filter_cookies('https://canvas.ssu.ac.kr')
        cookies3 = self.cookieJar.filter_cookies('https://smartid.ssu.ac.kr')
        cookies4 = self.cookieJar.filter_cookies('https://ssu.ac.kr')
        cookies5 = self.cookieJar.filter_cookies('https://class.ssu.ac.kr')

        cookies = {}
        cklist = [cookies1, cookies2, cookies3, cookies4, cookies5]
        for ck in cklist:
            for c in ck:
                cookies[c] = ck[c].value

        return cookies
        
                    




async def main():
    parser = Parser()
    await parser.login_portal()
    await parser.close()

if __name__ == '__main__':
    print("start time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    asyncio.run(main())
    print("end time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))