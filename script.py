import textwrap
import requests
import sqlite3
import private.config as config

from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageFont
from imgurpython import ImgurClient

class InstaBot:
    def __init__(self):
        self.connection = sqlite3.connect('private/data.db')
        self.cursor = self.connection.cursor()
        self.font = ImageFont.truetype("private/courier_prime.ttf", 120)
        self.template = Image.open('private/template.png')
        self.dim, _ = self.template.size
        self.wrapper = textwrap.TextWrapper(width=13)
        self.client = ImgurClient(config.client_id, config.client_secret)
        self.caption_template = Path('private/caption_template.txt').read_text().replace('#', '%23')
        self.access_token = Path('private/access_token.txt').read_text()


    # Generate Img from Template.png using DB contents
    def generate_images(self):
        self.cursor.execute("SELECT * FROM posts WHERE status = 0")
        row = self.cursor.fetchone()
        if row is None:
            exit("Database empty")
        i_id = row[0]
        msg = row[1]
        caption = row[2]
        wrapped_msg = ""
        paragraph = self.wrapper.wrap(msg)

        for ii in paragraph[:-1]:
            wrapped_msg = wrapped_msg + ii + '\n'
        wrapped_msg += paragraph[-1]

        img = ImageChops.duplicate(self.template)

        draw = ImageDraw.Draw(img)
        w, h = draw.textsize(wrapped_msg, font=self.font)

        draw.text(((self.dim-w)/2,(self.dim-h)/2), wrapped_msg, font=self.font, fill='white', align='center')
        img.save(f"img/{i_id}.png", "PNG")
        return i_id, caption


    # Upload img to Imgur and return link
    def upload_imgur(self, i):
        res = self.client.upload_from_path(f"img/{i}.png")
        print(res)
        return res['link']


    # Renew FB Access Token (60 Day Expiry)
    def renew_token(self):
        r_at = requests.get(f"https://graph.facebook.com/v11.0/oauth/access_token?grant_type=fb_exchange_token&client_id={config.fb_id}&client_secret={config.fb_secret}&fb_exchange_token={self.access_token}")
        if r_at.status_code == 200:
            f = open('private/access_token.txt', 'w')
            f.write(r_at.json()['access_token'])
            f.close()


    # Upload image to Facebook via Imgur Link & Add Caption
    def upload_img(self, i, ig_id, url, caption):
        r1 = requests.post(f"https://graph.facebook.com/v11.0/{ig_id}/media?image_url={url}&caption={caption}\n\n{self.caption_template}&access_token={self.access_token}")
        if r1.status_code != 200:
            exit(r1.json())

        return r1.json()['id']


    # Publish Post 
    def post_publish(self, ig_id, creation_id):
        r2 = requests.post(f"https://graph.facebook.com/v11.0/{ig_id}/media_publish?creation_id={creation_id}&access_token={self.access_token}")

        if r2.status_code != 200:
            exit(r2.json())

    
    # Set status of row in DB to 1 to indicate that it has been posted!
    def update_status(self, i):
        update_query = f"UPDATE posts SET status = 1 WHERE id = {i}"
        self.cursor.execute(update_query)
        self.connection.commit()


    # GRAPH API CALLS
    def post_image(self, url, i, caption):
        self.renew_token()
        post_id = self.upload_img(i, config.ig_id, url, caption)
        self.post_publish(config.ig_id, post_id)
        self.update_status(i)
        print("Done")
    

    # Run whole procedure
    def run(self):
        img_id, caption = self.generate_images()
        #link = self.upload_imgur(img_id)
        #self.post_image(link, img_id, caption)
        print("Done")

if __name__ == '__main__':
    bot = InstaBot()
    bot.run()
