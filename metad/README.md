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

SSH into the kubernetes-master. Make sure you have the Cluster Insight data collector running there. Do a git clone to get the hackathon/metad directory locally. From this directory type ```python metadata-service.py```. If you get a permissions error, you need to download a client-secrets.json file from the project you are monitoring, then set the env variable GOOGLE_APPLICATION_CREDENTIALS to the path of the client-secrets.json file.

