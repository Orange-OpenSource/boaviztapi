import os
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

from boaviztapi.dto.component import ComponentDTO
from boaviztapi.dto.usage.usage import smart_mapper_usage, Usage
from boaviztapi.model.boattribute import Status
from boaviztapi.model.component import ComponentCPU
from boaviztapi.utils.fuzzymatch import fuzzymatch_attr_from_pdf

_cpu_df = pd.read_csv(os.path.join(os.path.dirname(__file__), '../../data/components/cpu_manufacture.csv'))
_cpu_index = pd.read_csv(os.path.join(os.path.dirname(__file__), '../../data/components/cpu_index.csv'))


class CPU(ComponentDTO):
    core_units: Optional[int] = None
    die_size: Optional[float] = None
    die_size_per_core: Optional[float] = None
    manufacturer: Optional[str] = None
    model_range: Optional[str] = None
    family: Optional[str] = None
    name: Optional[str] = None
    tdp: Optional[int] = None


def smart_mapper_cpu(cpu_dto: CPU) -> ComponentCPU:
    cpu_component = ComponentCPU()
    cpu_component.usage = smart_mapper_usage(cpu_dto.usage or Usage())

    cpu_component.units = cpu_dto.units

    if cpu_dto.name is not None:
        manufacturer, model_range, family, tdp = attributes_from_cpu_name(cpu_dto.name)
        if manufacturer is not None:
            cpu_dto.manufacturer = manufacturer
            cpu_component.manufacturer.value = manufacturer
            cpu_component.manufacturer.status = Status.COMPLETED
            cpu_component.manufacturer.source = "from name"
        if model_range is not None:
            cpu_dto.model_range = model_range
            cpu_component.model_range.value = model_range
            cpu_component.model_range.status = Status.COMPLETED
            cpu_component.model_range.source = "from name"
        if family is not None:
            cpu_dto.family = family
            cpu_component.family.value = family
            cpu_component.family.status = Status.COMPLETED
            cpu_component.family.source = "from name"
        if tdp is not None:
            cpu_dto.tdp = tdp
            cpu_component.tdp.value = tdp
            cpu_component.tdp.status = Status.COMPLETED
            cpu_component.tdp.source = "from name"

    if cpu_dto.family is not None and cpu_component.family.status != Status.COMPLETED:
        cpu_component.family.value = cpu_dto.family
        cpu_component.family.status = Status.INPUT

    if cpu_dto.core_units is not None:
        cpu_component.core_units.value = cpu_dto.core_units
        cpu_component.core_units.status = Status.INPUT

    if cpu_dto.tdp is not None and cpu_component.tdp.status != Status.COMPLETED:
        cpu_component.tdp.value = cpu_dto.tdp
        cpu_component.tdp.status = Status.INPUT

    if cpu_dto.model_range is not None and cpu_component.model_range.status != Status.COMPLETED:
        cpu_component.model_range.value = cpu_dto.model_range
        cpu_component.model_range.status = Status.INPUT

    if cpu_dto.die_size_per_core is not None:
        cpu_component.die_size_per_core.value = cpu_dto.die_size_per_core
        cpu_component.die_size_per_core.status = Status.INPUT

    if cpu_dto.die_size_per_core is not None:
        cpu_component.core_units.value = cpu_dto.core_units
        cpu_component.die_size_per_core.status = Status.INPUT

    elif cpu_dto.die_size is not None and cpu_dto.core_units is not None:
        cpu_component.die_size_per_core.value = cpu_dto.die_size / cpu_dto.core_units
        cpu_component.die_size_per_core.status = Status.COMPLETED
        cpu_component.die_size_per_core.source = "INPUT : die_size / core_units"

    else:
        sub = _cpu_df
        if cpu_dto.family is not None:
            corrected_family = fuzzymatch_attr_from_pdf(cpu_dto.family, "family", sub)
            if corrected_family != cpu_dto.family:
                cpu_component.family.value = corrected_family
                cpu_component.family.status = Status.CHANGED
            tmp = sub[sub['family'] == corrected_family]
            if len(tmp) > 0:
                sub = tmp.copy()

        if len(sub) == 0 or len(sub) == len(_cpu_df):
            pass

        elif cpu_dto.core_units is not None:
            # Find the closest line to the number of cores provided by the user
            sub['core_dif'] = sub[['core_units']].apply(lambda x: abs(x[0] - cpu_dto.core_units), axis=1)
            sub = sub.sort_values(by='core_dif', ascending=True)
            row = sub.iloc[0]

            cpu_component.die_size_per_core.value = float(row['die_size_per_core'])
            cpu_component.die_size_per_core.status = Status.COMPLETED
            cpu_component.die_size_per_core.source = row['Source']

        else:
            # Maximize die_size_per_core
            sub = sub.sort_values(by='die_size_per_core', ascending=False)
            row = sub.iloc[0]
            cpu_component.die_size_per_core.value = float(row['die_size_per_core'])
            cpu_component.die_size_per_core.status = Status.COMPLETED
            cpu_component.die_size_per_core.source = row['Source'] + "- maximizing value without core_unit given"

    return cpu_component


def attributes_from_cpu_name(cpu_name: str) -> [str, str, str, int]:
    cpu_name = cpu_name.lower()
    manufacturer, cpu_sub_name = parse(cpu_name)
    sub = _cpu_index
    if manufacturer is None:
        name_list = list(sub.sub_model_name.unique())
    else:
        name_list = list(sub[sub['manufacturer'] == manufacturer].sub_model_name.unique())
    result = fuzzymatch(cpu_sub_name, name_list)

    if result is not None:
        model_range = sub[sub['sub_model_name'] == result[0]].iloc[0].model_range
        family = sub[sub['sub_model_name'] == result[0]].iloc[0].family
        tdp = sub[sub['sub_model_name'] == result[0]].iloc[0].tdp
        if np.isnan(tdp):
            tdp = None

    else:
        model_range = None
        family = None
        tdp = None

    return manufacturer, model_range, family, tdp


def parse(cpu_name: str) -> Tuple[str, str]:
    vendor_list = ["intel", "amd", "arm"]  # every string in lowercase
    for vendor in vendor_list:
        if vendor in cpu_name:
            cpu_name.replace(vendor, '')
            return vendor, cpu_name.replace(vendor, '')
    return None, cpu_name


def fuzzymatch(cpu_name_to_match: str, cpu_name_list: list) -> Optional[Tuple[str, float, int]]:
    foo = process.extractOne(cpu_name_to_match, cpu_name_list, scorer=fuzz.WRatio)
    if foo is not None:
        return foo if foo[1] > 88.0 else None
