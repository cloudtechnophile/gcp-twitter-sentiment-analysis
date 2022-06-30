//Twitter sentiment analysis data pipeline on GCP

//Creates new topic to write the streaming data

resource "google_pubsub_topic" "topic-creation" {
  name = "twitter-stream"

  labels = {
    twitter = "realtime"
  }
}

//Creates a subscriber to read the data from the pub/sub topic

resource "google_pubsub_subscription" "tweet-subscriber" {
  project = "melodic-media-312309"
  name    = "twitter-subscription"
  topic   = google_pubsub_topic.topic-creation.name
}

//Creates a storage bucket to store the code as well as the resources required for the pipeline execution

resource "google_storage_bucket" "bucket" {
  name     = "twitter-resources-bucket"
  location = "EU"
  force_destroy = true
}

//Todo: Make it to single resource using zipping, if this is changed please change the start up script accordingly

//Creates file archives of the source code and resources


data "archive_file" "twitterAnalyserCode" {
  type        = "zip"
  source_dir = "/Users/jakeersyed/Desktop/code/twitter-realtime-sentiment-analysis-data-pipeline/twitter-sentiment-analysis/twitterAnalyser" //Please change the paths accordingly if you are using linux file system
  output_path = "twitterAnalyserCode.zip"
}

data "archive_file" "twitterListenerCode" {
  type        = "zip"
  source_dir = "/Users/jakeersyed/Desktop/code/twitter-realtime-sentiment-analysis-data-pipeline/twitter-sentiment-analysis/twitterListener"  //Please change the paths accordingly if you are using linux file system
  output_path = "twitterListenerCode.zip"
}

data "archive_file" "resources" {
  type        = "zip"
  source_dir = "/Users/jakeersyed/Desktop/code/twitter-realtime-sentiment-analysis-data-pipeline/twitter-sentiment-analysis/resources"   //Please change the paths accordingly if you are using linux file system
  output_path = "resources.zip"
}

//Copies the source code and resources to the storage bucket created in the previous steps


resource "google_storage_bucket_object" "AnalyserCode" {
  name   = "twitterAnalyserCode.zip"
  source = element(var.twitter-resources, 0)
  bucket = google_storage_bucket.bucket.name
}

resource "google_storage_bucket_object" "ListenerCode" {
  name   = "twitterListenerCode.zip"
  source = element(var.twitter-resources, 1)
  bucket = google_storage_bucket.bucket.name
}

resource "google_storage_bucket_object" "resource-data" {
  name   = "resources.zip"
  source = element(var.twitter-resources, 2)
  bucket = google_storage_bucket.bucket.name
}


//Creates a compute instance to execute the twitter data scraping script (twitterListener.py) to extract the data from tweepy API filtering base up on the list of hashtags

resource "google_compute_instance" "twitter-instance" {
  name         = "twitter-scraper"
  machine_type = "n1-standard-1"
  zone         = "europe-west3-c"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-10"
    }
  }

  network_interface {
   
    network = "default"
  
    access_config {
     
       network_tier = "PREMIUM"
	
    }
  }

  metadata_startup_script = file("../resources/start_script.sh") //Executes start up script which contains the command line arguments to execute the twitterListener code
 
  service_account {
     scopes = ["userinfo-email", "compute-ro", "storage-ro", "pubsub" , "storage-full" , "service-control" , "service-management" , "monitoring-write" , "monitoring"]
  }

}

//Creates a bigquery dataset to write the data post sentiment analysis

resource "google_bigquery_dataset" "twitter-dataset" {
  dataset_id                  = "TWITTER_DATA"
  friendly_name               = "tweetdata"
  description                 = "This is twitter sentiment analysis dataset"
  location                    = "EU"
  delete_contents_on_destroy  = true
  default_table_expiration_ms = 3600000

}


//Launches a dataflow job to perform the sentiment analysis on the twitter data scraped and posted to pubsub topics

resource "google_dataflow_job" "twitter-sentiment-analysis-job" {
  name              = "twitter-sentiment-analysis-job"
  template_gcs_path = "gs://twitter-resources-bucket/templates/tweetAnalysertemplate"
  temp_gcs_location = "gs://twitter-resources-bucket/tmp/"
  zone            = "us-central1-a"
  parameters = {
    inputSubscription = "projects/melodic-media-312309/subscriptions/twitter-subscription"
    output_table = "melodic-media-312309:TWITTER_DATA.TWEET_DATA"
    runner = "DataFlowRunner"
    project = "melodic-media-312309"
    staging_location = "gs://twitter-resources-bucket/staging/"
    setup_file = "gs://twitter-resources-bucket/setup.py"
    }
  depends_on = [time_sleep.wait_5_minutes]
}

resource "time_sleep" "wait_5_minutes" {
  depends_on = [google_bigquery_dataset.twitter-dataset]
  create_duration = "5m"
}