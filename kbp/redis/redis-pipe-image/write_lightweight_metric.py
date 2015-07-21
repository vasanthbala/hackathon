#!/usr/bin/python
"""Writes and reads a lightweight custom metric.

This is an example of how to use the Google Cloud Monitoring API to write
and read a lightweight custom metric. Lightweight custom metrics have no
labels and you do not need to create a metric descriptor for them.

Prerequisites: Run this Python example on a Google Compute Engine virtual
machine instance that has been set up using these intructions:
https://cloud.google.com/monitoring/demos/setup_compute_instance.

Typical usage: Run the following shell commands on the instance:
    python write_lightweight_metric.py
    python write_lightweight_metric.py
    python write_lightweight_metric.py
"""

import os
import time

from apiclient.discovery import build
import httplib2
from oauth2client.gce import AppAssertionCredentials

CUSTOM_METRIC_NAME = "custom.cloudmonitoring.googleapis.com/pid"


def GetProjectId():
  """Read the numeric project ID from metadata service."""
  http = httplib2.Http()
  resp, content = http.request(
      ("http://metadata.google.internal/"
       "computeMetadata/v1/project/numeric-project-id"),
      "GET", headers={"Metadata-Flavor": "Google"})
  if resp["status"] != "200":
    raise Exception("Unable to get project ID from metadata service")
  return content


def GetNowRfc3339():
  """Give the current time formatted per RFC 3339."""
  return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main():
  project_id = GetProjectId()

  # Create a cloudmonitoring service to call. Use OAuth2 credentials.
  credentials = AppAssertionCredentials(
      scope="https://www.googleapis.com/auth/monitoring")
  http = credentials.authorize(httplib2.Http())
  service = build(serviceName="cloudmonitoring", version="v2beta2", http=http)

  # Set up the write request.
  now = GetNowRfc3339()
  desc = {"project": project_id,
          "metric": CUSTOM_METRIC_NAME}
  point = {"start": now,
           "end": now,
           "doubleValue": os.getpid()}
  print "Writing %d at %s" % (point["doubleValue"], now)

  # Write a new data point.
  try:
    write_request = service.timeseries().write(
        project=project_id,
        body={"timeseries": [{"timeseriesDesc": desc, "point": point}]})
    _ = write_request.execute()  # Ignore the response.
  except Exception as e:
    print "Failed to read custom metric data: exception=%s" % e
    raise  # propagate exception

  # Read all data points from the time series.
  # When a custom metric is created, it may take a few seconds
  # to propagate throughout the system. Retry a few times.
  print "Reading data from custom metric timeseries..."
  read_request = service.timeseries().list(
      project=project_id,
      metric=CUSTOM_METRIC_NAME,
      youngest=now)
  start = time.time()
  while True:
    try:
      read_response = read_request.execute()
      for point in read_response["timeseries"][0]["points"]:
        print "  %s: %s" % (point["end"], point["doubleValue"])
      break
    except Exception as e:
      if time.time() < start + 20:
        print "Failed to read custom metric data, retrying..."
        time.sleep(3)
      else:
        print "Failed to read custom metric data, aborting: exception=%s" % e
        raise  # propagate exception


if __name__ == "__main__":
  main()
