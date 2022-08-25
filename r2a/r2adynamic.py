from ast import parse
from r2a.ir2a import IR2A
from statistics import mean
from player.parser import *
import time

class R2ADynamic(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.time_request = 0
        self.qi = []
        self.diffAverage = []
        self.segmentSize = []
        pass

    def handle_xml_request(self, msg):
        self.time_request = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):

        self.parsed_mpd = parse_mpd(msg.get_payload())

        #RTT - Round Trip Time
        time_response = time.perf_counter() - self.time_request
        self.qi = self.parsed_mpd.get_qi()

        # Throughput = bit length / time to execute (bits per second)
        self.throughput = msg.get_bit_length()/time_response
        self.throughputs.append(self.throughput)

        self.send_up(msg)
    
    def handle_segment_size_request(self, msg):

        # Calculates average throughput from RTT
        averageThroughput = mean(self.throughputs) / 2

        self.diffAverage.append(abs(self.throughput - averageThroughput))

        #Standard Deviation
        stdDev = mean(self.diffAverage)

        p = averageThroughput / (averageThroughput + stdDev)

        #tau = (1-p)*
        #omega = p*

        # if first loop, get lowest quality
        if len(self.throughputs) == 1:

            msg.add_quality_id(self.qi[0])

        else:

            # replace 19 by index of the quality to be selected 
            msg.add_quality_id(self.qi[19])

        self.send_down(msg)
    
    def handle_segment_size_response(self, msg):
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass