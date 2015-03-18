#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
#===============================================================================
# FileName:     car.py
# Author:       noodleBin
# Version:      0.0.1
# Created:      2015-04-06
# Company:      CASCO
# LastChange:   create 2015-04-05
# History:     
#===============================================================================
#------------------------------------------------------------------------------ 

Created on 2014-11-10

@author: 61504

'''
from lxml import etree
from xmldeal import XMLDeal
class Car:
    # 路径信息
    # 一条线路由若干block组成的列表
    _blockList = []
    
    #所有地图Id列表
    _mapList = None
    
    #SSA列表
    _ssaList = []
    # 正负加速度（设定正负加速度相等）
    _accel_positive = None
    _accel_negative = None
    
    # 全程时间
    _running_time = None
    
    #当前运行模式
    _mode = None
    
    _sTimer = None
    
    #每站停车时间
    _stop_time = None
    # 最大限制速度
    _V_max = None
    
    # 车轮内外径
    _out_radio = None
    _in_radio = None
    
    # 周期为100ms
    _Timer = None
    # 小周期为2ms
    _smallTimer = None
    
    #列车行驶方向
    _direction = None
    
    #线路地图信息
    _block_map = None
    
    _cogSmallNumberList = None#当前周期之内齿数列表
    
    #临时存放的齿数的余数列表
    _cogRemain = None
    
    #临时存放齿数余数
    _sum = None
    
    #当前速度
    _currentV = None
    
    #保存当前速度
    _V = None
    
    #当前位移
    _currentSmallMileage = None
    
    #当前总位移
    _currentMileage = None
    
    #小车每个周期行驶的总共位移列表
    _mileList = None
    
    #行驶总共的位移和
    _AmountMile = None
    
    #匀加速和匀速行驶的位移
    _AccelAndConstantMile = None
    
    #当前加速标志位
    _AcelPostiveFlag = None
    
    #当前减速标志位
    _AcelNegativeFlag = None
    
    #匀速行驶时间
    _AccelAndconstantTime = None
    
    #到站停止标志
    _StopFlag = None
    
    #允许按钮停站标志
    _AllowStopFlag = None
    
    _allowstop = False
    
    _manualStop = False #手动停车
    
    _manualStart = False #手动开车
    
    _carStop = False
    
    _carBrack = False
    #匀速行驶时间
    _constantCycle = None
    
    #加速和匀速行驶Cycle
    _tempAccelConstantCycle = None
    
    #加速行驶时间
    _tempAccelCycle = None
    
    
    _IdAndSingular = None
    _IdAndLoopInfo = None
    _continuousSingular = None
    _continuousLoopInfo = None
    
    GradientButton = None
#     _IdAndSSA = None
    
    def __init__(self, name):
        mode,stop_time,cog_dir,accel,V_max,time,radio= XMLDeal.importSmartTramInfo( r'./scenario/smartTram_info.xml' )
        Car._mode = mode
        Car._stop_time = stop_time
        self.__cog = cog_dir
        self._accel_positive = accel[0]
        self._accel_negative = accel[1]
        self._V_max = V_max
    
        self._Timer = time[0]
        self._smallTimer = time[1]
        Car._sTimer = self._smallTimer
            
        self._out_radio = radio[0]
        self._in_radio = radio[1]
        
        self.lineList = {}
        self._block_map = {}
        self.__singular = {}
        
        self._IdAndSingular = {}
        self._IdAndLoopInfo = {}
        self._continuousSingular = {}
        self._continuousLoopInfo = {}
#         self._IdAndSSA = []
        
        self.__count = 0
        self._currentV = 0
        self._V = 0#当前速度
        self._currentSmallMileage = 0
        #当前总位移
        self._currentMileage = 0
        self._AcelPostiveFlag = True
        self._AcelNegativeFlag = False
        self._StopFlag = False
        Car._carStop = False
        self._AllowStopFlag = False
        self._AccelAndConstantMile = 0
        self._AccelAndconstantTime = 0
        self._constantCycle = 0
        self._tempAccelConstantCycle = 0#匀加速和匀速周期
        self._tempAccelCycle = 0#匀加速周期
        self._mileList = []
#         self._AmountMile = 0
        
        self.__i = 0
        self.__j = 0
        self.__frontGPS = []
        self.__lastSingularLength = 0
        self._cogSmallNumberList = []
        self._cogRemain = []
        self._sum = 0
#         print '------car initial complete------'
#         print mode,stop_time,cog_dir,accel,V_max,time,radio
        
    def deviceInit(self):
#         self.IterateBlockMap()
        self._block_map = self.IterateBlockMap()
#         print'-----------car init------'
#         print self._block_map
#         pass
    
    def reInit(self):
        mode,stop_time,cog_dir,accel,V_max,time,radio= XMLDeal.importSmartTramInfo( r'./scenario/smartTram_info.xml' )
        Car._mode = mode
        Car._stop_time = stop_time
        self.__cog = cog_dir
        self._accel_positive = accel[0]
        self._accel_negative = accel[1]
        self._V_max = V_max
    
        self._Timer = time[0]
        self._smallTimer = time[1]
        Car._sTimer = self._smallTimer
            
        self._out_radio = radio[0]
        self._in_radio = radio[1]
        self.lineList = {}
#         self._block_map = {}
        self.__singular = {}
        
        self._IdAndSingular = {}
        self._IdAndLoopInfo = {}
        self.__continuousSingular = {}
        self.__continuousLoopInfo = {}
        
        self.__count = 0
        self._currentV = 0
        self._V = 0#当前速度
        self._currentSmallMileage = 0
        #当前总位移
        self._currentMileage = 0
        self._AcelPostiveFlag = True
        self._AcelNegativeFlag = False
        self._StopFlag = False
        Car._carStop = False
        self._AllowStopFlag = False
        self._AccelAndConstantMile = 0
        self._AccelAndconstantTime = 0
        self._constantCycle = 0
        self._tempAccelConstantCycle = 0#匀加速和匀速周期
        self._tempAccelCycle = 0#匀加速周期
        self._mileList = []
        self._AmountMile = 0
        
        self.__i = 0
        self.__j = 0
        self.__frontGPS = []
        self.__lastSingularLength = 0
        self._cogSmallNumberList = []
        self._cogRemain = []
        self._sum = 0
        self._block_map = self.IterateBlockMap()
#         print'-----------car reinit block map------'
#         print self._block_map
#         print '------car ReInitial complete------'
        print mode,stop_time,cog_dir,accel,V_max,time,radio
    
    #清空每个周期行驶的总共位移列表
    def ReSetMileList(self):
        self._mileList = []
    
    #获取总共的行驶里程
    @staticmethod
    def getAmountMile():
        return Car._AmountMile
    
    def setAmountMile(self,_mile):
        Car._AmountMile = _mile
    #清空总共行驶里程
    def ReSetAmountMile(self):
        self._AmountMile = 0
    
    #获取当前速度
    def getCurrentV(self):
        return self._currentV
    
    #获取当前小周期内总共行驶位移
    def getCurrentSmallMileage(self):
        return self._currentSmallMileage
    
    def getCurrentMileage(self):
        return self._currentMileage
    
    def setCurrentMileage(self,_mileage):
        self._currentMileage = _mileage
        return self._currentMileage
    
    def getAllowStopFlag(self):
        return self._AllowStopFlag
    
    def setAllowStopFlag(self,_flag):
        self._AllowStopFlag = _flag
    
    def getAcelPositiveFlag(self):
        return self._AcelPostiveFlag
    
    def setAcelPositiveFlag(self,flag):
        self._AcelPostiveFlag = flag
        
    def getAcelNegativeFlag(self):
        return self._AcelNegativeFlag
    
    def setAcelNegativeFlag(self,flag):
        self._AcelNegativeFlag = flag    
    
    def getStopFlag(self):
        return self._StopFlag
    
    def setStopFlag(self,flag):
        self._StopFlag = flag
    
    def getDirection(self):
        return self._direction
    
    # 获取一个block
    def GetBlock(self, Id):
        return self._block_map[Id]
    
    def GetBlockAttr(self, Id, attr):
        return self._block_map[Id][attr]
    
    def GetBlockSubAttr(self, Id, attr1, attr2):
        return self._block_map[Id][attr1][attr2]
    
    def getBlockMap(self):
        return self._block_map
    def setBlockMap(self,_map):
        self._block_map = _map
    
    def getBlockList(self):
        return self._blockList
    
    def getBlockListItem(self, _id):
        return self._blockList[_id]
    
    def getSSAList(self):
        return self._ssaList
    
    def getSSAListItem(self,_id):
        return self._ssaList[_id]
    
    def getMapList(self):
        return self._mapList
    
    def getMapListItem(self,_id):
        return self._mapList[_id]
    
    def getSingular(self):
        return self.__singular
    
    def getSingularItem(self, _id):
        return self.__singular(_id)
    
    #获取刹车总位移
    def getBrackDisplacement(self,_v):
        _time = _v/self._accel_positive
        
        return 0.5*self._accel_positive*(_time**2)
    
    # 迭代遍历线路地图
    def IterateBlockMap(self):
#         _tree = etree.parse(r'C:\SGDCsvToXml_cha1_TRAM_ZC1_V1 - version.xml')
#         _tree = etree.parse(r'./Map/SGDCsvToXml_cha1_TRAM_ZC1_V1 - version.xml')
        _blockMap = {}
        _tree = etree.parse(r'./Map/SGDCsvToXml_cha1_TRAM_ZC1_V1_20141209.xml')
        rootNode = _tree.getroot()
        count = 0
        block = rootNode.getiterator("Block")
        for b in block:
            count += 1
            _blockMap[count] = self.iterate_node(b)
        return _blockMap

    # 迭代遍历线路地图的节点
    def iterate_node(self, node):
        tmp = {}  
        tmp['Next_block'] = []
        tmp['Closed_track_end'] = []
        tmp['Permanent_speed_restriction'] = []
        tmp['Service_stopping_area'] = []
        tmp['Points'] = []
        tmp['Crossing_area'] = []
        tmp['Signal'] = []
        tmp['Loop_info'] = []
        tmp['Singular'] = []
#         print "====================================="
        for sub2node in node.getchildren():
#             print "%s:%s" % (sub2node.tag, sub2node.text)
            
            if sub2node.tag == 'Next_block':
                _next = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
                    
                    _next.append(sub3node.text)
                tmp['Next_block'].append(_next)
            elif sub2node.tag == 'Closed_track_end':
                _Closed_track_end = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
                    _Closed_track_end.append(sub3node.text)
                tmp['Closed_track_end'].append(_Closed_track_end)
            elif sub2node.tag == 'Permanent_speed_restriction':
                _Permanent_speed_restriction = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
                    _Permanent_speed_restriction.append(sub3node.text)
                tmp['Permanent_speed_restriction'].append(_Permanent_speed_restriction)
            elif sub2node.tag == 'Service_stopping_area':
                _Service_stopping_area = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
                    _Service_stopping_area.append(sub3node.text)
                tmp['Service_stopping_area'].append(_Service_stopping_area)
            elif sub2node.tag == 'Points':
                _Points = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
                    _Points.append(sub3node.text)
                tmp['Points'].append(_Points)
            elif sub2node.tag == 'Crossing_area':
                _Crossing_area = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
                    _Crossing_area.append(sub3node.text)
                tmp['Crossing_area'].append(_Crossing_area)
            elif sub2node.tag == 'Signal':
                _Signal = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
                    _Signal.append(sub3node.text)
                tmp['Signal'].append(_Signal)
            elif sub2node.tag == 'Loop_info':
                _Loop_info = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
                    _Loop_info.append(sub3node.text)
                tmp['Loop_info'].append(_Loop_info)
            elif sub2node.tag == 'Singular':
                _Singular = []
                for sub3node in sub2node.getchildren():
#                     print "%s:%s" % (sub3node.tag, sub3node.text)
    #                 _Singular.append(sub3node.text)
                    if sub3node.tag == 'GPS_loc':
                        _GPS_loc = []
                        for sub4node in sub3node.getchildren():
#                             print "%s:%s" % (sub4node.tag, sub4node.text)
                            _GPS_loc.append(sub4node.text)
                        _Singular.append(_GPS_loc)
                    else:
                        _Singular.append(sub3node.text)   
                tmp['Singular'].append(_Singular)
            else:
                tmp[sub2node.tag] = sub2node.text
        return tmp

        # 获得加速时间
    def getAccelPositiveTime(self):
        return self._V_max / self._accel_positive
    
    #获取减速时间
    def getAccelNegativeTime(self):
        return -(self._V_max/self._accel_negative)
    
    # 获得加速行车里程
    def getTotalPositiveMileage(self):
        return 0.5 * self._V_max * self.getAccelPositiveTime()
    
    #获取减速行车里程
    def getTotalNegativeMileage(self):
        return 0.5*self._V_max*self.getAccelNegativeTime()
    
    # 获得全部行车里程
    def getTotalMileage(self):
        _total = 0
        for x in range(len(self._blockList)):
            _total = _total + float(self._block_map[self._blockList[x]]['Length'])
        return _total
    
    #===========================================================================
    # _cogSmallNumberList 复位
    #===========================================================================
    def reSetCogSmallNumberList(self):
        self._cogSmallNumberList = []
        pass
    
    def getCogListWhenStop(self):
        _temp = [0,0]
        self._cogSmallNumberList .append(_temp)
        return self._cogSmallNumberList
    
    #===========================================================================
    # 获取当前行驶总位移
    #===========================================================================
    def CalculateMileage(self,Mile):
        _tempM = 0
        if len(self._mileList) ==0:
            self._currentMileage = Mile
            pass
        else:
            for x in range(len(self._mileList)):
                _tempM = _tempM + self._mileList[x]
            self._currentMileage = _tempM + Mile
        return self._currentMileage
    
    #===========================================================================
    # 以当前速度减速到0行驶的总位移    这个位移可以用来判断车在距离站头多长位置需要停车的距离
    #===========================================================================
    def getDecelerationMiles(self,_currentV,_accel):
        _time = _currentV/_accel
        _mile = (0.5*_currentV**2)/_accel
        return _mile
    
    #===========================================================================
    # 添加是否点击Stop按钮标志位，如果按钮Stop停止则匀减速到速度为0
    # 匀加速时不能Stop
    # 匀减速时不能Stop
    #===========================================================================
    def StopRunningStatus(self,_smallCycleId,_SSALength,_stop):
        _smallTime = self._smallTimer * _smallCycleId# self._smallTimer = 0.02
        _smallCycleMileage = 0#当前周期之内的位移-->上一个周期和当前周期之间的位移
        _constantCycle = 0#匀加速和匀速行驶周期数
        
#         print '--------stop runing status----------',_SSALength
        if 0 <= self._currentV < self._V_max:#匀加速行驶过程
            if self.getAcelPositiveFlag() == True:
                self._currentV = self._accel_positive * _smallTime
                self._currentSmallMileage = 0.5*self._accel_positive*_smallTime**2
                _smallCycleMileage = 0.5*self._accel_positive*(_smallTime**2-((_smallTime-self._smallTimer))**2)
                self._constantCycle += 1
                self._V = self._currentV
                self.setAllowStopFlag(False)
                Car._allowstop = False
                Car._manualStart = False
                Car._manualStop = False
#                 self._AmountMile = self.CalculateMileage(self._currentSmallMileage)
                self.setAmountMile(self.CalculateMileage(self._currentSmallMileage))
#                 print '----1 currentV-------',self._currentV
#                 print '----1 amount mile-------',self.getAmountMile()
                #匀加速中没有收到停止指令，此时也需要判断加速是否到达终点站前面15米处，如果到达则需要减速了
                if 0 <= abs(_SSALength - 10 - self.getBrackDisplacement(self._currentV) -self.getAmountMile()) <= 1:
                    self._currentV = self._currentV - self._accel_positive * self._smallTimer
                    self._V = self._currentV #self._V--->V0
                    self.setAcelPositiveFlag(False)#开始减速
                    self.setAcelNegativeFlag(True)
                    self.setAllowStopFlag(False)
                    Car._allowstop = False
                    self._AccelAndconstantTime = _smallTime#匀加速和匀速行驶的时间
                    self._tempAccelConstantCycle =  self._constantCycle
#                     print '---------accel cycle slow down------',self._tempAccelConstantCycle
                    self._constantCycle = 0
#                 print '----_smallCycleMileage ------- ',_smallCycleMileage
            else:#匀减速行驶过程
#                 print '----------in to 2-------------'
                Car._allowstop = False
                Car._manualStart = False
                self._currentV = self._currentV - self._accel_positive * self._smallTimer
#                 print '----2 currentV-------',self._currentV
                _smallCycleMileage = 0.5*self._smallTimer*(2*self._currentV - self._accel_negative*self._smallTimer)
#                 print '-------------_smallCycleMileage ------------',_smallCycleMileage
                self._currentSmallMileage = self._AccelAndConstantMile + 0.5*(self._V + self._currentV)*(_smallTime - self._tempAccelConstantCycle*self._smallTimer)
#                 print '----2 _currentSmallMileage ------- ',self._currentSmallMileage
                self.setAmountMile(self.CalculateMileage(self._currentSmallMileage))
#                 print '----2 amount mile-------',self.getAmountMile()
                if  0<abs(self._currentV)<0.00001 or 0 <=abs(_SSALength -self.getAmountMile() - 10)<1:
#                 if 0<= abs(self._currentV) <= 0.000001:
                    self._mileList.append(self._currentSmallMileage)
#                     print '----currentV-------',self._currentV
#                     print '--------_SSALength--------',_SSALength
#                     print '---_currentSmallMileage---',self._currentSmallMileage
                    self.setStopFlag(True)
                    Car._carStop = True
                    print 'already set stop true'
#                     self.setCurrentMileage(self._currentSmallMileage)
                    
        elif self._currentV == self._V_max:#匀速行驶过程
            if _stop != True:
#             if Car._manualStop != True:
                _smallCycleMileage = self._smallTimer * self._V_max
                self._currentSmallMileage = 0.5*self._accel_positive*self.getAccelPositiveTime()**2 + self._V_max*(_smallTime-self.getAccelPositiveTime())
                self._AccelAndConstantMile = self._currentSmallMileage
#                 self._AmountMile = self.CalculateMileage(self._currentSmallMileage)
                self.setAmountMile(self.CalculateMileage(self._currentSmallMileage))
#                 print '----3 currentV-------',self._currentV
#                 print '----3 amount mile-------',self.getAmountMile()
#                 print '----3 _smallCycleMileage ------- ',self._currentSmallMileage
#                 print '---------ssa length-------------',_SSALength
                self._constantCycle += 1
                self.setAllowStopFlag(True)
                Car._allowstop = True
                Car._manualStop = False
                if 0 <= abs(_SSALength - 10 - self.getBrackDisplacement(self._currentV) - self.getAmountMile()) <= 1:
                    self._currentV = self._currentV - self._accel_positive * self._smallTimer
                    self._V = self._currentV #self._V--->V0
                    self.setAcelPositiveFlag(False)#开始减速
                    self.setAcelNegativeFlag(True)
                    self.setAllowStopFlag(False)
                    Car._allowstop = False
                    self._AccelAndconstantTime = _smallTime#匀加速和匀速行驶的时间
                    self._tempAccelConstantCycle =  self._constantCycle
#                     print '---------accel and constant cycle------',self._tempAccelConstantCycle
                    self._constantCycle = 0
            else:
                #需要紧急刹车了
#                 print '---------into emergency stop--------------'
                self._currentV = self._currentV - self._accel_positive * self._smallTimer
                self._V = self._currentV #self._V--->V0
                self.setAcelPositiveFlag(False)#开始减速
                self.setAcelNegativeFlag(True)
                self.setAllowStopFlag(False)
                self._AccelAndconstantTime = _smallTime#匀加速和匀速行驶的时间
                self._tempAccelConstantCycle =  self._constantCycle
#                 print '---------accel and constant cycle------',self._tempAccelConstantCycle
                self._constantCycle = 0
        self._cogSmallNumberList = self.getCogSmallNumberList(_smallCycleMileage)
        return self._cogSmallNumberList
    
    #===========================================================================
    # 根据当前小周期内行驶位移_smallCycleMileage 算出齿数（算法已优化）
    #===========================================================================
    def getCogSmallNumberList(self,_smallCycleMileage):
        _temp = [0,0]
        _cogSmallNumber = (_smallCycleMileage * self._in_radio)/(self._out_radio*self.__cog)
#         print'----------_cogSmallNumber----------',_cogSmallNumber
        _cogIntNumber = int(_cogSmallNumber)
#         print'----------_cogIntNumber------------',_cogIntNumber
        _cogRemainder = _cogSmallNumber - _cogIntNumber#齿数的小数点部分
#         print'----------_cogRemainder------------',_cogRemainder
        self._cogRemain.append(_cogRemainder)#添加到数据列表中
        for i in range(len(self._cogRemain)):
            self._sum = self._sum + self._cogRemain[i]#求和，判断是否到一个
#         print '---------------sum-----------------',self._sum
        if self._sum >= 1:
            _n = int(self._sum)
            _cogRemainder = self._sum - _n
            self._cogRemain = []
            self._cogRemain.append(_cogRemainder)
            _cogfinalNumber = _cogIntNumber + _n
        else:
            _cogfinalNumber = _cogIntNumber
            pass
        self._sum = 0
        _temp[0] = _cogfinalNumber
        _temp[1] = _cogfinalNumber
        self._cogSmallNumberList.append(_temp)
        return self._cogSmallNumberList

if __name__ == '__main__':
    car = Car('car')
    car.deviceInit()
#     car.reInit()
