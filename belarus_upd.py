import os
from collections import defaultdict
from itertools import chain
from typing import Dict, Optional, List, Iterable, Sequence, Tuple

import shapely.algorithms
import shapely.geometry
import shapely.ops
import shapely.strtree
import shapely.validation
import shapely.wkt

from belarus_utils import (
    ChangeRule, DependantChangeRule, FoundElement, ElementRuleChange, ElementChanges, Issue,
    BaseSearchReadWriteEngine, PostgisSearchReadEngine, OsmApiReadWriteEngine, GeoJsonWriteEngine,
    OsmChangeWriteEngine, PrintIssuesEngine, ManualChange, CYRILIC_CHARS,
)

POSTGRES_HOST = os.environ['POSTGRES_HOST']
POSTGRES_HOST2 = os.environ['POSTGRES_HOST2']
POSTGRES_PORT = os.environ['POSTGRES_PORT']
POSTGRES_DB = os.environ['POSTGRES_DB']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
OSM_USER = os.environ['OSM_USER']
OSM_PASSWORD = os.environ['OSM_PASSWORD']
DRY_RUN = bool(int(os.environ['DRY_RUN']))
RULES = [
    # admin
    ChangeRule('вобласьці', 'name', {'admin_level': ['4']}),
    ChangeRule('раёны', 'name', {'admin_level': ['6']}),
    ChangeRule('сельскія саветы', 'name', {'admin_level': ['8']}),
    ChangeRule('гарадзкія раёны', 'name', {'admin_level': ['9']}),

    # place
    ChangeRule('населенныя пункты', 'name', {'place': [
        'city', 'town', 'village', 'hamlet', 'isolated_dwelling',
    ]}),
    ChangeRule('населенныя пункты', 'name', {'boundary': ['administrative']}),
    ChangeRule('населенныя пункты', 'name', {'admin_level': None}),
    ChangeRule('населенныя пункты', 'name', {'traffic_sign': ['city_limit']}),
    ChangeRule('населенныя пункты - прэфіксы', 'name:prefix', {'place': [
        'city', 'town', 'village', 'hamlet', 'isolated_dwelling',
    ]}),
    ChangeRule('населенныя пункты - прэфіксы', 'name:prefix', {'boundary': ['administrative']}),
    ChangeRule('населенныя пункты - прэфіксы', 'name:prefix', {'admin_level': None}),

    # allotments
    ChangeRule('садовыя таварыствы', 'name', {'place': ['allotments']}),
    ChangeRule('садовыя таварыствы', 'name', {'landuse': ['allotments']}),
    ChangeRule('садовыя таварыствы', 'short_name', {'place': ['allotments']}),
    ChangeRule('садовыя таварыствы', 'short_name', {'landuse': ['allotments']}),
    ChangeRule('садовыя таварыствы', 'official_name', {'place': ['allotments']}),
    ChangeRule('садовыя таварыствы', 'official_name', {'landuse': ['allotments']}),
    ChangeRule('садовыя таварыствы - статусы', 'official_status', {'place': ['allotments']}),
    ChangeRule('садовыя таварыствы - статусы', 'official_status', {'landuse': ['allotments']}),

    # locality
    ChangeRule('урочышча', 'name', {'place': ['locality']}),
    ChangeRule('урочышча', 'name', {'abandoned:place': None}),
    ChangeRule('урочышча - прэфіксы', 'name:prefix', {'place': ['locality']}),
    ChangeRule('урочышча - прэфіксы', 'name:prefix', {'abandoned:place': None}),
    ChangeRule('урочышча - прэфіксы', 'was:name:prefix', {'place': ['locality']}),
    ChangeRule('урочышча - прэфіксы', 'was:name:prefix', {'abandoned:place': None}),

    # suburb

    # highway
    ChangeRule('дарогі', 'name', {'highway': None}),
    ChangeRule('дарогі', 'name', {'type': ['associatedStreet', 'street']}),

    # public_transport
    # infrastructure
    # religion
    # education
    # healthcare
    # government
    # office
    # amenity
    # building
    # water
    # natural
]
DEPENDANT_RULES = [
    DependantChangeRule('dep', 'addr:region'),
    DependantChangeRule('dep', 'addr:district'),
    DependantChangeRule('dep', 'addr:subdistrict'),
    DependantChangeRule('dep', 'addr:city'),
    DependantChangeRule('dep', 'addr:place'),
    DependantChangeRule('dep', 'addr:street'),
    DependantChangeRule('dep', 'addr2:street'),

    DependantChangeRule('dep', 'from'),
    DependantChangeRule('dep', 'to'),
    DependantChangeRule('dep', 'via'),
    DependantChangeRule('dep', 'destination'),
    DependantChangeRule('dep', 'destination:backward'),
    DependantChangeRule('dep', 'destination:forward'),

    DependantChangeRule('dep', 'water_tank:city'),
]
MANUAL = [
    # osm_type, osm_id, name:ru, name:be
    (None, None,
     'Пограничная полоса - Border line',
     'Памежная паласа - Border line'),
    (None, None,
     'Пограничная полоса - Border Line',
     'Памежная паласа - Border Line'),
    (None, None,
     'Пограничная зона - Border line',
     'Памежная зона - Border line'),
    (None, None,
     'Пограничная полоса - Border zone',
     'Памежная паласа - Border zone'),
    (None, None,
     'Пограничная полоса - Border Line (Водопропуск за изгордью системы с КСП)',
     'Памежная паласа - Border Line (Водапропуск за агароджаю сыстэмы з КСП)'),
    (None, None,
     'Пограничная полоса - Border Line (Левый Фланг 3 Погз)',
     'Памежная паласа - Border Line (Левы Фланг 3 Погз)'),
    (None, None,
     'Р45 Зелёный коридор / Green Lane',
     'Р45 Зялёны калідор / Green Lane'),
    (None, None,
     'Р45 (Зялёны калідор / Green Lane)',
     'Р45 (Зелёный коридор / Green Lane'),
    (None, None,
     'Р45 (Красный коридор / Red lane)',
     'Р45 (Чырвоны калідор / Red lane)'),
    (None, None,
     'Р45 (Зелёный коридор / Green channel)',
     'Р45 (Зялёны калідор / Green channel)'),
    (None, None,
     'Р45 (Красный коридор / Red channel)',
     'Р45 (Чырвоны калідор / Red channel)'),
    (None, None,
     'М7 (Зелёный коридор / Green lane)',
     'М7 (Зялёны калідор / Green lane)'),
    (None, None,
     'М7 (Красный коридор/Red lane)',
     'М7 (Чырвоны калідор/Red Lane)'),
]
OUT_OF_BORDER_NAMES = [
    ('Масква', 'Москва', 'Москва'),
    ('Вільнюс', 'Вильнюс', 'Vilnius'),
    ('Пскоў', 'Псков', 'Псков'),
    ('Чарнігаў', 'Чернигов', 'Чернігів'),
    ('Жытомір', 'Житомир', 'Житомир'),
    ('Луцк', 'Луцк', 'Луцк'),
    ('Беласток', 'Белосток', 'Białystok', 'Bialystok'),
    ('Смаленск', 'Смоленск', 'Смоленск'),
    ('Друскінінкай', 'Друскининкай', 'Druskininkai'),
    ('Санкт-Пецярбург', 'Санкт-Петербург', 'Санкт-Петербург'),
]


class Engine:
    def __init__(
            self,
            search_engine: BaseSearchReadWriteEngine,
            read_engine: BaseSearchReadWriteEngine,
            write_engine: BaseSearchReadWriteEngine,
            issues_engine: BaseSearchReadWriteEngine,
            suffix_from: str,
            suffix_to: str,
    ):
        self._search_engine = search_engine
        self._read_engine = read_engine
        self._write_engine = write_engine
        self._issues_engine = issues_engine
        self._suffix_from = suffix_from
        self._suffix_to = suffix_to

    @staticmethod
    def _choose_nearest(
        indexes: Dict[str, shapely.strtree.STRtree],
        elements: Dict[str, Sequence[FoundElement]],
        value: str,
        way: str,
    ):
        if len(elements[value]) == 1:
            return elements[value][0]
        geom = shapely.wkt.loads(way)
        i = indexes[value].nearest_item(geom)
        return elements[value][i]

    @staticmethod
    def _geom_type_order(geom_wkt: str):
        # there are can be duplicates in poly and line for same osm_type and osm_id,
        # so for deduplication it important use right order to prevent poly disappearing
        for i, prefix in enumerate([
            'POINT',
            'MULTIPOINT',
            'LINESTRING',
            'MULTILINESTRING',
            'POLYGON',
            'MULTIPOLYGON',
            'GEOMETRYCOLLECTION',
        ]):
            if geom_wkt.startswith(prefix):
                return i
        raise TypeError(geom_wkt)

    def tags_switch(
            self,
            rules: Iterable[ChangeRule],
            dependant_rules: Iterable[DependantChangeRule],
            manual: List[Tuple[Optional[str], Optional[int], Optional[str], str]],
            out_border_name_map: Dict[str, str],
    ) -> List[int]:
        changes = list(self._rule_changes(rules, manual))
        dependant_changes = list(self._dependant_rule_changes(dependant_rules, out_border_name_map))
        return self._update_elements(changes + dependant_changes)

    def _rule_changes(
            self,
            rules: Iterable[ChangeRule],
            manual: List[Tuple[Optional[str], Optional[int], Optional[str], str]],
    ) -> Iterable[ElementRuleChange]:
        manual_by_id = {
            (osm_type, osm_id): ManualChange(osm_type, osm_id, value_from, value_to)
            for osm_type, osm_id, value_from, value_to in manual
            if osm_type and osm_id
        }
        manual_by_value_to = {
            value_to: ManualChange(osm_type, osm_id, value_from, value_to)
            for osm_type, osm_id, value_from, value_to in manual
        }
        manual_by_value_from = {
            value_from: ManualChange(osm_type, osm_id, value_from, value_to)
            for osm_type, osm_id, value_from, value_to in manual
            if value_from
        }

        for rule in rules:
            print(f'search {rule}')
            tag_from = f'{rule.update_tag}:{self._suffix_from}'
            tag_to = f'{rule.update_tag}:{self._suffix_to}'
            found_elements = self._find_elements(
                {rule.update_tag: None, tag_from: None, tag_to: None, **rule.search_tags}
            )
            for found_element in found_elements:
                if (found_element.osm_type, found_element.osm_id) in manual_by_id:
                    manual = manual_by_id[(found_element.osm_type, found_element.osm_id)]
                    value_from = manual.value_from
                    value_to = manual.value_to
                elif found_element.tags[rule.update_tag] in manual_by_value_from:
                    manual = manual_by_value_from[found_element.tags[rule.update_tag]]
                    value_from = manual.value_from
                    value_to = manual.value_to
                elif found_element.tags[rule.update_tag] in manual_by_value_to:
                    manual = manual_by_value_to[found_element.tags[rule.update_tag]]
                    value_from = manual.value_to
                    value_to = manual.value_to
                else:
                    value_from = found_element.tags[tag_from]
                    value_to = found_element.tags[tag_to]
                element_change = ElementRuleChange(
                    rule.comment,
                    found_element.osm_id,
                    found_element.osm_type,
                    rule.update_tag,
                    value_from,
                    value_to,
                    True,
                    tuple([found_element.osm_id]),
                    tuple([found_element.osm_type]),
                )
                if self._valid_for_update(element_change, found_element.tags):
                    yield element_change

    def _dependant_rule_changes(
            self,
            dependant_rules: Iterable[DependantChangeRule],
            out_border_name_map: Dict[str, str],
    ) -> Iterable[ElementRuleChange]:
        print('search dependants')
        names = list({
            (element.osm_id, element.osm_type): element
            for element in sorted(chain(
                self._search_engine.search({'name': None}),
                self._search_engine.search({'name:be': None}),
                self._search_engine.search({'name:ru': None}),
            ), key=lambda element: self._geom_type_order(element.way))
        }.values())
        name_elements = defaultdict(list)
        for element in names:
            if 'name' in element.tags:
                name_elements[element.tags['name']].append(element)
            if 'name:be' in element.tags and element.tags['name:be'] != element.tags.get('name'):
                name_elements[element.tags['name:be']].append(element)
            if 'name:ru' in element.tags and element.tags['name:ru'] != element.tags.get('name') \
                    and element.tags['name:ru'] != element.tags.get('name:be'):
                name_elements[element.tags['name:ru']].append(element)
        name_index = {}
        for name, elements in name_elements.items():
            name_index[name] = shapely.strtree.STRtree([shapely.wkt.loads(element.way) for element in elements])

        names_full = [
            element
            for element in names
            if 'name' in element.tags
            and 'name:be' in element.tags
            and 'name:ru' in element.tags
        ]
        name_elements_full = defaultdict(list)
        for element in names_full:
            if 'name' in element.tags:
                name_elements_full[element.tags['name']].append(element)
            if 'name:be' in element.tags and element.tags['name:be'] != element.tags.get('name'):
                name_elements_full[element.tags['name:be']].append(element)
            if 'name:ru' in element.tags and element.tags['name:ru'] != element.tags.get('name') \
                    and element.tags['name:ru'] != element.tags.get('name:be'):
                name_elements_full[element.tags['name:ru']].append(element)
        name_index_full = {}
        for name, elements in name_elements_full.items():
            name_index_full[name] = shapely.strtree.STRtree([shapely.wkt.loads(element.way) for element in elements])

        for dependant_rule in dependant_rules:
            print(f'search dependant {dependant_rule}')
            tag = dependant_rule.update_tag
            stat_el_ok = stat_el_part = stat_el_zero = stat_ok = stat_no_lang = stat_not_found = 0
            no_lang = defaultdict(list)
            not_found = defaultdict(list)
            values = defaultdict(list)

            for element in self._search_engine.search({tag: None}):
                values[element.tags[tag]].append(element)
                origin = []
                change = []
                change_el = []
                split = ';'
                if not (frozenset(element.tags[tag]) & CYRILIC_CHARS):
                    continue
                for value in element.tags[tag].split(split):
                    value = value.strip()
                    origin.append(value)
                    if value in name_elements_full:
                        found_element = self._choose_nearest(name_index_full, name_elements_full, value, element.way)
                        stat_ok += 1
                        if f'name:{self._suffix_to}' in found_element.tags:
                            change.append(found_element.tags[f'name:{self._suffix_to}'])
                            change_el.append(found_element)
                    elif value.count(' - ') == 1 and value.split(' - ')[-1].isdigit() \
                            and value.split(' - ')[0] in name_elements_full:
                        value_main, value_num = value.split(' - ')
                        found_element = self._choose_nearest(
                            name_index_full, name_elements_full, value_main, element.way)
                        stat_ok += 1
                        if f'name:{self._suffix_to}' in found_element.tags:
                            change.append(found_element.tags[f'name:{self._suffix_to}'] + ' - ' + value_num)
                            change_el.append(found_element)
                    elif value in out_border_name_map:
                        to_value = out_border_name_map[value]
                        change.append(to_value)
                    elif value in name_elements:
                        found_element = self._choose_nearest(name_index, name_elements, value, element.way)
                        stat_no_lang += 1
                        no_lang[(
                            value,
                            found_element.tags.get('name'),
                            found_element.tags.get(f'name:{self._suffix_from}'),
                            found_element.tags.get(f'name:{self._suffix_to}'),
                        )].append((element.osm_type, element.osm_id))
                    else:
                        stat_not_found += 1
                        not_found[(value,)].append((element.osm_type, element.osm_id))

                if len(origin) == len(change):
                    stat_el_ok += 1
                elif change:
                    stat_el_part += 1
                else:
                    stat_el_zero += 1

                if len(origin) == len(change):
                    osm_type_id_change = sorted((e.osm_type, e.osm_id) for e in change_el)
                    element_change = ElementRuleChange(
                        tag,
                        element.osm_id,
                        element.osm_type,
                        tag,
                        element.tags[tag],
                        split.join(change),
                        False,
                        tuple(osm_id for osm_type, osm_id in osm_type_id_change),
                        tuple(osm_type for osm_type, osm_id in osm_type_id_change),
                    )
                    yield element_change

    def _find_elements(self, search_tags: Dict[str, Optional[Iterable[str]]]) -> List[FoundElement]:
        return self._search_engine.search(search_tags)

    def _valid_for_update(self, element: ElementRuleChange, tags: Dict[str, str]) -> bool:
        if element.main:
            # main element should have language suffix tags
            tag_from = f'{element.update_tag}:{self._suffix_from}'
            tag_to = f'{element.update_tag}:{self._suffix_to}'
            # assert tags[element.update_tag] in (tags[tag_from], tags[tag_to])
            if tags[element.update_tag] not in (element.value_from, element.value_to):
                self._issues_engine.report_issue(
                    Issue(message=Issue.ISSUE_TAG_VALUE_NOT_IN_LANGUAGE_TAGS, changes=[element], extra={
                        element.update_tag: tags[element.update_tag],
                    })
                )
            return (
                element.update_tag in tags
                and tag_from in tags
                and tag_to in tags
                and tags[element.update_tag] == element.value_from
                and tags[tag_from] == element.value_from
                and tags[tag_to] == element.value_to
                and element.value_from != element.value_to
            )
        else:
            # dependant element in general miss language suffix tags
            return (
                element.update_tag in tags
                and tags[element.update_tag] == element.value_from
                and element.value_from != element.value_to
            )

    def _update_element(self, data: dict, elements: Iterable[ElementRuleChange]) -> ElementChanges:
        changes = []
        for element in elements:
            if data['visible'] and self._valid_for_update(element, data['tag']):
                data['tag'][element.update_tag] = element.value_to
                changes.append(element)
        return ElementChanges(data, changes)

    def _update_elements(self, elements: Iterable[ElementRuleChange]) -> List[int]:
        # group changes per osm element
        nodes = defaultdict(set)
        ways = defaultdict(set)
        relations = defaultdict(set)
        for element in elements:
            if element.osm_type == 'node':
                nodes[element.osm_id].add(element)
            elif element.osm_type == 'way':
                ways[element.osm_id].add(element)
            elif element.osm_type == 'relation':
                relations[element.osm_id].add(element)

        # validate grouped changes
        skip_node = set()
        skip_way = set()
        skip_rel = set()
        skip_type = {'node': skip_node, 'way': skip_way, 'relation': skip_rel}
        for element_changes in chain(nodes.values(), ways.values(), relations.values()):
            counter = defaultdict(set)
            for element in element_changes:
                counter[element.update_tag].add((element.value_from, element.value_to))
            if any(len(updates) != 1 for tag, updates in counter.items()):
                skip_type[element.osm_type].add(element.osm_id)

                self._issues_engine.report_issue(Issue(
                    message=Issue.ISSUE_TAG_CHANGED_WITH_DIFFERENT_VALUES,
                    changes=list(element_changes),
                    extra={tag: updates for tag, updates in counter.items() if len(updates) != 1}
                ))

        # fetch real latest data ready to update (this required to avoid optimistic lock)
        nodes_data = self._read_engine.read_nodes(nodes.keys() - skip_node)
        ways_data = self._read_engine.read_ways(ways.keys() - skip_way)
        relations_data = self._read_engine.read_relations(relations.keys() - skip_rel)

        # update latest data
        upd_nodes_data = [self._update_element(node, nodes[osm_id]) for osm_id, node in nodes_data.items()]
        upd_ways_data = [self._update_element(way, ways[osm_id]) for osm_id, way in ways_data.items()]
        upd_relations_data = [self._update_element(rel, relations[osm_id]) for osm_id, rel in relations_data.items()]
        upd_data = [change for change in chain(upd_nodes_data, upd_ways_data, upd_relations_data) if change.changes]

        # save changes
        return self._write_engine.write(upd_data)


if __name__ == '__main__':
    postgis_search_engine = PostgisSearchReadEngine(
        host=POSTGRES_HOST2,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    osm_api_rw_engine = OsmApiReadWriteEngine(username=OSM_USER, password=OSM_PASSWORD, dry_run=DRY_RUN)
    osm_change_w_engine = OsmChangeWriteEngine('belarus-result.osc')
    geojson_w_engine = GeoJsonWriteEngine(postgis_search_engine, 'results')
    print_issues_engine = PrintIssuesEngine()

    Engine(
        search_engine=postgis_search_engine,
        read_engine=postgis_search_engine,
        # read_engine=osm_api_rw_engine,
        # write_engine=osm_api_rw_engine,
        write_engine=osm_change_w_engine,
        # write_engine=geojson_w_engine,
        issues_engine=print_issues_engine,
        suffix_from='ru',
        suffix_to='be',
    ).tags_switch(
        RULES,
        DEPENDANT_RULES,
        MANUAL,
        {v: vv[2] if v == vv[2] else vv[0] for vv in OUT_OF_BORDER_NAMES for v in vv},
    )