import os
import httplib2
import sys
import requests
import simplejson as json
import flask
from collections import defaultdict
import datetime

from apiclient.discovery import build
from oauth2client.client import GoogleCredentials
from oauth2client.gce import AppAssertionCredentials
from httplib2 import Http
from apiclient.errors import HttpError


PROJECT_ID = 'cooltool-1009'
PROJECT_NUMBER = '518787634948'
DATASET_ID = 'meta'
TABLE_ID = 'resources'
CLUSTER_INSIGHT_URL = 'http://localhost:8080/api/v1/proxy/namespaces/default/services/cluster-insight:cluster-insight/cluster'
#CLUSTER_INSIGHT_URL = 'http://199.223.236.105:5555/cluster'

bq_service = None
app = flask.Flask(__name__)

resource_cache = None

def context_to_bqjson(context):
    # convert into a dict of resources
    resource_dict = {}
    for resource in context['resources']:
        resource['properties'] = json.dumps(resource['properties'])
        resource['annotations'] = json.dumps(resource['annotations'])
        resource['relations'] = defaultdict(list)
        resource_dict[resource['id']] = resource
    # add relations to each resource, keyed by relation type
    for relation in context['relations']:
        resource = resource_dict[relation['source']]
        relation_type = relation['type']
        resource['relations'][relation_type].append(relation['target'])
    # convert resource_dict into a BQ json string
    resource_array = []
    for resource in resource_dict.values():
        relations_array = []
        for rtype, rtargets in resource['relations'].iteritems():
            relations_array.append({'type': rtype, 'targets': rtargets})
        resource['relations'] = relations_array
        row = {
            'insertId': '%s-%s' % (resource['id'], resource['timestamp']),
            'json': resource
        }
        resource_array.append(row)
    return resource_array


@app.route("/")
def help():
    api_help = [
        "GET  /\t\t\t\t\tShow this help message.",
        "GET  /resources\t\t\tList all resources.",
        "GET  /resource/(id)\t\tShow detailed metadata for a specific resource.",
        "GET  /update\t\t\tAutomatically update resource metadata from available sources.",
        "GET  /query/(BQ-query)\tQuery the metadata (Big Query query on dataset meta.resources).",
        "\t\t\t\t\t\tExample: \"SELECT id FROM meta.resources",
        "\t\t\t\t\t\t\t\t\tWHERE type='Container'",
        "\t\t\t\t\t\t\t\t\tAND properties CONTAINS 'redis-master'\"",
        " ",
        "POST /resources\t\t\tManually update resource metadata with the given payload.",
        "\t\t\t\t\t\tPayload schema:",
        "\t\t\t\t\t\t{",
        "\t\t\t\t\t\t\t'resources': [",
        "\t\t\t\t\t\t\t\t{",
        "\t\t\t\t\t\t\t\t\t'id': (string),",
        "\t\t\t\t\t\t\t\t\t'properties': (dict),",
        "\t\t\t\t\t\t\t\t\t'relations': (type-to-targets-dict),",
        "\t\t\t\t\t\t\t\t},",
        "\t\t\t\t\t\t\t\t...",
        "\t\t\t\t\t\t\t]",
        "\t\t\t\t\t\t}"
    ]
    return '\n'.join(api_help)


@app.route("/reset", methods=["GET"])
def reset_resources():
    # replace the current meta.resources table with a new empty table
    try:
        list_response = bq_service.tables().list(projectId=PROJECT_NUMBER, datasetId=DATASET_ID).execute()
        if list_response['totalItems'] > 0:
            full_table_id = '%s:%s.%s' % (PROJECT_ID, DATASET_ID, TABLE_ID)
            for table in list_response['tables']:
                if table['id'] == full_table_id:
                    # table already exists, need to delete it first
                    print 'Deleting existing table'
                    delete_response = bq_service.tables().delete(
                        projectId=PROJECT_NUMBER, datasetId=DATASET_ID, tableId=TABLE_ID).execute()
        # insert a new empty table
        with open('resource.schema', 'r') as fp:
            resource_schema = json.loads(fp.read())
        insert_data = {
            'schema': resource_schema,
            'tableReference': {
                'projectId': PROJECT_NUMBER,
                'datasetId': DATASET_ID,
                'tableId': TABLE_ID
            }
        }
        print 'Creating new table'
        insert_response = bq_service.tables().insert(
            projectId=PROJECT_NUMBER, datasetId=DATASET_ID, body=insert_data).execute()
        return  flask.jsonify(insert_response)
    except HttpError as err:
        return err.content


@app.route("/update", methods=["GET"])
def update_resources_from_context():
    # get a fresh context snapshot and update the BQ meta.resources table
    response = requests.get(CLUSTER_INSIGHT_URL)
    context = response.json()
    resource_array = context_to_bqjson(context)
    try:
        update_data = {
            'ignoreUnknownValues': True,
            'rows': resource_array
        }
        update_response = bq_service.tabledata().insertAll(
            projectId=PROJECT_NUMBER, datasetId=DATASET_ID, tableId=TABLE_ID, 
            body=update_data).execute()
        if 'insertErrors' in update_response:
            return  flask.jsonify(update_response)
        else:
            return 'Successfully updated resource metadata from Cluster-Insight context.'
    except HttpError as err:
        return err.content


@app.route("/resources", methods=["POST"])
def update_resources():
    # get a fresh context snapshot and update the BQ meta.resources table
    resources = flask.request.get_json()
    assert 'resource' in resources
    resource_array = []
    for r in resources['resources']:
        assert 'id' in r
        if 'properties' in r:
            assert type(r['properties']) is dict
            r['properties'] = json.dumps(r['properties'])
        if 'annotations' in r:
            assert type(r['annotations']) is dict
            r['annotations'] = json.dumps(r['annotations'])
        if 'relations' in r:
            assert type(r['relations']) is dict
            for rtype, rtargets in r['relations'].iteritems():
                relations_array.append({'type': rtype, 'targets': rtargets})
            r['relations'] = relations_array
        if 'timestamp' not in r:
            r['timestamp'] = datetime.datetime.utcnow().isoformat("T") + "Z"
        row = {
            'insertId': '%s-%s' % (r['id'], r['timestamp']),
            'json': r
        }
        resource_array.append(row)
    try:
        update_data = {
            'ignoreUnknownValues': True,
            'rows': resource_array
        }
        update_response = bq_service.tabledata().insertAll(
            projectId=PROJECT_NUMBER, datasetId=DATASET_ID, tableId=TABLE_ID, 
            body=update_data).execute()
        if 'insertErrors' in update_response:
            return  flask.jsonify(update_response)
        else:
            resource_cache = None
            return 'Successfully updated resource metadata.'
    except HttpError as err:
        return err.content



@app.route("/resources", methods=["GET"])
def get_resources(internal=False):
    try:
        if resource_cache:
            results = resource_cache
        else:
            query_data = {'query': 'SELECT id, type, relations.type, relations.targets from meta.resources'}
            query_response = bq_service.jobs().query(projectId=PROJECT_NUMBER, body=query_data).execute()
            resources = defaultdict(dict)
            if 'rows' in query_response:
                for row in query_response['rows']:
                    assert len(row['f']) == len(['id', 'type', 'relations.type', 'relations.targets'])
                    resource_id, resource_type, relation_type, relation_target = row['f'][0]['v'], row['f'][1]['v'], row['f'][2]['v'], row['f'][3]['v']
                    resources[resource_id]['type'] = resource_type
                    if relation_type:
                        resources[resource_id].setdefault('relations', {}).setdefault(relation_type, []).append(relation_target)
            results = []
            for r_id, r in resources.iteritems():
               resource = {
                  'id': r_id,
                  'type': r['type']
               }
               if 'relations' in r:
                   resource['relations'] = r['relations']
               results.append(resource)
        if internal:
            return results
        else:
            return flask.jsonify(resources=results)
    except HttpError as err:
        if internal:
	    raise
        return err.content


@app.route("/resources/<path:resource_id>", methods=["GET"])
def get_resource(resource_id):
    try:
        query_data = {
            'query': 'SELECT id, type, properties, annotations from meta.resources where id = "%s"' % resource_id
        }
        query_response = bq_service.jobs().query(projectId=PROJECT_NUMBER, body=query_data).execute()
        assert len(query_response['rows']) == 1
        row = query_response['rows'][0]
        assert len(row['f']) == len(['id', 'type', 'properties', 'annotations'])
        result = {
            'id': row['f'][0]['v'],
            'type': row['f'][1]['v'],
            'properties': json.loads(row['f'][2]['v']),
            'annotations': json.loads(row['f'][3]['v']),
            'relations': get_relations(resource_id, internal=True)
        }
        return flask.jsonify(resource=result)
    except HttpError as err:
        return err.content


@app.route("/resources/<path:resource_id>/relations", methods=["GET"])
def get_relations(resource_id, internal=False):
    try:
        query_data = {
            'query': 'SELECT relations.type, relations.targets from meta.resources where id = "%s"' % resource_id
        }
        query_response = bq_service.jobs().query(projectId=PROJECT_NUMBER, body=query_data).execute()
        results = defaultdict(list)
        for row in query_response['rows']:
            assert len(row['f']) == len(['type', 'target'])
            results[row['f'][0]['v']].append(row['f'][1]['v'])
        if internal:
            return results
        return flask.jsonify(relations=results)
    except HttpError as err:
        if internal:
            raise
        return err.content


@app.route("/query/<path:query>", methods=["GET"])
def query_resources(query):
    try:
        query_data = {'query': query}
        query_response = bq_service.jobs().query(projectId=PROJECT_NUMBER, body=query_data).execute()
        results = []
        for row in query_response['rows']:
            results_row = []
            for field in row['f']:
                field_str = field['v']
                if field_str.startswith("{\"") and field_str.endswith("\"}"):
                    results_row.append(json.loads(field_str))
                else:
                    results_row.append(field_str)
            results.append(results_row)
        return flask.jsonify(results=results)
    except HttpError as err:
        return err.content


color_map = {
    'Container': 'blue',
    'Service': 'orange',
    'Node': 'purple',
    'ReplicationController': 'pink',
    'Cluster': 'grey',
    'Pod': 'lightgreen',
    'Process': 'yellow'
}

short_type = {
    'ReplicationController': 'R',
    'Cluster': 'C',
    'Container': 'c',
    'Pod': 'P',
    'Process': 'p',
    'Node': 'N',
    'Service': 'S',
    'Image': 'I',
}

@app.route("/context")
def show_context():
    resources_csv = []
    relations_matrix = []
    resources = get_resources(internal=True)
    rindex = 0
    rindex_table = {}
    for r in resources:
        rindex_table[r['id']] = rindex
        rindex += 1
    for r in resources:
        rname = r['id'].split(':', 1)
        rname[0] = short_type.get(rname[0], rname[0])
        rname = ':'.join(rname)
        resource_str = '%s,%s,%s,%s' % (rname[:20], r['type'], color_map.get(r['type'], 'white'), r['id'])
        resources_csv.append(resource_str)
        relations = r.get('relations', {})
        edges = [0 for i in range(len(resources))]
        for rtype in relations:
            for target in relations[rtype]:
                edges[rindex_table[target]] += 1
        relations_matrix.append(edges)
    return flask.render_template('chord.html', 
        resources_csv='\n'.join(resources_csv),
        relations_matrix=json.dumps(relations_matrix))

def init_bigquery():
    api_key = os.environ.get('API_KEY', None)
    if api_key:
       print 'Using API_KEY environment variable.'
       return build('bigquery', 'v2', developerKey=api_key)
    else:
       print 'Using AppAssertion credentials - set GOOGLE_APPLICATION_CREDENTIALS'
       print ' to the client-secrets.json file if you get a permissions error.'
       credentials = AppAssertionCredentials('https://www.googleapis.com/auth/bigquery')
       http_auth = credentials.authorize(Http())
       return build('bigquery', 'v2', http=http_auth)
       """
       credentials = GoogleCredentials.get_application_default()
       return build('bigquery', 'v2', credentials=credentials)
       """

if __name__ == "__main__":

    bq_service = init_bigquery()
    app.run(host='0.0.0.0', debug=True)
    print 'here now'
