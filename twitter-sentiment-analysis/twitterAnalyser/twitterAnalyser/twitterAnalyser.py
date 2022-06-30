
import datetime
import os
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types


class MyOptions(PipelineOptions):
  @classmethod
  def _add_argparse_args(cls, parser):

    parser.add_value_provider_argument(
                        '--inputSubscription',
                        type=str,
                        required = False,
                        default='projects/melodic-media-312309/topics/twitter-stream',
                        help='Location to stage temporary files'
                        )
    parser.add_value_provider_argument(
                        '--output_table',
                        type=str,
                        required = False,
                        default='projects/melodic-media-312309/topics/twitter-stream',
                        help='Location to stage temporary files'
                        )
    parser.add_value_provider_argument (
                        '--serviceAccount',
                        type=str,
                        required = False,
                        default='realtime-data-pipeline@diag-gcp-training.iam.gserviceaccount.com',
                        help='Location to stage temporary files'
                        )


RUNNER_TYPE = 'DataFlowRunner'
PROJECT_ID = 'melodic-media-312309'
BUCKET = 'twitter-resources-bucket'

version = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

pipeline_options = PipelineOptions()
custom_options = pipeline_options.view_as(MyOptions)

google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)
google_cloud_options.project = PROJECT_ID
google_cloud_options.job_name = 'terr-v{}'.format(version)
google_cloud_options.staging_location = 'gs://{}/staging'.format(BUCKET)
google_cloud_options.temp_location  = 'gs://{}/tmp'.format(BUCKET)
pipeline_options.view_as(StandardOptions).runner = RUNNER_TYPE
pipeline_options.view_as(StandardOptions).streaming = True

#installing packages used in process
setup_options = pipeline_options.view_as(SetupOptions)
setup_options.setup_file = './setup.py'
setup_options.save_main_session = True

def parse_pubsub(line):
    import json
    record = json.loads(line)
    return [record['text'], record['posted_at']]

table_schema = 'tweet_text:STRING,sentiment_score:FLOAT,sentiment_magnitude:FLOAT,posted_at:STRING'

class splitAnalysis(beam.DoFn):
    def process(self,element):
        tweet_text = element[0]
        schema = table_schema
        client = language.LanguageServiceClient()
        document = types.Document(content=tweet_text, type=enums.Document.Type.PLAIN_TEXT)
        sent_analysis = client.analyze_sentiment(document=document)
        sentiment = sent_analysis.document_sentiment
        data = [element[0], sentiment.score, sentiment.magnitude, element[1].encode('utf-8')]
        header = map(lambda x: x.split(':')[0], schema.split(','))
        return [dict(zip(header, data))]

def run():

   with beam.Pipeline(options=pipeline_options) as p:
            # Read the pubsub topic into a PCollection.
         (p | beam.io.ReadFromPubSub(subscription=str(custom_options.inputSubscription))
            | beam.Map(parse_pubsub)
            | beam.ParDo(splitAnalysis())
            | beam.io.WriteToBigQuery(str(custom_options.output_table),
                                        schema=table_schema,
                                        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                                        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND))