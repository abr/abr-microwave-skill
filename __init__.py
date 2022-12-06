import datetime
import re
import time

import mycroft
from mycroft import MycroftSkill, intent_file_handler


class AbrMicrowave(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

        # Current status of the microwave
        """
        status: int
            0: microwave off
            1: microwave on or running
            2: microwave in timer mode
        heat_mode: str
            current heat mode: one of low, medium or high
        type: str
            One of defrost, cook and reheat. This assumes that specifying the heat_level
            and time to cook is not sufficient.
        timer: int
            Keeps track of time in seconds. When status=1, it corresponds to running the microwave,
            and when status=2, it is simply used as a timer (i.e with microwave off)
        light : int
            0: light off
            1: ligt on
        """
        self.state = {
            "status": 0,
            "heat_mode": "medium",
            "type": "reheat",
            "timer": 0,
            "light": 0,
        }
        self.paused_state = (
            {}
        )  # used in pausing and resuming (in pause_handler and resume_handler)

        # Avaialble heat/power modes
        self.heat_modes = ["low", "medium", "high"]

        # food databases
        # {"food name": [type, heat level, cooking time per unit in seconds]}
        self.reheat_foods = {
            "default": ["reheat", "medium", 60],
            "coffee": ["reheat", "medium", 60],
            "water": ["reheat", "medium", 60],
            "milk": ["reheat", "medium", 60],
            "hot chocolate": ["reheat", "medium", 60],
            "apple cider": ["reheat", "medium", 60],
            "soup": ["reheat", "medium", 60],
            "noodle soup": ["reheat", "medium", 60],
            "rice": ["reheat", "medium", 60],
            "pasta": ["reheat", "medium", 60],
            "mashed potatoes": ["reheat", "medium", 60],
            "casserole": ["reheat", "medium", 60],
            "frozen food": ["reheat", "medium", 60],
            "dinner plate": ["reheat", "medium", 60],
            "dinner plates": ["reheat", "medium", 60],
            "burger": ["reheat", "medium", 60],
            "burgers": ["reheat", "medium", 60],
            "sandwich": ["reheat", "medium", 60],
            "sandwiches": ["reheat", "medium", 60],
        }

        self.cook_foods = {
            "default": ["cook", "high", 60],
            "popcorn": ["cook", "high", 60],
            "pop corn": ["cook", "high", 60],
            "frozen vegetables": ["cook", "high", 60],
            "frozen veggies": ["cook", "high", 60],
            "broccoli": ["cook", "high", 60],
            "oatmeal": ["cook", "high", 60],
            "potato": ["cook", "high", 60],
            "potatoes": ["cook", "high", 60],
            "sweet potato": ["cook", "high", 60],
            "sweet potatoes": ["cook", "high", 60],
            "hot dog": ["cook", "high", 60],
            "hot dogs": ["cook", "high", 60],
            "corn on the cob": ["cook", "high", 60],
            "corn": ["cook", "high", 60],
        }

        self.defrost_foods = {
            "default": ["defrost", "low", 60],
            "corn": ["defrost", "low", 60],
            "peas": ["defrost", "low", 60],
            "vegetables": ["defrost", "low", 60],
            "broccoli": ["defrost", "low", 60],
            "chicken": ["defrost", "low", 60],
            "ground beef": ["defrost", "low", 60],
            "salmon fillet": ["defrost", "low", 60],
            "salmon filltes": ["defrost", "low", 60],
            "pork": ["defrost", "low", 60],
            "sausage": ["defrost", "low", 60],
            "sauages": ["defrost", "low", 60],
        }

        self.foods = {
            "defrost": self.defrost_foods,
            "cook": self.cook_foods,
            "reheat": self.reheat_foods,
        }

        self.types_expanded = {
            "heat": "reheat",
            "reheat": "reheat",
            "cook": "cook",
            "microwave": "cook",
            "defrost": "defrost",
        }

    def _extract_number(self, s: str) -> int:
        """
        Extract numbers from a string
        """
        str_num = "".join([x for x in s if x.isnumeric()])
        return round(float(str_num))

    def _extract_time(self, time_entity):
        """
        Extract time from the string and convert it to seconds.
        """
        hrs = re.search(r"\d+ (hour|hours)", time_entity)
        hrs = self._extract_number(hrs.group()) if hrs else 0

        mins = re.search(r"\d+ (minute|minutes)", time_entity)
        mins = self._extract_number(mins.group()) if mins else 0

        secs = re.search(r"\d+ (second|seconds)", time_entity)
        secs = self._extract_number(secs.group()) if secs else 0

        total_time = (hrs * 3600) + (mins * 60) + secs
        return total_time

    def _extract_and_set_time(self, time_entity):
        """
        Extract number from the input string, convert the number to
        seconds, and update state["timer"].
        """
        time = self._extract_time(time_entity)
        self.state["timer"] = time

    def _set_state_to_default(self):
        self.state["status"] = 0
        self.state["heat_mode"] = "medium"
        self.state["type"] = "reheat"
        self.state["timer"] = 0
        self.state["light"] = 0

    def _run_and_display_time(self) -> None:
        """
        Print countdown to screen and update state["timer"].
        Note the when the loop exits or if status changes while the function is running,
        the 'set_state_to_default' is called.
        """
        while self.state["timer"] >= 0:
            if self.state["status"] != 0:
                print(
                    f"{datetime.timedelta(seconds=self.state['timer'])}",
                    end="\r",
                    flush=True,
                )
                time.sleep(1)
                self.state["timer"] -= 1
            else:
                self._set_state_to_default()
                break
        self._set_state_to_default()

    def _validate_new_item(self, text: str) -> bool:
        if text:
            return True
        return False

    def _validate_heat_level(self, text: str) -> bool:
        _, score = mycroft.util.parse.match_one(text, self.heat_modes)
        if score > 0.5:
            return True
        return False

    def initialize(self):
        self.register_entity_file("time.entity")
        self.register_entity_file("types_expanded.entity")
        self.register_entity_file("type.entity")
        self.register_entity_file("foods.entity")
        self.register_entity_file("quantity.entity")

    # ------------------------------------------------ Cook/Reheat/Defrost Intents

    def _validate_time(self, text: str) -> bool:
        match = re.search(r"\d+ (second|minute|hour)s?", text)
        if match:
            self._extract_and_set_time(match.group(0))
            return True
        return False

    @intent_file_handler("basic.intent")
    def handle_basic(self, message):
        """
        Handles basic cook/reheat/defrost commands that do not
        contain any time-specific or food-specific information (food type and quantity).
        Examples: run the microwave, cook my food, heat my food.
        """

        self.log.info("In BASIC handler")

        if "types_expanded" in message.data:
            type_ = self.types_expanded[message.data["types_expanded"]]
        else:
            type_ = "reheat"

        time = self.get_response(
            f"For how long?",
            validator=self._validate_time,
            num_retries=0,
        )

        if "heat_mode" in message.data:
            self.state["heat_mode"] = message.data["heat_mode"]
        else:
            self.state["heat_mode"] = self.foods[type_]["default"][1]

        if time is not None:
            self._extract_and_set_time(time)
            self.state["status"] = 1
            self.state["type"] = type_
            self.log.info(self.state)
            self._run_and_display_time()

    @intent_file_handler("time.specific.intent")
    def handle_time_specific(self, message):
        """
        Handles time-specific defrost commands such as
        'defrost/cook/heat my food for 30 seconds'. That is, it handles
        commnads that do NOT include food specific information but include
        timing information.
        """
        self.log.info("In TIME SPECIFIC handler")

        if "types_expanded" in message.data:
            type_ = self.types_expanded[message.data["types_expanded"]]
        else:
            type_ = "reheat"

        if "heat_mode" in message.data:
            self.state["heat_mode"] = message.data["heat_mode"]
        else:
            self.state["heat_mode"] = self.foods[type_]["default"][1]

        self._extract_and_set_time(message.data["time"])
        self.state["status"] = 1
        self.state["type"] = type_
        self.log.info(self.state)
        self._run_and_display_time()

    @intent_file_handler("food.specific.intent")
    def handle_food_specific(self, message):
        """
        Handles food-specific defrost commands such as
        'defrost/cook/heat 10 ounces of chicken', where the user specifies the type and
        quantity of food. Note that that timing information
        is derived from the quantity of food, if the food is part of
        'foods.entity'. Otherwise, a prompt asks for timing info,
        and then adds it to the database.
        """
        self.log.info("In FOOD SPECIFIC handler")
        if "types_expanded" in message.data:
            type_ = self.types_expanded[message.data["types_expanded"]]
        else:
            type_ = "reheat"
        food = message.data["foods"]
        quantity = self._extract_number(message.data["quantity"])
        time = round(self.foods[type_][food][2] * quantity)  # time per unit of food

        self.state["timer"] = time
        self.state["status"] = 1
        self.state["type"] = type_
        self.state["heat_mode"] = self.foods["type"][food][1]
        self.log.info(self.state)
        self._run_and_display_time()

    # ------------------------------------------------ Timer Intents
    @intent_file_handler("timer.basic.intent")
    def timer_basic_handler(self):
        """
        Handles utterances that do not contain timing information.
        Note that the microwave remains off.
        """
        self.log.info("In TIMER BASIC handler")
        time = self.get_response(
            f"For how long?",
            validator=self._validate_time,
            num_retries=0,
        )
        if time is not None:
            self._extract_and_set_time(time)
            self.state["status"] = 2
            self._run_and_display_time()

    @intent_file_handler("timer.specific.intent")
    def timer_specific_handler(self, message):
        """
        Handles utterances that contain timing information.
        Note that the microwave remains off.
        """
        self.log.info("In TIMER SPECIFIC handler")
        self.state["status"] = 2
        self._extract_and_set_time(message.data["time"])
        self._run_and_display_time()

    @intent_file_handler("timer.query.intent")
    def timer_query_intent(self):
        """
        Handles timer realted queries such as
        'how much time is left on the timer'.
        """

        self.log.info("In TIMER QUERY intent")
        if self.state["timer"] > 0:
            clock_format = str(datetime.timedelta(self.state["timer"]))
            hrs, mins, secs = [int(x) for x in clock_format.split(":")]
            dialogue = ""
            if hrs > 0:
                dialogue += f"{hrs} hour" + "s" * min(hrs - 1, 1)
            if mins > 0:
                dialogue += ", " * min(hrs, 1)
                dialogue += f"{mins} minutue" + "s" * min(mins - 1, 1)
            if secs > 0:
                dialogue += " and " * min(hrs + mins, 1)
                dialogue += f"{secs} second" + "s" * min(hrs - 1, 1)
            self.speak_dialog(f"{dialogue} left on the timer")

    @intent_file_handler("timer.add.intent")
    def timer_add_handler(self, message):
        """
        Handles commands that request to add time to the timer. This
        is to be used when the microwave or the timer is already running
        (i.e status is 1 or 2).
        """

        self.log.info("In TIMER ADD Intent")
        time = self._extract_time(message.data["time"])
        if self.state["status"] != 0:
            self.state["timer"] += time
        else:
            self.speak_dialog("Both microwave and timer are off.")

    # ------------------------------------------------ Personalization Intents

    def _validate_time_quantity_info(self, s: str):
        match = re.search(r"\d+ \w+ for \d+", s)
        if match:
            return True
        return False

    @intent_file_handler("add.new.item.intent")
    def handle_add_new_item(self, message):
        """
        Handles utterances that want to add a new food item to the database.
        Each new item requires the specification of the following information:
        1. reheat/cook/defrost
        2. low/medium/high (assuming here that the type of microwaving listed above does a bit more
        than simply setting that heat or power level).
        3. time (in seconds) per unit of food.
        """

        item_name = self.get_response(
            f"What you like to call the new item?",
            validator=self._validate_new_item,
            num_retries=0,
        )
        if not "type" in message.data:
            self.speak_dialog("Please select type")
            type = self.ask_selection(["cook", "defrost", "reheat"])
        else:
            type = message.data["type"]
        if item_name and type:
            time_info = self.get_response(
                f"""Please set the time to {type} in the following format: X weight for Y time, for example, you could say something like '100 ounces for 2 minutes and 30 seconds.'""",
                validator=self._validate_time_quantity_info,
                num_retries=0,
            )
            if time_info:
                quantity = self._extract_number(time_info.split("for")[0])
                time = round(self._extract_number(time_info.split("for")[1]))
                unit_time = time / quantity
                self.speak_dialog(f"At what heat level would you like to {type}")
                heat_level = self.ask_selection(self.heat_modes)

                if heat_level:
                    self.foods[type][item_name] = [type, heat_level, unit_time]
                    self.log.info(f"{item_name}, {self.foods[type][item_name]}")
                    self.speak_dialog(f"You are all set!")

    # ------------------------------------------------ MISC Intents

    @intent_file_handler("stop.intent")
    def handle_stop(self):
        """
        Handles utterances that request to stop the microwave midway.
        """
        self.log.info("In STOP handler")
        self.state["status"] = 0
        self.state["timer"] = 0
        self.log.info(self.state)

    @intent_file_handler("pause.intent")
    def handle_pause(self):
        """
        Handles requests to pause the ongoing activity (microwaving or countdown timer).
        Stores all the relevant state variables -- everything that is needed to resume the
        activity -- in the dict 'paused_state'.
        """

        self.log.info("In PAUSE handler")
        if self.state["status"] != 0:
            self.paused_state = self.state.copy()
            self.state["status"] = 0
            self.state["timer"] = 0
        else:
            self.speak_dialog("Both microwave and timer are already off.")

    @intent_file_handler("resume.intent")
    def handle_resume(self):
        """
        Handles requests to resume the previously paused activity.
        """
        self.log.info("In RESUME handler")
        if self.state["status"] == 0 and self.paused_state:
            self.state = self.paused_state.copy()
            self.paused_state = {}
            self._run_and_display_time()


def create_skill():
    return AbrMicrowave()
