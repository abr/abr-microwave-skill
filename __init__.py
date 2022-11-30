import datetime
import time

from mycroft import MycroftSkill, intent_file_handler


class AbrMicrowave(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

        # Current status of the microwave
        self.state = {
            "state": 0,  #  microwave on/off
            "heat_mode": "medium",  # Literal["low", "medium", "high"], current heat mode
            "timer": 0.0,  # int, keeps track of the cooking time in seconds
            "light": 0,  # microwave light on/off
        }
        # Avaialble heat/power modes
        self.heat_modes = ("low", "medium", "high")

    def _extract_and_set_time(self, time_entity):
        time = "".join([x for x in time_entity if x.isnumeric()])
        time = int(time)
        if "second" in time_entity:
            self.state["timer"] = time
        elif "minute" in time_entity:
            self.state["timer"] = int(time * 60)
        elif "hour" in time_entity:
            self.state["timer"] = int(time * 3600)

    def _time_display_and_track(self):
        for i in range(self.state["timer"], -1, -1):
            print(f"{datetime.timedelta(seconds=i)}", end="\r", flush=True)
            time.sleep(1)
            self.state["timer"] -= 1
        self.acknowledge()

    def initialize(self):
        self.register_entity_file("time.entity")

    @intent_file_handler("reheat.basic.intent")
    def handle_reheat_basic(self, message):
        self.log.info("In REHEAT BASIC handler")
        self._extract_and_set_time(message.data["time"])
        self._time_display_and_track()


def create_skill():
    return AbrMicrowave()
