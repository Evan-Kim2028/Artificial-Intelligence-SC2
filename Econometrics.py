from sc2.ids.unit_typeid import UnitTypeId

class WorkForce(object):
    def __init__(self):
        self.building_amount = {
        UnitTypeId.ARMORY: 0,
        UnitTypeId.BARRACKS: 0,
        UnitTypeId.BARRACKSREACTOR: 0,
        UnitTypeId.BARRACKSTECHLAB: 0,
        UnitTypeId.COMMANDCENTER: 0,       
        UnitTypeId.ENGINEERINGBAY:0,
        UnitTypeId.FACTORY: 0,
        UnitTypeId.FACTORYREACTOR: 0,
        UnitTypeId.FACTORYTECHLAB: 0,
        UnitTypeId.ORBITALCOMMAND: 0,
        UnitTypeId.PLANETARYFORTRESS: 0,
        UnitTypeId.REFINERY: 0,
        UnitTypeId.STARPORT: 0,
        UnitTypeId.STARPORTREACTOR: 0,
        UnitTypeId.STARPORTTECHLAB: 0,
        UnitTypeId.SUPPLYDEPOT: 0,
        }
        self.unit_amount = {
            UnitTypeId.BANSHEE: 0,
            UnitTypeId.BATTLECRUISER: 0,
            UnitTypeId.GHOST: 0,
            UnitTypeId.HELLION: 0,
            UnitTypeId.HELLIONTANK: 0,
            UnitTypeId.MARAUDER: 0,
            UnitTypeId.MARINE: 0,
            UnitTypeId.MEDIVAC: 0,
            UnitTypeId.RAVEN: 0,
            UnitTypeId.REAPER: 0,
            UnitTypeId.SCV: 0,
            UnitTypeId.SIEGETANK: 0,
            UnitTypeId.THOR: 0,
            UnitTypeId.VIKINGFIGHTER: 0,        
            UnitTypeId.WIDOWMINE: 0,
        }

    def unit_count(self, unit: UnitTypeId, amount: int):
        if isinstance(amount, int):
            self.unit_amount[unit] = amount
            print("WorkForce amount for", unit, " = " , self.unit_amount[unit])
        else:
            pass

class HistoricalData(object):
    def __init__(self):
        self.building_amount = {
        UnitTypeId.ARMORY: 0,
        UnitTypeId.BARRACKS: 0,
        UnitTypeId.BARRACKSREACTOR: 0,
        UnitTypeId.BARRACKSTECHLAB: 0,
        UnitTypeId.COMMANDCENTER: 1,       
        UnitTypeId.ENGINEERINGBAY:0,
        UnitTypeId.FACTORY: 0,
        UnitTypeId.FACTORYREACTOR: 0,
        UnitTypeId.FACTORYTECHLAB: 0,
        UnitTypeId.ORBITALCOMMAND: 0,
        UnitTypeId.PLANETARYFORTRESS: 0,
        UnitTypeId.REFINERY: 0,
        UnitTypeId.STARPORT: 0,
        UnitTypeId.STARPORTREACTOR: 0,
        UnitTypeId.STARPORTTECHLAB: 0,
        UnitTypeId.SUPPLYDEPOT: 0,
        }
        self.unit_amount = {
            UnitTypeId.BANSHEE: 0,
            UnitTypeId.BATTLECRUISER: 0,
            UnitTypeId.GHOST: 0,
            UnitTypeId.HELLION: 0,
            UnitTypeId.HELLIONTANK: 0,
            UnitTypeId.MARAUDER: 0,
            UnitTypeId.MARINE: 0,
            UnitTypeId.MEDIVAC: 0,
            UnitTypeId.RAVEN: 0,
            UnitTypeId.REAPER: 0,
            UnitTypeId.SCV: 12,
            UnitTypeId.SIEGETANK: 0,
            UnitTypeId.THOR: 0,
            UnitTypeId.VIKINGFIGHTER: 0,        
            UnitTypeId.WIDOWMINE: 0,
        }

    def unit_count(self, unit: UnitTypeId, amount: int):
        if isinstance(amount, int):
            self.unit_amount[unit] += 1
            print("Historical Data amount for", unit, " = " , self.unit_amount[unit])
        else:
            pass