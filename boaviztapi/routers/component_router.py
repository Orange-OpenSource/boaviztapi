from typing import List

from fastapi import APIRouter, Body, HTTPException, Query

from boaviztapi import config
from boaviztapi.dto.component import CPU, RAM, Disk, PowerSupply, Motherboard, Case
from boaviztapi.dto.component.cpu import mapper_cpu
from boaviztapi.dto.component.other import mapper_motherboard, mapper_power_supply, mapper_case
from boaviztapi.dto.component.ram import mapper_ram
from boaviztapi.dto.component.disk import mapper_ssd, mapper_hdd
from boaviztapi.model.component import Component
from boaviztapi.routers.openapi_doc.descriptions import cpu_description, ram_description, ssd_description, \
    hdd_description, motherboard_description, power_supply_description, case_description
from boaviztapi.routers.openapi_doc.examples import components_examples
from boaviztapi.service.allocation import Allocation
from boaviztapi.service.archetype import get_component_archetype
from boaviztapi.service.bottom_up import bottom_up
from boaviztapi.service.verbose import verbose_component

component_router = APIRouter(
    prefix='/v1/component',
    tags=['component']
)


@component_router.post('/cpu',
                       description=cpu_description)
async def cpu_impact_bottom_up(cpu: CPU = Body(None, example=components_examples["cpu"]),
                               verbose: bool = True,
                               allocation: Allocation = Allocation.TOTAL,
                               archetype: str = config["default_cpu"],
                               criteria: List[str] = Query(config["default_criteria"])):
    archetype_config = get_component_archetype(archetype, "cpu")

    if not archetype_config:
        raise HTTPException(status_code=404, detail=f"{archetype} not found")

    component = mapper_cpu(cpu, archetype_config)

    return await component_impact_bottom_up(
        component=component,
        verbose=verbose,
        allocation=allocation,
        criteria=criteria
    )


@component_router.post('/ram',
                       description=ram_description)
async def ram_impact_bottom_up(ram: RAM = Body(None, example=components_examples["ram"]),
                               verbose: bool = True,
                               allocation: Allocation = Allocation.TOTAL, archetype: str = config["default_ram"],
                               criteria: List[str] = Query(config["default_criteria"])):
    archetype_config = get_component_archetype(archetype, "ram")

    if not archetype_config:
        raise HTTPException(status_code=404, detail=f"{archetype} not found")

    component = mapper_ram(ram, archetype_config)

    return await component_impact_bottom_up(
        component=component,
        verbose=verbose,
        allocation=allocation,
        criteria=criteria
    )


@component_router.post('/ssd',
                       description=ssd_description)
async def disk_impact_bottom_up(disk: Disk = Body(None, example=components_examples["ssd"]),
                                verbose: bool = True,
                                allocation: Allocation = Allocation.TOTAL, archetype: str = config["default_ssd"],
                                criteria: List[str] = Query(config["default_criteria"])):
    disk.type = "ssd"
    archetype_config = get_component_archetype(archetype, "ssd")

    if not archetype_config:
        raise HTTPException(status_code=404, detail=f"{archetype} not found")

    component = mapper_ssd(disk, archetype_config)

    return await component_impact_bottom_up(
        component=component,
        verbose=verbose,
        allocation=allocation,
        criteria=criteria
    )


@component_router.post('/hdd',
                       description=hdd_description)
async def disk_impact_bottom_up(disk: Disk = Body(None, example=components_examples["hdd"]),
                                verbose: bool = True,
                                allocation: Allocation = Allocation.TOTAL, archetype: str = config["default_hdd"],
                                criteria: List[str] = Query(config["default_criteria"])):
    disk.type = "hdd"
    archetype_config = get_component_archetype(archetype, "hdd")

    if not archetype_config:
        raise HTTPException(status_code=404, detail=f"{archetype} not found")

    component = mapper_hdd(disk, archetype_config)

    return await component_impact_bottom_up(
        component=component,
        verbose=verbose,
        allocation=allocation,
        criteria=criteria
    )


@component_router.post('/motherboard',
                       description=motherboard_description)
async def motherboard_impact_bottom_up(
        motherboard: Motherboard = Body(None, example=components_examples["motherboard"]),
        verbose: bool = True, allocation: Allocation = Allocation.TOTAL,
        criteria: List[str] = Query(config["default_criteria"])):

    completed_motherboard = mapper_motherboard(motherboard)

    return await component_impact_bottom_up(
        component=completed_motherboard,
        verbose=verbose,
        allocation=allocation,
        criteria=criteria
    )


@component_router.post('/power_supply',
                       description=power_supply_description)
async def power_supply_impact_bottom_up(
        power_supply: PowerSupply = Body(None, example=components_examples["power_supply"]),
        verbose: bool = True, allocation: Allocation = Allocation.TOTAL, archetype: str = config["default_power_supply"],
                               criteria: List[str] = Query(config["default_criteria"])):

    archetype_config = get_component_archetype(archetype, "power_supply")

    if not archetype_config:
        raise HTTPException(status_code=404, detail=f"{archetype} not found")

    completed_power_supply = mapper_power_supply(power_supply, archetype_config)

    return await component_impact_bottom_up(
        component=completed_power_supply,
        verbose=verbose,
        allocation=allocation,
        criteria=criteria
    )


@component_router.post('/case',
                       description=case_description)
async def case_impact_bottom_up(case: Case = Body(None, example=components_examples["case"]),
                                verbose: bool = True,
                                allocation: Allocation = Allocation.TOTAL, archetype: str = config["default_case"],
                                criteria: List[str] = Query(config["default_criteria"])):
    archetype_config = get_component_archetype(archetype, "hdd")

    if not archetype_config:
        raise HTTPException(status_code=404, detail=f"{archetype} not found")

    completed_case = mapper_case(case)

    return await component_impact_bottom_up(
        component=completed_case,
        verbose=verbose,
        allocation=allocation,
        criteria=criteria
    )


async def component_impact_bottom_up(component: Component,
                                     verbose: bool, allocation: Allocation, criteria=config["default_criteria"]) -> dict:

    impacts = bottom_up(model=component, allocation=allocation, selected_criteria=criteria)
    if verbose:
        return {
            "impacts": impacts,
            "verbose": verbose_component(component=component, selected_criteria=criteria)
        }
    return impacts