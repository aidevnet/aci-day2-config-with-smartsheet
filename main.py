"""Integrate Smartsheet API with Cisco ACI APIC
#                                                                      #
Use Smartsheets to perform 8 common ACI configuration use cases:
    * Deploy an application
    * Create static path binding
    * Configure contracts
    * Configure filters
    * Configure policy groups
    * Configure switch interface profiles
    * Associate interface to policy groups
    * Associate EPGs to contracts
The application is divided into frontend and backend components. The frontend
can be started by navigating to the frontend folder and opening the index.html
file with an Internet browser. The backend component is a FLASK application 
and can be started with:

export FLASK_APP=main.py
python -m flask run --host=localhost --port=3000
export ANSIBLE_STDOUT_CALLBACK=json

For development purposes, ngrok was used for receiving the Smartsheet webhooks 
and ngrok can be started with:

ngrok http 3000

In a production environment, port forwarding should be enabled and inbound 
Internet access given to the FLASK application.

Required module variables:
See requirements.txt
Outputs:
    Creates Ansible var files and playbooks for each configuration change
Version log
v1      2021-0727   Published in automation exchange
"""

__version__ = '1'
__author__ = 'Adrian Iliesiu - ailiesiu@cisco.com'
__license__ = "Cisco Sample Code License, Version 1.1 - https://developer.cisco.com/site/license/cisco-sample-code-license/"

from modules.initiate import Initiate
from modules.process import Process
from modules.status import Status
from flask import Flask, request, Response
from datetime import date
import smartsheet
import threading
import json

app = Flask(__name__)

# receives callbacks from Smartsheet.
@app.route("/", methods=["POST"])
def verification():
    # Callback could be due to validation, status change, or actual sheet change events.
    try:
        body = request.get_json()
        # Received challenge for enabling webhook.
        if "challenge" in body:
            print("[Initialize] - Received verification callback")
            data = {'smartsheetHookResponse': body["challenge"]}
            response = Response(response=json.dumps(
                data), status=200, mimetype='application/json')
            # Verify server is listening by echoing challenge value.
            return response
        # Received sheet update.
        elif "events" in body:
            now = date.today()
            events = body["events"]
            print(f"[Sheet Update] - Received event callback with {len(events)} events at {now}")
            response = process.process_events(body, initiate.smartsheet_client)

            thread_status = threading.Thread(group=None, target=status.send_update(response), name="Thread-status")
            thread_status.daemon = True
            thread_status.start()

            # the following callback response must be received within a few seconds.
            # for complex processing, you will need to queue up pending work.
            return Response(status=200)
        # Received status callback.
        elif "new_web_hook_status" in body:
            print(f"[Initialize] - Received status callback, new status: {body}")
            return Response(status=200)
        # Received unknown callback.
        else:
            print(f"[Initialize] - Received unknown callback: {body}")
            return Response(status=200)

    except Exception as e:
        print(e)
        data = {"Error": e}
        response = Response(response=json.dumps(data), status=500, mimetype='application/json')
        return response

# Start up when Flask Starts
def configure():
    global initiate, process, status
    initiate = Initiate()
    process = Process(initiate.smartsheet_client)
    status = Status(initiate.smartsheet_client, initiate.status_sheet)

# Runs configure() in a second thread when Flask starts
thread_startup = threading.Thread(group=None, target=configure, name="Thread-startup")
thread_startup.daemon = True
thread_startup.start()
