import os

from core.resources.Option import OptString, OptBool, OptList
from core.resources.printer import print_error, print_info, print_status
from core.resources.request import BaseRequest
import requests
import json


class Request(BaseRequest):
    __info__ = {
        "name": "Request module",
        "authors": (
            "AjferSanjo",
        ),
    }

    host = OptString("")
    scheme = OptString("")
    path = OptString("")
    payload = OptString("")
    headers = OptList("")
    query_params = OptList("")
    path_params = OptList("")

    def get(self):

        try:
            self._assert_valid()
            print_info("Aiming for: " + self.scheme + "://" + self.host + self.path)
            self.path = self._forge_path_params()
            r = requests.get(self.scheme + "://" + self.host + self.path, headers=self.headers)
            for key in r.headers:
                print_info(key, r.headers[key])
            print("Body:" + r.text)
        except Exception as ex:
            print_error(str(ex))

    def post(self):

        try:
            self._assert_valid()
            print_info("Aiming for: " + self.scheme + "://" + self.host + self.path)
            self.path = self._forge_path_params()
            r = requests.post(self.scheme + "://" + self.host + self.path, headers=self.headers, data=self.payload)
            for key in r.headers:
                print_info(key, r.headers[key])
            print("Body:" + r.text)
        except Exception as ex:
            print_error(ex)

    def put(self):

        try:
            self._assert_valid()
            print_info("Aiming for: " + self.scheme + "://" + self.host + self.path)
            self.path = self._forge_path_params()
            r = requests.put(self.scheme + "://" + self.host + self.path, headers=self.headers, data=self.payload)
            for key in r.headers:
                print_info(key, r.headers[key])
            print("Body:" + r.text)
        except Exception as ex:
            print_error(str(ex))

    def delete(self):

        try:
            self._assert_valid()
            print_info("Aiming for: " + self.scheme + "://" + self.host + self.path)
            self.path = self._forge_path_params()
            r = requests.delete(self.scheme + "://" + self.host + self.path, headers=self.headers, data=self.payload)
            for key in r.headers:
                print_info(key, r.headers[key])
            print("Body:" + r.text)
        except Exception as ex:
            print_error(str(ex))


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
                        setattr(self, key, data[p][0])
                        self.module_attributes[key][0] = data[p][0]
                        continue
        print_status("Template {} loaded successfully".format(args[0]))

    def _assert_valid(self):
        if self.host is None or self.host is "":
            raise Exception("Must specify valid host")
        if self.path is None or self.path is "":
            raise Exception("Must specify valid path")
        if self.scheme != "http" and self.scheme != "https":
            raise Exception("Must specify valid scheme: [ https | http ]")

    def _forge_path_params(self):
        url_raw = self.path
        for param in self.path_params:
            if url_raw.find("{"+param+"}") != -1:
                url_raw = url_raw.replace("{"+param+"}", self.path_params[param])

        return url_raw