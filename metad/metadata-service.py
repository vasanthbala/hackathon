
import httplib2
import sys
import requests
import simplejson as json
import flask
from collections import defaultdict
import datetime

from apiclient.discovery import build
from oauth2client.client import GoogleCredentials
from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.errors import HttpError


PROJECT = 'cooltool-1009'
ZONE = 'us-central1-b'
PROJECT_NUMBER = '518787634948'
DATASET_ID = 'meta'
TABLE_ID = 'resources'
CLUSTER_INSIGHT_URL = 'http://108.59.84.220:5555/cluster'

bq_service = None
app = flask.Flask(__name__)

resource_cache = [
    {
      "id": "Container:k8s_kube-ui.3f6c8325_kube-ui-v1-1mz59_kube-system_b0d4c923-2cac-11e5-bfac-42010af0c42c_e8138cdc",
      "relations": {
        "contains": [
          "Process:bf67f148549e/3830"
        ],
        "createdFrom": [
          "Image:a5aea7f6bfd4df8af894cecf7218f489a2806a78eabe47745d61ae7c3d1d394c"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:3d99630a59c1/6551",
      "type": "Process"
    },
    {
      "id": "Pod:kube-ui-v1-1mz59",
      "type": "Pod"
    },
    {
      "id": "Container:k8s_influxdb.b95ecd41_monitoring-influx-grafana-v1-8phd1_kube-system_b0d38917-2cac-11e5-bfac-42010af0c42c_6517a144",
      "relations": {
        "contains": [
          "Process:9f67dbc60a37/4027",
          "Process:9f67dbc60a37/4035"
        ],
        "createdFrom": [
          "Image:514b330600afe3ed9f948f65fab7593b374075d194c65263fe3bafc43820fdad"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Pod:fluentd-cloud-logging-kubernetes-minion-66xf",
      "type": "Pod"
    },
    {
      "id": "Service:redismaster",
      "relations": {
        "loadBalances": [
          "Pod:redis-master-ec4yb"
        ]
      },
      "type": "Service"
    },
    {
      "id": "Process:6bb4e7821381/3794",
      "type": "Process"
    },
    {
      "id": "Process:70ec68255adf/3447",
      "type": "Process"
    },
    {
      "id": "Image:67bedf4bbf07333b6df642a0751270851f153b19ed5ade1e2dcdd45523ef99bf",
      "type": "Image"
    },
    {
      "id": "Pod:cluster-insight-minion-controller-v1-fr6c4",
      "relations": {
        "contains": [
          "Container:k8s_POD.baeedb8_cluster-insight-minion-controller-v1-fr6c4_default_ae74df60-2eeb-11e5-bfac-42010af0c42c_67bd1ebd",
          "Container:k8s_cluster-insight.b73d9b0e_cluster-insight-minion-controller-v1-fr6c4_default_ae74df60-2eeb-11e5-bfac-42010af0c42c_fe6b7571"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "Process:5585d9ce931c/751",
      "type": "Process"
    },
    {
      "id": "Container:k8s_bigquery.e8abca62_bigquery-controller-wbf2n_default_66c3fbd1-2e54-11e5-bfac-42010af0c42c_d65019fd",
      "relations": {
        "contains": [
          "Process:01c75701b6b4/12518",
          "Process:01c75701b6b4/12533",
          "Process:01c75701b6b4/12540",
          "Process:01c75701b6b4/12541"
        ],
        "createdFrom": [
          "Image:ce64b646452af6e32db633710fe272dc09ea505913009099812951ed4b908ecc"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Pod:cluster-insight-master-controller-v1-4oris",
      "relations": {
        "contains": [
          "Container:k8s_POD.63b1eee2_cluster-insight-master-controller-v1-4oris_default_af115aee-2eeb-11e5-bfac-42010af0c42c_99058b70",
          "Container:k8s_cluster-insight.870d79c8_cluster-insight-master-controller-v1-4oris_default_af115aee-2eeb-11e5-bfac-42010af0c42c_68622e6a"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "ReplicationController:kube-ui-v1",
      "relations": {
        "monitors": [
          "Pod:kube-ui-v1-1mz59"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "Container:k8s_master.439546ac_redis-master-ec4yb_default_274969fa-2fb4-11e5-bfac-42010af0c42c_e4b53d57",
      "relations": {
        "contains": [
          "Process:5585d9ce931c/751"
        ],
        "createdFrom": [
          "Image:0ff407d5a7d9ed36acdf3e75de8cc127afecc9af234d05486be2981cdc01a38c"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_POD.e4cc795_fluentd-cloud-logging-kubernetes-minion-ktb7_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_d862be11",
      "relations": {
        "contains": [
          "Process:08f713d47484/3449"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Pod:kube-dns-v6-0maif",
      "type": "Pod"
    },
    {
      "id": "Service:cluster-insight",
      "relations": {
        "loadBalances": [
          "Pod:cluster-insight-master-controller-v1-4oris"
        ]
      },
      "type": "Service"
    },
    {
      "id": "Process:746a3ec2fa52/3760",
      "type": "Process"
    },
    {
      "id": "Container:k8s_cluster-insight.b73d9b0e_cluster-insight-minion-controller-v1-fr6c4_default_ae74df60-2eeb-11e5-bfac-42010af0c42c_fe6b7571",
      "relations": {
        "contains": [
          "Process:39cc7df5bc03/7226"
        ],
        "createdFrom": [
          "Image:8ca46931f6b73e325978e0b5d0269d8492d0b8e6256269c7692a66f2cdf602bc"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Node:kubernetes-minion-4t8q",
      "relations": {
        "contains": [
          "Container:k8s_skydns.b3bac0b9_kube-dns-v6-0maif_kube-system_b0d3008c-2cac-11e5-bfac-42010af0c42c_af011d5f",
          "Container:k8s_fluentd-cloud-logging.7721935b_fluentd-cloud-logging-kubernetes-minion-4t8q_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_0ebf19dd",
          "Container:k8s_POD.8fdb0e41_kube-dns-v6-0maif_kube-system_b0d3008c-2cac-11e5-bfac-42010af0c42c_9d207e0c",
          "Container:k8s_kube2sky.fc5e6a2f_kube-dns-v6-0maif_kube-system_b0d3008c-2cac-11e5-bfac-42010af0c42c_ff02ec86",
          "Container:k8s_POD.e4cc795_fluentd-cloud-logging-kubernetes-minion-4t8q_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_53f69dbd",
          "Container:k8s_etcd.f1079875_kube-dns-v6-0maif_kube-system_b0d3008c-2cac-11e5-bfac-42010af0c42c_4d478686"
        ],
        "runs": [
          "Pod:cluster-insight-minion-controller-v1-4gru9",
          "Pod:fluentd-cloud-logging-kubernetes-minion-4t8q",
          "Pod:kube-dns-v6-0maif"
        ]
      },
      "type": "Node"
    },
    {
      "id": "Process:d93c671fbc37/27212",
      "type": "Process"
    },
    {
      "id": "ReplicationController:bigquery-controller",
      "relations": {
        "monitors": [
          "Pod:bigquery-controller-m38fd",
          "Pod:bigquery-controller-wbf2n"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "Pod:cluster-insight-minion-controller-v1-p9cfs",
      "relations": {
        "contains": [
          "Container:k8s_cluster-insight.b73d9b0e_cluster-insight-minion-controller-v1-p9cfs_default_adcfe98a-2eeb-11e5-bfac-42010af0c42c_529f39d4",
          "Container:k8s_POD.baeedb8_cluster-insight-minion-controller-v1-p9cfs_default_adcfe98a-2eeb-11e5-bfac-42010af0c42c_607396ab"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "Process:01c75701b6b4/12533",
      "type": "Process"
    },
    {
      "id": "Process:f6702c5d22a8/12250",
      "type": "Process"
    },
    {
      "id": "ReplicationController:cluster-insight-minion-controller-v1",
      "relations": {
        "monitors": [
          "Pod:cluster-insight-minion-controller-v1-4gru9",
          "Pod:cluster-insight-minion-controller-v1-fr6c4",
          "Pod:cluster-insight-minion-controller-v1-p9cfs",
          "Pod:cluster-insight-minion-controller-v1-qi6o1"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "ReplicationController:redis-master",
      "relations": {
        "monitors": [
          "Pod:redis-master-ec4yb"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "Image:22182f122d461ef2e96af4c2ac1ebfbccf127894da9e9ceb56f7d74496583b30",
      "type": "Image"
    },
    {
      "id": "Process:e1a5c5408936/3817",
      "type": "Process"
    },
    {
      "id": "Process:66057ed21515/5339",
      "type": "Process"
    },
    {
      "id": "Pod:cluster-insight-minion-controller-v1-4gru9",
      "relations": {
        "contains": [
          "Container:k8s_POD.baeedb8_cluster-insight-minion-controller-v1-4gru9_default_ae756d5a-2eeb-11e5-bfac-42010af0c42c_e4416ba0",
          "Container:k8s_cluster-insight.b73d9b0e_cluster-insight-minion-controller-v1-4gru9_default_ae756d5a-2eeb-11e5-bfac-42010af0c42c_469b436f"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "Node:kubernetes-minion-66xf",
      "relations": {
        "contains": [
          "Container:k8s_influxdb.b95ecd41_monitoring-influx-grafana-v1-8phd1_kube-system_b0d38917-2cac-11e5-bfac-42010af0c42c_6517a144",
          "Container:k8s_POD.e4cc795_fluentd-cloud-logging-kubernetes-minion-66xf_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_0bd3aad6",
          "Container:k8s_grafana.c0ddde22_monitoring-influx-grafana-v1-8phd1_kube-system_b0d38917-2cac-11e5-bfac-42010af0c42c_3388704f",
          "Container:k8s_POD.fc880c63_monitoring-influx-grafana-v1-8phd1_kube-system_b0d38917-2cac-11e5-bfac-42010af0c42c_3c413da7",
          "Container:k8s_fluentd-cloud-logging.7721935b_fluentd-cloud-logging-kubernetes-minion-66xf_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_c77746e6"
        ],
        "runs": [
          "Pod:bigquery-controller-m38fd",
          "Pod:cluster-insight-minion-controller-v1-fr6c4",
          "Pod:fluentd-cloud-logging-kubernetes-minion-66xf",
          "Pod:monitoring-influx-grafana-v1-8phd1"
        ]
      },
      "type": "Node"
    },
    {
      "id": "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1",
      "type": "Image"
    },
    {
      "id": "Container:k8s_grafana.c0ddde22_monitoring-influx-grafana-v1-8phd1_kube-system_b0d38917-2cac-11e5-bfac-42010af0c42c_3388704f",
      "relations": {
        "contains": [
          "Process:679a6ad96854/4242"
        ],
        "createdFrom": [
          "Image:22182f122d461ef2e96af4c2ac1ebfbccf127894da9e9ceb56f7d74496583b30"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:96d33b780edf/9591",
      "type": "Process"
    },
    {
      "id": "Pod:monitoring-influx-grafana-v1-8phd1",
      "type": "Pod"
    },
    {
      "id": "ReplicationController:kube-dns-v6",
      "relations": {
        "monitors": [
          "Pod:kube-dns-v6-0maif"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "Container:k8s_POD.e4cc795_fluentd-cloud-logging-kubernetes-minion-4t8q_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_53f69dbd",
      "relations": {
        "contains": [
          "Process:70ec68255adf/3447"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:40bae1192755/1138",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.49eee8c2_redis-master-ec4yb_default_274969fa-2fb4-11e5-bfac-42010af0c42c_53191161",
      "relations": {
        "contains": [
          "Process:539b5964af18/719"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Pod:fluentd-cloud-logging-kubernetes-minion-4t8q",
      "type": "Pod"
    },
    {
      "id": "Process:6bb4e7821381/3816",
      "type": "Process"
    },
    {
      "id": "Process:1cca8af95032/3436",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.baeedb8_cluster-insight-minion-controller-v1-qi6o1_default_ae747d7e-2eeb-11e5-bfac-42010af0c42c_3949b241",
      "relations": {
        "contains": [
          "Process:58fc25ff3d89/15077"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Service:monitoring-heapster",
      "relations": {
        "loadBalances": [
          "Pod:monitoring-heapster-v5-i20xx"
        ]
      },
      "type": "Service"
    },
    {
      "id": "Process:e1a5c5408936/3807",
      "type": "Process"
    },
    {
      "id": "Container:k8s_collectd.37f930b6_redis-master-ec4yb_default_274969fa-2fb4-11e5-bfac-42010af0c42c_81c4f26b",
      "relations": {
        "contains": [
          "Process:40bae1192755/1138"
        ],
        "createdFrom": [
          "Image:67bedf4bbf07333b6df642a0751270851f153b19ed5ade1e2dcdd45523ef99bf"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:746a3ec2fa52/3812",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.e4cc795_bigquery-controller-m38fd_default_66c4113e-2e54-11e5-bfac-42010af0c42c_dcb6db5f",
      "relations": {
        "contains": [
          "Process:f6702c5d22a8/12250"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_POD.baeedb8_cluster-insight-minion-controller-v1-4gru9_default_ae756d5a-2eeb-11e5-bfac-42010af0c42c_e4416ba0",
      "relations": {
        "contains": [
          "Process:efcac7ee8ba7/26547"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:d630945f90de/3952",
      "type": "Process"
    },
    {
      "id": "Pod:twitter-stream-oyveu",
      "relations": {
        "contains": [
          "Container:k8s_POD.e4cc795_twitter-stream-oyveu_default_4c6c1e8f-3002-11e5-bfac-42010af0c42c_facd4ca9",
          "Container:k8s_twitter-to-redis.48e4392a_twitter-stream-oyveu_default_4c6c1e8f-3002-11e5-bfac-42010af0c42c_26a74eac"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "Node:kubernetes-minion-ktb7",
      "relations": {
        "contains": [
          "Container:k8s_fluentd-cloud-logging.7721935b_fluentd-cloud-logging-kubernetes-minion-ktb7_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_c5859c41",
          "Container:k8s_kube-ui.3f6c8325_kube-ui-v1-1mz59_kube-system_b0d4c923-2cac-11e5-bfac-42010af0c42c_e8138cdc",
          "Container:k8s_POD.3b46e8b9_kube-ui-v1-1mz59_kube-system_b0d4c923-2cac-11e5-bfac-42010af0c42c_e519d1d7",
          "Container:k8s_POD.e4cc795_fluentd-cloud-logging-kubernetes-minion-ktb7_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_d862be11"
        ],
        "runs": [
          "Pod:cluster-insight-master-controller-v1-4oris",
          "Pod:cluster-insight-minion-controller-v1-p9cfs",
          "Pod:redis-master-ec4yb",
          "Pod:fluentd-cloud-logging-kubernetes-minion-ktb7",
          "Pod:kube-ui-v1-1mz59"
        ]
      },
      "type": "Node"
    },
    {
      "id": "Process:3e558b019040/3687",
      "type": "Process"
    },
    {
      "id": "Service:kube-ui",
      "relations": {
        "loadBalances": [
          "Pod:kube-ui-v1-1mz59"
        ]
      },
      "type": "Service"
    },
    {
      "id": "Container:k8s_POD.e4cc795_monitoring-heapster-v5-i20xx_kube-system_b0d50440-2cac-11e5-bfac-42010af0c42c_00209b6e",
      "relations": {
        "contains": [
          "Process:3ab41cd50d15/3679"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Image:0ff407d5a7d9ed36acdf3e75de8cc127afecc9af234d05486be2981cdc01a38c",
      "type": "Image"
    },
    {
      "id": "Process:58fc25ff3d89/15077",
      "type": "Process"
    },
    {
      "id": "Pod:fluentd-cloud-logging-kubernetes-minion-ktb7",
      "type": "Pod"
    },
    {
      "id": "Cluster:_unknown_",
      "relations": {
        "contains": [
          "Node:kubernetes-minion-ktb7",
          "Node:kubernetes-minion-mc5n",
          "Node:kubernetes-minion-66xf",
          "Node:kubernetes-minion-4t8q",
          "ReplicationController:cluster-insight-minion-controller-v1",
          "ReplicationController:cluster-insight-master-controller-v1",
          "ReplicationController:kube-ui-v1",
          "Service:kubernetes",
          "Service:cluster-insight",
          "ReplicationController:monitoring-heapster-v5",
          "ReplicationController:bigquery-controller",
          "Service:kube-ui",
          "Service:monitoring-heapster",
          "Service:monitoring-influxdb",
          "Service:kube-dns",
          "ReplicationController:redis-master",
          "ReplicationController:monitoring-influx-grafana-v1",
          "ReplicationController:twitter-stream",
          "Service:monitoring-grafana",
          "ReplicationController:kube-dns-v6",
          "Service:redismaster"
        ]
      },
      "type": "Cluster"
    },
    {
      "id": "Image:e52a547dca17cd83e8b6022e8ae1c1883d0855bce2d1c30071ffa0dcb8a8caf6",
      "type": "Image"
    },
    {
      "id": "Container:k8s_fluentd-cloud-logging.7721935b_fluentd-cloud-logging-kubernetes-minion-4t8q_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_0ebf19dd",
      "relations": {
        "contains": [
          "Process:f9df98f04bbf/3750",
          "Process:f9df98f04bbf/3757",
          "Process:f9df98f04bbf/3770"
        ],
        "createdFrom": [
          "Image:9855059e588fee45695a2cb5f2e57d2a0ded43cb3e3ae6567623b77f485dd2d0"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:64fabc78d725/8697",
      "type": "Process"
    },
    {
      "id": "Process:64fabc78d725/8696",
      "type": "Process"
    },
    {
      "id": "Image:ce64b646452af6e32db633710fe272dc09ea505913009099812951ed4b908ecc",
      "type": "Image"
    },
    {
      "id": "Process:64fabc78d725/8698",
      "type": "Process"
    },
    {
      "id": "Service:kube-dns",
      "relations": {
        "loadBalances": [
          "Pod:kube-dns-v6-0maif"
        ]
      },
      "type": "Service"
    },
    {
      "id": "ReplicationController:cluster-insight-master-controller-v1",
      "relations": {
        "monitors": [
          "Pod:cluster-insight-master-controller-v1-4oris"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "Process:01c75701b6b4/12518",
      "type": "Process"
    },
    {
      "id": "Container:k8s_fluentd-cloud-logging.7721935b_fluentd-cloud-logging-kubernetes-minion-mc5n_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_14e79e80",
      "relations": {
        "contains": [
          "Process:6bb4e7821381/3794",
          "Process:6bb4e7821381/3816",
          "Process:6bb4e7821381/6885"
        ],
        "createdFrom": [
          "Image:9855059e588fee45695a2cb5f2e57d2a0ded43cb3e3ae6567623b77f485dd2d0"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_twitter-to-redis.48e4392a_twitter-stream-oyveu_default_4c6c1e8f-3002-11e5-bfac-42010af0c42c_26a74eac",
      "relations": {
        "contains": [
          "Process:59b0e728208c/19815",
          "Process:59b0e728208c/19829",
          "Process:59b0e728208c/19834",
          "Process:59b0e728208c/19835"
        ],
        "createdFrom": [
          "Image:df3151d80a3511a56765214a7b24f71c6c575e09c6677119274954c44eec15c9"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_cluster-insight.b73d9b0e_cluster-insight-minion-controller-v1-qi6o1_default_ae747d7e-2eeb-11e5-bfac-42010af0c42c_3d2d48ae",
      "relations": {
        "contains": [
          "Process:b1744db8a684/15930"
        ],
        "createdFrom": [
          "Image:8ca46931f6b73e325978e0b5d0269d8492d0b8e6256269c7692a66f2cdf602bc"
        ]
      },
      "type": "Container"
    },
    {
      "id": "ReplicationController:monitoring-heapster-v5",
      "relations": {
        "monitors": [
          "Pod:monitoring-heapster-v5-i20xx"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "Process:3ab41cd50d15/3679",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.e4cc795_fluentd-cloud-logging-kubernetes-minion-mc5n_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_44324a65",
      "relations": {
        "contains": [
          "Process:1cca8af95032/3436"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:b1744db8a684/15930",
      "type": "Process"
    },
    {
      "id": "Process:f9df98f04bbf/3770",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.e4cc795_bigquery-controller-wbf2n_default_66c3fbd1-2e54-11e5-bfac-42010af0c42c_3f9d1b9d",
      "relations": {
        "contains": [
          "Process:66057ed21515/5339"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Image:a5aea7f6bfd4df8af894cecf7218f489a2806a78eabe47745d61ae7c3d1d394c",
      "type": "Image"
    },
    {
      "id": "Pod:fluentd-cloud-logging-kubernetes-minion-mc5n",
      "type": "Pod"
    },
    {
      "id": "Process:bf67f148549e/3830",
      "type": "Process"
    },
    {
      "id": "Container:k8s_fluentd-cloud-logging.7721935b_fluentd-cloud-logging-kubernetes-minion-ktb7_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_c5859c41",
      "relations": {
        "contains": [
          "Process:e1a5c5408936/3807",
          "Process:e1a5c5408936/3817",
          "Process:e1a5c5408936/3842"
        ],
        "createdFrom": [
          "Image:9855059e588fee45695a2cb5f2e57d2a0ded43cb3e3ae6567623b77f485dd2d0"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Service:monitoring-influxdb",
      "relations": {
        "loadBalances": [
          "Pod:monitoring-influx-grafana-v1-8phd1"
        ]
      },
      "type": "Service"
    },
    {
      "id": "Process:64fabc78d725/8688",
      "type": "Process"
    },
    {
      "id": "Process:59cff23ad9d9/3692",
      "type": "Process"
    },
    {
      "id": "Process:b3e66f7b2fff/3438",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.baeedb8_cluster-insight-minion-controller-v1-fr6c4_default_ae74df60-2eeb-11e5-bfac-42010af0c42c_67bd1ebd",
      "relations": {
        "contains": [
          "Process:3d99630a59c1/6551"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "ReplicationController:twitter-stream",
      "relations": {
        "monitors": [
          "Pod:twitter-stream-oyveu"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "Process:59b0e728208c/19815",
      "type": "Process"
    },
    {
      "id": "Node:kubernetes-minion-mc5n",
      "relations": {
        "contains": [
          "Container:k8s_POD.e4cc795_monitoring-heapster-v5-i20xx_kube-system_b0d50440-2cac-11e5-bfac-42010af0c42c_00209b6e",
          "Container:k8s_POD.e4cc795_fluentd-cloud-logging-kubernetes-minion-mc5n_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_44324a65",
          "Container:k8s_fluentd-cloud-logging.7721935b_fluentd-cloud-logging-kubernetes-minion-mc5n_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_14e79e80"
        ],
        "runs": [
          "Pod:bigquery-controller-wbf2n",
          "Pod:cluster-insight-minion-controller-v1-qi6o1",
          "Pod:twitter-stream-oyveu",
          "Pod:fluentd-cloud-logging-kubernetes-minion-mc5n",
          "Pod:monitoring-heapster-v5-i20xx"
        ]
      },
      "type": "Node"
    },
    {
      "id": "Container:k8s_POD.3b46e8b9_kube-ui-v1-1mz59_kube-system_b0d4c923-2cac-11e5-bfac-42010af0c42c_e519d1d7",
      "relations": {
        "contains": [
          "Process:3e558b019040/3687"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:b90b8a1a0eb3/3811",
      "type": "Process"
    },
    {
      "id": "Pod:bigquery-controller-m38fd",
      "relations": {
        "contains": [
          "Container:k8s_bigquery.e8abca62_bigquery-controller-m38fd_default_66c4113e-2e54-11e5-bfac-42010af0c42c_fc8a48a0",
          "Container:k8s_POD.e4cc795_bigquery-controller-m38fd_default_66c4113e-2e54-11e5-bfac-42010af0c42c_dcb6db5f"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "Process:59b0e728208c/19835",
      "type": "Process"
    },
    {
      "id": "Service:kubernetes",
      "type": "Service"
    },
    {
      "id": "Container:k8s_etcd.f1079875_kube-dns-v6-0maif_kube-system_b0d3008c-2cac-11e5-bfac-42010af0c42c_4d478686",
      "relations": {
        "contains": [
          "Process:c36457d94110/3896"
        ],
        "createdFrom": [
          "Image:b6b9a86dc06aa1361357ca1b105feba961f6a4145adca6c54e142c0be0fe87b0"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:9f67dbc60a37/4027",
      "type": "Process"
    },
    {
      "id": "Container:k8s_cluster-insight.b73d9b0e_cluster-insight-minion-controller-v1-4gru9_default_ae756d5a-2eeb-11e5-bfac-42010af0c42c_469b436f",
      "relations": {
        "contains": [
          "Process:d93c671fbc37/27212"
        ],
        "createdFrom": [
          "Image:8ca46931f6b73e325978e0b5d0269d8492d0b8e6256269c7692a66f2cdf602bc"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Image:b6b9a86dc06aa1361357ca1b105feba961f6a4145adca6c54e142c0be0fe87b0",
      "type": "Image"
    },
    {
      "id": "Process:539b5964af18/719",
      "type": "Process"
    },
    {
      "id": "Process:6bb4e7821381/6885",
      "type": "Process"
    },
    {
      "id": "Container:k8s_fluentd-cloud-logging.7721935b_fluentd-cloud-logging-kubernetes-minion-66xf_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_c77746e6",
      "relations": {
        "contains": [
          "Process:746a3ec2fa52/3760",
          "Process:746a3ec2fa52/3812",
          "Process:746a3ec2fa52/3825"
        ],
        "createdFrom": [
          "Image:9855059e588fee45695a2cb5f2e57d2a0ded43cb3e3ae6567623b77f485dd2d0"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Image:8ca46931f6b73e325978e0b5d0269d8492d0b8e6256269c7692a66f2cdf602bc",
      "type": "Image"
    },
    {
      "id": "Pod:redis-master-ec4yb",
      "relations": {
        "contains": [
          "Container:k8s_master.439546ac_redis-master-ec4yb_default_274969fa-2fb4-11e5-bfac-42010af0c42c_e4b53d57",
          "Container:k8s_POD.49eee8c2_redis-master-ec4yb_default_274969fa-2fb4-11e5-bfac-42010af0c42c_53191161",
          "Container:k8s_collectd.37f930b6_redis-master-ec4yb_default_274969fa-2fb4-11e5-bfac-42010af0c42c_81c4f26b"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "Image:791ddf327076e0fd35a1125568a56c05ee1f1dfd7a165c74f4d489d8a5e65ac5",
      "type": "Image"
    },
    {
      "id": "Container:k8s_cluster-insight.b73d9b0e_cluster-insight-minion-controller-v1-p9cfs_default_adcfe98a-2eeb-11e5-bfac-42010af0c42c_529f39d4",
      "relations": {
        "contains": [
          "Process:bc371b625ac2/9584"
        ],
        "createdFrom": [
          "Image:8ca46931f6b73e325978e0b5d0269d8492d0b8e6256269c7692a66f2cdf602bc"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_POD.8fdb0e41_kube-dns-v6-0maif_kube-system_b0d3008c-2cac-11e5-bfac-42010af0c42c_9d207e0c",
      "relations": {
        "contains": [
          "Process:91311de4ade0/3696"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_skydns.b3bac0b9_kube-dns-v6-0maif_kube-system_b0d3008c-2cac-11e5-bfac-42010af0c42c_af011d5f",
      "relations": {
        "contains": [
          "Process:b90b8a1a0eb3/3811"
        ],
        "createdFrom": [
          "Image:791ddf327076e0fd35a1125568a56c05ee1f1dfd7a165c74f4d489d8a5e65ac5"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_cluster-insight.870d79c8_cluster-insight-master-controller-v1-4oris_default_af115aee-2eeb-11e5-bfac-42010af0c42c_68622e6a",
      "relations": {
        "contains": [
          "Process:96d33b780edf/9591"
        ],
        "createdFrom": [
          "Image:8ca46931f6b73e325978e0b5d0269d8492d0b8e6256269c7692a66f2cdf602bc"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Service:monitoring-grafana",
      "relations": {
        "loadBalances": [
          "Pod:monitoring-influx-grafana-v1-8phd1"
        ]
      },
      "type": "Service"
    },
    {
      "id": "Process:f9df98f04bbf/3750",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.63b1eee2_cluster-insight-master-controller-v1-4oris_default_af115aee-2eeb-11e5-bfac-42010af0c42c_99058b70",
      "relations": {
        "contains": [
          "Process:bbce39e662f7/8772"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Pod:monitoring-heapster-v5-i20xx",
      "type": "Pod"
    },
    {
      "id": "Container:k8s_POD.e4cc795_fluentd-cloud-logging-kubernetes-minion-66xf_kube-system_d0feac1ad02da9e97c4bf67970ece7a1_0bd3aad6",
      "relations": {
        "contains": [
          "Process:b3e66f7b2fff/3438"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:f9df98f04bbf/3757",
      "type": "Process"
    },
    {
      "id": "ReplicationController:monitoring-influx-grafana-v1",
      "relations": {
        "monitors": [
          "Pod:monitoring-influx-grafana-v1-8phd1"
        ]
      },
      "type": "ReplicationController"
    },
    {
      "id": "Process:9f67dbc60a37/4035",
      "type": "Process"
    },
    {
      "id": "Process:59b0e728208c/19829",
      "type": "Process"
    },
    {
      "id": "Process:679a6ad96854/4242",
      "type": "Process"
    },
    {
      "id": "Container:k8s_bigquery.e8abca62_bigquery-controller-m38fd_default_66c4113e-2e54-11e5-bfac-42010af0c42c_fc8a48a0",
      "relations": {
        "contains": [
          "Process:64fabc78d725/8688",
          "Process:64fabc78d725/8696",
          "Process:64fabc78d725/8697",
          "Process:64fabc78d725/8698"
        ],
        "createdFrom": [
          "Image:ce64b646452af6e32db633710fe272dc09ea505913009099812951ed4b908ecc"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_POD.fc880c63_monitoring-influx-grafana-v1-8phd1_kube-system_b0d38917-2cac-11e5-bfac-42010af0c42c_3c413da7",
      "relations": {
        "contains": [
          "Process:59cff23ad9d9/3692"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Container:k8s_kube2sky.fc5e6a2f_kube-dns-v6-0maif_kube-system_b0d3008c-2cac-11e5-bfac-42010af0c42c_ff02ec86",
      "relations": {
        "contains": [
          "Process:d630945f90de/3952"
        ],
        "createdFrom": [
          "Image:e52a547dca17cd83e8b6022e8ae1c1883d0855bce2d1c30071ffa0dcb8a8caf6"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:c36457d94110/3896",
      "type": "Process"
    },
    {
      "id": "Process:bbce39e662f7/8772",
      "type": "Process"
    },
    {
      "id": "Image:9855059e588fee45695a2cb5f2e57d2a0ded43cb3e3ae6567623b77f485dd2d0",
      "type": "Image"
    },
    {
      "id": "Pod:bigquery-controller-wbf2n",
      "relations": {
        "contains": [
          "Container:k8s_bigquery.e8abca62_bigquery-controller-wbf2n_default_66c3fbd1-2e54-11e5-bfac-42010af0c42c_d65019fd",
          "Container:k8s_POD.e4cc795_bigquery-controller-wbf2n_default_66c3fbd1-2e54-11e5-bfac-42010af0c42c_3f9d1b9d"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "Process:08f713d47484/3449",
      "type": "Process"
    },
    {
      "id": "Pod:cluster-insight-minion-controller-v1-qi6o1",
      "relations": {
        "contains": [
          "Container:k8s_POD.baeedb8_cluster-insight-minion-controller-v1-qi6o1_default_ae747d7e-2eeb-11e5-bfac-42010af0c42c_3949b241",
          "Container:k8s_cluster-insight.b73d9b0e_cluster-insight-minion-controller-v1-qi6o1_default_ae747d7e-2eeb-11e5-bfac-42010af0c42c_3d2d48ae"
        ]
      },
      "type": "Pod"
    },
    {
      "id": "Process:bc371b625ac2/9584",
      "type": "Process"
    },
    {
      "id": "Process:e1a5c5408936/3842",
      "type": "Process"
    },
    {
      "id": "Process:c3c13b738537/16137",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.e4cc795_twitter-stream-oyveu_default_4c6c1e8f-3002-11e5-bfac-42010af0c42c_facd4ca9",
      "relations": {
        "contains": [
          "Process:c3c13b738537/16137"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:91311de4ade0/3696",
      "type": "Process"
    },
    {
      "id": "Image:514b330600afe3ed9f948f65fab7593b374075d194c65263fe3bafc43820fdad",
      "type": "Image"
    },
    {
      "id": "Process:39cc7df5bc03/7226",
      "type": "Process"
    },
    {
      "id": "Process:efcac7ee8ba7/26547",
      "type": "Process"
    },
    {
      "id": "Image:df3151d80a3511a56765214a7b24f71c6c575e09c6677119274954c44eec15c9",
      "type": "Image"
    },
    {
      "id": "Process:4fef401e9687/8682",
      "type": "Process"
    },
    {
      "id": "Process:59b0e728208c/19834",
      "type": "Process"
    },
    {
      "id": "Process:746a3ec2fa52/3825",
      "type": "Process"
    },
    {
      "id": "Container:k8s_POD.baeedb8_cluster-insight-minion-controller-v1-p9cfs_default_adcfe98a-2eeb-11e5-bfac-42010af0c42c_607396ab",
      "relations": {
        "contains": [
          "Process:4fef401e9687/8682"
        ],
        "createdFrom": [
          "Image:2c40b0526b6358710fd09e7b8c022429268cc61703b4777e528ac9d469a07ca1"
        ]
      },
      "type": "Container"
    },
    {
      "id": "Process:01c75701b6b4/12540",
      "type": "Process"
    },
    {
      "id": "Process:01c75701b6b4/12541",
      "type": "Process"
    }
]


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
        delete_response = bq_service.tables().delete(
            projectId=PROJECT_NUMBER, datasetId=DATASET_ID, tableId=TABLE_ID).execute()
        insert_data = {
            'schema': resource_schema,
            'tableReference': {
                'projectId': PROJECT_NUMBER,
                'datasetId': 'metadata',
                'tableId': 'resources'
            }
        }
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
            return 'Successfully updated resource metadata.'
    except HttpError as err:
        return err.content



@app.route("/resources", methods=["GET"])
def get_resources(internal=False):
    try:
        if resource_cache:
            results = resource_cache
        else:
            query_data = {'query': 'SELECT id, type from meta.resources'}
            query_response = bq_service.jobs().query(projectId=PROJECT_NUMBER, body=query_data).execute()
            results = []
            if 'rows' in query_response:
                for row in query_response['rows']:
                    assert len(row['f']) == len(['id', 'type'])
                    resource_id, resource_type = row['f'][0]['v'], row['f'][1]['v']
                    result_row = {
                        'id': resource_id,
                        'type': resource_type,
                        'relations': get_relations(resource_id, internal=True)
                    }
                    results.append(result_row)
        if internal:
            return results
        else:
            return flask.jsonify(resources=results)
    except HttpError as err:
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
    credentials = GoogleCredentials.get_application_default()
    return build('bigquery', 'v2', credentials=credentials)


if __name__ == "__main__":

    bq_service = init_bigquery()
    app.run(debug=True)
