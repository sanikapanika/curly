import os

from core.resources.Option import OptString, OptBool, OptList
from core.resources.printer import print_error, print_info, print_status
from core.resources.request import BaseRequest
import requests
import json


class Request(BaseRequest):
    __info__ = {
        "name": "Post Request module",
        "authors": (
            "AjferSanjo",
        ),
    }

    host = OptString("")
    ssl = OptBool(False)
    path = OptString("")
    payload = OptString("")
    headers = OptList("")
    query_params = OptList("")

    def run(self):
        if self.host is None or self.host is "":
            print_error("Must specify valid host")
            return
        if self.path is None or self.path is "":
            print_error("Must specify valid path")
            return
        if self.ssl:
            self.host = "https://" + self.host
        else:
            self.host = "http://" + self.host

        r = requests.post(self.host + self.path, data=self.payload, headers=self.headers)

        print_info(r.text)

    def save(self, args):
        if os.path.isfile('templates/post/' + args[0] + '.json'):
            print_error('File with given name already exists, pick another')
            return
        print_status("Saving template as json...")
        with open("templates/post/" + args[0] + '.json', 'w') as outfile:
            json.dump(self.module_attributes, outfile)

    def load(self, args):
        if not os.path.isfile('templates/post/' + args[0] + '.json'):
            print_error("File with given name does not exist")
            return
        print_status("Loading template {}".format(args[0]))
        with open("templates/post/" + args[0] + '.json') as json_file:
            data = json.load(json_file)
            for key in self.module_attributes:
                for p in data:
                    if key == p:
                        self.module_attributes[key][0] = data[p][0]
                        continue
        print_status("Template {} loaded successfully".format(args[0]))

    def _everything_set(self):
        if self.host is not None and self.path is not None:
            return True
        else:
            return False
