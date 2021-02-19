"""
.. module:: instance2
.. moduleauthor:: Andrej Cermak <github.com/andrejcermak>
"""

import regex
from json import JSONDecoder as decoder
from flask import request
from flask_restful import Resource
from flask import session as flask_session

from schema import StartServerSchema
from Connection import connect
import requests


class InstanceTf(Resource):


    @staticmethod
    def post():
        connection = connect(flask_session['token'], flask_session['project_id'])
        data = StartServerSchema().load(request.json)

        image = connection.compute.find_image(data["image"])
        flavor = connection.compute.find_flavor(data["flavor"])
        network = connection.network.find_network(data["network_id"])
        key_pair = connection.compute.find_keypair(data["key_name"])

        if (image is None) or (flavor is None) or (network is None) or (key_pair is None):
            return {"message": "resource not found"}, 400

        user_variables = {
            "instance_name": "data",
            "key_pair": key_pair.name,
            "network_id": network.id,
            "user_name": data["metadata"]["name"],
            "user_email": data["metadata"]["email"],
            "floating_ip": "78.128.250.94",
            "token": connection.authorize()
        }
        response = requests.post("http://terrestrial_api_1:8000/api/v1/configurations/bioconductor/apply?async",
                             headers={'Authorization': 'Token dev'},
                             data=user_variables)
        return {"id": response.content.decode()}, response.status_code


class Task(Resource):

    @staticmethod
    def get(task_id):
        connection = connect(flask_session['token'], flask_session['project_id'])
        response = requests.get("http://terrestrial_api_1:8000/api/v1/tasks/"+task_id,
                                 headers={'Authorization': 'Token dev'})
        state = response.content.decode()

        if state == "PENDING":
            return {"state": state, "reason": {}, "log": ""}, 200

        if state == "SUCCESS":
            result = requests.get("http://localhost:8000/api/v1/tasks/%s/result" % task_id,
                                  headers={'Authorization': 'Token dev'}).content.decode()
            if result.find("Apply complete!") != -1:
                return {"state": "success", "reason": {}, "log": result}, 201

            if result.find("Error creating OpenStack") != -1:
                pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
                print("reason", result)
                reason, _ = decoder().raw_decode(pattern.findall(result)[0])
                keys = [i for i in reason.keys()]
                return {"state": "error", "reason": reason[keys[0]], "log": result}, 201

        return {"state": state, "reason": {}, "log": ""}, 200
