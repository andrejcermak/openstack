from flask import Flask
from flask_restful import Api
from resources.limit import Limit
from resources.security_group import SecurityGroup
from resources.security_group_rule import SecurityGroupRule
from resources.gateway import Gateway
from resources.floating_ip import FloatingIp
from resources.network import Network
from resources.metadata import Metadata
from resources.keypair import Keypair
from resources.instance import Instance
from resources.router import Router
from resources.project import Project
from resources.login import Login
from resources.image import Image
from resources.instance_tf import InstanceTf, Task

import os
import logging
from marshmallow import ValidationError
# from marshmallow.exceptions import  ValidationError
from openstack.exceptions import HttpException, SDKException

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
app.logger.debug('Gunicorn logging start')
app.secret_key = os.urandom(12).hex()
app.config["PROPAGATE_EXCEPTIONS"] = True

api = Api(app)
app.permanent_session_lifetime = 10000


@app.errorhandler(HttpException)
def handle_exception(e):
    app.logger.info("HTTPException handled: " + str(e))
    return {}, 400


@app.errorhandler(SDKException)
def handle_exception(e):
    app.logger.info("SDKException handled, probably bad OIDC token on input")
    return {"message": e.message.message}, e.message.http_status


@app.errorhandler(ValidationError)
def handle_exception(e):
    app.logger.info("(Marshmallow) ValidationError handled, bad format, reason: "+str(e))
    return {}, 400


@app.errorhandler(KeyError)
def handle_exception(e):
    app.logger.info("KeyError handled, reason: " + str(e))
    if str(e) == "'token'" or str(e) == "'project_id'":
        return {"message": "unauthorized, please log in"}, 401
    return {}, 400


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.info("Unknown" + str(type(e)) + "error: "+str(e))
    return {}, 500



api.add_resource(Limit, '/limits/')

api.add_resource(SecurityGroup, '/security_groups/', '/security_groups/<string:security_group_id>/')
api.add_resource(SecurityGroupRule,
                 '/security_groups/<string:security_group_id>/security_group_rules/',
                 '/security_groups/<string:security_group_id>/security_group_rules/<string:security_group_rule_id>/')

api.add_resource(Gateway, '/gateways/', '/gateways/<string:router_id>/')
api.add_resource(FloatingIp, '/floating_ips/', '/floating_ips/<string:floating_ip_id>/')
api.add_resource(Network, '/networks/', '/networks/<string:network_id>/')

api.add_resource(Metadata, '/metadata/<string:instance_id>/')

api.add_resource(Keypair, '/keypairs/', '/keypairs/<string:keypair_id>/')

api.add_resource(Instance, '/instances/', '/instances/<string:instance_id>/')

api.add_resource(Router, '/routers/', '/routers/<string:router_id>/')

api.add_resource(Project, '/projects/')

api.add_resource(Image, '/images/', '/images/<string:image_id>/')
api.add_resource(Task, '/tasks/', '/tasks/<string:task_id>/')
api.add_resource(InstanceTf, '/instances_tf/')

api.add_resource(Login, '/')

if __name__ == '__main__':
    app.run()
