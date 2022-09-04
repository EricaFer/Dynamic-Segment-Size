"""
@author: Erica Fernandes ( https://github.com/EricaFer )

@description: Dynamic Segment-Size Implementation on pyDash

Here lies the implementation of "Dynamic Segment Size Selection in HTTP Based Adaptative Video Streaming",
paper written by Luca Bedogni, Marco Di Felice and Luciano Bononi, about a new selection of segment sizes in a video streaming method.
The project consists on analysing the bandwidth oscilations, as well as the previous selections made in the segment size of the video, and then, use
estimations to calculate what is the best next segment to choose, based on the network average capacity.

This work was mostly done by Erica Fernandes, but the other group members put effort on writing the report of the implemetation, as well as showing the comparisons
with other approaches.

September, 2022
"""

from ast import parse
from math import factorial
from r2a.ir2a import IR2A
from statistics import mean
from player.parser import *
import time
import numpy as np
import matplotlib.pyplot as plt

class R2ADynamic(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.time_request = 0
        self.qi = []
        self.diffAverage = []
        self.segmentSize = []
        self.last_qis = []
        self.stdlist = []
        self.plist = []
        self.M = 10

        pass

    def handle_xml_request(self, msg):
        self.time_request = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):

        self.parsed_mpd = parse_mpd(msg.get_payload())

        #RTT - Round Trip Time
        time_response = time.perf_counter() - self.time_request

        # Throughput = bit length / time to execute (bits per second)
        self.throughput = msg.get_bit_length()/time_response
        self.throughputs.append(self.throughput)

        self.qi = self.parsed_mpd.get_qi()

        self.throughputs = [self.qi[0]] * self.M
        self.last_qis = [self.qi[0]]

        self.send_up(msg)
    
    def handle_segment_size_request(self, msg):

        self.time_request = time.perf_counter()

        # Calculates average throughput from RTT
        # analogous to μ in the article 
        averageThroughput = mean(self.throughputs[-self.M:])

        # Calculating Standard Deviation - stdDev
        stdDev = 0

        for i in range(1,self.M+1):
            stdDev += (abs(self.throughputs[-i] - averageThroughput))*(i/self.M)

        self.stdlist.append(stdDev)

        # Probability - willingness of changing video quality
        p = averageThroughput / (averageThroughput + stdDev)

        self.plist.append(p)

        # index of the last quality used in the ordered list
        indexQi = self.qi.index(self.last_qis[-1])

        # Probability of decreasing to the previous lower quality
        tau = (1-p)*self.qi[max(0,indexQi-1)]

        # Probability of increasing to the next higher quality
        teta = p*self.qi[min(len(self.qi)-1,indexQi+1)]

        # Target quality - the one I want,
        #  but still have to check the closest that exists 
        target = self.last_qis[-1] - tau + teta

        # Calculating the difference for every quality that exists and 
        # the target
        self.qiDiff = [abs(x - target) for x in self.qi]

        print(f'Last Qualities = {self.last_qis}',end="\n")

        # if first loop, get lowest quality
        if len(self.throughputs) == self.M:

            newQiIndex = 0
            # does not append to last_qis because
            # list is already initialized with the first value

        else:

            # argmin gets the index of the quality with the smallest
            # difference to the target quality
            newQiIndex = np.argmin(self.qiDiff)

            self.last_qis.append(self.qi[newQiIndex])

        msg.add_quality_id(self.qi[newQiIndex])

        plt.plot([i for i in range(0,len(self.last_qis))],self.stdlist)
        plt.savefig('std.png')

        self.send_down(msg)
    
    def handle_segment_size_response(self, msg):
        #RTT - Round Trip Time
        time_response = time.perf_counter() - self.time_request

        # Throughput = bit length / time to execute (bits per second)
        self.throughput = msg.get_bit_length()/time_response
        self.throughputs.append(self.throughput)

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass