import bz2
import csv
import datetime
import gzip
import io
import json
import os.path
import sys
import time
from collections import defaultdict, Counter

import osmapi
import requests
import shapely.geometry
import shapely.wkt
from lxml import etree


DATE_FROM = sys.argv[1]
DATE_TO = sys.argv[2]
DUMP_FILE = os.path.expanduser(sys.argv[3])
API_USER = sys.argv[4]
API_PASS = sys.argv[5]
BBOX = [51.2626864, 32.7627809, 56.17218, 23.1783313]
B_MIN_LAT, B_MAX_LON, B_MAX_LAT, B_MIN_LON = BBOX
with open('belarus.wkt') as h:
    B_GEOM = shapely.wkt.load(h)
with open('belarus-full.wkt') as h:
    B_GEOM_FULL = shapely.wkt.load(h)
B_GEOM_INNER = B_GEOM.buffer(-0.01).simplify(0.005)
IGNORE_USERS = {'SomeoneElse_Revert'}
CHANGESETS_IN_BOUNDARY_CACHE_FILE = 'belarus_changeset_cache.json'
with open(CHANGESETS_IN_BOUNDARY_CACHE_FILE) as h:
    CHANGESETS_IN_BOUNDARY_CACHE = {int(cid): isin for cid, isin in json.load(h).items()}
api = osmapi.OsmApi(username=API_USER, password=API_PASS)


def iter_changes_replication(top_dir, sub_dir, file_num):
    url_template = 'https://planet.openstreetmap.org/replication/changesets/{:03}/{:03}/{:03}.osm.gz'
    for i1 in range(top_dir, -1, -1):
        for i2 in range(sub_dir, -1, -1):
            print(url_template.format(i1, i2, file_num))
            for i3 in range(file_num, -1, -1):
                yield url_template.format(i1, i2, i3)
            file_num = 999
        sub_dir = 999


def iter_changes(dump):
    i = 0
    latest_cid = 0
    main_start = start = datetime.datetime.utcnow()
    with bz2.open(dump) as h:
        context = etree.iterparse(h, events=('end',), tag='changeset')
        for _, elem in context:
            i += 1
            if i % 1_000_000 == 0:
                end = datetime.datetime.utcnow()
                print(i, end - main_start, end - start)
                start = end

            attrib_get = elem.attrib.get
            cid = int(attrib_get('id'))
            latest_cid = max(latest_cid, cid)
            yield cid, attrib_get
            elem.clear()

    print(latest_cid)
    session = requests.session()
    response = session.get('https://planet.openstreetmap.org/replication/changesets/state.yaml')
    response.raise_for_status()
    last_id = int(response.text.splitlines()[2].split(': ')[1])
    for url in iter_changes_replication(last_id // 1_000_000, last_id // 1000 % 1000, last_id % 1000):
        for i in range(10 + 1):
            try:
                response = session.get(url)
                response.raise_for_status()
                break
            except Exception as err:
                print(url, err)
                if i == 10:
                    raise
                time.sleep(2**i)
        new = 0
        with gzip.open(io.BytesIO(response.content)) as h:
            context = etree.iterparse(h, events=('end',), tag='changeset')
            for _, elem in context:
                new += 1
                i += 1
                if i % 1_000_000 == 0:
                    end = datetime.datetime.utcnow()
                    print(i, end - main_start, end - start)
                    start = end

                attrib_get = elem.attrib.get
                cid = int(attrib_get('id'))
                if cid <= latest_cid:
                    new -= 1
                else:
                    yield cid, attrib_get
                elem.clear()
        if new == 0:
            return


def get_bbox_geom(min_lon, min_lat, max_lon, max_lat):
    if min_lon == max_lon and min_lat == max_lat:
        return shapely.geometry.Point(min_lon, min_lat)
    elif min_lon == max_lon or min_lat == max_lat:
        return shapely.geometry.LineString([(min_lon, min_lat), (max_lon, max_lat)])
    else:
        return shapely.geometry.box(min_lon, min_lat, max_lon, max_lat)


def process():
    data = defaultdict(list)
    for cid, attrib_get in iter_changes(DUMP_FILE):
        created_at = attrib_get('created_at')
        closed_at = attrib_get('closed_at')
        if closed_at is not None:
            if not (DATE_FROM <= closed_at <= DATE_TO):
                continue
        elif created_at is not None:
            if not (DATE_FROM <= created_at <= DATE_TO):
                continue
        else:
            continue

        user = attrib_get('user')
        uid_str = attrib_get('uid')
        uid = int(uid_str) if uid_str is not None else None
        min_lat = float(attrib_get('min_lat', 0))
        max_lat = float(attrib_get('max_lat', 0))
        min_lon = float(attrib_get('min_lon', 0))
        max_lon = float(attrib_get('max_lon', 0))

        intersects = min_lat < B_MAX_LAT and B_MIN_LAT < max_lat and min_lon < B_MAX_LON and B_MIN_LON < max_lon
        if intersects:
            geom = get_bbox_geom(min_lon, min_lat, max_lon, max_lat)
            if B_GEOM.intersects(geom):
                data[uid].append({
                    'cid': cid,
                    'uid': uid,
                    'user': user,
                    'created_at': created_at,
                    'closed_at': closed_at,
                    'min_lat': min_lat,
                    'min_lon': min_lon,
                    'max_lat': max_lat,
                    'max_lon': max_lon,
                })

    return data


def geom_intersects(cc):
    result = []
    for c in cc:
        geom = get_bbox_geom(c['min_lon'], c['min_lat'], c['max_lon'], c['max_lat'])
        if B_GEOM.intersects(geom):
            result.append(c)
    return result


def geom_contains(cc):
    result = []
    for c in cc:
        geom = get_bbox_geom(c['min_lon'], c['min_lat'], c['max_lon'], c['max_lat'])
        if B_GEOM_INNER.contains(geom):
            result.append(c)
    return result


def count_mount(cc):
    return len(set((c['closed_at'] or c['created_at'])[:7] for c in cc))


def _split_chunks(items, max_chunk_size):
    for i in range(0, len(items), max_chunk_size):
        yield items[i:i + max_chunk_size]


def changeset_in_boundary(cid):
    print(cid)
    changeset = api.ChangesetDownload(cid)
    invisible_nodes = []
    invisible_ways = []
    invisible_rels = []

    # nodes
    node_ids = [change['data']['id'] for change in changeset if change['type'] == 'node']
    nodes = [change['data'] for change in changeset if change['type'] == 'node']
    for node in nodes:
        if not node['visible']:
            invisible_nodes.append(node['id'])
        else:
            point = shapely.geometry.Point(node['lon'], node['lat'])
            if B_GEOM.contains(point) and B_GEOM_FULL.contains(point):
                return True

    # rels
    rels = [change['data'] for change in changeset if change['type'] == 'relation']
    rel_way_ids = [member['ref'] for rel in rels for member in rel['member'] if member['type'] == 'way']
    rel_node_ids = [member['ref'] for rel in rels for member in rel['member'] if member['type'] == 'node']
    invisible_rels.extend(rel['id'] for rel in rels if not rel['visible'])
    for rel_id in invisible_rels:
        history = [version for version in api.RelationHistory(rel_id).values() if version['visible']]
        if history:
            rel = history[-1]
            rel_way_ids.extend(member['ref'] for member in rel['member'] if member['type'] == 'way')
            rel_node_ids.extend(member['ref'] for member in rel['member'] if member['type'] == 'node')
    rel_way_node_ids = []
    for chunk_ids in _split_chunks(rel_way_ids, 725):
        ways = list(api.WaysGet(chunk_ids).values())
        rel_way_node_ids.extend(node for way in ways for node in way['nd'])
        invisible_ways.extend(way['id'] for way in ways if not way['visible'])

    # ways
    ways = [change['data'] for change in changeset if change['type'] == 'way']
    way_node_ids = [node for way in ways for node in way['nd']]
    invisible_ways.extend(way['id'] for way in ways if not way['visible'])
    for way_id in invisible_ways:
        history = [version for version in api.WayHistory(way_id).values() if version['visible']]
        if history:
            way = history[-1]
            way_node_ids.extend(way['nd'])

    # way and rel nodes
    all_node_ids = list(set(way_node_ids + rel_node_ids + rel_way_node_ids) - set(node_ids))
    for chunk_ids in _split_chunks(all_node_ids, 725):
        nodes = api.NodesGet(chunk_ids)
        for node in nodes.values():
            if not node['visible']:
                invisible_nodes.append(node['id'])
            else:
                point = shapely.geometry.Point(node['lon'], node['lat'])
                if B_GEOM.contains(point) and B_GEOM_FULL.contains(point):
                    return True

    # deleted nodes
    for node_id in invisible_nodes:
        history = [version for version in api.NodeHistory(node_id).values() if version['visible']]
        if history:
            node = history[-1]
            point = shapely.geometry.Point(node['lon'], node['lat'])
            if B_GEOM.contains(point) and B_GEOM_FULL.contains(point):
                return True

    return False


def changeset_in_boundary_cached(c):
    cid = c['cid']
    bbox = get_bbox_geom(c['min_lon'], c['min_lat'], c['max_lon'], c['max_lat'])

    # simply check is bbox intersects with boundary
    if not B_GEOM.intersects(bbox):
        return False

    # simply check is bbox in boundary
    if B_GEOM_INNER.contains(bbox):
        return True

    # collect changeset bodies
    if cid not in CHANGESETS_IN_BOUNDARY_CACHE:
        CHANGESETS_IN_BOUNDARY_CACHE[cid] = changeset_in_boundary(cid)
        with open(CHANGESETS_IN_BOUNDARY_CACHE_FILE, 'w') as h:
            json.dump(CHANGESETS_IN_BOUNDARY_CACHE, h, indent=2)
    return CHANGESETS_IN_BOUNDARY_CACHE[cid]


if not os.path.exists('belarus_users.json'):
    data = process()
    with open('belarus_users.json', 'w') as h:
        json.dump(data, h, indent=2, ensure_ascii=False)
with open('belarus_users.json') as h:
    data = json.load(h)


data_edited_3_month = {u: cc for u, cc in data.items() if count_mount(cc) >= 3}
data_edited_3_month_in_bel = {u: cc for u, cc in data.items() if count_mount(geom_contains(cc)) >= 3}

data_not_fully_checked = {u: cc for u, cc in data_edited_3_month.items() if u not in data_edited_3_month_in_bel}
data_detailed_checked = {
    u: [c for c in cc if changeset_in_boundary_cached(c)]
    for u, cc in data_not_fully_checked.items()
    if cc[0]['user'] not in IGNORE_USERS
}
data_detailed_checked_edited_3_month = {u: cc for u, cc in data_detailed_checked.items() if count_mount(cc) >= 3}

data_final = {**data_edited_3_month_in_bel, **data_detailed_checked_edited_3_month}

print('origin', len(data), sum(len(cc) for cc in data.values()))
print('origin 3 month', len(data_edited_3_month), sum(len(cc) for cc in data_edited_3_month.values()))
print('contains 3 month', len(data_edited_3_month_in_bel), sum(len(cc) for cc in data_edited_3_month_in_bel.values()))
print('for check', len(data_not_fully_checked), sum(len(cc) for cc in data_not_fully_checked.values()))
print('checked', len(data_detailed_checked), sum(len(cc) for cc in data_detailed_checked.values()))
print('checked 3 month', len(data_detailed_checked_edited_3_month), sum(len(cc) for cc in data_detailed_checked_edited_3_month.values()))
print('final', len(data_final), sum(len(cc) for cc in data_final.values()))


dates = [
    '2021-09', '2021-10', '2021-11',
    '2021-12', '2022-01', '2022-02',
    '2022-03', '2022-04', '2022-05',
    '2022-06', '2022-07', '2022-08',
]


def get_row(cc):
    counter = Counter((c['closed_at'] or c['created_at'])[:7] for c in cc)
    results = [cc[0]['user'], cc[0]['uid'], sum(counter.values())]
    for date in dates:
        results.append(counter[date])
    return results


with open('belarus_active_users.csv', 'w') as h:
    writer = csv.writer(h)
    writer.writerow(['user', 'uid', 'sum'] + dates)
    writer.writerows([get_row(cc) for cc in sorted(data_final.values(), key=lambda cc: -len(cc))])
