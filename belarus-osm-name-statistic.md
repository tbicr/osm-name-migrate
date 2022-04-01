# Аналіз дадзеных тэгу name у ОСМ Беларусі

## Зьмест

- Праблематыка
- Спампуем дамп ОСМ
- Усталёўваем залежанасьцьі
- Пошук сувязей дзеля падтрыманьня спасылачнай цэласнасьці

## Праблематыка

У беларускім ОСМ шырока выкарыстоўваюцца беларуская і расейская мова, для іх ёсьць адпаведнікі `name:be` і `name:ru`, таксама мовы выкарыстоўваюцца ў агульных тэгах як `name`, `addr:*` і іншых. Праблематка выкарыстоўваньня аднае, ці іншае, ці абедзьвух моваў апісанае тут https://wiki.openstreetmap.org/wiki/BE:Belarus_language_issues. Незалежна ад варыянту выкарыстоўваньня мовы павінны вытрымлівацца наступныя правілы: пошук на любое мове мусіць працаваць, павінна быць магчымасьць паказываць подпісы на любой мове (ці ў арыгінале, але гэтае правіла зараз не выконваецца), павінна захоўвацца спасылкавая цэласнасьць (што можа ўплываць на папярэднія два пункты).

Гэты аналіз ставіць мэтаю знайсьці адпаведныя катэгорыі і тэгі якія ўтрымліваюць кірылічныя значэньні тэгу name і падлічыць запаўняльнасьць тэгаў name:be, name:ru.

## Спампуем дамп ОСМ


```python
!wget https://download.geofabrik.de/europe/belarus-latest.osm.pbf
```

    --2022-04-01 19:26:40--  https://download.geofabrik.de/europe/belarus-latest.osm.pbf
    Resolving download.geofabrik.de (download.geofabrik.de)... 95.216.28.113, 116.202.112.212
    Connecting to download.geofabrik.de (download.geofabrik.de)|95.216.28.113|:443... connected.
    HTTP request sent, awaiting response... 200 OK
    Length: 256830245 (245M) [application/octet-stream]
    Saving to: ‘belarus-latest.osm.pbf.1’
    
    belarus-latest.osm. 100%[===================>] 244.93M  3.60MB/s    in 66s     
    
    2022-04-01 19:27:46 (3.72 MB/s) - ‘belarus-latest.osm.pbf.1’ saved [256830245/256830245]
    


## Загрузім дамп у postgis
- патрэбна толькі калі хочам атрымаць больш дакладныя дадзеныя, але можа не ўтрымліваць некаторыя дачыненьні


```python
!PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_POST -U $POSTGRES_USER -d $POSTGRES_DB  -c "CREATE EXTENSION IF NOT EXISTS hstore"
!PGPASSWORD=$POSTGRES_PASSWORD osm2pgsql -H $POSTGRES_HOST -P $POSTGRES_POST -U $POSTGRES_USER -d $POSTGRES_DB -v -m -j -G -x --latlong --hstore-add-index -C $OSM2PGSQL_CACHE -S /usr/share/osm2pgsql/default.style belarus-latest.osm.pbf
```

    NOTICE:  extension "hstore" already exists, skipping
    CREATE EXTENSION
    2022-04-01 21:53:03  osm2pgsql version 1.6.0
    2022-04-01 21:53:03  [0] Database version: 14.2
    2022-04-01 21:53:03  [0] PostGIS version: 3.2
    2022-04-01 21:53:03  [0] Reading file: belarus-latest.osm.pbf
    2022-04-01 21:53:03  [0] Started pool with 4 threads.
    2022-04-01 21:53:03  [0] Using projection SRS 4326 (Latlong)
    2022-04-01 21:53:03  [0] Using built-in tag transformations
    2022-04-01 21:53:03  [0] Middle 'ram' options:
    2022-04-01 21:53:03  [0]   locations: true
    2022-04-01 21:53:03  [0]   way_nodes: true
    2022-04-01 21:53:03  [0]   nodes: false
    2022-04-01 21:53:03  [0]   untagged_nodes: true
    2022-04-01 21:53:03  [0]   ways: false
    2022-04-01 21:53:03  [0]   relations: false
    2022-04-01 21:53:03  [0] Setting up table 'planet_osm_point'
    2022-04-01 21:53:03  [0] Setting up table 'planet_osm_line'
    2022-04-01 21:53:03  [0] Setting up table 'planet_osm_polygon'
    2022-04-01 21:53:03  [0] Setting up table 'planet_osm_roads'
    2022-04-01 21:54:26  [0] Reading input files done in 83s (1m 23s).                        
    2022-04-01 21:54:26  [0]   Processed 30656445 nodes in 28s - 1095k/s
    2022-04-01 21:54:26  [0]   Processed 4340833 ways in 49s - 89k/s
    2022-04-01 21:54:26  [0]   Processed 64186 relations in 6s - 11k/s
    2022-04-01 21:54:26  [0] Overall memory usage: peak=1400MByte current=1350MByte
    2022-04-01 21:54:27  [0] Middle 'ram': Node locations: size=30656445 bytes=296M
    2022-04-01 21:54:27  [1] Starting task...
    2022-04-01 21:54:27  [2] Starting task...
    2022-04-01 21:54:27  [0] Middle 'ram': Way nodes data: size=79406738 capacity=125829120 bytes=120M
    2022-04-01 21:54:27  [0] Middle 'ram': Way nodes index: size=4340833 capacity=7340032 bytes=56M
    2022-04-01 21:54:27  [0] Middle 'ram': Object data: size=0 capacity=1048576 bytes=1M
    2022-04-01 21:54:27  [0] Middle 'ram': Object indexes: size=0 capacity=0 bytes=0M
    2022-04-01 21:54:27  [0] Middle 'ram': Memory used overall: 473MBytes
    2022-04-01 21:54:27  [3] Starting task...
    2022-04-01 21:54:27  [1] Clustering table 'planet_osm_point' by geometry...
    2022-04-01 21:54:27  [4] Starting task...
    2022-04-01 21:54:27  [4] Clustering table 'planet_osm_polygon' by geometry...
    2022-04-01 21:54:27  [3] Clustering table 'planet_osm_roads' by geometry...
    2022-04-01 21:54:27  [2] Clustering table 'planet_osm_line' by geometry...
    2022-04-01 21:54:27  [2] Using native order for clustering table 'planet_osm_line'
    2022-04-01 21:54:27  [1] Using native order for clustering table 'planet_osm_point'
    2022-04-01 21:54:27  [3] Using native order for clustering table 'planet_osm_roads'
    2022-04-01 21:54:27  [4] Using native order for clustering table 'planet_osm_polygon'
    2022-04-01 21:54:33  [3] Creating geometry index on table 'planet_osm_roads'...
    2022-04-01 21:54:36  [3] Creating hstore indexes on table 'planet_osm_roads'...
    2022-04-01 21:54:45  [1] Creating geometry index on table 'planet_osm_point'...
    2022-04-01 21:54:47  [3] Analyzing table 'planet_osm_roads'...
    2022-04-01 21:54:49  [3] Done task in 22348ms.
    2022-04-01 21:54:59  [2] Creating geometry index on table 'planet_osm_line'...
    2022-04-01 21:55:03  [1] Creating hstore indexes on table 'planet_osm_point'...
    2022-04-01 21:55:21  [4] Creating geometry index on table 'planet_osm_polygon'...
    2022-04-01 21:55:30  [1] Analyzing table 'planet_osm_point'...
    2022-04-01 21:55:31  [2] Creating hstore indexes on table 'planet_osm_line'...
    2022-04-01 21:55:32  [1] Done task in 64764ms.
    2022-04-01 21:55:32  [0] All postprocessing on table 'planet_osm_point' done in 64s (1m 4s).
    2022-04-01 21:56:04  [2] Analyzing table 'planet_osm_line'...
    2022-04-01 21:56:05  [2] Done task in 98179ms.
    2022-04-01 21:56:05  [0] All postprocessing on table 'planet_osm_line' done in 98s (1m 38s).
    2022-04-01 21:56:31  [4] Creating hstore indexes on table 'planet_osm_polygon'...
    2022-04-01 21:57:57  [4] Analyzing table 'planet_osm_polygon'...
    2022-04-01 21:57:58  [4] Done task in 211805ms.
    2022-04-01 21:57:58  [0] All postprocessing on table 'planet_osm_polygon' done in 211s (3m 31s).
    2022-04-01 21:57:58  [0] All postprocessing on table 'planet_osm_roads' done in 22s.
    2022-04-01 21:57:59  [0] Overall memory usage: peak=1400MByte current=792MByte
    2022-04-01 21:57:59  [0] osm2pgsql took 296s (4m 56s) overall.


## Усталюем залежнасьці


```python
!pip install pandas matplotlib psycopg2-binary https://github.com/lechup/imposm-parser/archive/python3.zip
```

    Collecting https://github.com/lechup/imposm-parser/archive/python3.zip
      Using cached https://github.com/lechup/imposm-parser/archive/python3.zip
      Preparing metadata (setup.py) ... [?25ldone
    [33mWARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv[0m[33m
    [0m[?25h

## Вызначым катэгорыі


```python
import os
from collections import defaultdict, Counter

from imposm.parser import OSMParser
import psycopg2

import pandas as pd
pd.set_option('display.max_rows', None)


cirylic_chars = frozenset('абвгдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГДЕЁЖЗІИІЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ')

```


```python
categories_rules = {
    'place': [
        ['place', 'city'],
        ['place', 'town'],
        ['place', 'village'],
        ['place', 'hamlet'],
        ['place', 'isolated_dwelling'],
        ['place', 'farm'],
        ['place', 'allotments'],
    ],
    'locality': [
        ['place', 'locality'],
        ['abandoned:place', None],
    ],
    'suburb': [
        ['landuse', 'commercial'],
        ['landuse', 'construction'],
        ['landuse', 'education'],
        ['landuse', 'industrial'],
        ['landuse', 'residential'],
        ['landuse', 'retail'],
        ['landuse', None],
        ['place', None],
        ['residential', None],
        ['industrial', None],
    ],
    'admin': [
        ['boundary', 'administrative'],
        ['admin_level', '2'],
        ['admin_level', '4'],
        ['admin_level', '6'],
        ['admin_level', '8'],
        ['admin_level', '9'],
        ['admin_level', '10'],
        ['admin_level', None],
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
    ],
    'public_transport': [
        ['highway', 'bus_stop'],
        ['public_transport', None],
        ['route', None],
        ['type', 'route'],
        ['railway', None],
        ['route_master', None],
    ],
    'infrastructure': [
        ['tunnel', None],
        ['barrier', None],
        ['power', None],
        ['bridge', None],
        ['substation', None],
        ['emergency', None],
        ['ele', None],
        ['man_made', None],
        ['embankment', None],
    ],
    'amenity': [
        ['amenity', 'place_of_worship'],
        ['amenity', 'school'],
        ['amenity', 'kindergarten'],
#         ['amenity', 'cafe'],
#         ['amenity', 'atm'],
#         ['amenity', 'pharmacy'],
#         ['amenity', 'bank'],
#         ['amenity', 'post_office'],
#         ['amenity', 'fast_food'],
#         ['amenity', 'fuel'],
#         ['amenity', 'community_centre'],
#         ['amenity', 'hospital'],
#         ['amenity', 'police'],
#         ['amenity', 'restaurant'],
#         ['amenity', 'clinic'],
#         ['amenity', 'doctors'],
#         ['amenity', 'library'],
#         ['amenity', 'bar'],
        ['amenity', None],
        ['shop', None],
        ['leisure', None],
        ['sport', None],
        ['craft', 'shoemaker'],
        ['clothes', None],
    ],
    'government': [
        ['healthcare', None],
        ['office', 'government'],
        ['government', None],
        ['military', None],
    ],
    'office': [
        ['office', None],
    ],
    'building': [
        ['building', 'industrial'],
        ['building', 'service'],
        ['building', 'retail'],
        ['building', 'school'],
        ['building', 'kindergarten'],
        ['building', 'commercial'],
        ['building', 'church'],
        ['building', 'warehouse'],
        ['building', 'public'],
        ['building', 'dormitory'],
        ['building', 'hospital'],
        ['building', 'warehouse'],
        ['building', None],
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
    'water': [
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
    'natural': [
        ['natural', None],
        ['place', 'island'],
        ['place', 'islet'],
    ],
}

usage = defaultdict(set)
categories_rules2 = {}
for category, group in categories_rules.items():
    if category not in categories_rules2:
        categories_rules2[category] = []
    for tag, value in group:
        if value is not None:
            categories_rules2[category].append([tag, True, {value}])
            usage[tag].add(value)                          
for category, group in categories_rules.items():
    if category not in categories_rules2:
        categories_rules2[category] = []
    for tag, value in group:
        if value is None:
            categories_rules2[category].append([tag, False, usage[tag]])
```

## Падлічам статыстыку для дампу
- дамп падліча ўсе дадзеныя, але можа быць трошкі недакладным таму што не ўлічвае грубую абрэзку Беларусі


```python
key_counter = defaultdict(lambda: defaultdict(list))

categories_tags = {}
categories_rules_tags_set = {}
for category, group in categories_rules2.items():
    for tag, eq, values in group:
        if tag not in categories_tags:
            categories_tags[tag] = {category}
        else:
            categories_tags[tag].add(category)

            
def process(params):
    for _, tags, _ in params:
        if 'name' not in tags:
            continue
        if not (frozenset(tags['name']) & cirylic_chars):
            continue
        categories = {category for tag in categories_tags.keys() & tags.keys() for category in categories_tags[tag]}
        for tag in ['name', 'name:be', 'name:ru']:
            if tag not in tags:
                continue
            value = tags[tag]
            cyr = frozenset(value) & cirylic_chars
            if not cyr:
                continue
            match = False
            for category in categories:
                group = categories_rules2[category]
                category_match = False
                for i, (k, eq, vv) in enumerate(group):
                    if k not in tags:
                        continue
                    if eq:
                        if tags[k] in vv:
                            if not category_match:
                                key_counter[(category,)][tag].append(value)
                                match = category_match = True
                            key_counter[(category, i)][tag].append(value)   
                    else:
                        if tags[k] not in vv:
                            if not category_match:
                                key_counter[(category,)][tag].append(value)
                                match = category_match = True
                            key_counter[(category, i)][tag].append(value)   
            if not match:
                key_counter[('other',)][tag].append(value)
                

OSMParser(
    nodes_callback=process,
    ways_callback=process,
    relations_callback=process,
).parse('belarus-latest.osm.pbf')


# cirylic tag values count
data = []
for c in list(categories_rules) + ['other']:
    name_cnt = len(key_counter[(c,)]['name'])
    name_uniq = len(set(key_counter[(c,)]['name']))
    name_be_cnt = len(key_counter[(c,)]['name:be'])
    name_be_uniq = len(set(key_counter[(c,)]['name:be']))
    name_ru_cnt = len(key_counter[(c,)]['name:ru'])
    name_ru_uniq = len(set(key_counter[(c,)]['name:ru']))
    data.append([
        '#', c, 
        name_cnt, name_be_cnt, name_ru_cnt, name_be_cnt/name_cnt, name_ru_cnt/name_cnt,
        name_uniq, name_be_uniq, name_ru_uniq, name_be_uniq/name_uniq, name_ru_uniq/name_uniq,
    ])
    if c == 'other':
        continue
    for i, (k, eq, vv) in enumerate(categories_rules2[c]):
        if eq:
            tag = f'{k} = {list(vv)[0]}'
        else:
            tag = f'{k} = *'
        name_cnt = len(key_counter[(c, i)]['name'])
        name_uniq = len(set(key_counter[(c, i)]['name']))
        name_be_cnt = len(key_counter[(c, i)]['name:be'])
        name_be_uniq = len(set(key_counter[(c, i)]['name:be']))
        name_ru_cnt = len(key_counter[(c, i)]['name:ru'])
        name_ru_uniq = len(set(key_counter[(c, i)]['name:ru']))
        data.append([
            '', tag, 
            name_cnt, name_be_cnt, name_ru_cnt, name_be_cnt/name_cnt, name_ru_cnt/name_cnt,
            name_uniq, name_be_uniq, name_ru_uniq, name_be_uniq/name_uniq, name_ru_uniq/name_uniq,
        ])
```


```python
df = pd.DataFrame(data, columns=[
    'lvl', 'category', 
    'all name', 'all name:be', 'all name:ru', 'all name:be%', 'all name:ru%',
    'uniq name', 'uniq name:be', 'uniq name:ru', 'uniq name:be%', 'uniq name:ru%',
])
df.to_csv('dump.csv')
df.style.set_properties(**{'text-align': 'left'}).background_gradient('YlOrRd', subset=[
    'all name:be%', 'all name:ru%', 'uniq name:be%', 'uniq name:ru%',
]).apply(lambda row: [("font-weight: bold" if row.loc['lvl'] == '#' else '') for _ in row], axis=1)
```





<table id="T_a86e0">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_a86e0_level0_col0" class="col_heading level0 col0" >lvl</th>
      <th id="T_a86e0_level0_col1" class="col_heading level0 col1" >category</th>
      <th id="T_a86e0_level0_col2" class="col_heading level0 col2" >all name</th>
      <th id="T_a86e0_level0_col3" class="col_heading level0 col3" >all name:be</th>
      <th id="T_a86e0_level0_col4" class="col_heading level0 col4" >all name:ru</th>
      <th id="T_a86e0_level0_col5" class="col_heading level0 col5" >all name:be%</th>
      <th id="T_a86e0_level0_col6" class="col_heading level0 col6" >all name:ru%</th>
      <th id="T_a86e0_level0_col7" class="col_heading level0 col7" >uniq name</th>
      <th id="T_a86e0_level0_col8" class="col_heading level0 col8" >uniq name:be</th>
      <th id="T_a86e0_level0_col9" class="col_heading level0 col9" >uniq name:ru</th>
      <th id="T_a86e0_level0_col10" class="col_heading level0 col10" >uniq name:be%</th>
      <th id="T_a86e0_level0_col11" class="col_heading level0 col11" >uniq name:ru%</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_a86e0_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_a86e0_row0_col0" class="data row0 col0" >#</td>
      <td id="T_a86e0_row0_col1" class="data row0 col1" >place</td>
      <td id="T_a86e0_row0_col2" class="data row0 col2" >47238</td>
      <td id="T_a86e0_row0_col3" class="data row0 col3" >45398</td>
      <td id="T_a86e0_row0_col4" class="data row0 col4" >46900</td>
      <td id="T_a86e0_row0_col5" class="data row0 col5" >0.961048</td>
      <td id="T_a86e0_row0_col6" class="data row0 col6" >0.992845</td>
      <td id="T_a86e0_row0_col7" class="data row0 col7" >16794</td>
      <td id="T_a86e0_row0_col8" class="data row0 col8" >15860</td>
      <td id="T_a86e0_row0_col9" class="data row0 col9" >16616</td>
      <td id="T_a86e0_row0_col10" class="data row0 col10" >0.944385</td>
      <td id="T_a86e0_row0_col11" class="data row0 col11" >0.989401</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_a86e0_row1_col0" class="data row1 col0" ></td>
      <td id="T_a86e0_row1_col1" class="data row1 col1" >place = city</td>
      <td id="T_a86e0_row1_col2" class="data row1 col2" >31</td>
      <td id="T_a86e0_row1_col3" class="data row1 col3" >31</td>
      <td id="T_a86e0_row1_col4" class="data row1 col4" >31</td>
      <td id="T_a86e0_row1_col5" class="data row1 col5" >1.000000</td>
      <td id="T_a86e0_row1_col6" class="data row1 col6" >1.000000</td>
      <td id="T_a86e0_row1_col7" class="data row1 col7" >16</td>
      <td id="T_a86e0_row1_col8" class="data row1 col8" >16</td>
      <td id="T_a86e0_row1_col9" class="data row1 col9" >16</td>
      <td id="T_a86e0_row1_col10" class="data row1 col10" >1.000000</td>
      <td id="T_a86e0_row1_col11" class="data row1 col11" >1.000000</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_a86e0_row2_col0" class="data row2 col0" ></td>
      <td id="T_a86e0_row2_col1" class="data row2 col1" >place = town</td>
      <td id="T_a86e0_row2_col2" class="data row2 col2" >274</td>
      <td id="T_a86e0_row2_col3" class="data row2 col3" >272</td>
      <td id="T_a86e0_row2_col4" class="data row2 col4" >273</td>
      <td id="T_a86e0_row2_col5" class="data row2 col5" >0.992701</td>
      <td id="T_a86e0_row2_col6" class="data row2 col6" >0.996350</td>
      <td id="T_a86e0_row2_col7" class="data row2 col7" >138</td>
      <td id="T_a86e0_row2_col8" class="data row2 col8" >138</td>
      <td id="T_a86e0_row2_col9" class="data row2 col9" >138</td>
      <td id="T_a86e0_row2_col10" class="data row2 col10" >1.000000</td>
      <td id="T_a86e0_row2_col11" class="data row2 col11" >1.000000</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_a86e0_row3_col0" class="data row3 col0" ></td>
      <td id="T_a86e0_row3_col1" class="data row3 col1" >place = village</td>
      <td id="T_a86e0_row3_col2" class="data row3 col2" >5031</td>
      <td id="T_a86e0_row3_col3" class="data row3 col3" >4987</td>
      <td id="T_a86e0_row3_col4" class="data row3 col4" >5015</td>
      <td id="T_a86e0_row3_col5" class="data row3 col5" >0.991254</td>
      <td id="T_a86e0_row3_col6" class="data row3 col6" >0.996820</td>
      <td id="T_a86e0_row3_col7" class="data row3 col7" >2227</td>
      <td id="T_a86e0_row3_col8" class="data row3 col8" >2207</td>
      <td id="T_a86e0_row3_col9" class="data row3 col9" >2214</td>
      <td id="T_a86e0_row3_col10" class="data row3 col10" >0.991019</td>
      <td id="T_a86e0_row3_col11" class="data row3 col11" >0.994163</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_a86e0_row4_col0" class="data row4 col0" ></td>
      <td id="T_a86e0_row4_col1" class="data row4 col1" >place = hamlet</td>
      <td id="T_a86e0_row4_col2" class="data row4 col2" >38803</td>
      <td id="T_a86e0_row4_col3" class="data row4 col3" >38564</td>
      <td id="T_a86e0_row4_col4" class="data row4 col4" >38611</td>
      <td id="T_a86e0_row4_col5" class="data row4 col5" >0.993841</td>
      <td id="T_a86e0_row4_col6" class="data row4 col6" >0.995052</td>
      <td id="T_a86e0_row4_col7" class="data row4 col7" >13578</td>
      <td id="T_a86e0_row4_col8" class="data row4 col8" >13622</td>
      <td id="T_a86e0_row4_col9" class="data row4 col9" >13505</td>
      <td id="T_a86e0_row4_col10" class="data row4 col10" >1.003241</td>
      <td id="T_a86e0_row4_col11" class="data row4 col11" >0.994624</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_a86e0_row5_col0" class="data row5 col0" ></td>
      <td id="T_a86e0_row5_col1" class="data row5 col1" >place = isolated_dwelling</td>
      <td id="T_a86e0_row5_col2" class="data row5 col2" >1265</td>
      <td id="T_a86e0_row5_col3" class="data row5 col3" >1178</td>
      <td id="T_a86e0_row5_col4" class="data row5 col4" >1233</td>
      <td id="T_a86e0_row5_col5" class="data row5 col5" >0.931225</td>
      <td id="T_a86e0_row5_col6" class="data row5 col6" >0.974704</td>
      <td id="T_a86e0_row5_col7" class="data row5 col7" >640</td>
      <td id="T_a86e0_row5_col8" class="data row5 col8" >590</td>
      <td id="T_a86e0_row5_col9" class="data row5 col9" >618</td>
      <td id="T_a86e0_row5_col10" class="data row5 col10" >0.921875</td>
      <td id="T_a86e0_row5_col11" class="data row5 col11" >0.965625</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_a86e0_row6_col0" class="data row6 col0" ></td>
      <td id="T_a86e0_row6_col1" class="data row6 col1" >place = farm</td>
      <td id="T_a86e0_row6_col2" class="data row6 col2" >11</td>
      <td id="T_a86e0_row6_col3" class="data row6 col3" >4</td>
      <td id="T_a86e0_row6_col4" class="data row6 col4" >4</td>
      <td id="T_a86e0_row6_col5" class="data row6 col5" >0.363636</td>
      <td id="T_a86e0_row6_col6" class="data row6 col6" >0.363636</td>
      <td id="T_a86e0_row6_col7" class="data row6 col7" >10</td>
      <td id="T_a86e0_row6_col8" class="data row6 col8" >3</td>
      <td id="T_a86e0_row6_col9" class="data row6 col9" >3</td>
      <td id="T_a86e0_row6_col10" class="data row6 col10" >0.300000</td>
      <td id="T_a86e0_row6_col11" class="data row6 col11" >0.300000</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_a86e0_row7_col0" class="data row7 col0" ></td>
      <td id="T_a86e0_row7_col1" class="data row7 col1" >place = allotments</td>
      <td id="T_a86e0_row7_col2" class="data row7 col2" >1823</td>
      <td id="T_a86e0_row7_col3" class="data row7 col3" >362</td>
      <td id="T_a86e0_row7_col4" class="data row7 col4" >1733</td>
      <td id="T_a86e0_row7_col5" class="data row7 col5" >0.198574</td>
      <td id="T_a86e0_row7_col6" class="data row7 col6" >0.950631</td>
      <td id="T_a86e0_row7_col7" class="data row7 col7" >1363</td>
      <td id="T_a86e0_row7_col8" class="data row7 col8" >298</td>
      <td id="T_a86e0_row7_col9" class="data row7 col9" >1294</td>
      <td id="T_a86e0_row7_col10" class="data row7 col10" >0.218635</td>
      <td id="T_a86e0_row7_col11" class="data row7 col11" >0.949376</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_a86e0_row8_col0" class="data row8 col0" >#</td>
      <td id="T_a86e0_row8_col1" class="data row8 col1" >locality</td>
      <td id="T_a86e0_row8_col2" class="data row8 col2" >11997</td>
      <td id="T_a86e0_row8_col3" class="data row8 col3" >2731</td>
      <td id="T_a86e0_row8_col4" class="data row8 col4" >11382</td>
      <td id="T_a86e0_row8_col5" class="data row8 col5" >0.227640</td>
      <td id="T_a86e0_row8_col6" class="data row8 col6" >0.948737</td>
      <td id="T_a86e0_row8_col7" class="data row8 col7" >8406</td>
      <td id="T_a86e0_row8_col8" class="data row8 col8" >2061</td>
      <td id="T_a86e0_row8_col9" class="data row8 col9" >7972</td>
      <td id="T_a86e0_row8_col10" class="data row8 col10" >0.245182</td>
      <td id="T_a86e0_row8_col11" class="data row8 col11" >0.948370</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_a86e0_row9_col0" class="data row9 col0" ></td>
      <td id="T_a86e0_row9_col1" class="data row9 col1" >place = locality</td>
      <td id="T_a86e0_row9_col2" class="data row9 col2" >11954</td>
      <td id="T_a86e0_row9_col3" class="data row9 col3" >2690</td>
      <td id="T_a86e0_row9_col4" class="data row9 col4" >11339</td>
      <td id="T_a86e0_row9_col5" class="data row9 col5" >0.225029</td>
      <td id="T_a86e0_row9_col6" class="data row9 col6" >0.948553</td>
      <td id="T_a86e0_row9_col7" class="data row9 col7" >8383</td>
      <td id="T_a86e0_row9_col8" class="data row9 col8" >2031</td>
      <td id="T_a86e0_row9_col9" class="data row9 col9" >7949</td>
      <td id="T_a86e0_row9_col10" class="data row9 col10" >0.242276</td>
      <td id="T_a86e0_row9_col11" class="data row9 col11" >0.948229</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_a86e0_row10_col0" class="data row10 col0" ></td>
      <td id="T_a86e0_row10_col1" class="data row10 col1" >abandoned:place = *</td>
      <td id="T_a86e0_row10_col2" class="data row10 col2" >3035</td>
      <td id="T_a86e0_row10_col3" class="data row10 col3" >2068</td>
      <td id="T_a86e0_row10_col4" class="data row10 col4" >3001</td>
      <td id="T_a86e0_row10_col5" class="data row10 col5" >0.681384</td>
      <td id="T_a86e0_row10_col6" class="data row10 col6" >0.988797</td>
      <td id="T_a86e0_row10_col7" class="data row10 col7" >2198</td>
      <td id="T_a86e0_row10_col8" class="data row10 col8" >1551</td>
      <td id="T_a86e0_row10_col9" class="data row10 col9" >2170</td>
      <td id="T_a86e0_row10_col10" class="data row10 col10" >0.705641</td>
      <td id="T_a86e0_row10_col11" class="data row10 col11" >0.987261</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_a86e0_row11_col0" class="data row11 col0" >#</td>
      <td id="T_a86e0_row11_col1" class="data row11 col1" >suburb</td>
      <td id="T_a86e0_row11_col2" class="data row11 col2" >14729</td>
      <td id="T_a86e0_row11_col3" class="data row11 col3" >3202</td>
      <td id="T_a86e0_row11_col4" class="data row11 col4" >5021</td>
      <td id="T_a86e0_row11_col5" class="data row11 col5" >0.217394</td>
      <td id="T_a86e0_row11_col6" class="data row11 col6" >0.340892</td>
      <td id="T_a86e0_row11_col7" class="data row11 col7" >11011</td>
      <td id="T_a86e0_row11_col8" class="data row11 col8" >2433</td>
      <td id="T_a86e0_row11_col9" class="data row11 col9" >3825</td>
      <td id="T_a86e0_row11_col10" class="data row11 col10" >0.220961</td>
      <td id="T_a86e0_row11_col11" class="data row11 col11" >0.347380</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_a86e0_row12_col0" class="data row12 col0" ></td>
      <td id="T_a86e0_row12_col1" class="data row12 col1" >landuse = commercial</td>
      <td id="T_a86e0_row12_col2" class="data row12 col2" >179</td>
      <td id="T_a86e0_row12_col3" class="data row12 col3" >24</td>
      <td id="T_a86e0_row12_col4" class="data row12 col4" >30</td>
      <td id="T_a86e0_row12_col5" class="data row12 col5" >0.134078</td>
      <td id="T_a86e0_row12_col6" class="data row12 col6" >0.167598</td>
      <td id="T_a86e0_row12_col7" class="data row12 col7" >163</td>
      <td id="T_a86e0_row12_col8" class="data row12 col8" >23</td>
      <td id="T_a86e0_row12_col9" class="data row12 col9" >30</td>
      <td id="T_a86e0_row12_col10" class="data row12 col10" >0.141104</td>
      <td id="T_a86e0_row12_col11" class="data row12 col11" >0.184049</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_a86e0_row13_col0" class="data row13 col0" ></td>
      <td id="T_a86e0_row13_col1" class="data row13 col1" >landuse = construction</td>
      <td id="T_a86e0_row13_col2" class="data row13 col2" >166</td>
      <td id="T_a86e0_row13_col3" class="data row13 col3" >18</td>
      <td id="T_a86e0_row13_col4" class="data row13 col4" >20</td>
      <td id="T_a86e0_row13_col5" class="data row13 col5" >0.108434</td>
      <td id="T_a86e0_row13_col6" class="data row13 col6" >0.120482</td>
      <td id="T_a86e0_row13_col7" class="data row13 col7" >155</td>
      <td id="T_a86e0_row13_col8" class="data row13 col8" >17</td>
      <td id="T_a86e0_row13_col9" class="data row13 col9" >20</td>
      <td id="T_a86e0_row13_col10" class="data row13 col10" >0.109677</td>
      <td id="T_a86e0_row13_col11" class="data row13 col11" >0.129032</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_a86e0_row14_col0" class="data row14 col0" ></td>
      <td id="T_a86e0_row14_col1" class="data row14 col1" >landuse = education</td>
      <td id="T_a86e0_row14_col2" class="data row14 col2" >804</td>
      <td id="T_a86e0_row14_col3" class="data row14 col3" >153</td>
      <td id="T_a86e0_row14_col4" class="data row14 col4" >165</td>
      <td id="T_a86e0_row14_col5" class="data row14 col5" >0.190299</td>
      <td id="T_a86e0_row14_col6" class="data row14 col6" >0.205224</td>
      <td id="T_a86e0_row14_col7" class="data row14 col7" >796</td>
      <td id="T_a86e0_row14_col8" class="data row14 col8" >151</td>
      <td id="T_a86e0_row14_col9" class="data row14 col9" >164</td>
      <td id="T_a86e0_row14_col10" class="data row14 col10" >0.189698</td>
      <td id="T_a86e0_row14_col11" class="data row14 col11" >0.206030</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_a86e0_row15_col0" class="data row15 col0" ></td>
      <td id="T_a86e0_row15_col1" class="data row15 col1" >landuse = industrial</td>
      <td id="T_a86e0_row15_col2" class="data row15 col2" >4271</td>
      <td id="T_a86e0_row15_col3" class="data row15 col3" >363</td>
      <td id="T_a86e0_row15_col4" class="data row15 col4" >381</td>
      <td id="T_a86e0_row15_col5" class="data row15 col5" >0.084992</td>
      <td id="T_a86e0_row15_col6" class="data row15 col6" >0.089206</td>
      <td id="T_a86e0_row15_col7" class="data row15 col7" >3697</td>
      <td id="T_a86e0_row15_col8" class="data row15 col8" >333</td>
      <td id="T_a86e0_row15_col9" class="data row15 col9" >370</td>
      <td id="T_a86e0_row15_col10" class="data row15 col10" >0.090073</td>
      <td id="T_a86e0_row15_col11" class="data row15 col11" >0.100081</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_a86e0_row16_col0" class="data row16 col0" ></td>
      <td id="T_a86e0_row16_col1" class="data row16 col1" >landuse = residential</td>
      <td id="T_a86e0_row16_col2" class="data row16 col2" >869</td>
      <td id="T_a86e0_row16_col3" class="data row16 col3" >373</td>
      <td id="T_a86e0_row16_col4" class="data row16 col4" >338</td>
      <td id="T_a86e0_row16_col5" class="data row16 col5" >0.429229</td>
      <td id="T_a86e0_row16_col6" class="data row16 col6" >0.388953</td>
      <td id="T_a86e0_row16_col7" class="data row16 col7" >785</td>
      <td id="T_a86e0_row16_col8" class="data row16 col8" >354</td>
      <td id="T_a86e0_row16_col9" class="data row16 col9" >330</td>
      <td id="T_a86e0_row16_col10" class="data row16 col10" >0.450955</td>
      <td id="T_a86e0_row16_col11" class="data row16 col11" >0.420382</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_a86e0_row17_col0" class="data row17 col0" ></td>
      <td id="T_a86e0_row17_col1" class="data row17 col1" >landuse = retail</td>
      <td id="T_a86e0_row17_col2" class="data row17 col2" >236</td>
      <td id="T_a86e0_row17_col3" class="data row17 col3" >54</td>
      <td id="T_a86e0_row17_col4" class="data row17 col4" >60</td>
      <td id="T_a86e0_row17_col5" class="data row17 col5" >0.228814</td>
      <td id="T_a86e0_row17_col6" class="data row17 col6" >0.254237</td>
      <td id="T_a86e0_row17_col7" class="data row17 col7" >149</td>
      <td id="T_a86e0_row17_col8" class="data row17 col8" >35</td>
      <td id="T_a86e0_row17_col9" class="data row17 col9" >43</td>
      <td id="T_a86e0_row17_col10" class="data row17 col10" >0.234899</td>
      <td id="T_a86e0_row17_col11" class="data row17 col11" >0.288591</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_a86e0_row18_col0" class="data row18 col0" ></td>
      <td id="T_a86e0_row18_col1" class="data row18 col1" >landuse = *</td>
      <td id="T_a86e0_row18_col2" class="data row18 col2" >6173</td>
      <td id="T_a86e0_row18_col3" class="data row18 col3" >1052</td>
      <td id="T_a86e0_row18_col4" class="data row18 col4" >2555</td>
      <td id="T_a86e0_row18_col5" class="data row18 col5" >0.170420</td>
      <td id="T_a86e0_row18_col6" class="data row18 col6" >0.413899</td>
      <td id="T_a86e0_row18_col7" class="data row18 col7" >4215</td>
      <td id="T_a86e0_row18_col8" class="data row18 col8" >773</td>
      <td id="T_a86e0_row18_col9" class="data row18 col9" >2016</td>
      <td id="T_a86e0_row18_col10" class="data row18 col10" >0.183393</td>
      <td id="T_a86e0_row18_col11" class="data row18 col11" >0.478292</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_a86e0_row19_col0" class="data row19 col0" ></td>
      <td id="T_a86e0_row19_col1" class="data row19 col1" >place = *</td>
      <td id="T_a86e0_row19_col2" class="data row19 col2" >2074</td>
      <td id="T_a86e0_row19_col3" class="data row19 col3" >1241</td>
      <td id="T_a86e0_row19_col4" class="data row19 col4" >1560</td>
      <td id="T_a86e0_row19_col5" class="data row19 col5" >0.598361</td>
      <td id="T_a86e0_row19_col6" class="data row19 col6" >0.752170</td>
      <td id="T_a86e0_row19_col7" class="data row19 col7" >1440</td>
      <td id="T_a86e0_row19_col8" class="data row19 col8" >894</td>
      <td id="T_a86e0_row19_col9" class="data row19 col9" >1050</td>
      <td id="T_a86e0_row19_col10" class="data row19 col10" >0.620833</td>
      <td id="T_a86e0_row19_col11" class="data row19 col11" >0.729167</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_a86e0_row20_col0" class="data row20 col0" ></td>
      <td id="T_a86e0_row20_col1" class="data row20 col1" >residential = *</td>
      <td id="T_a86e0_row20_col2" class="data row20 col2" >693</td>
      <td id="T_a86e0_row20_col3" class="data row20 col3" >317</td>
      <td id="T_a86e0_row20_col4" class="data row20 col4" >284</td>
      <td id="T_a86e0_row20_col5" class="data row20 col5" >0.457431</td>
      <td id="T_a86e0_row20_col6" class="data row20 col6" >0.409812</td>
      <td id="T_a86e0_row20_col7" class="data row20 col7" >629</td>
      <td id="T_a86e0_row20_col8" class="data row20 col8" >300</td>
      <td id="T_a86e0_row20_col9" class="data row20 col9" >277</td>
      <td id="T_a86e0_row20_col10" class="data row20 col10" >0.476948</td>
      <td id="T_a86e0_row20_col11" class="data row20 col11" >0.440382</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_a86e0_row21_col0" class="data row21 col0" ></td>
      <td id="T_a86e0_row21_col1" class="data row21 col1" >industrial = *</td>
      <td id="T_a86e0_row21_col2" class="data row21 col2" >460</td>
      <td id="T_a86e0_row21_col3" class="data row21 col3" >34</td>
      <td id="T_a86e0_row21_col4" class="data row21 col4" >45</td>
      <td id="T_a86e0_row21_col5" class="data row21 col5" >0.073913</td>
      <td id="T_a86e0_row21_col6" class="data row21 col6" >0.097826</td>
      <td id="T_a86e0_row21_col7" class="data row21 col7" >368</td>
      <td id="T_a86e0_row21_col8" class="data row21 col8" >32</td>
      <td id="T_a86e0_row21_col9" class="data row21 col9" >43</td>
      <td id="T_a86e0_row21_col10" class="data row21 col10" >0.086957</td>
      <td id="T_a86e0_row21_col11" class="data row21 col11" >0.116848</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_a86e0_row22_col0" class="data row22 col0" >#</td>
      <td id="T_a86e0_row22_col1" class="data row22 col1" >admin</td>
      <td id="T_a86e0_row22_col2" class="data row22 col2" >25056</td>
      <td id="T_a86e0_row22_col3" class="data row22 col3" >24695</td>
      <td id="T_a86e0_row22_col4" class="data row22 col4" >24663</td>
      <td id="T_a86e0_row22_col5" class="data row22 col5" >0.985592</td>
      <td id="T_a86e0_row22_col6" class="data row22 col6" >0.984315</td>
      <td id="T_a86e0_row22_col7" class="data row22 col7" >16989</td>
      <td id="T_a86e0_row22_col8" class="data row22 col8" >16891</td>
      <td id="T_a86e0_row22_col9" class="data row22 col9" >16818</td>
      <td id="T_a86e0_row22_col10" class="data row22 col10" >0.994232</td>
      <td id="T_a86e0_row22_col11" class="data row22 col11" >0.989935</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_a86e0_row23_col0" class="data row23 col0" ></td>
      <td id="T_a86e0_row23_col1" class="data row23 col1" >boundary = administrative</td>
      <td id="T_a86e0_row23_col2" class="data row23 col2" >25054</td>
      <td id="T_a86e0_row23_col3" class="data row23 col3" >24693</td>
      <td id="T_a86e0_row23_col4" class="data row23 col4" >24661</td>
      <td id="T_a86e0_row23_col5" class="data row23 col5" >0.985591</td>
      <td id="T_a86e0_row23_col6" class="data row23 col6" >0.984314</td>
      <td id="T_a86e0_row23_col7" class="data row23 col7" >16989</td>
      <td id="T_a86e0_row23_col8" class="data row23 col8" >16891</td>
      <td id="T_a86e0_row23_col9" class="data row23 col9" >16818</td>
      <td id="T_a86e0_row23_col10" class="data row23 col10" >0.994232</td>
      <td id="T_a86e0_row23_col11" class="data row23 col11" >0.989935</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row24" class="row_heading level0 row24" >24</th>
      <td id="T_a86e0_row24_col0" class="data row24 col0" ></td>
      <td id="T_a86e0_row24_col1" class="data row24 col1" >admin_level = 2</td>
      <td id="T_a86e0_row24_col2" class="data row24 col2" >702</td>
      <td id="T_a86e0_row24_col3" class="data row24 col3" >638</td>
      <td id="T_a86e0_row24_col4" class="data row24 col4" >477</td>
      <td id="T_a86e0_row24_col5" class="data row24 col5" >0.908832</td>
      <td id="T_a86e0_row24_col6" class="data row24 col6" >0.679487</td>
      <td id="T_a86e0_row24_col7" class="data row24 col7" >109</td>
      <td id="T_a86e0_row24_col8" class="data row24 col8" >83</td>
      <td id="T_a86e0_row24_col9" class="data row24 col9" >85</td>
      <td id="T_a86e0_row24_col10" class="data row24 col10" >0.761468</td>
      <td id="T_a86e0_row24_col11" class="data row24 col11" >0.779817</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row25" class="row_heading level0 row25" >25</th>
      <td id="T_a86e0_row25_col0" class="data row25 col0" ></td>
      <td id="T_a86e0_row25_col1" class="data row25 col1" >admin_level = 4</td>
      <td id="T_a86e0_row25_col2" class="data row25 col2" >73</td>
      <td id="T_a86e0_row25_col3" class="data row25 col3" >65</td>
      <td id="T_a86e0_row25_col4" class="data row25 col4" >65</td>
      <td id="T_a86e0_row25_col5" class="data row25 col5" >0.890411</td>
      <td id="T_a86e0_row25_col6" class="data row25 col6" >0.890411</td>
      <td id="T_a86e0_row25_col7" class="data row25 col7" >40</td>
      <td id="T_a86e0_row25_col8" class="data row25 col8" >35</td>
      <td id="T_a86e0_row25_col9" class="data row25 col9" >37</td>
      <td id="T_a86e0_row25_col10" class="data row25 col10" >0.875000</td>
      <td id="T_a86e0_row25_col11" class="data row25 col11" >0.925000</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row26" class="row_heading level0 row26" >26</th>
      <td id="T_a86e0_row26_col0" class="data row26 col0" ></td>
      <td id="T_a86e0_row26_col1" class="data row26 col1" >admin_level = 6</td>
      <td id="T_a86e0_row26_col2" class="data row26 col2" >234</td>
      <td id="T_a86e0_row26_col3" class="data row26 col3" >213</td>
      <td id="T_a86e0_row26_col4" class="data row26 col4" >216</td>
      <td id="T_a86e0_row26_col5" class="data row26 col5" >0.910256</td>
      <td id="T_a86e0_row26_col6" class="data row26 col6" >0.923077</td>
      <td id="T_a86e0_row26_col7" class="data row26 col7" >189</td>
      <td id="T_a86e0_row26_col8" class="data row26 col8" >169</td>
      <td id="T_a86e0_row26_col9" class="data row26 col9" >173</td>
      <td id="T_a86e0_row26_col10" class="data row26 col10" >0.894180</td>
      <td id="T_a86e0_row26_col11" class="data row26 col11" >0.915344</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row27" class="row_heading level0 row27" >27</th>
      <td id="T_a86e0_row27_col0" class="data row27 col0" ></td>
      <td id="T_a86e0_row27_col1" class="data row27 col1" >admin_level = 8</td>
      <td id="T_a86e0_row27_col2" class="data row27 col2" >1353</td>
      <td id="T_a86e0_row27_col3" class="data row27 col3" >1306</td>
      <td id="T_a86e0_row27_col4" class="data row27 col4" >1307</td>
      <td id="T_a86e0_row27_col5" class="data row27 col5" >0.965262</td>
      <td id="T_a86e0_row27_col6" class="data row27 col6" >0.966001</td>
      <td id="T_a86e0_row27_col7" class="data row27 col7" >1234</td>
      <td id="T_a86e0_row27_col8" class="data row27 col8" >1195</td>
      <td id="T_a86e0_row27_col9" class="data row27 col9" >1192</td>
      <td id="T_a86e0_row27_col10" class="data row27 col10" >0.968395</td>
      <td id="T_a86e0_row27_col11" class="data row27 col11" >0.965964</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row28" class="row_heading level0 row28" >28</th>
      <td id="T_a86e0_row28_col0" class="data row28 col0" ></td>
      <td id="T_a86e0_row28_col1" class="data row28 col1" >admin_level = 9</td>
      <td id="T_a86e0_row28_col2" class="data row28 col2" >27</td>
      <td id="T_a86e0_row28_col3" class="data row28 col3" >26</td>
      <td id="T_a86e0_row28_col4" class="data row28 col4" >26</td>
      <td id="T_a86e0_row28_col5" class="data row28 col5" >0.962963</td>
      <td id="T_a86e0_row28_col6" class="data row28 col6" >0.962963</td>
      <td id="T_a86e0_row28_col7" class="data row28 col7" >14</td>
      <td id="T_a86e0_row28_col8" class="data row28 col8" >13</td>
      <td id="T_a86e0_row28_col9" class="data row28 col9" >13</td>
      <td id="T_a86e0_row28_col10" class="data row28 col10" >0.928571</td>
      <td id="T_a86e0_row28_col11" class="data row28 col11" >0.928571</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row29" class="row_heading level0 row29" >29</th>
      <td id="T_a86e0_row29_col0" class="data row29 col0" ></td>
      <td id="T_a86e0_row29_col1" class="data row29 col1" >admin_level = 10</td>
      <td id="T_a86e0_row29_col2" class="data row29 col2" >22634</td>
      <td id="T_a86e0_row29_col3" class="data row29 col3" >22440</td>
      <td id="T_a86e0_row29_col4" class="data row29 col4" >22565</td>
      <td id="T_a86e0_row29_col5" class="data row29 col5" >0.991429</td>
      <td id="T_a86e0_row29_col6" class="data row29 col6" >0.996951</td>
      <td id="T_a86e0_row29_col7" class="data row29 col7" >15469</td>
      <td id="T_a86e0_row29_col8" class="data row29 col8" >15495</td>
      <td id="T_a86e0_row29_col9" class="data row29 col9" >15419</td>
      <td id="T_a86e0_row29_col10" class="data row29 col10" >1.001681</td>
      <td id="T_a86e0_row29_col11" class="data row29 col11" >0.996768</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row30" class="row_heading level0 row30" >30</th>
      <td id="T_a86e0_row30_col0" class="data row30 col0" ></td>
      <td id="T_a86e0_row30_col1" class="data row30 col1" >admin_level = *</td>
      <td id="T_a86e0_row30_col2" class="data row30 col2" >25</td>
      <td id="T_a86e0_row30_col3" class="data row30 col3" >2</td>
      <td id="T_a86e0_row30_col4" class="data row30 col4" >2</td>
      <td id="T_a86e0_row30_col5" class="data row30 col5" >0.080000</td>
      <td id="T_a86e0_row30_col6" class="data row30 col6" >0.080000</td>
      <td id="T_a86e0_row30_col7" class="data row30 col7" >25</td>
      <td id="T_a86e0_row30_col8" class="data row30 col8" >2</td>
      <td id="T_a86e0_row30_col9" class="data row30 col9" >2</td>
      <td id="T_a86e0_row30_col10" class="data row30 col10" >0.080000</td>
      <td id="T_a86e0_row30_col11" class="data row30 col11" >0.080000</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row31" class="row_heading level0 row31" >31</th>
      <td id="T_a86e0_row31_col0" class="data row31 col0" >#</td>
      <td id="T_a86e0_row31_col1" class="data row31 col1" >highway</td>
      <td id="T_a86e0_row31_col2" class="data row31 col2" >92576</td>
      <td id="T_a86e0_row31_col3" class="data row31 col3" >89846</td>
      <td id="T_a86e0_row31_col4" class="data row31 col4" >90485</td>
      <td id="T_a86e0_row31_col5" class="data row31 col5" >0.970511</td>
      <td id="T_a86e0_row31_col6" class="data row31 col6" >0.977413</td>
      <td id="T_a86e0_row31_col7" class="data row31 col7" >11923</td>
      <td id="T_a86e0_row31_col8" class="data row31 col8" >10321</td>
      <td id="T_a86e0_row31_col9" class="data row31 col9" >10928</td>
      <td id="T_a86e0_row31_col10" class="data row31 col10" >0.865638</td>
      <td id="T_a86e0_row31_col11" class="data row31 col11" >0.916548</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row32" class="row_heading level0 row32" >32</th>
      <td id="T_a86e0_row32_col0" class="data row32 col0" ></td>
      <td id="T_a86e0_row32_col1" class="data row32 col1" >highway = motorway</td>
      <td id="T_a86e0_row32_col2" class="data row32 col2" >76</td>
      <td id="T_a86e0_row32_col3" class="data row32 col3" >0</td>
      <td id="T_a86e0_row32_col4" class="data row32 col4" >0</td>
      <td id="T_a86e0_row32_col5" class="data row32 col5" >0.000000</td>
      <td id="T_a86e0_row32_col6" class="data row32 col6" >0.000000</td>
      <td id="T_a86e0_row32_col7" class="data row32 col7" >1</td>
      <td id="T_a86e0_row32_col8" class="data row32 col8" >0</td>
      <td id="T_a86e0_row32_col9" class="data row32 col9" >0</td>
      <td id="T_a86e0_row32_col10" class="data row32 col10" >0.000000</td>
      <td id="T_a86e0_row32_col11" class="data row32 col11" >0.000000</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row33" class="row_heading level0 row33" >33</th>
      <td id="T_a86e0_row33_col0" class="data row33 col0" ></td>
      <td id="T_a86e0_row33_col1" class="data row33 col1" >highway = trunk</td>
      <td id="T_a86e0_row33_col2" class="data row33 col2" >1325</td>
      <td id="T_a86e0_row33_col3" class="data row33 col3" >1190</td>
      <td id="T_a86e0_row33_col4" class="data row33 col4" >1192</td>
      <td id="T_a86e0_row33_col5" class="data row33 col5" >0.898113</td>
      <td id="T_a86e0_row33_col6" class="data row33 col6" >0.899623</td>
      <td id="T_a86e0_row33_col7" class="data row33 col7" >140</td>
      <td id="T_a86e0_row33_col8" class="data row33 col8" >122</td>
      <td id="T_a86e0_row33_col9" class="data row33 col9" >123</td>
      <td id="T_a86e0_row33_col10" class="data row33 col10" >0.871429</td>
      <td id="T_a86e0_row33_col11" class="data row33 col11" >0.878571</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row34" class="row_heading level0 row34" >34</th>
      <td id="T_a86e0_row34_col0" class="data row34 col0" ></td>
      <td id="T_a86e0_row34_col1" class="data row34 col1" >highway = primary</td>
      <td id="T_a86e0_row34_col2" class="data row34 col2" >7625</td>
      <td id="T_a86e0_row34_col3" class="data row34 col3" >7492</td>
      <td id="T_a86e0_row34_col4" class="data row34 col4" >7498</td>
      <td id="T_a86e0_row34_col5" class="data row34 col5" >0.982557</td>
      <td id="T_a86e0_row34_col6" class="data row34 col6" >0.983344</td>
      <td id="T_a86e0_row34_col7" class="data row34 col7" >531</td>
      <td id="T_a86e0_row34_col8" class="data row34 col8" >495</td>
      <td id="T_a86e0_row34_col9" class="data row34 col9" >501</td>
      <td id="T_a86e0_row34_col10" class="data row34 col10" >0.932203</td>
      <td id="T_a86e0_row34_col11" class="data row34 col11" >0.943503</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row35" class="row_heading level0 row35" >35</th>
      <td id="T_a86e0_row35_col0" class="data row35 col0" ></td>
      <td id="T_a86e0_row35_col1" class="data row35 col1" >highway = secondary</td>
      <td id="T_a86e0_row35_col2" class="data row35 col2" >7175</td>
      <td id="T_a86e0_row35_col3" class="data row35 col3" >7145</td>
      <td id="T_a86e0_row35_col4" class="data row35 col4" >7153</td>
      <td id="T_a86e0_row35_col5" class="data row35 col5" >0.995819</td>
      <td id="T_a86e0_row35_col6" class="data row35 col6" >0.996934</td>
      <td id="T_a86e0_row35_col7" class="data row35 col7" >732</td>
      <td id="T_a86e0_row35_col8" class="data row35 col8" >712</td>
      <td id="T_a86e0_row35_col9" class="data row35 col9" >721</td>
      <td id="T_a86e0_row35_col10" class="data row35 col10" >0.972678</td>
      <td id="T_a86e0_row35_col11" class="data row35 col11" >0.984973</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row36" class="row_heading level0 row36" >36</th>
      <td id="T_a86e0_row36_col0" class="data row36 col0" ></td>
      <td id="T_a86e0_row36_col1" class="data row36 col1" >highway = tertiary</td>
      <td id="T_a86e0_row36_col2" class="data row36 col2" >10371</td>
      <td id="T_a86e0_row36_col3" class="data row36 col3" >10157</td>
      <td id="T_a86e0_row36_col4" class="data row36 col4" >10227</td>
      <td id="T_a86e0_row36_col5" class="data row36 col5" >0.979366</td>
      <td id="T_a86e0_row36_col6" class="data row36 col6" >0.986115</td>
      <td id="T_a86e0_row36_col7" class="data row36 col7" >1634</td>
      <td id="T_a86e0_row36_col8" class="data row36 col8" >1470</td>
      <td id="T_a86e0_row36_col9" class="data row36 col9" >1536</td>
      <td id="T_a86e0_row36_col10" class="data row36 col10" >0.899633</td>
      <td id="T_a86e0_row36_col11" class="data row36 col11" >0.940024</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row37" class="row_heading level0 row37" >37</th>
      <td id="T_a86e0_row37_col0" class="data row37 col0" ></td>
      <td id="T_a86e0_row37_col1" class="data row37 col1" >highway = unclassified</td>
      <td id="T_a86e0_row37_col2" class="data row37 col2" >2964</td>
      <td id="T_a86e0_row37_col3" class="data row37 col3" >2887</td>
      <td id="T_a86e0_row37_col4" class="data row37 col4" >2890</td>
      <td id="T_a86e0_row37_col5" class="data row37 col5" >0.974022</td>
      <td id="T_a86e0_row37_col6" class="data row37 col6" >0.975034</td>
      <td id="T_a86e0_row37_col7" class="data row37 col7" >910</td>
      <td id="T_a86e0_row37_col8" class="data row37 col8" >847</td>
      <td id="T_a86e0_row37_col9" class="data row37 col9" >857</td>
      <td id="T_a86e0_row37_col10" class="data row37 col10" >0.930769</td>
      <td id="T_a86e0_row37_col11" class="data row37 col11" >0.941758</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row38" class="row_heading level0 row38" >38</th>
      <td id="T_a86e0_row38_col0" class="data row38 col0" ></td>
      <td id="T_a86e0_row38_col1" class="data row38 col1" >highway = residential</td>
      <td id="T_a86e0_row38_col2" class="data row38 col2" >55305</td>
      <td id="T_a86e0_row38_col3" class="data row38 col3" >54388</td>
      <td id="T_a86e0_row38_col4" class="data row38 col4" >54755</td>
      <td id="T_a86e0_row38_col5" class="data row38 col5" >0.983419</td>
      <td id="T_a86e0_row38_col6" class="data row38 col6" >0.990055</td>
      <td id="T_a86e0_row38_col7" class="data row38 col7" >9539</td>
      <td id="T_a86e0_row38_col8" class="data row38 col8" >8759</td>
      <td id="T_a86e0_row38_col9" class="data row38 col9" >9168</td>
      <td id="T_a86e0_row38_col10" class="data row38 col10" >0.918230</td>
      <td id="T_a86e0_row38_col11" class="data row38 col11" >0.961107</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row39" class="row_heading level0 row39" >39</th>
      <td id="T_a86e0_row39_col0" class="data row39 col0" ></td>
      <td id="T_a86e0_row39_col1" class="data row39 col1" >highway = service</td>
      <td id="T_a86e0_row39_col2" class="data row39 col2" >3160</td>
      <td id="T_a86e0_row39_col3" class="data row39 col3" >2859</td>
      <td id="T_a86e0_row39_col4" class="data row39 col4" >3004</td>
      <td id="T_a86e0_row39_col5" class="data row39 col5" >0.904747</td>
      <td id="T_a86e0_row39_col6" class="data row39 col6" >0.950633</td>
      <td id="T_a86e0_row39_col7" class="data row39 col7" >1539</td>
      <td id="T_a86e0_row39_col8" class="data row39 col8" >1300</td>
      <td id="T_a86e0_row39_col9" class="data row39 col9" >1426</td>
      <td id="T_a86e0_row39_col10" class="data row39 col10" >0.844704</td>
      <td id="T_a86e0_row39_col11" class="data row39 col11" >0.926576</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row40" class="row_heading level0 row40" >40</th>
      <td id="T_a86e0_row40_col0" class="data row40 col0" ></td>
      <td id="T_a86e0_row40_col1" class="data row40 col1" >highway = track</td>
      <td id="T_a86e0_row40_col2" class="data row40 col2" >782</td>
      <td id="T_a86e0_row40_col3" class="data row40 col3" >560</td>
      <td id="T_a86e0_row40_col4" class="data row40 col4" >567</td>
      <td id="T_a86e0_row40_col5" class="data row40 col5" >0.716113</td>
      <td id="T_a86e0_row40_col6" class="data row40 col6" >0.725064</td>
      <td id="T_a86e0_row40_col7" class="data row40 col7" >213</td>
      <td id="T_a86e0_row40_col8" class="data row40 col8" >142</td>
      <td id="T_a86e0_row40_col9" class="data row40 col9" >146</td>
      <td id="T_a86e0_row40_col10" class="data row40 col10" >0.666667</td>
      <td id="T_a86e0_row40_col11" class="data row40 col11" >0.685446</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row41" class="row_heading level0 row41" >41</th>
      <td id="T_a86e0_row41_col0" class="data row41 col0" ></td>
      <td id="T_a86e0_row41_col1" class="data row41 col1" >type = associatedStreet</td>
      <td id="T_a86e0_row41_col2" class="data row41 col2" >1817</td>
      <td id="T_a86e0_row41_col3" class="data row41 col3" >1815</td>
      <td id="T_a86e0_row41_col4" class="data row41 col4" >1817</td>
      <td id="T_a86e0_row41_col5" class="data row41 col5" >0.998899</td>
      <td id="T_a86e0_row41_col6" class="data row41 col6" >1.000000</td>
      <td id="T_a86e0_row41_col7" class="data row41 col7" >1170</td>
      <td id="T_a86e0_row41_col8" class="data row41 col8" >1163</td>
      <td id="T_a86e0_row41_col9" class="data row41 col9" >1169</td>
      <td id="T_a86e0_row41_col10" class="data row41 col10" >0.994017</td>
      <td id="T_a86e0_row41_col11" class="data row41 col11" >0.999145</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row42" class="row_heading level0 row42" >42</th>
      <td id="T_a86e0_row42_col0" class="data row42 col0" ></td>
      <td id="T_a86e0_row42_col1" class="data row42 col1" >highway = *</td>
      <td id="T_a86e0_row42_col2" class="data row42 col2" >1976</td>
      <td id="T_a86e0_row42_col3" class="data row42 col3" >1353</td>
      <td id="T_a86e0_row42_col4" class="data row42 col4" >1382</td>
      <td id="T_a86e0_row42_col5" class="data row42 col5" >0.684717</td>
      <td id="T_a86e0_row42_col6" class="data row42 col6" >0.699393</td>
      <td id="T_a86e0_row42_col7" class="data row42 col7" >989</td>
      <td id="T_a86e0_row42_col8" class="data row42 col8" >655</td>
      <td id="T_a86e0_row42_col9" class="data row42 col9" >663</td>
      <td id="T_a86e0_row42_col10" class="data row42 col10" >0.662285</td>
      <td id="T_a86e0_row42_col11" class="data row42 col11" >0.670374</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row43" class="row_heading level0 row43" >43</th>
      <td id="T_a86e0_row43_col0" class="data row43 col0" >#</td>
      <td id="T_a86e0_row43_col1" class="data row43 col1" >public_transport</td>
      <td id="T_a86e0_row43_col2" class="data row43 col2" >34688</td>
      <td id="T_a86e0_row43_col3" class="data row43 col3" >19326</td>
      <td id="T_a86e0_row43_col4" class="data row43 col4" >19907</td>
      <td id="T_a86e0_row43_col5" class="data row43 col5" >0.557138</td>
      <td id="T_a86e0_row43_col6" class="data row43 col6" >0.573887</td>
      <td id="T_a86e0_row43_col7" class="data row43 col7" >14315</td>
      <td id="T_a86e0_row43_col8" class="data row43 col8" >7237</td>
      <td id="T_a86e0_row43_col9" class="data row43 col9" >7472</td>
      <td id="T_a86e0_row43_col10" class="data row43 col10" >0.505554</td>
      <td id="T_a86e0_row43_col11" class="data row43 col11" >0.521970</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row44" class="row_heading level0 row44" >44</th>
      <td id="T_a86e0_row44_col0" class="data row44 col0" ></td>
      <td id="T_a86e0_row44_col1" class="data row44 col1" >highway = bus_stop</td>
      <td id="T_a86e0_row44_col2" class="data row44 col2" >17332</td>
      <td id="T_a86e0_row44_col3" class="data row44 col3" >8968</td>
      <td id="T_a86e0_row44_col4" class="data row44 col4" >9436</td>
      <td id="T_a86e0_row44_col5" class="data row44 col5" >0.517424</td>
      <td id="T_a86e0_row44_col6" class="data row44 col6" >0.544426</td>
      <td id="T_a86e0_row44_col7" class="data row44 col7" >8475</td>
      <td id="T_a86e0_row44_col8" class="data row44 col8" >4270</td>
      <td id="T_a86e0_row44_col9" class="data row44 col9" >4510</td>
      <td id="T_a86e0_row44_col10" class="data row44 col10" >0.503835</td>
      <td id="T_a86e0_row44_col11" class="data row44 col11" >0.532153</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row45" class="row_heading level0 row45" >45</th>
      <td id="T_a86e0_row45_col0" class="data row45 col0" ></td>
      <td id="T_a86e0_row45_col1" class="data row45 col1" >type = route</td>
      <td id="T_a86e0_row45_col2" class="data row45 col2" >3892</td>
      <td id="T_a86e0_row45_col3" class="data row45 col3" >1856</td>
      <td id="T_a86e0_row45_col4" class="data row45 col4" >1877</td>
      <td id="T_a86e0_row45_col5" class="data row45 col5" >0.476876</td>
      <td id="T_a86e0_row45_col6" class="data row45 col6" >0.482271</td>
      <td id="T_a86e0_row45_col7" class="data row45 col7" >3863</td>
      <td id="T_a86e0_row45_col8" class="data row45 col8" >1853</td>
      <td id="T_a86e0_row45_col9" class="data row45 col9" >1869</td>
      <td id="T_a86e0_row45_col10" class="data row45 col10" >0.479679</td>
      <td id="T_a86e0_row45_col11" class="data row45 col11" >0.483821</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row46" class="row_heading level0 row46" >46</th>
      <td id="T_a86e0_row46_col0" class="data row46 col0" ></td>
      <td id="T_a86e0_row46_col1" class="data row46 col1" >public_transport = *</td>
      <td id="T_a86e0_row46_col2" class="data row46 col2" >24847</td>
      <td id="T_a86e0_row46_col3" class="data row46 col3" >15288</td>
      <td id="T_a86e0_row46_col4" class="data row46 col4" >15795</td>
      <td id="T_a86e0_row46_col5" class="data row46 col5" >0.615286</td>
      <td id="T_a86e0_row46_col6" class="data row46 col6" >0.635690</td>
      <td id="T_a86e0_row46_col7" class="data row46 col7" >7960</td>
      <td id="T_a86e0_row46_col8" class="data row46 col8" >4392</td>
      <td id="T_a86e0_row46_col9" class="data row46 col9" >4536</td>
      <td id="T_a86e0_row46_col10" class="data row46 col10" >0.551759</td>
      <td id="T_a86e0_row46_col11" class="data row46 col11" >0.569849</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row47" class="row_heading level0 row47" >47</th>
      <td id="T_a86e0_row47_col0" class="data row47 col0" ></td>
      <td id="T_a86e0_row47_col1" class="data row47 col1" >route = *</td>
      <td id="T_a86e0_row47_col2" class="data row47 col2" >3944</td>
      <td id="T_a86e0_row47_col3" class="data row47 col3" >1884</td>
      <td id="T_a86e0_row47_col4" class="data row47 col4" >1902</td>
      <td id="T_a86e0_row47_col5" class="data row47 col5" >0.477688</td>
      <td id="T_a86e0_row47_col6" class="data row47 col6" >0.482252</td>
      <td id="T_a86e0_row47_col7" class="data row47 col7" >3901</td>
      <td id="T_a86e0_row47_col8" class="data row47 col8" >1870</td>
      <td id="T_a86e0_row47_col9" class="data row47 col9" >1885</td>
      <td id="T_a86e0_row47_col10" class="data row47 col10" >0.479364</td>
      <td id="T_a86e0_row47_col11" class="data row47 col11" >0.483209</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row48" class="row_heading level0 row48" >48</th>
      <td id="T_a86e0_row48_col0" class="data row48 col0" ></td>
      <td id="T_a86e0_row48_col1" class="data row48 col1" >railway = *</td>
      <td id="T_a86e0_row48_col2" class="data row48 col2" >2846</td>
      <td id="T_a86e0_row48_col3" class="data row48 col3" >1847</td>
      <td id="T_a86e0_row48_col4" class="data row48 col4" >1788</td>
      <td id="T_a86e0_row48_col5" class="data row48 col5" >0.648981</td>
      <td id="T_a86e0_row48_col6" class="data row48 col6" >0.628250</td>
      <td id="T_a86e0_row48_col7" class="data row48 col7" >1355</td>
      <td id="T_a86e0_row48_col8" class="data row48 col8" >1158</td>
      <td id="T_a86e0_row48_col9" class="data row48 col9" >1164</td>
      <td id="T_a86e0_row48_col10" class="data row48 col10" >0.854613</td>
      <td id="T_a86e0_row48_col11" class="data row48 col11" >0.859041</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row49" class="row_heading level0 row49" >49</th>
      <td id="T_a86e0_row49_col0" class="data row49 col0" ></td>
      <td id="T_a86e0_row49_col1" class="data row49 col1" >route_master = *</td>
      <td id="T_a86e0_row49_col2" class="data row49 col2" >598</td>
      <td id="T_a86e0_row49_col3" class="data row49 col3" >99</td>
      <td id="T_a86e0_row49_col4" class="data row49 col4" >106</td>
      <td id="T_a86e0_row49_col5" class="data row49 col5" >0.165552</td>
      <td id="T_a86e0_row49_col6" class="data row49 col6" >0.177258</td>
      <td id="T_a86e0_row49_col7" class="data row49 col7" >549</td>
      <td id="T_a86e0_row49_col8" class="data row49 col8" >97</td>
      <td id="T_a86e0_row49_col9" class="data row49 col9" >103</td>
      <td id="T_a86e0_row49_col10" class="data row49 col10" >0.176685</td>
      <td id="T_a86e0_row49_col11" class="data row49 col11" >0.187614</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row50" class="row_heading level0 row50" >50</th>
      <td id="T_a86e0_row50_col0" class="data row50 col0" >#</td>
      <td id="T_a86e0_row50_col1" class="data row50 col1" >infrastructure</td>
      <td id="T_a86e0_row50_col2" class="data row50 col2" >18333</td>
      <td id="T_a86e0_row50_col3" class="data row50 col3" >6800</td>
      <td id="T_a86e0_row50_col4" class="data row50 col4" >7269</td>
      <td id="T_a86e0_row50_col5" class="data row50 col5" >0.370916</td>
      <td id="T_a86e0_row50_col6" class="data row50 col6" >0.396498</td>
      <td id="T_a86e0_row50_col7" class="data row50 col7" >10137</td>
      <td id="T_a86e0_row50_col8" class="data row50 col8" >3081</td>
      <td id="T_a86e0_row50_col9" class="data row50 col9" >3428</td>
      <td id="T_a86e0_row50_col10" class="data row50 col10" >0.303936</td>
      <td id="T_a86e0_row50_col11" class="data row50 col11" >0.338167</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row51" class="row_heading level0 row51" >51</th>
      <td id="T_a86e0_row51_col0" class="data row51 col0" ></td>
      <td id="T_a86e0_row51_col1" class="data row51 col1" >tunnel = *</td>
      <td id="T_a86e0_row51_col2" class="data row51 col2" >5589</td>
      <td id="T_a86e0_row51_col3" class="data row51 col3" >3589</td>
      <td id="T_a86e0_row51_col4" class="data row51 col4" >3916</td>
      <td id="T_a86e0_row51_col5" class="data row51 col5" >0.642154</td>
      <td id="T_a86e0_row51_col6" class="data row51 col6" >0.700662</td>
      <td id="T_a86e0_row51_col7" class="data row51 col7" >1613</td>
      <td id="T_a86e0_row51_col8" class="data row51 col8" >1006</td>
      <td id="T_a86e0_row51_col9" class="data row51 col9" >1180</td>
      <td id="T_a86e0_row51_col10" class="data row51 col10" >0.623683</td>
      <td id="T_a86e0_row51_col11" class="data row51 col11" >0.731556</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row52" class="row_heading level0 row52" >52</th>
      <td id="T_a86e0_row52_col0" class="data row52 col0" ></td>
      <td id="T_a86e0_row52_col1" class="data row52 col1" >barrier = *</td>
      <td id="T_a86e0_row52_col2" class="data row52 col2" >4391</td>
      <td id="T_a86e0_row52_col3" class="data row52 col3" >1048</td>
      <td id="T_a86e0_row52_col4" class="data row52 col4" >1058</td>
      <td id="T_a86e0_row52_col5" class="data row52 col5" >0.238670</td>
      <td id="T_a86e0_row52_col6" class="data row52 col6" >0.240947</td>
      <td id="T_a86e0_row52_col7" class="data row52 col7" >3661</td>
      <td id="T_a86e0_row52_col8" class="data row52 col8" >778</td>
      <td id="T_a86e0_row52_col9" class="data row52 col9" >829</td>
      <td id="T_a86e0_row52_col10" class="data row52 col10" >0.212510</td>
      <td id="T_a86e0_row52_col11" class="data row52 col11" >0.226441</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row53" class="row_heading level0 row53" >53</th>
      <td id="T_a86e0_row53_col0" class="data row53 col0" ></td>
      <td id="T_a86e0_row53_col1" class="data row53 col1" >power = *</td>
      <td id="T_a86e0_row53_col2" class="data row53 col2" >4860</td>
      <td id="T_a86e0_row53_col3" class="data row53 col3" >626</td>
      <td id="T_a86e0_row53_col4" class="data row53 col4" >670</td>
      <td id="T_a86e0_row53_col5" class="data row53 col5" >0.128807</td>
      <td id="T_a86e0_row53_col6" class="data row53 col6" >0.137860</td>
      <td id="T_a86e0_row53_col7" class="data row53 col7" >3843</td>
      <td id="T_a86e0_row53_col8" class="data row53 col8" >538</td>
      <td id="T_a86e0_row53_col9" class="data row53 col9" >579</td>
      <td id="T_a86e0_row53_col10" class="data row53 col10" >0.139995</td>
      <td id="T_a86e0_row53_col11" class="data row53 col11" >0.150664</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row54" class="row_heading level0 row54" >54</th>
      <td id="T_a86e0_row54_col0" class="data row54 col0" ></td>
      <td id="T_a86e0_row54_col1" class="data row54 col1" >bridge = *</td>
      <td id="T_a86e0_row54_col2" class="data row54 col2" >1351</td>
      <td id="T_a86e0_row54_col3" class="data row54 col3" >1005</td>
      <td id="T_a86e0_row54_col4" class="data row54 col4" >1000</td>
      <td id="T_a86e0_row54_col5" class="data row54 col5" >0.743893</td>
      <td id="T_a86e0_row54_col6" class="data row54 col6" >0.740192</td>
      <td id="T_a86e0_row54_col7" class="data row54 col7" >496</td>
      <td id="T_a86e0_row54_col8" class="data row54 col8" >388</td>
      <td id="T_a86e0_row54_col9" class="data row54 col9" >391</td>
      <td id="T_a86e0_row54_col10" class="data row54 col10" >0.782258</td>
      <td id="T_a86e0_row54_col11" class="data row54 col11" >0.788306</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row55" class="row_heading level0 row55" >55</th>
      <td id="T_a86e0_row55_col0" class="data row55 col0" ></td>
      <td id="T_a86e0_row55_col1" class="data row55 col1" >substation = *</td>
      <td id="T_a86e0_row55_col2" class="data row55 col2" >2547</td>
      <td id="T_a86e0_row55_col3" class="data row55 col3" >455</td>
      <td id="T_a86e0_row55_col4" class="data row55 col4" >481</td>
      <td id="T_a86e0_row55_col5" class="data row55 col5" >0.178642</td>
      <td id="T_a86e0_row55_col6" class="data row55 col6" >0.188850</td>
      <td id="T_a86e0_row55_col7" class="data row55 col7" >2358</td>
      <td id="T_a86e0_row55_col8" class="data row55 col8" >413</td>
      <td id="T_a86e0_row55_col9" class="data row55 col9" >439</td>
      <td id="T_a86e0_row55_col10" class="data row55 col10" >0.175148</td>
      <td id="T_a86e0_row55_col11" class="data row55 col11" >0.186175</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row56" class="row_heading level0 row56" >56</th>
      <td id="T_a86e0_row56_col0" class="data row56 col0" ></td>
      <td id="T_a86e0_row56_col1" class="data row56 col1" >emergency = *</td>
      <td id="T_a86e0_row56_col2" class="data row56 col2" >1149</td>
      <td id="T_a86e0_row56_col3" class="data row56 col3" >121</td>
      <td id="T_a86e0_row56_col4" class="data row56 col4" >108</td>
      <td id="T_a86e0_row56_col5" class="data row56 col5" >0.105309</td>
      <td id="T_a86e0_row56_col6" class="data row56 col6" >0.093995</td>
      <td id="T_a86e0_row56_col7" class="data row56 col7" >283</td>
      <td id="T_a86e0_row56_col8" class="data row56 col8" >100</td>
      <td id="T_a86e0_row56_col9" class="data row56 col9" >98</td>
      <td id="T_a86e0_row56_col10" class="data row56 col10" >0.353357</td>
      <td id="T_a86e0_row56_col11" class="data row56 col11" >0.346290</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row57" class="row_heading level0 row57" >57</th>
      <td id="T_a86e0_row57_col0" class="data row57 col0" ></td>
      <td id="T_a86e0_row57_col1" class="data row57 col1" >ele = *</td>
      <td id="T_a86e0_row57_col2" class="data row57 col2" >308</td>
      <td id="T_a86e0_row57_col3" class="data row57 col3" >77</td>
      <td id="T_a86e0_row57_col4" class="data row57 col4" >147</td>
      <td id="T_a86e0_row57_col5" class="data row57 col5" >0.250000</td>
      <td id="T_a86e0_row57_col6" class="data row57 col6" >0.477273</td>
      <td id="T_a86e0_row57_col7" class="data row57 col7" >281</td>
      <td id="T_a86e0_row57_col8" class="data row57 col8" >76</td>
      <td id="T_a86e0_row57_col9" class="data row57 col9" >139</td>
      <td id="T_a86e0_row57_col10" class="data row57 col10" >0.270463</td>
      <td id="T_a86e0_row57_col11" class="data row57 col11" >0.494662</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row58" class="row_heading level0 row58" >58</th>
      <td id="T_a86e0_row58_col0" class="data row58 col0" ></td>
      <td id="T_a86e0_row58_col1" class="data row58 col1" >man_made = *</td>
      <td id="T_a86e0_row58_col2" class="data row58 col2" >1587</td>
      <td id="T_a86e0_row58_col3" class="data row58 col3" >239</td>
      <td id="T_a86e0_row58_col4" class="data row58 col4" >277</td>
      <td id="T_a86e0_row58_col5" class="data row58 col5" >0.150599</td>
      <td id="T_a86e0_row58_col6" class="data row58 col6" >0.174543</td>
      <td id="T_a86e0_row58_col7" class="data row58 col7" >1164</td>
      <td id="T_a86e0_row58_col8" class="data row58 col8" >216</td>
      <td id="T_a86e0_row58_col9" class="data row58 col9" >242</td>
      <td id="T_a86e0_row58_col10" class="data row58 col10" >0.185567</td>
      <td id="T_a86e0_row58_col11" class="data row58 col11" >0.207904</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row59" class="row_heading level0 row59" >59</th>
      <td id="T_a86e0_row59_col0" class="data row59 col0" ></td>
      <td id="T_a86e0_row59_col1" class="data row59 col1" >embankment = *</td>
      <td id="T_a86e0_row59_col2" class="data row59 col2" >211</td>
      <td id="T_a86e0_row59_col3" class="data row59 col3" >127</td>
      <td id="T_a86e0_row59_col4" class="data row59 col4" >127</td>
      <td id="T_a86e0_row59_col5" class="data row59 col5" >0.601896</td>
      <td id="T_a86e0_row59_col6" class="data row59 col6" >0.601896</td>
      <td id="T_a86e0_row59_col7" class="data row59 col7" >89</td>
      <td id="T_a86e0_row59_col8" class="data row59 col8" >67</td>
      <td id="T_a86e0_row59_col9" class="data row59 col9" >67</td>
      <td id="T_a86e0_row59_col10" class="data row59 col10" >0.752809</td>
      <td id="T_a86e0_row59_col11" class="data row59 col11" >0.752809</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row60" class="row_heading level0 row60" >60</th>
      <td id="T_a86e0_row60_col0" class="data row60 col0" >#</td>
      <td id="T_a86e0_row60_col1" class="data row60 col1" >amenity</td>
      <td id="T_a86e0_row60_col2" class="data row60 col2" >61726</td>
      <td id="T_a86e0_row60_col3" class="data row60 col3" >11487</td>
      <td id="T_a86e0_row60_col4" class="data row60 col4" >16381</td>
      <td id="T_a86e0_row60_col5" class="data row60 col5" >0.186097</td>
      <td id="T_a86e0_row60_col6" class="data row60 col6" >0.265382</td>
      <td id="T_a86e0_row60_col7" class="data row60 col7" >30388</td>
      <td id="T_a86e0_row60_col8" class="data row60 col8" >6506</td>
      <td id="T_a86e0_row60_col9" class="data row60 col9" >9542</td>
      <td id="T_a86e0_row60_col10" class="data row60 col10" >0.214098</td>
      <td id="T_a86e0_row60_col11" class="data row60 col11" >0.314006</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row61" class="row_heading level0 row61" >61</th>
      <td id="T_a86e0_row61_col0" class="data row61 col0" ></td>
      <td id="T_a86e0_row61_col1" class="data row61 col1" >amenity = place_of_worship</td>
      <td id="T_a86e0_row61_col2" class="data row61 col2" >2662</td>
      <td id="T_a86e0_row61_col3" class="data row61 col3" >1287</td>
      <td id="T_a86e0_row61_col4" class="data row61 col4" >1561</td>
      <td id="T_a86e0_row61_col5" class="data row61 col5" >0.483471</td>
      <td id="T_a86e0_row61_col6" class="data row61 col6" >0.586401</td>
      <td id="T_a86e0_row61_col7" class="data row61 col7" >1874</td>
      <td id="T_a86e0_row61_col8" class="data row61 col8" >939</td>
      <td id="T_a86e0_row61_col9" class="data row61 col9" >1231</td>
      <td id="T_a86e0_row61_col10" class="data row61 col10" >0.501067</td>
      <td id="T_a86e0_row61_col11" class="data row61 col11" >0.656884</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row62" class="row_heading level0 row62" >62</th>
      <td id="T_a86e0_row62_col0" class="data row62 col0" ></td>
      <td id="T_a86e0_row62_col1" class="data row62 col1" >amenity = school</td>
      <td id="T_a86e0_row62_col2" class="data row62 col2" >1975</td>
      <td id="T_a86e0_row62_col3" class="data row62 col3" >595</td>
      <td id="T_a86e0_row62_col4" class="data row62 col4" >722</td>
      <td id="T_a86e0_row62_col5" class="data row62 col5" >0.301266</td>
      <td id="T_a86e0_row62_col6" class="data row62 col6" >0.365570</td>
      <td id="T_a86e0_row62_col7" class="data row62 col7" >1419</td>
      <td id="T_a86e0_row62_col8" class="data row62 col8" >405</td>
      <td id="T_a86e0_row62_col9" class="data row62 col9" >511</td>
      <td id="T_a86e0_row62_col10" class="data row62 col10" >0.285412</td>
      <td id="T_a86e0_row62_col11" class="data row62 col11" >0.360113</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row63" class="row_heading level0 row63" >63</th>
      <td id="T_a86e0_row63_col0" class="data row63 col0" ></td>
      <td id="T_a86e0_row63_col1" class="data row63 col1" >amenity = kindergarten</td>
      <td id="T_a86e0_row63_col2" class="data row63 col2" >1876</td>
      <td id="T_a86e0_row63_col3" class="data row63 col3" >422</td>
      <td id="T_a86e0_row63_col4" class="data row63 col4" >501</td>
      <td id="T_a86e0_row63_col5" class="data row63 col5" >0.224947</td>
      <td id="T_a86e0_row63_col6" class="data row63 col6" >0.267058</td>
      <td id="T_a86e0_row63_col7" class="data row63 col7" >1352</td>
      <td id="T_a86e0_row63_col8" class="data row63 col8" >380</td>
      <td id="T_a86e0_row63_col9" class="data row63 col9" >435</td>
      <td id="T_a86e0_row63_col10" class="data row63 col10" >0.281065</td>
      <td id="T_a86e0_row63_col11" class="data row63 col11" >0.321746</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row64" class="row_heading level0 row64" >64</th>
      <td id="T_a86e0_row64_col0" class="data row64 col0" ></td>
      <td id="T_a86e0_row64_col1" class="data row64 col1" >craft = shoemaker</td>
      <td id="T_a86e0_row64_col2" class="data row64 col2" >225</td>
      <td id="T_a86e0_row64_col3" class="data row64 col3" >30</td>
      <td id="T_a86e0_row64_col4" class="data row64 col4" >43</td>
      <td id="T_a86e0_row64_col5" class="data row64 col5" >0.133333</td>
      <td id="T_a86e0_row64_col6" class="data row64 col6" >0.191111</td>
      <td id="T_a86e0_row64_col7" class="data row64 col7" >64</td>
      <td id="T_a86e0_row64_col8" class="data row64 col8" >6</td>
      <td id="T_a86e0_row64_col9" class="data row64 col9" >13</td>
      <td id="T_a86e0_row64_col10" class="data row64 col10" >0.093750</td>
      <td id="T_a86e0_row64_col11" class="data row64 col11" >0.203125</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row65" class="row_heading level0 row65" >65</th>
      <td id="T_a86e0_row65_col0" class="data row65 col0" ></td>
      <td id="T_a86e0_row65_col1" class="data row65 col1" >amenity = *</td>
      <td id="T_a86e0_row65_col2" class="data row65 col2" >23587</td>
      <td id="T_a86e0_row65_col3" class="data row65 col3" >5622</td>
      <td id="T_a86e0_row65_col4" class="data row65 col4" >7435</td>
      <td id="T_a86e0_row65_col5" class="data row65 col5" >0.238352</td>
      <td id="T_a86e0_row65_col6" class="data row65 col6" >0.315216</td>
      <td id="T_a86e0_row65_col7" class="data row65 col7" >12678</td>
      <td id="T_a86e0_row65_col8" class="data row65 col8" >2877</td>
      <td id="T_a86e0_row65_col9" class="data row65 col9" >4122</td>
      <td id="T_a86e0_row65_col10" class="data row65 col10" >0.226929</td>
      <td id="T_a86e0_row65_col11" class="data row65 col11" >0.325130</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row66" class="row_heading level0 row66" >66</th>
      <td id="T_a86e0_row66_col0" class="data row66 col0" ></td>
      <td id="T_a86e0_row66_col1" class="data row66 col1" >shop = *</td>
      <td id="T_a86e0_row66_col2" class="data row66 col2" >28784</td>
      <td id="T_a86e0_row66_col3" class="data row66 col3" >2945</td>
      <td id="T_a86e0_row66_col4" class="data row66 col4" >5435</td>
      <td id="T_a86e0_row66_col5" class="data row66 col5" >0.102314</td>
      <td id="T_a86e0_row66_col6" class="data row66 col6" >0.188820</td>
      <td id="T_a86e0_row66_col7" class="data row66 col7" >11962</td>
      <td id="T_a86e0_row66_col8" class="data row66 col8" >1546</td>
      <td id="T_a86e0_row66_col9" class="data row66 col9" >2854</td>
      <td id="T_a86e0_row66_col10" class="data row66 col10" >0.129243</td>
      <td id="T_a86e0_row66_col11" class="data row66 col11" >0.238589</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row67" class="row_heading level0 row67" >67</th>
      <td id="T_a86e0_row67_col0" class="data row67 col0" ></td>
      <td id="T_a86e0_row67_col1" class="data row67 col1" >leisure = *</td>
      <td id="T_a86e0_row67_col2" class="data row67 col2" >3227</td>
      <td id="T_a86e0_row67_col3" class="data row67 col3" >716</td>
      <td id="T_a86e0_row67_col4" class="data row67 col4" >860</td>
      <td id="T_a86e0_row67_col5" class="data row67 col5" >0.221878</td>
      <td id="T_a86e0_row67_col6" class="data row67 col6" >0.266501</td>
      <td id="T_a86e0_row67_col7" class="data row67 col7" >2357</td>
      <td id="T_a86e0_row67_col8" class="data row67 col8" >565</td>
      <td id="T_a86e0_row67_col9" class="data row67 col9" >704</td>
      <td id="T_a86e0_row67_col10" class="data row67 col10" >0.239711</td>
      <td id="T_a86e0_row67_col11" class="data row67 col11" >0.298685</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row68" class="row_heading level0 row68" >68</th>
      <td id="T_a86e0_row68_col0" class="data row68 col0" ></td>
      <td id="T_a86e0_row68_col1" class="data row68 col1" >sport = *</td>
      <td id="T_a86e0_row68_col2" class="data row68 col2" >774</td>
      <td id="T_a86e0_row68_col3" class="data row68 col3" >171</td>
      <td id="T_a86e0_row68_col4" class="data row68 col4" >158</td>
      <td id="T_a86e0_row68_col5" class="data row68 col5" >0.220930</td>
      <td id="T_a86e0_row68_col6" class="data row68 col6" >0.204134</td>
      <td id="T_a86e0_row68_col7" class="data row68 col7" >582</td>
      <td id="T_a86e0_row68_col8" class="data row68 col8" >115</td>
      <td id="T_a86e0_row68_col9" class="data row68 col9" >110</td>
      <td id="T_a86e0_row68_col10" class="data row68 col10" >0.197595</td>
      <td id="T_a86e0_row68_col11" class="data row68 col11" >0.189003</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row69" class="row_heading level0 row69" >69</th>
      <td id="T_a86e0_row69_col0" class="data row69 col0" ></td>
      <td id="T_a86e0_row69_col1" class="data row69 col1" >clothes = *</td>
      <td id="T_a86e0_row69_col2" class="data row69 col2" >228</td>
      <td id="T_a86e0_row69_col3" class="data row69 col3" >32</td>
      <td id="T_a86e0_row69_col4" class="data row69 col4" >42</td>
      <td id="T_a86e0_row69_col5" class="data row69 col5" >0.140351</td>
      <td id="T_a86e0_row69_col6" class="data row69 col6" >0.184211</td>
      <td id="T_a86e0_row69_col7" class="data row69 col7" >129</td>
      <td id="T_a86e0_row69_col8" class="data row69 col8" >18</td>
      <td id="T_a86e0_row69_col9" class="data row69 col9" >23</td>
      <td id="T_a86e0_row69_col10" class="data row69 col10" >0.139535</td>
      <td id="T_a86e0_row69_col11" class="data row69 col11" >0.178295</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row70" class="row_heading level0 row70" >70</th>
      <td id="T_a86e0_row70_col0" class="data row70 col0" >#</td>
      <td id="T_a86e0_row70_col1" class="data row70 col1" >government</td>
      <td id="T_a86e0_row70_col2" class="data row70 col2" >4619</td>
      <td id="T_a86e0_row70_col3" class="data row70 col3" >823</td>
      <td id="T_a86e0_row70_col4" class="data row70 col4" >1336</td>
      <td id="T_a86e0_row70_col5" class="data row70 col5" >0.178177</td>
      <td id="T_a86e0_row70_col6" class="data row70 col6" >0.289240</td>
      <td id="T_a86e0_row70_col7" class="data row70 col7" >3238</td>
      <td id="T_a86e0_row70_col8" class="data row70 col8" >694</td>
      <td id="T_a86e0_row70_col9" class="data row70 col9" >1090</td>
      <td id="T_a86e0_row70_col10" class="data row70 col10" >0.214330</td>
      <td id="T_a86e0_row70_col11" class="data row70 col11" >0.336628</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row71" class="row_heading level0 row71" >71</th>
      <td id="T_a86e0_row71_col0" class="data row71 col0" ></td>
      <td id="T_a86e0_row71_col1" class="data row71 col1" >office = government</td>
      <td id="T_a86e0_row71_col2" class="data row71 col2" >1878</td>
      <td id="T_a86e0_row71_col3" class="data row71 col3" >328</td>
      <td id="T_a86e0_row71_col4" class="data row71 col4" >541</td>
      <td id="T_a86e0_row71_col5" class="data row71 col5" >0.174654</td>
      <td id="T_a86e0_row71_col6" class="data row71 col6" >0.288072</td>
      <td id="T_a86e0_row71_col7" class="data row71 col7" >1563</td>
      <td id="T_a86e0_row71_col8" class="data row71 col8" >298</td>
      <td id="T_a86e0_row71_col9" class="data row71 col9" >474</td>
      <td id="T_a86e0_row71_col10" class="data row71 col10" >0.190659</td>
      <td id="T_a86e0_row71_col11" class="data row71 col11" >0.303263</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row72" class="row_heading level0 row72" >72</th>
      <td id="T_a86e0_row72_col0" class="data row72 col0" ></td>
      <td id="T_a86e0_row72_col1" class="data row72 col1" >healthcare = *</td>
      <td id="T_a86e0_row72_col2" class="data row72 col2" >2262</td>
      <td id="T_a86e0_row72_col3" class="data row72 col3" >444</td>
      <td id="T_a86e0_row72_col4" class="data row72 col4" >711</td>
      <td id="T_a86e0_row72_col5" class="data row72 col5" >0.196286</td>
      <td id="T_a86e0_row72_col6" class="data row72 col6" >0.314324</td>
      <td id="T_a86e0_row72_col7" class="data row72 col7" >1376</td>
      <td id="T_a86e0_row72_col8" class="data row72 col8" >362</td>
      <td id="T_a86e0_row72_col9" class="data row72 col9" >558</td>
      <td id="T_a86e0_row72_col10" class="data row72 col10" >0.263081</td>
      <td id="T_a86e0_row72_col11" class="data row72 col11" >0.405523</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row73" class="row_heading level0 row73" >73</th>
      <td id="T_a86e0_row73_col0" class="data row73 col0" ></td>
      <td id="T_a86e0_row73_col1" class="data row73 col1" >government = *</td>
      <td id="T_a86e0_row73_col2" class="data row73 col2" >710</td>
      <td id="T_a86e0_row73_col3" class="data row73 col3" >182</td>
      <td id="T_a86e0_row73_col4" class="data row73 col4" >208</td>
      <td id="T_a86e0_row73_col5" class="data row73 col5" >0.256338</td>
      <td id="T_a86e0_row73_col6" class="data row73 col6" >0.292958</td>
      <td id="T_a86e0_row73_col7" class="data row73 col7" >561</td>
      <td id="T_a86e0_row73_col8" class="data row73 col8" >154</td>
      <td id="T_a86e0_row73_col9" class="data row73 col9" >166</td>
      <td id="T_a86e0_row73_col10" class="data row73 col10" >0.274510</td>
      <td id="T_a86e0_row73_col11" class="data row73 col11" >0.295900</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row74" class="row_heading level0 row74" >74</th>
      <td id="T_a86e0_row74_col0" class="data row74 col0" ></td>
      <td id="T_a86e0_row74_col1" class="data row74 col1" >military = *</td>
      <td id="T_a86e0_row74_col2" class="data row74 col2" >470</td>
      <td id="T_a86e0_row74_col3" class="data row74 col3" >52</td>
      <td id="T_a86e0_row74_col4" class="data row74 col4" >83</td>
      <td id="T_a86e0_row74_col5" class="data row74 col5" >0.110638</td>
      <td id="T_a86e0_row74_col6" class="data row74 col6" >0.176596</td>
      <td id="T_a86e0_row74_col7" class="data row74 col7" >297</td>
      <td id="T_a86e0_row74_col8" class="data row74 col8" >36</td>
      <td id="T_a86e0_row74_col9" class="data row74 col9" >59</td>
      <td id="T_a86e0_row74_col10" class="data row74 col10" >0.121212</td>
      <td id="T_a86e0_row74_col11" class="data row74 col11" >0.198653</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row75" class="row_heading level0 row75" >75</th>
      <td id="T_a86e0_row75_col0" class="data row75 col0" >#</td>
      <td id="T_a86e0_row75_col1" class="data row75 col1" >office</td>
      <td id="T_a86e0_row75_col2" class="data row75 col2" >5316</td>
      <td id="T_a86e0_row75_col3" class="data row75 col3" >522</td>
      <td id="T_a86e0_row75_col4" class="data row75 col4" >777</td>
      <td id="T_a86e0_row75_col5" class="data row75 col5" >0.098194</td>
      <td id="T_a86e0_row75_col6" class="data row75 col6" >0.146163</td>
      <td id="T_a86e0_row75_col7" class="data row75 col7" >3837</td>
      <td id="T_a86e0_row75_col8" class="data row75 col8" >387</td>
      <td id="T_a86e0_row75_col9" class="data row75 col9" >552</td>
      <td id="T_a86e0_row75_col10" class="data row75 col10" >0.100860</td>
      <td id="T_a86e0_row75_col11" class="data row75 col11" >0.143862</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row76" class="row_heading level0 row76" >76</th>
      <td id="T_a86e0_row76_col0" class="data row76 col0" ></td>
      <td id="T_a86e0_row76_col1" class="data row76 col1" >office = *</td>
      <td id="T_a86e0_row76_col2" class="data row76 col2" >5316</td>
      <td id="T_a86e0_row76_col3" class="data row76 col3" >522</td>
      <td id="T_a86e0_row76_col4" class="data row76 col4" >777</td>
      <td id="T_a86e0_row76_col5" class="data row76 col5" >0.098194</td>
      <td id="T_a86e0_row76_col6" class="data row76 col6" >0.146163</td>
      <td id="T_a86e0_row76_col7" class="data row76 col7" >3837</td>
      <td id="T_a86e0_row76_col8" class="data row76 col8" >387</td>
      <td id="T_a86e0_row76_col9" class="data row76 col9" >552</td>
      <td id="T_a86e0_row76_col10" class="data row76 col10" >0.100860</td>
      <td id="T_a86e0_row76_col11" class="data row76 col11" >0.143862</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row77" class="row_heading level0 row77" >77</th>
      <td id="T_a86e0_row77_col0" class="data row77 col0" >#</td>
      <td id="T_a86e0_row77_col1" class="data row77 col1" >building</td>
      <td id="T_a86e0_row77_col2" class="data row77 col2" >33646</td>
      <td id="T_a86e0_row77_col3" class="data row77 col3" >5345</td>
      <td id="T_a86e0_row77_col4" class="data row77 col4" >6200</td>
      <td id="T_a86e0_row77_col5" class="data row77 col5" >0.158860</td>
      <td id="T_a86e0_row77_col6" class="data row77 col6" >0.184272</td>
      <td id="T_a86e0_row77_col7" class="data row77 col7" >19973</td>
      <td id="T_a86e0_row77_col8" class="data row77 col8" >3989</td>
      <td id="T_a86e0_row77_col9" class="data row77 col9" >4725</td>
      <td id="T_a86e0_row77_col10" class="data row77 col10" >0.199720</td>
      <td id="T_a86e0_row77_col11" class="data row77 col11" >0.236569</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row78" class="row_heading level0 row78" >78</th>
      <td id="T_a86e0_row78_col0" class="data row78 col0" ></td>
      <td id="T_a86e0_row78_col1" class="data row78 col1" >building = industrial</td>
      <td id="T_a86e0_row78_col2" class="data row78 col2" >1607</td>
      <td id="T_a86e0_row78_col3" class="data row78 col3" >52</td>
      <td id="T_a86e0_row78_col4" class="data row78 col4" >61</td>
      <td id="T_a86e0_row78_col5" class="data row78 col5" >0.032358</td>
      <td id="T_a86e0_row78_col6" class="data row78 col6" >0.037959</td>
      <td id="T_a86e0_row78_col7" class="data row78 col7" >1224</td>
      <td id="T_a86e0_row78_col8" class="data row78 col8" >50</td>
      <td id="T_a86e0_row78_col9" class="data row78 col9" >59</td>
      <td id="T_a86e0_row78_col10" class="data row78 col10" >0.040850</td>
      <td id="T_a86e0_row78_col11" class="data row78 col11" >0.048203</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row79" class="row_heading level0 row79" >79</th>
      <td id="T_a86e0_row79_col0" class="data row79 col0" ></td>
      <td id="T_a86e0_row79_col1" class="data row79 col1" >building = service</td>
      <td id="T_a86e0_row79_col2" class="data row79 col2" >1368</td>
      <td id="T_a86e0_row79_col3" class="data row79 col3" >583</td>
      <td id="T_a86e0_row79_col4" class="data row79 col4" >588</td>
      <td id="T_a86e0_row79_col5" class="data row79 col5" >0.426170</td>
      <td id="T_a86e0_row79_col6" class="data row79 col6" >0.429825</td>
      <td id="T_a86e0_row79_col7" class="data row79 col7" >1032</td>
      <td id="T_a86e0_row79_col8" class="data row79 col8" >506</td>
      <td id="T_a86e0_row79_col9" class="data row79 col9" >513</td>
      <td id="T_a86e0_row79_col10" class="data row79 col10" >0.490310</td>
      <td id="T_a86e0_row79_col11" class="data row79 col11" >0.497093</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row80" class="row_heading level0 row80" >80</th>
      <td id="T_a86e0_row80_col0" class="data row80 col0" ></td>
      <td id="T_a86e0_row80_col1" class="data row80 col1" >building = retail</td>
      <td id="T_a86e0_row80_col2" class="data row80 col2" >1912</td>
      <td id="T_a86e0_row80_col3" class="data row80 col3" >330</td>
      <td id="T_a86e0_row80_col4" class="data row80 col4" >502</td>
      <td id="T_a86e0_row80_col5" class="data row80 col5" >0.172594</td>
      <td id="T_a86e0_row80_col6" class="data row80 col6" >0.262552</td>
      <td id="T_a86e0_row80_col7" class="data row80 col7" >1127</td>
      <td id="T_a86e0_row80_col8" class="data row80 col8" >259</td>
      <td id="T_a86e0_row80_col9" class="data row80 col9" >364</td>
      <td id="T_a86e0_row80_col10" class="data row80 col10" >0.229814</td>
      <td id="T_a86e0_row80_col11" class="data row80 col11" >0.322981</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row81" class="row_heading level0 row81" >81</th>
      <td id="T_a86e0_row81_col0" class="data row81 col0" ></td>
      <td id="T_a86e0_row81_col1" class="data row81 col1" >building = school</td>
      <td id="T_a86e0_row81_col2" class="data row81 col2" >680</td>
      <td id="T_a86e0_row81_col3" class="data row81 col3" >73</td>
      <td id="T_a86e0_row81_col4" class="data row81 col4" >97</td>
      <td id="T_a86e0_row81_col5" class="data row81 col5" >0.107353</td>
      <td id="T_a86e0_row81_col6" class="data row81 col6" >0.142647</td>
      <td id="T_a86e0_row81_col7" class="data row81 col7" >574</td>
      <td id="T_a86e0_row81_col8" class="data row81 col8" >65</td>
      <td id="T_a86e0_row81_col9" class="data row81 col9" >91</td>
      <td id="T_a86e0_row81_col10" class="data row81 col10" >0.113240</td>
      <td id="T_a86e0_row81_col11" class="data row81 col11" >0.158537</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row82" class="row_heading level0 row82" >82</th>
      <td id="T_a86e0_row82_col0" class="data row82 col0" ></td>
      <td id="T_a86e0_row82_col1" class="data row82 col1" >building = kindergarten</td>
      <td id="T_a86e0_row82_col2" class="data row82 col2" >366</td>
      <td id="T_a86e0_row82_col3" class="data row82 col3" >25</td>
      <td id="T_a86e0_row82_col4" class="data row82 col4" >35</td>
      <td id="T_a86e0_row82_col5" class="data row82 col5" >0.068306</td>
      <td id="T_a86e0_row82_col6" class="data row82 col6" >0.095628</td>
      <td id="T_a86e0_row82_col7" class="data row82 col7" >276</td>
      <td id="T_a86e0_row82_col8" class="data row82 col8" >24</td>
      <td id="T_a86e0_row82_col9" class="data row82 col9" >32</td>
      <td id="T_a86e0_row82_col10" class="data row82 col10" >0.086957</td>
      <td id="T_a86e0_row82_col11" class="data row82 col11" >0.115942</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row83" class="row_heading level0 row83" >83</th>
      <td id="T_a86e0_row83_col0" class="data row83 col0" ></td>
      <td id="T_a86e0_row83_col1" class="data row83 col1" >building = commercial</td>
      <td id="T_a86e0_row83_col2" class="data row83 col2" >598</td>
      <td id="T_a86e0_row83_col3" class="data row83 col3" >87</td>
      <td id="T_a86e0_row83_col4" class="data row83 col4" >81</td>
      <td id="T_a86e0_row83_col5" class="data row83 col5" >0.145485</td>
      <td id="T_a86e0_row83_col6" class="data row83 col6" >0.135452</td>
      <td id="T_a86e0_row83_col7" class="data row83 col7" >549</td>
      <td id="T_a86e0_row83_col8" class="data row83 col8" >78</td>
      <td id="T_a86e0_row83_col9" class="data row83 col9" >72</td>
      <td id="T_a86e0_row83_col10" class="data row83 col10" >0.142077</td>
      <td id="T_a86e0_row83_col11" class="data row83 col11" >0.131148</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row84" class="row_heading level0 row84" >84</th>
      <td id="T_a86e0_row84_col0" class="data row84 col0" ></td>
      <td id="T_a86e0_row84_col1" class="data row84 col1" >building = church</td>
      <td id="T_a86e0_row84_col2" class="data row84 col2" >1413</td>
      <td id="T_a86e0_row84_col3" class="data row84 col3" >802</td>
      <td id="T_a86e0_row84_col4" class="data row84 col4" >1036</td>
      <td id="T_a86e0_row84_col5" class="data row84 col5" >0.567587</td>
      <td id="T_a86e0_row84_col6" class="data row84 col6" >0.733192</td>
      <td id="T_a86e0_row84_col7" class="data row84 col7" >1095</td>
      <td id="T_a86e0_row84_col8" class="data row84 col8" >602</td>
      <td id="T_a86e0_row84_col9" class="data row84 col9" >833</td>
      <td id="T_a86e0_row84_col10" class="data row84 col10" >0.549772</td>
      <td id="T_a86e0_row84_col11" class="data row84 col11" >0.760731</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row85" class="row_heading level0 row85" >85</th>
      <td id="T_a86e0_row85_col0" class="data row85 col0" ></td>
      <td id="T_a86e0_row85_col1" class="data row85 col1" >building = warehouse</td>
      <td id="T_a86e0_row85_col2" class="data row85 col2" >232</td>
      <td id="T_a86e0_row85_col3" class="data row85 col3" >11</td>
      <td id="T_a86e0_row85_col4" class="data row85 col4" >19</td>
      <td id="T_a86e0_row85_col5" class="data row85 col5" >0.047414</td>
      <td id="T_a86e0_row85_col6" class="data row85 col6" >0.081897</td>
      <td id="T_a86e0_row85_col7" class="data row85 col7" >164</td>
      <td id="T_a86e0_row85_col8" class="data row85 col8" >9</td>
      <td id="T_a86e0_row85_col9" class="data row85 col9" >14</td>
      <td id="T_a86e0_row85_col10" class="data row85 col10" >0.054878</td>
      <td id="T_a86e0_row85_col11" class="data row85 col11" >0.085366</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row86" class="row_heading level0 row86" >86</th>
      <td id="T_a86e0_row86_col0" class="data row86 col0" ></td>
      <td id="T_a86e0_row86_col1" class="data row86 col1" >building = public</td>
      <td id="T_a86e0_row86_col2" class="data row86 col2" >361</td>
      <td id="T_a86e0_row86_col3" class="data row86 col3" >112</td>
      <td id="T_a86e0_row86_col4" class="data row86 col4" >97</td>
      <td id="T_a86e0_row86_col5" class="data row86 col5" >0.310249</td>
      <td id="T_a86e0_row86_col6" class="data row86 col6" >0.268698</td>
      <td id="T_a86e0_row86_col7" class="data row86 col7" >298</td>
      <td id="T_a86e0_row86_col8" class="data row86 col8" >103</td>
      <td id="T_a86e0_row86_col9" class="data row86 col9" >92</td>
      <td id="T_a86e0_row86_col10" class="data row86 col10" >0.345638</td>
      <td id="T_a86e0_row86_col11" class="data row86 col11" >0.308725</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row87" class="row_heading level0 row87" >87</th>
      <td id="T_a86e0_row87_col0" class="data row87 col0" ></td>
      <td id="T_a86e0_row87_col1" class="data row87 col1" >building = dormitory</td>
      <td id="T_a86e0_row87_col2" class="data row87 col2" >591</td>
      <td id="T_a86e0_row87_col3" class="data row87 col3" >81</td>
      <td id="T_a86e0_row87_col4" class="data row87 col4" >85</td>
      <td id="T_a86e0_row87_col5" class="data row87 col5" >0.137056</td>
      <td id="T_a86e0_row87_col6" class="data row87 col6" >0.143824</td>
      <td id="T_a86e0_row87_col7" class="data row87 col7" >444</td>
      <td id="T_a86e0_row87_col8" class="data row87 col8" >71</td>
      <td id="T_a86e0_row87_col9" class="data row87 col9" >85</td>
      <td id="T_a86e0_row87_col10" class="data row87 col10" >0.159910</td>
      <td id="T_a86e0_row87_col11" class="data row87 col11" >0.191441</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row88" class="row_heading level0 row88" >88</th>
      <td id="T_a86e0_row88_col0" class="data row88 col0" ></td>
      <td id="T_a86e0_row88_col1" class="data row88 col1" >building = hospital</td>
      <td id="T_a86e0_row88_col2" class="data row88 col2" >398</td>
      <td id="T_a86e0_row88_col3" class="data row88 col3" >68</td>
      <td id="T_a86e0_row88_col4" class="data row88 col4" >53</td>
      <td id="T_a86e0_row88_col5" class="data row88 col5" >0.170854</td>
      <td id="T_a86e0_row88_col6" class="data row88 col6" >0.133166</td>
      <td id="T_a86e0_row88_col7" class="data row88 col7" >294</td>
      <td id="T_a86e0_row88_col8" class="data row88 col8" >63</td>
      <td id="T_a86e0_row88_col9" class="data row88 col9" >48</td>
      <td id="T_a86e0_row88_col10" class="data row88 col10" >0.214286</td>
      <td id="T_a86e0_row88_col11" class="data row88 col11" >0.163265</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row89" class="row_heading level0 row89" >89</th>
      <td id="T_a86e0_row89_col0" class="data row89 col0" ></td>
      <td id="T_a86e0_row89_col1" class="data row89 col1" >building = warehouse</td>
      <td id="T_a86e0_row89_col2" class="data row89 col2" >232</td>
      <td id="T_a86e0_row89_col3" class="data row89 col3" >11</td>
      <td id="T_a86e0_row89_col4" class="data row89 col4" >19</td>
      <td id="T_a86e0_row89_col5" class="data row89 col5" >0.047414</td>
      <td id="T_a86e0_row89_col6" class="data row89 col6" >0.081897</td>
      <td id="T_a86e0_row89_col7" class="data row89 col7" >164</td>
      <td id="T_a86e0_row89_col8" class="data row89 col8" >9</td>
      <td id="T_a86e0_row89_col9" class="data row89 col9" >14</td>
      <td id="T_a86e0_row89_col10" class="data row89 col10" >0.054878</td>
      <td id="T_a86e0_row89_col11" class="data row89 col11" >0.085366</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row90" class="row_heading level0 row90" >90</th>
      <td id="T_a86e0_row90_col0" class="data row90 col0" ></td>
      <td id="T_a86e0_row90_col1" class="data row90 col1" >building = *</td>
      <td id="T_a86e0_row90_col2" class="data row90 col2" >24120</td>
      <td id="T_a86e0_row90_col3" class="data row90 col3" >3121</td>
      <td id="T_a86e0_row90_col4" class="data row90 col4" >3546</td>
      <td id="T_a86e0_row90_col5" class="data row90 col5" >0.129395</td>
      <td id="T_a86e0_row90_col6" class="data row90 col6" >0.147015</td>
      <td id="T_a86e0_row90_col7" class="data row90 col7" >13978</td>
      <td id="T_a86e0_row90_col8" class="data row90 col8" >2313</td>
      <td id="T_a86e0_row90_col9" class="data row90 col9" >2682</td>
      <td id="T_a86e0_row90_col10" class="data row90 col10" >0.165474</td>
      <td id="T_a86e0_row90_col11" class="data row90 col11" >0.191873</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row91" class="row_heading level0 row91" >91</th>
      <td id="T_a86e0_row91_col0" class="data row91 col0" >#</td>
      <td id="T_a86e0_row91_col1" class="data row91 col1" >tourism</td>
      <td id="T_a86e0_row91_col2" class="data row91 col2" >13850</td>
      <td id="T_a86e0_row91_col3" class="data row91 col3" >5470</td>
      <td id="T_a86e0_row91_col4" class="data row91 col4" >4747</td>
      <td id="T_a86e0_row91_col5" class="data row91 col5" >0.394946</td>
      <td id="T_a86e0_row91_col6" class="data row91 col6" >0.342744</td>
      <td id="T_a86e0_row91_col7" class="data row91 col7" >9829</td>
      <td id="T_a86e0_row91_col8" class="data row91 col8" >3411</td>
      <td id="T_a86e0_row91_col9" class="data row91 col9" >3349</td>
      <td id="T_a86e0_row91_col10" class="data row91 col10" >0.347034</td>
      <td id="T_a86e0_row91_col11" class="data row91 col11" >0.340726</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row92" class="row_heading level0 row92" >92</th>
      <td id="T_a86e0_row92_col0" class="data row92 col0" ></td>
      <td id="T_a86e0_row92_col1" class="data row92 col1" >tourism = *</td>
      <td id="T_a86e0_row92_col2" class="data row92 col2" >9022</td>
      <td id="T_a86e0_row92_col3" class="data row92 col3" >4293</td>
      <td id="T_a86e0_row92_col4" class="data row92 col4" >3675</td>
      <td id="T_a86e0_row92_col5" class="data row92 col5" >0.475837</td>
      <td id="T_a86e0_row92_col6" class="data row92 col6" >0.407338</td>
      <td id="T_a86e0_row92_col7" class="data row92 col7" >6478</td>
      <td id="T_a86e0_row92_col8" class="data row92 col8" >2501</td>
      <td id="T_a86e0_row92_col9" class="data row92 col9" >2507</td>
      <td id="T_a86e0_row92_col10" class="data row92 col10" >0.386076</td>
      <td id="T_a86e0_row92_col11" class="data row92 col11" >0.387002</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row93" class="row_heading level0 row93" >93</th>
      <td id="T_a86e0_row93_col0" class="data row93 col0" ></td>
      <td id="T_a86e0_row93_col1" class="data row93 col1" >historic = *</td>
      <td id="T_a86e0_row93_col2" class="data row93 col2" >5302</td>
      <td id="T_a86e0_row93_col3" class="data row93 col3" >1524</td>
      <td id="T_a86e0_row93_col4" class="data row93 col4" >1391</td>
      <td id="T_a86e0_row93_col5" class="data row93 col5" >0.287439</td>
      <td id="T_a86e0_row93_col6" class="data row93 col6" >0.262354</td>
      <td id="T_a86e0_row93_col7" class="data row93 col7" >3868</td>
      <td id="T_a86e0_row93_col8" class="data row93 col8" >1243</td>
      <td id="T_a86e0_row93_col9" class="data row93 col9" >1145</td>
      <td id="T_a86e0_row93_col10" class="data row93 col10" >0.321355</td>
      <td id="T_a86e0_row93_col11" class="data row93 col11" >0.296019</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row94" class="row_heading level0 row94" >94</th>
      <td id="T_a86e0_row94_col0" class="data row94 col0" ></td>
      <td id="T_a86e0_row94_col1" class="data row94 col1" >memorial = *</td>
      <td id="T_a86e0_row94_col2" class="data row94 col2" >1597</td>
      <td id="T_a86e0_row94_col3" class="data row94 col3" >346</td>
      <td id="T_a86e0_row94_col4" class="data row94 col4" >338</td>
      <td id="T_a86e0_row94_col5" class="data row94 col5" >0.216656</td>
      <td id="T_a86e0_row94_col6" class="data row94 col6" >0.211647</td>
      <td id="T_a86e0_row94_col7" class="data row94 col7" >1280</td>
      <td id="T_a86e0_row94_col8" class="data row94 col8" >312</td>
      <td id="T_a86e0_row94_col9" class="data row94 col9" >304</td>
      <td id="T_a86e0_row94_col10" class="data row94 col10" >0.243750</td>
      <td id="T_a86e0_row94_col11" class="data row94 col11" >0.237500</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row95" class="row_heading level0 row95" >95</th>
      <td id="T_a86e0_row95_col0" class="data row95 col0" ></td>
      <td id="T_a86e0_row95_col1" class="data row95 col1" >ruins = *</td>
      <td id="T_a86e0_row95_col2" class="data row95 col2" >214</td>
      <td id="T_a86e0_row95_col3" class="data row95 col3" >58</td>
      <td id="T_a86e0_row95_col4" class="data row95 col4" >75</td>
      <td id="T_a86e0_row95_col5" class="data row95 col5" >0.271028</td>
      <td id="T_a86e0_row95_col6" class="data row95 col6" >0.350467</td>
      <td id="T_a86e0_row95_col7" class="data row95 col7" >162</td>
      <td id="T_a86e0_row95_col8" class="data row95 col8" >55</td>
      <td id="T_a86e0_row95_col9" class="data row95 col9" >69</td>
      <td id="T_a86e0_row95_col10" class="data row95 col10" >0.339506</td>
      <td id="T_a86e0_row95_col11" class="data row95 col11" >0.425926</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row96" class="row_heading level0 row96" >96</th>
      <td id="T_a86e0_row96_col0" class="data row96 col0" ></td>
      <td id="T_a86e0_row96_col1" class="data row96 col1" >information = *</td>
      <td id="T_a86e0_row96_col2" class="data row96 col2" >971</td>
      <td id="T_a86e0_row96_col3" class="data row96 col3" >718</td>
      <td id="T_a86e0_row96_col4" class="data row96 col4" >685</td>
      <td id="T_a86e0_row96_col5" class="data row96 col5" >0.739444</td>
      <td id="T_a86e0_row96_col6" class="data row96 col6" >0.705458</td>
      <td id="T_a86e0_row96_col7" class="data row96 col7" >284</td>
      <td id="T_a86e0_row96_col8" class="data row96 col8" >81</td>
      <td id="T_a86e0_row96_col9" class="data row96 col9" >49</td>
      <td id="T_a86e0_row96_col10" class="data row96 col10" >0.285211</td>
      <td id="T_a86e0_row96_col11" class="data row96 col11" >0.172535</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row97" class="row_heading level0 row97" >97</th>
      <td id="T_a86e0_row97_col0" class="data row97 col0" ></td>
      <td id="T_a86e0_row97_col1" class="data row97 col1" >attraction = *</td>
      <td id="T_a86e0_row97_col2" class="data row97 col2" >165</td>
      <td id="T_a86e0_row97_col3" class="data row97 col3" >41</td>
      <td id="T_a86e0_row97_col4" class="data row97 col4" >28</td>
      <td id="T_a86e0_row97_col5" class="data row97 col5" >0.248485</td>
      <td id="T_a86e0_row97_col6" class="data row97 col6" >0.169697</td>
      <td id="T_a86e0_row97_col7" class="data row97 col7" >145</td>
      <td id="T_a86e0_row97_col8" class="data row97 col8" >36</td>
      <td id="T_a86e0_row97_col9" class="data row97 col9" >24</td>
      <td id="T_a86e0_row97_col10" class="data row97 col10" >0.248276</td>
      <td id="T_a86e0_row97_col11" class="data row97 col11" >0.165517</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row98" class="row_heading level0 row98" >98</th>
      <td id="T_a86e0_row98_col0" class="data row98 col0" ></td>
      <td id="T_a86e0_row98_col1" class="data row98 col1" >resort = *</td>
      <td id="T_a86e0_row98_col2" class="data row98 col2" >133</td>
      <td id="T_a86e0_row98_col3" class="data row98 col3" >11</td>
      <td id="T_a86e0_row98_col4" class="data row98 col4" >52</td>
      <td id="T_a86e0_row98_col5" class="data row98 col5" >0.082707</td>
      <td id="T_a86e0_row98_col6" class="data row98 col6" >0.390977</td>
      <td id="T_a86e0_row98_col7" class="data row98 col7" >126</td>
      <td id="T_a86e0_row98_col8" class="data row98 col8" >11</td>
      <td id="T_a86e0_row98_col9" class="data row98 col9" >49</td>
      <td id="T_a86e0_row98_col10" class="data row98 col10" >0.087302</td>
      <td id="T_a86e0_row98_col11" class="data row98 col11" >0.388889</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row99" class="row_heading level0 row99" >99</th>
      <td id="T_a86e0_row99_col0" class="data row99 col0" ></td>
      <td id="T_a86e0_row99_col1" class="data row99 col1" >artwork_type = *</td>
      <td id="T_a86e0_row99_col2" class="data row99 col2" >576</td>
      <td id="T_a86e0_row99_col3" class="data row99 col3" >169</td>
      <td id="T_a86e0_row99_col4" class="data row99 col4" >183</td>
      <td id="T_a86e0_row99_col5" class="data row99 col5" >0.293403</td>
      <td id="T_a86e0_row99_col6" class="data row99 col6" >0.317708</td>
      <td id="T_a86e0_row99_col7" class="data row99 col7" >533</td>
      <td id="T_a86e0_row99_col8" class="data row99 col8" >160</td>
      <td id="T_a86e0_row99_col9" class="data row99 col9" >177</td>
      <td id="T_a86e0_row99_col10" class="data row99 col10" >0.300188</td>
      <td id="T_a86e0_row99_col11" class="data row99 col11" >0.332083</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row100" class="row_heading level0 row100" >100</th>
      <td id="T_a86e0_row100_col0" class="data row100 col0" >#</td>
      <td id="T_a86e0_row100_col1" class="data row100 col1" >water</td>
      <td id="T_a86e0_row100_col2" class="data row100 col2" >23403</td>
      <td id="T_a86e0_row100_col3" class="data row100 col3" >15104</td>
      <td id="T_a86e0_row100_col4" class="data row100 col4" >16424</td>
      <td id="T_a86e0_row100_col5" class="data row100 col5" >0.645387</td>
      <td id="T_a86e0_row100_col6" class="data row100 col6" >0.701790</td>
      <td id="T_a86e0_row100_col7" class="data row100 col7" >5491</td>
      <td id="T_a86e0_row100_col8" class="data row100 col8" >2976</td>
      <td id="T_a86e0_row100_col9" class="data row100 col9" >3678</td>
      <td id="T_a86e0_row100_col10" class="data row100 col10" >0.541978</td>
      <td id="T_a86e0_row100_col11" class="data row100 col11" >0.669823</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row101" class="row_heading level0 row101" >101</th>
      <td id="T_a86e0_row101_col0" class="data row101 col0" ></td>
      <td id="T_a86e0_row101_col1" class="data row101 col1" >waterway = drain</td>
      <td id="T_a86e0_row101_col2" class="data row101 col2" >395</td>
      <td id="T_a86e0_row101_col3" class="data row101 col3" >65</td>
      <td id="T_a86e0_row101_col4" class="data row101 col4" >132</td>
      <td id="T_a86e0_row101_col5" class="data row101 col5" >0.164557</td>
      <td id="T_a86e0_row101_col6" class="data row101 col6" >0.334177</td>
      <td id="T_a86e0_row101_col7" class="data row101 col7" >108</td>
      <td id="T_a86e0_row101_col8" class="data row101 col8" >27</td>
      <td id="T_a86e0_row101_col9" class="data row101 col9" >40</td>
      <td id="T_a86e0_row101_col10" class="data row101 col10" >0.250000</td>
      <td id="T_a86e0_row101_col11" class="data row101 col11" >0.370370</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row102" class="row_heading level0 row102" >102</th>
      <td id="T_a86e0_row102_col0" class="data row102 col0" ></td>
      <td id="T_a86e0_row102_col1" class="data row102 col1" >waterway = ditch</td>
      <td id="T_a86e0_row102_col2" class="data row102 col2" >643</td>
      <td id="T_a86e0_row102_col3" class="data row102 col3" >154</td>
      <td id="T_a86e0_row102_col4" class="data row102 col4" >169</td>
      <td id="T_a86e0_row102_col5" class="data row102 col5" >0.239502</td>
      <td id="T_a86e0_row102_col6" class="data row102 col6" >0.262830</td>
      <td id="T_a86e0_row102_col7" class="data row102 col7" >130</td>
      <td id="T_a86e0_row102_col8" class="data row102 col8" >32</td>
      <td id="T_a86e0_row102_col9" class="data row102 col9" >36</td>
      <td id="T_a86e0_row102_col10" class="data row102 col10" >0.246154</td>
      <td id="T_a86e0_row102_col11" class="data row102 col11" >0.276923</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row103" class="row_heading level0 row103" >103</th>
      <td id="T_a86e0_row103_col0" class="data row103 col0" ></td>
      <td id="T_a86e0_row103_col1" class="data row103 col1" >waterway = stream</td>
      <td id="T_a86e0_row103_col2" class="data row103 col2" >6074</td>
      <td id="T_a86e0_row103_col3" class="data row103 col3" >2962</td>
      <td id="T_a86e0_row103_col4" class="data row103 col4" >4274</td>
      <td id="T_a86e0_row103_col5" class="data row103 col5" >0.487652</td>
      <td id="T_a86e0_row103_col6" class="data row103 col6" >0.703655</td>
      <td id="T_a86e0_row103_col7" class="data row103 col7" >1082</td>
      <td id="T_a86e0_row103_col8" class="data row103 col8" >496</td>
      <td id="T_a86e0_row103_col9" class="data row103 col9" >774</td>
      <td id="T_a86e0_row103_col10" class="data row103 col10" >0.458410</td>
      <td id="T_a86e0_row103_col11" class="data row103 col11" >0.715342</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row104" class="row_heading level0 row104" >104</th>
      <td id="T_a86e0_row104_col0" class="data row104 col0" ></td>
      <td id="T_a86e0_row104_col1" class="data row104 col1" >waterway = river</td>
      <td id="T_a86e0_row104_col2" class="data row104 col2" >11964</td>
      <td id="T_a86e0_row104_col3" class="data row104 col3" >9731</td>
      <td id="T_a86e0_row104_col4" class="data row104 col4" >9338</td>
      <td id="T_a86e0_row104_col5" class="data row104 col5" >0.813357</td>
      <td id="T_a86e0_row104_col6" class="data row104 col6" >0.780508</td>
      <td id="T_a86e0_row104_col7" class="data row104 col7" >1816</td>
      <td id="T_a86e0_row104_col8" class="data row104 col8" >1260</td>
      <td id="T_a86e0_row104_col9" class="data row104 col9" >1298</td>
      <td id="T_a86e0_row104_col10" class="data row104 col10" >0.693833</td>
      <td id="T_a86e0_row104_col11" class="data row104 col11" >0.714758</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row105" class="row_heading level0 row105" >105</th>
      <td id="T_a86e0_row105_col0" class="data row105 col0" ></td>
      <td id="T_a86e0_row105_col1" class="data row105 col1" >waterway = canal</td>
      <td id="T_a86e0_row105_col2" class="data row105 col2" >570</td>
      <td id="T_a86e0_row105_col3" class="data row105 col3" >271</td>
      <td id="T_a86e0_row105_col4" class="data row105 col4" >202</td>
      <td id="T_a86e0_row105_col5" class="data row105 col5" >0.475439</td>
      <td id="T_a86e0_row105_col6" class="data row105 col6" >0.354386</td>
      <td id="T_a86e0_row105_col7" class="data row105 col7" >121</td>
      <td id="T_a86e0_row105_col8" class="data row105 col8" >47</td>
      <td id="T_a86e0_row105_col9" class="data row105 col9" >39</td>
      <td id="T_a86e0_row105_col10" class="data row105 col10" >0.388430</td>
      <td id="T_a86e0_row105_col11" class="data row105 col11" >0.322314</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row106" class="row_heading level0 row106" >106</th>
      <td id="T_a86e0_row106_col0" class="data row106 col0" ></td>
      <td id="T_a86e0_row106_col1" class="data row106 col1" >type = waterway</td>
      <td id="T_a86e0_row106_col2" class="data row106 col2" >2043</td>
      <td id="T_a86e0_row106_col3" class="data row106 col3" >1426</td>
      <td id="T_a86e0_row106_col4" class="data row106 col4" >1351</td>
      <td id="T_a86e0_row106_col5" class="data row106 col5" >0.697993</td>
      <td id="T_a86e0_row106_col6" class="data row106 col6" >0.661282</td>
      <td id="T_a86e0_row106_col7" class="data row106 col7" >1807</td>
      <td id="T_a86e0_row106_col8" class="data row106 col8" >1276</td>
      <td id="T_a86e0_row106_col9" class="data row106 col9" >1221</td>
      <td id="T_a86e0_row106_col10" class="data row106 col10" >0.706143</td>
      <td id="T_a86e0_row106_col11" class="data row106 col11" >0.675706</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row107" class="row_heading level0 row107" >107</th>
      <td id="T_a86e0_row107_col0" class="data row107 col0" ></td>
      <td id="T_a86e0_row107_col1" class="data row107 col1" >natural = water</td>
      <td id="T_a86e0_row107_col2" class="data row107 col2" >3124</td>
      <td id="T_a86e0_row107_col3" class="data row107 col3" >1817</td>
      <td id="T_a86e0_row107_col4" class="data row107 col4" >2212</td>
      <td id="T_a86e0_row107_col5" class="data row107 col5" >0.581626</td>
      <td id="T_a86e0_row107_col6" class="data row107 col6" >0.708067</td>
      <td id="T_a86e0_row107_col7" class="data row107 col7" >2538</td>
      <td id="T_a86e0_row107_col8" class="data row107 col8" >1487</td>
      <td id="T_a86e0_row107_col9" class="data row107 col9" >1816</td>
      <td id="T_a86e0_row107_col10" class="data row107 col10" >0.585894</td>
      <td id="T_a86e0_row107_col11" class="data row107 col11" >0.715524</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row108" class="row_heading level0 row108" >108</th>
      <td id="T_a86e0_row108_col0" class="data row108 col0" ></td>
      <td id="T_a86e0_row108_col1" class="data row108 col1" >natural = spring</td>
      <td id="T_a86e0_row108_col2" class="data row108 col2" >589</td>
      <td id="T_a86e0_row108_col3" class="data row108 col3" >89</td>
      <td id="T_a86e0_row108_col4" class="data row108 col4" >81</td>
      <td id="T_a86e0_row108_col5" class="data row108 col5" >0.151104</td>
      <td id="T_a86e0_row108_col6" class="data row108 col6" >0.137521</td>
      <td id="T_a86e0_row108_col7" class="data row108 col7" >530</td>
      <td id="T_a86e0_row108_col8" class="data row108 col8" >75</td>
      <td id="T_a86e0_row108_col9" class="data row108 col9" >79</td>
      <td id="T_a86e0_row108_col10" class="data row108 col10" >0.141509</td>
      <td id="T_a86e0_row108_col11" class="data row108 col11" >0.149057</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row109" class="row_heading level0 row109" >109</th>
      <td id="T_a86e0_row109_col0" class="data row109 col0" ></td>
      <td id="T_a86e0_row109_col1" class="data row109 col1" >waterway = *</td>
      <td id="T_a86e0_row109_col2" class="data row109 col2" >36</td>
      <td id="T_a86e0_row109_col3" class="data row109 col3" >11</td>
      <td id="T_a86e0_row109_col4" class="data row109 col4" >12</td>
      <td id="T_a86e0_row109_col5" class="data row109 col5" >0.305556</td>
      <td id="T_a86e0_row109_col6" class="data row109 col6" >0.333333</td>
      <td id="T_a86e0_row109_col7" class="data row109 col7" >30</td>
      <td id="T_a86e0_row109_col8" class="data row109 col8" >9</td>
      <td id="T_a86e0_row109_col9" class="data row109 col9" >10</td>
      <td id="T_a86e0_row109_col10" class="data row109 col10" >0.300000</td>
      <td id="T_a86e0_row109_col11" class="data row109 col11" >0.333333</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row110" class="row_heading level0 row110" >110</th>
      <td id="T_a86e0_row110_col0" class="data row110 col0" ></td>
      <td id="T_a86e0_row110_col1" class="data row110 col1" >water = *</td>
      <td id="T_a86e0_row110_col2" class="data row110 col2" >3003</td>
      <td id="T_a86e0_row110_col3" class="data row110 col3" >1800</td>
      <td id="T_a86e0_row110_col4" class="data row110 col4" >2192</td>
      <td id="T_a86e0_row110_col5" class="data row110 col5" >0.599401</td>
      <td id="T_a86e0_row110_col6" class="data row110 col6" >0.729937</td>
      <td id="T_a86e0_row110_col7" class="data row110 col7" >2436</td>
      <td id="T_a86e0_row110_col8" class="data row110 col8" >1471</td>
      <td id="T_a86e0_row110_col9" class="data row110 col9" >1797</td>
      <td id="T_a86e0_row110_col10" class="data row110 col10" >0.603859</td>
      <td id="T_a86e0_row110_col11" class="data row110 col11" >0.737685</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row111" class="row_heading level0 row111" >111</th>
      <td id="T_a86e0_row111_col0" class="data row111 col0" >#</td>
      <td id="T_a86e0_row111_col1" class="data row111 col1" >natural</td>
      <td id="T_a86e0_row111_col2" class="data row111 col2" >1507</td>
      <td id="T_a86e0_row111_col3" class="data row111 col3" >412</td>
      <td id="T_a86e0_row111_col4" class="data row111 col4" >641</td>
      <td id="T_a86e0_row111_col5" class="data row111 col5" >0.273391</td>
      <td id="T_a86e0_row111_col6" class="data row111 col6" >0.425348</td>
      <td id="T_a86e0_row111_col7" class="data row111 col7" >1235</td>
      <td id="T_a86e0_row111_col8" class="data row111 col8" >371</td>
      <td id="T_a86e0_row111_col9" class="data row111 col9" >566</td>
      <td id="T_a86e0_row111_col10" class="data row111 col10" >0.300405</td>
      <td id="T_a86e0_row111_col11" class="data row111 col11" >0.458300</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row112" class="row_heading level0 row112" >112</th>
      <td id="T_a86e0_row112_col0" class="data row112 col0" ></td>
      <td id="T_a86e0_row112_col1" class="data row112 col1" >place = island</td>
      <td id="T_a86e0_row112_col2" class="data row112 col2" >11</td>
      <td id="T_a86e0_row112_col3" class="data row112 col3" >3</td>
      <td id="T_a86e0_row112_col4" class="data row112 col4" >3</td>
      <td id="T_a86e0_row112_col5" class="data row112 col5" >0.272727</td>
      <td id="T_a86e0_row112_col6" class="data row112 col6" >0.272727</td>
      <td id="T_a86e0_row112_col7" class="data row112 col7" >11</td>
      <td id="T_a86e0_row112_col8" class="data row112 col8" >3</td>
      <td id="T_a86e0_row112_col9" class="data row112 col9" >3</td>
      <td id="T_a86e0_row112_col10" class="data row112 col10" >0.272727</td>
      <td id="T_a86e0_row112_col11" class="data row112 col11" >0.272727</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row113" class="row_heading level0 row113" >113</th>
      <td id="T_a86e0_row113_col0" class="data row113 col0" ></td>
      <td id="T_a86e0_row113_col1" class="data row113 col1" >place = islet</td>
      <td id="T_a86e0_row113_col2" class="data row113 col2" >87</td>
      <td id="T_a86e0_row113_col3" class="data row113 col3" >47</td>
      <td id="T_a86e0_row113_col4" class="data row113 col4" >79</td>
      <td id="T_a86e0_row113_col5" class="data row113 col5" >0.540230</td>
      <td id="T_a86e0_row113_col6" class="data row113 col6" >0.908046</td>
      <td id="T_a86e0_row113_col7" class="data row113 col7" >77</td>
      <td id="T_a86e0_row113_col8" class="data row113 col8" >43</td>
      <td id="T_a86e0_row113_col9" class="data row113 col9" >69</td>
      <td id="T_a86e0_row113_col10" class="data row113 col10" >0.558442</td>
      <td id="T_a86e0_row113_col11" class="data row113 col11" >0.896104</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row114" class="row_heading level0 row114" >114</th>
      <td id="T_a86e0_row114_col0" class="data row114 col0" ></td>
      <td id="T_a86e0_row114_col1" class="data row114 col1" >natural = *</td>
      <td id="T_a86e0_row114_col2" class="data row114 col2" >1447</td>
      <td id="T_a86e0_row114_col3" class="data row114 col3" >376</td>
      <td id="T_a86e0_row114_col4" class="data row114 col4" >594</td>
      <td id="T_a86e0_row114_col5" class="data row114 col5" >0.259848</td>
      <td id="T_a86e0_row114_col6" class="data row114 col6" >0.410504</td>
      <td id="T_a86e0_row114_col7" class="data row114 col7" >1185</td>
      <td id="T_a86e0_row114_col8" class="data row114 col8" >338</td>
      <td id="T_a86e0_row114_col9" class="data row114 col9" >528</td>
      <td id="T_a86e0_row114_col10" class="data row114 col10" >0.285232</td>
      <td id="T_a86e0_row114_col11" class="data row114 col11" >0.445570</td>
    </tr>
    <tr>
      <th id="T_a86e0_level0_row115" class="row_heading level0 row115" >115</th>
      <td id="T_a86e0_row115_col0" class="data row115 col0" >#</td>
      <td id="T_a86e0_row115_col1" class="data row115 col1" >other</td>
      <td id="T_a86e0_row115_col2" class="data row115 col2" >4928</td>
      <td id="T_a86e0_row115_col3" class="data row115 col3" >462</td>
      <td id="T_a86e0_row115_col4" class="data row115 col4" >704</td>
      <td id="T_a86e0_row115_col5" class="data row115 col5" >0.093750</td>
      <td id="T_a86e0_row115_col6" class="data row115 col6" >0.142857</td>
      <td id="T_a86e0_row115_col7" class="data row115 col7" >3305</td>
      <td id="T_a86e0_row115_col8" class="data row115 col8" >398</td>
      <td id="T_a86e0_row115_col9" class="data row115 col9" >594</td>
      <td id="T_a86e0_row115_col10" class="data row115 col10" >0.120424</td>
      <td id="T_a86e0_row115_col11" class="data row115 col11" >0.179728</td>
    </tr>
  </tbody>
</table>




## Падлічам статыстыку для выгрузкі ў postgis
- вынік будзе больш дакладным, але можа ня ўлічываць дачыненьні што не пераносяцца ў postgis


```python
# query_template = """
# SELECT '{category}' AS category, {num} AS num, g.tags->'name' AS name, g.tags->'name:be' AS name_be, g.tags->'name:ru' AS name_ru
# FROM {table} g
# INNER JOIN planet_osm_polygon p
# ON ST_Intersects(g.way, p.way)
# WHERE p.osm_id = -59065
# AND g.tags->'name' ~ '({cyr})'
# AND {condition}
# """
query_template = """
SELECT '{category}' AS category, {num} AS num, g.tags->'name' AS name, g.tags->'name:be' AS name_be, g.tags->'name:ru' AS name_ru
FROM {table} g
WHERE {condition}
-- ({cyr})
"""
# tables = ['planet_osm_line', 'planet_osm_point', 'planet_osm_polygon']
tables = ['planet_osm_data']
cyr = '|'.join(cirylic_chars)

queries = []
exclude = []
for category, group in categories_rules2.items():
    conditions = []
    for i, (k, eq, vv) in enumerate(group):
        if vv:
            eq_str = 'IN' if eq else 'NOT IN'
            vv_str = ','.join(f"'{v}'" for v in vv)
            condition = f"g.tags->'{k}' {eq_str} ({vv_str})"
        elif not eq:
            condition = f"g.tags->'{k}' IS NOT NULL"
        else:
            raise ValueError()
        conditions.append(condition)
        exclude.append(condition)
        for table in tables:
            query = query_template.format(category=category, num=i, table=table, cyr=cyr, condition=condition)
            queries.append(query)
    condition = ' OR '.join(f'({c})' for c in conditions)
    for table in tables:
        query = query_template.format(category=category, num=-1, table=table, cyr=cyr, condition=condition)
        queries.append(query)
condition = ' OR '.join(f'({c})' for c in conditions)
for table in tables:
    query = query_template.format(category='other', num=-1, table=table, cyr=cyr, condition=f'NOT ({condition})')
    queries.append(query)
query = ' UNION ALL '.join(queries)

print(len(queries))

```

    116



```python
key_counter = defaultdict(lambda: defaultdict(list))

view_creation = """
CREATE MATERIALIZED VIEW IF NOT EXISTS planet_osm_data AS

SELECT g.tags
FROM planet_osm_point g
INNER JOIN planet_osm_polygon p
ON ST_Intersects(g.way, p.way)
WHERE p.osm_id = -59065
AND g.tags->'name' ~ '({cyr})'

UNION ALL

SELECT g.tags
FROM planet_osm_line g
INNER JOIN planet_osm_polygon p
ON ST_Intersects(g.way, p.way)
WHERE p.osm_id = -59065
AND g.tags->'name' ~ '({cyr})'

UNION ALL

SELECT g.tags
FROM planet_osm_polygon g
INNER JOIN planet_osm_polygon p
ON ST_Intersects(g.way, p.way)
WHERE p.osm_id = -59065
AND g.tags->'name' ~ '({cyr})'
""".format(cyr=cyr)
index_creation = """
CREATE INDEX IF NOT EXISTS "planet_osm_data_tags_idx" ON planet_osm_data USING GIN (tags)
"""

conn = psycopg2.connect(
    host=os.environ['POSTGRES_HOST'],
    dbname=os.environ['POSTGRES_DB'],
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD'],
)
cur = conn.cursor()
cur.execute(view_creation)
cur.execute(index_creation)
for i, query in enumerate(queries, 1):
    cur.execute(query)
    records = cur.fetchall()
    for category, num, name, name_be, name_ru in records:
        key = (category,) if num == -1 else (category, num)
        key_counter[key]['name'].append(name)
        if name_be is not None:
            key_counter[key]['name:be'].append(name_be)
        if name_ru is not None:
            key_counter[key]['name:ru'].append(name_ru)
cur.close()
conn.close()
```


```python
data = []
for c in list(categories_rules) + ['other']:
    name_cnt = len(key_counter[(c,)]['name'])
    name_uniq = len(set(key_counter[(c,)]['name']))
    name_be_cnt = len(key_counter[(c,)]['name:be'])
    name_be_uniq = len(set(key_counter[(c,)]['name:be']))
    name_ru_cnt = len(key_counter[(c,)]['name:ru'])
    name_ru_uniq = len(set(key_counter[(c,)]['name:ru']))
    data.append([
        '#', c, 
        name_cnt, name_be_cnt, name_ru_cnt, name_be_cnt/(name_cnt or 1), name_ru_cnt/(name_cnt or 1),
        name_uniq, name_be_uniq, name_ru_uniq, name_be_uniq/(name_uniq or 1), name_ru_uniq/(name_uniq or 1),
    ])
    if c == 'other':
        continue
    for i, (k, eq, vv) in enumerate(categories_rules2[c]):
        if eq:
            tag = f'{k} = {list(vv)[0]}'
        else:
            tag = f'{k} = *'
        name_cnt = len(key_counter[(c, i)]['name'])
        name_uniq = len(set(key_counter[(c, i)]['name']))
        name_be_cnt = len(key_counter[(c, i)]['name:be'])
        name_be_uniq = len(set(key_counter[(c, i)]['name:be']))
        name_ru_cnt = len(key_counter[(c, i)]['name:ru'])
        name_ru_uniq = len(set(key_counter[(c, i)]['name:ru']))
        data.append([
            '', tag, 
            name_cnt, name_be_cnt, name_ru_cnt, name_be_cnt/(name_cnt or 1), name_ru_cnt/(name_cnt or 1),
            name_uniq, name_be_uniq, name_ru_uniq, name_be_uniq/(name_uniq or 1), name_ru_uniq/(name_uniq or 1),
        ])

```


```python
df = pd.DataFrame(data, columns=[
    'lvl', 'category', 
    'all name', 'all name:be', 'all name:ru', 'all name:be%', 'all name:ru%',
    'uniq name', 'uniq name:be', 'uniq name:ru', 'uniq name:be%', 'uniq name:ru%',
])
df.to_csv('postgis.csv')
df.style.set_properties(**{'text-align': 'left'}).background_gradient('YlOrRd', subset=[
    'all name:be%', 'all name:ru%', 'uniq name:be%', 'uniq name:ru%',
]).apply(lambda row: [("font-weight: bold" if row.loc['lvl'] == '#' else '') for _ in row], axis=1)
```





<table id="T_6c98d">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_6c98d_level0_col0" class="col_heading level0 col0" >lvl</th>
      <th id="T_6c98d_level0_col1" class="col_heading level0 col1" >category</th>
      <th id="T_6c98d_level0_col2" class="col_heading level0 col2" >all name</th>
      <th id="T_6c98d_level0_col3" class="col_heading level0 col3" >all name:be</th>
      <th id="T_6c98d_level0_col4" class="col_heading level0 col4" >all name:ru</th>
      <th id="T_6c98d_level0_col5" class="col_heading level0 col5" >all name:be%</th>
      <th id="T_6c98d_level0_col6" class="col_heading level0 col6" >all name:ru%</th>
      <th id="T_6c98d_level0_col7" class="col_heading level0 col7" >uniq name</th>
      <th id="T_6c98d_level0_col8" class="col_heading level0 col8" >uniq name:be</th>
      <th id="T_6c98d_level0_col9" class="col_heading level0 col9" >uniq name:ru</th>
      <th id="T_6c98d_level0_col10" class="col_heading level0 col10" >uniq name:be%</th>
      <th id="T_6c98d_level0_col11" class="col_heading level0 col11" >uniq name:ru%</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_6c98d_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_6c98d_row0_col0" class="data row0 col0" >#</td>
      <td id="T_6c98d_row0_col1" class="data row0 col1" >place</td>
      <td id="T_6c98d_row0_col2" class="data row0 col2" >76828</td>
      <td id="T_6c98d_row0_col3" class="data row0 col3" >75123</td>
      <td id="T_6c98d_row0_col4" class="data row0 col4" >76675</td>
      <td id="T_6c98d_row0_col5" class="data row0 col5" >0.977808</td>
      <td id="T_6c98d_row0_col6" class="data row0 col6" >0.998009</td>
      <td id="T_6c98d_row0_col7" class="data row0 col7" >16665</td>
      <td id="T_6c98d_row0_col8" class="data row0 col8" >15834</td>
      <td id="T_6c98d_row0_col9" class="data row0 col9" >16572</td>
      <td id="T_6c98d_row0_col10" class="data row0 col10" >0.950135</td>
      <td id="T_6c98d_row0_col11" class="data row0 col11" >0.994419</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_6c98d_row1_col0" class="data row1 col0" ></td>
      <td id="T_6c98d_row1_col1" class="data row1 col1" >place = city</td>
      <td id="T_6c98d_row1_col2" class="data row1 col2" >75</td>
      <td id="T_6c98d_row1_col3" class="data row1 col3" >75</td>
      <td id="T_6c98d_row1_col4" class="data row1 col4" >75</td>
      <td id="T_6c98d_row1_col5" class="data row1 col5" >1.000000</td>
      <td id="T_6c98d_row1_col6" class="data row1 col6" >1.000000</td>
      <td id="T_6c98d_row1_col7" class="data row1 col7" >16</td>
      <td id="T_6c98d_row1_col8" class="data row1 col8" >16</td>
      <td id="T_6c98d_row1_col9" class="data row1 col9" >16</td>
      <td id="T_6c98d_row1_col10" class="data row1 col10" >1.000000</td>
      <td id="T_6c98d_row1_col11" class="data row1 col11" >1.000000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_6c98d_row2_col0" class="data row2 col0" ></td>
      <td id="T_6c98d_row2_col1" class="data row2 col1" >place = town</td>
      <td id="T_6c98d_row2_col2" class="data row2 col2" >474</td>
      <td id="T_6c98d_row2_col3" class="data row2 col3" >473</td>
      <td id="T_6c98d_row2_col4" class="data row2 col4" >473</td>
      <td id="T_6c98d_row2_col5" class="data row2 col5" >0.997890</td>
      <td id="T_6c98d_row2_col6" class="data row2 col6" >0.997890</td>
      <td id="T_6c98d_row2_col7" class="data row2 col7" >137</td>
      <td id="T_6c98d_row2_col8" class="data row2 col8" >138</td>
      <td id="T_6c98d_row2_col9" class="data row2 col9" >137</td>
      <td id="T_6c98d_row2_col10" class="data row2 col10" >1.007299</td>
      <td id="T_6c98d_row2_col11" class="data row2 col11" >1.000000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_6c98d_row3_col0" class="data row3 col0" ></td>
      <td id="T_6c98d_row3_col1" class="data row3 col1" >place = village</td>
      <td id="T_6c98d_row3_col2" class="data row3 col2" >8578</td>
      <td id="T_6c98d_row3_col3" class="data row3 col3" >8566</td>
      <td id="T_6c98d_row3_col4" class="data row3 col4" >8576</td>
      <td id="T_6c98d_row3_col5" class="data row3 col5" >0.998601</td>
      <td id="T_6c98d_row3_col6" class="data row3 col6" >0.999767</td>
      <td id="T_6c98d_row3_col7" class="data row3 col7" >2198</td>
      <td id="T_6c98d_row3_col8" class="data row3 col8" >2205</td>
      <td id="T_6c98d_row3_col9" class="data row3 col9" >2197</td>
      <td id="T_6c98d_row3_col10" class="data row3 col10" >1.003185</td>
      <td id="T_6c98d_row3_col11" class="data row3 col11" >0.999545</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_6c98d_row4_col0" class="data row4 col0" ></td>
      <td id="T_6c98d_row4_col1" class="data row4 col1" >place = hamlet</td>
      <td id="T_6c98d_row4_col2" class="data row4 col2" >63810</td>
      <td id="T_6c98d_row4_col3" class="data row4 col3" >63699</td>
      <td id="T_6c98d_row4_col4" class="data row4 col4" >63778</td>
      <td id="T_6c98d_row4_col5" class="data row4 col5" >0.998260</td>
      <td id="T_6c98d_row4_col6" class="data row4 col6" >0.999499</td>
      <td id="T_6c98d_row4_col7" class="data row4 col7" >13487</td>
      <td id="T_6c98d_row4_col8" class="data row4 col8" >13603</td>
      <td id="T_6c98d_row4_col9" class="data row4 col9" >13483</td>
      <td id="T_6c98d_row4_col10" class="data row4 col10" >1.008601</td>
      <td id="T_6c98d_row4_col11" class="data row4 col11" >0.999703</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_6c98d_row5_col0" class="data row5 col0" ></td>
      <td id="T_6c98d_row5_col1" class="data row5 col1" >place = isolated_dwelling</td>
      <td id="T_6c98d_row5_col2" class="data row5 col2" >2058</td>
      <td id="T_6c98d_row5_col3" class="data row5 col3" >1944</td>
      <td id="T_6c98d_row5_col4" class="data row5 col4" >2037</td>
      <td id="T_6c98d_row5_col5" class="data row5 col5" >0.944606</td>
      <td id="T_6c98d_row5_col6" class="data row5 col6" >0.989796</td>
      <td id="T_6c98d_row5_col7" class="data row5 col7" >629</td>
      <td id="T_6c98d_row5_col8" class="data row5 col8" >584</td>
      <td id="T_6c98d_row5_col9" class="data row5 col9" >612</td>
      <td id="T_6c98d_row5_col10" class="data row5 col10" >0.928458</td>
      <td id="T_6c98d_row5_col11" class="data row5 col11" >0.972973</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_6c98d_row6_col0" class="data row6 col0" ></td>
      <td id="T_6c98d_row6_col1" class="data row6 col1" >place = farm</td>
      <td id="T_6c98d_row6_col2" class="data row6 col2" >11</td>
      <td id="T_6c98d_row6_col3" class="data row6 col3" >4</td>
      <td id="T_6c98d_row6_col4" class="data row6 col4" >4</td>
      <td id="T_6c98d_row6_col5" class="data row6 col5" >0.363636</td>
      <td id="T_6c98d_row6_col6" class="data row6 col6" >0.363636</td>
      <td id="T_6c98d_row6_col7" class="data row6 col7" >10</td>
      <td id="T_6c98d_row6_col8" class="data row6 col8" >3</td>
      <td id="T_6c98d_row6_col9" class="data row6 col9" >3</td>
      <td id="T_6c98d_row6_col10" class="data row6 col10" >0.300000</td>
      <td id="T_6c98d_row6_col11" class="data row6 col11" >0.300000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_6c98d_row7_col0" class="data row7 col0" ></td>
      <td id="T_6c98d_row7_col1" class="data row7 col1" >place = allotments</td>
      <td id="T_6c98d_row7_col2" class="data row7 col2" >1822</td>
      <td id="T_6c98d_row7_col3" class="data row7 col3" >362</td>
      <td id="T_6c98d_row7_col4" class="data row7 col4" >1732</td>
      <td id="T_6c98d_row7_col5" class="data row7 col5" >0.198683</td>
      <td id="T_6c98d_row7_col6" class="data row7 col6" >0.950604</td>
      <td id="T_6c98d_row7_col7" class="data row7 col7" >1363</td>
      <td id="T_6c98d_row7_col8" class="data row7 col8" >298</td>
      <td id="T_6c98d_row7_col9" class="data row7 col9" >1294</td>
      <td id="T_6c98d_row7_col10" class="data row7 col10" >0.218635</td>
      <td id="T_6c98d_row7_col11" class="data row7 col11" >0.949376</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_6c98d_row8_col0" class="data row8 col0" >#</td>
      <td id="T_6c98d_row8_col1" class="data row8 col1" >locality</td>
      <td id="T_6c98d_row8_col2" class="data row8 col2" >12541</td>
      <td id="T_6c98d_row8_col3" class="data row8 col3" >3107</td>
      <td id="T_6c98d_row8_col4" class="data row8 col4" >11997</td>
      <td id="T_6c98d_row8_col5" class="data row8 col5" >0.247747</td>
      <td id="T_6c98d_row8_col6" class="data row8 col6" >0.956622</td>
      <td id="T_6c98d_row8_col7" class="data row8 col7" >8351</td>
      <td id="T_6c98d_row8_col8" class="data row8 col8" >2059</td>
      <td id="T_6c98d_row8_col9" class="data row8 col9" >7962</td>
      <td id="T_6c98d_row8_col10" class="data row8 col10" >0.246557</td>
      <td id="T_6c98d_row8_col11" class="data row8 col11" >0.953419</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_6c98d_row9_col0" class="data row9 col0" ></td>
      <td id="T_6c98d_row9_col1" class="data row9 col1" >place = locality</td>
      <td id="T_6c98d_row9_col2" class="data row9 col2" >12497</td>
      <td id="T_6c98d_row9_col3" class="data row9 col3" >3065</td>
      <td id="T_6c98d_row9_col4" class="data row9 col4" >11953</td>
      <td id="T_6c98d_row9_col5" class="data row9 col5" >0.245259</td>
      <td id="T_6c98d_row9_col6" class="data row9 col6" >0.956470</td>
      <td id="T_6c98d_row9_col7" class="data row9 col7" >8328</td>
      <td id="T_6c98d_row9_col8" class="data row9 col8" >2029</td>
      <td id="T_6c98d_row9_col9" class="data row9 col9" >7939</td>
      <td id="T_6c98d_row9_col10" class="data row9 col10" >0.243636</td>
      <td id="T_6c98d_row9_col11" class="data row9 col11" >0.953290</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_6c98d_row10_col0" class="data row10 col0" ></td>
      <td id="T_6c98d_row10_col1" class="data row10 col1" >abandoned:place = *</td>
      <td id="T_6c98d_row10_col2" class="data row10 col2" >3617</td>
      <td id="T_6c98d_row10_col3" class="data row10 col3" >2423</td>
      <td id="T_6c98d_row10_col4" class="data row10 col4" >3589</td>
      <td id="T_6c98d_row10_col5" class="data row10 col5" >0.669892</td>
      <td id="T_6c98d_row10_col6" class="data row10 col6" >0.992259</td>
      <td id="T_6c98d_row10_col7" class="data row10 col7" >2187</td>
      <td id="T_6c98d_row10_col8" class="data row10 col8" >1550</td>
      <td id="T_6c98d_row10_col9" class="data row10 col9" >2164</td>
      <td id="T_6c98d_row10_col10" class="data row10 col10" >0.708733</td>
      <td id="T_6c98d_row10_col11" class="data row10 col11" >0.989483</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_6c98d_row11_col0" class="data row11 col0" >#</td>
      <td id="T_6c98d_row11_col1" class="data row11 col1" >suburb</td>
      <td id="T_6c98d_row11_col2" class="data row11 col2" >14773</td>
      <td id="T_6c98d_row11_col3" class="data row11 col3" >3268</td>
      <td id="T_6c98d_row11_col4" class="data row11 col4" >5102</td>
      <td id="T_6c98d_row11_col5" class="data row11 col5" >0.221214</td>
      <td id="T_6c98d_row11_col6" class="data row11 col6" >0.345360</td>
      <td id="T_6c98d_row11_col7" class="data row11 col7" >10967</td>
      <td id="T_6c98d_row11_col8" class="data row11 col8" >2430</td>
      <td id="T_6c98d_row11_col9" class="data row11 col9" >3817</td>
      <td id="T_6c98d_row11_col10" class="data row11 col10" >0.221574</td>
      <td id="T_6c98d_row11_col11" class="data row11 col11" >0.348044</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_6c98d_row12_col0" class="data row12 col0" ></td>
      <td id="T_6c98d_row12_col1" class="data row12 col1" >landuse = commercial</td>
      <td id="T_6c98d_row12_col2" class="data row12 col2" >179</td>
      <td id="T_6c98d_row12_col3" class="data row12 col3" >24</td>
      <td id="T_6c98d_row12_col4" class="data row12 col4" >30</td>
      <td id="T_6c98d_row12_col5" class="data row12 col5" >0.134078</td>
      <td id="T_6c98d_row12_col6" class="data row12 col6" >0.167598</td>
      <td id="T_6c98d_row12_col7" class="data row12 col7" >163</td>
      <td id="T_6c98d_row12_col8" class="data row12 col8" >23</td>
      <td id="T_6c98d_row12_col9" class="data row12 col9" >30</td>
      <td id="T_6c98d_row12_col10" class="data row12 col10" >0.141104</td>
      <td id="T_6c98d_row12_col11" class="data row12 col11" >0.184049</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_6c98d_row13_col0" class="data row13 col0" ></td>
      <td id="T_6c98d_row13_col1" class="data row13 col1" >landuse = construction</td>
      <td id="T_6c98d_row13_col2" class="data row13 col2" >166</td>
      <td id="T_6c98d_row13_col3" class="data row13 col3" >18</td>
      <td id="T_6c98d_row13_col4" class="data row13 col4" >20</td>
      <td id="T_6c98d_row13_col5" class="data row13 col5" >0.108434</td>
      <td id="T_6c98d_row13_col6" class="data row13 col6" >0.120482</td>
      <td id="T_6c98d_row13_col7" class="data row13 col7" >155</td>
      <td id="T_6c98d_row13_col8" class="data row13 col8" >17</td>
      <td id="T_6c98d_row13_col9" class="data row13 col9" >20</td>
      <td id="T_6c98d_row13_col10" class="data row13 col10" >0.109677</td>
      <td id="T_6c98d_row13_col11" class="data row13 col11" >0.129032</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_6c98d_row14_col0" class="data row14 col0" ></td>
      <td id="T_6c98d_row14_col1" class="data row14 col1" >landuse = education</td>
      <td id="T_6c98d_row14_col2" class="data row14 col2" >803</td>
      <td id="T_6c98d_row14_col3" class="data row14 col3" >152</td>
      <td id="T_6c98d_row14_col4" class="data row14 col4" >164</td>
      <td id="T_6c98d_row14_col5" class="data row14 col5" >0.189290</td>
      <td id="T_6c98d_row14_col6" class="data row14 col6" >0.204234</td>
      <td id="T_6c98d_row14_col7" class="data row14 col7" >795</td>
      <td id="T_6c98d_row14_col8" class="data row14 col8" >150</td>
      <td id="T_6c98d_row14_col9" class="data row14 col9" >163</td>
      <td id="T_6c98d_row14_col10" class="data row14 col10" >0.188679</td>
      <td id="T_6c98d_row14_col11" class="data row14 col11" >0.205031</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_6c98d_row15_col0" class="data row15 col0" ></td>
      <td id="T_6c98d_row15_col1" class="data row15 col1" >landuse = industrial</td>
      <td id="T_6c98d_row15_col2" class="data row15 col2" >4272</td>
      <td id="T_6c98d_row15_col3" class="data row15 col3" >364</td>
      <td id="T_6c98d_row15_col4" class="data row15 col4" >382</td>
      <td id="T_6c98d_row15_col5" class="data row15 col5" >0.085206</td>
      <td id="T_6c98d_row15_col6" class="data row15 col6" >0.089419</td>
      <td id="T_6c98d_row15_col7" class="data row15 col7" >3697</td>
      <td id="T_6c98d_row15_col8" class="data row15 col8" >333</td>
      <td id="T_6c98d_row15_col9" class="data row15 col9" >370</td>
      <td id="T_6c98d_row15_col10" class="data row15 col10" >0.090073</td>
      <td id="T_6c98d_row15_col11" class="data row15 col11" >0.100081</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_6c98d_row16_col0" class="data row16 col0" ></td>
      <td id="T_6c98d_row16_col1" class="data row16 col1" >landuse = residential</td>
      <td id="T_6c98d_row16_col2" class="data row16 col2" >853</td>
      <td id="T_6c98d_row16_col3" class="data row16 col3" >395</td>
      <td id="T_6c98d_row16_col4" class="data row16 col4" >357</td>
      <td id="T_6c98d_row16_col5" class="data row16 col5" >0.463072</td>
      <td id="T_6c98d_row16_col6" class="data row16 col6" >0.418523</td>
      <td id="T_6c98d_row16_col7" class="data row16 col7" >747</td>
      <td id="T_6c98d_row16_col8" class="data row16 col8" >352</td>
      <td id="T_6c98d_row16_col9" class="data row16 col9" >325</td>
      <td id="T_6c98d_row16_col10" class="data row16 col10" >0.471218</td>
      <td id="T_6c98d_row16_col11" class="data row16 col11" >0.435074</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_6c98d_row17_col0" class="data row17 col0" ></td>
      <td id="T_6c98d_row17_col1" class="data row17 col1" >landuse = retail</td>
      <td id="T_6c98d_row17_col2" class="data row17 col2" >235</td>
      <td id="T_6c98d_row17_col3" class="data row17 col3" >54</td>
      <td id="T_6c98d_row17_col4" class="data row17 col4" >60</td>
      <td id="T_6c98d_row17_col5" class="data row17 col5" >0.229787</td>
      <td id="T_6c98d_row17_col6" class="data row17 col6" >0.255319</td>
      <td id="T_6c98d_row17_col7" class="data row17 col7" >149</td>
      <td id="T_6c98d_row17_col8" class="data row17 col8" >35</td>
      <td id="T_6c98d_row17_col9" class="data row17 col9" >43</td>
      <td id="T_6c98d_row17_col10" class="data row17 col10" >0.234899</td>
      <td id="T_6c98d_row17_col11" class="data row17 col11" >0.288591</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_6c98d_row18_col0" class="data row18 col0" ></td>
      <td id="T_6c98d_row18_col1" class="data row18 col1" >landuse = *</td>
      <td id="T_6c98d_row18_col2" class="data row18 col2" >6174</td>
      <td id="T_6c98d_row18_col3" class="data row18 col3" >1059</td>
      <td id="T_6c98d_row18_col4" class="data row18 col4" >2562</td>
      <td id="T_6c98d_row18_col5" class="data row18 col5" >0.171526</td>
      <td id="T_6c98d_row18_col6" class="data row18 col6" >0.414966</td>
      <td id="T_6c98d_row18_col7" class="data row18 col7" >4212</td>
      <td id="T_6c98d_row18_col8" class="data row18 col8" >773</td>
      <td id="T_6c98d_row18_col9" class="data row18 col9" >2015</td>
      <td id="T_6c98d_row18_col10" class="data row18 col10" >0.183523</td>
      <td id="T_6c98d_row18_col11" class="data row18 col11" >0.478395</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_6c98d_row19_col0" class="data row19 col0" ></td>
      <td id="T_6c98d_row19_col1" class="data row19 col1" >place = *</td>
      <td id="T_6c98d_row19_col2" class="data row19 col2" >2118</td>
      <td id="T_6c98d_row19_col3" class="data row19 col3" >1262</td>
      <td id="T_6c98d_row19_col4" class="data row19 col4" >1598</td>
      <td id="T_6c98d_row19_col5" class="data row19 col5" >0.595845</td>
      <td id="T_6c98d_row19_col6" class="data row19 col6" >0.754485</td>
      <td id="T_6c98d_row19_col7" class="data row19 col7" >1436</td>
      <td id="T_6c98d_row19_col8" class="data row19 col8" >893</td>
      <td id="T_6c98d_row19_col9" class="data row19 col9" >1047</td>
      <td id="T_6c98d_row19_col10" class="data row19 col10" >0.621866</td>
      <td id="T_6c98d_row19_col11" class="data row19 col11" >0.729109</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_6c98d_row20_col0" class="data row20 col0" ></td>
      <td id="T_6c98d_row20_col1" class="data row20 col1" >residential = *</td>
      <td id="T_6c98d_row20_col2" class="data row20 col2" >691</td>
      <td id="T_6c98d_row20_col3" class="data row20 col3" >337</td>
      <td id="T_6c98d_row20_col4" class="data row20 col4" >303</td>
      <td id="T_6c98d_row20_col5" class="data row20 col5" >0.487699</td>
      <td id="T_6c98d_row20_col6" class="data row20 col6" >0.438495</td>
      <td id="T_6c98d_row20_col7" class="data row20 col7" >607</td>
      <td id="T_6c98d_row20_col8" class="data row20 col8" >299</td>
      <td id="T_6c98d_row20_col9" class="data row20 col9" >275</td>
      <td id="T_6c98d_row20_col10" class="data row20 col10" >0.492586</td>
      <td id="T_6c98d_row20_col11" class="data row20 col11" >0.453048</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_6c98d_row21_col0" class="data row21 col0" ></td>
      <td id="T_6c98d_row21_col1" class="data row21 col1" >industrial = *</td>
      <td id="T_6c98d_row21_col2" class="data row21 col2" >460</td>
      <td id="T_6c98d_row21_col3" class="data row21 col3" >34</td>
      <td id="T_6c98d_row21_col4" class="data row21 col4" >46</td>
      <td id="T_6c98d_row21_col5" class="data row21 col5" >0.073913</td>
      <td id="T_6c98d_row21_col6" class="data row21 col6" >0.100000</td>
      <td id="T_6c98d_row21_col7" class="data row21 col7" >368</td>
      <td id="T_6c98d_row21_col8" class="data row21 col8" >32</td>
      <td id="T_6c98d_row21_col9" class="data row21 col9" >44</td>
      <td id="T_6c98d_row21_col10" class="data row21 col10" >0.086957</td>
      <td id="T_6c98d_row21_col11" class="data row21 col11" >0.119565</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_6c98d_row22_col0" class="data row22 col0" >#</td>
      <td id="T_6c98d_row22_col1" class="data row22 col1" >admin</td>
      <td id="T_6c98d_row22_col2" class="data row22 col2" >57537</td>
      <td id="T_6c98d_row22_col3" class="data row22 col3" >57035</td>
      <td id="T_6c98d_row22_col4" class="data row22 col4" >57164</td>
      <td id="T_6c98d_row22_col5" class="data row22 col5" >0.991275</td>
      <td id="T_6c98d_row22_col6" class="data row22 col6" >0.993517</td>
      <td id="T_6c98d_row22_col7" class="data row22 col7" >16920</td>
      <td id="T_6c98d_row22_col8" class="data row22 col8" >16869</td>
      <td id="T_6c98d_row22_col9" class="data row22 col9" >16796</td>
      <td id="T_6c98d_row22_col10" class="data row22 col10" >0.996986</td>
      <td id="T_6c98d_row22_col11" class="data row22 col11" >0.992671</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_6c98d_row23_col0" class="data row23 col0" ></td>
      <td id="T_6c98d_row23_col1" class="data row23 col1" >boundary = administrative</td>
      <td id="T_6c98d_row23_col2" class="data row23 col2" >57535</td>
      <td id="T_6c98d_row23_col3" class="data row23 col3" >57033</td>
      <td id="T_6c98d_row23_col4" class="data row23 col4" >57162</td>
      <td id="T_6c98d_row23_col5" class="data row23 col5" >0.991275</td>
      <td id="T_6c98d_row23_col6" class="data row23 col6" >0.993517</td>
      <td id="T_6c98d_row23_col7" class="data row23 col7" >16920</td>
      <td id="T_6c98d_row23_col8" class="data row23 col8" >16869</td>
      <td id="T_6c98d_row23_col9" class="data row23 col9" >16796</td>
      <td id="T_6c98d_row23_col10" class="data row23 col10" >0.996986</td>
      <td id="T_6c98d_row23_col11" class="data row23 col11" >0.992671</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row24" class="row_heading level0 row24" >24</th>
      <td id="T_6c98d_row24_col0" class="data row24 col0" ></td>
      <td id="T_6c98d_row24_col1" class="data row24 col1" >admin_level = 2</td>
      <td id="T_6c98d_row24_col2" class="data row24 col2" >776</td>
      <td id="T_6c98d_row24_col3" class="data row24 col3" >713</td>
      <td id="T_6c98d_row24_col4" class="data row24 col4" >552</td>
      <td id="T_6c98d_row24_col5" class="data row24 col5" >0.918814</td>
      <td id="T_6c98d_row24_col6" class="data row24 col6" >0.711340</td>
      <td id="T_6c98d_row24_col7" class="data row24 col7" >107</td>
      <td id="T_6c98d_row24_col8" class="data row24 col8" >82</td>
      <td id="T_6c98d_row24_col9" class="data row24 col9" >83</td>
      <td id="T_6c98d_row24_col10" class="data row24 col10" >0.766355</td>
      <td id="T_6c98d_row24_col11" class="data row24 col11" >0.775701</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row25" class="row_heading level0 row25" >25</th>
      <td id="T_6c98d_row25_col0" class="data row25 col0" ></td>
      <td id="T_6c98d_row25_col1" class="data row25 col1" >admin_level = 4</td>
      <td id="T_6c98d_row25_col2" class="data row25 col2" >243</td>
      <td id="T_6c98d_row25_col3" class="data row25 col3" >235</td>
      <td id="T_6c98d_row25_col4" class="data row25 col4" >235</td>
      <td id="T_6c98d_row25_col5" class="data row25 col5" >0.967078</td>
      <td id="T_6c98d_row25_col6" class="data row25 col6" >0.967078</td>
      <td id="T_6c98d_row25_col7" class="data row25 col7" >40</td>
      <td id="T_6c98d_row25_col8" class="data row25 col8" >35</td>
      <td id="T_6c98d_row25_col9" class="data row25 col9" >37</td>
      <td id="T_6c98d_row25_col10" class="data row25 col10" >0.875000</td>
      <td id="T_6c98d_row25_col11" class="data row25 col11" >0.925000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row26" class="row_heading level0 row26" >26</th>
      <td id="T_6c98d_row26_col0" class="data row26 col0" ></td>
      <td id="T_6c98d_row26_col1" class="data row26 col1" >admin_level = 6</td>
      <td id="T_6c98d_row26_col2" class="data row26 col2" >781</td>
      <td id="T_6c98d_row26_col3" class="data row26 col3" >745</td>
      <td id="T_6c98d_row26_col4" class="data row26 col4" >754</td>
      <td id="T_6c98d_row26_col5" class="data row26 col5" >0.953905</td>
      <td id="T_6c98d_row26_col6" class="data row26 col6" >0.965429</td>
      <td id="T_6c98d_row26_col7" class="data row26 col7" >189</td>
      <td id="T_6c98d_row26_col8" class="data row26 col8" >169</td>
      <td id="T_6c98d_row26_col9" class="data row26 col9" >173</td>
      <td id="T_6c98d_row26_col10" class="data row26 col10" >0.894180</td>
      <td id="T_6c98d_row26_col11" class="data row26 col11" >0.915344</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row27" class="row_heading level0 row27" >27</th>
      <td id="T_6c98d_row27_col0" class="data row27 col0" ></td>
      <td id="T_6c98d_row27_col1" class="data row27 col1" >admin_level = 8</td>
      <td id="T_6c98d_row27_col2" class="data row27 col2" >3288</td>
      <td id="T_6c98d_row27_col3" class="data row27 col3" >3229</td>
      <td id="T_6c98d_row27_col4" class="data row27 col4" >3230</td>
      <td id="T_6c98d_row27_col5" class="data row27 col5" >0.982056</td>
      <td id="T_6c98d_row27_col6" class="data row27 col6" >0.982360</td>
      <td id="T_6c98d_row27_col7" class="data row27 col7" >1233</td>
      <td id="T_6c98d_row27_col8" class="data row27 col8" >1195</td>
      <td id="T_6c98d_row27_col9" class="data row27 col9" >1192</td>
      <td id="T_6c98d_row27_col10" class="data row27 col10" >0.969181</td>
      <td id="T_6c98d_row27_col11" class="data row27 col11" >0.966748</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row28" class="row_heading level0 row28" >28</th>
      <td id="T_6c98d_row28_col0" class="data row28 col0" ></td>
      <td id="T_6c98d_row28_col1" class="data row28 col1" >admin_level = 9</td>
      <td id="T_6c98d_row28_col2" class="data row28 col2" >65</td>
      <td id="T_6c98d_row28_col3" class="data row28 col3" >65</td>
      <td id="T_6c98d_row28_col4" class="data row28 col4" >65</td>
      <td id="T_6c98d_row28_col5" class="data row28 col5" >1.000000</td>
      <td id="T_6c98d_row28_col6" class="data row28 col6" >1.000000</td>
      <td id="T_6c98d_row28_col7" class="data row28 col7" >13</td>
      <td id="T_6c98d_row28_col8" class="data row28 col8" >13</td>
      <td id="T_6c98d_row28_col9" class="data row28 col9" >13</td>
      <td id="T_6c98d_row28_col10" class="data row28 col10" >1.000000</td>
      <td id="T_6c98d_row28_col11" class="data row28 col11" >1.000000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row29" class="row_heading level0 row29" >29</th>
      <td id="T_6c98d_row29_col0" class="data row29 col0" ></td>
      <td id="T_6c98d_row29_col1" class="data row29 col1" >admin_level = 10</td>
      <td id="T_6c98d_row29_col2" class="data row29 col2" >52320</td>
      <td id="T_6c98d_row29_col3" class="data row29 col3" >52016</td>
      <td id="T_6c98d_row29_col4" class="data row29 col4" >52296</td>
      <td id="T_6c98d_row29_col5" class="data row29 col5" >0.994190</td>
      <td id="T_6c98d_row29_col6" class="data row29 col6" >0.999541</td>
      <td id="T_6c98d_row29_col7" class="data row29 col7" >15405</td>
      <td id="T_6c98d_row29_col8" class="data row29 col8" >15474</td>
      <td id="T_6c98d_row29_col9" class="data row29 col9" >15399</td>
      <td id="T_6c98d_row29_col10" class="data row29 col10" >1.004479</td>
      <td id="T_6c98d_row29_col11" class="data row29 col11" >0.999611</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row30" class="row_heading level0 row30" >30</th>
      <td id="T_6c98d_row30_col0" class="data row30 col0" ></td>
      <td id="T_6c98d_row30_col1" class="data row30 col1" >admin_level = *</td>
      <td id="T_6c98d_row30_col2" class="data row30 col2" >48</td>
      <td id="T_6c98d_row30_col3" class="data row30 col3" >19</td>
      <td id="T_6c98d_row30_col4" class="data row30 col4" >19</td>
      <td id="T_6c98d_row30_col5" class="data row30 col5" >0.395833</td>
      <td id="T_6c98d_row30_col6" class="data row30 col6" >0.395833</td>
      <td id="T_6c98d_row30_col7" class="data row30 col7" >25</td>
      <td id="T_6c98d_row30_col8" class="data row30 col8" >2</td>
      <td id="T_6c98d_row30_col9" class="data row30 col9" >2</td>
      <td id="T_6c98d_row30_col10" class="data row30 col10" >0.080000</td>
      <td id="T_6c98d_row30_col11" class="data row30 col11" >0.080000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row31" class="row_heading level0 row31" >31</th>
      <td id="T_6c98d_row31_col0" class="data row31 col0" >#</td>
      <td id="T_6c98d_row31_col1" class="data row31 col1" >highway</td>
      <td id="T_6c98d_row31_col2" class="data row31 col2" >90665</td>
      <td id="T_6c98d_row31_col3" class="data row31 col3" >88015</td>
      <td id="T_6c98d_row31_col4" class="data row31 col4" >88635</td>
      <td id="T_6c98d_row31_col5" class="data row31 col5" >0.970772</td>
      <td id="T_6c98d_row31_col6" class="data row31 col6" >0.977610</td>
      <td id="T_6c98d_row31_col7" class="data row31 col7" >11882</td>
      <td id="T_6c98d_row31_col8" class="data row31 col8" >10314</td>
      <td id="T_6c98d_row31_col9" class="data row31 col9" >10916</td>
      <td id="T_6c98d_row31_col10" class="data row31 col10" >0.868036</td>
      <td id="T_6c98d_row31_col11" class="data row31 col11" >0.918701</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row32" class="row_heading level0 row32" >32</th>
      <td id="T_6c98d_row32_col0" class="data row32 col0" ></td>
      <td id="T_6c98d_row32_col1" class="data row32 col1" >highway = motorway</td>
      <td id="T_6c98d_row32_col2" class="data row32 col2" >76</td>
      <td id="T_6c98d_row32_col3" class="data row32 col3" >0</td>
      <td id="T_6c98d_row32_col4" class="data row32 col4" >0</td>
      <td id="T_6c98d_row32_col5" class="data row32 col5" >0.000000</td>
      <td id="T_6c98d_row32_col6" class="data row32 col6" >0.000000</td>
      <td id="T_6c98d_row32_col7" class="data row32 col7" >1</td>
      <td id="T_6c98d_row32_col8" class="data row32 col8" >0</td>
      <td id="T_6c98d_row32_col9" class="data row32 col9" >0</td>
      <td id="T_6c98d_row32_col10" class="data row32 col10" >0.000000</td>
      <td id="T_6c98d_row32_col11" class="data row32 col11" >0.000000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row33" class="row_heading level0 row33" >33</th>
      <td id="T_6c98d_row33_col0" class="data row33 col0" ></td>
      <td id="T_6c98d_row33_col1" class="data row33 col1" >highway = trunk</td>
      <td id="T_6c98d_row33_col2" class="data row33 col2" >1309</td>
      <td id="T_6c98d_row33_col3" class="data row33 col3" >1189</td>
      <td id="T_6c98d_row33_col4" class="data row33 col4" >1191</td>
      <td id="T_6c98d_row33_col5" class="data row33 col5" >0.908327</td>
      <td id="T_6c98d_row33_col6" class="data row33 col6" >0.909855</td>
      <td id="T_6c98d_row33_col7" class="data row33 col7" >138</td>
      <td id="T_6c98d_row33_col8" class="data row33 col8" >121</td>
      <td id="T_6c98d_row33_col9" class="data row33 col9" >122</td>
      <td id="T_6c98d_row33_col10" class="data row33 col10" >0.876812</td>
      <td id="T_6c98d_row33_col11" class="data row33 col11" >0.884058</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row34" class="row_heading level0 row34" >34</th>
      <td id="T_6c98d_row34_col0" class="data row34 col0" ></td>
      <td id="T_6c98d_row34_col1" class="data row34 col1" >highway = primary</td>
      <td id="T_6c98d_row34_col2" class="data row34 col2" >7620</td>
      <td id="T_6c98d_row34_col3" class="data row34 col3" >7492</td>
      <td id="T_6c98d_row34_col4" class="data row34 col4" >7498</td>
      <td id="T_6c98d_row34_col5" class="data row34 col5" >0.983202</td>
      <td id="T_6c98d_row34_col6" class="data row34 col6" >0.983990</td>
      <td id="T_6c98d_row34_col7" class="data row34 col7" >529</td>
      <td id="T_6c98d_row34_col8" class="data row34 col8" >495</td>
      <td id="T_6c98d_row34_col9" class="data row34 col9" >501</td>
      <td id="T_6c98d_row34_col10" class="data row34 col10" >0.935728</td>
      <td id="T_6c98d_row34_col11" class="data row34 col11" >0.947070</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row35" class="row_heading level0 row35" >35</th>
      <td id="T_6c98d_row35_col0" class="data row35 col0" ></td>
      <td id="T_6c98d_row35_col1" class="data row35 col1" >highway = secondary</td>
      <td id="T_6c98d_row35_col2" class="data row35 col2" >7172</td>
      <td id="T_6c98d_row35_col3" class="data row35 col3" >7145</td>
      <td id="T_6c98d_row35_col4" class="data row35 col4" >7150</td>
      <td id="T_6c98d_row35_col5" class="data row35 col5" >0.996235</td>
      <td id="T_6c98d_row35_col6" class="data row35 col6" >0.996933</td>
      <td id="T_6c98d_row35_col7" class="data row35 col7" >730</td>
      <td id="T_6c98d_row35_col8" class="data row35 col8" >712</td>
      <td id="T_6c98d_row35_col9" class="data row35 col9" >720</td>
      <td id="T_6c98d_row35_col10" class="data row35 col10" >0.975342</td>
      <td id="T_6c98d_row35_col11" class="data row35 col11" >0.986301</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row36" class="row_heading level0 row36" >36</th>
      <td id="T_6c98d_row36_col0" class="data row36 col0" ></td>
      <td id="T_6c98d_row36_col1" class="data row36 col1" >highway = tertiary</td>
      <td id="T_6c98d_row36_col2" class="data row36 col2" >10343</td>
      <td id="T_6c98d_row36_col3" class="data row36 col3" >10157</td>
      <td id="T_6c98d_row36_col4" class="data row36 col4" >10226</td>
      <td id="T_6c98d_row36_col5" class="data row36 col5" >0.982017</td>
      <td id="T_6c98d_row36_col6" class="data row36 col6" >0.988688</td>
      <td id="T_6c98d_row36_col7" class="data row36 col7" >1618</td>
      <td id="T_6c98d_row36_col8" class="data row36 col8" >1470</td>
      <td id="T_6c98d_row36_col9" class="data row36 col9" >1536</td>
      <td id="T_6c98d_row36_col10" class="data row36 col10" >0.908529</td>
      <td id="T_6c98d_row36_col11" class="data row36 col11" >0.949320</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row37" class="row_heading level0 row37" >37</th>
      <td id="T_6c98d_row37_col0" class="data row37 col0" ></td>
      <td id="T_6c98d_row37_col1" class="data row37 col1" >highway = unclassified</td>
      <td id="T_6c98d_row37_col2" class="data row37 col2" >2952</td>
      <td id="T_6c98d_row37_col3" class="data row37 col3" >2883</td>
      <td id="T_6c98d_row37_col4" class="data row37 col4" >2884</td>
      <td id="T_6c98d_row37_col5" class="data row37 col5" >0.976626</td>
      <td id="T_6c98d_row37_col6" class="data row37 col6" >0.976965</td>
      <td id="T_6c98d_row37_col7" class="data row37 col7" >903</td>
      <td id="T_6c98d_row37_col8" class="data row37 col8" >847</td>
      <td id="T_6c98d_row37_col9" class="data row37 col9" >856</td>
      <td id="T_6c98d_row37_col10" class="data row37 col10" >0.937984</td>
      <td id="T_6c98d_row37_col11" class="data row37 col11" >0.947951</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row38" class="row_heading level0 row38" >38</th>
      <td id="T_6c98d_row38_col0" class="data row38 col0" ></td>
      <td id="T_6c98d_row38_col1" class="data row38 col1" >highway = residential</td>
      <td id="T_6c98d_row38_col2" class="data row38 col2" >55283</td>
      <td id="T_6c98d_row38_col3" class="data row38 col3" >54379</td>
      <td id="T_6c98d_row38_col4" class="data row38 col4" >54737</td>
      <td id="T_6c98d_row38_col5" class="data row38 col5" >0.983648</td>
      <td id="T_6c98d_row38_col6" class="data row38 col6" >0.990124</td>
      <td id="T_6c98d_row38_col7" class="data row38 col7" >9531</td>
      <td id="T_6c98d_row38_col8" class="data row38 col8" >8759</td>
      <td id="T_6c98d_row38_col9" class="data row38 col9" >9164</td>
      <td id="T_6c98d_row38_col10" class="data row38 col10" >0.919001</td>
      <td id="T_6c98d_row38_col11" class="data row38 col11" >0.961494</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row39" class="row_heading level0 row39" >39</th>
      <td id="T_6c98d_row39_col0" class="data row39 col0" ></td>
      <td id="T_6c98d_row39_col1" class="data row39 col1" >highway = service</td>
      <td id="T_6c98d_row39_col2" class="data row39 col2" >3158</td>
      <td id="T_6c98d_row39_col3" class="data row39 col3" >2857</td>
      <td id="T_6c98d_row39_col4" class="data row39 col4" >3002</td>
      <td id="T_6c98d_row39_col5" class="data row39 col5" >0.904687</td>
      <td id="T_6c98d_row39_col6" class="data row39 col6" >0.950602</td>
      <td id="T_6c98d_row39_col7" class="data row39 col7" >1539</td>
      <td id="T_6c98d_row39_col8" class="data row39 col8" >1300</td>
      <td id="T_6c98d_row39_col9" class="data row39 col9" >1426</td>
      <td id="T_6c98d_row39_col10" class="data row39 col10" >0.844704</td>
      <td id="T_6c98d_row39_col11" class="data row39 col11" >0.926576</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row40" class="row_heading level0 row40" >40</th>
      <td id="T_6c98d_row40_col0" class="data row40 col0" ></td>
      <td id="T_6c98d_row40_col1" class="data row40 col1" >highway = track</td>
      <td id="T_6c98d_row40_col2" class="data row40 col2" >776</td>
      <td id="T_6c98d_row40_col3" class="data row40 col3" >560</td>
      <td id="T_6c98d_row40_col4" class="data row40 col4" >565</td>
      <td id="T_6c98d_row40_col5" class="data row40 col5" >0.721649</td>
      <td id="T_6c98d_row40_col6" class="data row40 col6" >0.728093</td>
      <td id="T_6c98d_row40_col7" class="data row40 col7" >211</td>
      <td id="T_6c98d_row40_col8" class="data row40 col8" >142</td>
      <td id="T_6c98d_row40_col9" class="data row40 col9" >146</td>
      <td id="T_6c98d_row40_col10" class="data row40 col10" >0.672986</td>
      <td id="T_6c98d_row40_col11" class="data row40 col11" >0.691943</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row41" class="row_heading level0 row41" >41</th>
      <td id="T_6c98d_row41_col0" class="data row41 col0" ></td>
      <td id="T_6c98d_row41_col1" class="data row41 col1" >type = associatedStreet</td>
      <td id="T_6c98d_row41_col2" class="data row41 col2" >0</td>
      <td id="T_6c98d_row41_col3" class="data row41 col3" >0</td>
      <td id="T_6c98d_row41_col4" class="data row41 col4" >0</td>
      <td id="T_6c98d_row41_col5" class="data row41 col5" >0.000000</td>
      <td id="T_6c98d_row41_col6" class="data row41 col6" >0.000000</td>
      <td id="T_6c98d_row41_col7" class="data row41 col7" >0</td>
      <td id="T_6c98d_row41_col8" class="data row41 col8" >0</td>
      <td id="T_6c98d_row41_col9" class="data row41 col9" >0</td>
      <td id="T_6c98d_row41_col10" class="data row41 col10" >0.000000</td>
      <td id="T_6c98d_row41_col11" class="data row41 col11" >0.000000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row42" class="row_heading level0 row42" >42</th>
      <td id="T_6c98d_row42_col0" class="data row42 col0" ></td>
      <td id="T_6c98d_row42_col1" class="data row42 col1" >highway = *</td>
      <td id="T_6c98d_row42_col2" class="data row42 col2" >1976</td>
      <td id="T_6c98d_row42_col3" class="data row42 col3" >1353</td>
      <td id="T_6c98d_row42_col4" class="data row42 col4" >1382</td>
      <td id="T_6c98d_row42_col5" class="data row42 col5" >0.684717</td>
      <td id="T_6c98d_row42_col6" class="data row42 col6" >0.699393</td>
      <td id="T_6c98d_row42_col7" class="data row42 col7" >989</td>
      <td id="T_6c98d_row42_col8" class="data row42 col8" >655</td>
      <td id="T_6c98d_row42_col9" class="data row42 col9" >663</td>
      <td id="T_6c98d_row42_col10" class="data row42 col10" >0.662285</td>
      <td id="T_6c98d_row42_col11" class="data row42 col11" >0.670374</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row43" class="row_heading level0 row43" >43</th>
      <td id="T_6c98d_row43_col0" class="data row43 col0" >#</td>
      <td id="T_6c98d_row43_col1" class="data row43 col1" >public_transport</td>
      <td id="T_6c98d_row43_col2" class="data row43 col2" >38331</td>
      <td id="T_6c98d_row43_col3" class="data row43 col3" >19704</td>
      <td id="T_6c98d_row43_col4" class="data row43 col4" >20171</td>
      <td id="T_6c98d_row43_col5" class="data row43 col5" >0.514049</td>
      <td id="T_6c98d_row43_col6" class="data row43 col6" >0.526232</td>
      <td id="T_6c98d_row43_col7" class="data row43 col7" >13630</td>
      <td id="T_6c98d_row43_col8" class="data row43 col8" >7142</td>
      <td id="T_6c98d_row43_col9" class="data row43 col9" >7368</td>
      <td id="T_6c98d_row43_col10" class="data row43 col10" >0.523991</td>
      <td id="T_6c98d_row43_col11" class="data row43 col11" >0.540572</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row44" class="row_heading level0 row44" >44</th>
      <td id="T_6c98d_row44_col0" class="data row44 col0" ></td>
      <td id="T_6c98d_row44_col1" class="data row44 col1" >highway = bus_stop</td>
      <td id="T_6c98d_row44_col2" class="data row44 col2" >17312</td>
      <td id="T_6c98d_row44_col3" class="data row44 col3" >8969</td>
      <td id="T_6c98d_row44_col4" class="data row44 col4" >9437</td>
      <td id="T_6c98d_row44_col5" class="data row44 col5" >0.518080</td>
      <td id="T_6c98d_row44_col6" class="data row44 col6" >0.545113</td>
      <td id="T_6c98d_row44_col7" class="data row44 col7" >8472</td>
      <td id="T_6c98d_row44_col8" class="data row44 col8" >4271</td>
      <td id="T_6c98d_row44_col9" class="data row44 col9" >4511</td>
      <td id="T_6c98d_row44_col10" class="data row44 col10" >0.504131</td>
      <td id="T_6c98d_row44_col11" class="data row44 col11" >0.532460</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row45" class="row_heading level0 row45" >45</th>
      <td id="T_6c98d_row45_col0" class="data row45 col0" ></td>
      <td id="T_6c98d_row45_col1" class="data row45 col1" >type = route</td>
      <td id="T_6c98d_row45_col2" class="data row45 col2" >1</td>
      <td id="T_6c98d_row45_col3" class="data row45 col3" >1</td>
      <td id="T_6c98d_row45_col4" class="data row45 col4" >1</td>
      <td id="T_6c98d_row45_col5" class="data row45 col5" >1.000000</td>
      <td id="T_6c98d_row45_col6" class="data row45 col6" >1.000000</td>
      <td id="T_6c98d_row45_col7" class="data row45 col7" >1</td>
      <td id="T_6c98d_row45_col8" class="data row45 col8" >1</td>
      <td id="T_6c98d_row45_col9" class="data row45 col9" >1</td>
      <td id="T_6c98d_row45_col10" class="data row45 col10" >1.000000</td>
      <td id="T_6c98d_row45_col11" class="data row45 col11" >1.000000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row46" class="row_heading level0 row46" >46</th>
      <td id="T_6c98d_row46_col0" class="data row46 col0" ></td>
      <td id="T_6c98d_row46_col1" class="data row46 col1" >public_transport = *</td>
      <td id="T_6c98d_row46_col2" class="data row46 col2" >23688</td>
      <td id="T_6c98d_row46_col3" class="data row46 col3" >14498</td>
      <td id="T_6c98d_row46_col4" class="data row46 col4" >14996</td>
      <td id="T_6c98d_row46_col5" class="data row46 col5" >0.612040</td>
      <td id="T_6c98d_row46_col6" class="data row46 col6" >0.633063</td>
      <td id="T_6c98d_row46_col7" class="data row46 col7" >7843</td>
      <td id="T_6c98d_row46_col8" class="data row46 col8" >4383</td>
      <td id="T_6c98d_row46_col9" class="data row46 col9" >4528</td>
      <td id="T_6c98d_row46_col10" class="data row46 col10" >0.558842</td>
      <td id="T_6c98d_row46_col11" class="data row46 col11" >0.577330</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row47" class="row_heading level0 row47" >47</th>
      <td id="T_6c98d_row47_col0" class="data row47 col0" ></td>
      <td id="T_6c98d_row47_col1" class="data row47 col1" >route = *</td>
      <td id="T_6c98d_row47_col2" class="data row47 col2" >9352</td>
      <td id="T_6c98d_row47_col3" class="data row47 col3" >3151</td>
      <td id="T_6c98d_row47_col4" class="data row47 col4" >3075</td>
      <td id="T_6c98d_row47_col5" class="data row47 col5" >0.336933</td>
      <td id="T_6c98d_row47_col6" class="data row47 col6" >0.328807</td>
      <td id="T_6c98d_row47_col7" class="data row47 col7" >3737</td>
      <td id="T_6c98d_row47_col8" class="data row47 col8" >1856</td>
      <td id="T_6c98d_row47_col9" class="data row47 col9" >1871</td>
      <td id="T_6c98d_row47_col10" class="data row47 col10" >0.496655</td>
      <td id="T_6c98d_row47_col11" class="data row47 col11" >0.500669</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row48" class="row_heading level0 row48" >48</th>
      <td id="T_6c98d_row48_col0" class="data row48 col0" ></td>
      <td id="T_6c98d_row48_col1" class="data row48 col1" >railway = *</td>
      <td id="T_6c98d_row48_col2" class="data row48 col2" >2830</td>
      <td id="T_6c98d_row48_col3" class="data row48 col3" >1845</td>
      <td id="T_6c98d_row48_col4" class="data row48 col4" >1779</td>
      <td id="T_6c98d_row48_col5" class="data row48 col5" >0.651943</td>
      <td id="T_6c98d_row48_col6" class="data row48 col6" >0.628622</td>
      <td id="T_6c98d_row48_col7" class="data row48 col7" >1341</td>
      <td id="T_6c98d_row48_col8" class="data row48 col8" >1157</td>
      <td id="T_6c98d_row48_col9" class="data row48 col9" >1156</td>
      <td id="T_6c98d_row48_col10" class="data row48 col10" >0.862789</td>
      <td id="T_6c98d_row48_col11" class="data row48 col11" >0.862043</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row49" class="row_heading level0 row49" >49</th>
      <td id="T_6c98d_row49_col0" class="data row49 col0" ></td>
      <td id="T_6c98d_row49_col1" class="data row49 col1" >route_master = *</td>
      <td id="T_6c98d_row49_col2" class="data row49 col2" >3</td>
      <td id="T_6c98d_row49_col3" class="data row49 col3" >0</td>
      <td id="T_6c98d_row49_col4" class="data row49 col4" >0</td>
      <td id="T_6c98d_row49_col5" class="data row49 col5" >0.000000</td>
      <td id="T_6c98d_row49_col6" class="data row49 col6" >0.000000</td>
      <td id="T_6c98d_row49_col7" class="data row49 col7" >2</td>
      <td id="T_6c98d_row49_col8" class="data row49 col8" >0</td>
      <td id="T_6c98d_row49_col9" class="data row49 col9" >0</td>
      <td id="T_6c98d_row49_col10" class="data row49 col10" >0.000000</td>
      <td id="T_6c98d_row49_col11" class="data row49 col11" >0.000000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row50" class="row_heading level0 row50" >50</th>
      <td id="T_6c98d_row50_col0" class="data row50 col0" >#</td>
      <td id="T_6c98d_row50_col1" class="data row50 col1" >infrastructure</td>
      <td id="T_6c98d_row50_col2" class="data row50 col2" >18333</td>
      <td id="T_6c98d_row50_col3" class="data row50 col3" >6758</td>
      <td id="T_6c98d_row50_col4" class="data row50 col4" >7231</td>
      <td id="T_6c98d_row50_col5" class="data row50 col5" >0.368625</td>
      <td id="T_6c98d_row50_col6" class="data row50 col6" >0.394425</td>
      <td id="T_6c98d_row50_col7" class="data row50 col7" >10095</td>
      <td id="T_6c98d_row50_col8" class="data row50 col8" >3050</td>
      <td id="T_6c98d_row50_col9" class="data row50 col9" >3396</td>
      <td id="T_6c98d_row50_col10" class="data row50 col10" >0.302130</td>
      <td id="T_6c98d_row50_col11" class="data row50 col11" >0.336404</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row51" class="row_heading level0 row51" >51</th>
      <td id="T_6c98d_row51_col0" class="data row51 col0" ></td>
      <td id="T_6c98d_row51_col1" class="data row51 col1" >tunnel = *</td>
      <td id="T_6c98d_row51_col2" class="data row51 col2" >5574</td>
      <td id="T_6c98d_row51_col3" class="data row51 col3" >3582</td>
      <td id="T_6c98d_row51_col4" class="data row51 col4" >3906</td>
      <td id="T_6c98d_row51_col5" class="data row51 col5" >0.642626</td>
      <td id="T_6c98d_row51_col6" class="data row51 col6" >0.700753</td>
      <td id="T_6c98d_row51_col7" class="data row51 col7" >1605</td>
      <td id="T_6c98d_row51_col8" class="data row51 col8" >1002</td>
      <td id="T_6c98d_row51_col9" class="data row51 col9" >1173</td>
      <td id="T_6c98d_row51_col10" class="data row51 col10" >0.624299</td>
      <td id="T_6c98d_row51_col11" class="data row51 col11" >0.730841</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row52" class="row_heading level0 row52" >52</th>
      <td id="T_6c98d_row52_col0" class="data row52 col0" ></td>
      <td id="T_6c98d_row52_col1" class="data row52 col1" >barrier = *</td>
      <td id="T_6c98d_row52_col2" class="data row52 col2" >4347</td>
      <td id="T_6c98d_row52_col3" class="data row52 col3" >1010</td>
      <td id="T_6c98d_row52_col4" class="data row52 col4" >1019</td>
      <td id="T_6c98d_row52_col5" class="data row52 col5" >0.232344</td>
      <td id="T_6c98d_row52_col6" class="data row52 col6" >0.234415</td>
      <td id="T_6c98d_row52_col7" class="data row52 col7" >3635</td>
      <td id="T_6c98d_row52_col8" class="data row52 col8" >753</td>
      <td id="T_6c98d_row52_col9" class="data row52 col9" >807</td>
      <td id="T_6c98d_row52_col10" class="data row52 col10" >0.207153</td>
      <td id="T_6c98d_row52_col11" class="data row52 col11" >0.222008</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row53" class="row_heading level0 row53" >53</th>
      <td id="T_6c98d_row53_col0" class="data row53 col0" ></td>
      <td id="T_6c98d_row53_col1" class="data row53 col1" >power = *</td>
      <td id="T_6c98d_row53_col2" class="data row53 col2" >4908</td>
      <td id="T_6c98d_row53_col3" class="data row53 col3" >625</td>
      <td id="T_6c98d_row53_col4" class="data row53 col4" >672</td>
      <td id="T_6c98d_row53_col5" class="data row53 col5" >0.127343</td>
      <td id="T_6c98d_row53_col6" class="data row53 col6" >0.136919</td>
      <td id="T_6c98d_row53_col7" class="data row53 col7" >3837</td>
      <td id="T_6c98d_row53_col8" class="data row53 col8" >535</td>
      <td id="T_6c98d_row53_col9" class="data row53 col9" >576</td>
      <td id="T_6c98d_row53_col10" class="data row53 col10" >0.139432</td>
      <td id="T_6c98d_row53_col11" class="data row53 col11" >0.150117</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row54" class="row_heading level0 row54" >54</th>
      <td id="T_6c98d_row54_col0" class="data row54 col0" ></td>
      <td id="T_6c98d_row54_col1" class="data row54 col1" >bridge = *</td>
      <td id="T_6c98d_row54_col2" class="data row54 col2" >1350</td>
      <td id="T_6c98d_row54_col3" class="data row54 col3" >1005</td>
      <td id="T_6c98d_row54_col4" class="data row54 col4" >1000</td>
      <td id="T_6c98d_row54_col5" class="data row54 col5" >0.744444</td>
      <td id="T_6c98d_row54_col6" class="data row54 col6" >0.740741</td>
      <td id="T_6c98d_row54_col7" class="data row54 col7" >495</td>
      <td id="T_6c98d_row54_col8" class="data row54 col8" >388</td>
      <td id="T_6c98d_row54_col9" class="data row54 col9" >391</td>
      <td id="T_6c98d_row54_col10" class="data row54 col10" >0.783838</td>
      <td id="T_6c98d_row54_col11" class="data row54 col11" >0.789899</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row55" class="row_heading level0 row55" >55</th>
      <td id="T_6c98d_row55_col0" class="data row55 col0" ></td>
      <td id="T_6c98d_row55_col1" class="data row55 col1" >substation = *</td>
      <td id="T_6c98d_row55_col2" class="data row55 col2" >2547</td>
      <td id="T_6c98d_row55_col3" class="data row55 col3" >455</td>
      <td id="T_6c98d_row55_col4" class="data row55 col4" >481</td>
      <td id="T_6c98d_row55_col5" class="data row55 col5" >0.178642</td>
      <td id="T_6c98d_row55_col6" class="data row55 col6" >0.188850</td>
      <td id="T_6c98d_row55_col7" class="data row55 col7" >2358</td>
      <td id="T_6c98d_row55_col8" class="data row55 col8" >413</td>
      <td id="T_6c98d_row55_col9" class="data row55 col9" >439</td>
      <td id="T_6c98d_row55_col10" class="data row55 col10" >0.175148</td>
      <td id="T_6c98d_row55_col11" class="data row55 col11" >0.186175</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row56" class="row_heading level0 row56" >56</th>
      <td id="T_6c98d_row56_col0" class="data row56 col0" ></td>
      <td id="T_6c98d_row56_col1" class="data row56 col1" >emergency = *</td>
      <td id="T_6c98d_row56_col2" class="data row56 col2" >1149</td>
      <td id="T_6c98d_row56_col3" class="data row56 col3" >122</td>
      <td id="T_6c98d_row56_col4" class="data row56 col4" >108</td>
      <td id="T_6c98d_row56_col5" class="data row56 col5" >0.106179</td>
      <td id="T_6c98d_row56_col6" class="data row56 col6" >0.093995</td>
      <td id="T_6c98d_row56_col7" class="data row56 col7" >283</td>
      <td id="T_6c98d_row56_col8" class="data row56 col8" >101</td>
      <td id="T_6c98d_row56_col9" class="data row56 col9" >98</td>
      <td id="T_6c98d_row56_col10" class="data row56 col10" >0.356890</td>
      <td id="T_6c98d_row56_col11" class="data row56 col11" >0.346290</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row57" class="row_heading level0 row57" >57</th>
      <td id="T_6c98d_row57_col0" class="data row57 col0" ></td>
      <td id="T_6c98d_row57_col1" class="data row57 col1" >ele = *</td>
      <td id="T_6c98d_row57_col2" class="data row57 col2" >309</td>
      <td id="T_6c98d_row57_col3" class="data row57 col3" >79</td>
      <td id="T_6c98d_row57_col4" class="data row57 col4" >149</td>
      <td id="T_6c98d_row57_col5" class="data row57 col5" >0.255663</td>
      <td id="T_6c98d_row57_col6" class="data row57 col6" >0.482201</td>
      <td id="T_6c98d_row57_col7" class="data row57 col7" >280</td>
      <td id="T_6c98d_row57_col8" class="data row57 col8" >76</td>
      <td id="T_6c98d_row57_col9" class="data row57 col9" >139</td>
      <td id="T_6c98d_row57_col10" class="data row57 col10" >0.271429</td>
      <td id="T_6c98d_row57_col11" class="data row57 col11" >0.496429</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row58" class="row_heading level0 row58" >58</th>
      <td id="T_6c98d_row58_col0" class="data row58 col0" ></td>
      <td id="T_6c98d_row58_col1" class="data row58 col1" >man_made = *</td>
      <td id="T_6c98d_row58_col2" class="data row58 col2" >1598</td>
      <td id="T_6c98d_row58_col3" class="data row58 col3" >240</td>
      <td id="T_6c98d_row58_col4" class="data row58 col4" >284</td>
      <td id="T_6c98d_row58_col5" class="data row58 col5" >0.150188</td>
      <td id="T_6c98d_row58_col6" class="data row58 col6" >0.177722</td>
      <td id="T_6c98d_row58_col7" class="data row58 col7" >1162</td>
      <td id="T_6c98d_row58_col8" class="data row58 col8" >216</td>
      <td id="T_6c98d_row58_col9" class="data row58 col9" >242</td>
      <td id="T_6c98d_row58_col10" class="data row58 col10" >0.185886</td>
      <td id="T_6c98d_row58_col11" class="data row58 col11" >0.208262</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row59" class="row_heading level0 row59" >59</th>
      <td id="T_6c98d_row59_col0" class="data row59 col0" ></td>
      <td id="T_6c98d_row59_col1" class="data row59 col1" >embankment = *</td>
      <td id="T_6c98d_row59_col2" class="data row59 col2" >211</td>
      <td id="T_6c98d_row59_col3" class="data row59 col3" >127</td>
      <td id="T_6c98d_row59_col4" class="data row59 col4" >127</td>
      <td id="T_6c98d_row59_col5" class="data row59 col5" >0.601896</td>
      <td id="T_6c98d_row59_col6" class="data row59 col6" >0.601896</td>
      <td id="T_6c98d_row59_col7" class="data row59 col7" >89</td>
      <td id="T_6c98d_row59_col8" class="data row59 col8" >67</td>
      <td id="T_6c98d_row59_col9" class="data row59 col9" >67</td>
      <td id="T_6c98d_row59_col10" class="data row59 col10" >0.752809</td>
      <td id="T_6c98d_row59_col11" class="data row59 col11" >0.752809</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row60" class="row_heading level0 row60" >60</th>
      <td id="T_6c98d_row60_col0" class="data row60 col0" >#</td>
      <td id="T_6c98d_row60_col1" class="data row60 col1" >amenity</td>
      <td id="T_6c98d_row60_col2" class="data row60 col2" >61923</td>
      <td id="T_6c98d_row60_col3" class="data row60 col3" >11704</td>
      <td id="T_6c98d_row60_col4" class="data row60 col4" >16623</td>
      <td id="T_6c98d_row60_col5" class="data row60 col5" >0.189009</td>
      <td id="T_6c98d_row60_col6" class="data row60 col6" >0.268446</td>
      <td id="T_6c98d_row60_col7" class="data row60 col7" >30362</td>
      <td id="T_6c98d_row60_col8" class="data row60 col8" >6515</td>
      <td id="T_6c98d_row60_col9" class="data row60 col9" >9564</td>
      <td id="T_6c98d_row60_col10" class="data row60 col10" >0.214577</td>
      <td id="T_6c98d_row60_col11" class="data row60 col11" >0.314999</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row61" class="row_heading level0 row61" >61</th>
      <td id="T_6c98d_row61_col0" class="data row61 col0" ></td>
      <td id="T_6c98d_row61_col1" class="data row61 col1" >amenity = place_of_worship</td>
      <td id="T_6c98d_row61_col2" class="data row61 col2" >2650</td>
      <td id="T_6c98d_row61_col3" class="data row61 col3" >1277</td>
      <td id="T_6c98d_row61_col4" class="data row61 col4" >1553</td>
      <td id="T_6c98d_row61_col5" class="data row61 col5" >0.481887</td>
      <td id="T_6c98d_row61_col6" class="data row61 col6" >0.586038</td>
      <td id="T_6c98d_row61_col7" class="data row61 col7" >1873</td>
      <td id="T_6c98d_row61_col8" class="data row61 col8" >939</td>
      <td id="T_6c98d_row61_col9" class="data row61 col9" >1231</td>
      <td id="T_6c98d_row61_col10" class="data row61 col10" >0.501335</td>
      <td id="T_6c98d_row61_col11" class="data row61 col11" >0.657234</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row62" class="row_heading level0 row62" >62</th>
      <td id="T_6c98d_row62_col0" class="data row62 col0" ></td>
      <td id="T_6c98d_row62_col1" class="data row62 col1" >amenity = school</td>
      <td id="T_6c98d_row62_col2" class="data row62 col2" >1973</td>
      <td id="T_6c98d_row62_col3" class="data row62 col3" >594</td>
      <td id="T_6c98d_row62_col4" class="data row62 col4" >721</td>
      <td id="T_6c98d_row62_col5" class="data row62 col5" >0.301064</td>
      <td id="T_6c98d_row62_col6" class="data row62 col6" >0.365433</td>
      <td id="T_6c98d_row62_col7" class="data row62 col7" >1418</td>
      <td id="T_6c98d_row62_col8" class="data row62 col8" >405</td>
      <td id="T_6c98d_row62_col9" class="data row62 col9" >511</td>
      <td id="T_6c98d_row62_col10" class="data row62 col10" >0.285614</td>
      <td id="T_6c98d_row62_col11" class="data row62 col11" >0.360367</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row63" class="row_heading level0 row63" >63</th>
      <td id="T_6c98d_row63_col0" class="data row63 col0" ></td>
      <td id="T_6c98d_row63_col1" class="data row63 col1" >amenity = kindergarten</td>
      <td id="T_6c98d_row63_col2" class="data row63 col2" >1876</td>
      <td id="T_6c98d_row63_col3" class="data row63 col3" >422</td>
      <td id="T_6c98d_row63_col4" class="data row63 col4" >501</td>
      <td id="T_6c98d_row63_col5" class="data row63 col5" >0.224947</td>
      <td id="T_6c98d_row63_col6" class="data row63 col6" >0.267058</td>
      <td id="T_6c98d_row63_col7" class="data row63 col7" >1352</td>
      <td id="T_6c98d_row63_col8" class="data row63 col8" >380</td>
      <td id="T_6c98d_row63_col9" class="data row63 col9" >435</td>
      <td id="T_6c98d_row63_col10" class="data row63 col10" >0.281065</td>
      <td id="T_6c98d_row63_col11" class="data row63 col11" >0.321746</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row64" class="row_heading level0 row64" >64</th>
      <td id="T_6c98d_row64_col0" class="data row64 col0" ></td>
      <td id="T_6c98d_row64_col1" class="data row64 col1" >craft = shoemaker</td>
      <td id="T_6c98d_row64_col2" class="data row64 col2" >225</td>
      <td id="T_6c98d_row64_col3" class="data row64 col3" >30</td>
      <td id="T_6c98d_row64_col4" class="data row64 col4" >43</td>
      <td id="T_6c98d_row64_col5" class="data row64 col5" >0.133333</td>
      <td id="T_6c98d_row64_col6" class="data row64 col6" >0.191111</td>
      <td id="T_6c98d_row64_col7" class="data row64 col7" >64</td>
      <td id="T_6c98d_row64_col8" class="data row64 col8" >6</td>
      <td id="T_6c98d_row64_col9" class="data row64 col9" >13</td>
      <td id="T_6c98d_row64_col10" class="data row64 col10" >0.093750</td>
      <td id="T_6c98d_row64_col11" class="data row64 col11" >0.203125</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row65" class="row_heading level0 row65" >65</th>
      <td id="T_6c98d_row65_col0" class="data row65 col0" ></td>
      <td id="T_6c98d_row65_col1" class="data row65 col1" >amenity = *</td>
      <td id="T_6c98d_row65_col2" class="data row65 col2" >23554</td>
      <td id="T_6c98d_row65_col3" class="data row65 col3" >5628</td>
      <td id="T_6c98d_row65_col4" class="data row65 col4" >7440</td>
      <td id="T_6c98d_row65_col5" class="data row65 col5" >0.238940</td>
      <td id="T_6c98d_row65_col6" class="data row65 col6" >0.315870</td>
      <td id="T_6c98d_row65_col7" class="data row65 col7" >12662</td>
      <td id="T_6c98d_row65_col8" class="data row65 col8" >2885</td>
      <td id="T_6c98d_row65_col9" class="data row65 col9" >4130</td>
      <td id="T_6c98d_row65_col10" class="data row65 col10" >0.227847</td>
      <td id="T_6c98d_row65_col11" class="data row65 col11" >0.326173</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row66" class="row_heading level0 row66" >66</th>
      <td id="T_6c98d_row66_col0" class="data row66 col0" ></td>
      <td id="T_6c98d_row66_col1" class="data row66 col1" >shop = *</td>
      <td id="T_6c98d_row66_col2" class="data row66 col2" >28782</td>
      <td id="T_6c98d_row66_col3" class="data row66 col3" >2948</td>
      <td id="T_6c98d_row66_col4" class="data row66 col4" >5451</td>
      <td id="T_6c98d_row66_col5" class="data row66 col5" >0.102425</td>
      <td id="T_6c98d_row66_col6" class="data row66 col6" >0.189389</td>
      <td id="T_6c98d_row66_col7" class="data row66 col7" >11962</td>
      <td id="T_6c98d_row66_col8" class="data row66 col8" >1548</td>
      <td id="T_6c98d_row66_col9" class="data row66 col9" >2872</td>
      <td id="T_6c98d_row66_col10" class="data row66 col10" >0.129410</td>
      <td id="T_6c98d_row66_col11" class="data row66 col11" >0.240094</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row67" class="row_heading level0 row67" >67</th>
      <td id="T_6c98d_row67_col0" class="data row67 col0" ></td>
      <td id="T_6c98d_row67_col1" class="data row67 col1" >leisure = *</td>
      <td id="T_6c98d_row67_col2" class="data row67 col2" >3473</td>
      <td id="T_6c98d_row67_col3" class="data row67 col3" >935</td>
      <td id="T_6c98d_row67_col4" class="data row67 col4" >1090</td>
      <td id="T_6c98d_row67_col5" class="data row67 col5" >0.269220</td>
      <td id="T_6c98d_row67_col6" class="data row67 col6" >0.313850</td>
      <td id="T_6c98d_row67_col7" class="data row67 col7" >2349</td>
      <td id="T_6c98d_row67_col8" class="data row67 col8" >564</td>
      <td id="T_6c98d_row67_col9" class="data row67 col9" >700</td>
      <td id="T_6c98d_row67_col10" class="data row67 col10" >0.240102</td>
      <td id="T_6c98d_row67_col11" class="data row67 col11" >0.297999</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row68" class="row_heading level0 row68" >68</th>
      <td id="T_6c98d_row68_col0" class="data row68 col0" ></td>
      <td id="T_6c98d_row68_col1" class="data row68 col1" >sport = *</td>
      <td id="T_6c98d_row68_col2" class="data row68 col2" >774</td>
      <td id="T_6c98d_row68_col3" class="data row68 col3" >171</td>
      <td id="T_6c98d_row68_col4" class="data row68 col4" >159</td>
      <td id="T_6c98d_row68_col5" class="data row68 col5" >0.220930</td>
      <td id="T_6c98d_row68_col6" class="data row68 col6" >0.205426</td>
      <td id="T_6c98d_row68_col7" class="data row68 col7" >582</td>
      <td id="T_6c98d_row68_col8" class="data row68 col8" >115</td>
      <td id="T_6c98d_row68_col9" class="data row68 col9" >111</td>
      <td id="T_6c98d_row68_col10" class="data row68 col10" >0.197595</td>
      <td id="T_6c98d_row68_col11" class="data row68 col11" >0.190722</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row69" class="row_heading level0 row69" >69</th>
      <td id="T_6c98d_row69_col0" class="data row69 col0" ></td>
      <td id="T_6c98d_row69_col1" class="data row69 col1" >clothes = *</td>
      <td id="T_6c98d_row69_col2" class="data row69 col2" >228</td>
      <td id="T_6c98d_row69_col3" class="data row69 col3" >33</td>
      <td id="T_6c98d_row69_col4" class="data row69 col4" >42</td>
      <td id="T_6c98d_row69_col5" class="data row69 col5" >0.144737</td>
      <td id="T_6c98d_row69_col6" class="data row69 col6" >0.184211</td>
      <td id="T_6c98d_row69_col7" class="data row69 col7" >129</td>
      <td id="T_6c98d_row69_col8" class="data row69 col8" >19</td>
      <td id="T_6c98d_row69_col9" class="data row69 col9" >23</td>
      <td id="T_6c98d_row69_col10" class="data row69 col10" >0.147287</td>
      <td id="T_6c98d_row69_col11" class="data row69 col11" >0.178295</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row70" class="row_heading level0 row70" >70</th>
      <td id="T_6c98d_row70_col0" class="data row70 col0" >#</td>
      <td id="T_6c98d_row70_col1" class="data row70 col1" >government</td>
      <td id="T_6c98d_row70_col2" class="data row70 col2" >4610</td>
      <td id="T_6c98d_row70_col3" class="data row70 col3" >820</td>
      <td id="T_6c98d_row70_col4" class="data row70 col4" >1334</td>
      <td id="T_6c98d_row70_col5" class="data row70 col5" >0.177874</td>
      <td id="T_6c98d_row70_col6" class="data row70 col6" >0.289371</td>
      <td id="T_6c98d_row70_col7" class="data row70 col7" >3234</td>
      <td id="T_6c98d_row70_col8" class="data row70 col8" >696</td>
      <td id="T_6c98d_row70_col9" class="data row70 col9" >1093</td>
      <td id="T_6c98d_row70_col10" class="data row70 col10" >0.215213</td>
      <td id="T_6c98d_row70_col11" class="data row70 col11" >0.337972</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row71" class="row_heading level0 row71" >71</th>
      <td id="T_6c98d_row71_col0" class="data row71 col0" ></td>
      <td id="T_6c98d_row71_col1" class="data row71 col1" >office = government</td>
      <td id="T_6c98d_row71_col2" class="data row71 col2" >1865</td>
      <td id="T_6c98d_row71_col3" class="data row71 col3" >317</td>
      <td id="T_6c98d_row71_col4" class="data row71 col4" >531</td>
      <td id="T_6c98d_row71_col5" class="data row71 col5" >0.169973</td>
      <td id="T_6c98d_row71_col6" class="data row71 col6" >0.284718</td>
      <td id="T_6c98d_row71_col7" class="data row71 col7" >1560</td>
      <td id="T_6c98d_row71_col8" class="data row71 col8" >297</td>
      <td id="T_6c98d_row71_col9" class="data row71 col9" >474</td>
      <td id="T_6c98d_row71_col10" class="data row71 col10" >0.190385</td>
      <td id="T_6c98d_row71_col11" class="data row71 col11" >0.303846</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row72" class="row_heading level0 row72" >72</th>
      <td id="T_6c98d_row72_col0" class="data row72 col0" ></td>
      <td id="T_6c98d_row72_col1" class="data row72 col1" >healthcare = *</td>
      <td id="T_6c98d_row72_col2" class="data row72 col2" >2261</td>
      <td id="T_6c98d_row72_col3" class="data row72 col3" >446</td>
      <td id="T_6c98d_row72_col4" class="data row72 col4" >714</td>
      <td id="T_6c98d_row72_col5" class="data row72 col5" >0.197258</td>
      <td id="T_6c98d_row72_col6" class="data row72 col6" >0.315789</td>
      <td id="T_6c98d_row72_col7" class="data row72 col7" >1375</td>
      <td id="T_6c98d_row72_col8" class="data row72 col8" >364</td>
      <td id="T_6c98d_row72_col9" class="data row72 col9" >561</td>
      <td id="T_6c98d_row72_col10" class="data row72 col10" >0.264727</td>
      <td id="T_6c98d_row72_col11" class="data row72 col11" >0.408000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row73" class="row_heading level0 row73" >73</th>
      <td id="T_6c98d_row73_col0" class="data row73 col0" ></td>
      <td id="T_6c98d_row73_col1" class="data row73 col1" >government = *</td>
      <td id="T_6c98d_row73_col2" class="data row73 col2" >699</td>
      <td id="T_6c98d_row73_col3" class="data row73 col3" >172</td>
      <td id="T_6c98d_row73_col4" class="data row73 col4" >198</td>
      <td id="T_6c98d_row73_col5" class="data row73 col5" >0.246066</td>
      <td id="T_6c98d_row73_col6" class="data row73 col6" >0.283262</td>
      <td id="T_6c98d_row73_col7" class="data row73 col7" >560</td>
      <td id="T_6c98d_row73_col8" class="data row73 col8" >154</td>
      <td id="T_6c98d_row73_col9" class="data row73 col9" >166</td>
      <td id="T_6c98d_row73_col10" class="data row73 col10" >0.275000</td>
      <td id="T_6c98d_row73_col11" class="data row73 col11" >0.296429</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row74" class="row_heading level0 row74" >74</th>
      <td id="T_6c98d_row74_col0" class="data row74 col0" ></td>
      <td id="T_6c98d_row74_col1" class="data row74 col1" >military = *</td>
      <td id="T_6c98d_row74_col2" class="data row74 col2" >475</td>
      <td id="T_6c98d_row74_col3" class="data row74 col3" >58</td>
      <td id="T_6c98d_row74_col4" class="data row74 col4" >88</td>
      <td id="T_6c98d_row74_col5" class="data row74 col5" >0.122105</td>
      <td id="T_6c98d_row74_col6" class="data row74 col6" >0.185263</td>
      <td id="T_6c98d_row74_col7" class="data row74 col7" >297</td>
      <td id="T_6c98d_row74_col8" class="data row74 col8" >37</td>
      <td id="T_6c98d_row74_col9" class="data row74 col9" >59</td>
      <td id="T_6c98d_row74_col10" class="data row74 col10" >0.124579</td>
      <td id="T_6c98d_row74_col11" class="data row74 col11" >0.198653</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row75" class="row_heading level0 row75" >75</th>
      <td id="T_6c98d_row75_col0" class="data row75 col0" >#</td>
      <td id="T_6c98d_row75_col1" class="data row75 col1" >office</td>
      <td id="T_6c98d_row75_col2" class="data row75 col2" >5308</td>
      <td id="T_6c98d_row75_col3" class="data row75 col3" >522</td>
      <td id="T_6c98d_row75_col4" class="data row75 col4" >779</td>
      <td id="T_6c98d_row75_col5" class="data row75 col5" >0.098342</td>
      <td id="T_6c98d_row75_col6" class="data row75 col6" >0.146760</td>
      <td id="T_6c98d_row75_col7" class="data row75 col7" >3832</td>
      <td id="T_6c98d_row75_col8" class="data row75 col8" >387</td>
      <td id="T_6c98d_row75_col9" class="data row75 col9" >554</td>
      <td id="T_6c98d_row75_col10" class="data row75 col10" >0.100992</td>
      <td id="T_6c98d_row75_col11" class="data row75 col11" >0.144572</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row76" class="row_heading level0 row76" >76</th>
      <td id="T_6c98d_row76_col0" class="data row76 col0" ></td>
      <td id="T_6c98d_row76_col1" class="data row76 col1" >office = *</td>
      <td id="T_6c98d_row76_col2" class="data row76 col2" >5308</td>
      <td id="T_6c98d_row76_col3" class="data row76 col3" >522</td>
      <td id="T_6c98d_row76_col4" class="data row76 col4" >779</td>
      <td id="T_6c98d_row76_col5" class="data row76 col5" >0.098342</td>
      <td id="T_6c98d_row76_col6" class="data row76 col6" >0.146760</td>
      <td id="T_6c98d_row76_col7" class="data row76 col7" >3832</td>
      <td id="T_6c98d_row76_col8" class="data row76 col8" >387</td>
      <td id="T_6c98d_row76_col9" class="data row76 col9" >554</td>
      <td id="T_6c98d_row76_col10" class="data row76 col10" >0.100992</td>
      <td id="T_6c98d_row76_col11" class="data row76 col11" >0.144572</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row77" class="row_heading level0 row77" >77</th>
      <td id="T_6c98d_row77_col0" class="data row77 col0" >#</td>
      <td id="T_6c98d_row77_col1" class="data row77 col1" >building</td>
      <td id="T_6c98d_row77_col2" class="data row77 col2" >33610</td>
      <td id="T_6c98d_row77_col3" class="data row77 col3" >5337</td>
      <td id="T_6c98d_row77_col4" class="data row77 col4" >6192</td>
      <td id="T_6c98d_row77_col5" class="data row77 col5" >0.158792</td>
      <td id="T_6c98d_row77_col6" class="data row77 col6" >0.184231</td>
      <td id="T_6c98d_row77_col7" class="data row77 col7" >19948</td>
      <td id="T_6c98d_row77_col8" class="data row77 col8" >3982</td>
      <td id="T_6c98d_row77_col9" class="data row77 col9" >4719</td>
      <td id="T_6c98d_row77_col10" class="data row77 col10" >0.199619</td>
      <td id="T_6c98d_row77_col11" class="data row77 col11" >0.236565</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row78" class="row_heading level0 row78" >78</th>
      <td id="T_6c98d_row78_col0" class="data row78 col0" ></td>
      <td id="T_6c98d_row78_col1" class="data row78 col1" >building = industrial</td>
      <td id="T_6c98d_row78_col2" class="data row78 col2" >1607</td>
      <td id="T_6c98d_row78_col3" class="data row78 col3" >52</td>
      <td id="T_6c98d_row78_col4" class="data row78 col4" >62</td>
      <td id="T_6c98d_row78_col5" class="data row78 col5" >0.032358</td>
      <td id="T_6c98d_row78_col6" class="data row78 col6" >0.038581</td>
      <td id="T_6c98d_row78_col7" class="data row78 col7" >1224</td>
      <td id="T_6c98d_row78_col8" class="data row78 col8" >50</td>
      <td id="T_6c98d_row78_col9" class="data row78 col9" >60</td>
      <td id="T_6c98d_row78_col10" class="data row78 col10" >0.040850</td>
      <td id="T_6c98d_row78_col11" class="data row78 col11" >0.049020</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row79" class="row_heading level0 row79" >79</th>
      <td id="T_6c98d_row79_col0" class="data row79 col0" ></td>
      <td id="T_6c98d_row79_col1" class="data row79 col1" >building = service</td>
      <td id="T_6c98d_row79_col2" class="data row79 col2" >1368</td>
      <td id="T_6c98d_row79_col3" class="data row79 col3" >583</td>
      <td id="T_6c98d_row79_col4" class="data row79 col4" >588</td>
      <td id="T_6c98d_row79_col5" class="data row79 col5" >0.426170</td>
      <td id="T_6c98d_row79_col6" class="data row79 col6" >0.429825</td>
      <td id="T_6c98d_row79_col7" class="data row79 col7" >1032</td>
      <td id="T_6c98d_row79_col8" class="data row79 col8" >506</td>
      <td id="T_6c98d_row79_col9" class="data row79 col9" >513</td>
      <td id="T_6c98d_row79_col10" class="data row79 col10" >0.490310</td>
      <td id="T_6c98d_row79_col11" class="data row79 col11" >0.497093</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row80" class="row_heading level0 row80" >80</th>
      <td id="T_6c98d_row80_col0" class="data row80 col0" ></td>
      <td id="T_6c98d_row80_col1" class="data row80 col1" >building = retail</td>
      <td id="T_6c98d_row80_col2" class="data row80 col2" >1912</td>
      <td id="T_6c98d_row80_col3" class="data row80 col3" >330</td>
      <td id="T_6c98d_row80_col4" class="data row80 col4" >502</td>
      <td id="T_6c98d_row80_col5" class="data row80 col5" >0.172594</td>
      <td id="T_6c98d_row80_col6" class="data row80 col6" >0.262552</td>
      <td id="T_6c98d_row80_col7" class="data row80 col7" >1127</td>
      <td id="T_6c98d_row80_col8" class="data row80 col8" >259</td>
      <td id="T_6c98d_row80_col9" class="data row80 col9" >364</td>
      <td id="T_6c98d_row80_col10" class="data row80 col10" >0.229814</td>
      <td id="T_6c98d_row80_col11" class="data row80 col11" >0.322981</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row81" class="row_heading level0 row81" >81</th>
      <td id="T_6c98d_row81_col0" class="data row81 col0" ></td>
      <td id="T_6c98d_row81_col1" class="data row81 col1" >building = school</td>
      <td id="T_6c98d_row81_col2" class="data row81 col2" >679</td>
      <td id="T_6c98d_row81_col3" class="data row81 col3" >73</td>
      <td id="T_6c98d_row81_col4" class="data row81 col4" >97</td>
      <td id="T_6c98d_row81_col5" class="data row81 col5" >0.107511</td>
      <td id="T_6c98d_row81_col6" class="data row81 col6" >0.142857</td>
      <td id="T_6c98d_row81_col7" class="data row81 col7" >573</td>
      <td id="T_6c98d_row81_col8" class="data row81 col8" >65</td>
      <td id="T_6c98d_row81_col9" class="data row81 col9" >91</td>
      <td id="T_6c98d_row81_col10" class="data row81 col10" >0.113438</td>
      <td id="T_6c98d_row81_col11" class="data row81 col11" >0.158813</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row82" class="row_heading level0 row82" >82</th>
      <td id="T_6c98d_row82_col0" class="data row82 col0" ></td>
      <td id="T_6c98d_row82_col1" class="data row82 col1" >building = kindergarten</td>
      <td id="T_6c98d_row82_col2" class="data row82 col2" >366</td>
      <td id="T_6c98d_row82_col3" class="data row82 col3" >25</td>
      <td id="T_6c98d_row82_col4" class="data row82 col4" >35</td>
      <td id="T_6c98d_row82_col5" class="data row82 col5" >0.068306</td>
      <td id="T_6c98d_row82_col6" class="data row82 col6" >0.095628</td>
      <td id="T_6c98d_row82_col7" class="data row82 col7" >276</td>
      <td id="T_6c98d_row82_col8" class="data row82 col8" >24</td>
      <td id="T_6c98d_row82_col9" class="data row82 col9" >32</td>
      <td id="T_6c98d_row82_col10" class="data row82 col10" >0.086957</td>
      <td id="T_6c98d_row82_col11" class="data row82 col11" >0.115942</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row83" class="row_heading level0 row83" >83</th>
      <td id="T_6c98d_row83_col0" class="data row83 col0" ></td>
      <td id="T_6c98d_row83_col1" class="data row83 col1" >building = commercial</td>
      <td id="T_6c98d_row83_col2" class="data row83 col2" >598</td>
      <td id="T_6c98d_row83_col3" class="data row83 col3" >87</td>
      <td id="T_6c98d_row83_col4" class="data row83 col4" >82</td>
      <td id="T_6c98d_row83_col5" class="data row83 col5" >0.145485</td>
      <td id="T_6c98d_row83_col6" class="data row83 col6" >0.137124</td>
      <td id="T_6c98d_row83_col7" class="data row83 col7" >549</td>
      <td id="T_6c98d_row83_col8" class="data row83 col8" >78</td>
      <td id="T_6c98d_row83_col9" class="data row83 col9" >73</td>
      <td id="T_6c98d_row83_col10" class="data row83 col10" >0.142077</td>
      <td id="T_6c98d_row83_col11" class="data row83 col11" >0.132969</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row84" class="row_heading level0 row84" >84</th>
      <td id="T_6c98d_row84_col0" class="data row84 col0" ></td>
      <td id="T_6c98d_row84_col1" class="data row84 col1" >building = church</td>
      <td id="T_6c98d_row84_col2" class="data row84 col2" >1412</td>
      <td id="T_6c98d_row84_col3" class="data row84 col3" >801</td>
      <td id="T_6c98d_row84_col4" class="data row84 col4" >1036</td>
      <td id="T_6c98d_row84_col5" class="data row84 col5" >0.567280</td>
      <td id="T_6c98d_row84_col6" class="data row84 col6" >0.733711</td>
      <td id="T_6c98d_row84_col7" class="data row84 col7" >1095</td>
      <td id="T_6c98d_row84_col8" class="data row84 col8" >601</td>
      <td id="T_6c98d_row84_col9" class="data row84 col9" >833</td>
      <td id="T_6c98d_row84_col10" class="data row84 col10" >0.548858</td>
      <td id="T_6c98d_row84_col11" class="data row84 col11" >0.760731</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row85" class="row_heading level0 row85" >85</th>
      <td id="T_6c98d_row85_col0" class="data row85 col0" ></td>
      <td id="T_6c98d_row85_col1" class="data row85 col1" >building = warehouse</td>
      <td id="T_6c98d_row85_col2" class="data row85 col2" >232</td>
      <td id="T_6c98d_row85_col3" class="data row85 col3" >11</td>
      <td id="T_6c98d_row85_col4" class="data row85 col4" >19</td>
      <td id="T_6c98d_row85_col5" class="data row85 col5" >0.047414</td>
      <td id="T_6c98d_row85_col6" class="data row85 col6" >0.081897</td>
      <td id="T_6c98d_row85_col7" class="data row85 col7" >164</td>
      <td id="T_6c98d_row85_col8" class="data row85 col8" >9</td>
      <td id="T_6c98d_row85_col9" class="data row85 col9" >14</td>
      <td id="T_6c98d_row85_col10" class="data row85 col10" >0.054878</td>
      <td id="T_6c98d_row85_col11" class="data row85 col11" >0.085366</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row86" class="row_heading level0 row86" >86</th>
      <td id="T_6c98d_row86_col0" class="data row86 col0" ></td>
      <td id="T_6c98d_row86_col1" class="data row86 col1" >building = public</td>
      <td id="T_6c98d_row86_col2" class="data row86 col2" >361</td>
      <td id="T_6c98d_row86_col3" class="data row86 col3" >112</td>
      <td id="T_6c98d_row86_col4" class="data row86 col4" >97</td>
      <td id="T_6c98d_row86_col5" class="data row86 col5" >0.310249</td>
      <td id="T_6c98d_row86_col6" class="data row86 col6" >0.268698</td>
      <td id="T_6c98d_row86_col7" class="data row86 col7" >298</td>
      <td id="T_6c98d_row86_col8" class="data row86 col8" >103</td>
      <td id="T_6c98d_row86_col9" class="data row86 col9" >92</td>
      <td id="T_6c98d_row86_col10" class="data row86 col10" >0.345638</td>
      <td id="T_6c98d_row86_col11" class="data row86 col11" >0.308725</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row87" class="row_heading level0 row87" >87</th>
      <td id="T_6c98d_row87_col0" class="data row87 col0" ></td>
      <td id="T_6c98d_row87_col1" class="data row87 col1" >building = dormitory</td>
      <td id="T_6c98d_row87_col2" class="data row87 col2" >591</td>
      <td id="T_6c98d_row87_col3" class="data row87 col3" >81</td>
      <td id="T_6c98d_row87_col4" class="data row87 col4" >85</td>
      <td id="T_6c98d_row87_col5" class="data row87 col5" >0.137056</td>
      <td id="T_6c98d_row87_col6" class="data row87 col6" >0.143824</td>
      <td id="T_6c98d_row87_col7" class="data row87 col7" >444</td>
      <td id="T_6c98d_row87_col8" class="data row87 col8" >71</td>
      <td id="T_6c98d_row87_col9" class="data row87 col9" >85</td>
      <td id="T_6c98d_row87_col10" class="data row87 col10" >0.159910</td>
      <td id="T_6c98d_row87_col11" class="data row87 col11" >0.191441</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row88" class="row_heading level0 row88" >88</th>
      <td id="T_6c98d_row88_col0" class="data row88 col0" ></td>
      <td id="T_6c98d_row88_col1" class="data row88 col1" >building = hospital</td>
      <td id="T_6c98d_row88_col2" class="data row88 col2" >398</td>
      <td id="T_6c98d_row88_col3" class="data row88 col3" >68</td>
      <td id="T_6c98d_row88_col4" class="data row88 col4" >53</td>
      <td id="T_6c98d_row88_col5" class="data row88 col5" >0.170854</td>
      <td id="T_6c98d_row88_col6" class="data row88 col6" >0.133166</td>
      <td id="T_6c98d_row88_col7" class="data row88 col7" >294</td>
      <td id="T_6c98d_row88_col8" class="data row88 col8" >63</td>
      <td id="T_6c98d_row88_col9" class="data row88 col9" >48</td>
      <td id="T_6c98d_row88_col10" class="data row88 col10" >0.214286</td>
      <td id="T_6c98d_row88_col11" class="data row88 col11" >0.163265</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row89" class="row_heading level0 row89" >89</th>
      <td id="T_6c98d_row89_col0" class="data row89 col0" ></td>
      <td id="T_6c98d_row89_col1" class="data row89 col1" >building = warehouse</td>
      <td id="T_6c98d_row89_col2" class="data row89 col2" >232</td>
      <td id="T_6c98d_row89_col3" class="data row89 col3" >11</td>
      <td id="T_6c98d_row89_col4" class="data row89 col4" >19</td>
      <td id="T_6c98d_row89_col5" class="data row89 col5" >0.047414</td>
      <td id="T_6c98d_row89_col6" class="data row89 col6" >0.081897</td>
      <td id="T_6c98d_row89_col7" class="data row89 col7" >164</td>
      <td id="T_6c98d_row89_col8" class="data row89 col8" >9</td>
      <td id="T_6c98d_row89_col9" class="data row89 col9" >14</td>
      <td id="T_6c98d_row89_col10" class="data row89 col10" >0.054878</td>
      <td id="T_6c98d_row89_col11" class="data row89 col11" >0.085366</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row90" class="row_heading level0 row90" >90</th>
      <td id="T_6c98d_row90_col0" class="data row90 col0" ></td>
      <td id="T_6c98d_row90_col1" class="data row90 col1" >building = *</td>
      <td id="T_6c98d_row90_col2" class="data row90 col2" >24086</td>
      <td id="T_6c98d_row90_col3" class="data row90 col3" >3114</td>
      <td id="T_6c98d_row90_col4" class="data row90 col4" >3536</td>
      <td id="T_6c98d_row90_col5" class="data row90 col5" >0.129287</td>
      <td id="T_6c98d_row90_col6" class="data row90 col6" >0.146807</td>
      <td id="T_6c98d_row90_col7" class="data row90 col7" >13954</td>
      <td id="T_6c98d_row90_col8" class="data row90 col8" >2306</td>
      <td id="T_6c98d_row90_col9" class="data row90 col9" >2674</td>
      <td id="T_6c98d_row90_col10" class="data row90 col10" >0.165257</td>
      <td id="T_6c98d_row90_col11" class="data row90 col11" >0.191630</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row91" class="row_heading level0 row91" >91</th>
      <td id="T_6c98d_row91_col0" class="data row91 col0" >#</td>
      <td id="T_6c98d_row91_col1" class="data row91 col1" >tourism</td>
      <td id="T_6c98d_row91_col2" class="data row91 col2" >13818</td>
      <td id="T_6c98d_row91_col3" class="data row91 col3" >5455</td>
      <td id="T_6c98d_row91_col4" class="data row91 col4" >4736</td>
      <td id="T_6c98d_row91_col5" class="data row91 col5" >0.394775</td>
      <td id="T_6c98d_row91_col6" class="data row91 col6" >0.342741</td>
      <td id="T_6c98d_row91_col7" class="data row91 col7" >9804</td>
      <td id="T_6c98d_row91_col8" class="data row91 col8" >3400</td>
      <td id="T_6c98d_row91_col9" class="data row91 col9" >3342</td>
      <td id="T_6c98d_row91_col10" class="data row91 col10" >0.346797</td>
      <td id="T_6c98d_row91_col11" class="data row91 col11" >0.340881</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row92" class="row_heading level0 row92" >92</th>
      <td id="T_6c98d_row92_col0" class="data row92 col0" ></td>
      <td id="T_6c98d_row92_col1" class="data row92 col1" >tourism = *</td>
      <td id="T_6c98d_row92_col2" class="data row92 col2" >8999</td>
      <td id="T_6c98d_row92_col3" class="data row92 col3" >4280</td>
      <td id="T_6c98d_row92_col4" class="data row92 col4" >3667</td>
      <td id="T_6c98d_row92_col5" class="data row92 col5" >0.475608</td>
      <td id="T_6c98d_row92_col6" class="data row92 col6" >0.407490</td>
      <td id="T_6c98d_row92_col7" class="data row92 col7" >6461</td>
      <td id="T_6c98d_row92_col8" class="data row92 col8" >2492</td>
      <td id="T_6c98d_row92_col9" class="data row92 col9" >2502</td>
      <td id="T_6c98d_row92_col10" class="data row92 col10" >0.385699</td>
      <td id="T_6c98d_row92_col11" class="data row92 col11" >0.387247</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row93" class="row_heading level0 row93" >93</th>
      <td id="T_6c98d_row93_col0" class="data row93 col0" ></td>
      <td id="T_6c98d_row93_col1" class="data row93 col1" >historic = *</td>
      <td id="T_6c98d_row93_col2" class="data row93 col2" >5293</td>
      <td id="T_6c98d_row93_col3" class="data row93 col3" >1522</td>
      <td id="T_6c98d_row93_col4" class="data row93 col4" >1388</td>
      <td id="T_6c98d_row93_col5" class="data row93 col5" >0.287550</td>
      <td id="T_6c98d_row93_col6" class="data row93 col6" >0.262233</td>
      <td id="T_6c98d_row93_col7" class="data row93 col7" >3860</td>
      <td id="T_6c98d_row93_col8" class="data row93 col8" >1241</td>
      <td id="T_6c98d_row93_col9" class="data row93 col9" >1142</td>
      <td id="T_6c98d_row93_col10" class="data row93 col10" >0.321503</td>
      <td id="T_6c98d_row93_col11" class="data row93 col11" >0.295855</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row94" class="row_heading level0 row94" >94</th>
      <td id="T_6c98d_row94_col0" class="data row94 col0" ></td>
      <td id="T_6c98d_row94_col1" class="data row94 col1" >memorial = *</td>
      <td id="T_6c98d_row94_col2" class="data row94 col2" >1596</td>
      <td id="T_6c98d_row94_col3" class="data row94 col3" >346</td>
      <td id="T_6c98d_row94_col4" class="data row94 col4" >338</td>
      <td id="T_6c98d_row94_col5" class="data row94 col5" >0.216792</td>
      <td id="T_6c98d_row94_col6" class="data row94 col6" >0.211779</td>
      <td id="T_6c98d_row94_col7" class="data row94 col7" >1279</td>
      <td id="T_6c98d_row94_col8" class="data row94 col8" >312</td>
      <td id="T_6c98d_row94_col9" class="data row94 col9" >304</td>
      <td id="T_6c98d_row94_col10" class="data row94 col10" >0.243941</td>
      <td id="T_6c98d_row94_col11" class="data row94 col11" >0.237686</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row95" class="row_heading level0 row95" >95</th>
      <td id="T_6c98d_row95_col0" class="data row95 col0" ></td>
      <td id="T_6c98d_row95_col1" class="data row95 col1" >ruins = *</td>
      <td id="T_6c98d_row95_col2" class="data row95 col2" >213</td>
      <td id="T_6c98d_row95_col3" class="data row95 col3" >57</td>
      <td id="T_6c98d_row95_col4" class="data row95 col4" >74</td>
      <td id="T_6c98d_row95_col5" class="data row95 col5" >0.267606</td>
      <td id="T_6c98d_row95_col6" class="data row95 col6" >0.347418</td>
      <td id="T_6c98d_row95_col7" class="data row95 col7" >161</td>
      <td id="T_6c98d_row95_col8" class="data row95 col8" >54</td>
      <td id="T_6c98d_row95_col9" class="data row95 col9" >68</td>
      <td id="T_6c98d_row95_col10" class="data row95 col10" >0.335404</td>
      <td id="T_6c98d_row95_col11" class="data row95 col11" >0.422360</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row96" class="row_heading level0 row96" >96</th>
      <td id="T_6c98d_row96_col0" class="data row96 col0" ></td>
      <td id="T_6c98d_row96_col1" class="data row96 col1" >information = *</td>
      <td id="T_6c98d_row96_col2" class="data row96 col2" >962</td>
      <td id="T_6c98d_row96_col3" class="data row96 col3" >715</td>
      <td id="T_6c98d_row96_col4" class="data row96 col4" >682</td>
      <td id="T_6c98d_row96_col5" class="data row96 col5" >0.743243</td>
      <td id="T_6c98d_row96_col6" class="data row96 col6" >0.708940</td>
      <td id="T_6c98d_row96_col7" class="data row96 col7" >278</td>
      <td id="T_6c98d_row96_col8" class="data row96 col8" >79</td>
      <td id="T_6c98d_row96_col9" class="data row96 col9" >47</td>
      <td id="T_6c98d_row96_col10" class="data row96 col10" >0.284173</td>
      <td id="T_6c98d_row96_col11" class="data row96 col11" >0.169065</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row97" class="row_heading level0 row97" >97</th>
      <td id="T_6c98d_row97_col0" class="data row97 col0" ></td>
      <td id="T_6c98d_row97_col1" class="data row97 col1" >attraction = *</td>
      <td id="T_6c98d_row97_col2" class="data row97 col2" >165</td>
      <td id="T_6c98d_row97_col3" class="data row97 col3" >41</td>
      <td id="T_6c98d_row97_col4" class="data row97 col4" >28</td>
      <td id="T_6c98d_row97_col5" class="data row97 col5" >0.248485</td>
      <td id="T_6c98d_row97_col6" class="data row97 col6" >0.169697</td>
      <td id="T_6c98d_row97_col7" class="data row97 col7" >145</td>
      <td id="T_6c98d_row97_col8" class="data row97 col8" >36</td>
      <td id="T_6c98d_row97_col9" class="data row97 col9" >24</td>
      <td id="T_6c98d_row97_col10" class="data row97 col10" >0.248276</td>
      <td id="T_6c98d_row97_col11" class="data row97 col11" >0.165517</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row98" class="row_heading level0 row98" >98</th>
      <td id="T_6c98d_row98_col0" class="data row98 col0" ></td>
      <td id="T_6c98d_row98_col1" class="data row98 col1" >resort = *</td>
      <td id="T_6c98d_row98_col2" class="data row98 col2" >133</td>
      <td id="T_6c98d_row98_col3" class="data row98 col3" >11</td>
      <td id="T_6c98d_row98_col4" class="data row98 col4" >52</td>
      <td id="T_6c98d_row98_col5" class="data row98 col5" >0.082707</td>
      <td id="T_6c98d_row98_col6" class="data row98 col6" >0.390977</td>
      <td id="T_6c98d_row98_col7" class="data row98 col7" >126</td>
      <td id="T_6c98d_row98_col8" class="data row98 col8" >11</td>
      <td id="T_6c98d_row98_col9" class="data row98 col9" >49</td>
      <td id="T_6c98d_row98_col10" class="data row98 col10" >0.087302</td>
      <td id="T_6c98d_row98_col11" class="data row98 col11" >0.388889</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row99" class="row_heading level0 row99" >99</th>
      <td id="T_6c98d_row99_col0" class="data row99 col0" ></td>
      <td id="T_6c98d_row99_col1" class="data row99 col1" >artwork_type = *</td>
      <td id="T_6c98d_row99_col2" class="data row99 col2" >576</td>
      <td id="T_6c98d_row99_col3" class="data row99 col3" >169</td>
      <td id="T_6c98d_row99_col4" class="data row99 col4" >183</td>
      <td id="T_6c98d_row99_col5" class="data row99 col5" >0.293403</td>
      <td id="T_6c98d_row99_col6" class="data row99 col6" >0.317708</td>
      <td id="T_6c98d_row99_col7" class="data row99 col7" >533</td>
      <td id="T_6c98d_row99_col8" class="data row99 col8" >160</td>
      <td id="T_6c98d_row99_col9" class="data row99 col9" >177</td>
      <td id="T_6c98d_row99_col10" class="data row99 col10" >0.300188</td>
      <td id="T_6c98d_row99_col11" class="data row99 col11" >0.332083</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row100" class="row_heading level0 row100" >100</th>
      <td id="T_6c98d_row100_col0" class="data row100 col0" >#</td>
      <td id="T_6c98d_row100_col1" class="data row100 col1" >water</td>
      <td id="T_6c98d_row100_col2" class="data row100 col2" >21177</td>
      <td id="T_6c98d_row100_col3" class="data row100 col3" >13619</td>
      <td id="T_6c98d_row100_col4" class="data row100 col4" >14982</td>
      <td id="T_6c98d_row100_col5" class="data row100 col5" >0.643103</td>
      <td id="T_6c98d_row100_col6" class="data row100 col6" >0.707466</td>
      <td id="T_6c98d_row100_col7" class="data row100 col7" >5331</td>
      <td id="T_6c98d_row100_col8" class="data row100 col8" >2922</td>
      <td id="T_6c98d_row100_col9" class="data row100 col9" >3510</td>
      <td id="T_6c98d_row100_col10" class="data row100 col10" >0.548115</td>
      <td id="T_6c98d_row100_col11" class="data row100 col11" >0.658413</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row101" class="row_heading level0 row101" >101</th>
      <td id="T_6c98d_row101_col0" class="data row101 col0" ></td>
      <td id="T_6c98d_row101_col1" class="data row101 col1" >waterway = drain</td>
      <td id="T_6c98d_row101_col2" class="data row101 col2" >387</td>
      <td id="T_6c98d_row101_col3" class="data row101 col3" >63</td>
      <td id="T_6c98d_row101_col4" class="data row101 col4" >130</td>
      <td id="T_6c98d_row101_col5" class="data row101 col5" >0.162791</td>
      <td id="T_6c98d_row101_col6" class="data row101 col6" >0.335917</td>
      <td id="T_6c98d_row101_col7" class="data row101 col7" >105</td>
      <td id="T_6c98d_row101_col8" class="data row101 col8" >25</td>
      <td id="T_6c98d_row101_col9" class="data row101 col9" >39</td>
      <td id="T_6c98d_row101_col10" class="data row101 col10" >0.238095</td>
      <td id="T_6c98d_row101_col11" class="data row101 col11" >0.371429</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row102" class="row_heading level0 row102" >102</th>
      <td id="T_6c98d_row102_col0" class="data row102 col0" ></td>
      <td id="T_6c98d_row102_col1" class="data row102 col1" >waterway = ditch</td>
      <td id="T_6c98d_row102_col2" class="data row102 col2" >543</td>
      <td id="T_6c98d_row102_col3" class="data row102 col3" >133</td>
      <td id="T_6c98d_row102_col4" class="data row102 col4" >160</td>
      <td id="T_6c98d_row102_col5" class="data row102 col5" >0.244936</td>
      <td id="T_6c98d_row102_col6" class="data row102 col6" >0.294659</td>
      <td id="T_6c98d_row102_col7" class="data row102 col7" >99</td>
      <td id="T_6c98d_row102_col8" class="data row102 col8" >24</td>
      <td id="T_6c98d_row102_col9" class="data row102 col9" >33</td>
      <td id="T_6c98d_row102_col10" class="data row102 col10" >0.242424</td>
      <td id="T_6c98d_row102_col11" class="data row102 col11" >0.333333</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row103" class="row_heading level0 row103" >103</th>
      <td id="T_6c98d_row103_col0" class="data row103 col0" ></td>
      <td id="T_6c98d_row103_col1" class="data row103 col1" >waterway = stream</td>
      <td id="T_6c98d_row103_col2" class="data row103 col2" >5904</td>
      <td id="T_6c98d_row103_col3" class="data row103 col3" >2882</td>
      <td id="T_6c98d_row103_col4" class="data row103 col4" >4176</td>
      <td id="T_6c98d_row103_col5" class="data row103 col5" >0.488144</td>
      <td id="T_6c98d_row103_col6" class="data row103 col6" >0.707317</td>
      <td id="T_6c98d_row103_col7" class="data row103 col7" >1063</td>
      <td id="T_6c98d_row103_col8" class="data row103 col8" >485</td>
      <td id="T_6c98d_row103_col9" class="data row103 col9" >760</td>
      <td id="T_6c98d_row103_col10" class="data row103 col10" >0.456256</td>
      <td id="T_6c98d_row103_col11" class="data row103 col11" >0.714958</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row104" class="row_heading level0 row104" >104</th>
      <td id="T_6c98d_row104_col0" class="data row104 col0" ></td>
      <td id="T_6c98d_row104_col1" class="data row104 col1" >waterway = river</td>
      <td id="T_6c98d_row104_col2" class="data row104 col2" >10185</td>
      <td id="T_6c98d_row104_col3" class="data row104 col3" >8390</td>
      <td id="T_6c98d_row104_col4" class="data row104 col4" >8090</td>
      <td id="T_6c98d_row104_col5" class="data row104 col5" >0.823760</td>
      <td id="T_6c98d_row104_col6" class="data row104 col6" >0.794305</td>
      <td id="T_6c98d_row104_col7" class="data row104 col7" >1404</td>
      <td id="T_6c98d_row104_col8" class="data row104 col8" >1062</td>
      <td id="T_6c98d_row104_col9" class="data row104 col9" >1068</td>
      <td id="T_6c98d_row104_col10" class="data row104 col10" >0.756410</td>
      <td id="T_6c98d_row104_col11" class="data row104 col11" >0.760684</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row105" class="row_heading level0 row105" >105</th>
      <td id="T_6c98d_row105_col0" class="data row105 col0" ></td>
      <td id="T_6c98d_row105_col1" class="data row105 col1" >waterway = canal</td>
      <td id="T_6c98d_row105_col2" class="data row105 col2" >516</td>
      <td id="T_6c98d_row105_col3" class="data row105 col3" >245</td>
      <td id="T_6c98d_row105_col4" class="data row105 col4" >188</td>
      <td id="T_6c98d_row105_col5" class="data row105 col5" >0.474806</td>
      <td id="T_6c98d_row105_col6" class="data row105 col6" >0.364341</td>
      <td id="T_6c98d_row105_col7" class="data row105 col7" >113</td>
      <td id="T_6c98d_row105_col8" class="data row105 col8" >42</td>
      <td id="T_6c98d_row105_col9" class="data row105 col9" >37</td>
      <td id="T_6c98d_row105_col10" class="data row105 col10" >0.371681</td>
      <td id="T_6c98d_row105_col11" class="data row105 col11" >0.327434</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row106" class="row_heading level0 row106" >106</th>
      <td id="T_6c98d_row106_col0" class="data row106 col0" ></td>
      <td id="T_6c98d_row106_col1" class="data row106 col1" >type = waterway</td>
      <td id="T_6c98d_row106_col2" class="data row106 col2" >0</td>
      <td id="T_6c98d_row106_col3" class="data row106 col3" >0</td>
      <td id="T_6c98d_row106_col4" class="data row106 col4" >0</td>
      <td id="T_6c98d_row106_col5" class="data row106 col5" >0.000000</td>
      <td id="T_6c98d_row106_col6" class="data row106 col6" >0.000000</td>
      <td id="T_6c98d_row106_col7" class="data row106 col7" >0</td>
      <td id="T_6c98d_row106_col8" class="data row106 col8" >0</td>
      <td id="T_6c98d_row106_col9" class="data row106 col9" >0</td>
      <td id="T_6c98d_row106_col10" class="data row106 col10" >0.000000</td>
      <td id="T_6c98d_row106_col11" class="data row106 col11" >0.000000</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row107" class="row_heading level0 row107" >107</th>
      <td id="T_6c98d_row107_col0" class="data row107 col0" ></td>
      <td id="T_6c98d_row107_col1" class="data row107 col1" >natural = water</td>
      <td id="T_6c98d_row107_col2" class="data row107 col2" >3018</td>
      <td id="T_6c98d_row107_col3" class="data row107 col3" >1807</td>
      <td id="T_6c98d_row107_col4" class="data row107 col4" >2147</td>
      <td id="T_6c98d_row107_col5" class="data row107 col5" >0.598741</td>
      <td id="T_6c98d_row107_col6" class="data row107 col6" >0.711398</td>
      <td id="T_6c98d_row107_col7" class="data row107 col7" >2453</td>
      <td id="T_6c98d_row107_col8" class="data row107 col8" >1479</td>
      <td id="T_6c98d_row107_col9" class="data row107 col9" >1767</td>
      <td id="T_6c98d_row107_col10" class="data row107 col10" >0.602935</td>
      <td id="T_6c98d_row107_col11" class="data row107 col11" >0.720342</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row108" class="row_heading level0 row108" >108</th>
      <td id="T_6c98d_row108_col0" class="data row108 col0" ></td>
      <td id="T_6c98d_row108_col1" class="data row108 col1" >natural = spring</td>
      <td id="T_6c98d_row108_col2" class="data row108 col2" >588</td>
      <td id="T_6c98d_row108_col3" class="data row108 col3" >89</td>
      <td id="T_6c98d_row108_col4" class="data row108 col4" >80</td>
      <td id="T_6c98d_row108_col5" class="data row108 col5" >0.151361</td>
      <td id="T_6c98d_row108_col6" class="data row108 col6" >0.136054</td>
      <td id="T_6c98d_row108_col7" class="data row108 col7" >529</td>
      <td id="T_6c98d_row108_col8" class="data row108 col8" >75</td>
      <td id="T_6c98d_row108_col9" class="data row108 col9" >79</td>
      <td id="T_6c98d_row108_col10" class="data row108 col10" >0.141777</td>
      <td id="T_6c98d_row108_col11" class="data row108 col11" >0.149338</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row109" class="row_heading level0 row109" >109</th>
      <td id="T_6c98d_row109_col0" class="data row109 col0" ></td>
      <td id="T_6c98d_row109_col1" class="data row109 col1" >waterway = *</td>
      <td id="T_6c98d_row109_col2" class="data row109 col2" >35</td>
      <td id="T_6c98d_row109_col3" class="data row109 col3" >10</td>
      <td id="T_6c98d_row109_col4" class="data row109 col4" >11</td>
      <td id="T_6c98d_row109_col5" class="data row109 col5" >0.285714</td>
      <td id="T_6c98d_row109_col6" class="data row109 col6" >0.314286</td>
      <td id="T_6c98d_row109_col7" class="data row109 col7" >29</td>
      <td id="T_6c98d_row109_col8" class="data row109 col8" >8</td>
      <td id="T_6c98d_row109_col9" class="data row109 col9" >9</td>
      <td id="T_6c98d_row109_col10" class="data row109 col10" >0.275862</td>
      <td id="T_6c98d_row109_col11" class="data row109 col11" >0.310345</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row110" class="row_heading level0 row110" >110</th>
      <td id="T_6c98d_row110_col0" class="data row110 col0" ></td>
      <td id="T_6c98d_row110_col1" class="data row110 col1" >water = *</td>
      <td id="T_6c98d_row110_col2" class="data row110 col2" >2906</td>
      <td id="T_6c98d_row110_col3" class="data row110 col3" >1792</td>
      <td id="T_6c98d_row110_col4" class="data row110 col4" >2131</td>
      <td id="T_6c98d_row110_col5" class="data row110 col5" >0.616655</td>
      <td id="T_6c98d_row110_col6" class="data row110 col6" >0.733310</td>
      <td id="T_6c98d_row110_col7" class="data row110 col7" >2358</td>
      <td id="T_6c98d_row110_col8" class="data row110 col8" >1465</td>
      <td id="T_6c98d_row110_col9" class="data row110 col9" >1752</td>
      <td id="T_6c98d_row110_col10" class="data row110 col10" >0.621289</td>
      <td id="T_6c98d_row110_col11" class="data row110 col11" >0.743003</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row111" class="row_heading level0 row111" >111</th>
      <td id="T_6c98d_row111_col0" class="data row111 col0" >#</td>
      <td id="T_6c98d_row111_col1" class="data row111 col1" >natural</td>
      <td id="T_6c98d_row111_col2" class="data row111 col2" >1508</td>
      <td id="T_6c98d_row111_col3" class="data row111 col3" >427</td>
      <td id="T_6c98d_row111_col4" class="data row111 col4" >654</td>
      <td id="T_6c98d_row111_col5" class="data row111 col5" >0.283156</td>
      <td id="T_6c98d_row111_col6" class="data row111 col6" >0.433687</td>
      <td id="T_6c98d_row111_col7" class="data row111 col7" >1221</td>
      <td id="T_6c98d_row111_col8" class="data row111 col8" >371</td>
      <td id="T_6c98d_row111_col9" class="data row111 col9" >564</td>
      <td id="T_6c98d_row111_col10" class="data row111 col10" >0.303849</td>
      <td id="T_6c98d_row111_col11" class="data row111 col11" >0.461916</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row112" class="row_heading level0 row112" >112</th>
      <td id="T_6c98d_row112_col0" class="data row112 col0" ></td>
      <td id="T_6c98d_row112_col1" class="data row112 col1" >place = island</td>
      <td id="T_6c98d_row112_col2" class="data row112 col2" >11</td>
      <td id="T_6c98d_row112_col3" class="data row112 col3" >3</td>
      <td id="T_6c98d_row112_col4" class="data row112 col4" >3</td>
      <td id="T_6c98d_row112_col5" class="data row112 col5" >0.272727</td>
      <td id="T_6c98d_row112_col6" class="data row112 col6" >0.272727</td>
      <td id="T_6c98d_row112_col7" class="data row112 col7" >11</td>
      <td id="T_6c98d_row112_col8" class="data row112 col8" >3</td>
      <td id="T_6c98d_row112_col9" class="data row112 col9" >3</td>
      <td id="T_6c98d_row112_col10" class="data row112 col10" >0.272727</td>
      <td id="T_6c98d_row112_col11" class="data row112 col11" >0.272727</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row113" class="row_heading level0 row113" >113</th>
      <td id="T_6c98d_row113_col0" class="data row113 col0" ></td>
      <td id="T_6c98d_row113_col1" class="data row113 col1" >place = islet</td>
      <td id="T_6c98d_row113_col2" class="data row113 col2" >86</td>
      <td id="T_6c98d_row113_col3" class="data row113 col3" >47</td>
      <td id="T_6c98d_row113_col4" class="data row113 col4" >78</td>
      <td id="T_6c98d_row113_col5" class="data row113 col5" >0.546512</td>
      <td id="T_6c98d_row113_col6" class="data row113 col6" >0.906977</td>
      <td id="T_6c98d_row113_col7" class="data row113 col7" >76</td>
      <td id="T_6c98d_row113_col8" class="data row113 col8" >43</td>
      <td id="T_6c98d_row113_col9" class="data row113 col9" >68</td>
      <td id="T_6c98d_row113_col10" class="data row113 col10" >0.565789</td>
      <td id="T_6c98d_row113_col11" class="data row113 col11" >0.894737</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row114" class="row_heading level0 row114" >114</th>
      <td id="T_6c98d_row114_col0" class="data row114 col0" ></td>
      <td id="T_6c98d_row114_col1" class="data row114 col1" >natural = *</td>
      <td id="T_6c98d_row114_col2" class="data row114 col2" >1449</td>
      <td id="T_6c98d_row114_col3" class="data row114 col3" >391</td>
      <td id="T_6c98d_row114_col4" class="data row114 col4" >608</td>
      <td id="T_6c98d_row114_col5" class="data row114 col5" >0.269841</td>
      <td id="T_6c98d_row114_col6" class="data row114 col6" >0.419600</td>
      <td id="T_6c98d_row114_col7" class="data row114 col7" >1172</td>
      <td id="T_6c98d_row114_col8" class="data row114 col8" >338</td>
      <td id="T_6c98d_row114_col9" class="data row114 col9" >527</td>
      <td id="T_6c98d_row114_col10" class="data row114 col10" >0.288396</td>
      <td id="T_6c98d_row114_col11" class="data row114 col11" >0.449659</td>
    </tr>
    <tr>
      <th id="T_6c98d_level0_row115" class="row_heading level0 row115" >115</th>
      <td id="T_6c98d_row115_col0" class="data row115 col0" >#</td>
      <td id="T_6c98d_row115_col1" class="data row115 col1" >other</td>
      <td id="T_6c98d_row115_col2" class="data row115 col2" >0</td>
      <td id="T_6c98d_row115_col3" class="data row115 col3" >0</td>
      <td id="T_6c98d_row115_col4" class="data row115 col4" >0</td>
      <td id="T_6c98d_row115_col5" class="data row115 col5" >0.000000</td>
      <td id="T_6c98d_row115_col6" class="data row115 col6" >0.000000</td>
      <td id="T_6c98d_row115_col7" class="data row115 col7" >0</td>
      <td id="T_6c98d_row115_col8" class="data row115 col8" >0</td>
      <td id="T_6c98d_row115_col9" class="data row115 col9" >0</td>
      <td id="T_6c98d_row115_col10" class="data row115 col10" >0.000000</td>
      <td id="T_6c98d_row115_col11" class="data row115 col11" >0.000000</td>
    </tr>
  </tbody>
</table>





```python

```
