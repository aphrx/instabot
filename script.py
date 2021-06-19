import textwrap
import requests
import sqlite3
import private.config as config

from PIL import Image, ImageDraw, ImageChops, ImageFont
from imgurpython import ImgurClient

class InstaBot:
    def __init__(self):
        self.connection = sqlite3.connect('private/data.db')
        self.cursor = self.connection.cursor()
        self.font = ImageFont.truetype("public/courier_prime.ttf", 120)
        self.template = Image.open('public/template.png')
        self.dim, _ = self.template.size
        self.wrapper = textwrap.TextWrapper(width=13)
        self.client = ImgurClient(config.client_id, config.client_secret)

    def generate_images(self):
        self.cursor.execute("SELECT * FROM posts")
        rows = self.cursor.fetchall()

        for i, row in enumerate(rows):
            print(row)
            if row[3] == 0:
                msg = row[1]
                wrapped_msg = ""
                paragraph = self.wrapper.wrap(msg)

                for ii in paragraph[:-1]:
                    wrapped_msg = wrapped_msg + ii + '\n'
                wrapped_msg += paragraph[-1]

                img = ImageChops.duplicate(self.template)

                draw = ImageDraw.Draw(img)
                w, h = draw.textsize(wrapped_msg, font=self.font)

                draw.text(((self.dim-w)/2,(self.dim-h)/2), wrapped_msg, font=self.font, fill='white', align='center')
                img.save(f"img/{i}.png", "PNG")

    def upload_image(self, i):
        return self.client.upload_from_path(f"img/{i}.png")['link']

    def post_image(self, url):
        r = requests.get(f"https://graph.facebook.com/v11.0/{config.uid}?fields=instagram_business_account&access_token={config.access_token}")
        if r.status_code != 200:
            print(r.json())
            return
        
        ig_id = r.json()['instagram_business_account']['id']
        r1 = requests.post(f"https://graph.facebook.com/v11.0/{ig_id}/media?image_url={url}&caption=Test&access_token={config.access_token}")

        if r1.status_code != 200:
            print(r1.json())
            return

        creation_id = r1.json()['id']

        r2 = requests.post(f"https://graph.facebook.com/v11.0/{ig_id}/media_publish?creation_id={creation_id}&access_token={config.access_token}")

        if r2.status_code != 200:
            print(r2.json())

        print("Done")
        return

    def run(self):
        self.generate_images()
        self.post_image(self.upload_image())

if __name__ == '__main__':
    bot = InstaBot()
    bot.run()