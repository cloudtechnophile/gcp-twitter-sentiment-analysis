import datetime
import json
import time
import os
import tweepy
import emoji
import re

from google.cloud import pubsub
from tweepy.streaming import StreamListener

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="diag-gcp-training-b22e07895f4e.json"

# Config

publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path(os.environ["PROJECT_ID"], os.environ["TOPIC_NAME"])


# Load in a json file with your Tweepy API credentials
with open("account.json") as json_data:
    account_data = json.load(json_data)

# Select the account you want to listen with
listener_1 = account_data["user_1"]

# Authenticate to the API
auth = tweepy.OAuthHandler(account_data["consumer_key"], account_data["consumer_secret"])
auth.set_access_token(account_data["access_token"], account_data["access_token_secret"])

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=False)

# Define the list of terms to listen to
lst_hashtags = ["#Israel","#Palestine"]

# Method to push messages to pubsub
def reformat_tweet(tweet):
    x = tweet

    processed_doc = {
        "id": x["id"],
        "lang": x["lang"],
        "retweeted_id": x["retweeted_status"]["id"] if "retweeted_status" in x else None,
        "favorite_count": x["favorite_count"] if "favorite_count" in x else 0,
        "retweet_count": x["retweet_count"] if "retweet_count" in x else 0,
        "coordinates_latitude": x["coordinates"]["coordinates"][0] if x["coordinates"] else 0,
        "coordinates_longitude": x["coordinates"]["coordinates"][0] if x["coordinates"] else 0,
        "place": x["place"]["country_code"] if x["place"] else None,
        "user_id": x["user"]["id"],
        "created_at": time.mktime(time.strptime(x["created_at"], "%a %b %d %H:%M:%S +0000 %Y"))
    }

    if x["entities"]["hashtags"]:
        processed_doc["hashtags"] = [{"text": y["text"], "startindex": y["indices"][0]} for y in
                                     x["entities"]["hashtags"]]
    else:
        processed_doc["hashtags"] = []

    if x["entities"]["user_mentions"]:
        processed_doc["usermentions"] = [{"screen_name": y["screen_name"], "startindex": y["indices"][0]} for y in
                                         x["entities"]["user_mentions"]]
    else:
        processed_doc["usermentions"] = []

    if "extended_tweet" in x:
        processed_doc["text"] = x["extended_tweet"]["full_text"]
    elif "full_text" in x:
        processed_doc["text"] = x["full_text"]
    else:
        processed_doc["text"] = x["text"]

    return processed_doc

def write_to_pubsub(data):
   try:
        if data["lang"] == "en":
            tweet_text = data["text"]
            tweet_text = ' '.join(re.sub("(@[A-Za-z0-9]+)|(#[A-Za-z0-9]+)", " ", tweet_text).split())
            tweet_text = ' '.join(re.sub("(\w+:\/\/\S+)", " ", tweet_text).split())
            tweet_text = emoji.demojize(tweet_text)
            tweet_text = ' '.join(re.sub("[\.\,\!\?\:\;\-\=\'\"]", " ", tweet_text).split())
            tweet_text = re.sub('RT ','',tweet_text)
            tweet_text = re.sub("n't",' not',tweet_text)
            tweet_text = re.sub("'ve", ' have', tweet_text)
            tweet_text = re.sub("'s",' has',tweet_text)
            tweet_text = tweet_text.lower()
            publisher.publish(topic_path, data=json.dumps({
                "text": tweet_text,
                "user_id": data["user_id"],
                "id": data["id"],
                "posted_at": datetime.datetime.fromtimestamp(data["created_at"]).strftime('%Y-%m-%d %H:%M:%S')
        }).encode("utf-8"), tweet_id=str(data["id"]).encode("utf-8"))
                
   except Exception as e:
         raise


# Custom listener class
class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just pushes tweets to pubsub
    """

    def __init__(self):
        super(StdOutListener, self).__init__()
        self._counter = 0

    def on_status(self, data):
        write_to_pubsub(reformat_tweet(data._json))
        print(reformat_tweet(data._json))
        self._counter += 1
        return True

    def on_error(self, status):
        if status == 420:
            print("rate limit active")
            return False


# Start listening
l = StdOutListener()
stream = tweepy.Stream(auth, l, tweet_mode='extended')
stream.filter(track=lst_hashtags)
