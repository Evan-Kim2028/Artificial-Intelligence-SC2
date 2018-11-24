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
        #dict = {key:value} {unit type: pre-req}
        self.techtree = {
            SCV:[COMMANDCENTER,ORBITALCOMMAND],
            SUPPLYDEPOT:SCV,
            REFINERY:SCV,
            BARRACKS:SUPPLYDEPOT,
            BARRACKSTECHLAB:BARRACKS,
            BARRACKSREACTOR:BARRACKS,
            MARINE:BARRACKS,
            REAPER:BARRACKS,
            MARAUDER:BARRACKSTECHLAB,
            GHOST:BARRACKSTECHLAB,
            ORBITALCOMMAND:[COMMANDCENTER,BARRACKS],
            FACTORY:BARRACKS,
            FACTORYTECHLAB:FACTORY,
            FACTORYREACTOR:FACTORY,
            HELLION:FACTORY,
            HELLIONTANK:FACTORY,
            WIDOWMINE:FACTORY,
            THOR:FACTORYTECHLAB,
            SIEGETANK:FACTORYTECHLAB,
            STARPORT:FACTORY,
            STARPORTTECHLAB:STARPORT,
            STARPORTREACTOR:STARPORT,
            MEDIVAC:STARPORT,
            VIKINGFIGHTER:STARPORT,
            RAVEN:STARPORTTECHLAB,
            BANSHEE:STARPORTTECHLAB,
            BATTLECRUISER:STARPORTTECHLAB,
            ENGINEERINGBAY:SUPPLYDEPOT,
            ARMORY:FACTORY,
                        }
        self.unit_stats = {
            SCV:0,
            SUPPLYDEPOT:0,
            REFINERY:0,
            BARRACKS:0,
            BARRACKSTECHLAB:0,
            BARRACKSREACTOR:0,
            MARINE:0,
            REAPER:0,
            MARAUDER:0,
            GHOST:0,
            ORBITALCOMMAND:0,
            FACTORY:0,
            FACTORYTECHLAB:0,
            FACTORYREACTOR:0,
            HELLION:0,
            HELLIONTANK:0,
            WIDOWMINE:0,
            THOR:0,
            SIEGETANK:0,
            STARPORT:0,
            STARPORTTECHLAB:0,
            STARPORTREACTOR:0,
            MEDIVAC:0,
            VIKINGFIGHTER:0,
            RAVEN:0,
            BANSHEE:0,
            BATTLECRUISER:0,
            ENGINEERINGBAY:0,
            ARMORY:0,
                        }

    async def on_step(self, iteration):
        await self.do_actions(self.combinedActions)
        self.combinedActions = []
        await self.distribute_workers()
        await self.manage_supply(SUPPLYDEPOT)   #supply depot builds
        await self.train_unit(SCV)
        await self.construct(BARRACKS)
    

    def unit_counter(self, unit):
        if unit in self.unit_stats.keys():
            self.unit_stats[unit] = len(self.units(unit))
            print("# of ", unit, " = ", self.unit_stats[unit])

    async def train_unit(self, unit): 
        if unit in self.techtree.keys():
            if self.can_build(unit) is True:
                producer = self.check_req(unit)#HERE
                for producer in self.units(producer).ready.noqueue:
                    self.combinedActions.append(producer.train(unit))
                    self.unit_counter(unit)

    async def construct(self, structure):
        if self.can_build(structure) is True:
            builder = self.get_builder()
            loc = self.get_build_loc()
            self.combinedActions.append(builder.build(structure, loc))
            self.unit_counter(structure)
        
    def can_build(self, unit):
        if self.can_afford(unit) and not self.already_pending(unit):
            return True
    
    def check_req(self, unit):
        if isinstance(self.techtree[unit], list):
            for x in self.techtree[unit]:
                if self.units(x).exists:
                    req_unit = x
                    return req_unit
        elif isinstance(self.techtree[unit], UnitTypeId):
            req_unit = self.techtree[unit]
            return req_unit

    def get_build_loc(self):
        cc = self.townhalls.first
        rand = random.randint(0,19)
        loc = cc.position.towards(self.game_info.map_center, rand)
        return loc

    def get_builder(self):
        ws = self.workers.gathering
        if ws:
            w = ws.furthest_to(ws.center)
            return w

    async def manage_supply(self, supply_building):
        if self.supply_left < 3:
            await self.construct(supply_building)



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