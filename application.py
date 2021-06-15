import logging
import flask
from flask import request, Response
import os
from boto3 import client
from sentence_transformers import SentenceTransformer
import uuid
import torch
import torch.nn as nn
import requests

# Create and configure the Flask app
application = flask.Flask(__name__)
os.environ['APP_CONFIG'] = 'default_config'
application.config.from_envvar('APP_CONFIG', silent=True)
application.debug = application.config['FLASK_DEBUG'] in ['true', 'True']

ddb = client('dynamodb', region_name=application.config['AWS_REGION'])


sts = SentenceTransformer('sentence-transformers/distilbert-multilingual-nli-stsb-quora-ranking')
cos = nn.CosineSimilarity(dim=0, eps=1e-6)


@application.route('/match_reply_to_topic', methods=['POST'])
def match_reply_to_topic():
    response = None
    if request.json is None:
        # Expect application/json request
        response = Response("", status=415)
    else:
        try:
            reply_data = {k: v for k, v in request.json.items()}
            logging.warning('reply: ' + str(reply_data))
            reply_embeds = torch.tensor(sts.encode(reply_data['text']))

            topics = get_topics()
            match_topic = max(
                topics,
                key=lambda x: cos(torch.tensor(sts.encode(x['topic'])), reply_embeds)
            )
            logging.warning('matched topic: ' + str(match_topic))

            reply_id = uuid.uuid4().hex
            reply_data['reply_id'] = reply_id

            write_reply_to_ddb(reply_data, match_topic)

            frontend_response = publish_to_frontend(reply_data, match_topic)
            logging.warning('frontend response: ' + str(frontend_response))
            if frontend_response.status_code == 200:
                logging.warning('frontend response content: ' + frontend_response.text)

            response = Response("", status=200)
        except Exception as ex:
            logging.exception('Error processing message: %s' % request.json)
            response = Response(ex.message, status=500)

    return response

def get_topics():
    items = ddb.scan(TableName=application.config['TOPIC_TABLE_NAME'])
    topics = [{k: v['S'] for k, v in item.items()} for item in items['Items']]
    return topics

def write_reply_to_ddb(reply_data, match_topic):
    response = ddb.put_item(
        TableName=application.config['REPLY_TABLE_NAME'],
        Item={
            'reply_id': {'S': reply_data['reply_id']},
            'username': {'S': reply_data.get('userId', '')},
            'date': {'S': reply_data.get('date', '')},
            'time': {'S': reply_data.get('time', '')},
            'topic_id': {'S': match_topic['topic_id']},
            'text': {'S': reply_data['text']}
        }
    )
    return response

def publish_to_frontend(reply_data, match_topic):
    url = 'https://wiq2ve4q31.execute-api.us-east-1.amazonaws.com/devx/dialugue'
    date, time = reply_data.get('date', ''), reply_data.get('time', '')
    timestamp = f'{date} {time}' if date and time else ''
    response = requests.post(
        url=url,
        json={
            'id': reply_data['reply_id'],
            'title_id': match_topic['topic_id'],
            'speaker': reply_data.get('userId', ''),
            'content': reply_data['text'],
            'timestamp': timestamp
        }
    )
    return response

if __name__ == '__main__':
    application.run(host='0.0.0.0')