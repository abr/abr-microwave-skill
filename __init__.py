from mycroft import MycroftSkill, intent_file_handler


class AbrMicrowave(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('microwave.abr.intent')
    def handle_microwave_abr(self, message):
        self.speak_dialog('microwave.abr')


def create_skill():
    return AbrMicrowave()

