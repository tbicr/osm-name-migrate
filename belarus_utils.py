import dataclasses
import datetime
import functools
import json
import math
import os
import time
import urllib.parse
from collections import defaultdict
from functools import partial
from itertools import chain
from typing import Sequence, Dict, Optional, Tuple, List, Iterable
from xml.sax.saxutils import quoteattr

import shapely.geometry
import shapely.ops
import shapely.validation
import shapely.wkt


def _split_chunks(items: Sequence, max_chunk_size: int):
    for i in range(0, len(items), max_chunk_size):
        yield items[i:i + max_chunk_size]


@dataclasses.dataclass(frozen=True, slots=True)
class ChangeDependant:
    comment: str
    search_tags: Dict[str, Optional[Sequence[str]]]
    update_tag: str


@dataclasses.dataclass(frozen=True, slots=True)
class ChangeRule:
    comment: str
    search_tags: Dict[str, Optional[Sequence[str]]]
    update_tag: str
    dependants: Sequence[ChangeDependant]


@dataclasses.dataclass(frozen=True, slots=True)
class FoundElement:
    osm_id: int
    osm_type: str
    lon: Optional[float]
    lat: Optional[float]
    way: Optional[str]
    tags: Dict[str, str]

    @property
    def osm_tid(self) -> str:
        return f'{self.osm_type[0]}{self.osm_id}'

    @property
    def osm_url(self) -> str:
        return f'https://www.openstreetmap.org/{self.osm_type}/{self.osm_id}'


@dataclasses.dataclass(frozen=True, slots=True)
class ElementRuleChange:
    comment: str
    osm_id: int
    osm_type: str
    update_tag: str
    value_from: str
    value_to: str
    main: bool
    use_osm_id: Tuple[int, ...]
    use_osm_type: Tuple[str, ...]

    @property
    def osm_tid(self) -> str:
        return f'{self.osm_type[0]}{self.osm_id}'

    @property
    def osm_url(self) -> str:
        return f'https://www.openstreetmap.org/{self.osm_type}/{self.osm_id}'


@dataclasses.dataclass(frozen=True, slots=True)
class ElementChanges:
    data: dict
    changes: Sequence[ElementRuleChange]

    @property
    def osm_type(self) -> str:
        return self.changes[0].osm_type

    @property
    def osm_id(self) -> int:
        return self.changes[0].osm_id

    @property
    def osm_tid(self) -> str:
        return f'{self.osm_type[0]}{self.osm_id}'

    @property
    def osm_url(self) -> str:
        return self.changes[0].osm_url


@dataclasses.dataclass(frozen=True, slots=True)
class Issue:
    ISSUE_TAG_VALUE_NOT_IN_LANGUAGE_TAGS = '111 tag value not in language tags'
    ISSUE_SAME_VALUES_IN_FROM_AND_TO_LANGUAGE_TAGS = '222 same values in from and to language tags'
    ISSUE_FROM_HAS_MORE_THAN_ONE_TO_VARIANTS = '333 from has more than one to variants'
    ISSUE_TO_HAS_MORE_THAN_ONE_FROM_VARIANTS = '444 to has more than one from variants'
    ISSUE_TAG_CHANGED_WITH_DIFFERENT_VALUES = '555 tag changed with different values'

    message: str
    changes: Sequence[ElementRuleChange]
    extra: Optional[dict] = None

    @property
    def osm_type(self) -> str:
        return self.changes[0].osm_type

    @property
    def osm_id(self) -> int:
        return self.changes[0].osm_id

    @property
    def osm_tid(self) -> str:
        return f'{self.osm_type[0]}{self.osm_id}'

    @property
    def osm_url(self) -> str:
        return self.changes[0].osm_url

    def __str__(self):
        return '\n'.join([
            f"Issue(message='{self.message}', changes=[",
            *('  ' + str(change) for change in self.changes),
            f"], extra={self.extra})",
        ])


class BaseSearchReadWriteEngine:
    MAX_READ_CHUNK = 725
    MAX_WRITE_CHUNK = 5000

    def _match_tags(self, search_tags: Dict[str, Optional[Sequence[str]]], data_tags: Dict[str, str]) -> bool:
        return all(
            tag in data_tags and (not search_tags[tag] or data_tags[tag] in search_tags[tag])
            for tag in search_tags.keys()
        )

    def search(self, search_tags: Dict[str, Optional[Sequence[str]]]) -> List[FoundElement]:
        raise NotImplementedError()

    def read_nodes(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        raise NotImplementedError()

    def read_ways(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        raise NotImplementedError()

    def read_relations(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        raise NotImplementedError()

    def write(self, changes: Sequence[ElementChanges]) -> List[int]:
        raise NotImplementedError()

    def report_issue(self, issue: Issue):
        raise NotImplementedError


class DumpSearchEngine(BaseSearchReadWriteEngine):
    def __init__(self, filename: str = 'belarus-latest.osm.pbf'):
        self._filename = filename

    def search(self, search_tags: Dict[str, Optional[Sequence[str]]]) -> List[FoundElement]:
        from imposm.parser import OSMParser

        results = []

        def process(params, osm_type):
            for osm_id, tags, _ in params:
                if self._match_tags(search_tags, tags):
                    results.append(FoundElement(osm_id, osm_type, None, None, None, tags))

        OSMParser(
            nodes_callback=partial(process, type_='node'),
            ways_callback=partial(process, type_='way'),
            relations_callback=partial(process, type_='relation'),
        ).parse(self._filename)

        return results


class PostgisSearchReadEngine(BaseSearchReadWriteEngine):
    REGION_VIEW_SQL = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS planet_osm_region AS

        SELECT
            osm_id,
            tags->'name' AS name,
            tags->'name:be' AS name_be,
            tags->'name:ru' AS name_ru,
            tags->'admin_level' AS admin_level,
            ST_Buffer(way, -0.000000001) AS way
        FROM planet_osm_polygon
        WHERE tags->'admin_level' IN ('2', '4', '6', '8', '9')
    """
    REGION_WAY_INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS planet_osm_region_way_idx 
        ON planet_osm_region USING GIST (way)
    """
    REGION_ANALYZE_SQL = "ANALYZE planet_osm_region"

    OSM_DATA_VIEW_SQL = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS planet_osm_data_{suffix} AS

        SELECT
            g.osm_id AS osm_id,
            'node' AS osm_type,
            'point' AS kind,
            g.tags AS tags,
            g.tags->'name' AS name,
            g.tags->'name:be' AS name_be,
            g.tags->'name:ru' AS name_ru,
            ST_X(ST_Centroid(g.way)) AS lon,
            ST_Y(ST_Centroid(g.way)) AS lat,
            g.way AS way
        FROM planet_osm_point g
        INNER JOIN planet_osm_region p
        ON ST_Intersects(p.way, g.way)
        WHERE p.osm_id = {region}

        UNION ALL

        SELECT
            ABS(g.osm_id) AS osm_id,
            CASE WHEN g.osm_id < 0 THEN 'relation' ELSE 'way' END AS osm_type,
            'line' AS kind,
            g.tags AS tags,
            g.tags->'name' AS name,
            g.tags->'name:be' AS name_be,
            g.tags->'name:ru' AS name_ru,
            ST_X(ST_Centroid(g.way)) AS lon,
            ST_Y(ST_Centroid(g.way)) AS lat,
            g.way AS way
        FROM planet_osm_line g
        INNER JOIN planet_osm_region p
        ON ST_Intersects(p.way, g.way)
        WHERE p.osm_id = {region}
        
        UNION ALL

        SELECT
            ABS(g.osm_id) AS osm_id,
            CASE WHEN g.osm_id < 0 THEN 'relation' ELSE 'way' END AS osm_type,
            'road' AS kind,
            g.tags AS tags,
            g.tags->'name' AS name,
            g.tags->'name:be' AS name_be,
            g.tags->'name:ru' AS name_ru,
            ST_X(ST_Centroid(g.way)) AS lon,
            ST_Y(ST_Centroid(g.way)) AS lat,
            g.way AS way
        FROM planet_osm_roads g
        INNER JOIN planet_osm_region p
        ON ST_Intersects(p.way, g.way)
        WHERE p.osm_id = {region}

        UNION ALL

        SELECT
            ABS(g.osm_id) AS osm_id,
            CASE WHEN g.osm_id < 0 THEN 'relation' ELSE 'way' END AS osm_type,
            'poly' AS kind,
            g.tags AS tags,
            g.tags->'name' AS name,
            g.tags->'name:be' AS name_be,
            g.tags->'name:ru' AS name_ru,
            ST_X(ST_Centroid(g.way)) AS lon,
            ST_Y(ST_Centroid(g.way)) AS lat,
            g.way AS way
        FROM planet_osm_polygon g
        INNER JOIN planet_osm_region p
        ON ST_Intersects(p.way, g.way)
        WHERE p.osm_id = {region}
    """
    OSM_DATA_OSM_ID_TYPE_INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS planet_osm_data_{suffix}_osm_id_type_idx 
        ON planet_osm_data_{suffix} (osm_id, osm_type)
    """
    OSM_DATA_NAME_INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS planet_osm_data_{suffix}_name_idx 
        ON planet_osm_data_{suffix} (name)
    """
    OSM_DATA_NAME_BE_INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS planet_osm_data_{suffix}_name_be_idx 
        ON planet_osm_data_{suffix} (name_be)
    """
    OSM_DATA_NAME_RU_INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS planet_osm_data_{suffix}_name_ru_idx 
        ON planet_osm_data_{suffix} (name_ru)
    """
    OSM_DATA_TAGS_INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS planet_osm_data_{suffix}_tags_idx 
        ON planet_osm_data_{suffix} USING GIN (tags)
    """
    OSM_DATA_WAY_INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS planet_osm_data_{suffix}_way_idx
        ON planet_osm_data_{suffix} USING GIST (way)
    """
    OSM_DATA_ANALYZE_SQL = "ANALYZE planet_osm_data_{suffix}"

    def __init__(self, region: int = -59065, **params):
        self._region = region
        self._suffix = str(region).replace('-', '_')
        self._params = params
        self.data_table = f'planet_osm_data_{self._suffix}'

    def _values_str(self, values):
        return ', '.join("'" + value.replace("'", "''") + "'" for value in values)

    def insert_extra_relations(self, items: List[FoundElement]):
        import psycopg2
        with psycopg2.connect(**self._params) as conn:
            with conn.cursor() as cur:
                node_ids = ','.join(str(item.osm_id) for item in items if item.osm_type == 'node')
                way_rel_ids = ','.join(
                    [str(item.osm_id) for item in items if item.osm_type == 'way'] +
                    [str(-item.osm_id) for item in items if item.osm_type == 'relation']
                )
                cur.execute('BEGIN')
                if node_ids:
                    cur.execute(f'DELETE FROM planet_osm_point WHERE osm_id IN ({node_ids})')
                if way_rel_ids:
                    cur.execute(f'DELETE FROM planet_osm_line WHERE osm_id IN ({way_rel_ids})')
                    cur.execute(f'DELETE FROM planet_osm_roads WHERE osm_id IN ({way_rel_ids})')
                    cur.execute(f'DELETE FROM planet_osm_polygon WHERE osm_id IN ({way_rel_ids})')
                for item in items:
                    osm_id = -item.osm_id if item.osm_type == 'relation' else item.osm_id
                    table = 'planet_osm_point' if item.osm_type == 'node' else 'planet_osm_polygon'
                    query = f"""
                        INSERT INTO {table} (osm_id, tags, way) 
                        VALUES (%s, hstore(%s, %s), ST_GeomFromText(%s, 4326))
                    """
                    cur.execute(query, (osm_id, list(item.tags.keys()), list(item.tags.values()), item.way))
                cur.execute('COMMIT')

    @functools.cache
    def create_materialized_views(self):
        import psycopg2
        with psycopg2.connect(**self._params) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(self.REGION_VIEW_SQL)
                cur.execute(self.REGION_WAY_INDEX_SQL)
                cur.execute(self.REGION_ANALYZE_SQL)

                cur.execute(self.OSM_DATA_VIEW_SQL.format(suffix=self._suffix, region=self._region))
                cur.execute(self.OSM_DATA_OSM_ID_TYPE_INDEX_SQL.format(suffix=self._suffix, region=self._region))
                cur.execute(self.OSM_DATA_TAGS_INDEX_SQL.format(suffix=self._suffix, region=self._region))
                cur.execute(self.OSM_DATA_NAME_INDEX_SQL.format(suffix=self._suffix, region=self._region))
                cur.execute(self.OSM_DATA_NAME_BE_INDEX_SQL.format(suffix=self._suffix, region=self._region))
                cur.execute(self.OSM_DATA_NAME_RU_INDEX_SQL.format(suffix=self._suffix, region=self._region))
                cur.execute(self.OSM_DATA_WAY_INDEX_SQL.format(suffix=self._suffix, region=self._region))
                cur.execute(self.OSM_DATA_ANALYZE_SQL.format(suffix=self._suffix, region=self._region))

    def search(self, search_tags: Dict[str, Optional[Sequence[str]]]) -> List[FoundElement]:
        assert all(v is None or isinstance(v, (list, tuple)) for v in search_tags.values())
        import psycopg2

        self.create_materialized_views()

        results = []

        condition = ' AND '.join(
            (f"tags->'{tag}' IN ({self._values_str(values)})" if values else f"tags ? '{tag}'")
            for tag, values in search_tags.items()
        )
        query = f"""
            SELECT
                osm_id,
                osm_type,
                lon,
                lat,
                ST_AsText(way) AS way,
                hstore_to_json(tags) AS tags 
            FROM planet_osm_data_{self._suffix} 
            WHERE {condition}
        """

        with psycopg2.connect(**self._params) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                for osm_id, osm_type, lon, lat, way, tags in cur.fetchall():
                    results.append(FoundElement(osm_id, osm_type, lon, lat, way, tags))

        return results

    def _base_read(self, osm_ids: Iterable[int], tables: Iterable[str]) -> Dict[int, dict]:
        import psycopg2

        osm_ids_str = ', '.join(str(osm_id) for osm_id in osm_ids)
        queries = []
        for table in tables:
            query = f"""
                SELECT
                    0 AS changeset,  -- TODO
                    ABS(osm_id) AS id,
                    hstore_to_json(tags) AS tag,
                    '2030-01-01T00:00:00'::timestamp AS timestamp,  -- TODO
                    0 AS uid,  -- TODO
                    '' AS user,  -- TODO
                    0 AS version,  -- TODO
                    TRUE AS visible,
                    way AS way
                FROM {table}
                WHERE osm_id IN ({osm_ids_str})
            """
            queries.append(query)
        query = f"""
            SELECT 
                MAX(changeset) AS changeset, 
                id AS id,
                (array_agg(tag))[1] AS tag,
                MAX(timestamp) AS timestamp,
                MAX(uid) AS uid,
                MAX(user) AS user,
                MAX(version) AS version,
                bool_and(visible) AS visible,
                ST_X(ST_Centroid(ST_Union(way))) AS lon,
                ST_Y(ST_Centroid(ST_Union(way))) AS lat,
                ST_AsText(ST_Union(way)) AS way,
                ST_AsGeoJSON(ST_Union(way))::json AS geometry
            FROM ({' UNION ALL '.join(queries)}) t 
            GROUP BY id
        """
        columns = ['changeset', 'id', 'tag', 'timestamp', 'uid', 'user', 'version', 'visible', 'lon', 'lat', 'way', 'geometry']
        result = {}

        with psycopg2.connect(**self._params) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                for record in cur.fetchall():
                    data = dict(zip(columns, record))
                    result[data['id']] = data

        return result

    def read_nodes(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        result = {}
        for osm_ids_chunk in _split_chunks(tuple(osm_ids), 100000):
            result.update(self._base_read(osm_ids_chunk, ['planet_osm_point']))
        return result

    def read_ways(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        result = {}
        for osm_ids_chunk in _split_chunks(tuple(osm_ids), 100000):
            result.update(self._base_read(osm_ids_chunk, ['planet_osm_line', 'planet_osm_roads', 'planet_osm_polygon']))
        return result

    def read_relations(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        result = {}
        for osm_ids_chunk in _split_chunks(tuple(osm_ids), 100000):
            result.update(self._base_read(
                (-osm_id for osm_id in osm_ids_chunk),
                ['planet_osm_line', 'planet_osm_roads', 'planet_osm_polygon'],
            ))
        return result


class OverpassApiSearchEnigne(BaseSearchReadWriteEngine):
    AREA_WAY_INC = 2400000000
    AREA_REL_INC = 3600000000

    def __init__(self, region: int = -59065, timeout: int = 300, cache: bool = False):
        self._region = region
        self._timeout = timeout
        self._cache = cache

    @property
    def _area_region(self):
        return (self.AREA_REL_INC - self._region) if self._region < 0 else (self.AREA_WAY_INC + self._region)

    def _osm_to_geometry(self, osm_type, osm_id, type_id_elements):
        element = type_id_elements.get((osm_type, osm_id))
        if element is None:
            return None
        if element['type'] == 'node':
            return shapely.geometry.Point(element['lon'], element['lat'])
        if element['type'] == 'way' and len(element['nodes']) > 1:
            return shapely.geometry.LineString([
                (type_id_elements[('node', n)]['lon'], type_id_elements[('node', n)]['lat'])
                for n in element['nodes']
            ])
        if element['type'] == 'relation':
            lines = []
            geoms = []
            all_filter = all(
                member['role'] in {'spring', 'tributary', 'riverbank', 'waterbody'}
                for member in element['members']
            )
            for member in element['members']:
                if not all_filter and member['role'] in {'spring', 'tributary', 'riverbank', 'waterbody'}:
                    continue
                geom = self._osm_to_geometry(member['type'], member['ref'], type_id_elements)
                if geom is not None:
                    if geom.type == 'LineString':
                        lines.append(geom)
                    if geom.type == 'MultiLineString':
                        lines.extend(geom.geoms)
                    geoms.append(geom)
            if lines:
                geoms.append(shapely.ops.linemerge(lines))
                # geoms.extend(shapely.ops.polygonize(lines))
            geoms = [shapely.validation.make_valid(geom) for geom in geoms]
            return shapely.ops.unary_union([geom for geom in geoms if geom.is_valid])
        return None

    def _generate_queries(self, query, suffix, tags_values):
        if not tags_values:
            yield f'{query}{suffix}'
            return
        (tag, values), *tags_values_left = tags_values
        if not values:
            yield from self._generate_queries(f'{query}["{tag}"]', suffix, tags_values_left)
        else:
            for value in values:
                escaped_value = (
                    value
                    .replace('\\', '\\\\')
                    .replace('"', '\\"')
                    .replace('\n', '\\n')
                    .replace('\t', '\\t')
                )
                yield from self._generate_queries(f'{query}["{tag}"="{escaped_value}"]', suffix, tags_values_left)

    @functools.cache
    def _get_latest_update(self) -> str:
        import requests

        response = requests.get('http://download.geofabrik.de/europe/belarus-updates/state.txt')
        response.raise_for_status()
        return response.text.splitlines()[1][len('timestamp='):].replace('\\', '')

    def _request(self, query: str, cache_params: Optional[List[str]] = None) -> str:
        import requests

        cache = None
        if self._cache is not None and cache_params:
            cache_params_str = '-'.join(str(part) for part in cache_params)
            cache = f'/tmp/overpass-{cache_params_str}.txt'
            if os.path.exists(cache):
                with open(cache) as h:
                    return h.read()

        encoded_query = urllib.parse.quote(query.encode('utf-8'), safe='~()*!.\'')
        for retry_delay in [5, 30, 120, None]:
            try:
                response = requests.post(
                    'https://overpass-api.de/api/interpreter/',
                    data=f'data={encoded_query}',
                    headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'},
                )
                response.raise_for_status()
                if cache is not None:
                    with open(cache, 'w') as h:
                        h.write(response.text)
                return response.text
            except Exception as err:
                if retry_delay is not None:
                    time.sleep(retry_delay)
                else:
                    raise err

    def _build_geometries(
            self,
            elements: Sequence[dict],
            type_id_elements: Dict[Tuple[str, int], dict],
    ) -> List[FoundElement]:
        results = []
        for element in elements:
            osm_id = element['id']
            osm_type = element['type']
            geom = self._osm_to_geometry(osm_type, osm_id, type_id_elements)
            center = geom.centroid
            results.append(FoundElement(
                osm_id, osm_type, center.x, center.y, shapely.wkt.dumps(geom), element.get('tags', {}),
            ))

        return results

    def search(self, search_tags: Dict[str, Optional[Sequence[str]]]) -> List[FoundElement]:
        assert all(v is None or isinstance(v, (list, tuple)) for v in search_tags.values())

        query_parts = '\n'.join(self._generate_queries('nwr', '(area.b);', list(search_tags.items())))
        query = f"""
            [out:json][timeout:{self._timeout}];
            (
              area({self._area_region})->.b;
              {query_parts}
            );
            out body;
            >;
            out skel qt;
        """
        cache_params = [
            str(self._area_region),
            self._get_latest_update(),
            *(str(v) for k, vv in search_tags.items() for v in chain([k], vv))
        ]
        overpass_json = json.loads(self._request(query, cache_params))
        type_id_elements = {(e['type'], e['id']): e for e in overpass_json['elements']}
        elements = [e for e in type_id_elements.values() if self._match_tags(search_tags, e.get('tags', {}))]
        return self._build_geometries(elements, type_id_elements)

    def get_updates(self) -> List[FoundElement]:
        date_from_iso = self._get_latest_update()
        date_from = datetime.datetime.fromisoformat(date_from_iso[:-1])
        date_to = datetime.datetime.utcnow()
        delta = datetime.timedelta(hours=1)

        date_from_step = date_from
        date_to_step = date_from_step + delta
        type_id_elements = {}
        while date_from_step < date_to:
            date_from_step_iso = date_from_step.isoformat().split('.')[0] + 'Z'
            date_to_step_iso = date_to_step.isoformat().split('.')[0] + 'Z'
            query = f"""
                [out:json][timeout:{self._timeout}];
                (
                  area({self._area_region})->.b;
                  nwr(area.b)(changed:"{date_from_step_iso}","{date_to_step_iso}");
                );
                out meta;
                >;
                out skel qt;
            """
            if date_to_step < date_to:
                cache_params = [str(self._area_region), date_from_step_iso, date_to_step_iso]
            else:
                cache_params = None
            overpass_json = json.loads(self._request(query, cache_params))
            for e in overpass_json['elements']:
                type_id_elements[(e['type'], e['id'])] = e
            date_from_step = date_to_step
            date_to_step = date_to_step + delta

        elements = [e for e in type_id_elements.values() if 'timestamp' in e and e['timestamp'] >= date_from_iso]
        return self._build_geometries(elements, type_id_elements)

    def get_updates_osc(self, latest_node_id: int, latest_way_id: int, latest_relation_id: int) -> str:
        date_from_iso = self._get_latest_update()
        date_from = datetime.datetime.fromisoformat(date_from_iso[:-1])
        date_to = datetime.datetime.utcnow()
        delta = datetime.timedelta(hours=1)

        date_from_step = date_from
        date_to_step = date_from_step + delta
        type_id_elements = {}
        while date_from_step < date_to:
            date_from_step_iso = date_from_step.isoformat().split('.')[0] + 'Z'
            date_to_step_iso = date_to_step.isoformat().split('.')[0] + 'Z'
            query = f"""
                [out:json][timeout:{self._timeout}];
                (
                  area({self._area_region})->.b;
                  nwr(area.b)(changed:"{date_from_step_iso}","{date_to_step_iso}");
                );
                out meta;
                >;
                out skel qt;
            """
            if date_to_step < date_to:
                cache_params = [str(self._area_region), date_from_step_iso, date_to_step_iso]
            else:
                cache_params = None
            overpass_json = json.loads(self._request(query, cache_params))
            for e in overpass_json['elements']:
                type_id_elements[(e['type'], e['id'])] = e
            date_from_step = date_to_step
            date_to_step = date_to_step + delta

        def build(elements):
            yield '<?xml version="1.0" encoding="UTF-8"?>'
            yield '<osmChange version="0.6" generator="migration belarus">'
            yield '<modify>'
            for e in type_id_elements.values():
                try:
                    if e['type'] == 'node':
                        latest_id = latest_node_id
                    elif e['type'] == 'way':
                        latest_id = latest_way_id
                    elif e['type'] == 'relation':
                        latest_id = latest_relation_id
                    else:
                        continue
                    if 'version' not in e and e['id'] <= latest_id:
                        continue
                    osm_id = e['id']
                    version = e.get('version', 1)
                    timestamp = e.get('timestamp', '2025-01-01T00:00:00Z')
                    changeset = e.get('changeset', 1)
                    uid = e.get('uid', 1)
                    user = e.get('user', '')
                    if e['type'] == 'node' and not e.get('tags'):
                        lat = e['lat']
                        lon = e['lon']
                        yield (
                            f'  <node id="{osm_id}" lat="{lat}" lon="{lon}" visible="true" version="{version}" '
                            f'timestamp="{timestamp}" changeset="{changeset}" uid="{uid}" user={quoteattr(user)}/>'
                        )
                    elif e['type'] == 'node':
                        lat = e['lat']
                        lon = e['lon']
                        yield (
                            f'  <node id="{osm_id}" lat="{lat}" lon="{lon}" visible="true" version="{version}" '
                            f'timestamp="{timestamp}" changeset="{changeset}" uid="{uid}" user={quoteattr(user)}>'
                        )
                        for k, v in e.get('tags', {}).items():
                            yield f'    <tag k={quoteattr(k)} v={quoteattr(v)}/>'
                        yield f'  </node>'
                    elif e['type'] == 'way':
                        yield (
                            f'  <way id="{osm_id}" visible="true" version="{version}" '
                            f'timestamp="{timestamp}" changeset="{changeset}" uid="{uid}" user={quoteattr(user)}>'
                        )
                        for n in e['nodes']:
                            yield f'    <nd ref="{n}"/>'
                        for k, v in e.get('tags', {}).items():
                            yield f'    <tag k={quoteattr(k)} v={quoteattr(v)}/>'
                        yield f'  </way>'
                    elif e['type'] == 'relation':
                        yield (
                            f'  <relation id="{osm_id}" visible="true" version="{version}" '
                            f'timestamp="{timestamp}" changeset="{changeset}" uid="{uid}" user={quoteattr(user)}>'
                        )
                        for m in e['members']:
                            type_ = m['type']
                            ref = m['ref']
                            role = m['role']
                            yield f'    <member type="{type_}" ref="{ref}" role={quoteattr(role)}/>'
                        for k, v in e.get('tags', {}).items():
                            yield f'    <tag k={quoteattr(k)} v={quoteattr(v)}/>'
                        yield f'  </relation>'
                except Exception:
                    raise ValueError(e)
            yield '</modify>'
            yield '</osmChange>'
        return '\n'.join(build(type_id_elements.values()))


class OsmApiReadWriteEngine(BaseSearchReadWriteEngine):
    def __init__(self, username, password, dry_run=False):
        import osmapi

        self._api = osmapi.OsmApi(username=username, password=password)
        self._dry_run = False

    def read_nodes(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        result = {}
        for osm_ids_chunk in _split_chunks(tuple(osm_ids), self.MAX_READ_CHUNK):
            result.update(self._api.NodesGet(osm_ids_chunk))
        return result

    def read_ways(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        result = {}
        for osm_ids_chunk in _split_chunks(tuple(osm_ids), self.MAX_READ_CHUNK):
            result.update(self._api.WaysGet(osm_ids_chunk))
        return result

    def read_relations(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        result = {}
        for osm_ids_chunk in _split_chunks(tuple(osm_ids), self.MAX_READ_CHUNK):
            result.update(self._api.RelationsGet(osm_ids_chunk))
        return result

    def write(self, changes: Sequence[ElementChanges]) -> List[int]:
        group_changes_map = defaultdict(list)
        group_comments_map = defaultdict(set)
        for change in changes:
            group_changes_map[change.changes[0].comment].append(change)
            group_comments_map[change.changes[0].comment] |= {element.comment for element in change.changes}

        changesets = []
        for group, group_changes in group_changes_map.items():
            comment = '; '.join(sorted(group_comments_map[group]))
            chunks = math.ceil(len(group_changes) / self.MAX_WRITE_CHUNK)

            changes_data = [
                {
                    'action': 'modify',
                    'type': change.osm_type,
                    'data': change.data,
                }
                for change in group_changes
                if change.changes
            ]

            for i, changes_data_chunk in enumerate(_split_chunks(changes_data, self.MAX_WRITE_CHUNK), 1):
                if self._dry_run:
                    continue
                self._api.ChangesetCreate({'comment': f'{comment} ({i} of {chunks})'})
                self._api.ChangesetUpload(changes_data_chunk)
                changeset = self._api.ChangesetClose()
                changesets.append(changeset)
        return changesets


class GeoJsonWriteEngine(BaseSearchReadWriteEngine):
    def __init__(self, postgis_search_engine: PostgisSearchReadEngine, out_dir: str):
        self._out_dir = out_dir
        self._postgis_search_engine = postgis_search_engine

    def write(self, changes: Sequence[ElementChanges]) -> List[int]:
        os.makedirs(self._out_dir, exist_ok=True)

        node_ids = [change.osm_id for change in changes if change.osm_type == 'node']
        way_ids = [change.osm_id for change in changes if change.osm_type == 'way']
        rel_ids = [change.osm_id for change in changes if change.osm_type == 'relation']

        node_geoms = self._postgis_search_engine.read_nodes(node_ids)
        way_geoms = self._postgis_search_engine.read_ways(way_ids)
        rel_geoms = self._postgis_search_engine.read_relations(rel_ids)
        type_geoms = {
            'node': node_geoms,
            'way': way_geoms,
            'relation': rel_geoms,
        }

        group_changes_map = defaultdict(list)
        group_comments_map = defaultdict(set)
        for change in changes:
            group_main = '; '.join(sorted({
                element.comment for element in change.changes if ' - ' not in element.comment
            }))
            group_dep = '; '.join(sorted({
                element.comment.split(' - ')[-1] for element in change.changes if ' - ' in element.comment
            }))
            if group_main:
                group_changes_map[group_main].append(change)
                group_comments_map[group_main] |= {element.comment for element in change.changes}
            elif ';' not in group_dep:
                group_changes_map[group_dep].append(change)
                group_comments_map[group_dep] |= {element.comment for element in change.changes}
            else:
                group_changes_map['other'].append(change)
                group_comments_map['other'] |= {element.comment for element in change.changes}

        for group, group_changes in group_changes_map.items():
            comment = '; '.join(sorted(group_comments_map[group]))
            chunks = math.ceil(len(group_changes) / self.MAX_WRITE_CHUNK)
            result = {
                'type': 'FeatureCollection',
                'features': [
                    {
                        'type': 'Feature',
                        'geometry': type_geoms[change.osm_type][change.osm_id]['geometry'],
                        'properties': {
                            'comment': f'{comment} ({i} of {chunks})',
                            'osm_type': change.osm_type,
                            'osm_id': change.osm_id,
                            'url': change.osm_url,
                            'tags': {
                                element.update_tag: {
                                    'from': element.value_from,
                                    'to': element.value_to,
                                }
                                for element in change.changes
                            },
                        },
                    }
                    for i, changes_group_chunk in enumerate(_split_chunks(group_changes, self.MAX_WRITE_CHUNK), 1)
                    for change in changes_group_chunk
                ],
            }
            filename = (
                f'{self._out_dir}/{group}-{len(group_changes)}.geojson'
                .replace(':', '_')
                .replace(' - ', '_')
                .replace(' ', '_')
            )
            with open(filename, 'w') as handle:
                json.dump(result, handle, ensure_ascii=False, separators=(',', ':'))

        return []


class OsmChangeWriteEngine(BaseSearchReadWriteEngine):
    """
        osmium apply-changes -o belarus-result.osm.pbf belarus-latest.osm.pbf belarus-result.osc
    """

    def __init__(self, out: str, changeset_id: str = 999999999, creaeted_by: str = 'belarus migration script'):
        self._out = out

        self._created_by = creaeted_by
        self._CurrentChangesetId = changeset_id

    def write(self, changes: Sequence[ElementChanges]) -> List[int]:
        from osmapi import xmlbuilder

        changes_data = [
            {
                'action': 'modify',
                'type': change.osm_type,
                'data': change.data,
            }
            for change in changes
            if change.changes
        ]

        data = ""
        data += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        data += "<osmChange version=\"0.6\" generator=\""
        data += "migration belarus" + "\">\n"
        for change in changes_data:
            data += "<" + change["action"] + ">\n"
            change["data"]["changeset"] = self._CurrentChangesetId
            data += xmlbuilder._XmlBuild(
                change["type"],
                change["data"],
                False,
                data=self
            ).decode("utf-8")
            data += "</" + change["action"] + ">\n"
        data += "</osmChange>"

        with open(self._out, 'w') as handle:
            handle.write(data)

        return []


class PrintIssuesEngine(BaseSearchReadWriteEngine):
    def report_issue(self, issue: Issue):
        print(issue)
        # groups = defaultdict(list)
        # for issue in issues:
        #     groups[issue.message].append(issue)
        # for group, group_issues in groups.items():
        #     print(group)
        #     for issue in group_issues:
        #         print(issue.changes)


class TestEngine(BaseSearchReadWriteEngine):
    def __init__(self, elements: Dict[Tuple[int, str], dict]):
        self.elements = elements

    def search(self, search_tags: Dict[str, Optional[Sequence[str]]]) -> List[FoundElement]:
        results = []
        for (osm_id, osm_type), element in self.elements.items():
            if self._match_tags(search_tags, element['tag']):
                results.append(FoundElement(osm_id, osm_type, None, None, None, element['tag']))
        return results

    def _base_read(self, osm_ids: Iterable[int], osm_type: str) -> Dict[int, dict]:
        return {
            element_osm_id: element
            for (element_osm_id, element_osm_type), element in self.elements.items()
            if element_osm_type == osm_type
            and element_osm_id in osm_ids
        }

    def read_nodes(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        return self._base_read(osm_ids, 'node')

    def read_ways(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        return self._base_read(osm_ids, 'way')

    def read_relations(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        return self._base_read(osm_ids, 'relation')

    def write(self, changes: Sequence[ElementChanges]) -> List[int]:
        for change in changes:
            self.elements[(change.osm_id, change.osm_type)] = change.data
        return []

    def report_issue(self, issue: Issue):
        raise AssertionError(issue)


class PostgisTestEngine(PostgisSearchReadEngine):
    def __init__(self, region=-59065, **params):
        super().__init__(region=region, **params)
        # self.original_data = {}
        self.changed_data = {}

    def search(self, search_tags: Dict[str, Optional[Sequence[str]]]) -> List[FoundElement]:
        results = []
        processed = set()

        for found_element in super().search(search_tags):
            changed_element_data = self.changed_data.get((found_element.osm_id, found_element.osm_type))
            if changed_element_data is not None:
                if self._match_tags(search_tags, changed_element_data['tag']):
                    results.append(FoundElement(
                        found_element.osm_id,
                        found_element.osm_type,
                        found_element.lon,
                        found_element.lat,
                        found_element.way,
                        changed_element_data['tag'].copy(),
                    ))
                    processed.add((found_element.osm_id, found_element.osm_type))
            else:
                results.append(found_element)

        for (osm_id, osm_type), data in self.changed_data.items():
            if (osm_id, osm_type) in processed:
                continue
            if self._match_tags(search_tags, data['tag']):
                results.append(FoundElement(
                    osm_id,
                    osm_type,
                    data['lon'],
                    data['lat'],
                    data['way'],
                    data['tag'].copy(),
                ))

        return results

    def _copy(self, data: dict) -> dict:
        data = data.copy()
        data['tag'] = data['tag'].copy()
        return data

    def read_nodes(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        return {
            osm_id: self._copy(self.changed_data.get((osm_id, 'node'), data))
            for osm_id, data in super().read_nodes(osm_ids).items()
        }

    def read_ways(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        return {
            osm_id: self._copy(self.changed_data.get((osm_id, 'way'), data))
            for osm_id, data in super().read_ways(osm_ids).items()
        }

    def read_relations(self, osm_ids: Iterable[int]) -> Dict[int, dict]:
        return {
            osm_id: self._copy(self.changed_data.get((osm_id, 'relation'), data))
            for osm_id, data in super().read_relations(osm_ids).items()
        }

    def write(self, changes: Sequence[ElementChanges]) -> List[int]:
        for change in changes:
            self.changed_data[(change.osm_id, change.osm_type)] = change.data
        return []