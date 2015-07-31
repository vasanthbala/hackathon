## Metadata store

This is a simple Web Service that provides an API for clients to store, query and retrieve resource metadata.

To create or update metadata do a POST to the /resources endpoint. The POST body must have this JSON format (only the 'id' attribute is mandatory):

```javascript
{
   'resources': [
       {
          'id': <unique resource ID>,
          'timestamp': <RFC339 timestamp when this resource metadata was changed/created>,
          'properties': <JSON dict object>,
          'relations': {
              <type>: [ <target id>, <target id>, ... ],
              <type>: [ <target id>, <target id>, ... ],
              ...
          }
       },
       ...
   ]
}
```

To fetch summarized metadata about all resources do a GET on /resources. To get detailed metadata about a specific resource do a GET on /resources/<id>.

To query the metadata store do a GET on /resources/<BQ query string>, where BQ query string is a Big Query query string that follows this BQ table schema:

```javascript
resource_schema = {
    'fields' : [
        {
            "name": "timestamp",
            "type": "timestamp",
            "mode": "nullable"
        },    
        {
            "name": "properties",
            "type": "string",
            "mode": "nullable"
        },
        {
            "name": "type",
            "type": "string",
            "mode": "nullable"
        },
        {
            "name": "annotations",
            "type": "string",
            "mode": "nullable",
        },
        {
            "name": "id",
            "type": "string",
            "mode": "nullable"
        },
        {
            "name": "relations",
            "type": "record",
            "mode": "repeated",
            "fields": [
                {
                    "name": "type",
                    "type": "string",
                    "mode": "nullable"
                },
                {
                    "name": "targets",
                    "type": "string",
                    "mode": "repeated"
                }
            ]
        }
    ]
}
```

To see a chord diagram of the context graph of all resources and relations, do a GET on /context.

## How to run this Web Server

SSH into the kubernetes-master. Do a git clone to get the hackathon GitHub directory locally. The sources for the web server are under ./hackathon/metad.

Follow [these instructions](https://github.com/google/cluster-insight) to install and run the Cluster Insight context graph collector for Kubernetes. We will store this context metadata in the metadata store, and allow Big Query queries against it.

Edit the constants at the top of hackathon/metad/metadata-service.py so they refer to the correct ID, NUMBER and ZONE of the project you want to monitor. This version is hardwired to provide a metadata storage service for one project only. Also check if the CLUSTER_INSIGHT_URL works when you call it locally on the kubernetes-master using curl.

From the hackathon/metad directory type ```python metadata-service.py```. If you get a permissions error, you need to download a client-secrets.json file from the project you are monitoring, then set the env variable GOOGLE_APPLICATION_CREDENTIALS to the path of the client-secrets.json file.

