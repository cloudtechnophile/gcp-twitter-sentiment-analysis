//Variable used to load the resources and source code files from local file system to storage bucket

variable "twitter-resources" {
  default = [
    "twitterAnalyserCode.zip",
    "twitterListenerCode.zip",
    "resources.zip"]
}