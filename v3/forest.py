# -*- coding: utf-8 -*-
"""

"""
import utiles,db,entity
from math import sqrt
from datetime import datetime,timedelta

class relevancy(object):
    def __init__(self,_minRel=0.6):
        self._minRel = _minRel
        data = db.select("select ah.airPressureAve,ah.airPressureMax,ah.airPressureMin,ah.temperatureAve,ah.temperatureMax,ah.temperatureMin,ah.waterPressureAve,ah.relativeHumidityAve,ah.relativeHumidityMin,ah.precipitation,ah.smallEvaporation,ah.largeEvaporation,ah.windVelocityAve,ah.windVelocityMax,ah.windVelocityDirection,ah.extremeWindVelocity,ah.extremeWindVelocityDir,ah.hoursOfSunshine,sh.daytype,sh.powerConsume from atmosphere_history ah INNER JOIN sw_history sh on ah.date = sh.date where sh.detailNum=96 ORDER BY ah.date") 
        powerConsumes = []
        atm = {}
            
        self._atmRel = {}

        for row in data:
            powerConsumes.append(float(row['powerConsume']))
            row.pop('powerConsume')

        for key in data[0].iterkeys():
            atm[key] = []
            self._atmRel[key] = 0
        for row in data:
            for key,val in row.iteritems():
                atm[key].append(int(val))
        for key in self._atmRel.iterkeys():
            self._atmRel[key] = utiles.sim_pearson(atm[key],powerConsumes)

        self._sevendayRel = {}
        # 计算前七天的相关度
        self._sevendayRel['oneday'] = utiles.sim_pearson(powerConsumes[1:],powerConsumes[0:len(powerConsumes)-1])
        self._sevendayRel['twoday'] = utiles.sim_pearson(powerConsumes[2:],powerConsumes[0:len(powerConsumes)-2])
        self._sevendayRel['threeday'] = utiles.sim_pearson(powerConsumes[3:],powerConsumes[0:len(powerConsumes)-3])
        self._sevendayRel['fourday'] = utiles.sim_pearson(powerConsumes[4:],powerConsumes[0:len(powerConsumes)-4])
        self._sevendayRel['fiveday'] = utiles.sim_pearson(powerConsumes[5:],powerConsumes[0:len(powerConsumes)-5])
        self._sevendayRel['sixday'] = utiles.sim_pearson(powerConsumes[6:],powerConsumes[0:len(powerConsumes)-6])
        self._sevendayRel['sevenday'] = utiles.sim_pearson(powerConsumes[7:],powerConsumes[0:len(powerConsumes)-7])

        self._rel = dict(self._sevendayRel,**self._atmRel)

        self._validAtmRel = {}
        for key,value in self._atmRel.iteritems():
            if abs(value) > self.minRel:
                self._validAtmRel[key] = value


        entity.AP.validAtmosphere = self.validAtmRel.keys()

    @property
    def minRel(self):
        return self._minRel
    @property
    def rel(self):
        return self._rel
    @property
    def atmRel(self):
        return self._atmRel
    @property
    def validAtmRel(self):
        return self._validAtmRel
    @property
    def sevendayRel(self):
        return self._sevendayRel
    
    
    def show(self):
        print '---------------minRel----------------'
        print self._minRel
        print '---------------validAtmRel----------------'
        print self.validAtmRel
        print '---------------atmRel----------------'
        print self._atmRel
        print '---------------sevendayRel----------------'
        print self._sevendayRel
        print '---------------validRel----------------'
        print self._validRel
        print '---------------rel----------------'
        print self._rel
    def normalizeRel(self,rel):
        sum = 0
        for value in rel.values():
            sum += value

        normalizedRel = {}
        for key,value in rel.iteritems():
            normalizedRel[key] = rel[key]/sum
        return normalizedRel

# a = relevancy()
# b = a.validRel
# print b
# print a.normalizeRel(b)
# print "-----------------------------"
# c = a.rel
# print c
# print a.normalizeRel(c)
# print "-----------------------------"
# print a.minRel

class normalization(object):
    def __init__(self):
        self._res = db.select("SELECT\
                        MAX(ah.airPressureMax) as airPressureMax,\
                        MIN(ah.airPressureMin) as airPressureMin,\
                        MAX(ah.temperatureMax) as temperatureMax,\
                        MIN(ah.temperatureMin) as temperatureMin,\
                        MAX(ah.waterPressureAve) as waterPressureMax,\
                        MIN(ah.waterPressureAve) as waterPressureMin,\
                        MAX(ah.relativeHumidityAve) as relativeHumidityMax,\
                        MIN(ah.relativeHumidityMin) as relativeHumidityMin,\
                        MAX(ah.precipitation) as precipitationMax,\
                        MIN(ah.precipitation) as precipitationMin,\
                        MAX(ah.smallEvaporation) as smallEvaporationMax,\
                        MIN(ah.smallEvaporation) as smallEvaporationMin,\
                        MAX(ah.largeEvaporation) as largeEvaporationMax,\
                        MIN(ah.largeEvaporation) as largeEvaporationMin,\
                        (CASE WHEN MAX(ah.windVelocityMax)>MAX(ah.extremeWindVelocity) THEN MAX(ah.windVelocityMax) ELSE MAX(ah.extremeWindVelocity) END) as windVelocityMax,\
                        (CASE WHEN MIN(ah.windVelocityAve)<MIN(ah.extremeWindVelocity) THEN MIN(ah.windVelocityAve) ELSE MIN(ah.extremeWindVelocity) END) as windVelocityMin,\
                        MAX(ah.hoursOfSunshine) as hoursOfSunshineMax,\
                        MIN(ah.hoursOfSunshine) as hoursOfSunshineMin\
                     FROM\
                        atmosphere_history ah\
                    where\
                        ah.cityName = 'shanwei';")
        self._res = self._res[0]

        pc = db.select("SELECT\
                        MAX(powerConsume) as powerConsumeMax,\
                        MIN(powerConsume) as powerConsumeMin\
                     FROM\
                        sw_history\
                    where\
                        cityName = 'shanwei';")
        self._res = dict(self._res,**pc[0])
        # self._res.extend(pc[0])
        for key in self._res.iterkeys():
            if key == 'powerConsumeMax' or key == 'powerConsumeMin':
                self._res[key] = float('%5.6f' % self._res[key])
            else:
                self._res[key] = int(self._res[key])

        self._normalize = {
            'airPressure':lambda airPressure : float((airPressure-self._res['airPressureMin']))/(self._res['airPressureMax']-self._res['airPressureMin']),
            'temperature':lambda temperature : float((temperature-self._res['temperatureMin']))/(self._res['temperatureMax']-self._res['temperatureMin']),
            'waterPressure':lambda waterPressure : float((waterPressure-self._res['waterPressureMin']))/(self._res['waterPressureMax']-self._res['waterPressureMin']),
            'relativeHumidity':lambda relativeHumidity : float((relativeHumidity-self._res['relativeHumidityMin']))/(self._res['relativeHumidityMax']-self._res['relativeHumidityMin']),
            'precipitation':lambda precipitation : float((precipitation-self._res['precipitationMin']))/(self._res['precipitationMax']-self._res['precipitationMin']),
            'smallEvaporation':lambda smallEvaporation : float((smallEvaporation-self._res['smallEvaporationMin']))/(self._res['smallEvaporationMax']-self._res['smallEvaporationMin']),
            'largeEvaporationMax':lambda largeEvaporationMax : float((largeEvaporationMax-self._res['largeEvaporationMin']))/(self._res['largeEvaporationMax']-self._res['largeEvaporationMin']),
            'windVelocity':lambda windVelocity : float((windVelocity-self._res['windVelocityMin']))/(self._res['windVelocityMax']-self._res['windVelocityMin']),
            'hoursOfSunshine':lambda hoursOfSunshine : float((hoursOfSunshine-self._res['hoursOfSunshineMin']))/(self._res['hoursOfSunshineMax']-self._res['hoursOfSunshineMin']),
            'windVelocityDir':lambda windVelocityDir : float((windVelocityDir-1))/(16-1),
            'powerConsume':lambda powerConsume : float((powerConsume-self._res['powerConsumeMin']))/(self._res['powerConsumeMax']-self._res['powerConsumeMin'])
        }

    @property
    def res(self):
        return self._res
    
    def normalize(self,name,value):
        return self._normalize[name](value)

# normalization = normalization()
# print normalization.res

class comparationEntity(object):
    __slots__ = ('_base','_similarityEntitys')
    def __init__(self,base,similarityEntitys):
        self._base = base
        self._similarityEntitys = similarityEntitys
    @property
    def base(self):
        return self._base
    @property
    def similarityEntitys(self):
        return self._similarityEntitys
    
class similarityEntity(object):
    __slots__ = ('_ap','_similarity')
    def __init__(self,ap,similarity):
        self._ap = ap
        self._similarity = similarity
    @property
    def ap(self):
        return self._ap

    @property
    def similarity(self):
        return self._similarity
    
    

class similarity(object):
    def __init__(self,_rel):
        self._rel = _rel

    def euclidean(self,early,predict):
        '''
        用于计算两个dict的相似度
        
        参数：
        early(dict)        :    历史日的气象数据
        predict(dict)      :    待预测日的气象数据
        _rel(dict)          :    相关度系数
        minRel(int)        :    最小相关系数
        '''
        sum = 0
        for key in self._rel.iterkeys():
            sum += abs(self._rel[key]) * (1-early[key]+predict[key])**2
        return sqrt(sum)


class forest(object):
    def __init__(self):

        self.setProcess()

        self._powerConsumes = []
        self._source = []
        self._forest = []
        self._forestSimilarity = []


        self._expect = []

    def setProcess(self):
        self.daytypeWeight = 0.6
        self.minRel = 0.6

        self._relevancy = relevancy(self.minRel)
        self._normalization = normalization()

        self._rel = self._relevancy.validAtmRel
        self._rel['Monday'] = self.daytypeWeight
        self._rel['Tuesday'] = self.daytypeWeight
        self._rel['Wednesday'] = self.daytypeWeight
        self._rel['Thursday'] = self.daytypeWeight
        self._rel['Friday'] = self.daytypeWeight
        self._rel['Saturday'] = self.daytypeWeight
        self._rel['Sunday'] = self.daytypeWeight

        self._similarity = similarity(self._rel)

    
    
    
    def setData(self,sourceNum,startDate,forestNum):
        '''
        参数：
        sourceNum(int)       :    历史日的天数
        startDate(str)       :    需要预测的日期（格式：'2007-4-5'）
        forestNum(str)       :    需要预测的天数，包含startDate向后数forestNum天
        '''
        
        d = datetime.strptime(startDate,"%Y-%m-%d")
        sevenday = (d-timedelta(sourceNum+7)).strftime("%Y-%m-%d")
        #计算历史日的第一天的日期
        preDate = (d-timedelta(sourceNum)).strftime("%Y-%m-%d")
        #计算待预测日的最后一天的日期
        endDate = (d+timedelta(forestNum-1)).strftime("%Y-%m-%d")
        #从数据库获取历史日 元数据 sourceDates(list(dict))
        sevenDates = db.select("select powerConsume from sw_history sh where date>=? and date<? and detailNum=96 ORDER BY date",sevenday,preDate)
        #从数据库获取历史日 元数据 sourceDates(list(dict))
        sourceDates = db.select("select ah.*,sh.daytype,sh.powerConsume from atmosphere_history ah INNER JOIN sw_history sh on ah.date = sh.date where ah.date>=? and ah.date<? and sh.detailNum=96 ORDER BY ah.date",preDate,startDate)
        #从数据库获取待预测日 元数据 forestDates(list(dict))        
        forestDates = db.select("select ah.*,sh.daytype,sh.powerConsume from atmosphere_history ah INNER JOIN sw_history sh on ah.date = sh.date where ah.date>=? and ah.date<=? and sh.detailNum=96 ORDER BY ah.date",startDate,endDate)

        utiles.clearList(self._powerConsumes)
        utiles.clearList(self._expect)
        utiles.clearList(self._expect)
        utiles.clearList(self._forest)

        sevenday_index = 0

        for row in sevenDates:
            self._powerConsumes.append(float('%5.6f'%row['powerConsume']))

        #1 将历史日元数据转化为 AP 对象
        #2 赋值到source
        for row in sourceDates:
            ap = entity.AP(**row)
            ap.sevendayPowerConsume = self._powerConsumes[sevenday_index:sevenday_index+7]
            sevenday_index += 1
            self._powerConsumes.append(ap.powerConsume['real'])
            self._expect.append(ap.powerConsume['real'])
            self._source.append(ap)
        
        #1 将待预测日元数据转化为 AP 对象
        #2 赋值到forest
        for row in forestDates:
            ap = entity.AP(**row)
            ap.sevendayPowerConsume = self._powerConsumes[sevenday_index:sevenday_index+7]
            sevenday_index += 1
            self._powerConsumes.append(ap.powerConsume['real'])
            self._expect.append(ap.powerConsume['real'])
            self._forest.append(ap)

    def normalize(self):
        for ap in self._source:
            ap.sevendayPowerConsumeN = {}
            for key,value in ap.sevendayPowerConsume.items():
                ap.sevendayPowerConsumeN[key] = self._normalization.normalize('powerConsume',value)

            ap.powerConsumeN = {}
            for key,value in ap.powerConsume.items():
                ap.powerConsumeN[key] = self._normalization.normalize('powerConsume',value)

            ap.atmosphereN = {}
            for key,value in ap.atmosphere.items():
                ap.atmosphereN[key] = self._normalization.normalize(entity.atmosphereType[key],value)

        for ap in self._forest:
            ap.sevendayPowerConsumeN = {}
            for key,value in ap.sevendayPowerConsume.items():
                ap.sevendayPowerConsumeN[key] = self._normalization.normalize('powerConsume',value)

            ap.powerConsumeN = {}
            for key,value in ap.powerConsume.items():
                ap.powerConsumeN[key] = self._normalization.normalize('powerConsume',value)

            ap.atmosphereN = {}
            for key,value in ap.atmosphere.items():
                ap.atmosphereN[key] = self._normalization.normalize(entity.atmosphereType[key],value)
            
    def countSimilarity(self):
        utiles.clearList(self.forestSimilarity)

        for forest in self._forest:
            comparationEntitys = []
            for source in self._source:
                similarity = self._similarity.euclidean(forest.getSimilarityCompareData(),source.getSimilarityCompareData())
                comparationEntitys.append(similarityEntity(source,similarity))

            self.forestSimilarity.append(comparationEntity(forest,comparationEntitys))

    


    @property
    def relevancy(self):
        return self._relevancy
    @property
    def normalization(self):
        return self._normalization
    @property
    def similarity(self):
        return self._similarity
    @property
    def powerConsumes(self):
        return self._powerConsumes
    @property
    def source(self):
        return self._source
    @property
    def forest(self):
        return self._forest
    @property
    def expect(self):
        return self._expect
    @property
    def forestSimilarity(self):
        return self._forestSimilarity

forest = forest()
# print entity.AP.validAtmosphere
# forest.relevancy.show()
forest.setData(40,'2007-4-4',7)
# one = forest.source[2]
# print one.cityName,one.date,one.atmosphere,one.powerConsume,one.daytype
forest.normalize()
# one = forest.source[0]
# print one.sevendayPowerConsumeN,one.powerConsumeN,one.atmosphereN

# print one.getSimilarityCompareData()
forest.countSimilarity()
one = forest.forestSimilarity[0]
two = one.similarityEntitys[0]
three = one.base
print three.date,"\n------------------\n",two.similarity,"\n------------------\n",two.ap.date
