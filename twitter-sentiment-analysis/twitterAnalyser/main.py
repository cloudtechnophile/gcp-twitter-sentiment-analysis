from __future__ import absolute_import
import logging

from twitterAnalyser import twitterAnalyser



if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  twitterAnalyser.run()
