from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

"""
Buildit checks unit tech requirements.
"""
class Buildit(object):
    def __init__(self):
        self.build_tree = {
        UnitTypeId.ARMORY: [UnitTypeId.FACTORY],
        UnitTypeId.BARRACKS: [UnitTypeId.SUPPLYDEPOT],
        UnitTypeId.BARRACKSREACTOR: [UnitTypeId.BARRACKS],
        UnitTypeId.BARRACKSTECHLAB: [UnitTypeId.BARRACKS],
        UnitTypeId.COMMANDCENTER: [UnitTypeId.SCV],       
        UnitTypeId.ENGINEERINGBAY:[UnitTypeId.SCV],
        UnitTypeId.FACTORY: [UnitTypeId.BARRACKS],
        UnitTypeId.FACTORYREACTOR: [UnitTypeId.FACTORY],
        UnitTypeId.FACTORYTECHLAB: [UnitTypeId.FACTORY],
        UnitTypeId.ORBITALCOMMAND: [UnitTypeId.COMMANDCENTER, 
                                    UnitTypeId.BARRACKS],
        UnitTypeId.PLANETARYFORTRESS: [UnitTypeId.COMMANDCENTER, 
                                        UnitTypeId.ENGINEERINGBAY],
        UnitTypeId.REFINERY: [UnitTypeId.SCV],
        UnitTypeId.STARPORT: [UnitTypeId.FACTORY],
        UnitTypeId.STARPORTREACTOR: [UnitTypeId.STARPORT],
        UnitTypeId.STARPORTTECHLAB: [UnitTypeId.STARPORT],
        UnitTypeId.SUPPLYDEPOT: [UnitTypeId.SCV],
        #TO-DO
        #Factory only needs 1 of the following - BARRACKS, BARRACKSTECHLAB, BARRACKSREACTOR
        #Ftarport only needs 1 of the following - FACTORY, FACTORYREACTOR, FACTORYTECHLAB        
        }           
        self.unit_tree = {
            UnitTypeId.BANSHEE: [UnitTypeId.STARPORTTECHLAB],
            UnitTypeId.BATTLECRUISER: [UnitTypeId.STARPORTTECHLAB],
            UnitTypeId.GHOST: [UnitTypeId.BARRACKSTECHLAB],
            UnitTypeId.HELLION: [UnitTypeId.FACTORY, 
                                UnitTypeId.FACTORYTECHLAB, 
                                UnitTypeId.FACTORYREACTOR],
            UnitTypeId.HELLIONTANK: [UnitTypeId.FACTORY, 
                                    UnitTypeId.FACTORYTECHLAB, 
                                    UnitTypeId.FACTORYREACTOR],
            UnitTypeId.MARAUDER: [UnitTypeId.BARRACKSTECHLAB],
            UnitTypeId.MARINE: [UnitTypeId.BARRACKS, 
                                UnitTypeId.BARRACKSTECHLAB, 
                                UnitTypeId.BARRACKSREACTOR],
            UnitTypeId.MEDIVAC: [UnitTypeId.STARPORT, 
                                UnitTypeId.STARPORTTECHLAB, 
                                UnitTypeId.STARPORTREACTOR],
            UnitTypeId.RAVEN: [UnitTypeId.STARPORTTECHLAB],
            UnitTypeId.REAPER: [UnitTypeId.BARRACKS, 
                                UnitTypeId.BARRACKSTECHLAB, 
                                UnitTypeId.BARRACKSREACTOR],
            UnitTypeId.SCV: [UnitTypeId.COMMANDCENTER, 
                            UnitTypeId.ORBITALCOMMAND],
            UnitTypeId.SIEGETANK: [UnitTypeId.FACTORYTECHLAB],
            UnitTypeId.THOR: [UnitTypeId.FACTORYTECHLAB],
            UnitTypeId.VIKINGFIGHTER: [UnitTypeId.STARPORT, 
                                        UnitTypeId.STARPORTTECHLAB, 
                                        UnitTypeId.STARPORTREACTOR],        
            UnitTypeId.WIDOWMINE: [UnitTypeId.FACTORY, 
                                    UnitTypeId.FACTORYTECHLAB, 
                                    UnitTypeId.FACTORYREACTOR],       
            #Units only need one requirement from value list.
        }
        #self.get_producers(unit)

    def get_producers(self, unit: UnitTypeId):           
        producer_list = self.unit_tree[unit]
        return producer_list





    #NEEDS TO BE REFACTORED 12/8/2018
    #def construct(self, structure: UnitTypeId):
    #"""Assigns a builder and arbitrary building location and then constructs building."""
    #if self.can_build(structure) is True:
        #builder = self.get_builder()
        #self.building_loc_setup()
        #print("construction starting")
        #depot_size = (2,2)
        #self.Micro.rolling_window(self.building_map, depot_size)
        #print("self.Micro.rolling_window", self.Micro.rolling_window(self.building_map, depot_size))
        #if self.Micro.rolling_window(self.building_map, depot_size).all() == 0:

            #loc = self.building_map[x][y]
            #print("getting building loc", loc)
            #self.combinedActions.append(builder.build(structure, loc))
            #self.unit_counter(structure)
        
    
    #IS THIS FUNCTION NEEDED?
    #def check_req(self, unit: UnitTypeId):
        #"""Check that unit pre-requisite building structure exists."""
        #if isinstance(self.unit_info[unit][0], list):
            #for x in self.unit_info[unit][0]:
                #if self.units(x).exists:
                    #req_unit = x
                    #return req_unit
        #elif isinstance(self.unit_info[unit][0], UnitTypeId):
            #req_unit = self.unit_info[unit][0]
            #return req_unit