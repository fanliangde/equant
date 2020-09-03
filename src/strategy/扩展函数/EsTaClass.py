#***********************************************************
#  Copyright © 2019 StarTech. All rights reserved
#  Author: Fanliangde
#  Description: 量化指标计算函数包
#  History:
#   1. Create Version1.0 on 2019/07/18
#   2.
#
#***********************************************************

import numpy as np
from EsSeries import NumericSeries
            

class UC_SAR(object):
    def __init__(self):
        self.Af       = NumericSeries()
        self.ParOpen  = NumericSeries()
        self.Position = NumericSeries()
        self.HHValue  = NumericSeries()
        self.LLValue  = NumericSeries()

    def U_SAR(self, High, Low, AfStep, AfLimit):
    
        oParClose    = 0
        oParOpen     = 0
        oPosition    = 0
        oTransition  = 0
                
        if len(High) == 1:
            self.Position[-1] = 1
            oTransition = 1
            self.Af[-1] = AfStep
            self.HHValue[-1] = High[-1]
            self.LLValue[-1] = Low[-1]
            oParClose = self.LLValue[-1]
            self.ParOpen[-1] = oParClose + self.Af[-1] * (self.HHValue[-1] - oParClose)

            if self.ParOpen[-1] > Low[-1]:
                self.ParOpen[-1] = Low[-1]
        else:
            oTransition = 0
            if High[-1] > self.HHValue[-2]:
                self.HHValue[-1] = High[-1]
            else:
                self.HHValue[-1] = self.HHValue[-2]

            if Low[-1] < self.LLValue[-2]:
                self.LLValue[-1] = Low[-1]
            else:
                self.LLValue[-1] = self.LLValue[-2]

            if self.Position[-2] == 1:
                if Low[-1] <= self.ParOpen[-2]:
                    self.Position[-1] = -1
                    oTransition = -1 
                    oParClose = self.HHValue[-1]
                    self.HHValue[-1] = High[-1]
                    self.LLValue[-1]  = Low[-1]

                    self.Af[-1] = AfStep
                    self.ParOpen[-1] = oParClose + self.Af[-1] * ( self.LLValue[-1] - oParClose )

                    if self.ParOpen[-1] < High[-1]:
                        self.ParOpen[-1] = High[-1]

                    if self.ParOpen[-1] < High[-2]:
                        self.ParOpen[-1] = High[-2]

                else:
                    self.Position[-1] = self.Position[-2]
                    oParClose = self.ParOpen[-2]

                    if self.HHValue[-1] > self.HHValue[-2] and self.Af[-2] < AfLimit:
                        if self.Af[-2] + AfStep > AfLimit:
                            self.Af[-1] = AfLimit
                        else:
                            self.Af[-1] = self.Af[-2]+AfStep
                    else:
                        self.Af[-1] = self.Af[-2]

                    self.ParOpen[-1] = oParClose + self.Af[-1] * ( self.HHValue[-1] - oParClose ) 

                    if self.ParOpen[-1] > Low[-1]:
                        self.ParOpen[-1] = Low[-1]

                    if self.ParOpen[-1] > Low[-2]:
                        self.ParOpen[-1] = Low[-2]
            else:
                if High[-1] >= self.ParOpen[-2]:
                    self.Position[-1] = 1 
                    oTransition = 1 

                    oParClose = self.LLValue[-1] 
                    self.HHValue[-1] = High[-1] 
                    self.LLValue[-1] = Low[-1]

                    self.Af[-1] = AfStep 
                    self.ParOpen[-1] = oParClose + self.Af[-1] * ( self.HHValue[-1] - oParClose) 

                    if self.ParOpen[-1] > Low[-1]:
                        self.ParOpen[-1] = Low[-1]

                    if self.ParOpen[-1] > Low[-2]:
                        self.ParOpen[-1] = Low[-2]
                else:
                    self.Position[-1] = self.Position[-2]
                    oParClose = self.ParOpen[-2]

                    if self.LLValue[-1] < self.LLValue[-2] and self.Af[-2] < AfLimit:
                        if self.Af[-2]+AfStep > AfLimit:
                            self.Af[-1] = AfLimit
                        else:
                            self.Af[-1] = self.Af[-2]+AfStep
                    else:
                        self.Af[-1] = self.Af[-2]

                    self.ParOpen[-1] = oParClose + self.Af[-1] * ( self.LLValue[-1] - oParClose ) 

                    if self.ParOpen[-1] < High[-1]:
                        self.ParOpen[-1] = High[-1]

                    if self.ParOpen[-1] < High[-2]:
                        self.ParOpen[-1] = High[-2]

        oParOpen = self.ParOpen[-1]
        oPosition = self.Position[-1]

        return oParClose, oParOpen, oPosition, oTransition
