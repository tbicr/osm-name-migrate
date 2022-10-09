import csv
import datetime
import html
import io
import os
from collections import defaultdict
from urllib.parse import urlencode

import github
import psycopg2

import pandas as pd
import shapely.wkt
import shapely.strtree
from jinja2 import Template

from belarus_upd import Engine
from belarus_utils import (
    PostgisSearchReadEngine, OverpassApiSearchEnigne, OsmApiReadWriteEngine, PrintIssuesEngine,
    CYRILIC_REGEXP, ElementRuleChange,
)

POSTGRES_HOST = os.environ['POSTGRES_HOST']
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', 5432)
POSTGRES_DB = os.environ['POSTGRES_DB']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
OSM2PGSQL_CACHE = os.environ['OSM2PGSQL_CACHE']
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
REPORT_OUTPUT_API = bool(int(os.environ['REPORT_OUTPUT_API']))
AUTOFIX_OSM = bool(int(os.environ['AUTOFIX_OSM']))

REPO_NAME = 'tbicr/osm-name-migrate'
REPO = f'https://github.com/{REPO_NAME}'
SKIP_CSV_COLUMNS = {'be=ru', 'be+ru', 'ru+be', 'be'}
FLOAT_FORMAT = '{:.3f}'.format
TABLE_ATTRS = 'class="table table-sm table-hover caption-top"'
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', FLOAT_FORMAT)

# define rules
CATEGORIES_RULES = {
    'admin': [
        ['admin_level', '2'],
        ['admin_level', '4'],
        ['admin_level', '6'],
        ['admin_level', '8'],
        ['admin_level', '9'],
    ],
    'place': [
        ['place', 'city'],
        ['place', 'town'],
        ['place', 'village'],
        ['place', 'hamlet'],
        ['place', 'isolated_dwelling'],
        ['admin_level', None],
        ['boundary', 'administrative'],
        ['traffic_sign', 'city_limit'],
    ],
    'allotments': [
        ['place', 'allotments'],
        ['landuse', 'allotments'],
    ],
    'locality': [
        ['place', 'locality'],
        ['abandoned:place', None],
    ],
    'suburb': [
        ['landuse', 'cemetery'],
        ['landuse', 'commercial'],
        ['landuse', 'construction'],
        ['landuse', 'farmland'],
        ['landuse', 'farmyard'],
        ['landuse', 'industrial'],
        ['landuse', 'residential'],
        ['landuse', 'retail'],
        ['place', None],
        ['residential', None],
        ['industrial', None],
        ['landuse', None],
    ],
    'natural': [
        ['boundary', None],
        ['natural', None],
        ['place', 'island'],
        ['place', 'islet'],
        ['ele', None],
        ['landuse', 'forest'],
    ],
    'water': [
        ['tunnel', None],
        ['waterway', 'drain'],
        ['waterway', 'ditch'],
        ['waterway', 'stream'],
        ['waterway', 'river'],
        ['waterway', 'canal'],
        ['waterway', None],
        ['type', 'waterway'],
        ['water', None],
        ['natural', 'water'],
        ['natural', 'spring'],
    ],
    'highway': [
        ['highway', 'motorway'],
        ['highway', 'trunk'],
        ['highway', 'primary'],
        ['highway', 'secondary'],
        ['highway', 'tertiary'],
        ['highway', 'unclassified'],
        ['highway', 'residential'],
        ['highway', 'service'],
        ['highway', 'track'],
        ['highway', None],
        ['type', 'associatedStreet'],
        ['type', 'street'],
        ['bridge', None],
    ],
    'public_transport': [
        ['highway', 'bus_stop'],
        ['public_transport', None],
        ['route', None],
        ['type', 'route'],
        ['railway', None],
        ['type', 'route_master'],
        ['route_master', None],
    ],
    'infrastructure': [
        ['barrier', None],
        ['power', None],
        ['substation', None],
        ['man_made', None],
        ['embankment', None],
        ['amenity', 'fuel'],
    ],
    'religion': [
        ['religion', None],
        ['amenity', 'place_of_worship'],
        ['amenity', 'monastery'],
        ['building', 'church'],
        ['building', 'cathedral'],
        ['building', 'chapel'],
    ],
    'education': [
        ['landuse', 'education'],
        ['amenity', 'university'],
        ['amenity', 'college'],
        ['amenity', 'school'],
        ['amenity', 'kindergarten'],
        ['building', 'university'],
        ['building', 'college'],
        ['building', 'school'],
        ['building', 'kindergarten'],
    ],
    'healthcare': [
        ['emergency', None],
        ['healthcare', None],
        ['amenity', 'hospital'],
        ['amenity', 'pharmacy'],
        ['amenity', 'clinic'],
        ['amenity', 'doctors'],
        ['amenity', 'dentist'],
        ['building', 'hospital'],
        ['building', 'clinic'],
    ],
    'government': [
        ['amenity', 'post_office'],
        ['amenity', 'police'],
        ['amenity', 'library'],
        ['office', 'government'],
        ['government', None],
        ['landuse', 'military'],
        ['military', None],
    ],
    'bank': [
        ['amenity', 'atm'],
        ['amenity', 'bank'],
    ],
    'office': [
        ['office', None],
    ],
    'tourism': [
        ['tourism', None],
        ['historic', None],
        ['memorial', None],
        ['ruins', None],
        ['information', None],
        ['attraction', None],
        ['resort', None],
        ['artwork_type', None],
    ],
    'amenity': [
        ['amenity', 'cafe'],
        ['amenity', 'fast_food'],
        ['amenity', 'community_centre'],
        ['amenity', 'restaurant'],
        ['amenity', 'bar'],
        ['amenity', None],
        ['shop', 'convenience'],
        ['shop', 'clothes'],
        ['shop', 'car_repair'],
        ['shop', 'hairdresser'],
        ['shop', 'chemist'],
        ['shop', 'supermarket'],
        ['shop', 'car_parts'],
        ['shop', 'furniture'],
        ['shop', 'hardware'],
        ['shop', 'kiosk'],
        ['shop', 'doityourself'],
        ['shop', 'pet'],
        ['shop', 'florist'],
        ['shop', 'beauty'],
        ['shop', 'mobile_phone'],
        ['shop', 'shoes'],
        ['shop', 'newsagent'],
        ['shop', 'electronics'],
        ['shop', 'alcohol'],
        ['shop', 'jewelry'],
        ['shop', 'mall'],
        ['shop', 'butcher'],
        ['shop', 'cosmetics'],
        ['shop', None],
        ['leisure', None],
        ['sport', None],
        ['craft', 'shoemaker'],
        ['clothes', None],
    ],
    'building': [
        ['building', 'industrial'],
        ['building', 'service'],
        ['building', 'retail'],
        ['building', 'commercial'],
        ['building', 'warehouse'],
        ['building', 'public'],
        ['building', 'dormitory'],
        ['building', 'warehouse'],
        ['building', None],
    ],
}

DEPENDANTS = [
    'addr:region',
    'addr:district',
    'addr:subdistrict',
    'addr:city',
    'addr:place',
    'addr:street',
    'addr2:street',

    'from',
    'to',
    'via',
    'destination',
    'destination:backward',
    'destination:forward',

    'water_tank:city',
]


LANGUAGE_TAGS = [
    'name',
    'name:prefix',
    'was:name:prefix',
    'short_name',
    'official_name',
    'official_status',
    'official_short_type',
    'operator',
    'brand',
    'network',
    'description',
]


usage = defaultdict(set)
CATEGORIES_RULES2 = {}
for category, group in CATEGORIES_RULES.items():
    if category not in CATEGORIES_RULES2:
        CATEGORIES_RULES2[category] = []
    for tag, value in group:
        if value is not None:
            CATEGORIES_RULES2[category].append([tag, True, {value}])
            usage[tag].add(value)
for category, group in CATEGORIES_RULES.items():
    if category not in CATEGORIES_RULES2:
        CATEGORIES_RULES2[category] = []
    for tag, value in group:
        if value is None:
            CATEGORIES_RULES2[category].append([tag, False, usage[tag]])


tag_star_category = {}
tag_star_values = {}
for category, group in CATEGORIES_RULES.items():
    for tag, value in group:
        if value is None:
            tag_star_category[tag] = category
            tag_star_values[tag] = set()
for category, group in CATEGORIES_RULES.items():
    for tag, value in group:
        if value is not None:
            if tag in tag_star_category and category == tag_star_category[tag]:
                tag_star_values[tag].add(value)
OVERPASS_QUERIES = {}
for category, group in CATEGORIES_RULES2.items():
    conditions = []
    for k, eq, vv in group:
        if vv and eq and len(vv) == 1:
            tag = f'{k} = {list(vv)[0]}'
            condition = f'["{k}"="{list(vv)[0]}"]'
            if k in tag_star_category and tag_star_category[k] == category:
                category_condition = None
            else:
                category_condition = condition
        elif vv and not eq:
            tag = f'{k} = *'
            condition = f'["{k}"]' + ''.join(
                f'["{k}"!="{v}"]' for v in sorted(vv))
            category_condition = f'["{k}"]' + ''.join(
                f'["{k}"!="{v}"]' for v in sorted(vv) if v not in tag_star_values[k])
        elif not eq:
            tag = f'{k} = *'
            condition = f'["{k}"]'
            category_condition = condition
        else:
            raise ValueError()
        OVERPASS_QUERIES[f'{category} - {tag}'] = [condition]
        if category_condition:
            conditions.append(category_condition)
    OVERPASS_QUERIES[category] = conditions


def run_psql(command):
    os.system(
        f'PGPASSWORD={POSTGRES_PASSWORD} '
        f'psql -h {POSTGRES_HOST} -p {POSTGRES_PORT} -U {POSTGRES_USER} -d {POSTGRES_DB} -c "{command}"'
    )


print('load dump to postgis')
os.system('wget --backups=1 -N -nv https://download.geofabrik.de/europe/belarus-latest.osm.pbf')
run_psql('CREATE EXTENSION IF NOT EXISTS hstore')
run_psql('CREATE EXTENSION IF NOT EXISTS postgis')
run_psql('DROP MATERIALIZED VIEW IF EXISTS planet_osm_region CASCADE')
os.system(
    f'PGPASSWORD={POSTGRES_PASSWORD} '
    f'osm2pgsql -H {POSTGRES_HOST} -P {POSTGRES_PORT} -U {POSTGRES_USER} -d {POSTGRES_DB} '
    f'-v -l -j -G -x --hstore-add-index -C {OSM2PGSQL_CACHE} -S /usr/share/osm2pgsql/default.style '
    f'belarus-latest.osm.pbf'
)


postgres_params = {
    'host': POSTGRES_HOST,
    'port': POSTGRES_PORT,
    'dbname': POSTGRES_DB,
    'user': POSTGRES_USER,
    'password': POSTGRES_PASSWORD,
}

print('add complex relations that was not loaded to postgis')
postgis_api = PostgisSearchReadEngine(**postgres_params)
overpass_api = OverpassApiSearchEnigne(cache=False)

print('type = street')
postgis_api.insert_extra_relations(overpass_api.search({'type': ['street']}))

print('type = associatedStreet')
postgis_api.insert_extra_relations(overpass_api.search({'type': ['associatedStreet']}))

print('type = route')
postgis_api.insert_extra_relations(overpass_api.search({'type': ['route']}))

print('type = route_master')
postgis_api.insert_extra_relations(overpass_api.search({'type': ['route_master']}))

print('type = waterway')
postgis_api.insert_extra_relations(overpass_api.search({'type': ['waterway']}))

postgis_api.create_materialized_views()


def precalculate_field_data(lang_tag):
    lang_tag_sql = lang_tag.replace(':', '__')
    data_table = f'{postgis_api.data_table}_{lang_tag_sql}'
    OSM_DATA_VIEW_SQL = f"""
    CREATE MATERIALIZED VIEW IF NOT EXISTS {data_table} AS
    
    SELECT osm_type, osm_id, tags
    FROM {postgis_api.data_table}
    WHERE tags->'{lang_tag}' ~ '{CYRILIC_REGEXP}'
    """
    OSM_DATA_TAGS_INDEX_SQL = f"""
    CREATE INDEX IF NOT EXISTS "{data_table}_tags_idx" ON {data_table} USING GIN (tags)
    """
    OSM_DATA_ANALYZE_SQL = f"ANALYZE {data_table}"

    with psycopg2.connect(**postgres_params) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(OSM_DATA_VIEW_SQL)
            cur.execute(OSM_DATA_TAGS_INDEX_SQL)
            cur.execute(OSM_DATA_ANALYZE_SQL)

    return data_table


def get_stat_query(lang_tag, data_table):
    query_template = """
        SELECT DISTINCT
               osm_type,
               osm_id,
              '{category}' AS category,
               {num} AS num,
               tags->'{field}' AS value,
               tags->'{field}:be' AS value_be,
               tags->'{field}:ru' AS value_ru
        FROM {data_table}
        WHERE {condition}
    """

    exclude = defaultdict(lambda: [[], []])
    for category, group in CATEGORIES_RULES2.items():
        conditions = []
        for i, (k, eq, vv) in enumerate(group):
            if vv:
                eq_str = 'IN' if eq else 'NOT IN'
                vv_str = ','.join(f"'{v}'" for v in vv)
                condition = f"tags->'{k}' {eq_str} ({vv_str})"
            elif not eq:
                condition = f"tags->'{k}' IS NOT NULL"
            else:
                raise ValueError()
            conditions.append(condition)
            exclude[k][eq].append(condition)
            query = query_template.format(
                data_table=data_table, field=lang_tag, category=category, num=i,
                condition=condition, cyrilic_regexp=CYRILIC_REGEXP)
            yield query
        condition = ' OR '.join(f'({c})' for c in conditions)
        query = query_template.format(
            data_table=data_table, field=lang_tag, category=category, num=-1,
            condition=condition, cyrilic_regexp=CYRILIC_REGEXP)
        yield query
    condition = ' OR '.join(f"(tags->'{k}' IS NOT NULL)" for k, eq_c in exclude.items())
    query = query_template.format(
        data_table=data_table, field=lang_tag, category='other', num=-1,
        condition=f'NOT ({condition})', cyrilic_regexp=CYRILIC_REGEXP)
    yield query
    query = query_template.format(
        data_table=data_table, field=lang_tag, category='TOTAL', num=-1,
        condition='TRUE', cyrilic_regexp=CYRILIC_REGEXP)
    yield query


def get_df(lang_tag, data_table):
    data = []
    with psycopg2.connect(**postgres_params) as conn:
        with conn.cursor() as cur:
            for i, query in enumerate(get_stat_query(lang_tag, data_table), 1):
                cur.execute(query)
                records = cur.fetchall()
                for osm_type, osm_id, category, num, value, value_be, value_ru in records:
                    if value == value_be == value_ru:
                        progress = [1, 0, 0, 0, 0, 0, 0, 0, 0]  # be=ru
                    elif value == value_be and value_ru is not None:
                        progress = [0, 1, 0, 0, 0, 0, 0, 0, 0]  # be+ru
                    elif value == value_be:
                        progress = [0, 0, 1, 0, 0, 0, 0, 0, 0]  # be
                    elif value == value_ru and value_be is not None:
                        progress = [0, 0, 0, 1, 0, 0, 0, 0, 0]  # ru+be
                    elif value == value_ru:
                        progress = [0, 0, 0, 0, 1, 0, 0, 0, 0]  # ru
                    elif value_be is not None and value_ru is not None:
                        progress = [0, 0, 0, 0, 0, 1, 0, 0, 0]  # other both
                    elif value_be is not None:
                        progress = [0, 0, 0, 0, 0, 0, 1, 0, 0]  # other be
                    elif value_ru is not None:
                        progress = [0, 0, 0, 0, 0, 0, 0, 1, 0]  # other ru
                    else:
                        progress = [0, 0, 0, 0, 0, 0, 0, 0, 1]  # no lang
                    data.append([
                        category, num, osm_type, osm_id, value, value_be, value_ru, *(bool(v) for v in progress)
                    ])
    return pd.DataFrame(data, columns=[
        'category', 'num', 'osm_type', 'osm_id', lang_tag, f'{lang_tag}:be', f'{lang_tag}:ru',
        'be=ru', 'be+ru', 'be', 'ru+be', 'ru',
        'other_both', 'other_be', 'other_ru', 'no_lang',
    ]).sort_values(by=['category', 'num', lang_tag, f'{lang_tag}:be', f'{lang_tag}:ru', 'osm_type', 'osm_id'])


def get_overpass_link(lang_tag, category, tag, column):
    if tag is None:
        parts = OVERPASS_QUERIES[category]
    else:
        parts = OVERPASS_QUERIES[f'{category} - {tag}']
    base = f'nwr["{lang_tag}"]["{lang_tag}"!~"^[0123456789]+$"]'
    if column == 'be=ru':
        parts = [(
            f'{base}["{lang_tag}:be"]["{lang_tag}:ru"]{part}(area.b)'
            f'(if: t["{lang_tag}"] == t["{lang_tag}:be"] && t["{lang_tag}"] == t["{lang_tag}:ru"]);'
        ) for part in parts]
    elif column == 'be+ru':
        parts = [(
            f'{base}["{lang_tag}:be"]["{lang_tag}:ru"]{part}(area.b)'
            f'(if: t["{lang_tag}"] == t["{lang_tag}:be"] && t["{lang_tag}"] != t["{lang_tag}:ru"]);'
        ) for part in parts]
    elif column == 'ru+be':
        parts = [(
            f'{base}["{lang_tag}:be"]["{lang_tag}:ru"]{part}(area.b)'
            f'(if: t["{lang_tag}"] != t["{lang_tag}:be"] && t["{lang_tag}"] == t["{lang_tag}:ru"]);'
        ) for part in parts]
    elif column == 'be':
        parts = [(
            f'{base}["{lang_tag}:be"][!"{lang_tag}:ru"]{part}(area.b)'
            f'(if: t["{lang_tag}"] == t["{lang_tag}:be"]);'
        ) for part in parts]
    elif column == 'ru':
        parts = [(
            f'{base}[!"{lang_tag}:be"]["{lang_tag}:ru"]{part}(area.b)'
            f'(if: t["{lang_tag}"] == t["{lang_tag}:ru"]);'
        ) for part in parts]
    elif column == 'other_both':
        parts = [(
            f'{base}["{lang_tag}:be"]["{lang_tag}:ru"]{part}(area.b)'
            f'(if: t["{lang_tag}"] != t["{lang_tag}:be"] && t["{lang_tag}"] != t["{lang_tag}:ru"]);'
        ) for part in parts]
    elif column == 'other_be':
        parts = [(
            f'{base}["{lang_tag}:be"][!"{lang_tag}:ru"]{part}(area.b)'
            f'(if: t["{lang_tag}"] != t["{lang_tag}:be"]);'
        ) for part in parts]
    elif column == 'other_ru':
        parts = [(
            f'{base}[!"{lang_tag}:be"]["{lang_tag}:ru"]{part}(area.b)'
            f'(if: t["{lang_tag}"] != t["{lang_tag}:ru"]);'
        ) for part in parts]
    elif column == 'no_lang':
        parts = [(
            f'{base}[!"{lang_tag}:be"][!"{lang_tag}:ru"]{part}(area.b);'
        ) for part in parts]
    parts_str = '\n          '.join(parts)
    query = f"""
        // tag: {lang_tag}
        // category: {category}
        // condition: {tag or '*'}
        // column: {column} 
        [out:json][timeout:300];
        (
          area["admin_level"="2"]["name"="Беларусь"]->.b;
          {parts_str}
        );
        out body;
        >;
        out skel qt;
    """.replace(' ' * 8, '').strip()

    return 'https://overpass-turbo.eu?' + urlencode({'Q': query})


def a_tag(link, name):
    return f"<a href='{link}' target='_blank'>{name}</a>"


def wrap_hint_progress(lang_tag, category, tag, column, value):
    if category == 'TOTAL':
        return value

    csv_link = None
    if should_create_csv(lang_tag, category, tag, column):
        if tag is None or category == 'other':
            csv_link = f'{REPO}/blob/main/data/{lang_tag}/{category}/{column}.csv'
        else:
            csv_link = f'{REPO}/blob/main/data/{lang_tag}/{category} - {tag}/{column}.csv'

    overpass_link = None
    if category != 'other':
        overpass_link = get_overpass_link(lang_tag, category, tag, column)

    if csv_link and overpass_link:
        title = f"{a_tag(csv_link, 'CSV')} or {a_tag(overpass_link, 'overpass')}"
    elif csv_link:
        title = a_tag(csv_link, 'CSV')
    elif overpass_link:
        title = a_tag(overpass_link, 'overpass')
    else:
        return value

    classes = 'text-decoration-none text-reset'
    return f'<a href="##" class="{classes}" data-bs-toggle="tooltip" data-bs-html="true" title="{title}">{value}</a>'


def wrap_hint_dependant_progress(category, column, value):
    if not should_create_csv('name', category, None, column):
        return value
    csv_link = f'{REPO}/blob/main/data/name/{category}/{column}.csv'
    title = a_tag(csv_link, 'CSV')
    classes = 'text-decoration-none text-reset'
    return f'<a href="##" class="{classes}" data-bs-toggle="tooltip" data-bs-html="true" title="{title}">{value}</a>'


def should_create_csv(lang_tag, category, tag, column):
    if lang_tag != 'name':
        return False
    if category in CATEGORIES_RULES and tag is None:
        return False
    if category in {'TOTAL', 'amenity', 'building'}:
        return False
    if column in SKIP_CSV_COLUMNS:
        return False
    return True


def statistic_report(lang_tag, df):
    report_data = []
    for c in list(CATEGORIES_RULES) + ['other', 'TOTAL']:
        raw_df = df[(df['category'] == c) & (df['num'] == -1)]

        field_df = raw_df[raw_df[lang_tag].notnull()]
        field_be_df = raw_df[raw_df[f'{lang_tag}:be'].notnull()]
        field_ru_df = raw_df[raw_df[f'{lang_tag}:ru'].notnull()]

        field_cnt = field_df[lang_tag].count()
        field_uniq = field_df[lang_tag].value_counts().count()
        field_be_cnt = field_be_df[f'{lang_tag}:be'].count()
        field_be_uniq = field_be_df[f'{lang_tag}:be'].value_counts().count()
        field_ru_cnt = field_ru_df[f'{lang_tag}:ru'].count()
        field_ru_uniq = field_ru_df[f'{lang_tag}:ru'].value_counts().count()

        report_data.append([
            '#', c,
            field_cnt, field_be_cnt, field_ru_cnt,
            field_be_cnt / (field_cnt or 1), field_ru_cnt / (field_cnt or 1),
            field_uniq, field_be_uniq, field_ru_uniq,
            field_be_uniq / (field_uniq or 1), field_ru_uniq / (field_uniq or 1),
        ])
        if c in {'other', 'TOTAL'}:
            continue
        for i, (k, eq, vv) in enumerate(CATEGORIES_RULES2[c]):
            if eq:
                tag = f'{k} = {list(vv)[0]}'
            else:
                tag = f'{k} = *'
            raw_df = df[(df['category'] == c) & (df['num'] == i)]

            field_df = raw_df[raw_df[lang_tag].notnull()]
            field_be_df = raw_df[raw_df[f'{lang_tag}:be'].notnull()]
            field_ru_df = raw_df[raw_df[f'{lang_tag}:ru'].notnull()]

            field_cnt = field_df[lang_tag].count()
            field_uniq = field_df[lang_tag].value_counts().count()
            field_be_cnt = field_be_df[f'{lang_tag}:be'].count()
            field_be_uniq = field_be_df[f'{lang_tag}:be'].value_counts().count()
            field_ru_cnt = field_ru_df[f'{lang_tag}:ru'].count()
            field_ru_uniq = field_ru_df[f'{lang_tag}:ru'].value_counts().count()

            report_data.append([
                '', tag,
                field_cnt, field_be_cnt, field_ru_cnt,
                field_be_cnt / (field_cnt or 1), field_ru_cnt / (field_cnt or 1),
                field_uniq, field_be_uniq, field_ru_uniq,
                field_be_uniq / (field_uniq or 1), field_ru_uniq / (field_uniq or 1),
            ])

    report_df = pd.DataFrame(report_data, columns=[
        'lvl', 'category',
        'all', 'all be', 'all ru',
        'all be%', 'all ru%',
        'uniq', 'uniq be', 'uniq ru',
        'uniq be%', 'uniq ru%',
    ])
    yield f'statistic-{lang_tag}.csv', report_df.to_csv(index=False, float_format=FLOAT_FORMAT)
    yield f'statistic-{lang_tag}.html', (
        report_df
        .style
        .set_properties(subset=['category'], **{'text-align': 'left'})
        .set_properties(subset=[c for c in report_df.columns if c != 'category'], **{'text-align': 'right'})
        .background_gradient('YlOrRd', subset=[c for c in report_df.columns if c.endswith('%')], vmin=0, vmax=1)
        .format({f: '{:.3f}' for f in [c for c in report_df.columns if c.endswith('%')]})
        .apply(lambda row: [("font-weight: bold" if row.loc['lvl'] == '#' else '') for _ in row], axis=1)
        .to_html(table_attributes=TABLE_ATTRS)
    )


def progress_report(lang_tag, df):
    report_data = []
    report_data_html = []
    for c in list(CATEGORIES_RULES) + ['other', 'TOTAL']:
        raw_df = df[(df['category'] == c) & (df['num'] == -1)]

        field_both_df = raw_df[raw_df['be=ru']]
        field_be_ru_df = raw_df[raw_df['be+ru']]
        field_be_df = raw_df[raw_df['be']]
        field_ru_be_df = raw_df[raw_df['ru+be']]
        field_ru_df = raw_df[raw_df['ru']]
        field_other_both_df = raw_df[raw_df['other_both']]
        field_other_be_df = raw_df[raw_df['other_be']]
        field_other_ru_df = raw_df[raw_df['other_ru']]
        field_none_df = raw_df[raw_df['no_lang']]

        raw_part_df_map = {
            'be=ru': field_both_df,
            'be+ru': field_be_ru_df,
            'be': field_be_df,
            'ru+be': field_ru_be_df,
            'ru': field_ru_df,
            'other_both': field_other_both_df,
            'other_be': field_other_be_df,
            'other_ru': field_other_ru_df,
            'no_lang': field_none_df,
        }

        field_both_cnt = field_both_df['be=ru'].count()
        field_be_ru_cnt = field_be_ru_df['be+ru'].count()
        field_be_cnt = field_be_df['be'].count()
        field_ru_be_cnt = field_ru_be_df['ru+be'].count()
        field_ru_cnt = field_ru_df['ru'].count()
        field_other_both_cnt = field_other_both_df['other_both'].count()
        field_other_be_cnt = field_other_be_df['other_be'].count()
        field_other_ru_cnt = field_other_ru_df['other_ru'].count()
        field_none_cnt = field_none_df['no_lang'].count()
        
        total = (
            field_both_cnt + field_be_ru_cnt + field_be_cnt + field_ru_be_cnt + field_ru_cnt +
            field_other_both_cnt + field_other_be_cnt + field_other_ru_cnt + field_none_cnt
        )

        report_data.append([
            '#', c,

            field_both_cnt,
            field_be_ru_cnt, field_be_cnt,
            field_ru_be_cnt, field_ru_cnt,
            field_other_both_cnt, field_other_be_cnt, field_other_ru_cnt,
            field_none_cnt,

            field_both_cnt / (total or 1),
            field_be_ru_cnt / (total or 1), field_be_cnt / (total or 1),
            field_ru_be_cnt / (total or 1), field_ru_cnt / (total or 1),
            field_other_both_cnt / (total or 1), field_other_be_cnt / (total or 1), field_other_ru_cnt / (total or 1),
            field_none_cnt / (total or 1),
        ])
        report_data_html.append([
            '#', c,

            wrap_hint_progress(lang_tag, c, None, 'be=ru', field_both_cnt),
            wrap_hint_progress(lang_tag, c, None, 'be+ru', field_be_ru_cnt),
            wrap_hint_progress(lang_tag, c, None, 'be', field_be_cnt),
            wrap_hint_progress(lang_tag, c, None, 'ru+be', field_ru_be_cnt),
            wrap_hint_progress(lang_tag, c, None, 'ru', field_ru_cnt),
            wrap_hint_progress(lang_tag, c, None, 'other_both', field_other_both_cnt),
            wrap_hint_progress(lang_tag, c, None, 'other_be', field_other_be_cnt),
            wrap_hint_progress(lang_tag, c, None, 'other_ru', field_other_ru_cnt),
            wrap_hint_progress(lang_tag, c, None, 'no_lang', field_none_cnt),

            field_both_cnt / (total or 1),
            field_be_ru_cnt / (total or 1), field_be_cnt / (total or 1),
            field_ru_be_cnt / (total or 1), field_ru_cnt / (total or 1),
            field_other_both_cnt / (total or 1), field_other_be_cnt / (total or 1), field_other_ru_cnt / (total or 1),
            field_none_cnt / (total or 1),
        ])
        if c != 'TOTAL':
            for part, raw_part_df in raw_part_df_map.items():
                if should_create_csv(lang_tag, c, None, part):
                    yield (
                        f'{lang_tag}/{c}/{part}.csv',
                        raw_part_df[[
                            'osm_type', 'osm_id', lang_tag, f'{lang_tag}:be', f'{lang_tag}:ru'
                        ]].to_csv(index=False, float_format=FLOAT_FORMAT)
                    )
        if c in {'other', 'TOTAL'}:
            continue
        for i, (k, eq, vv) in enumerate(CATEGORIES_RULES2[c]):
            if eq:
                tag = f'{k} = {list(vv)[0]}'
            else:
                tag = f'{k} = *'
            raw_df = df[(df['category'] == c) & (df['num'] == i)]

            field_both_df = raw_df[raw_df['be=ru']]
            field_be_ru_df = raw_df[raw_df['be+ru']]
            field_be_df = raw_df[raw_df['be']]
            field_ru_be_df = raw_df[raw_df['ru+be']]
            field_ru_df = raw_df[raw_df['ru']]
            field_other_both_df = raw_df[raw_df['other_both']]
            field_other_be_df = raw_df[raw_df['other_be']]
            field_other_ru_df = raw_df[raw_df['other_ru']]
            field_none_df = raw_df[raw_df['no_lang']]

            raw_part_df_map = {
                'be=ru': field_both_df,
                'be+ru': field_be_ru_df,
                'be': field_be_df,
                'ru+be': field_ru_be_df,
                'ru': field_ru_df,
                'other_both': field_other_both_df,
                'other_be': field_other_be_df,
                'other_ru': field_other_ru_df,
                'no_lang': field_none_df,
            }

            field_both_cnt = field_both_df['be=ru'].count()
            field_be_ru_cnt = field_be_ru_df['be+ru'].count()
            field_be_cnt = field_be_df['be'].count()
            field_ru_be_cnt = field_ru_be_df['ru+be'].count()
            field_ru_cnt = field_ru_df['ru'].count()
            field_other_both_cnt = field_other_both_df['other_both'].count()
            field_other_be_cnt = field_other_be_df['other_be'].count()
            field_other_ru_cnt = field_other_ru_df['other_ru'].count()
            field_none_cnt = field_none_df['no_lang'].count()

            total = (
                field_both_cnt + field_be_ru_cnt + field_be_cnt + field_ru_be_cnt + field_ru_cnt +
                field_other_both_cnt + field_other_be_cnt + field_other_ru_cnt + field_none_cnt
            )

            report_data.append([
                '', tag,

                field_both_cnt,
                field_be_ru_cnt, field_be_cnt,
                field_ru_be_cnt, field_ru_cnt,
                field_other_both_cnt, field_other_be_cnt, field_other_ru_cnt,
                field_none_cnt,

                field_both_cnt / (total or 1),
                field_be_ru_cnt / (total or 1), field_be_cnt / (total or 1),
                field_ru_be_cnt / (total or 1), field_ru_cnt / (total or 1),
                field_other_both_cnt / (total or 1), field_other_be_cnt / (total or 1),
                field_other_ru_cnt / (total or 1),
                field_none_cnt / (total or 1),
            ])
            report_data_html.append([
                '', tag,

                wrap_hint_progress(lang_tag, c, tag, 'be=ru', field_both_cnt),
                wrap_hint_progress(lang_tag, c, tag, 'be+ru', field_be_ru_cnt),
                wrap_hint_progress(lang_tag, c, tag, 'be', field_be_cnt),
                wrap_hint_progress(lang_tag, c, tag, 'ru+be', field_ru_be_cnt),
                wrap_hint_progress(lang_tag, c, tag, 'ru', field_ru_cnt),
                wrap_hint_progress(lang_tag, c, tag, 'other_both', field_other_both_cnt),
                wrap_hint_progress(lang_tag, c, tag, 'other_be', field_other_be_cnt),
                wrap_hint_progress(lang_tag, c, tag, 'other_ru', field_other_ru_cnt),
                wrap_hint_progress(lang_tag, c, tag, 'no_lang', field_none_cnt),

                field_both_cnt / (total or 1),
                field_be_ru_cnt / (total or 1), field_be_cnt / (total or 1),
                field_ru_be_cnt / (total or 1), field_ru_cnt / (total or 1),
                field_other_both_cnt / (total or 1), field_other_be_cnt / (total or 1),
                field_other_ru_cnt / (total or 1),
                field_none_cnt / (total or 1),
            ])
            for part, raw_part_df in raw_part_df_map.items():
                if should_create_csv(lang_tag, c, tag, part):
                    yield (
                        f'{lang_tag}/{c} - {tag}/{part}.csv',
                        raw_part_df[[
                            'osm_type', 'osm_id', lang_tag, f'{lang_tag}:be', f'{lang_tag}:ru'
                        ]].to_csv(index=False, float_format=FLOAT_FORMAT)
                    )

    report_df = pd.DataFrame(report_data, columns=[
        'lvl', 'category',
        'be=ru', 'be+ru', 'be', 'ru+be', 'ru',
        'other both', 'other be', 'other ru', 'no lang',
        'be=ru%', 'be+ru%', 'be%', 'ru+be%', 'ru%',
        'other both%', 'other be%', 'other ru%', 'no lang%',
    ])
    report_df_html = pd.DataFrame(report_data_html, columns=[
        'lvl', 'category',
        'be=ru', 'be+ru', 'be', 'ru+be', 'ru',
        'other both', 'other be', 'other ru', 'no lang',
        'be=ru%', 'be+ru%', 'be%', 'ru+be%', 'ru%',
        'other both%', 'other be%', 'other ru%', 'no lang%',
    ])
    yield f'progress-{lang_tag}.csv', report_df.to_csv(index=False, float_format=FLOAT_FORMAT)
    yield f'progress-{lang_tag}.html', (
        report_df_html
        .style
        .set_properties(subset=['category'], **{'text-align': 'left'})
        .set_properties(subset=[c for c in report_df_html.columns if c != 'category'], **{'text-align': 'right'})
        .set_properties(subset=['be=ru', 'be+ru', 'be'],
                        **{'background-color': '#d9ead3'})
        .set_properties(subset=['ru+be'],
                        **{'background-color': '#fff2cc'})
        .set_properties(subset=['ru', 'other both', 'other be', 'other ru', 'no lang'],
                        **{'background-color': '#f4cccc'})
        .background_gradient('YlOrRd', subset=[c for c in report_df_html.columns if c.endswith('%')], vmin=0, vmax=1)
        .format({f: '{:.3f}' for f in [c for c in report_df_html.columns if c.endswith('%')]})
        .apply(lambda row: [("font-weight: bold" if row.loc['lvl'] == '#' else '') for _ in row], axis=1)
        .to_html(table_attributes=TABLE_ATTRS)
    )


def get_dependant_df():
    data = []
    with psycopg2.connect(**postgres_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT osm_type, osm_id, name, name_be, name_ru, ST_AsText(way)
                FROM {postgis_api.data_table}
                WHERE name IS NOT NULL OR name_be IS NOT NULL OR name_ru IS NOT NULL
            """)
            name_idx = defaultdict(list)
            geom_idx = {}
            geoms = defaultdict(list)
            for osm_type, osm_id, name, name_be, name_ru, geom_wkt in cur.fetchall():
                names = {name, name_be, name_ru}
                geom = shapely.wkt.loads(geom_wkt)
                for name in names:
                    if not name:
                        continue
                    name_idx[name].append((osm_type, osm_id, name, name_be, name_ru))
                    geoms[name].append(geom)
            for name, name_geoms in geoms.items():
                geom_idx[name] = shapely.strtree.STRtree(name_geoms)

            empty = (None, None, None, None, None)
            for dependant in DEPENDANTS:
                cur.execute(f"""
                    SELECT osm_type, osm_id, tags->'{dependant}', ST_AsText(way)
                    FROM {postgis_api.data_table}
                    WHERE tags->'{dependant}' IS NOT NULL
                """)
                for osm_type, osm_id, name, geom_wkt in cur.fetchall():
                    geom = shapely.wkt.loads(geom_wkt)
                    for name_part in name.split(';'):
                        name_part = name_part.strip()
                        if name_part not in geom_idx:
                            v_osm_type, v_osm_id, value, value_be, value_ru = empty
                        else:
                            idx = geom_idx[name_part].nearest_item(geom)
                            v_osm_type, v_osm_id, value, value_be, value_ru = name_idx[name_part][idx]

                        if value and value_be and value_ru and name_part == value_be == value_ru:
                            progress = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # be=ru
                        elif value and value_be and value_ru and name_part == value_be:
                            progress = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]  # be+ru
                        elif value and value_be and value_ru and name_part == value_ru:
                            progress = [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]  # ru+be
                        elif value and value_be and value_ru:
                            progress = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]  # other both
                        elif value and value_be and not value_ru and name_part == value_be:
                            progress = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]  # be
                        elif value and value_be and not value_ru:
                            progress = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0]  # other be
                        elif value and not value_be and value_ru and name_part == value_ru:
                            progress = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0]  # ru
                        elif value and not value_be and value_ru:
                            progress = [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]  # other ru
                        elif value:
                            progress = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]  # no lang
                        else:
                            progress = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]  # not found

                        data.append((
                            dependant, osm_type, osm_id, name_part,
                            v_osm_type, str(v_osm_id) if v_osm_id  else None, value, value_be, value_ru,
                            *(bool(v) for v in progress),
                        ))
    return pd.DataFrame(data, columns=[
        'category', 'dep_osm_type', 'dep_osm_id', 'dependant',
        'osm_type', 'osm_id', 'name', 'name:be', 'name:ru',
        'be=ru', 'be+ru', 'be', 'ru+be', 'ru',
        'other_both', 'other_be', 'other_ru', 'no_lang', 'not_found',
    ]).sort_values(by=[
        'category', 'dependant', 'name', 'name:be', 'name:ru', 'dep_osm_type', 'dep_osm_id'
    ])


def dependant_statistic_report(df):
    report_data = []
    for c in DEPENDANTS:
        raw_df = df[df['category'] == c]

        dependant_df = raw_df[raw_df['dependant'].notnull()]
        field_df = raw_df[raw_df['name'].notnull()]
        field_be_df = raw_df[raw_df['name:be'].notnull()]
        field_ru_df = raw_df[raw_df['name:ru'].notnull()]

        dependant_cnt = dependant_df['dependant'].count()
        dependant_uniq = dependant_df['dependant'].value_counts().count()
        field_cnt = field_df['name'].count()
        field_uniq = field_df['name'].value_counts().count()
        field_be_cnt = field_be_df['name:be'].count()
        field_be_uniq = field_be_df['name:be'].value_counts().count()
        field_ru_cnt = field_ru_df['name:ru'].count()
        field_ru_uniq = field_ru_df['name:ru'].value_counts().count()

        report_data.append([
            c,

            dependant_cnt, field_cnt, field_be_cnt, field_ru_cnt,
            field_cnt / (dependant_cnt or 1),
            field_be_cnt / (dependant_cnt or 1), field_ru_cnt / (dependant_cnt or 1),
            dependant_uniq, field_uniq, field_be_uniq, field_ru_uniq,
            field_uniq / (dependant_uniq or 1),
            field_be_uniq / (dependant_uniq or 1), field_ru_uniq / (dependant_uniq or 1),
        ])

    report_df = pd.DataFrame(report_data, columns=[
        'category',
        'dep', 'all', 'all be', 'all ru',
        'all%', 'all be%', 'all ru%',
        'dep uniq', 'uniq', 'uniq be', 'uniq ru',
        'uniq%', 'uniq be%', 'uniq ru%',
    ])
    yield f'dependant_statistic-{lang_tag}.csv', report_df.to_csv(index=False, float_format=FLOAT_FORMAT)
    yield f'dependant_statistic-{lang_tag}.html', (
        report_df
            .style
            .set_properties(subset=['category'], **{'text-align': 'left'})
            .set_properties(subset=[c for c in report_df.columns if c != 'category'], **{'text-align': 'right'})
            .background_gradient('YlOrRd', subset=[c for c in report_df.columns if c.endswith('%')], vmin=0, vmax=1)
            .format({f: '{:.3f}' for f in [c for c in report_df.columns if c.endswith('%')]})
            .to_html(table_attributes=TABLE_ATTRS)
    )


def dependant_progress_report(df):
    report_data = []
    report_data_html = []
    for c in DEPENDANTS:
        raw_df = df[df['category'] == c]

        field_both_df = raw_df[raw_df['be=ru']]
        field_be_ru_df = raw_df[raw_df['be+ru']]
        field_be_df = raw_df[raw_df['be']]
        field_ru_be_df = raw_df[raw_df['ru+be']]
        field_ru_df = raw_df[raw_df['ru']]
        field_other_both_df = raw_df[raw_df['other_both']]
        field_other_be_df = raw_df[raw_df['other_be']]
        field_other_ru_df = raw_df[raw_df['other_ru']]
        field_no_lang_df = raw_df[raw_df['no_lang']]
        field_not_found_df = raw_df[raw_df['not_found']]

        raw_part_df_map = {
            'be=ru': field_both_df,
            'be+ru': field_be_ru_df,
            'be': field_be_df,
            'ru+be': field_ru_be_df,
            'ru': field_ru_df,
            'other_both': field_other_both_df,
            'other_be': field_other_be_df,
            'other_ru': field_other_ru_df,
            'no_lang': field_no_lang_df,
            'not_found': field_not_found_df,
        }

        field_both_cnt = field_both_df['be=ru'].count()
        field_be_ru_cnt = field_be_ru_df['be+ru'].count()
        field_be_cnt = field_be_df['be'].count()
        field_ru_be_cnt = field_ru_be_df['ru+be'].count()
        field_ru_cnt = field_ru_df['ru'].count()
        field_other_both_cnt = field_other_both_df['other_both'].count()
        field_other_be_cnt = field_other_be_df['other_be'].count()
        field_other_ru_cnt = field_other_ru_df['other_ru'].count()
        field_no_lang_cnt = field_no_lang_df['no_lang'].count()
        field_not_found_cnt = field_not_found_df['not_found'].count()

        total = (
            field_both_cnt + field_be_ru_cnt + field_be_cnt + field_ru_be_cnt + field_ru_cnt +
            field_other_both_cnt + field_other_be_cnt + field_other_ru_cnt + field_no_lang_cnt +
            field_not_found_cnt
        )

        report_data.append([
            c,

            field_both_cnt,
            field_be_ru_cnt, field_be_cnt,
            field_ru_be_cnt, field_ru_cnt,
            field_other_both_cnt, field_other_be_cnt, field_other_ru_cnt,
            field_no_lang_cnt, field_not_found_cnt,

            field_both_cnt / (total or 1),
            field_be_ru_cnt / (total or 1), field_be_cnt / (total or 1),
            field_ru_be_cnt / (total or 1), field_ru_cnt / (total or 1),
            field_other_both_cnt / (total or 1), field_other_be_cnt / (total or 1), field_other_ru_cnt / (total or 1),
            field_no_lang_cnt / (total or 1), field_not_found_cnt / (total or 1),
        ])
        report_data_html.append([
            c,

            wrap_hint_dependant_progress(c, 'be=ru', field_both_cnt),
            wrap_hint_dependant_progress(c, 'be+ru', field_be_ru_cnt),
            wrap_hint_dependant_progress(c, 'be', field_be_cnt),
            wrap_hint_dependant_progress(c, 'ru+be', field_ru_be_cnt),
            wrap_hint_dependant_progress(c, 'ru', field_ru_cnt),
            wrap_hint_dependant_progress(c, 'other_both', field_other_both_cnt),
            wrap_hint_dependant_progress(c, 'other_be', field_other_be_cnt),
            wrap_hint_dependant_progress(c, 'other_ru', field_other_ru_cnt),
            wrap_hint_dependant_progress(c, 'no_lang', field_no_lang_cnt),
            wrap_hint_dependant_progress(c, 'not_found', field_not_found_cnt),

            field_both_cnt / (total or 1),
            field_be_ru_cnt / (total or 1), field_be_cnt / (total or 1),
            field_ru_be_cnt / (total or 1), field_ru_cnt / (total or 1),
            field_other_both_cnt / (total or 1), field_other_be_cnt / (total or 1), field_other_ru_cnt / (total or 1),
            field_no_lang_cnt / (total or 1), field_not_found_cnt / (total or 1),
        ])

        for part, raw_part_df in raw_part_df_map.items():
            if should_create_csv(lang_tag, c, None, part):
                yield (
                    f'{lang_tag}/{c}/{part}.csv',
                    raw_part_df[[
                        'dep_osm_type', 'dep_osm_id', 'dependant', 'osm_type', 'osm_id', 'name', 'name:be', 'name:ru',
                    ]].to_csv(index=False, float_format=FLOAT_FORMAT)
                )

    report_df = pd.DataFrame(report_data, columns=[
        'category',
        'be=ru', 'be+ru', 'be', 'ru+be', 'ru',
        'other both', 'other be', 'other ru', 'no lang', 'not found',
        'be=ru%', 'be+ru%', 'be%', 'ru+be%', 'ru%',
        'other both%', 'other be%', 'other ru%', 'no lang%', 'not found%',
    ])
    report_df_html = pd.DataFrame(report_data_html, columns=[
        'category',
        'be=ru', 'be+ru', 'be', 'ru+be', 'ru',
        'other both', 'other be', 'other ru', 'no lang', 'not found',
        'be=ru%', 'be+ru%', 'be%', 'ru+be%', 'ru%',
        'other both%', 'other be%', 'other ru%', 'no lang%', 'not found%',
    ])
    yield f'dependant_progress-{lang_tag}.csv', report_df.to_csv(index=False, float_format=FLOAT_FORMAT)
    yield f'dependant_progress-{lang_tag}.html', (
        report_df_html
        .style
        .set_properties(subset=['category'], **{'text-align': 'left'})
        .set_properties(subset=[c for c in report_df_html.columns if c != 'category'], **{'text-align': 'right'})
        .set_properties(subset=['be=ru', 'be+ru', 'be'],
                        **{'background-color': '#d9ead3'})
        .set_properties(subset=['ru+be'],
                        **{'background-color': '#fff2cc'})
        .set_properties(subset=['ru', 'other both', 'other be', 'other ru', 'no lang'],
                        **{'background-color': '#f4cccc'})
        .set_properties(subset=['not found'],
                        **{'background-color': '#e6b8af'})
        .background_gradient('YlOrRd', subset=[c for c in report_df_html.columns if c.endswith('%')], vmin=0, vmax=1)
        .format({f: '{:.3f}' for f in [c for c in report_df_html.columns if c.endswith('%')]})
        .to_html(table_attributes=TABLE_ATTRS)
    )


print('create report')
files = []
for lang_tag in LANGUAGE_TAGS:
    print(lang_tag)
    data_table = precalculate_field_data(lang_tag)
    df = get_df(lang_tag, data_table)
    files.extend(statistic_report(lang_tag, df))
    files.extend(progress_report(lang_tag, df))
    if lang_tag == 'name':
        df = get_dependant_df()
        files.extend(dependant_statistic_report(df))
        files.extend(dependant_progress_report(df))
htmls = {}
result = {}
for name, content in files:
    if name.endswith('html'):
        htmls[name] = content
    else:
        result[f'data/{name}'] = content
groups = defaultdict(dict)
for name, content in htmls.items():
    table, tag = name[:-len('.html')].split('-')
    groups[tag][table] = content
with open('belarus_report.html') as t:
    result['index.html'] = Template(t.read()).render(groups=groups)

print('create atom')
autofix_items = []
rss_data = []
for name, content in result.items():
    if not name.startswith('data/name/'):
        continue
    _, lang_tag, category, issue = name.split('/')
    issue = issue[:-len('.csv')]
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        row['category'] = category
        row['issue'] = issue
        rss_data.append(row)
rss_data_prev = []
for root, _, files in os.walk('data/name/'):
    for file in files:
        name = os.path.join(root, file)
        _, lang_tag, category, issue = name.split('/')
        issue = issue[:-len('.csv')]
        with open(name) as h:
            reader = csv.DictReader(h)
            for row in reader:
                row['category'] = category
                row['issue'] = issue
                rss_data_prev.append(row)
rss_data_dict = {tuple(row.values()): row for row in rss_data}
rss_data_prev_dict = {tuple(row.values()): row for row in rss_data_prev}
rss_data_new = [rss_data_dict[k] for k in rss_data_dict.keys() - rss_data_prev_dict.keys()]
rss_groups = defaultdict(lambda: defaultdict(dict))
engine = Engine(postgis_api, None, None, None, None, None)
_, _, name_elements_full, name_index_full = engine.build_name_spatial_index()
for row in rss_data_new:
    main_category = row['category'].split(' - ')[0]
    sub_category = row['category'].split(' - ')[-1]
    key = tuple(v for k, v in row.items() if k not in {'category', 'issue'})
    item = rss_groups[main_category][key]
    item.update(row)
    item['categories'] = (item.get('categories', '') + ' | ' + sub_category).strip(' |')
    del item['category']
for name, group_dict in rss_groups.items():
    for item in group_dict.values():
        item['autofix:be'] = None
        item['autofix:ru'] = None
        if item['name'] and item['name'] in name_elements_full:
            osm_type = item['osm_type']
            osm_id = int(item['osm_id'])
            if osm_type == 'node':
                element = postgis_api.read_nodes([osm_id])[osm_id]
            elif osm_type == 'way':
                element = postgis_api.read_ways([osm_id])[osm_id]
            elif osm_type == 'relation':
                element = postgis_api.read_relations([osm_id])[osm_id]
            nearest = engine._choose_nearest(name_index_full, name_elements_full, item['name'], element['way'])
            distance = shapely.wkt.loads(element['way']).distance(shapely.wkt.loads(nearest.way)) * 111000
            if nearest.tags['name'] in {nearest.tags['name:be'], nearest.tags['name:ru']}:
                if 'dependant' in item or name == 'highway' or distance < 5000:
                    item['autofix:be'] = nearest.tags['name:be']
                    item['autofix:ru'] = nearest.tags['name:ru']
                    for tag in ['name:be', 'name:ru']:
                        if not item[tag] and 'dependant' not in item:
                            autofix_items.append(ElementRuleChange(
                                comment='autofix using similar object',
                                osm_id=osm_id,
                                osm_type=osm_type,
                                update_tag=tag,
                                value_from=None,
                                value_to=nearest.tags[tag],
                                main=False,  # reuse dependant checks for update as main more restrictive
                                use_osm_id=(nearest.osm_id,),
                                use_osm_type=(nearest.osm_type,),
                            ))


def render_style_template(item):
    if item['issue'] == 'other_both':
        return '<tr style="background-color:#fff2cc;">{}</tr>'
    if item['autofix:be']:
        return '<tr style="background-color:#d9ead3;">{}</tr>'
    return '<tr>{}</tr>'


def render_value(field, item):
    value = item[field]
    if field == 'name:be':
        if value:
            return html.escape(value)
        autofix = item['autofix:be']
        if autofix:
            return f'<b>{html.escape(autofix)}</b>'
    if field == 'name:ru':
        if value:
            return html.escape(value)
        autofix = item['autofix:ru']
        if autofix:
            return f'<b>{html.escape(autofix)}</b>'
    return html.escape(value)


rss_groups_rendered = {}
for name, group_dict in rss_groups.items():
    group = list(group_dict.values())
    non_fixed_group = [item for item in group if item['issue'] != 'other_both' and not item['autofix:be']]
    rss_groups_rendered[name] = {
        'title': f'{name} +{len(non_fixed_group)} not fixed +{len(group)} total',
        'content': (
            '<table>' +
            '<tr>' +
            ''.join(f'<th>{html.escape(k)}</th>' for k in group[0].keys() if k not in {'autofix:be', 'autofix:ru'}) +
            '</tr>' +
            ''.join(render_style_template(item).format(
                ''.join(
                    f'<td>{render_value(k, item) or "&nbsp;"}</td>'
                    for k in item.keys()
                    if k not in {'autofix:be', 'autofix:ru'}
                ))
                for item in group
            ) +
            '</table>'
        ),
    }
with open('belarus_report.atom') as t:
    result['index.atom'] = Template(t.read()).render(
        groups=rss_groups_rendered,
        time=datetime.datetime.utcnow().isoformat().split('.')[0] + 'Z',
    )

if AUTOFIX_OSM:
    OSM_USER = os.environ['OSM_USER']
    OSM_PASSWORD = os.environ['OSM_PASSWORD']
    DRY_RUN = bool(int(os.environ['DRY_RUN']))
    osm_api_rw_engine = OsmApiReadWriteEngine(username=OSM_USER, password=OSM_PASSWORD, dry_run=DRY_RUN)
    print_issues_engine = PrintIssuesEngine()
    engine = Engine(None, osm_api_rw_engine, osm_api_rw_engine, print_issues_engine, None, None)
    engine._update_elements(autofix_items)

if REPORT_OUTPUT_API:
    print('commit to github')
    g = github.Github(login_or_token=GITHUB_TOKEN, timeout=300)
    repo = g.get_repo(REPO_NAME)
    elements = []
    for name, content in result.items():
        blob = repo.create_git_blob(content, 'utf-8')
        element = github.InputGitTreeElement(path=name, mode='100644', type='blob', sha=blob.sha)
        elements.append(element)
    head_sha = repo.get_branch('main').commit.sha
    base_tree = repo.get_git_tree(sha=head_sha)
    tree = repo.create_git_tree(elements, base_tree)
    parent = repo.get_git_commit(sha=head_sha)
    commit = repo.create_git_commit('report update', tree, [parent])
    master_refs = repo.get_git_ref('heads/main')
    master_refs.edit(sha=commit.sha)
else:
    print('save locally')
    for name, content in result.items():
        if os.path.dirname(name):
            os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(name, 'w') as h:
            h.write(content)
