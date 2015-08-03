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

To query the metadata store do a GET on /resources/<BQ query string>, where BQ query string is a BigQuery query string that follows this BQ table schema:

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
            "mode": "required"
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

Follow [these instructions](https://github.com/google/cluster-insight) to install and run the Cluster Insight context graph collector for Kubernetes. We will store this context metadata in the metadata store, and allow BigQuery queries against it.

Build and upload a Docker image by executing the following commands in the `metad` directory. Replace `PROJECT` with the ID of the project that you want to instrument.

    docker build -t gcr.io/PROJECT/metad .
    gcloud docker push gcr.io/PROJECT/metad

There are two instances of the project ID in the file `metad-controller.yaml`. Update both to refer to your own project, and then create the `metad` replication controller and service as follows:

    kubectl create -f metad-controller.yaml
    kubectl create -f metad-service.yaml

Run the following command, and look for the value of `LoadBalancer Ingress`:

    kubectl describe service metad

Calling that IP address `LBIP`, visit `http://LBIP:5000/` in your browser and confirm that you get a help message.

To load all of the resource metadata for your project into BigQuery, first execute the following command to create the required BigQuery database:

    bq mk meta

Then visit `http://LBIP:5000/reset` to create the BigQuery table `meta.resources`, followed by `http://LBIP:5000/update` to fill it.

Now try the endpoints `http://LBIP:5000/resources` and `http://LBIP:5000/context`.
