class GALC_Application extends App.Application
    _client_type: App.ContinuousClient

    gold_objects_validation_message: "Only 3 words per line allowed."

    gold_objects_validator: (line) ->
        line.length != 3

a = new GALC_Application()
