import datetime
import re
import time

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
            "timer": 0,
            "light": 0,
            "timer_change": 0,
        }
        self.paused_state = {}

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
            "dinner plates": 60,
            "burger": 60,
            "burgers": 60,
            "sandwich": 60,
            "sandwiches": 60,
        }

        self.cook_foods = {
            "popcorn": 60,
            "pop corn": 60,
            "frozen vegetables": 60,
            "frozen veggies": 60,
            "broccoli": 60,
            "oatmeal": 60,
            "potato": 60,
            "potatoes": 60,
            "sweet potato": 60,
            "sweet potatoes": 60,
            "hot dog": 60,
            "hot dogs": 60,
            "corn on the cob": 60,
            "corn": 60,
        }

        self.defrost_foods = {
            "corn": 60,
            "peas": 60,
            "vegetables": 60,
            "broccoli": 60,
            "chicken": 60,
            "ground beef": 60,
            "salmon fillet": 60,
            "salmon filltes": 60,
            "pork": 60,
            "sausage": 60,
            "sauages": 60,
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

    def _run_and_display_time(self) -> None:
        """
        Print countdown to screen and update state["timer"].
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
                break
        self.state["status"] = 0

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
        self.register_entity_file("cook_foods.entity")
        self.register_entity_file("defrost_foods.entity")
        self.register_entity_file("quantity.entity")

    # ------------------------------------------------ REHEAT INTENT

    @intent_file_handler("reheat.basic.intent")
    def handle_reheat_basic(self, message):
        """
        Handles basic reheat/heat commands that do not
        contain any time-specific or food-specific information (food type and quantity).
        """
        self.log.info("In REHEAT BASIC handler")
        self.log.info(message.data)
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
            self._run_and_display_time()

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
        self._run_and_display_time()

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
            self._run_and_display_time()
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
                self._run_and_display_time()
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
            self._run_and_display_time()

    # ------------------------------------------------ Cook Intents
    @intent_file_handler("cook.basic.intent")
    def handle_cook_basic(self, message):
        """
        Handles basic cook/microwave commands that do not
        contain any time-specific or food-specific information (food type and quantity).
        """

        self.log.info("In COOK BASIC handler")
        time = self.get_response(
            f"For how long?",
            validator=self._validate_time,
            num_retries=0,
        )
        if "heat_mode" in message.data:
            self.state["heat_mode"] = message.data["heat_mode"]
        if time is not None:
            self._extract_and_set_time(time)
            self.state["status"] = 1
            self._run_and_display_time()

    @intent_file_handler("cook.time.specific.intent")
    def handle_cook_time_specific(self, message):
        """
        Handles time-specific cook/microwave commands such as
        'cook my food for 30 seconds'. That is, it handles
        commnads that do NOT include food specific information but include
        timing information.
        """
        self.log.info("In COOK TIME SPECIFIC handler")
        self.state["status"] = 1
        if "heat_mode" in message.data:
            self.state["heat_mode"] = message.data["heat_mode"]
        self._extract_and_set_time(message.data["time"])
        self._run_and_display_time()

    @intent_file_handler("cook.food.specific.intent")
    def cook_food_specific(self, message):
        """
        Handles food-specific cook/microwave commands such as
        'cook 1 sweet potato', where the user specifies the type and
        quantity of food. Note that that timing information
        is derived from the quantity of food, if the food is part of
        'cook_foods.entity'. Otherwise, a prompt asks for timing info,
        and then adds it to the database.

        TODO: Add heat_mode info to cook_foods database.
        """
        self.log.info("In COOK FOOD SPECIFIC handler")
        data = message.data
        if "cook_foods" in data:
            food = data["cook_foods"]
            quantity = self._extract_number(data["quantity"])
            time = self.cook_foods[food]  # time per unit of food
            # time = round(time * quantity)
            self.state["timer"] = time
            self.state["status"] = 1
            self._run_and_display_time()
        elif "food" in data and data["food"] not in self.cook_foods:
            food = data["food"]
            time = self.get_response(
                f"Sorry, the specified item is not in the database. Please specify the duration.",
                validator=self._validate_time,
                num_retries=0,
            )
            quantity = self._extract_number(data["quantity"])
            if time is not None:
                self._extract_and_set_time(time)
                unit_time = round(self.state["timer"] / quantity)
                self.state["status"] = 1
                self._run_and_display_time()
                # TODO: store all cook food info in a file so that it does not disappear
                # when mycroft is restarted.
                self.cook_foods[food] = unit_time
                self.log.info(f"Added {food} to the 'cook foods' database.")
        elif "food" in data and data["food"] in self.cook_foods:
            food = data["food"]
            quantity = self._extract_number(data["quantity"])
            time = self.cook_foods[food]  # time per unit of food
            # time = round(time * quantity)
            self.state["timer"] = time
            self.state["status"] = 1
            self._run_and_display_time()

    # ------------------------------------------------ Defrost Intents
    # TODO: reheat, cook and defrost functions are all very similar. Merge?

    @intent_file_handler("defrost.basic.intent")
    def handle_defrost_basic(self, message):
        """
        Handles basic defrost commands that do not
        contain any time-specific or food-specific information (food type and quantity).
        """

        self.log.info("In DEFROST BASIC handler")
        time = self.get_response(
            f"For how long?",
            validator=self._validate_time,
            num_retries=0,
        )
        if "heat_mode" in message.data:
            self.state["heat_mode"] = message.data["heat_mode"]
        if time is not None:
            self._extract_and_set_time(time)
            self.state["status"] = 1
            self._run_and_display_time()

    @intent_file_handler("defrost.time.specific.intent")
    def handle_defrost_time_specific(self, message):
        """
        Handles time-specific defrost commands such as
        'defrost my food for 30 seconds'. That is, it handles
        commnads that do NOT include food specific information but include
        timing information.
        """
        self.log.info("In DEFROST TIME SPECIFIC handler")
        self.state["status"] = 1
        if "heat_mode" in message.data:
            self.state["heat_mode"] = message.data["heat_mode"]
        self._extract_and_set_time(message.data["time"])
        self._run_and_display_time()

    @intent_file_handler("defrost.food.specific.intent")
    def defrost_food_specific(self, message):
        """
        Handles food-specific defrost commands such as
        'defrost 10 ounces of chicken', where the user specifies the type and
        quantity of food. Note that that timing information
        is derived from the quantity of food, if the food is part of
        'defrost_foods.entity'. Otherwise, a prompt asks for timing info,
        and then adds it to the database.

        TODO: Add heat_mode info to defrost_foods database.
        """
        self.log.info("In DEFROST FOOD SPECIFIC handler")
        data = message.data
        if "defrost_foods" in data:
            food = data["defrost_foods"]
            quantity = self._extract_number(data["quantity"])
            time = self.defrost_foods[food]  # time per unit of food
            # time = round(time * quantity)
            self.state["timer"] = time
            self.state["status"] = 1
            self._run_and_display_time()
        elif "food" in data and data["food"] not in self.defrost_foods:
            food = data["food"]
            time = self.get_response(
                f"Sorry, the specified item is not in the database. Please specify the duration.",
                validator=self._validate_time,
                num_retries=0,
            )
            quantity = self._extract_number(data["quantity"])
            if time is not None:
                self._extract_and_set_time(time)
                unit_time = round(self.state["timer"] / quantity)
                self.state["status"] = 1
                self._run_and_display_time()
                # TODO: store all defrost food info in a file so that it does not disappear
                # when mycroft is restarted.
                self.defrost_foods[food] = unit_time
                self.log.info(f"Added {food} to the 'defrost foods' database.")
        elif "food" in data and data["food"] in self.defrost_foods:
            food = data["food"]
            quantity = self._extract_number(data["quantity"])
            time = self.defrost_foods[food]  # time per unit of food
            # time = round(time * quantity)
            self.state["timer"] = time
            self.state["status"] = 1
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

    # ------------------------------------------------ MISC Intents

    @intent_file_handler("stop.intent")
    def handle_stop(self):
        """
        Handles utterances that request to stop the microwave midway.
        """
        self.log.info("In STOP handler")
        self.state["timer"] = 0
        self.state["status"] = 0
        self.log.info(self.state)

    @intent_file_handler("pause.intent")
    def handle_pause(self):
        """
        Handles requests to pause the ongoing activity (microwaving or countdown timer).
        Stores all the relevant state variable -- everything that is needed to resume the
        activity -- in the dict 'paused_state'.
        """

        self.log.info("In PAUSE handler")
        if self.state["status"] != 0:
            self.paused_state = self.state.copy()
            self.state["timer"] = 0
            self.state["status"] = 0
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
