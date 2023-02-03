#!/usr/bin/python3
"""
this script allows to replace main and dependant tags as name and addr:street or other with appropriate
language form the language tag or nearest parent object

this script use "pyosmium" and "shapely" python libraries and also "osmium" command from "osmium-tool":

    apt-get install osmium-tool
    pip install osmium shapely

as alternative all packages can be installed using system packages:

    apt-get install osmium-tool python3-pyosmium python3-shapely

as alternative use docker:

    docker build -t osm_back -f osm_back.dockerfile .
    docker run -it --rm -v $(pwd):/app/ osm_back \
        python3 osm_back.py -l ru -o belarus-latest-ru.osm.pbf belarus-latest.osm.pbf

"""
import argparse
import contextlib
import datetime
import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict, Counter
from functools import wraps
from itertools import chain
from typing import Union, Iterable, FrozenSet, Optional, Any, TypeVar, Callable

import shapely.ops
import shapely.strtree
import shapely.wkb

import osmium.version


NODE = 'node'
WAY = 'way'
REL = 'relation'

TYPE_OSC = 'osc'
TYPE_OSM = 'osm'
TYPE_OSM_BZ2 = 'osm.bz2'
TYPE_OSM_PBF = 'osm.pbf'

DEFAULT_MAIN_TAGS = [
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

DEFAULT_DEPENDANT_TAGS = [
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
]


T = TypeVar('T')
_log_stack = 0


if shapely.__version__ >= '2.0.0':
    STRtree = shapely.strtree.STRtree
else:
    class STRtree(shapely.strtree.STRtree):
        def nearest(self, geom):
            return self.nearest_item(geom)


def log(*params: Any):
    print(datetime.datetime.now(), '  ' * _log_stack, *params)


def log_time(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        global _log_stack
        start = datetime.datetime.now()
        log(func.__name__, 'start')
        _log_stack += 1
        try:
            result = func(*args, **kwargs)
            _log_stack -= 1
            end = datetime.datetime.now()
            log(func.__name__, 'finish', end - start)
            return result
        except Exception as err:
            _log_stack -= 1
            end = datetime.datetime.now()
            log(func.__name__, 'error', end - start)
            raise err
    return wrapper


@contextlib.contextmanager
def temp_file(content: bytes = b'', suffix: str = ''):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
        yield tmp.name
    finally:
        if tmp is not None and os.path.exists(tmp.name):
            os.unlink(tmp.name)


def get_input_file_name(stack: contextlib.ExitStack, file: [str, bytes], input_format: str) -> str:
    if isinstance(file, bytes):
        return stack.enter_context(temp_file(content=file, suffix=f'.{input_format}'))
    else:
        return file


def get_ids_file_name(stack: contextlib.ExitStack, ids: Iterable[str]) -> str:
    return stack.enter_context(temp_file(content='\n'.join(ids).encode('utf8'), suffix='.txt'))


def osmium_version(check: bool = True):
    result = subprocess.run(
        ['osmium', '--version'],
        capture_output=True, check=check,
    )
    return result.stdout


def osmium_fileinfo(input_file: str, json: bool = False, check: bool = True):
    params = ['osmium', 'fileinfo']
    if json:
        params.append('-j')
    result = subprocess.run(
        params + [input_file],
        capture_output=True, check=check,
    )
    return result.stdout


def osmium_fileformat(input_file: str, check: bool = True):
    info = json.loads(osmium_fileinfo(input_file, json=True, check=check))
    mapping = {
        ('XML', 'none'): TYPE_OSM,
        ('XML', 'bzip2'): TYPE_OSM_BZ2,
        ('PBF', 'none'): TYPE_OSM_PBF,
    }
    return mapping[(info['file']['format'], info['file']['compression'])]


@log_time
def osmium_getid(
        file: [str, bytes],
        nodes: Iterable[str] = (),
        ways: Iterable[str] = (),
        rels: Iterable[str] = (),
        mixed: Iterable[str] = (),
        add_referenced: bool = False,
        remove_tags: bool = False,
        input_format: str = TYPE_OSM_PBF,
        output_format: str = TYPE_OSM_PBF,
        check: bool = True,
) -> bytes:
    with contextlib.ExitStack() as stack:
        ids = chain(
            (f'n{node_id}' for node_id in nodes),
            (f'w{way_id}' for way_id in ways),
            (f'r{rel_id}' for rel_id in rels),
            mixed,
        )
        params = ['osmium', 'getid', '-i', get_ids_file_name(stack, ids), '-f', output_format]
        if add_referenced:
            params.append('-r')
        if remove_tags:
            params.append('-t')
        result = subprocess.run(
            params + [get_input_file_name(stack, file, input_format)],
            capture_output=True, check=False,
        )
        if check and result.returncode not in {0, 1}:
            raise subprocess.CalledProcessError(
                result.returncode, result.args, output=result.stdout, stderr=result.stderr,
            )
        return result.stdout


@log_time
def osmium_removeid(
        file: [str, bytes],
        nodes: Iterable[str] = (),
        ways: Iterable[str] = (),
        rels: Iterable[str] = (),
        mixed: Iterable[str] = (),
        input_format: str = TYPE_OSM_PBF,
        output_format: str = TYPE_OSM_PBF,
        check: bool = True,
) -> bytes:
    with contextlib.ExitStack() as stack:
        ids = chain(
            (f'n{node_id}' for node_id in nodes),
            (f'w{way_id}' for way_id in ways),
            (f'r{rel_id}' for rel_id in rels),
            mixed,
        )
        params = ['osmium', 'removeid', '-i', get_ids_file_name(stack, ids), '-f', output_format]
        result = subprocess.run(
            params + [get_input_file_name(stack, file, input_format)],
            capture_output=True, check=check,
        )
        return result.stdout


@log_time
def osmium_tags_filter(
        file: [str, bytes],
        tags: Iterable[str] = (),
        omit_referenced: bool = False,
        remove_tags: bool = False,
        input_format: str = TYPE_OSM_PBF,
        output_format: str = TYPE_OSM_PBF,
        check: bool = True,
) -> bytes:
    with contextlib.ExitStack() as stack:
        params = ['osmium', 'tags-filter', '-f', output_format]
        if omit_referenced:
            params.append('-R')
        if remove_tags:
            params.append('-t')
        result = subprocess.run(
            params + [get_input_file_name(stack, file, input_format), *tags],
            stdout=subprocess.PIPE, check=check,
        )
        return result.stdout


@log_time
def osmium_merge(
        *files: [str, bytes],
        input_format: str = TYPE_OSM_PBF,
        output_format: str = TYPE_OSM_PBF,
        check: bool = True,
) -> bytes:
    with contextlib.ExitStack() as stack:
        input_files = [get_input_file_name(stack, file, input_format) for file in files]
        result = subprocess.run(
            ['osmium', 'merge', '-f', output_format, *input_files],
            stdout=subprocess.PIPE, check=check,
        )
        return result.stdout


@log_time
def osmium_cat(
        file: [str, bytes],
        input_format: str = TYPE_OSM_PBF,
        output_format: str = TYPE_OSM_PBF,
        check: bool = True,
) -> bytes:
    with contextlib.ExitStack() as stack:
        result = subprocess.run(
            ['osmium', 'cat', '-f', output_format, get_input_file_name(stack, file, input_format)],
            stdout=subprocess.PIPE, check=check,
        )
        return result.stdout


class Container:
    def __init__(self, main_tags: FrozenSet[str], dependency_tags: FrozenSet[str], lang: str):
        self.main_tags = main_tags
        self.dependency_tags = dependency_tags
        self.lang = lang
        self.objects = {
            NODE: defaultdict(dict),
            WAY: defaultdict(dict),
            REL: defaultdict(dict),
        }
        self.dep_objects = {
            NODE: defaultdict(dict),
            WAY: defaultdict(dict),
            REL: defaultdict(dict),
        }
        self.dep_names = set()
        self.dep_stat = Counter()

        self.rel_nodes = set()
        self.type_geoms = {
            NODE: defaultdict(list),
            WAY: defaultdict(list),
            REL: defaultdict(list),
        }

        self.name_obj = defaultdict(list)
        self.name_geoms = defaultdict(list)
        self.name_strtree = {}
        self.updates = {
            NODE: defaultdict(dict),
            WAY: defaultdict(dict),
            REL: defaultdict(dict),
        }


class MainHandler(osmium.SimpleHandler):
    def __init__(self, container: Container):
        super().__init__()
        self.container = container

    def process(self, osm_type: str, obj: Union[osmium.osm.Node, osmium.osm.Way, osmium.osm.Relation]):
        if not obj.tags:
            return
        for key in self.container.main_tags:
            key_lang = f'{key}:{self.container.lang}'
            if key_lang in obj.tags:
                self.container.updates[osm_type][obj.id][key] = obj.tags[key_lang]

    def node(self, n: osmium.osm.Node):
        self.process(NODE, n)

    def way(self, w: osmium.osm.Way):
        self.process(WAY, w)

    def relation(self, r: osmium.osm.Relation):
        self.process(REL, r)


class DependenciesHandler(osmium.SimpleHandler):
    def __init__(self, container: Container):
        super().__init__()
        self.container = container

    def process(self, osm_type: str, obj: Union[osmium.osm.Node, osmium.osm.Way, osmium.osm.Relation]):
        if not obj.tags:
            return
        for key in self.container.dependency_tags:
            if key in obj.tags:
                value = obj.tags[key]
                self.container.dep_objects[osm_type][obj.id][key] = value
                self.container.dep_names.add(value)
                self.container.dep_stat[key] += 1

    def node(self, n: osmium.osm.Node):
        self.process(NODE, n)

    def way(self, w: osmium.osm.Way):
        self.process(WAY, w)

    def relation(self, r: osmium.osm.Relation):
        self.process(REL, r)


class ParentHandler(osmium.SimpleHandler):
    def __init__(self, container: Container):
        super().__init__()
        self.container = container
        self.lang = container.lang

    def process(self, osm_type: str, obj: Union[osmium.osm.Node, osmium.osm.Way, osmium.osm.Relation]):
        if 'name' in obj.tags and f'name:{self.lang}' in obj.tags and obj.tags['name'] in self.container.dep_names:
            self.container.objects[osm_type][obj.id]['name'] = obj.tags['name']
            self.container.objects[osm_type][obj.id][f'name:{self.lang}'] = obj.tags[f'name:{self.lang}']

    def node(self, n: osmium.osm.Node):
        self.process(NODE, n)

    def way(self, w: osmium.osm.Way):
        self.process(WAY, w)

    def relation(self, r: osmium.osm.Relation):
        self.process(REL, r)


class RelsHandler(osmium.SimpleHandler):
    def __init__(self, container: Container):
        super().__init__()
        self.container = container

    def relation(self, r: osmium.osm.Relation):
        for member in r.members:
            if member.type == 'n':
                self.container.rel_nodes.add(member.ref)


class GeometriesBuilderHandler(osmium.SimpleHandler):
    def __init__(self, container: Container):
        super().__init__()
        self.wkbfab = osmium.geom.WKBFactory()
        self.container = container
        self.nodes = (
            self.container.dep_objects[NODE].keys() |
            self.container.objects[NODE].keys() |
            self.container.rel_nodes
        )

    def node(self, n: osmium.osm.Node):
        try:
            if n.id in self.nodes:
                point = shapely.wkb.loads(self.wkbfab.create_point(n), hex=True)
                self.container.type_geoms[NODE][n.id].append(point)
        except ValueError:
            print(f'n{n.id}')
            raise

    def way(self, w: osmium.osm.Way):
        try:
            if len(w.nodes) < 2:
                for node_ref in w.nodes:
                    point = shapely.wkb.loads(self.wkbfab.create_point(node_ref), hex=True)
                    self.container.type_geoms[WAY][w.id].append(point)
            else:
                line = shapely.wkb.loads(self.wkbfab.create_linestring(w), hex=True)
                polys = list(shapely.ops.polygonize(line))
                if len(polys) == 0:
                    self.container.type_geoms[WAY][w.id].append(line)
                else:
                    self.container.type_geoms[WAY][w.id].extend(polys)
        except (RuntimeError, osmium.InvalidLocationError):
            # ignore geometries with bad references
            pass
        except ValueError:
            print(f'w{w.id}')
            raise

    def relation(self, r: osmium.osm.Relation):
        try:
            points = []
            lines = []
            polygons = []
            biggest_area = None
            biggest_geom = None
            for member in r.members:
                if member.type == 'n':
                    points.extend(self.container.type_geoms[NODE][member.ref])
                elif member.type == 'w':
                    for geom in self.container.type_geoms[WAY][member.ref]:
                        if geom.geom_type == 'LineString':
                            lines.append(geom)
                        else:
                            if biggest_area is None or geom.area > biggest_area:
                                biggest_geom = geom
                            polygons.append(geom)
            for polygon in shapely.ops.polygonize(lines):
                if biggest_area is None or polygon.area > biggest_area:
                    biggest_geom = polygon
                polygons.append(polygon)
            result = []
            if biggest_geom is not None:
                for point in points:
                    if not biggest_geom.covers(point):
                        result.append(point)
                for line in lines:
                    if not biggest_geom.covers(line):
                        result.append(line)
                for polygon in polygons:
                    if polygon is biggest_geom or not biggest_geom.covers(polygon):
                        result.append(polygon)
            else:
                result.extend(points)
                result.extend(lines)
                result.extend(polygons)
            if result:
                self.container.type_geoms[REL][r.id].append(shapely.ops.unary_union(result))
        except ValueError:
            print(f'r{r.id}')
            raise


class UpdateHandler(osmium.SimpleHandler):
    def __init__(self, container: Container, writer: osmium.SimpleWriter):
        super().__init__()
        self.container = container
        self.writer = writer

    def node(self, n: osmium.osm.Node):
        self.writer.add_node(n.replace(tags=dict(n.tags, **self.container.updates[NODE][n.id])))

    def way(self, w: osmium.osm.Way):
        self.writer.add_way(w.replace(tags=dict(w.tags, **self.container.updates[WAY][w.id])))

    def relation(self, r: osmium.osm.Relation):
        self.writer.add_relation(r.replace(tags=dict(r.tags, **self.container.updates[REL][r.id])))


@log_time
def collect_dependencies(container: Container, input_file: str):
    handler = DependenciesHandler(container)
    deps_pbf = osmium_tags_filter(input_file, container.dependency_tags, omit_referenced=True)
    handler.apply_buffer(deps_pbf, TYPE_OSM_PBF)
    log('STAT:', 'total unique names', len(container.dep_names))
    log('STAT:', 'total objects count', sum(len(objs) for objs in container.dep_objects.values()))
    for tag, count in container.dep_stat.most_common():
        log('STAT:', f'"{tag}" objects count', count)


@log_time
def collect_parent(container: Container, input_file: str):
    names_pbf = osmium_tags_filter(input_file, [f'name:{container.lang}'], omit_referenced=True)
    ParentHandler(container).apply_buffer(names_pbf, TYPE_OSM_PBF)
    log('STAT:', 'total objects count', sum(len(objs) for objs in container.objects.values()))


@log_time
def build_geoms(container: Container, input_file: str):
    ids_pbf = osmium_getid(
        input_file,
        nodes=container.objects[NODE].keys() | container.dep_objects[NODE].keys(),
        ways=container.objects[WAY].keys() | container.dep_objects[WAY].keys(),
        rels=container.objects[REL].keys() | container.dep_objects[REL].keys(),
        add_referenced=True,
        remove_tags=True,
    )
    RelsHandler(container).apply_buffer(ids_pbf, TYPE_OSM_PBF)
    GeometriesBuilderHandler(container).apply_buffer(ids_pbf, TYPE_OSM_PBF, locations=True)


@log_time
def build_index(container: Container):
    for osm_type, objects in container.objects.items():
        for osm_id, tags in objects.items():
            if 'name' in tags and f'name:{container.lang}' in tags and tags['name'] in container.dep_names:
                for geom in container.type_geoms[osm_type][osm_id]:
                    container.name_obj[tags['name']].append((osm_type, osm_id))
                    container.name_geoms[tags['name']].append(geom)
    for name, geoms in container.name_geoms.items():
        container.name_strtree[name] = STRtree(geoms)


@log_time
def find_dependency_parent_updates(container: Container):
    for osm_type, obj_tags in container.dep_objects.items():
        for osm_id, tags in obj_tags.items():
            for tag in container.dependency_tags:
                if tag in tags:
                    name = tags[tag]
                    if not container.type_geoms[osm_type][osm_id] or name not in container.name_obj:
                        continue
                    tree = container.name_strtree[name]
                    if len(container.name_geoms[name]) == 1:
                        closets_idx = 0
                    else:
                        closest_distance = None
                        closets_idx = None
                        for geom in container.type_geoms[osm_type][osm_id]:
                            idx = tree.nearest(geom)
                            distance = geom.distance(container.name_geoms[name][idx])
                            if closest_distance is None or closest_distance > distance:
                                closets_idx = idx
                                closest_distance = distance
                    new_type, new_id = container.name_obj[name][closets_idx]
                    obj_parent_tags = container.objects[new_type][new_id]
                    name_lang = obj_parent_tags[f'name:{container.lang}']
                    if name != name_lang:
                        container.updates[osm_type][osm_id][tag] = name_lang
    log('STAT:', 'total objects for update',
        sum(len(objects) for objects in container.updates.values()))
    log('STAT:', 'total tags for update',
        sum(len(tags) for objects in container.updates.values() for tags in objects.values()))


@log_time
def find_main_updates(container: Container, input_file: str):
    handler = MainHandler(container)
    main_pbf = osmium_tags_filter(input_file, container.main_tags)
    handler.apply_buffer(main_pbf, TYPE_OSM_PBF)


@log_time
def update(container: Container, input_file: str, output_format: str):
    keep_pbf = osmium_removeid(
        input_file,
        nodes=container.updates[NODE].keys(),
        ways=container.updates[WAY].keys(),
        rels=container.updates[REL].keys(),
    )
    update_pbf = osmium_getid(
        input_file,
        nodes=container.updates[NODE].keys(),
        ways=container.updates[WAY].keys(),
        rels=container.updates[REL].keys(),
    )
    with tempfile.TemporaryDirectory() as tmp:
        name = os.path.join(tmp, f'updated.{TYPE_OSM_PBF}')
        writer = osmium.SimpleWriter(name)
        UpdateHandler(container, writer).apply_buffer(update_pbf, TYPE_OSM_PBF)
        writer.close()
        result = osmium_merge(keep_pbf, name, output_format=output_format)
    return result


@log_time
def main(
        main_tags: Iterable[str],
        dep_tags: Iterable[str],
        lang: str,
        input_file: str,
        output_file: str,
        output_format: Optional[str],
):
    log('platform:', sys.platform)
    log('python version:', sys.version)
    log('shapely version:', shapely.__version__)
    log('pyosmium version:', osmium.version.pyosmium_release)
    log('osmium version:', osmium_version().decode('utf8'))

    try:
        if output_format is None:
            output_format = osmium_fileformat(input_file)

        container = Container(frozenset(main_tags), frozenset(dep_tags), lang)
        collect_dependencies(container, input_file)
        collect_parent(container, input_file)
        build_geoms(container, input_file)
        build_index(container)
        find_dependency_parent_updates(container)
        find_main_updates(container, input_file)
        result = update(container, input_file, output_format)
        with open(output_file, 'wb') as h:
            h.write(result)
    except subprocess.CalledProcessError as err:
        print(err.args, err.returncode, err.stderr.decode('utf8'))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='osm_back.py',
        description='Update dependant tag to parent on specified language.')
    parser.add_argument('-T', '--main-tag', dest='main_tags', nargs='+', default=DEFAULT_MAIN_TAGS,
                        help='Main tags for update. Can be "name" and etc.')
    parser.add_argument('-t', '--dep-tag', dest='dep_tags', nargs='+', default=DEFAULT_DEPENDANT_TAGS,
                        help='Dependency tags for update. Can be "addr:street" and etc.')
    parser.add_argument('-l', '--lang', required=True, help='Language to update to. Can be "be" or "ru".')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-O', '--overwrite', action='store_true',
                        help='Allow an existing output file to be overwritten.')
    group.add_argument('-o', '--output', dest='output_file', help='Name of the output file.')
    parser.add_argument('-f', '--output-format', help='The format of the output file.')
    parser.add_argument('OSM_FILE')
    args = parser.parse_args()

    main(
        main_tags=args.main_tags,
        dep_tags=args.dep_tags,
        lang=args.lang,
        input_file=args.OSM_FILE,
        output_file=args.OSM_FILE if args.overwrite else args.output_file,
        output_format=args.output_format,
    )
