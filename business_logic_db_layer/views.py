import requests
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.shortcuts import render

# Create your views here.
from django.views import View
from drf_yasg.utils import swagger_auto_schema
from requests import Response
from rest_framework import viewsets, mixins
from rest_framework.views import APIView

from travelando import settings
import json
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Create your views here.
class SearchView(APIView):
    def get_search(self, parameters):
        response = requests.get(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/search", parameters)
        return response

    def post(self, request):
        body = request.body.decode('utf-8')
        parameters = json.loads(body)

        print(parameters)
        context = parameters['context']
        user_id = parameters['request_parameters']['user_id']

        response_query = requests.get(
            f"http://{settings.SERVICE_UTILITY_HOST}:{settings.SERVICE_UTILITY_PORT}/{settings.SERVICE_UTILITY}/query_selection",
            context)
        query = json.loads(response_query.content)['query']
        parameters['query'] = query

        information = ""
        path_difficulty = ""
        order = ""

        for val in context['information']:
            information += val + " "

        for val in context['path_difficulty']:
            path_difficulty += val + " "

        for val in context['order']:
            order += val + " "

        search = {
            'subject': context['subject'],
            'checkin': context['checkin'],
            'city': context['comune'],
            'comune_from': context['comune_from'],
            'comune_to': context['comune_to'],
            'class_to': context['class_to'],
            'class_from': context['class_from'],
            'region': context['region'],
            'poi_activity_from': context['poi_activity_from'],
            'poi_activity_to': context['poi_activity_to'],
            'path_number': context['path_number'],
            'information': information,
            'shop_enum': context['shop_enum'],
            'order': order,
            'path_difficulty': path_difficulty,
            'info_equipment': context['info_equipment'],
            'time_period': context['time_period'],
            'type': context['type'],
            'ordinal': context['ordinal'],
            'user_id': user_id
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
        user_id = parameters.get('user_id', None)

        get_parameters = {'user_id': user_id}

        response = requests.get(
            f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/search/",
            get_parameters)

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

        response = Template.retrieve_search_response_message(results)

        return JsonResponse(response)


class ResultView(APIView):
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
            if address:
                response = self.create_new_result(information_result, address["id"])
        return response

    def save_result(self, parameters):
        ordinal = parameters['request_parameters']['ordinal']

        response = requests.post(
            f"http://{settings.SERVICE_MYDB_ADAPTER_LAYER_HOST}:{settings.SERVICE_MYDB_ADAPTER_LAYER_PORT}/{settings.SERVICE_MYDB_ADAPTER_LAYER}/result/",
            None, parameters)

        print(f"PARAMETERS: {parameters}")

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
                        address = addresses[index - 1]
                    else:
                        last = len(results) - 1
                        result = results[last]
                        address = addresses[last]
                    print(f"RESULT: {result}")
                    result['user_id'] = parameters['request_parameters']['user_id']
                    response = self.create_single_result(result, address)
                    response = Template.save_response_message("result", response.status_code)
                else:
                    status_code = []
                    index = -1
                    for result in results:
                        index += 1
                        result['user_id'] = parameters['request_parameters']['user_id']
                        response = self.create_single_result(result, addresses[index])
                        status_code.append(response.status_code)
                    if 201 in status_code:
                        response.status_code = 201
                        response = Template.save_response_message("results", response.status_code)
        else:
            if ordinal:
                response = Template.save_response_message("result", response.status_code)
            else:
                response = Template.save_response_message("results", response.status_code)
        print(f"RETRIEVE RESPONSE: {response}")
        return response

    def retrieve_result(self, parameters):
        ordinal = parameters.get('ordinal', None)
        number = parameters.get('number', None)
        info = parameters.get('info', None)
        subject = parameters.get('Class', None)
        path_difficulty = parameters.get('DifficultyActivityPath', None)
        shop_enum = parameters.get('ShopEnum', None)

        get_parameters = {'user_id': parameters.get('user_id')}
        if number and info:
            get_parameters[info] = number

        response = requests.get(
            f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/result/", get_parameters)

        response_content = response.content.decode('utf-8')
        response_json = json.loads(response_content)
        results = response_json

        print(f"RESULTS WITH USER_ID: {results}")

        if subject != '':
            type_results = []
            for result in results:
                if result['type'] == subject:
                    type_results.append(result)
            results = type_results

        if path_difficulty != '':
            difficulty_result = []
            for result in results:
                if result['path_difficulty'] == path_difficulty:
                    difficulty_result.append(result)
            results = difficulty_result

        if shop_enum != '':
            shop_result = []
            for result in results:
                if result['shop_enum'] == shop_enum:
                    shop_result.append(result)
            results = shop_result

        if ordinal:
            if ordinal != "last":
                ordinal = int(float(ordinal))
                required_index = ordinal - 1
            else:
                required_index = len(results) - 1
            if required_index in range(len(results)):
                current_index = -1
                for result in results:
                    current_index += 1
                    if current_index == required_index:
                        results = [result]
            else:
                results = []

        new_results = []
        for result in results:
            address_index = result["address"]
            address_response = requests.get(
                f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/address/{result['address']}/",
                None)
            address_content = address_response.content.decode('utf-8')
            address_json = json.loads(address_content)
            new_result = {'result_information': result, 'address_information': address_json}
            new_results.append(new_result)

        response = Template.retrieve_result_response_message(new_results)
        return response

    def post(self, request):
        body = request.body.decode('utf-8')
        parameters = json.loads(body)

        context = parameters['context']

        response_query = requests.get(
            f"http://{settings.SERVICE_UTILITY_HOST}:{settings.SERVICE_UTILITY_PORT}/{settings.SERVICE_UTILITY}/query_selection",
            context)
        query = json.loads(response_query.content)['query']
        parameters['query'] = query

        response = self.save_result(parameters)
        print(f"POST response: {response}")

        return JsonResponse(response)

    def get(self, request):
        parameters = request.GET

        response = self.retrieve_result(parameters)

        return JsonResponse(response)

class DeleteView(APIView):
    def remove_item(self, parameters):
        ordinal = parameters.get('ordinal', None)
        number = parameters.get('number', None)
        info = parameters.get('Info', None)
        type = parameters.get('type', None)
        subject = parameters.get('Class', None)
        path_difficulty = parameters.get('DifficultyActivityPath', None)
        shop_enum = parameters.get('ShopEnum', None)
        user_id = parameters.get('user_id', None)

        get_parameters = {'user_id': user_id}
        response = requests.get(
            f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/" +
            type + "/", get_parameters)
        response_content = response.content.decode('utf-8')
        response_json = json.loads(response_content)
        results = response_json

        print(f"RESULTS TO DELETE WITH USER ID: {results}")

        if subject != '':
            type_results = []
            for result in results:
                if result['type'] == subject:
                    type_results.append(result)
            results = type_results

        if path_difficulty != '':
            difficulty_result = []
            for result in results:
                if result['path_difficulty'] == path_difficulty:
                    difficulty_result.append(result)
            results = difficulty_result

        if shop_enum != '':
            shop_result = []
            for result in results:
                if result['shop_enum'] == shop_enum:
                    shop_result.append(result)
            results = shop_result

        if ordinal:
            if ordinal != "last":
                ordinal = int(float(ordinal))
                required_index = ordinal - 1
            else:
                required_index = len(results) - 1
            if required_index in range(len(results)):
                current_index = -1
                for result in results:
                    current_index += 1
                    if current_index == required_index:
                        results = [result]
            else:
                results = []

        status_codes = []
        for result in results:
            if info == 'id':
                id = int(float(number))
            else:
                id = result['id']
            print(f'id {id}')
            response = requests.delete(
                f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/" + type + "/" + str(id) + "/")
            print(f"status code {response.status_code}")
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
            status_code = 500

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
                result_information = result['result_information']
                address_information = result['address_information']
                type = result_information['type']

                message += f'Result [{result_information["id"]}]:\n' \
                           f'• Name: {result_information["name"]}\n'
                if type == 'Hotel':
                    message += f'• Type: {result_information["accommodation_type"]}\n'
                    if result_information["stars"] is not None:
                        message += f' with {result_information["stars"]} star'
                        if result_information['stars'] > 1:
                            message += 's'

                    check = False
                    if result_information['start_hour'] != 'None':
                        message += f'• Check-in from {result_information["start_hour"]}'
                    elif result_information['end_hour'] != 'None':
                        message += f'• Check-in until {result_information["end_hour"]}\n'
                        check = True

                    if result_information['end_hour'] != 'None' and not check:
                        message += f' to {result_information["end_hour"]}\n'
                elif type == 'ActivityPath':
                    message += f'• Type: Path\n'
                    message += f'• From {result_information["path_from"]} to {result_information["path_to"]}\n' \
                               f'• Total time: {result_information["time"]} minutes\n' \
                               f'• Total distance: {result_information["path_length"]} meters\n' \
                               f'• Difficulty: {result_information["path_difficulty"]}'
                elif type == 'Shop':
                    message += f'• Type: Shop\n'
                if type != 'ActivityPath':
                    message += f'• Address: {address_information["street"]} {address_information["number"]}, {address_information["city"]} ({address_information["province"]})'
                message += f'\n\n'
        else:
            message = "No results to show"
        messages.append(message)

        return messages

    @staticmethod
    def retrieve_search_response_templates(results):
        messages = []
        message = ""
        if results:
            for result in results:
                message += f'Search [{result["id"]}] with fields:\n'
                if result["subject"] != "":
                    message += f'• subject: {result["subject"]}\n'
                if result["city"] != "":
                    message += f'• city: {result["city"]}\n'
                if result["checkin"] != "":
                    message += f'• check-in: {result["checkin"]}\n'
                if result["comune_from"] != "":
                    message += f'• comune from: {result["comune_from"]}\n'
                if result["comune_to"] != "":
                    message += f'• comune to: {result["comune_to"]}\n'
                if result["class_from"] != "":
                    message += f'• class from: {result["class_from"]}\n'
                if result["class_to"] != "":
                    message += f'• class to: {result["class_to"]}\n'
                if result["region"] != "":
                    message += f'• region: {result["region"]}\n'
                if result["poi_activity_from"] != "":
                    message += f'• activity from: {result["poi_activity_from"]}\n'
                if result["poi_activity_to"] != "":
                    message += f'• activity to: {result["poi_activity_to"]}\n'
                if result["path_number"] != "":
                    message += f'• path number: {result["path_number"]}\n'
                if result["information"] != "":
                    message += f'• information: {result["information"]}\n'
                if result["shop_enum"] != "":
                    message += f'• shop enum: {result["shop_enum"]}\n'
                if result["order"] != "":
                    message += f'• order: {result["order"]}\n'
                if result["path_difficulty"] != "":
                    message += f'• path difficulty: {result["path_difficulty"]}\n'
                if result["info_equipment"] != "":
                    message += f'• equipment information: {result["info_equipment"]}\n'
                if result["time_period"] != "":
                    message += f'• time period: {result["time_period"]}\n'
                if result["type"] != "":
                    message += f'• type: {result["type"]}\n'
                if result["ordinal"] != "":
                    message += f'• ordinal: {result["ordinal"]}\n'
                message += "\n"
        else:
            message = "No searches to show"
        messages.append(message)

        return messages

    @staticmethod
    def save_response_templates(type, status_code):
        message = []
        print(f"DB STATUS: {status_code}")

        if status_code == 200:
            message.append(f"The {type} is already saved!")
        elif status_code == 201:
            message.append(f"{type.title()} successfully saved!")
        elif status_code == 404:
            message.append(f"No {type} found to save!")
        else:
            message.append(f"ERROR: Something was wrong!")
        print(f"Final message: {message}")
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