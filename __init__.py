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

        # time to reheat (in seconds) for 1 unit of food
        self.reheat_food = {
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

    def _extract_and_set_time(self, time_entity: str) -> None:
        """
        Extract number from the input string, convert the number to
        seconds, and update state["timer"].
        """
        time = "".join([x for x in time_entity if x.isnumeric()])
        time = int(time)
        if "second" in time_entity:
            self.state["timer"] = time
        elif "minute" in time_entity:
            self.state["timer"] = int(time * 60)
        elif "hour" in time_entity:
            self.state["timer"] = int(time * 3600)

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
        self.register_entity_file("reheat_food.entity")
        self.register_entity_file("quantity.entity")

    # ------------------------------------------------ REHEAT INTENT

    @intent_file_handler("reheat.basic.intent")
    def handle_reheat_basic(self, message):
        """
        Handles basic reheat/heat commands that do not
        contain any time-specific or food-specific information.
        """
        self.log.info("In REHEAT BASIC handler")
        time = self.get_response(
            f"For how long?",
            validator=self._validate_time,
            num_retries=0,
            on_fail="Sorry, I did not catch that",
        )
        if time is not None:
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
        self._extract_and_set_time(message.data["time"])
        self._time_display_and_update()

    @intent_file_handler("reheat.food.specific.intent")
    def handle_reheat_food_specific(self, message):
        """
        Handles food-specific reheat/heat commands such as
        'heat 2 sandwiches'. Note that that timing information
        is derived from the quantity of food, if the food is part of
        'reheat_food.entity' -- otherwise TODO: write a food specific method
        for foods that do not appear in there, with the option of storing
        new food-specific info.
        """
        self.log.info("In REHEAT FOOD SPECIFIC handler")
        food = message.data["reheat_food"]
        quantity = message.data["quantity"]
        time = self.reheat_food[food]  # time per unit of food
        # time = time * quantity
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
