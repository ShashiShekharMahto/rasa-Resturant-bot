# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher

from typing import Any, Text, Dict, List, Union, Optional
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, ActionReverted
import requests
import ast
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormValidationAction

#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
class Zomato:

    def __init__(self):
        self.api_key = "f3ee06da0d0818c8e258f8650b5bc506"  # Update Zomato API key here
        self.base_url = "https://developers.zomato.com/api/v2.1/"

    def getZomatoLocationInfo(self, location):
        '''
        Takes city name as argument.
        Returns the corressponding city_id.
        '''
        # list storing latitude,longitude...
        location_info = []

        queryString = {"query": location}

        headers = {'Accept': 'application/json', 'user-key': self.api_key}

        res = requests.get(self.base_url + "locations", params=queryString, headers=headers)

        data = res.json()

        if len(data['location_suggestions']) == 0:
            raise Exception('invalid_location')

        else:
            location_info.append(data["location_suggestions"][0]["latitude"])
            location_info.append(data["location_suggestions"][0]["longitude"])
            location_info.append(data["location_suggestions"][0]["entity_id"])
            location_info.append(data["location_suggestions"][0]["entity_type"])
            return location_info

    def get_cuisines(self, location_info):
        """
        Takes City ID as input.
        Returns dictionary of all cuisine names and their respective cuisine IDs in a given city.
        """

        headers = {'Accept': 'application/json', 'user-key': self.api_key}

        queryString = {
            "lat": location_info[0],
            "lon": location_info[1]
        }

        res = requests.get(self.base_url + "cuisines", params=queryString, headers=headers).content.decode("utf-8")

        a = ast.literal_eval(res)
        all_cuisines_in_a_city = a['cuisines']

        cuisines = {}

        for cuisine in all_cuisines_in_a_city:
            current_cuisine = cuisine['cuisine']
            cuisines[current_cuisine['cuisine_name'].lower()] = current_cuisine['cuisine_id']

        return cuisines

    def get_cuisine_id(self, cuisine_name, location_info):
        """
        Takes cuisine name and city id as argument.
        Returns the cuisine id for that cuisine.
        """
        cuisines = self.get_cuisines(location_info)

        return cuisines[cuisine_name.lower()]

    def get_all_restraunts(self, location, cuisine):
        """
        Takes city name and cuisine name as arguments.
        Returns a list of 5 restaurants.
        """

        location_info = self.getZomatoLocationInfo(location)
        cuisine_id = self.get_cuisine_id(cuisine, location_info)

        queryString = {
            "entity_type": location_info[3],
            "entity_id": location_info[2],
            "cuisines": cuisine_id,
            "count": 5
        }

        headers = {'Accept': 'application/json', 'user-key': self.api_key}
        res = requests.get(self.base_url + "search", params=queryString, headers=headers)

        list_of_all_rest = res.json()["restaurants"]

        json = []
        for rest in list_of_all_rest:
            name = rest["restaurant"]["name"]
            thumb = rest["restaurant"]["thumb"]
            url = rest["restaurant"]["url"]
            json.append(name)
            json.append(thumb)
            json.append(url)


        return json

    def get_all_restraunts_without_cuisne(self, location):
        '''
        Takes city name as arguments.
        Returns a list of 5 restaurants.
        '''

        location_info = self.getZomatoLocationInfo(location)

        queryString = {
            "entity_type": location_info[3],
            "entity_id": location_info[2],
            "count": 5
        }

        headers = {'Accept': 'application/json', 'user-key': self.api_key}
        res = requests.get(self.base_url + "search", params=queryString, headers=headers)

        list_ofall_rest = res.json()["restaurants"]
        names_of_all_rest = []
        for rest in list_ofall_rest:
            name = rest["restaurant"]["name"]
            thumb = rest["restaurant"]["thumb"]
            url = rest["restaurant"]["url"]
            list_ofall_rest.append(name)
            list_ofall_rest.append(thumb)
            list_ofall_rest.append(url)

        return names_of_all_rest


class ActionShowRestaurants(Action):

    def name(self):
        return "action_show_restaurants"

    def run(self, dispatcher, tracker, domain):

        user_input = tracker.latest_message['text']

        zo = Zomato()

        # Extracting location either from "location" slot or user input
        #le = BingLocationExtractor()
        location_name = tracker.get_slot('location')
        print('location name ', location_name)
        # if not location_name:
        #     locality, location_name = le.getLocationInfo(str(user_input), tracker)

        if not location_name:
            # Utter template
            return [UserUtteranceReverted(), ActionReverted()]
        else:
            cuisine_type = tracker.get_slot('cuisine')
            list_all_restaurants = zo.get_all_restraunts(location=location_name, cuisine=str(cuisine_type))

            if list_all_restaurants:
                finaldata = []
                for i in range(len(list_all_restaurants)):
                    if i % 3 != 0:
                        continue
                    finaldata.append(list_all_restaurants[i])
                #message = {"name":"{}".format(finaldata)}

                #dispatcher.utter_message(json_message=message)
                mess = " ,".join(finaldata)
                dispatcher.utter_message(text=mess)
            else:
                dispatcher.utter_message(template=
                                         "Sorry no such restaurant of " + cuisine_type.capitalize() + " available at " + location_name + ". Try looking for some other cuisine.")

        return []




class ActionAskLocation(Action):

    def name(self):
        return "action_ask_location_again"

    def run(self, dispatcher, tracker, domain):

        user_input = tracker.latest_message['text']

        zo = Zomato()

        # Extracting location either from "location" slot or user input
        #le = BingLocationExtractor()
        location_name = tracker.get_slot('location')
        print('location name ', location_name)
        # if not location_name:
        #     locality, location_name = le.getLocationInfo(str(user_input), tracker)

        if not location_name:
            # Utter template
            return [UserUtteranceReverted(), ActionReverted()]
