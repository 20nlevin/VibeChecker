import slack
import requests
import random
import os
from bs4 import BeautifulSoup
from ibm_watson import ToneAnalyzerV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

user_emotions = {}

ibm_api = os.getenv("IBM_API_KEY")
ibm_url = os.getenv("IBM_API_URL")

r = requests.get('https://www.google.com/search?q=dog&safe=strict&sxsrf=ACYBGNSU9lL9K9gT0p9BRINO9veZfPUR0Q:1581651025071&source=lnms&tbm=isch&sa=X&ved=2ahUKEwib4IecjdDnAhWMd98KHZFwDGwQ_AUoAXoECBIQAw&biw=1280&bih=578&dpr=2.5')
images = BeautifulSoup(r.text, "html.parser").find_all("img")
img_type = "dog"
image_links = []
for img in images:
    if img.get("src") and img.get("src")[:4] == "http":
        image_links.append(img.get("src"))


authenticator = IAMAuthenticator(ibm_api)
tone_analyzer = ToneAnalyzerV3(
    version='2017-09-21',
    authenticator=authenticator
)

tone_analyzer.set_service_url(ibm_url)

@slack.RTMClient.run_on(event='message')
def say_hello(**payload):
    global img_type
    global image_links
    data = payload['data']
    web_client = payload['web_client']
    if "user" in data:
        user = data['user']
        if user not in user_emotions.keys():
            user_emotions[user] = []
    else:
        user = "vibe_bot"
    if user != "vibe_bot":
        tones = tone_analyzer.tone(data.get("text")).get_result()["document_tone"]["tones"]
        tone_names = []

        if data.get("text").lower() == "!check":
            udata = {}
            u = user_emotions.get(user)
            for x in u:
                if x in udata.keys():
                    udata[x] += 1
                else:
                    udata[x] = 1
            msg = ""
            for key, value in udata.items():
                msg += key + ": " + "%.2f%%\n" % ((int(value)/len(u))*100)
            web_client.chat_postMessage(
                channel=data['channel'],
                text=msg
            )
        elif data.get("text").lower()[:4] == "!set":
            img_type = " ".join(data.get("text").split(" ")[1:])
            r = requests.get(
                'https://www.google.com/search?q=' + img_type + '&safe=strict&sxsrf=ACYBGNSU9lL9K9gT0p9BRINO9veZfPUR0Q:1581651025071&source=lnms&tbm=isch&sa=X&ved=2ahUKEwib4IecjdDnAhWMd98KHZFwDGwQ_AUoAXoECBIQAw&biw=1280&bih=578&dpr=2.5')
            images = BeautifulSoup(r.text, "html.parser").find_all("img")
            image_links = []
            for img in images:
                if img.get("src") and img.get("src")[:4] == "http":
                    image_links.append(img.get("src"))
            web_client.chat_postMessage(
                channel=data["channel"],
                text="Set your preferred image to " + img_type + "s."
            )
        else:
            for i in tones:
                tone_names.append(i["tone_name"])
                user_emotions[user].append(i["tone_name"])
            if "Anger" in tone_names:
                channel_id = data['channel']
                web_client.chat_postMessage(
                    channel=channel_id,
                    blocks= [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Hey, it looks like you're getting a little heated. Here's a picture of a " + img_type + " to calm you down.\n"
                        },
                        "accessory": {
                            "type": "image",
                            "image_url": random.choice(image_links),
                            "alt_text": img_type.title() + " image"
                    }}]
                )

slacktoken = os.getenv("SLACK_API_TOKEN")
rtm_client = slack.RTMClient(token=slacktoken)
rtm_client.start()
