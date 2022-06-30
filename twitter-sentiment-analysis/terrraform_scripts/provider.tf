provider "google" {
  credentials = file("../resources/melodic-media-312309-9c418a501ed2.json") //Service account key file to execute the scripts from local filesystem
  project     = "melodic-media-312309"
  region      = "europe-west1"
}
