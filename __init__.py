import datetime
import re
import time

from mycroft import MycroftSkill, intent_file_handler


class AbrMicrowave(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

        # Current status of the microwave
        self.state = {
            "status": 0,  #  microwave on/off
            "heat_mode": "medium",  # Literal["low", "medium", "high"], current heat mode
            "timer": 0,  # int, keeps track of the cooking time in seconds
            "light": 0,  # microwave light on/off
        }
        # Avaialble heat/power modes
        self.heat_modes = ("low", "medium", "high")

        # time to reheat (in seconds) per 1 unit of food
        # TODO: add power/heat level info
        self.reheat_foods = {
            "coffee": 60,
            "water": 60,
            "milk": 60,
            "hot chocolate": 60,
            "apple cider": 60,
            "soup": 60,
            "noodle soup": 60,
            "rice": 60,
            "pasta": 60,
            "mashed potatoes": 60,
            "casserole": 60,
            "frozen food": 60,
            "dinner plate": 60,
            "burger": 60,
            "sandwich": 60,
        }

    def _extract_number(self, s: str) -> int:
        """
        Extract numbers from a string
        """
        str_num = "".join([x for x in s if x.isnumeric()])
        return round(float(str_num))

    def _extract_and_set_time(self, time_entity: str) -> None:
        """
        Extract number from the input string, convert the number to
        seconds, and update state["timer"].
        """
        time = self._extract_number(time_entity)
        if "second" in time_entity:
            self.state["timer"] = time
        elif "minute" in time_entity:
            self.state["timer"] = time * 60
        elif "hour" in time_entity:
            self.state["timer"] = time * 3600

    def _time_display_and_update(self) -> None:
        """
        Print countdown to screen and update state["timer"].
        """
        for i in range(self.state["timer"], -1, -1):
            if self.state["status"]:
                print(f"{datetime.timedelta(seconds=i)}", end="\r", flush=True)
                time.sleep(1)
                self.state["timer"] -= 1
        self.acknowledge()

    def _validate_time(self, text: str) -> bool:
        match = re.search(r"\d+ (second|minute|hour)s?", text)
        if match:
            self._extract_and_set_time(match.group(0))
            return True
        return False

    def initialize(self):
        self.register_entity_file("time.entity")
        self.register_entity_file("food.entity")
        self.register_entity_file("reheat_food.entity")
        self.register_entity_file("quantity.entity")

    # ------------------------------------------------ REHEAT INTENT

    @intent_file_handler("reheat.basic.intent")
    def handle_reheat_basic(self, message):
        """
        Handles basic reheat/heat commands that do not
        contain any time-specific or food-specific information (food type and quantity).
        """
        self.log.info("In REHEAT BASIC handler")
        time = self.get_response(
            f"For how long?",
            validator=self._validate_time,
            num_retries=0,
            on_fail="Sorry, I did not catch that",
        )
        if "heat_mode" in message.data:
            self.state["heat_mode"] = message.data["heat_mode"]
        if time is not None:
            self._extract_and_set_time(time)
            self.state["status"] = 1
            self._time_display_and_update()

    @intent_file_handler("reheat.time.specific.intent")
    def handle_reheat_time_specific(self, message):
        """
        Handles time-specific reheat/heat commands such as
        'heat my food for 30 seconds'. That is, it handles
        commnads that do NOT include food specific information but include
        timing information.
        """
        self.log.info("In REHEAT TIME SPECIFIC handler")
        self.state["status"] = 1
        if "heat_mode" in message.data:
            self.state["heat_mode"] = message.data["heat_mode"]
        self._extract_and_set_time(message.data["time"])
        self._time_display_and_update()

    @intent_file_handler("reheat.food.specific.intent")
    def handle_reheat_food_specific(self, message):
        """
        Handles food-specific reheat/heat commands such as
        'heat 2 sandwiches', where the user specifies the type and
        quantity of food. Note that that timing information
        is derived from the quantity of food, if the food is part of
        'reheat_food.entity'. Otherwise, a prompt asks for timing info,
        and then adds it to the database.

        TODO: Add heat_mode info to reheat_foods database.
        """
        self.log.info("In REHEAT FOOD SPECIFIC handler")
        data = message.data
        if "reheat_food" in data:
            food = data["reheat_food"]
            quantity = self._extract_number(data["quantity"])
            time = self.reheat_foods[food]  # time per unit of food
            # time = round(time * quantity)
            self.state["timer"] = time
            self.state["status"] = 1
            self._time_display_and_update()
        elif "food" in data and data["food"] not in self.reheat_foods:
            food = data["food"]
            time = self.get_response(
                f"Sorry, the specified item is not in the database. Please specify the duration.",
                validator=self._validate_time,
                num_retries=0,
                on_fail="Sorry, I did not catch that",
            )
            quantity = self._extract_number(data["quantity"])
            if time is not None:
                self._extract_and_set_time(time)
                unit_time = round(self.state["timer"] / quantity)
                self.state["status"] = 1
                self._time_display_and_update()
                # TODO: store all reheat food info in a file so that it does not disappear
                # when mycroft is restarted.
                self.reheat_foods[food] = unit_time
                self.log.info(f"Added {food} to the Reheat database.")
        elif "food" in data and data["food"] in self.reheat_foods:
            food = data["food"]
            quantity = self._extract_number(data["quantity"])
            time = self.reheat_foods[food]  # time per unit of food
            # time = round(time * quantity)
            self.state["timer"] = time
            self.state["status"] = 1
            self._time_display_and_update()

    # ------------------------------------------------ MISC Intents

    @intent_file_handler("stop.intent")
    def handle_stop(self):
        """
        Handles utterances that request to stop the microwave midway.
        """
        self.log.info("In STOP handler")
        self.state["status"] = 0
        self.state["timer"] = 0


def create_skill():
    return AbrMicrowave()
