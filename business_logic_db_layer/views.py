import requests
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.shortcuts import render

# Create your views here.
from django.views import View
from requests import Response
from rest_framework import viewsets, mixins
from travelando import settings
import json

# Create your views here.
class SearchView(View):
    def get_search(self, parameters):
        response = requests.get(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/search", parameters)
        return response

    def post(self, request):
        body = request.body.decode('utf-8')
        parameters = json.loads(body)

        context = parameters['context']

        response_query = requests.get(
            f"http://{settings.SERVICE_QUERY_SELECTION_HOST}:{settings.SERVICE_QUERY_SELECTION_PORT}/{settings.SERVICE_QUERY_SELECTION}/query_selection",
            context)
        query = json.loads(response_query.content)['query']
        parameters['query'] = query

        search = {
            'type': context['subject'],
            'date': '2020-05-10',
            'city': context['comune']
        }

        response = self.get_search(search)
        response_content = response.content.decode('utf-8')
        response_json = json.loads(response_content)
        if not response_json:
            response = requests.post(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/search/", None,
                                     search)

        response = Template.save_response_message("search", response.status_code)

        return JsonResponse(response)

    def get(self, request):
        parameters = request.GET
        ordinal = parameters.get('ordinal', None)

        print(parameters)
        get_parameters = {}

        response = requests.get(
            f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/search/",
            get_parameters)

        print(response)
        response_content = response.content.decode('utf-8')
        response_json = json.loads(response_content)
        results = response_json

        if ordinal:
            if ordinal != "last":
                ordinal = int(float(ordinal))
                required_index = ordinal - 1
            else:
                required_index = len(results) - 1
            current_index = -1
            for result in results:
                current_index += 1
                if current_index == required_index:
                    results = [result]

        print(results)
        response = Template.retrieve_search_response_message(results)

        return JsonResponse(response)


class ResultView(View):
    def get_first_address(self, parameters):
        response = requests.get(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/address", parameters)
        if response.status_code == 200:
            json_response = response.json()
            if json_response:
                return json_response[0]
        return None

    def create_address(self, json):
        response = requests.post(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/address/", None, json)
        return response

    def get_or_create_address(self, address):
        response = self.get_first_address(address)
        print(f"get first result: {response}")
        if not response:
            address_response = self.create_address(address)
            if address_response.status_code == 201:
                response = address_response.json()
        return response

    def create_new_result(self, json, address_id):
        json["address"] = address_id
        response = requests.post(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/result/", None, json)
        return response

    def get_result(self, parameters):
        response = requests.get(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/result", parameters)
        return response

    def create_single_result(self, information_result, information_address):
        response = self.get_result(information_result)
        response_content = response.content.decode('utf-8')
        response_json = json.loads(response_content)
        if not response_json:
            address = self.get_or_create_address(information_address)
            print(f"address {address}")
            if address:
                response = self.create_new_result(information_result, address["id"])
        print(f"response code: {response.status_code}")
        return response

    def save_result(self, parameters):
        ordinal = parameters['request_parameters']['ordinal']

        response = requests.post(
            f"http://{settings.SERVICE_MYDB_ADAPTER_LAYER_HOST}:{settings.SERVICE_MYDB_ADAPTER_LAYER_PORT}/{settings.SERVICE_MYDB_ADAPTER_LAYER}/result/",
            None, parameters)

        if response.status_code == 200:
            response_content = response.content.decode('utf-8')
            json_results = json.loads(response_content)
            results = json_results['results']
            addresses = json_results['addresses']

            if results:
                if ordinal:
                    if ordinal != "last":
                        index = int(ordinal)
                        result = results[index - 1]
                        address = addresses[index -1]
                    else:
                        last = len(results) - 1
                        result = results[last]
                        address = addresses[last]
                    response = self.create_single_result(result, address)
                    response = Template.save_response_message("result", response.status_code)
                else:
                    status_code = []
                    index = -1
                    for result in results:
                        index += 1
                        response = self.create_single_result(result, addresses[index])
                        status_code.append(response.status_code)
                    if 201 in status_code:
                        response.status_code = 201
                        response = Template.save_response_message("results", response.status_code)
        else:
            if ordinal:
                print(response)
                response = Template.save_response_message("result", response.status_code)
            else:
                response = Template.save_response_message("results", response.status_code)
        return response

    def retrieve_result(self, parameters):
        ordinal = parameters.get('ordinal', None)
        number = parameters.get('number', None)
        info = parameters.get('info', None)

        get_parameters = {}
        if number and info:
            get_parameters[info] = number

        response = requests.get(
            f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/result/", get_parameters)

        response_content = response.content.decode('utf-8')
        response_json = json.loads(response_content)
        results = response_json

        print(f"RESULTS: {results}")

        if ordinal:
            if ordinal != "last":
                ordinal = int(float(ordinal))
                required_index = ordinal - 1
            else:
                required_index = len(results) - 1
            current_index = -1
            for result in results:
                current_index += 1
                if current_index == required_index:
                    results = [result]

        new_results = []
        for result in results:
            address_index = result["address"]
            print(address_index)
            address_response = requests.get(
                f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/address/{result['address']}/",
                None)
            address_content = address_response.content.decode('utf-8')
            address_json = json.loads(address_content)
            new_result = {"id": result["id"], "name": result["name"], "stars": result["stars"], "type": result["type"],
                          "city": address_json["city"], "street": address_json["street"], "number": address_json["number"],
                          "province": address_json["province"]}
            new_results.append(new_result)

        response = Template.retrieve_result_response_message(new_results)
        return response

    def post(self, request):
        body = request.body.decode('utf-8')
        parameters = json.loads(body)

        context = parameters['context']

        response_query = requests.get(
            f"http://{settings.SERVICE_QUERY_SELECTION_HOST}:{settings.SERVICE_QUERY_SELECTION_PORT}/{settings.SERVICE_QUERY_SELECTION}/query_selection",
            context)
        query = json.loads(response_query.content)['query']
        parameters['query'] = query

        response = self.save_result(parameters)

        return JsonResponse(response)

    def get(self, request):
        parameters = request.GET

        response = self.retrieve_result(parameters)

        return JsonResponse(response)

class DeleteView(View):
    def remove_item(self, parameters):
        ordinal = parameters.get('ordinal', None)
        number = parameters.get('number', None)
        info = parameters.get('Info', None)
        type = parameters.get('type', None)

        response = requests.get(
            f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/" +
            type + "/", None)
        response_content = response.content.decode('utf-8')
        response_json = json.loads(response_content)
        results = response_json

        if ordinal:
            if ordinal != "last":
                ordinal = int(float(ordinal))
                required_index = ordinal - 1
            else:
                required_index = len(results) - 1
            current_index = -1
            for result in results:
                current_index += 1
                if current_index == required_index:
                    results = [result]

        status_codes = []

        for result in results:
            if info == 'id':
                id = int(float(number))
            else:
                id = result['id']
            response = requests.delete(
                f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/" + type + "/" + str(id) + "/")
            status_codes.append(response.status_code)

        if len(status_codes) > 1:
            if 204 in status_codes:
                status_code = 204
            elif 404 in status_codes:
                status_code = 404
        elif len(status_codes) == 1:
            status_code = status_codes[0]
        elif len(status_codes) == 0:
            status_code = 200
        else:
            status_codes = 500

        response = Template.delete_response_message(type, status_code)
        return response

    def post(self, request):
        body = request.body.decode('utf-8')
        parameters = json.loads(body)

        response = self.remove_item(parameters)

        return JsonResponse(response)


class Template:
    @staticmethod
    def retrieve_result_response_templates(results):
        messages = []
        message = ""
        if results:
            for result in results:
                message = f'Result #{result["id"]}: {result["name"]} {result["type"]}'
                if result['stars'] != '':
                    message += f' with {result["stars"]} star'
                    if result['stars'] > 1:
                        message += 's'
                message += f' in {result["street"]} {result["number"]} {result["city"]} ({result["province"]})'
        else:
            message = "No results to show"
        messages.append(message)

        return messages

    @staticmethod
    def retrieve_search_response_templates(results):
        messages = []

        for result in results:
            message = f'Search #{result["id"]} with fields: (subject={result["type"]}, city={result["city"]}, date={result["date"]})'
            messages.append(message)

        return messages

    @staticmethod
    def save_response_templates(type, status_code):
        message = []

        if status_code == 200:
            message.append(f"The {type} is already saved!")
        elif status_code == 201:
            message.append(f"{type.title()} successfully saved!")
        elif status_code == 404:
            message.append(f"No {type} found to save!")
        else:
            message.append(f"ERROR: Something was wrong!")
        return message

    @staticmethod
    def save_response_message(type, status_code):
        message = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": Template.save_response_templates(type, status_code)
                    }
                }
            ]
        }
        return message

    @staticmethod
    def delete_response_templates(type, status_code):
        message = []

        if status_code == 204:
            message.append(f"The {type} is successfully deleted!")
        elif status_code == 404:
            message.append(f"{type.title()} not found!")
        elif status_code == 200:
            message.append(f"No {type} to delete")
        else:
            message.append(f"ERROR: Something was wrong!")
        return message

    @staticmethod
    def delete_response_message(type, status_code):
        message = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": Template.delete_response_templates(type, status_code)
                    }
                }
            ]
        }
        return message

    @staticmethod
    def retrieve_result_response_message(results):
        message = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": Template.retrieve_result_response_templates(results)
                    }
                }
            ]
        }

        return message

    @staticmethod
    def retrieve_search_response_message(results):
        message = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": Template.retrieve_search_response_templates(results)
                    }
                }
            ]
        }

        return message