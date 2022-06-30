#!/bin/sh
PROJECT=melodic-media-312309
BUCKET=twitter-resources-bucket
TOPIC=twitter-stream
REGION=europe-west1
export PROJECT_ID=$PROJECT
export BUCKET=$BUCKET
export TOPIC_NAME=$TOPIC
export REGION=$REGION
sudo apt-get  update
sudo apt-get -y install python3-distutils
sudo curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
sudo python3 get-pip.py
pip install tweepy --user
pip install emoji --user
pip install apache-beam[gcp]==2.23.0 --user
pip install google-cloud-language --user
sudo apt-get -y install google-cloud-sdk
sudo apt-get -y install zip unzip
sudo python3 -m pip install google-cloud-pubsub
gsutil cp gs://twitter-resources-bucket/resources.zip resources.zip
unzip -o resources.zip
export GOOGLE_APPLICATION_CREDENTIALS=melodic-media-312309-9c418a501ed2.json
gsutil cp gs://twitter-resources-bucket/twitterAnalyserCode.zip twitterAnalyserCode.zip
mkdir twitterAnalyserCode
unzip -o twitterAnalyserCode.zip -d twitterAnalyserCode
cd twitterAnalyserCode
chmod 777 main.py
python3 -m main \
--runner TemplatingDataFlowPipelineRunner \
--inputSubscription 'projects/melodic-media-312309/subscriptions/twitter-subscription' \
--output_table 'melodic-media-312309:TWITTER_DATA.TWEET_DATA' \
--region $REGION \
--project $PROJECT_ID \
--staging_location 'gs://twitter-resources-bucket/staging' \
--temp_location 'gs://twitter-resources-bucket/tmp' \
--serviceAccount=790982757019-compute@developer.gserviceaccount.com \
--setup_file '~/twitterAnalyserCode/setup.py' \
--template_location 'gs://twitter-resources-bucket/templates/tweetAnalysertemplate'
cd ..
gsutil cp gs://twitter-resources-bucket/twitterListenerCode.zip twitterListenerCode.zip
mkdir twitterListenerCode
cp melodic-media-312309-9c418a501ed2.json twitterListenerCode
cp account.json twitterListenerCode
unzip -o twitterListenerCode.zip -d twitterListenerCode
cd twitterListenerCode
chmod 777 twitterListener.py
nohup python3 twitterListener.py

