import os
import twilio
from twilio.rest import Client

twilioAccSSID = 'ACf5da1645597d0798f4ff3be7c16dfeb4'
twilioAccTOKEN = '8109477889737ed2b1e4ffce1b807b62'

client = Client(twilioAccSSID,twilioAccTOKEN)

client.messages.create(
        body = "TEST SMS MESSAGE!!!",
        to = "+6588159408",
        from_ = "16314961976"
    )


