import sys
import os
import iothub_client
from iothub_client import (IoTHubClient, IoTHubClientError, IoTHubError,
                           IoTHubMessage, IoTHubMessageDispositionResult,
                           IoTHubTransportProvider)

# global counters
SEND_CALLBACKS = 0

# Callback received when the message that we're forwarding is processed.
def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    SEND_CALLBACKS += 1

class HubManager(object):

    def __init__(
            self,
            connectionString,
            messageTimeout,
            protocol,
            verbose):
        '''
        Communicate with the Edge Hub

        :param str connectionString: Edge Hub connection string
        :param int messageTimeout: the maximum time in milliseconds until a message times out. The timeout period starts at IoTHubClient.send_event_async. By default, messages do not expire.
        :param IoTHubTransportProvider protocol: Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
        '''
        self.connectionString = connectionString
        self.messageTimeout = messageTimeout
        self.protocol = protocol
        self.client_protocol = self.protocol
        self.client = IoTHubClient(self.connectionString, self.protocol)
        self.client.set_option("messageTimeout", self.messageTimeout)
        if verbose:
            self.client.set_option("logtrace", 1)#enables MQTT logging
        self.set_certificates()# some embedded platforms need certificate information

    def set_certificates(self):
        isWindows = sys.platform.lower() in ['windows', 'win32']
        if not isWindows:
            pass
            # CERT_FILE = os.environ['EdgeModuleCACertificateFile']        
            # print("Adding TrustedCerts from: {0}".format(CERT_FILE))          
            # # this brings in x509 privateKey and certificate
            # file = open(CERT_FILE)
            # try:
            #     self.client.set_option("TrustedCerts", file.read())
            #     print ( "set_option TrustedCerts successful" )
            # except IoTHubClientError as iothub_client_error:
            #     print ( "set_option TrustedCerts failed (%s)" % iothub_client_error )
            # file.close()

    def send_event_to_output(self, outputQueueName, event, send_context):
        self.client.send_event_async(outputQueueName, event, send_confirmation_callback, send_context)