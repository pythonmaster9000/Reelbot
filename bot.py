import io
import time
import requests
import discord
from discord.ext import commands
from typing import Union

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents)


class ReelsDownloader:
    def __init__(self):
        self.last_called: float = time.time()
        self.cooldown_time: int = 1
        self.proxy: dict = {
            "http": "",
            "https": ""
        }

    @staticmethod
    def extract_shortcode_from_url(instagram_url) -> Union[str, None]:
        if "/reel/" in instagram_url:
            return instagram_url.split("/reel/")[1].split("/")[0]
        elif "/reels/" in instagram_url:
            return instagram_url.split("/reels/")[1].split("/")[0]
        return None

    def fetch_instagram_reel_data(self, shortcode: str) -> Union[str, None]:
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://www.instagram.com/reel/C_Ea4kIobB8/',
            'sec-ch-prefers-color-scheme': 'dark',
            'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-full-version-list': '"Google Chrome";v="129.0.6668.60", "Not=A?Brand";v="8.0.0.0", "Chromium";v="129.0.6668.60"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        }

        data = {
            'av': '0',
            '__d': 'www',
            '__user': '0',
            '__a': '1',
            '__req': '5',
            '__hs': '19994.HYP:instagram_web_pkg.2.1..0.0',
            'dpr': '1',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'PolarisPostActionLoadPostQueryQuery',
            'variables': '{"shortcode":"' + shortcode + '","fetch_tagged_user_count":null,"hoisted_comment_id":null,"hoisted_reply_id":null}',
            'server_timestamps': 'true',
            'doc_id': '8845758582119845',
        }
        response = requests.post('https://www.instagram.com/graphql/query', headers=headers, data=data,
                                 proxies=self.proxy)
        try:
            return response.json()['data']['xdt_shortcode_media']['video_url']
        except Exception as e:
            print('Query was not successful', e)

    def download_reel(self, instagram_url: str) -> Union[io.BytesIO, None]:
        if time.time() - self.last_called < self.cooldown_time:
            return
        self.last_called = time.time()
        shortcode = self.extract_shortcode_from_url(instagram_url)
        if not shortcode:
            return
        video_url = self.fetch_instagram_reel_data(shortcode)
        if not video_url:
            return
        response = requests.get(video_url, proxies=self.proxy, stream=True)
        if response.status_code == 200:
            return io.BytesIO(response.content)


reel_downloader = ReelsDownloader()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message: discord.Message):
    if client.user == message.author:
        return
    if message.content.startswith('https://www.instagram.com/reel'):
        result = reel_downloader.download_reel(message.content)
        if result:
            await message.channel.send(file=discord.File(result, filename='reel.mp4'))


if __name__ == "__main__":
    client.run('')
