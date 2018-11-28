import pandas as pd
import numpy as np
import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.player import Bot, Computer
from sc2.player import Human
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.data import Race, ActionResult, Attribute, race_worker, race_townhalls, race_gas
from sc2.game_info import GameInfo
from typing import List, Dict, Set, Tuple, Any, Optional, Union


class PrototypeAI(sc2.BotAI):
    def __init__(self):
        self.combinedActions = []
        self.building_map = np.zeros((1,1))  #initializes empty numpy array for caching with influence map & A* algo

        #dict = {key:value} {unit type: pre-req}
        #unit_id: unit tech requirement, current unit count, historic unit count, units in production
        self.unit_info = {
            COMMANDCENTER:[SCV, 0, 0, 0],
            SCV:[[COMMANDCENTER,ORBITALCOMMAND],0,0,0],
            SUPPLYDEPOT:[SCV,0,0,0],
            REFINERY:[SCV,0,0,0],
            BARRACKS:[SUPPLYDEPOT,0,0,0],
            BARRACKSTECHLAB:[BARRACKS,0,0,0],
            BARRACKSREACTOR:[BARRACKS,0,0,0],
            MARINE:[BARRACKS,0,0,0],
            REAPER:[BARRACKS,0,0,0],
            MARAUDER:[BARRACKSTECHLAB,0,0,0],
            GHOST:[BARRACKSTECHLAB,0,0,0],
            ORBITALCOMMAND:[BARRACKS,0,0,0],
            FACTORY:[BARRACKS,0,0,0],
            FACTORYTECHLAB:[FACTORY,0,0,0],
            FACTORYREACTOR:[FACTORY,0,0,0],
            HELLION:[FACTORY,0,0,0],
            HELLIONTANK:[FACTORY,0,0,0],
            WIDOWMINE:[FACTORY,0,0,0],
            THOR:[FACTORYTECHLAB,0,0,0],
            SIEGETANK:[FACTORYTECHLAB,0,0,0],
            STARPORT:[FACTORY,0,0,0],
            STARPORTTECHLAB:[STARPORT,0,0,0],
            STARPORTREACTOR:[STARPORT,0,0,0],
            MEDIVAC:[STARPORT,0,0,0],
            VIKINGFIGHTER:[STARPORT,0,0,0],
            RAVEN:[STARPORTTECHLAB,0,0,0],
            BANSHEE:[STARPORTTECHLAB,0,0,0],
            BATTLECRUISER:[STARPORTTECHLAB,0,0,0],
            ENGINEERINGBAY:[SUPPLYDEPOT,0,0,0],
            ARMORY:[FACTORY,0,0,0],
                    }
    
    async def on_step(self, iteration):
        self.playable_area = self.game_info.playable_area[2:4]   #tuple[2:4] to index the last two values (x,y) of the Rect object
        self.combinedActions = []
        await self.do_actions(self.combinedActions)
        await self.distribute_workers()
        await self.manage_supply(SUPPLYDEPOT)
        await self.train_unit(SCV)
        await self.construct(BARRACKS)
        await self.manage_gas(REFINERY)
    
 

    def return_building_queue(self, structure: UnitTypeId):
        """Checks if building queue is empty"""
        for building in self.units(structure):
            orders = building.orders
            if orders == []:
                self.unit_info[structure][2] = 0
                #print("building queue for ", structure, " = ", self.unit_info[structure][2])
            else:
                self.unit_info[structure][2] = len(self.units(structure).ready)
                #print("building queue for ", structure, " = ", self.unit_info[structure][2])


    def unit_counter(self, unit: UnitTypeId):
        """Takes length of current amount of units/structures in play and stores as a dictionary value."""
        if unit in self.unit_info.keys():
            #self.unit_info[unit] = len(self.units(unit))
            self.unit_info[unit][1] = self.units(unit).amount
            #print("# of ", unit, " = ", self.unit_info[unit]) #Debugging


    async def train_unit(self, unit: UnitTypeId): 
        """Trains unit from producer building after checking that producer exists and there are available resources."""
        if self.can_build(unit) is True:
            producer = self.check_req(unit)
            self.return_building_queue(producer)
            for building in self.units(producer).ready.noqueue:
                self.combinedActions.append(building.train(unit))
                self.unit_counter(unit)


    async def construct(self, structure: UnitTypeId):
        """Assigns a builder and arbitrary building location and then constructs building."""
        if self.can_build(structure) is True:
            builder = self.get_builder()
            loc = self.get_build_loc()
            self.combinedActions.append(builder.build(structure, loc))
            self.unit_counter(structure)
        
    def can_build(self, unit: UnitTypeId):
        """Check for resource requirement and that one unit isn't queued up already."""
        if self.can_afford(unit) and not self.already_pending(unit):
            return True
    
    def check_req(self, unit: UnitTypeId):
        """Check that unit pre-requisite building structure exists."""
        if isinstance(self.unit_info[unit], list):
            for x in self.unit_info[unit][0]:
                if self.units(x).exists:
                    req_unit = x
                    return req_unit
        elif isinstance(self.unit_info[unit], UnitTypeId):
            req_unit = self.unit_info[unit][0]
            return req_unit

    def get_build_loc(self):
        """Retrieves arbitrary buildling location for buildings."""
        #TODO 11/25/2018 - Specialized building location (gas, supply depot, structures, base design
        cc = self.townhalls.first
        rand = random.randint(0,19)
        loc = cc.position.towards(self.game_info.map_center, rand)
        return loc

    def get_builder(self):
        """Retrieves a builder from pool of active workers gathering minerals to construct a building."""
        #TODO 11/25/2018 - Optimize by utilizing idle workers and workers closest to building location.
        ws = self.workers.gathering
        if ws:
            w = ws.furthest_to(ws.center)
            return w

    async def manage_supply(self, supply_building: UnitTypeId):
        if self.supply_left < 3:
            await self.construct(supply_building)

    async def manage_gas(self, gas_structure: UnitTypeId):
        for cc in self.units(COMMANDCENTER):
            if self.already_pending(BARRACKS) and self.unit_stats[gas_structure] < 1:
                gas = self.state.vespene_geyser.closer_than(15.0, cc)
                for gas in gas:
                    if self.can_build(gas_structure):
                        builder = self.get_builder()
                        self.combinedActions.append(builder.build(gas_structure, gas))
                        self.unit_counter(gas_structure)

    def building_loc_setup(self, building_map) -> bool: 
        self.building_map = np.zeros(building_map)  #Move this to 'early game setup' function
        
        def in_pathing_grid(self, x, y):
            pos = (x,y)
            return self._game_info.placement_grid[pos] == 0

        for x in range(self.building_map.shape[0]):
            for y in range(self.building_map.shape[1]):
                if self.in_building_grid(x, y) == 0:
                    
                    self.building_map[x][y] = 1    #1 = buildable position

                    #Implement check to check around initial value point
        













    def set_early_game(self):
        terran_unit_list = ['scv']
        rax_units = ['marine', 'maurader', 'reaper']
        fac_units = ['hellion', 'hellbat', 'cyclone', 'tank', 'thor']
        starport_units = ['liberator', 'viking', 'banshee', 'raven', 'battlecruiser']
        terran_building_list = ['barracks', 'factory', 'starport', 'armory']

        def compile_list(name, *args):
            merged_list = []
            merged_list.extend(name)
            for arg in args:
                merged_list.extend(arg)
            return merged_list
        
        terran_list = compile_list(terran_unit_list, rax_units, fac_units, starport_units, terran_building_list)
        def build_dict(unit_list):
            blanks = []
            for n in range(len(unit_list)):
                blanks.append(0)
            unitdict = dict((zip(unit_list, blanks)))
            return unitdict
        terran_dict = build_dict(terran_list)

        def build_dataframe(dictval):
            df = pd.DataFrame()
            df['name'] = dictval.keys()
            df['current'] = dictval.values()
            df['killed'] = dictval.values()
            df['current_max'] = dictval.values()
            return df
        self.terran_dataframe = build_dataframe(terran_dict)

    async def distribute_workers(self, performanceHeavy=True, onlySaturateGas=False):
        # expansion_locations = self.expansion_locations
        # owned_expansions = self.owned_expansions
        if self.townhalls.exists:
            for w in self.workers.idle:
                th = self.townhalls.closest_to(w)
                mfs = self.state.mineral_field.closer_than(10, th)
                if mfs:
                    mf = mfs.closest_to(w)
                    self.combinedActions.append(w.gather(mf))

        mineralTags = [x.tag for x in self.state.units.mineral_field]
        # gasTags = [x.tag for x in self.state.units.vespene_geyser]
        geyserTags = [x.tag for x in self.geysers]

        workerPool = self.units & []
        workerPoolTags = set()

        # find all geysers that have surplus or deficit
        deficitGeysers = {}
        surplusGeysers = {}
        for g in self.geysers.filter(lambda x: x.vespene_contents > 0):
            # only loop over geysers that have still gas in them
            deficit = g.ideal_harvesters - g.assigned_harvesters
            if deficit > 0:
                deficitGeysers[g.tag] = {"unit": g, "deficit": deficit}
            elif deficit < 0:
                surplusWorkers = self.workers.closer_than(10, g).filter(
                    lambda w: w not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [
                        AbilityId.HARVEST_GATHER] and w.orders[0].target in geyserTags)
                # workerPool.extend(surplusWorkers)
                for i in range(-deficit):
                    if surplusWorkers.amount > 0:
                        w = surplusWorkers.pop()
                        workerPool.append(w)
                        workerPoolTags.add(w.tag)
                surplusGeysers[g.tag] = {"unit": g, "deficit": deficit}

        # find all townhalls that have surplus or deficit
        deficitTownhalls = {}
        surplusTownhalls = {}
        if not onlySaturateGas:
            for th in self.townhalls:
                deficit = th.ideal_harvesters - th.assigned_harvesters
                if deficit > 0:
                    deficitTownhalls[th.tag] = {"unit": th, "deficit": deficit}
                elif deficit < 0:
                    surplusWorkers = self.workers.closer_than(10, th).filter(
                        lambda w: w.tag not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [
                            AbilityId.HARVEST_GATHER] and w.orders[0].target in mineralTags)
                    # workerPool.extend(surplusWorkers)
                    for i in range(-deficit):
                        if surplusWorkers.amount > 0:
                            w = surplusWorkers.pop()
                            workerPool.append(w)
                            workerPoolTags.add(w.tag)
                    surplusTownhalls[th.tag] = {"unit": th, "deficit": deficit}

            if all([len(deficitGeysers) == 0, len(surplusGeysers) == 0,
                    len(surplusTownhalls) == 0 or deficitTownhalls == 0]):
                # cancel early if there is nothing to balance
                return

        # check if deficit in gas less or equal than what we have in surplus, else grab some more workers from surplus bases
        deficitGasCount = sum(
            gasInfo["deficit"] for gasTag, gasInfo in deficitGeysers.items() if gasInfo["deficit"] > 0)
        surplusCount = sum(-gasInfo["deficit"] for gasTag, gasInfo in surplusGeysers.items() if gasInfo["deficit"] < 0)
        surplusCount += sum(-thInfo["deficit"] for thTag, thInfo in surplusTownhalls.items() if thInfo["deficit"] < 0)

        if deficitGasCount - surplusCount > 0:
            # grab workers near the gas who are mining minerals
            for gTag, gInfo in deficitGeysers.items():
                if workerPool.amount >= deficitGasCount:
                    break
                workersNearGas = self.workers.closer_than(10, gInfo["unit"]).filter(
                    lambda w: w.tag not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [
                        AbilityId.HARVEST_GATHER] and w.orders[0].target in mineralTags)
                while workersNearGas.amount > 0 and workerPool.amount < deficitGasCount:
                    w = workersNearGas.pop()
                    workerPool.append(w)
                    workerPoolTags.add(w.tag)

        # now we should have enough workers in the pool to saturate all gases, and if there are workers left over, make them mine at townhalls that have mineral workers deficit
        for gTag, gInfo in deficitGeysers.items():
            if performanceHeavy:
                # sort furthest away to closest (as the pop() function will take the last element)
                workerPool.sort(key=lambda x: x.distance_to(gInfo["unit"]), reverse=True)
            for i in range(gInfo["deficit"]):
                if workerPool.amount > 0:
                    w = workerPool.pop()
                    if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                        self.combinedActions.append(w.gather(gInfo["unit"], queue=True))
                    else:
                        self.combinedActions.append(w.gather(gInfo["unit"]))

        if not onlySaturateGas:
            # if we now have left over workers, make them mine at bases with deficit in mineral workers
            for thTag, thInfo in deficitTownhalls.items():
                if performanceHeavy:
                    # sort furthest away to closest (as the pop() function will take the last element)
                    workerPool.sort(key=lambda x: x.distance_to(thInfo["unit"]), reverse=True)
                for i in range(thInfo["deficit"]):
                    if workerPool.amount > 0:
                        w = workerPool.pop()
                        mf = self.state.mineral_field.closer_than(10, thInfo["unit"]).closest_to(w)
                        if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                            self.combinedActions.append(w.gather(mf, queue=True))
                        else:
                            self.combinedActions.append(w.gather(mf))


def main():
    sc2.run_game(sc2.maps.get("FractureLE"), [
        Bot(Race.Terran, PrototypeAI()),
        Computer(Race.Protoss, Difficulty.VeryEasy)
    ], realtime=False)


if __name__ == '__main__':
    main()