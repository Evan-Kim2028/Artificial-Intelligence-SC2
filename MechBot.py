import random
import datetime
import numpy as np

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
from MicroController import Micro

class MechBot(sc2.BotAI):
    def __init__(self):
        super().__init__()
        self.combinedActions = []
        self.map = np.zeros((1,1))  #initializes empty numpy array for caching with influence map & A* algo
        self.passable_tile_map = np.zeros((1,1))
        #10/22/2018 - Need to wire influence map and pathable tile check to self.map and add A* algo as well.
       # Part of bansheebuild
        self.passable_tile_check = True
        self.lift_flag = True
        self.flag_fac_land = True
        self.scv_count = 0
        self.supply_depot_count = 0
        self.reaper_count = 0
        self.banshee_count = 0
        self.Micro = Micro

    async def on_step(self, iteration):
        await self.do_actions(self.combinedActions)
        self.combinedActions = []
        self.playable_area = self.game_info.playable_area[2:4]   #tuple[2:4] to index the last two values (x,y) of the Rect object
        self.initialize_passable_tiles(self.playable_area)
        # Buildings
        await self.build_barracks()
        await self.build_factory()
        await self.build_refinery()
        await self.build_starport()
        await self.build_supply_depots()
        await self.distribute_workers()
        await self.lift_buildings()
        await self.land_buildings()
        await self.research_cloak()
        await self.train_scv()
        await self.upgrade_to_oc()
        # Units
        await self.build_banshee()
        await self.build_scouting_reaper()
        #Control Units
        await self.control_scouting_reaper()



# Bulk of the banshee build is below
    async def train_scv(self):
        '''Builds SCV's until first expansion is saturated.'''
        for cc in self.units(COMMANDCENTER).ready.noqueue:
            if self.units(SCV).amount < 17:
                if self.can_afford(SCV) and not self.already_pending(SCV):
                    self.combinedActions.append(cc.train(SCV))
                    self.scv_count += 1
                    #print("Current Game Time", str(datetime.timedelta(seconds=round(self.time))))
                    #print("Total SCVs built:    " + str(self.scv_count))

        if self.units(ORBITALCOMMAND).exists:
            for oc in self.units(ORBITALCOMMAND).ready.noqueue:
                if self.units(SCV).amount < 50:
                    if self.can_afford(SCV) and not self.already_pending(SCV):
                        self.combinedActions.append(oc.train(SCV))
                        self.scv_count += 1
                        #print("Total SCVs built:    " + str(self.scv_count))
                        #print("Current Game Time", str(datetime.timedelta(seconds=round(self.time))))

    async def build_supply_depots(self):
        '''Builds supply depots to ensure adequate supply_left.'''
        cc = self.townhalls.first
        ws = self.workers.gathering
        if ws:
            w = ws.furthest_to(ws.center)
        if self.supply_left <= 4 and self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT):
            if self.units(SUPPLYDEPOT).amount < 1:
                first_loc = cc.position.towards(self.game_info.map_center, 6)
                self.combinedActions.append(w.build(SUPPLYDEPOT, first_loc))
                self.supply_depot_count += 1
                #print("Current Game Time", str(datetime.timedelta(seconds=round(self.time))))
                #print("Total depots built:    "+ (str(self.supply_depot_count)))
            else:
                last_depot_loc = self.units(SUPPLYDEPOT)[-1].position
                next_loc = await self.find_placement(SUPPLYDEPOT, last_depot_loc, placement_step=1)
                #next_loc = self.units(SUPPLYDEPOT[-1].random.position, placement_step=4)
                self.combinedActions.append(w.build(SUPPLYDEPOT, next_loc))
                self.supply_depot_count += 1
                #print("Current Game Time", str(datetime.timedelta(seconds=round(self.time))))
                #print("Total depots built:    "+ (str(self.supply_depot_count)))

    async def build_barracks(self):
        '''Builds 1st barracks, the pre-requisite tech for a factory.'''
        if self.can_afford(BARRACKS) and self.units(SUPPLYDEPOT).exists:
            if not self.already_pending(BARRACKS) and self.units(BARRACKS).amount < 1:
                cc = self.townhalls.first
                ws = self.workers.gathering
                if ws:
                    w = ws.furthest_to(ws.center)
                    start = self.game_info.player_start_location
                    #rax_loc = self.units(SUPPLYDEPOT)[-1].position.towards(start, 3)
                    rax_loc = cc.position.towards(
                        self.game_info.map_center, 10)
                    self.combinedActions.append(w.build(BARRACKS, rax_loc))

    async def build_refinery(self):
        '''Builds initial refineries in main base to reach 100% gas production on 1 base.'''
        for cc in self.units(COMMANDCENTER):
            if self.already_pending(BARRACKS):
                gas = self.state.vespene_geyser.closer_than(15.0, cc)
                for gas in gas:
                    if self.can_afford(REFINERY) and not self.already_pending(REFINERY) and self.units(REFINERY).amount < 2:
                        ws = self.workers.gathering
                        if ws:
                            w = ws.furthest_to(ws.center)
                            #worker = self.select_build_worker(gas.position)
                            self.combinedActions.append(w.build(REFINERY, gas))

    async def upgrade_to_oc(self):
        """Controls upgrade to OC, mule deployment, and scan usage."""
        if self.units(BARRACKS).exists and self.units(COMMANDCENTER).ready.exists:
            if not self.already_pending(ORBITALCOMMAND) and self.units(SCV).amount >= 17:
                if self.can_afford(ORBITALCOMMAND) and not self.already_pending(ORBITALCOMMAND):
                    self.combinedActions.append(self.units(COMMANDCENTER)[
                                               0](UPGRADETOORBITAL_ORBITALCOMMAND))
                    pass
                # Mule drop
        for oc in self.units(ORBITALCOMMAND).ready:
            abilities = await self.get_available_abilities(oc)
            if CALLDOWNMULE_CALLDOWNMULE in abilities:
                mf = self.state.mineral_field.closest_to(oc)
                self.combinedActions.append(oc(CALLDOWNMULE_CALLDOWNMULE, mf))

    async def build_scouting_reaper(self):
        '''Builds reaper to scout enemy base location/buildings.'''
        for rax in self.units(BARRACKS).ready.noqueue:
            if self.can_afford(REAPER) and not self.already_pending(REAPER) and self.reaper_count < 1:
                self.combinedActions.append(rax.train(REAPER))
                self.reaper_count += 1
                print("Current Game Time", str(
                    datetime.timedelta(seconds=round(self.time))))
                print("Total Reapers made:    " + str(self.reaper_count))

#Working on this function 9/17/2018
    async def control_scouting_reaper(self):
        '''Reaper moves to enemy location at the beginning of the game.'''
        for r in self.units(REAPER):
            if r:
                enemy_start_loc = self.enemy_start_locations[0]
                self.combinedActions.append(r.move(enemy_start_loc))
                print(self.find_friendly_unit_pos(r), 'r unit pos')
                print(self.find_closest_enemy_threat(r), 'enemy threat pos')
            enemy = self.known_enemy_units.exists
            if enemy:
                enemy_threat = self.find_closest_enemy_threat(r)
                unit_power = (r.health + r.shield)/r.ground_dps
                enemy_unit_power = (enemy_threat.health + enemy_threat.shield)/enemy_threat.ground_dps
                #Update values through self.map (array)
                new_harass_position = self.Micro.influence_map(self.map, enemy_threat.ground_range, enemy_unit_power, enemy_threat)

                ## new_harass_position = self.Micro.harass_micro_avg(self, self.find_friendly_unit_pos(r), self.find_closest_enemy_workers(r), self.find_closest_enemy_threat(r))
                #convert new_harass_position to Point2 position tuple.
                new_harass_position_point2 = Point2(tuple(new_harass_position))
                #move_closer_to_probes = working on function atm
                if r.weapon_cooldown != 0:
                    self.combinedActions.append(r.move(new_harass_position_point2))
                    self.Micro.influence_map(self.map, enemy_threat.ground_range,
                                                             enemy_unit_power, enemy_threat)
                else:
                    self.combinedActions.append(r.attack(self.find_closest_enemy_worker(r)))
                    self.Micro.influence_map(self.map, enemy_threat.ground_range,
                                                             enemy_unit_power, enemy_threat)
                if r.health_percentage < 45/60:
                    self.combinedActions.append(r.move(self.game_info.map_center))

    async def build_factory(self):
        '''Builds a factory, the pre-requisite tech for a starport.'''
        if not self.units(FACTORYFLYING):
            ws = self.workers.gathering
            if ws:
                w = ws.furthest_to(ws.center)
            if self.units(BARRACKS).exists and self.can_afford(FACTORY) and not self.already_pending(FACTORY):
                if self.units(FACTORY).amount < 1:
                    for rax in self.units(BARRACKS):
                        rax_loc = rax.position
                        building_loc = await self.find_placement(FACTORY, rax_loc, placement_step=6)
                        self.combinedActions.append(
                            w.build(FACTORY, building_loc))

    async def build_starport(self):
        '''Builds a starport. This production building is required to build a banshee and research cloak.'''
        '''Tech lab for starport is built on factory after starport starts building.'''
        if not self.units(STARPORTFLYING):
            ws = self.workers.gathering
            if ws:
                w = ws.furthest_to(ws.center)
            if self.units(FACTORY).exists and self.can_afford(STARPORT) and not self.already_pending(STARPORT):
                if self.units(STARPORT).amount < 1:
                    fac_loc = self.units(FACTORY)[0].position
                    building_loc = await self.find_placement(STARPORT, fac_loc, placement_step=2)
                    fac = self.units(FACTORY)[0]
                    self.combinedActions.append(fac.build(FACTORYTECHLAB))
                    self.combinedActions.append(w.build(STARPORT, building_loc))

    async def lift_buildings(self):
        '''Lifts starport and factory up.'''
        # Lift factory and starport and swap with each other.
        if self.lift_flag:
            if self.units(STARPORT).ready:
                # added iff statement
                if self.units(FACTORY).exists:
                    fac = self.units(FACTORY)[0]
                    if fac:
                        abilities = await self.get_available_abilities(fac)
                        if LIFT_FACTORY in abilities:
                            self.combinedActions.append(fac(LIFT_FACTORY))
                starport = self.units(STARPORT)[0]
                if starport:
                    abilities = await self.get_available_abilities(starport)
                    if LIFT_STARPORT in abilities:
                        self.combinedActions.append(starport(LIFT_STARPORT))
                self.lift_flag = False

    async def land_buildings(self):
        '''Lands starport and factory where the tech lab is now on the starport.'''
        fac = self.units(FACTORYFLYING)
        starport = self.units(STARPORTFLYING)
        if fac:
            abilities = await self.get_available_abilities(fac[0])
            if LAND_FACTORY in abilities:
                if self.flag_fac_land:
                    rax_loc = self.units(BARRACKS).first.position
                    building_loc = await self.find_placement(FACTORY, rax_loc, placement_step=6)
                    self.combinedActions.append(fac[0](LAND_FACTORY, building_loc))
                    self.flag_fac_land = False
        if self.units(TECHLAB).exists:
            addon_loc = self.units(TECHLAB).first.add_on_land_position
            if starport:
                abilities = await self.get_available_abilities(starport[0])
                if LAND_STARPORT in abilities:
                    self.combinedActions.append(
                        starport[0](LAND_STARPORT, addon_loc))

    async def research_cloak(self):
        '''Starts the research for banshee cloak upgrade on starport tech lab.'''
        '''Have experienced a rare bug here where the starport will lift up, but cloak will finish researching. '''
        for sp in self.units(STARPORTTECHLAB).ready.noqueue:
            if not self.already_pending_upgrade(BANSHEECLOAK) and self.can_afford(BANSHEECLOAK):
                print("Current Game Time", str(datetime.timedelta(
                    seconds=round(self.time))), ": researching cloak")
                self.combinedActions.append(sp.research(BANSHEECLOAK))

    async def build_banshee(self):
        '''Builds banshees for harass.'''
        for sp in self.units(STARPORT).ready.noqueue:
            if self.can_afford(BANSHEE) and not self.already_pending(BANSHEE) and self.banshee_count < 3:
                self.combinedActions.append(sp.train(BANSHEE))
                self.banshee_count += 1
                print("Current Game Time", str(
                    datetime.timedelta(seconds=round(self.time))))
                print("Total Banshees made:    " + str(self.banshee_count))

    def find_friendly_unit_pos(self, unit: Unit):
        '''Returns the friendly unit position in Point2 type of the unit inputted.'''
        friendly_unit_pos = unit.position
        return friendly_unit_pos

    def find_closest_enemy_worker(self, unit: Unit):
        '''Input a friendly unit. Returns the closest enemy worker unit.'''
        enemy = self.known_enemy_units.of_type([UnitTypeId.SCV,
                                                UnitTypeId.DRONE,
                                                UnitTypeId.PROBE])
        return self.find_closest_enemy_unit(unit, enemy)

    def find_closest_enemy_workers(self, unit: Unit):
        enemy = self.known_enemy_units.of_type([UnitTypeId.SCV,
                                                UnitTypeId.DRONE,
                                                UnitTypeId.PROBE])
        if enemy.exists:
            worker_pos = []
            closest_enemy_unit_pos = enemy.closer_than(7, unit)
            for u in closest_enemy_unit_pos:
                add_worker_pos = u.position
                worker_pos.append(add_worker_pos)
            return worker_pos

    def find_closest_enemy_threat(self, unit: Unit):
        '''Input a friendly unit. Returns the closest enemy unit.'''
        enemy = self.known_enemy_units.exclude_type([UnitTypeId.ADEPTPHASESHIFT,
                                                UnitTypeId.DISRUPTORPHASED,
                                                UnitTypeId.EGG,
                                                UnitTypeId.LARVA,
                                                UnitTypeId.SCV,
                                                UnitTypeId.DRONE,
                                                UnitTypeId.PROBE])
        return self.find_closest_enemy_unit(unit, enemy)

    def find_closest_enemy_unit(self, unit: Unit, enemy):
        '''Helper Function for find_closest_enemy_worker, find_closest_enemy_threat.
        Input friendly unit and enemy unit. Return closest enemy position to friendly unit in Point2 type.'''
        if enemy.exists:
            closest_enemy_unit_pos = enemy.closest_to(unit).position
            return closest_enemy_unit_pos

    def find_closest_enemy_unit_x_y(self, unit: Unit, enemy):
        '''Return closest enemy position to friendly unit in x,y type. FUNCTION MAY NOT BE NECESSARY'''
        if enemy.exists:
            closest_enemy_unit_pos_x = enemy.closest_to(unit).position.x
            closest_enemy_unit_pos_y = enemy.closest_to(unit).position.y
            return closest_enemy_unit_pos_x, closest_enemy_unit_pos_y

    def find_friendly_unit_pos_x_y(self, unit: Unit):
        '''Returns the friendly unit position in x,y values of the unit inputted. FUNCTION MAY NOT BE NECESSARY'''
        friendly_unit_pos_x = unit.position.x
        friendly_unit_pos_y = unit.position.y
        return friendly_unit_pos_x, friendly_unit_pos_y

    def find_closest_enemy_units(self, unit: Unit, enemy):
        '''Helper Function for find_closest_enemy_worker, find_closest_enemy_threat.
        Input friendly unit and enemy unit. Return closest enemy position to friendly unit in Point2 type.'''
        if enemy.exists:
            enemy_unit_pos = []
            closest_enemy_unit_pos = enemy.closer_than(7, unit)
            for u in closest_enemy_unit_pos:
                add_worker_pos = u.position
                enemy_unit_pos.append(add_worker_pos)
            return enemy_unit_pos

    def initialize_passable_tiles(self, playable_area):
        '''Initializes a 2d array the size of the map and fills values within the array with 100 if terrain is impassable
        and 0 if it is passable.'''
        self.passable_tile_map = np.zeros(playable_area)

        if self.passable_tile_check:
            for x in range(self.map.shape[0]):
                for y in range(self.map.shape[1]):
                    if not self.in_pathing_grid((x, y)):
                        self.map[x][y] = 100    #Sets value to 100 if tile is impassable.
            self.passable_tile_check = False    #Flag set to False to stop infinite looping.
            print(self.map)

    def in_pathing_grid(self, pos: Tuple):
        """ Returns True if a unit can pass through a grid point. Function is used with populate_passable_tiles"""
        return self._game_info.pathing_grid[pos] == 0   #also accepts rounded Point2 object values













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
        for g in self.geysers.filter(lambda x:x.vespene_contents > 0):
            # only loop over geysers that have still gas in them
            deficit = g.ideal_harvesters - g.assigned_harvesters
            if deficit > 0:
                deficitGeysers[g.tag] = {"unit": g, "deficit": deficit}
            elif deficit < 0:
                surplusWorkers = self.workers.closer_than(10, g).filter(lambda w:w not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER] and w.orders[0].target in geyserTags)
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
                    surplusWorkers = self.workers.closer_than(10, th).filter(lambda w:w.tag not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER] and w.orders[0].target in mineralTags)
                    # workerPool.extend(surplusWorkers)
                    for i in range(-deficit):
                        if surplusWorkers.amount > 0:
                            w = surplusWorkers.pop()
                            workerPool.append(w)
                            workerPoolTags.add(w.tag)
                    surplusTownhalls[th.tag] = {"unit": th, "deficit": deficit}

            if all([len(deficitGeysers) == 0, len(surplusGeysers) == 0, len(surplusTownhalls) == 0 or deficitTownhalls == 0]):
                # cancel early if there is nothing to balance
                return

        # check if deficit in gas less or equal than what we have in surplus, else grab some more workers from surplus bases
        deficitGasCount = sum(gasInfo["deficit"] for gasTag, gasInfo in deficitGeysers.items() if gasInfo["deficit"] > 0)
        surplusCount = sum(-gasInfo["deficit"] for gasTag, gasInfo in surplusGeysers.items() if gasInfo["deficit"] < 0)
        surplusCount += sum(-thInfo["deficit"] for thTag, thInfo in surplusTownhalls.items() if thInfo["deficit"] < 0)

        if deficitGasCount - surplusCount > 0:
            # grab workers near the gas who are mining minerals
            for gTag, gInfo in deficitGeysers.items():
                if workerPool.amount >= deficitGasCount:
                    break
                workersNearGas = self.workers.closer_than(10, gInfo["unit"]).filter(lambda w:w.tag not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER] and w.orders[0].target in mineralTags)
                while workersNearGas.amount > 0 and workerPool.amount < deficitGasCount:
                    w = workersNearGas.pop()
                    workerPool.append(w)
                    workerPoolTags.add(w.tag)

        # now we should have enough workers in the pool to saturate all gases, and if there are workers left over, make them mine at townhalls that have mineral workers deficit
        for gTag, gInfo in deficitGeysers.items():
            if performanceHeavy:
                # sort furthest away to closest (as the pop() function will take the last element)
                workerPool.sort(key=lambda x:x.distance_to(gInfo["unit"]), reverse=True)
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
                    workerPool.sort(key=lambda x:x.distance_to(thInfo["unit"]), reverse=True)
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
        Bot(Race.Terran, MechBot()),
        Computer(Race.Protoss, Difficulty.VeryEasy)
    ], realtime=False)


if __name__ == '__main__':
    main()
