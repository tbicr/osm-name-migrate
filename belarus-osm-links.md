# Аналіз дадзеных імёнаў у ОСМ Беларусі

## Зьмест

- Праблематыка
- Спампуем дамп ОСМ
- Усталёўваем залежанасьцьі
- Пошук сувязей дзеля падтрыманьня спасылачнай цэласнасьці

## Праблематыка

У беларускім ОСМ шырока выкарыстоўваюцца беларуская і расейская мова, для іх ёсьць адпаведнікі `name:be` і `name:ru`, таксама мовы выкарыстоўваюцца ў агульных тэгах як `name`, `addr:*` і іншых. Праблематка выкарыстоўваньня аднае, ці іншае, ці абедзьвух моваў апісанае тут https://wiki.openstreetmap.org/wiki/BE:Belarus_language_issues. Незалежна ад варыянту выкарыстоўваньня мовы павінны вытрымлівацца наступныя правілы: пошук на любое мове мусіць працаваць, павінна быць магчымасьць паказываць подпісы на любой мове (ці ў арыгінале, але гэтае правіла зараз не выконваецца), павінна захоўвацца спасылкавая цэласнасьць (што можа ўплываць на папярэднія два пункты).

Гэты аналіз ставіць мэтаю знайсьці адпаведныя катэгорыі і тэгі ў якіх кірылічныя значэньні на беларускай альбо расейскай мовах выкарыстоўваюцца як спасылка.

## Спампуем дамп ОСМ


```python
!wget https://download.geofabrik.de/europe/belarus-latest.osm.pbf
```

    --2021-03-17 18:35:46--  https://download.geofabrik.de/europe/belarus-latest.osm.pbf
    Resolving download.geofabrik.de (download.geofabrik.de)... 88.99.142.44, 138.201.219.183, 116.202.112.212
    Connecting to download.geofabrik.de (download.geofabrik.de)|88.99.142.44|:443... connected.
    HTTP request sent, awaiting response... 200 OK
    Length: 242289054 (231M) [application/octet-stream]
    Saving to: ‘belarus-latest.osm.pbf.1’
    
    belarus-latest.osm. 100%[===================>] 231.06M  1.15MB/s    in 2m 26s  
    
    2021-03-17 18:38:13 (1.58 MB/s) - ‘belarus-latest.osm.pbf.1’ saved [242289054/242289054]
    


## Усталюем залежнасьці


```python
!pip install https://github.com/lechup/imposm-parser/archive/python3.zip
```

    /bin/bash: pip: command not found


## Пошук залезнасьцяў


```python
from collections import defaultdict, Counter

from imposm.parser import OSMParser


cirylic_chars = frozenset('абвгдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГДЕЁЖЗІИІЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ')

# this keys should not be used as links
skip_lang_names = {
    'name:left',
    'name:right',
    'int_name',
    'loc_name',
    'nat_name',
    'old_name',
    'reg_name',
    'sorting_name',
    'alt_name',
}

# language specific keys prefixes also should not be used as links
skip_lang_names_prefixes = (
    'name:',
    'loc_name:',
    'nat_name:',
    'official_name:',
    'old_name:',
    'reg_name:',
    'short_name:',
    'sorting_name:',
    'alt_name:',
)

# also skip keys with most common lang suffixes
skip_lang_suffixes = (
    ':be',
    ':ru',
)
```


```python
key_counter = Counter()
key_val_counter = defaultdict(Counter)
key_val_tag_counter = defaultdict(lambda: defaultdict(Counter))


def process(params):
    for _, tags, _ in params:
        keys_and_tags = set()
        for k, v in tags.items():
            if k.startswith(skip_lang_names_prefixes):
                continue
            if k.endswith(skip_lang_suffixes):
                continue
            keys_and_tags |= {(k,)} | {(k, v)}
        for k, v in tags.items():
            if frozenset(v) & cirylic_chars:
                key_counter[k] += 1
            if k in skip_lang_names:
                continue
            if k.startswith(skip_lang_names_prefixes):
                continue
            if k.endswith(skip_lang_suffixes):
                continue
            if len(frozenset(v) & cirylic_chars) > 0:
                key_val_counter[k][v] += 1
                for key_or_tag in keys_and_tags - {(k,)} - {(k, v)}:
                    key_val_tag_counter[k][v][key_or_tag] += 1

                        
OSMParser(
    nodes_callback=process,
    ways_callback=process,
    relations_callback=process,
).parse('belarus-latest.osm.pbf')
```


```python
# cirylic tag values count
for k, c in key_counter.most_common():
    uniq_values = len(key_val_counter[k]) or ''
    print(f'{k.ljust(30)} {str(c).rjust(6)} {str(uniq_values).rjust(6)}')
```

    addr:street                    813801   9562
    name                           314939 109482
    name:ru                        203692       
    name:be                        186995       
    addr:city                       81913   1950
    addr:housenumber                72933   5390
    ref                             64029  11856
    name:prefix                     57217       
    addr:district                   51156    144
    addr:region                     50941     13
    addr:place                      35625   1151
    operator                        34810   6060
    wikipedia                       33095  29299
    official_name                   24827   8400
    name:prefix:ru                  12569       
    description                     11916   5886
    addr:subdistrict                10563    767
    source:population               10348      1
    alt_name:be                      8545       
    name:be-tarask                   8225       
    minsk_PT:note                    6445      3
    source                           5489     77
    name:uk                          5075       
    alt_name:ru                      4292       
    name:prefix:be                   4036       
    official_short_type              3238     35
    int_name                         3130       
    brand                            2936    185
    note                             2869   1525
    short_name                       2354   1801
    ...

```python
eq_keys_pair_vals1_counter = Counter()
eq_keys_pair_vals2_counter = Counter()
eq_keys_pair_tag_vals1_counter = defaultdict(Counter)
eq_keys_pair_tag_vals2_counter = defaultdict(Counter)
eq_keys_pair_val_tag_vals1_counter = defaultdict(Counter)
eq_keys_pair_val_tag_vals2_counter = defaultdict(Counter)

in_keys_pair_vals1_counter = Counter()
in_keys_pair_vals2_counter = Counter()
in_keys_pair_tag_vals1_counter = defaultdict(Counter)
in_keys_pair_tag_vals2_counter = defaultdict(Counter)
in_keys_pair_val_tag_vals1_counter = defaultdict(Counter)
in_keys_pair_val_tag_vals2_counter = defaultdict(Counter)


for k1, vals_counter1 in sorted(key_val_counter.items(), key=lambda kv: -len(kv[1])):
    for k2, vals_counter2 in sorted(key_val_counter.items(), key=lambda kv: -len(kv[1])):
        if k1 == k2:
            continue

        x = (k1, k2)
        for val1, vals_count1 in vals_counter1.items():    
            for val2, vals_count2 in vals_counter2.items():
                if val1 == val2:
                    eq_keys_pair_vals1_counter[x] += vals_count1
                    eq_keys_pair_vals2_counter[x] += vals_count2
                    
                    eq_keys_pair_tag_vals1_counter[x][val1] += vals_count1
                    eq_keys_pair_tag_vals2_counter[x][val2] += vals_count2
                    
                    for key_or_tag, tags_count1 in key_val_tag_counter[k1][val1].items():
                        eq_keys_pair_val_tag_vals1_counter[x][key_or_tag] += tags_count1
                    for key_or_tag, tags_count2 in key_val_tag_counter[k2][val2].items():
                        eq_keys_pair_val_tag_vals2_counter[x][key_or_tag] += tags_count2
                if val1 in val2:                    
                    in_keys_pair_vals1_counter[x] += vals_count1
                    in_keys_pair_vals2_counter[x] += vals_count2
                
                    in_keys_pair_tag_vals1_counter[x][val1] += vals_count1
                    in_keys_pair_tag_vals2_counter[x][val2] += vals_count2
                    
                    for key_or_tag, tags_count1 in key_val_tag_counter[k1][val1].items():
                        in_keys_pair_val_tag_vals1_counter[x][key_or_tag] += tags_count1
                    for key_or_tag, tags_count2 in key_val_tag_counter[k2][val2].items():
                        in_keys_pair_val_tag_vals2_counter[x][key_or_tag] += tags_count2

```


```python
def sortv(counter):
    return sorted(counter.items(), key=lambda kv: -kv[1])


shown = set()
keys = Counter()
for k in sorted(in_keys_pair_vals1_counter.keys(), 
                key=lambda k: -max(in_keys_pair_vals1_counter[k], in_keys_pair_vals2_counter[k])):
    x = tuple(sorted(k))
    if x in shown:
        continue
    shown.add(x)
    keys[k[0]] += 1
    keys[k[1]] += 1
    
    print(*k, in_keys_pair_vals1_counter[k], in_keys_pair_vals2_counter[k], 
              eq_keys_pair_vals1_counter[k], eq_keys_pair_vals2_counter[k])
    print('\t', len(in_keys_pair_tag_vals1_counter[k]), *sortv(in_keys_pair_tag_vals1_counter[k])[:3])
    print('\t', len(in_keys_pair_tag_vals2_counter[k]), *sortv(in_keys_pair_tag_vals2_counter[k])[:3])
    print('\t', len(in_keys_pair_val_tag_vals1_counter[k]), *sortv(in_keys_pair_val_tag_vals1_counter[k])[:3])
    print('\t', len(in_keys_pair_val_tag_vals2_counter[k]), *sortv(in_keys_pair_val_tag_vals1_counter[k])[:3])
    print('\t', len(eq_keys_pair_tag_vals1_counter[k]), *sortv(eq_keys_pair_tag_vals1_counter[k])[:3])
    print('\t', len(eq_keys_pair_tag_vals2_counter[k]), *sortv(eq_keys_pair_tag_vals2_counter[k])[:3])
    print('\t', len(eq_keys_pair_val_tag_vals1_counter[k]), *sortv(eq_keys_pair_val_tag_vals1_counter[k])[:3])
    print('\t', len(eq_keys_pair_val_tag_vals2_counter[k]), *sortv(eq_keys_pair_val_tag_vals2_counter[k])[:3])

```

    addr:housenumber name 17254739 431507 40536 4912
    	 393 ('н', 15592518) ('Н', 571680) ('ж', 384454)
    	 85227 ('Молодёжная улица', 6688) ('Центральная улица', 5298) ('Лесная улица', 2464)
    	 15009 (('building',), 17233859) (('building', 'yes'), 16723077) (('addr:street',), 14553334)
    	 139940 (('building',), 17233859) (('building', 'yes'), 16723077) (('addr:street',), 14553334)
    	 207 ('1А', 3265) ('2А', 3210) ('3А', 1618)
    	 207 ('Магазин', 534) ('Н', 382) ('КН', 369)
    	 13584 (('building',), 39164) (('addr:street',), 38631) (('building', 'yes'), 23577)
    	 1674 (('building',), 4025) (('building', 'yes'), 2533) (('addr:street',), 990)
    addr:housename name 12097466 823503 1278 10788
    	 326 ('н', 9901818) ('Н', 1329156) ('к', 390194)
    	 102808 ('Центральная улица', 7947) ('Молодёжная улица', 6688) ('Советская улица', 5970)
    	 770 (('building',), 12076432) (('building', 'yes'), 11757554) (('addr:street',), 8858907)
    	 173658 (('building',), 12076432) (('building', 'yes'), 11757554) (('addr:street',), 8858907)
    	 284 ('Н', 279) ('н', 174) ('кн', 99)
    	 284 ('Лесная улица', 1232) ('Беларусбанк', 1045) ('Магазин', 534)
    	 738 (('building',), 1240) (('building', 'yes'), 1149) (('addr:street',), 983)
    	 4901 (('building',), 5522) (('building', 'yes'), 3738) (('amenity',), 3249)
    addr:city name 11281746 60506 78524 17816
    	 1782 ('Минск', 8001140) ('Гродно', 1584900) ('Брест', 540753)
    	 15673 ('Центральная улица', 2649) ('Советская улица', 1990) ('Садовая улица', 1552)
    	 30462 (('addr:street',), 10833614) (('addr:housenumber',), 10611271) (('building',), 8312518)
    	 42852 (('addr:street',), 10833614) (('addr:housenumber',), 10611271) (('building',), 8312518)
    	 1749 ('Минск', 9380) ('Гродно', 5870) ('Колодищи', 3727)
    	 1749 ('Каменка', 367) ('Новосёлки', 261) ('Слобода', 200)
    	 30280 (('building',), 71641) (('addr:street',), 70734) (('addr:housenumber',), 69637)
    	 18056 (('place',), 11654) (('int_name',), 11360) (('addr:region',), 9888)
    addr:region wikipedia 9478919 1912 0 0
    	 13 ('Могилёвская область', 2965343) ('Гомельская область', 2050376) ('Минская область', 1599305)
    	 1582 ('ru:Улица Есенина (Минск)', 22) ('ru:Улица Маяковского (Минск)', 12) ('ru:Красноармейская улица (Минск)', 7)
    	 88131 (('addr:district',), 9304270) (('addr:country',), 9250388) (('addr:country', 'BY'), 9228144)
    	 5734 (('addr:district',), 9304270) (('addr:country',), 9250388) (('addr:country', 'BY'), 9228144)
    	 0
    	 0
    	 0
    	 0
    name wikipedia 7120209 234856 0 0
    	 8802 ('н', 5357457) ('Н', 558102) ('к', 261050)
    	 29277 ('be:Праспект Дзяржынскага (Мінск)', 1111) ('be:Альхоўка (басейн Нёмана)', 380) ('ru:Магистраль М12 (Белоруссия)', 312)
    	 44440 (('building',), 6615474) (('building', 'yes'), 5668394) (('building', 'residential'), 765868)
    	 77781 (('building',), 6615474) (('building', 'yes'), 5668394) (('building', 'residential'), 765868)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber wikipedia 5659782 59964 0 0
    	 35 ('н', 5299434) ('Н', 175320) ('ж', 79723)
    	 26181 ('be:Праспект Дзяржынскага (Мінск)', 606) ('be:Бярэзіна', 128) ('ru:Магистраль М12 (Белоруссия)', 117)
    	 225 (('building',), 5658321) (('building', 'yes'), 5536951) (('addr:street',), 4770652)
    	 68905 (('building',), 5658321) (('building', 'yes'), 5536951) (('addr:street',), 4770652)
    	 0
    	 0
    	 0
    	 0
    name addr:street 2100218 5085251 82390 811491
    	 11466 ('н', 1392202) ('Н', 165406) ('к', 65870)
    	 9561 ('Центральная улица', 276651) ('Советская улица', 181506) ('Молодёжная улица', 116067)
    	 31830 (('building',), 1787515) (('building', 'yes'), 1523938) (('highway',), 229956)
    	 65778 (('building',), 1787515) (('building', 'yes'), 1523938) (('highway',), 229956)
    	 9095 ('Центральная улица', 2649) ('Советская улица', 1990) ('Молодёжная улица', 1672)
    	 9095 ('Центральная улица', 30739) ('Советская улица', 30251) ('Молодёжная улица', 16581)
    	 17167 (('highway',), 79940) (('int_name',), 69132) (('highway', 'residential'), 50433)
    	 65297 (('building',), 790801) (('addr:housenumber',), 781274) (('building', 'yes'), 470397)
    addr:housename wikipedia 4057389 115276 0 0
    	 46 ('н', 3365334) ('Н', 407619) ('к', 182735)
    	 29054 ('be:Праспект Дзяржынскага (Мінск)', 606) ('be:Альхоўка (басейн Нёмана)', 228) ('be:Лоша (прыток Ашмянкі)', 150)
    	 210 (('building',), 4052262) (('building', 'yes'), 3943164) (('addr:street',), 2973433)
    	 77070 (('building',), 4052262) (('building', 'yes'), 3943164) (('addr:street',), 2973433)
    	 0
    	 0
    	 0
    	 0
    name ref 3606366 81470 19773 3024
    	 1082 ('Н', 3031552) ('ТП', 197802) ('К-150', 188705)
    	 11523 ('М1', 4148) ('б/н', 1598) ('М6', 1261)
    	 9718 (('building',), 3320657) (('building', 'residential'), 1870968) (('building', 'yes'), 1035666)
    	 16245 (('building',), 3320657) (('building', 'residential'), 1870968) (('building', 'yes'), 1035666)
    	 456 ('Центральная улица', 2649) ('Советская улица', 1990) ('Садовая улица', 1552)
    	 456 ('М1', 2074) ('Р16', 63) ('ПНС', 60)
    	 5014 (('highway',), 16974) (('int_name',), 12927) (('highway', 'residential'), 10378)
    	 1157 (('highway',), 2323) (('surface',), 2234) (('surface', 'asphalt'), 2222)
    addr:city wikipedia 3306646 8459 0 0
    	 1120 ('Минск', 2251200) ('Гомель', 329918) ('Брест', 243408)
    	 5872 ('be:Праспект Дзяржынскага (Мінск)', 101) ('be:Лоша (прыток Ашмянкі)', 25) ('ru:Улица Маяковского (Минск)', 24)
    	 28326 (('addr:street',), 3180732) (('addr:housenumber',), 3111938) (('building',), 2429166)
    	 17444 (('addr:street',), 3180732) (('addr:housenumber',), 3111938) (('building',), 2429166)
    	 0
    	 0
    	 0
    	 0
    description name 3141663 288145 1268 9855
    	 599 ('н', 3016071) ('улица', 49140) ('Шиномонтаж', 17184)
    	 68703 ('Центральная улица', 5298) ('Молодёжная улица', 5016) ('Лесная улица', 2464)
    	 2421 (('building',), 3063998) (('building', 'yes'), 3058266) (('addr:street',), 2940128)
    	 112431 (('building',), 3063998) (('building', 'yes'), 3058266) (('addr:street',), 2940128)
    	 423 ('Шиномонтаж', 358) ('н', 53) ('н/ж', 53)
    	 423 ('Магазин', 534) ('Продукты', 529) ('кладбище', 436)
    	 1768 (('building',), 585) (('shop',), 475) (('building', 'yes'), 457)
    	 4023 (('building',), 4875) (('building', 'yes'), 3235) (('shop',), 2006)
    addr:city operator 2895789 10298 676 8
    	 174 ('Минск', 1547700) ('Гродно', 1197480) ('Брест', 59469)
    	 1104 ('КТУП «Гомельоблпассажиртранс»', 1665) ('ОАО "Гроднооблавтотранс"', 1028) ('ОАО «Витебскоблавтотранс»', 819)
    	 25030 (('addr:street',), 2816440) (('addr:housenumber',), 2759914) (('building',), 2151196)
    	 13703 (('addr:street',), 2816440) (('addr:housenumber',), 2759914) (('building',), 2151196)
    	 7 ('Гомель', 586) ('Восход', 66) ('Радуга', 14)
    	 7 ('Дружба', 2) ('Гомель', 1) ('Восход', 1)
    	 1975 (('addr:street',), 643) (('addr:housenumber',), 638) (('building',), 502)
    	 42 (('name',), 4) (('shop',), 3) (('opening_hours',), 3)
    name official_name 2615396 245592 1390 2606
    	 9526 ('н', 1597736) ('Н', 317060) ('к', 62120)
    	 8400 ('Столбцы — Ивацевичи — Кобрин', 3636) ('Борисов — Вилейка — Ошмяны', 3248) ('граница Республики Польша (Песчатка) — Каменец — Шерешево — Свислочь', 2736)
    	 55240 (('building',), 2206786) (('building', 'yes'), 1789024) (('building', 'residential'), 331488)
    	 18521 (('building',), 2206786) (('building', 'yes'), 1789024) (('building', 'residential'), 331488)
    	 276 ('Юбилейная улица', 607) ('РУП «Издательство «Белбланкавыд»', 76) ('улица Володарского', 75)
    	 276 ('Столбцы — Ивацевичи — Кобрин', 303) ('Борисов — Вилейка — Ошмяны', 232) ('Витебск — Городок (до автомобильной дороги М-8)', 146)
    	 1727 (('highway',), 806) (('int_name',), 724) (('highway', 'residential'), 480)
    	 1543 (('highway',), 2478) (('ref',), 2428) (('surface',), 2353)
    addr:city official_name 2326473 27903 310 9
    	 1040 ('Минск', 1172500) ('Гродно', 798320) ('Брест', 23511)
    	 3986 ('Столбцы — Ивацевичи — Кобрин', 909) ('Борисов — Вилейка — Ошмяны', 696) ('граница Республики Польша (Песчатка) — Каменец — Шерешево — Свислочь', 432)
    	 28470 (('addr:street',), 2240567) (('addr:housenumber',), 2198808) (('building',), 1758714)
    	 8724 (('addr:street',), 2240567) (('addr:housenumber',), 2198808) (('building',), 1758714)
    	 6 ('Носилово', 233) ('Мозырь', 46) ('Мороськи', 25)
    	 6 ('Центральная', 3) ('Носилово', 2) ('Мозырь', 1)
    	 489 (('addr:street',), 291) (('building',), 272) (('addr:housenumber',), 269)
    	 92 (('surface', 'asphalt'), 6) (('surface',), 6) (('name',), 6)
    addr:housename ref 2255726 51575 470 226
    	 94 ('Н', 2214144) ('н', 34452) ('к', 1449)
    	 10583 ('М1', 2074) ('М6', 1261) ('М5', 1230)
    	 335 (('building',), 2239495) (('building', 'yes'), 2214207) (('addr:street',), 2029895)
    	 14614 (('building',), 2239495) (('building', 'yes'), 2214207) (('addr:street',), 2029895)
    	 49 ('Н', 279) ('кн', 99) ('ж', 20)
    	 49 ('ПНС', 60) ('ТП', 27) ('7а', 13)
    	 169 (('building',), 467) (('building', 'yes'), 445) (('addr:street',), 408)
    	 341 (('building',), 90) (('name',), 75) (('substance',), 67)
    addr:housename addr:street 1070447 2235491 4 14793
    	 53 ('н', 874524) ('Н', 120807) ('к', 46109)
    	 9547 ('Центральная улица', 92217) ('Советская улица', 90753) ('Молодёжная улица', 66324)
    	 279 (('building',), 1069138) (('building', 'yes'), 1039802) (('addr:street',), 787723)
    	 65766 (('building',), 1069138) (('building', 'yes'), 1039802) (('addr:street',), 787723)
    	 2 ('Лесная улица', 3) ('Пролетарская улица', 1)
    	 2 ('Лесная улица', 9003) ('Пролетарская улица', 5790)
    	 10 (('building',), 4) (('addr:housenumber',), 4) (('building', 'yes'), 3)
    	 1649 (('building',), 14612) (('addr:housenumber',), 14004) (('building', 'yes'), 9370)
    addr:housenumber official_name 1771361 51175 0 0
    	 53 ('н', 1580432) ('Н', 99600) ('ж', 46109)
    	 7408 ('Борисов — Вилейка — Ошмяны', 696) ('Столбцы — Ивацевичи — Кобрин', 606) ('Минск — Калачи — Мядель', 294)
    	 290 (('building',), 1770427) (('building', 'yes'), 1725739) (('addr:street',), 1491340)
    	 16300 (('building',), 1770427) (('building', 'yes'), 1725739) (('addr:street',), 1491340)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber addr:street 1482082 1261983 1 1
    	 40 ('н', 1377124) ('Н', 51960) ('ж', 26313)
    	 7754 ('Молодёжная улица', 66324) ('Центральная улица', 61478) ('Советская улица', 30251)
    	 2090 (('building',), 1481563) (('building', 'yes'), 1448163) (('addr:street',), 1249099)
    	 57838 (('building',), 1481563) (('building', 'yes'), 1448163) (('addr:street',), 1249099)
    	 1 ('Грабск 2,5км', 1)
    	 1 ('Грабск 2,5км', 1)
    	 4 (('addr:street',), 1) (('building',), 1) (('addr:street', 'Грабск 2,5км'), 1)
    	 4 (('building',), 1) (('addr:housenumber',), 1) (('addr:housenumber', 'Грабск 2,5км'), 1)
    addr:housenumber description 1428633 28886 886 263
    	 118 ('н', 1260674) ('ж', 60368) ('Н', 48120)
    	 5449 ('Минская Кольцевая АвтоДорога', 1809) ('Шиномонтаж', 716) ('Аптечная сеть, занимающаяся розничной торговлей товарами для красоты и здоровья', 312)
    	 6177 (('building',), 1427373) (('building', 'yes'), 1387895) (('addr:street',), 1203324)
    	 15697 (('building',), 1427373) (('building', 'yes'), 1387895) (('addr:street',), 1203324)
    	 34 ('н', 274) ('КН', 150) ('кн', 129)
    	 34 ('н', 53) ('н/ж', 53) ('к/ж', 49)
    	 278 (('building',), 884) (('building', 'yes'), 848) (('addr:street',), 751)
    	 143 (('building',), 258) (('building', 'yes'), 244) (('addr:street',), 196)
    addr:city description 1376453 5675 7 2
    	 503 ('Минск', 1097460) ('Гродно', 158490) ('Брест', 34575)
    	 1087 ('Минская Кольцевая АвтоДорога', 603) ('Птичь - Петриков - Житковичи', 129) ('Голоцк-Зазерье-Седча-Озеричино', 106)
    	 26302 (('addr:street',), 1319924) (('addr:housenumber',), 1288547) (('building',), 1000218)
    	 3276 (('addr:street',), 1319924) (('addr:housenumber',), 1288547) (('building',), 1000218)
    	 2 ('Снов', 6) ('Коробчицы', 1)
    	 2 ('Коробчицы', 1) ('Снов', 1)
    	 48 (('name',), 7) (('building',), 6) (('addr:street',), 6)
    	 12 (('note',), 1) (('map_size',), 1) (('map_type', 'street'), 1)
    name operator 1342987 277821 10640 9869
    	 3036 ('н', 841526) ('Н', 153564) ('к', 27820)
    	 6050 ('ГП "Столичный транспорт и связь"', 46992) ('КТУП «Гомельоблпассажиртранс»', 24975) ('ОАО "Гроднооблавтотранс"', 9252)
    	 22137 (('building',), 1204427) (('building', 'yes'), 966782) (('building', 'residential'), 185119)
    	 46199 (('building',), 1204427) (('building', 'yes'), 966782) (('building', 'residential'), 185119)
    	 893 ('Беларусбанк', 1045) ('Мила', 568) ('Белагропромбанк', 380)
    	 893 ('ОАО «Витебскоблавтотранс»', 819) ('Беларусбанк', 770) ('водоканал', 693)
    	 11231 (('opening_hours',), 4576) (('amenity',), 4132) (('shop',), 4002)
    	 12930 (('name',), 7018) (('amenity',), 4933) (('opening_hours',), 4725)
    addr:housename official_name 1324876 93915 1 4
    	 77 ('н', 1003632) ('Н', 231570) ('к', 43484)
    	 8337 ('Столбцы — Ивацевичи — Кобрин', 1212) ('Борисов — Вилейка — Ошмяны', 928) ('Витебск — Городок (до автомобильной дороги М-8)', 876)
    	 363 (('building',), 1322483) (('building', 'yes'), 1289489) (('addr:street',), 987258)
    	 18432 (('building',), 1322483) (('building', 'yes'), 1289489) (('addr:street',), 987258)
    	 1 ('Комплексный приёмный пункт', 1)
    	 1 ('Комплексный приёмный пункт', 4)
    	 4 (('addr:street',), 1) (('building',), 1) (('addr:street', 'Октябрьская улица'), 1)
    	 10 (('name', 'КПП'), 4) (('name',), 4) (('opening_hours',), 4)
    building ref 1293343 50784 190 60
    	 24 ('Н', 1277696) ('ТП', 8991) ('К', 2745)
    	 10285 ('М1', 2074) ('М6', 1261) ('М5', 1230)
    	 79 (('name',), 273312) (('name', 'Н'), 261888) (('building:levels',), 8127)
    	 13242 (('name',), 273312) (('name', 'Н'), 261888) (('building:levels',), 8127)
    	 12 ('Н', 161) ('ТП', 9) ('кн', 5)
    	 12 ('ТП', 27) ('кн', 12) ('КТП', 4)
    	 21 (('name',), 40) (('name', 'Н'), 33) (('addr:street',), 5)
    	 73 (('building',), 44) (('power', 'substation'), 33) (('power',), 33)
    description addr:street 313651 1283774 1 86
    	 43 ('н', 266378) ('улица', 41727) ('проезд', 3289)
    	 8196 ('Центральная улица', 61478) ('Молодёжная улица', 49743) ('Советская улица', 30251)
    	 216 (('building',), 268486) (('building', 'yes'), 268468) (('addr:street',), 258293)
    	 62462 (('building',), 268486) (('building', 'yes'), 268468) (('addr:street',), 258293)
    	 1 ('улица Коржа', 1)
    	 1 ('улица Коржа', 86)
    	 6 (('addr:street',), 1) (('building', 'yes'), 1) (('building',), 1)
    	 168 (('addr:housenumber',), 83) (('building',), 71) (('building:levels',), 46)
    addr:housenumber ref 1232617 53145 32578 1004
    	 196 ('Н', 952320) ('н', 54252) ('П', 32460)
    	 10595 ('М1', 2074) ('б/н', 1598) ('М6', 1261)
    	 13471 (('building',), 1212871) (('building', 'yes'), 1101921) (('addr:street',), 1083987)
    	 13261 (('building',), 1212871) (('building', 'yes'), 1101921) (('addr:street',), 1083987)
    	 89 ('1А', 3265) ('2А', 3210) ('3А', 1618)
    	 89 ('б/н', 799) ('ТП', 27) ('кн', 12)
    	 12104 (('building',), 31389) (('addr:street',), 31095) (('building', 'yes'), 18667)
    	 846 (('name',), 881) (('operator',), 837) (('fire_hydrant:type',), 799)
    official_short_type name 1186252 10350 884 628
    	 28 ('ВЛ', 507262) ('ТП', 434600) ('ПС', 118300)
    	 4986 ('ЦТП', 252) ('Минская Фармация', 236) ('ТП', 198)
    	 2434 (('power',), 1141833) (('voltage',), 1074308) (('ref',), 901889)
    	 8058 (('power',), 1141833) (('voltage',), 1074308) (('ref',), 901889)
    	 13 ('ТП', 410) ('ЗТП', 224) ('ЦТП', 111)
    	 13 ('ТП', 198) ('ЦТП', 126) ('ГРП', 93)
    	 983 (('ref',), 813) (('building',), 752) (('building', 'service'), 713)
    	 341 (('building',), 543) (('building', 'yes'), 304) (('building:levels',), 200)
    building addr:street 93610 1115826 1 1
    	 20 ('Н', 69713) ('н', 10052) ('р', 5998)
    	 8324 ('Центральная улица', 61478) ('Молодёжная улица', 33162) ('Советская улица', 30251)
    	 71 (('name',), 19741) (('name', 'Н'), 14289) (('addr:street',), 6472)
    	 58918 (('name',), 19741) (('name', 'Н'), 14289) (('addr:street',), 6472)
    	 1 ('Советская', 1)
    	 1 ('Советская', 1)
    	 4 (('addr:street',), 1) (('addr:housenumber',), 1) (('addr:street', 'Советская улица'), 1)
    	 6 (('surface', 'asphalt'), 1) (('surface',), 1) (('highway', 'tertiary'), 1)
    building name 1072272 421025 531 3737
    	 85 ('Н', 767004) ('н', 113814) ('р', 58019)
    	 90110 ('Центральная улица', 5298) ('Молодёжная улица', 3344) ('Беларусбанк', 2090)
    	 217 (('name',), 240368) (('name', 'Н'), 157212) (('addr:street',), 69940)
    	 150188 (('name',), 240368) (('name', 'Н'), 157212) (('addr:street',), 69940)
    	 74 ('Н', 161) ('КЖ', 130) ('КН', 104)
    	 74 ('Магазин', 534) ('Н', 382) ('КН', 369)
    	 202 (('name',), 205) (('building:levels',), 45) (('addr:street',), 40)
    	 1118 (('building',), 3049) (('building', 'yes'), 1918) (('building', 'residential'), 575)
    description wikipedia 1031128 25947 0 0
    	 39 ('н', 1025073) ('ж', 3254) ('Н', 1461)
    	 20407 ('be:Праспект Дзяржынскага (Мінск)', 202) ('be:Альхоўка (басейн Нёмана)', 76) ('be:Бярэзіна', 64)
    	 138 (('building',), 1030903) (('building', 'yes'), 1030881) (('addr:street',), 991828)
    	 52831 (('building',), 1030903) (('building', 'yes'), 1030881) (('addr:street',), 991828)
    	 0
    	 0
    	 0
    	 0
    operator addr:street 12022 1025437 2 1
    	 56 ('е', 6013) ('я', 3574) ('б', 930)
    	 8243 ('Центральная улица', 61478) ('Советская улица', 60502) ('Юбилейная улица', 21528)
    	 1327 (('name',), 8292) (('landuse',), 6022) (('name', 'Складской комплекс «Северный»'), 6013)
    	 54560 (('name',), 8292) (('landuse',), 6022) (('name', 'Складской комплекс «Северный»'), 6013)
    	 1 ('Родный кут', 2)
    	 1 ('Родный кут', 1)
    	 16 (('shop', 'convenience'), 2) (('name', 'Продуктовый магазин'), 2) (('shop',), 2)
    	 4 (('building', 'yes'), 1) (('building',), 1) (('addr:housenumber',), 1)
    addr:district wikipedia 1011146 3594 0 0
    	 139 ('Минский район', 99225) ('Буда-Кошелёвский район', 83367) ('Речицкий район', 57834)
    	 3094 ('ru:Дубица (Брестская область)', 6) ('ru:Костюковка (Гомельский район, деревня)', 4) ('ru:Секеричи (Петриковский район)', 4)
    	 86742 (('addr:region',), 1009306) (('addr:country',), 997173) (('addr:country', 'BY'), 992220)
    	 9097 (('addr:region',), 1009306) (('addr:country',), 997173) (('addr:country', 'BY'), 992220)
    	 0
    	 0
    	 0
    	 0
    addr:housename description 998590 49204 866 263
    	 129 ('н', 800574) ('Н', 111879) ('к', 27692)
    	 5805 ('Минская Кольцевая АвтоДорога', 4221) ('Шиномонтаж', 1790) ('Аптечная сеть, занимающаяся розничной торговлей товарами для красоты и здоровья', 624)
    	 474 (('building',), 996984) (('building', 'yes'), 971739) (('addr:street',), 734567)
    	 16519 (('building',), 996984) (('building', 'yes'), 971739) (('addr:street',), 734567)
    	 45 ('Н', 279) ('н', 174) ('кн', 99)
    	 45 ('н/ж', 53) ('н', 53) ('кн', 46)
    	 284 (('building',), 856) (('building', 'yes'), 829) (('addr:street',), 694)
    	 194 (('building',), 252) (('building', 'yes'), 216) (('addr:street',), 169)
    addr:housenumber operator 950112 60643 33 29
    	 67 ('н', 832412) ('Н', 48240) ('П', 34035)
    	 4944 ('ГП "Столичный транспорт и связь"', 15664) ('КТУП «Гомельоблпассажиртранс»', 4995) ('Минские кабельные сети', 1278)
    	 5146 (('building',), 948944) (('building', 'yes'), 913006) (('addr:street',), 799075)
    	 40342 (('building',), 948944) (('building', 'yes'), 913006) (('addr:street',), 799075)
    	 8 ('ТП', 23) ('Почта', 3) ('АТС', 2)
    	 8 ('жкх', 16) ('ТП', 6) ('Почта', 2)
    	 55 (('addr:street',), 29) (('building',), 27) (('building', 'yes'), 21)
    	 61 (('amenity',), 19) (('amenity', 'waste_disposal'), 12) (('building',), 7)
    fire_hydrant:city name 908121 2248 1922 124
    	 5 ('Минск', 866648) ('Речица', 40598) ('Микашевичи', 636)
    	 1050 ('Минская улица', 281) ('Минская Фармация', 236) ('Могилёвская улица', 81)
    	 1863 (('fire_hydrant:type',), 908121) (('emergency', 'fire_hydrant'), 908121) (('emergency',), 908121)
    	 3417 (('fire_hydrant:type',), 908121) (('emergency', 'fire_hydrant'), 908121) (('emergency',), 908121)
    	 5 ('Минск', 1016) ('Речица', 766) ('Микашевичи', 106)
    	 5 ('Речица', 56) ('Минск', 42) ('Микашевичи', 11)
    	 1863 (('fire_hydrant:type',), 1922) (('emergency', 'fire_hydrant'), 1922) (('emergency',), 1922)
    	 284 (('int_name',), 51) (('int_name', 'Rečyca'), 38) (('waterway',), 30)
    type addr:street 6488 743801 0 0
    	 4 ('ц', 6190) ('ель', 171) ('Дуб', 126)
    	 6279 ('Центральная улица', 30739) ('Советская улица', 30251) ('Молодёжная улица', 16581)
    	 11 (('natural',), 6488) (('natural', 'wetland'), 6190) (('natural', 'tree'), 298)
    	 57471 (('natural',), 6488) (('natural', 'wetland'), 6190) (('natural', 'tree'), 298)
    	 0
    	 0
    	 0
    	 0
    fixme addr:street 5995 727671 1 275
    	 4 ('улица', 5961) ('кв', 21) ('тип', 12)
    	 5964 ('Центральная улица', 30739) ('Советская улица', 30251) ('Молодёжная улица', 16581)
    	 49 (('building',), 5967) (('addr:housenumber',), 5965) (('addr:street',), 5964)
    	 56886 (('building',), 5967) (('addr:housenumber',), 5965) (('addr:street',), 5964)
    	 1 ('улица Плеханова', 1)
    	 1 ('улица Плеханова', 275)
    	 12 (('addr2:housenumber', '7'), 1) (('addr:housenumber', '14'), 1) (('addr2:street', 'улица Плеханова'), 1)
    	 361 (('addr:housenumber',), 261) (('building',), 253) (('addr:postcode',), 159)
    ref addr:street 44183 690600 71 193894
    	 93 ('М1', 24888) ('М', 3332) ('М5', 2460)
    	 5964 ('Советская улица', 60502) ('Молодёжная улица', 33162) ('Центральная улица', 30739)
    	 852 (('highway',), 31468) (('surface',), 31032) (('surface', 'asphalt'), 30975)
    	 46939 (('highway',), 31468) (('surface',), 31032) (('surface', 'asphalt'), 30975)
    	 50 ('Заводская улица', 4) ('Центральная улица', 4) ('Круговая улица', 3)
    	 50 ('Центральная улица', 30739) ('Советская улица', 30251) ('Садовая улица', 15276)
    	 120 (('highway',), 71) (('int_name',), 70) (('name',), 70)
    	 15042 (('building',), 191061) (('addr:housenumber',), 183790) (('building', 'yes'), 116422)
    addr:housename operator 686124 117304 27 2170
    	 86 ('н', 528612) ('Н', 112158) ('к', 19474)
    	 5820 ('ГП "Столичный транспорт и связь"', 11748) ('КТУП «Гомельоблпассажиртранс»', 9990) ('ОАО "Гроднооблавтотранс"', 4112)
    	 403 (('building',), 683718) (('building', 'yes'), 666660) (('addr:street',), 508649)
    	 45548 (('building',), 683718) (('building', 'yes'), 666660) (('addr:street',), 508649)
    	 16 ('Почта', 7) ('Белагропромбанк', 3) ('МЧС', 2)
    	 16 ('Беларусбанк', 770) ('водоканал', 693) ('Белагропромбанк', 456)
    	 102 (('addr:street',), 24) (('building',), 23) (('building', 'yes'), 22)
    	 2378 (('name',), 1606) (('amenity',), 1387) (('ref',), 869)
    name note 530900 22733 487 70
    	 1050 ('н', 366748) ('Н', 56918) ('п', 13209)
    	 1521 ('Не надо ставить эту камеру на линию дороги!', 792) ('Необходим тэг add:street или add:place', 512) ('маршрутам присвоены 3 рефа одновременно', 504)
    	 8719 (('building',), 497990) (('building', 'yes'), 412097) (('building', 'residential'), 64359)
    	 3644 (('building',), 497990) (('building', 'yes'), 412097) (('building', 'residential'), 64359)
    	 46 ('Котельная', 199) ('Автодром', 67) ('Гараж', 38)
    	 46 ('газон', 20) ('Беласток', 3) ('не работает', 2)
    	 641 (('building',), 222) (('power',), 107) (('building', 'industrial'), 105)
    	 259 (('name',), 38) (('operator',), 29) (('ref',), 22)
    official_short_type ref 511991 3262 652 107
    	 25 ('ТП', 409590) ('ВЛ', 72466) ('ЦТП', 16206)
    	 2142 ('ПНС', 60) ('ПГ-?К-100', 28) ('ТП', 27)
    	 2423 (('power',), 481360) (('ref',), 462277) (('voltage',), 425012)
    	 644 (('power',), 481360) (('ref',), 462277) (('voltage',), 425012)
    	 8 ('ТП', 410) ('ЦТП', 111) ('ГРП', 44)
    	 8 ('ПНС', 60) ('ТП', 27) ('ЦТП', 8)
    	 777 (('ref',), 589) (('building',), 531) (('building', 'service'), 508)
    	 113 (('substance',), 69) (('building',), 69) (('man_made', 'pumping_station'), 61)
    name addr:region 2250 436680 61 50898
    	 39 ('н', 1662) ('к', 130) ('М', 104)
    	 13 ('Минская область', 125163) ('Витебская область', 95392) ('Гродненская область', 77625)
    	 470 (('building',), 2041) (('building', 'yes'), 1839) (('building', 'residential'), 143)
    	 88131 (('building',), 2041) (('building', 'yes'), 1839) (('building', 'residential'), 143)
    	 12 ('Минск', 42) ('Могилёвская область', 3) ('Минская область', 3)
    	 12 ('Минская область', 13907) ('Витебская область', 11924) ('Гродненская область', 8625)
    	 219 (('admin_level',), 31) (('admin_level', '4'), 30) (('boundary', 'administrative'), 30)
    	 88127 (('addr:district',), 50357) (('addr:country',), 50065) (('addr:country', 'BY'), 49493)
    addr:housenumber note 418953 6909 11 3
    	 62 ('н', 362776) ('Н', 17880) ('ж', 13622)
    	 1451 ('Не надо ставить эту камеру на линию дороги!', 264) ('Уточнить обязательно название улицы, если неправильно то исправить!!!', 168) ('Имеются не идентифицированные узловые точки (до 10%)', 138)
    	 7054 (('building',), 418184) (('building', 'yes'), 403008) (('addr:street',), 354592)
    	 3539 (('building',), 418184) (('building', 'yes'), 403008) (('addr:street',), 354592)
    	 3 ('Котельная', 9) ('хлебозавод', 1) ('Гараж', 1)
    	 3 ('хлебозавод', 1) ('Котельная', 1) ('Гараж', 1)
    	 29 (('building',), 11) (('building', 'yes'), 11) (('addr:street',), 9)
    	 7 (('building',), 3) (('building', 'yes'), 2) (('building', 'factory'), 1)
    name addr:district 44869 381254 176 50511
    	 308 ('н', 38226) ('Н', 1910) ('к', 1430)
    	 144 ('Минский район', 31752) ('Поставский район', 8700) ('Воложинский район', 7632)
    	 2724 (('building',), 43069) (('building', 'yes'), 38373) (('building', 'residential'), 3826)
    	 87411 (('building',), 43069) (('building', 'yes'), 38373) (('building', 'residential'), 3826)
    	 142 ('Костюковка', 12) ('Октябрьский район', 10) ('Светлогорск', 6)
    	 142 ('Минский район', 3969) ('Браславский район', 1008) ('Поставский район', 870)
    	 922 (('wikidata',), 151) (('wikipedia',), 150) (('type',), 144)
    	 87168 (('addr:region',), 50399) (('addr:country',), 49875) (('addr:country', 'BY'), 49320)
    brand name 354659 11242 2894 7355
    	 159 ('Белоруснефть', 281112) ('Беларусбанк', 45486) ('Лукойл', 8930)
    	 1988 ('Беларусбанк', 1045) ('Евроопт Market', 750) ('Мила', 568)
    	 6860 (('amenity',), 345975) (('opening_hours',), 318378) (('name',), 278744)
    	 12304 (('amenity',), 345975) (('opening_hours',), 318378) (('name',), 278744)
    	 154 ('Белоруснефть', 884) ('Копеечка', 273) ('Беларусбанк', 266)
    	 154 ('Беларусбанк', 1045) ('Мила', 568) ('Белагропромбанк', 380)
    	 6836 (('name',), 2427) (('opening_hours',), 2315) (('operator',), 2037)
    	 7449 (('opening_hours',), 4276) (('operator',), 3888) (('shop',), 3725)
    fire_hydrant:street addr:street 4135 336731 124 34232
    	 150 ('Фрунзе', 434) ('Чапаева', 406) ('Набережная', 320)
    	 657 ('Центральная улица', 30739) ('Садовая улица', 30552) ('Советская улица', 30251)
    	 525 (('fire_hydrant:type',), 4135) (('fire_hydrant:diameter',), 4135) (('name',), 4135)
    	 25586 (('fire_hydrant:type',), 4135) (('fire_hydrant:diameter',), 4135) (('name',), 4135)
    	 27 ('Советская', 40) ('Набережная', 16) ('Пролетарская', 9)
    	 27 ('Садовая улица', 15276) ('Школьная улица', 11201) ('Озёрная улица', 3705)
    	 196 (('fire_hydrant:type',), 124) (('fire_hydrant:diameter',), 124) (('name',), 124)
    	 3391 (('building',), 33818) (('addr:housenumber',), 32351) (('building', 'yes'), 20471)
    name short_name 326306 13896 802 374
    	 2130 ('н', 195008) ('Н', 33234) ('Т', 32475)
    	 1798 ('СТ "Лесная Поляна"', 126) ('СТ "Строитель"', 78) ('СТ "Дружба"', 77)
    	 14021 (('building',), 292208) (('building', 'yes'), 218501) (('building', 'residential'), 61485)
    	 5463 (('building',), 292208) (('building', 'yes'), 218501) (('building', 'residential'), 61485)
    	 203 ('ФАП', 158) ('ЗАГС', 53) ('ФОК', 40)
    	 203 ('СТ "Строитель"', 13) ('СТ "Дружба"', 11) ('СТ "Медик"', 9)
    	 1005 (('building',), 304) (('amenity',), 300) (('building', 'yes'), 250)
    	 919 (('name',), 369) (('official_name',), 296) (('landuse',), 247)
    building wikipedia 320247 55815 0 0
    	 19 ('Н', 235221) ('н', 38682) ('р', 18826)
    	 25566 ('be:Праспект Дзяржынскага (Мінск)', 303) ('be:Бярэзіна', 128) ('be:Заходняя Дзвіна', 88)
    	 43 (('name',), 68622) (('name', 'Н'), 48213) (('building:levels',), 20308)
    	 67063 (('name',), 68622) (('name', 'Н'), 48213) (('building:levels',), 20308)
    	 0
    	 0
    	 0
    	 0
    description official_name 311876 26497 410 645
    	 202 ('н', 305704) ('ж', 1882) ('Садоводческое товарищество', 1203)
    	 7085 ('Столбцы — Ивацевичи — Кобрин', 303) ('Витебск — Городок (до автомобильной дороги М-8)', 292) ('Борисов — Вилейка — Ошмяны', 232)
    	 903 (('building',), 309223) (('building', 'yes'), 309101) (('addr:street',), 297269)
    	 16473 (('building',), 309223) (('building', 'yes'), 309101) (('addr:street',), 297269)
    	 116 ('Жодино - Дениски', 19) ('Ясеновка - Тихиничи - Ректа', 19) ('Новый Двор - Михановичи - Пятевщина', 18)
    	 116 ('Витебск — Городок (до автомобильной дороги М-8)', 146) ('Минск - Могилёв', 87) ('Юньки - Воропаево - Мерецкие', 34)
    	 355 (('highway',), 405) (('ref',), 399) (('highway', 'tertiary'), 317)
    	 359 (('highway',), 642) (('ref',), 636) (('surface',), 608)
    addr:city addr:street 306439 191236 126 17
    	 271 ('Минск', 225120) ('Брест', 23511) ('Полоцк', 8876)
    	 902 ('Центральная улица', 30739) ('Советская улица', 30251) ('Садовая улица', 15276)
    	 24773 (('addr:street',), 290060) (('addr:housenumber',), 281822) (('building',), 228592)
    	 18660 (('addr:street',), 290060) (('addr:housenumber',), 281822) (('building',), 228592)
    	 6 ('Бояры', 93) ('Новоселки', 28) ('Кирово', 2)
    	 6 ('Бояры', 8) ('Центральная', 4) ('Ворняны', 2)
    	 114 (('building',), 125) (('addr:housenumber',), 121) (('addr:street',), 103)
    	 50 (('building',), 9) (('addr:housenumber',), 9) (('addr:city',), 9)
    addr:street addr2:street 294047 792 272666 630
    	 270 ('Центральная улица', 30739) ('Молодёжная улица', 16581) ('Садовая улица', 15276)
    	 239 ('Октябрьская улица', 28) ('Молодёжная улица', 22) ('2-й переулок Дзержинского', 21)
    	 21786 (('building',), 289053) (('addr:housenumber',), 280558) (('building', 'yes'), 169857)
    	 490 (('building',), 289053) (('addr:housenumber',), 280558) (('building', 'yes'), 169857)
    	 239 ('Центральная улица', 30739) ('Молодёжная улица', 16581) ('Садовая улица', 15276)
    	 239 ('переулок Дзержинского', 19) ('улица Пушкина', 18) ('Октябрьская улица', 14)
    	 21173 (('building',), 268049) (('addr:housenumber',), 260174) (('building', 'yes'), 157012)
    	 490 (('addr:street',), 629) (('addr:housenumber',), 629) (('building',), 628)
    addr:housename note 291869 12082 6 2
    	 60 ('н', 230376) ('Н', 41571) ('к', 7084)
    	 1508 ('Не надо ставить эту камеру на линию дороги!', 792) ('Необходим тэг add:street или add:place', 384) ('маршрутам присвоены 3 рефа одновременно', 252)
    	 284 (('building',), 291274) (('building', 'yes'), 284118) (('addr:street',), 215536)
    	 3633 (('building',), 291274) (('building', 'yes'), 284118) (('addr:street',), 215536)
    	 2 ('Котельная', 5) ('нежилое', 1)
    	 2 ('Котельная', 1) ('нежилое', 1)
    	 23 (('addr:street',), 5) (('building',), 5) (('building', 'yes'), 4)
    	 20 (('source', 'survey'), 1) (('building',), 1) (('source',), 1)
    addr:city addr:place 265498 12795 10289 9546
    	 317 ('Минск', 187600) ('Гродно', 58700) ('Берёзовка', 1603)
    	 366 ('СТ "Малинники"', 815) ('Первомайский', 522) ('Огородники', 388)
    	 23715 (('addr:street',), 254133) (('addr:housenumber',), 250481) (('building',), 195242)
    	 1891 (('addr:street',), 254133) (('addr:housenumber',), 250481) (('building',), 195242)
    	 257 ('Берёзовка', 1603) ('Новосёлки', 572) ('Высокое', 378)
    	 257 ('Огородники', 388) ('Старое Село', 383) ('Королищевичи', 372)
    	 2996 (('building',), 9874) (('addr:housenumber',), 9156) (('addr:street',), 8043)
    	 1363 (('building',), 9242) (('addr:housenumber',), 9020) (('building', 'house'), 5054)
    addr:place name 265164 22819 32087 10926
    	 1056 ('Остров', 39312) ('Бор', 16284) ('Колядичи', 11966)
    	 5245 ('Зелёная улица', 733) ('Набережная улица', 597) ('Каменка', 367)
    	 2953 (('building',), 258275) (('addr:housenumber',), 256454) (('building', 'house'), 130499)
    	 18483 (('building',), 258275) (('addr:housenumber',), 256454) (('building', 'house'), 130499)
    	 1049 ('Ёдки', 409) ('Огородники', 388) ('Старое Село', 383)
    	 1049 ('Набережная улица', 597) ('Каменка', 367) ('Новосёлки', 261)
    	 2932 (('building',), 31069) (('addr:housenumber',), 30219) (('building', 'house'), 18560)
    	 10786 (('int_name',), 7450) (('place',), 7376) (('addr:region',), 6200)
    addr:city short_name 247556 444 416 38
    	 164 ('Гродно', 223060) ('Минск', 9380) ('Берёзовка', 1603)
    	 309 ('СТ "Лесная Поляна"', 14) ('СТ "Сосновый Бор"', 12) ('СТ "Дружба"', 11)
    	 22899 (('addr:street',), 243205) (('addr:housenumber',), 240551) (('building',), 195251)
    	 1159 (('addr:street',), 243205) (('addr:housenumber',), 240551) (('building',), 195251)
    	 16 ('СТ "Мелиоратор"', 94) ('СТ "Берёзка УВД"', 85) ('СТ "Энергетик-1"', 50)
    	 16 ('СТ "Колос"', 9) ('СТ "Мелиоратор"', 9) ('СТ "Энергетик-1"', 4)
    	 312 (('building',), 322) (('addr:housenumber',), 308) (('building', 'house'), 286)
    	 55 (('name',), 38) (('official_name',), 38) (('official_status', 'садоводческое товарищество'), 36)
    fire_hydrant:city wikipedia 245981 909 0 0
    	 4 ('Минск', 243840) ('Речица', 1532) ('Могилёв', 576)
    	 819 ('ru:Улица Есенина (Минск)', 22) ('ru:Улица Маяковского (Минск)', 12) ('ru:Красноармейская улица (Минск)', 7)
    	 1639 (('fire_hydrant:type',), 245981) (('emergency', 'fire_hydrant'), 245981) (('emergency',), 245981)
    	 3190 (('fire_hydrant:type',), 245981) (('emergency', 'fire_hydrant'), 245981) (('emergency',), 245981)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber addr:city 238825 80922 823 3
    	 22 ('н', 217008) ('Н', 9600) ('ж', 3920)
    	 1301 ('Минск', 18760) ('Гродно', 5870) ('Хойники', 2125)
    	 3431 (('building',), 238610) (('building', 'yes'), 232063) (('addr:street',), 201720)
    	 25190 (('building',), 238610) (('building', 'yes'), 232063) (('addr:street',), 201720)
    	 3 ('31А', 489) ('40А', 333) ('35а', 1)
    	 3 ('31А', 1) ('40А', 1) ('35а', 1)
    	 965 (('building',), 795) (('addr:street',), 783) (('building', 'yes'), 477)
    	 8 (('building',), 3) (('addr:street',), 2) (('building', 'yes'), 2)
    name inscription 237596 7699 1666 66
    	 663 ('н', 142101) ('Н', 39346) ('п', 6188)
    	 585 ('На этом месте 26 июня 1944 г. в жестокой схватке с фашистскими оккупантами был спасён от взрыва мост группой бойцов под командованием ст. сержанта Блохина Ф. Т., удостоенного за этот подвиг звания Героя Советского Союза.', 40) ('Стоматология', 36) ('Князев Василий Александрович. Герой Сов. Союза, лётчик-истребитель. Совершил 1088 боевых вылетов, сбил 29 самолётов. Уроженец ст. Княжица витебского р-на. Работал в локомотивном депо. Окончил Витебский аэроклуб.', 34)
    	 6196 (('building',), 221545) (('building', 'yes'), 172535) (('building', 'residential'), 37260)
    	 1313 (('building',), 221545) (('building', 'yes'), 172535) (('building', 'residential'), 37260)
    	 50 ('Продукты', 529) ('Ремонт обуви', 169) ('Шиномонтаж', 148)
    	 50 ('Стоматология', 6) ('Продукты', 5) ('Автозапчасти', 3)
    	 1551 (('shop',), 1259) (('opening_hours',), 498) (('shop', 'convenience'), 489)
    	 309 (('name',), 27) (('noname',), 27) (('noname', 'yes'), 27)
    addr:housenumber short_name 214641 2452 3 3
    	 25 ('н', 192896) ('Н', 10440) ('П', 5385)
    	 1211 ('СТ "Лесная Поляна"', 42) ('СТ "Дорожник"', 16) ('СТ "Ясная Поляна"', 15)
    	 223 (('building',), 214542) (('building', 'yes'), 208344) (('addr:street',), 180491)
    	 3889 (('building',), 214542) (('building', 'yes'), 208344) (('addr:street',), 180491)
    	 1 ('ФАП', 3)
    	 1 ('ФАП', 3)
    	 8 (('addr:street',), 3) (('building', 'yes'), 3) (('building',), 3)
    	 14 (('amenity', 'doctors'), 3) (('name',), 3) (('amenity',), 3)
    addr:city inscription 204499 177 140 3
    	 67 ('Минск', 150080) ('Гродно', 41090) ('Брест', 4149)
    	 139 ('В 1941-1942 гг. в г.Минске по ул. Советской, в доме №6, в помещении аптеки, находилась конспиративная квартира минских подпольщиков, которую содержал Г.Г. Фалевич / казнен фашистами в сентябре 1942 г. /', 3) ('Передан комсомольцам Витебска делегацией Брестской области на XII республиканском слёте участников похода по местам Славы Советского народа', 3) ('Этот Ленинский сквер заложен дружиной "Юные искровцы" при музее революционной боевой и трудовой славы Витебского завода имени С.М. Кирова. Саженцы получены от трудящихся и молодёжи Ленинграда', 3)
    	 22380 (('addr:street',), 197167) (('addr:housenumber',), 192972) (('building',), 148327)
    	 322 (('addr:street',), 197167) (('addr:housenumber',), 192972) (('building',), 148327)
    	 3 ('Гожа', 133) ('Бегомль', 5) ('Мир', 2)
    	 3 ('Бегомль', 1) ('Гожа', 1) ('Мир', 1)
    	 221 (('building',), 135) (('addr:street',), 134) (('addr:housenumber',), 134)
    	 20 (('information',), 2) (('tourism',), 2) (('tourism', 'information'), 2)
    addr:city note 204061 439 5 1
    	 92 ('Минск', 150080) ('Гродно', 35220) ('Гомель', 11720)
    	 218 ('Внешняя нода для согласования с картой Минска', 45) ('административная граница г. Минска', 28) ('Решение Брестский облсовет 256 10.03.2017 Об изменениях в административно-территориальном устройстве Лунинецкого района Брестской области', 26)
    	 21663 (('addr:street',), 196481) (('addr:housenumber',), 192817) (('building',), 147592)
    	 745 (('addr:street',), 196481) (('addr:housenumber',), 192817) (('building',), 147592)
    	 1 ('Мінск', 5)
    	 1 ('Мінск', 1)
    	 42 (('addr:street',), 5) (('addr:housenumber',), 5) (('addr:country',), 3)
    	 6 (('type', 'destination_sign'), 1) (('type',), 1) (('source', 'survey'), 1)
    addr:housename addr:region 1174 201444 0 0
    	 7 ('н', 1044) ('к', 91) ('а', 12)
    	 13 ('Минская область', 69535) ('Витебская область', 35772) ('Гродненская область', 34500)
    	 58 (('building',), 1174) (('building', 'yes'), 1138) (('addr:street',), 836)
    	 88131 (('building',), 1174) (('building', 'yes'), 1138) (('addr:street',), 836)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:diameter ref 191576 1213 0 0
    	 8 ('К-150', 187530) ('Т-100', 1564) ('К-110', 1510)
    	 663 ('ПГ-?К-100', 28) ('ПГ-4 К-100', 27) ('ПГ-1 К-100', 25)
    	 753 (('fire_hydrant:type',), 191576) (('name',), 191576) (('fire_operator',), 191576)
    	 24 (('fire_hydrant:type',), 191576) (('name',), 191576) (('fire_operator',), 191576)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr:district 26824 180824 0 0
    	 11 ('н', 24012) ('Н', 1395) ('к', 1001)
    	 144 ('Минский район', 15876) ('Поставский район', 3480) ('Воложинский район', 3392)
    	 88 (('building',), 26814) (('building', 'yes'), 26107) (('addr:street',), 19318)
    	 87411 (('building',), 26814) (('building', 'yes'), 26107) (('addr:street',), 19318)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city operator 173885 1934 0 0
    	 4 ('Минск', 167640) ('Речица', 6128) ('Микашевичи', 106)
    	 185 ('Минские кабельные сети', 426) ('Торгово-производственное республиканское унитарное предприятие "Минская Фармация"', 240) ('РУП "Белоруснефть-Минскавтозаправка"', 229)
    	 1844 (('fire_hydrant:type',), 173885) (('emergency', 'fire_hydrant'), 173885) (('emergency',), 173885)
    	 4321 (('fire_hydrant:type',), 173885) (('emergency', 'fire_hydrant'), 173885) (('emergency',), 173885)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber inscription 172086 2114 0 0
    	 31 ('н', 140562) ('ж', 12495) ('Н', 12360)
    	 566 ('На этом месте 26 июня 1944 г. в жестокой схватке с фашистскими оккупантами был спасён от взрыва мост группой бойцов под командованием ст. сержанта Блохина Ф. Т., удостоенного за этот подвиг звания Героя Советского Союза.', 12) ('Продукты', 10) ('Здесь 22 июня 1941 года, совершая таран фашистского истребителя, погиб экапиж бомбардировщика СБ-2М под командованием капитана Анатолия Протасова. Это - первый в истории Великой Отечественной Войны и мировой авиации таран истребителя бомбардировщиком.', 9)
    	 1738 (('building',), 171926) (('building', 'yes'), 167263) (('addr:street',), 144660)
    	 1233 (('building',), 171926) (('building', 'yes'), 167263) (('addr:street',), 144660)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr:city 169288 151007 5 3
    	 25 ('н', 137808) ('Н', 22320) ('к', 4900)
    	 1734 ('Минск', 28140) ('Гродно', 5870) ('Хойники', 4250)
    	 171 (('building',), 169064) (('building', 'yes'), 164709) (('addr:street',), 124396)
    	 29827 (('building',), 169064) (('building', 'yes'), 164709) (('addr:street',), 124396)
    	 3 ('ТАСК', 3) ('Садовая', 1) ('35а', 1)
    	 3 ('Садовая', 1) ('ТАСК', 1) ('35а', 1)
    	 18 (('name',), 4) (('office', 'insurance'), 3) (('office',), 3)
    	 14 (('building',), 2) (('building', 'house'), 2) (('building:levels',), 1)
    building official_name 165430 53152 0 0
    	 28 ('Н', 133630) ('н', 11536) ('р', 6142)
    	 7937 ('Столбцы — Ивацевичи — Кобрин', 909) ('Борисов — Вилейка — Ошмяны', 464) ('Витебск — Городок (до автомобильной дороги М-8)', 438)
    	 165 (('name',), 36402) (('name', 'Н'), 27390) (('addr:street',), 7721)
    	 17421 (('name',), 36402) (('name', 'Н'), 27390) (('addr:street',), 7721)
    	 0
    	 0
    	 0
    	 0
    description operator 163540 27585 48 52
    	 87 ('н', 161014) ('кн', 644) ('ж', 644)
    	 3485 ('ГП "Столичный транспорт и связь"', 3916) ('КТУП «Гомельоблпассажиртранс»', 3330) ('ОАО "Гроднооблавтотранс"', 1028)
    	 436 (('building',), 163194) (('building', 'yes'), 163038) (('addr:street',), 156834)
    	 32627 (('building',), 163194) (('building', 'yes'), 163038) (('addr:street',), 156834)
    	 19 ('Платная', 28) ('Барановичское райпо', 2) ('Верхнедвинское райпо', 2)
    	 19 ('ОАО "ДорОрс"', 12) ('Белнефтехим', 11) ('ОАО "Беларуськалий"', 10)
    	 106 (('amenity',), 31) (('fee', 'yes'), 28) (('fee',), 28)
    	 226 (('name',), 42) (('opening_hours',), 25) (('shop',), 22)
    name destination 159433 7137 3091 364
    	 414 ('н', 111631) ('Н', 21392) ('М', 4498)
    	 676 ('Мiнск', 267) ('Мінск', 156) ('Западная Двина', 135)
    	 3562 (('building',), 149279) (('building', 'yes'), 121377) (('building', 'residential'), 22762)
    	 1105 (('building',), 149279) (('building', 'yes'), 121377) (('building', 'residential'), 22762)
    	 149 ('Каменка', 367) ('Малиновка', 152) ('Березина', 124)
    	 149 ('Мінск', 39) ('Гомель', 32) ('Днепр', 21)
    	 2208 (('waterway',), 1752) (('waterway', 'river'), 1461) (('int_name',), 1408)
    	 714 (('type',), 203) (('name',), 179) (('type', 'waterway'), 177)
    addr:housenumber addr:place 156338 37036 0 0
    	 20 ('н', 143302) ('Н', 3960) ('2А', 3210)
    	 823 ('СТ "Малинники"', 1630) ('Минойты', 708) ('Малейковщизна', 702)
    	 3300 (('building',), 156167) (('building', 'yes'), 151490) (('addr:street',), 132149)
    	 2645 (('building',), 156167) (('building', 'yes'), 151490) (('addr:street',), 132149)
    	 0
    	 0
    	 0
    	 0
    addr:housename short_name 156151 4901 13 5
    	 31 ('н', 122496) ('Н', 24273) ('к', 4634)
    	 1623 ('СТ "Лесная Поляна"', 28) ('СТ "Мелиоратор"', 27) ('СТ "Монтажник"', 24)
    	 170 (('building',), 155847) (('building', 'yes'), 151904) (('addr:street',), 115580)
    	 4788 (('building',), 155847) (('building', 'yes'), 151904) (('addr:street',), 115580)
    	 2 ('ФАП', 12) ('СШ № 1', 1)
    	 2 ('ФАП', 3) ('СШ № 1', 2)
    	 28 (('addr:street',), 12) (('building',), 12) (('building', 'yes'), 12)
    	 28 (('name',), 5) (('amenity',), 5) (('amenity', 'doctors'), 3)
    operator addr:region 30 137781 0 0
    	 4 ('б', 12) ('я', 10) ('е', 7)
    	 12 ('Витебская область', 35772) ('Минская область', 27814) ('Гродненская область', 25875)
    	 18 (('amenity', 'atm'), 22) (('amenity',), 22) (('name',), 20)
    	 88118 (('amenity', 'atm'), 22) (('amenity',), 22) (('name',), 20)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city official_name 137333 957 0 0
    	 4 ('Минск', 127000) ('Речица', 9958) ('Микашевичи', 318)
    	 195 ('Минск - Могилёв', 174) ('Могилёв — Славгород', 116) ('Минск — Калачи — Мядель', 98)
    	 1844 (('fire_hydrant:type',), 137333) (('emergency', 'fire_hydrant'), 137333) (('emergency',), 137333)
    	 944 (('fire_hydrant:type',), 137333) (('emergency', 'fire_hydrant'), 137333) (('emergency',), 137333)
    	 0
    	 0
    	 0
    	 0
    addr:city ref 136875 144 1 1
    	 64 ('Минск', 75040) ('Гродно', 41090) ('Брест', 8298)
    	 99 ('Первомайский переулок', 4) ('Центральная поликлиника', 4) ('Центральная улица', 4)
    	 22697 (('addr:street',), 132776) (('addr:housenumber',), 129919) (('building',), 101815)
    	 320 (('addr:street',), 132776) (('addr:housenumber',), 129919) (('building',), 101815)
    	 1 ('40А', 1)
    	 1 ('40А', 1)
    	 6 (('addr:street',), 1) (('name', 'Уют'), 1) (('building', 'yes'), 1)
    	 4 (('name', 'Боровка'), 1) (('man_made', 'water_works'), 1) (('man_made',), 1)
    addr:housename inscription 130314 3313 1 1
    	 40 ('н', 89262) ('Н', 28737) ('ж', 5100)
    	 583 ('Стоматология', 18) ('На этом месте 26 июня 1944 г. в жестокой схватке с фашистскими оккупантами был спасён от взрыва мост группой бойцов под командованием ст. сержанта Блохина Ф. Т., удостоенного за этот подвиг звания Героя Советского Союза.', 14) ('Дерево посажено Народным артистом БССР Смольским Дмитрием Борисовичем и Филиалом №529 "Белсвязь" ОАО "АСБ Беларусбанк" 2017', 10)
    	 240 (('building',), 129975) (('building', 'yes'), 127053) (('addr:street',), 99169)
    	 1300 (('building',), 129975) (('building', 'yes'), 127053) (('addr:street',), 99169)
    	 1 ('Ремонт обуви', 1)
    	 1 ('Ремонт обуви', 1)
    	 6 (('addr:street',), 1) (('building', 'yes'), 1) (('addr:housenumber', '40'), 1)
    	 8 (('noname',), 1) (('craft', 'shoemaker'), 1) (('level',), 1)
    name addr:subdistrict 125655 79259 865 9853
    	 1155 ('н', 89194) ('Н', 9932) ('к', 7650)
    	 767 ('Кобринский р-н', 3804) ('Михалишковский сельский Совет', 963) ('Октябрьский сельский Совет', 891)
    	 6304 (('building',), 117037) (('building', 'yes'), 100275) (('building', 'residential'), 13665)
    	 24833 (('building',), 117037) (('building', 'yes'), 100275) (('building', 'residential'), 13665)
    	 740 ('Костюковка', 12) ('Октябрьский сельский Совет', 7) ('Каменский сельский Совет', 6)
    	 740 ('Михалишковский сельский Совет', 107) ('Василишковский сельский Совет', 103) ('Рытанский сельский Совет', 83)
    	 2643 (('admin_level',), 847) (('type',), 846) (('admin_level', '8'), 846)
    	 24209 (('name',), 9832) (('place',), 9820) (('addr:district',), 9819)
    addr:housenumber destination 122077 2550 0 0
    	 16 ('н', 110422) ('Н', 6720) ('ж', 2695)
    	 581 ('Мiнск', 178) ('Мінск', 78) ('Брэст', 45)
    	 160 (('building',), 122021) (('building', 'yes'), 119519) (('addr:street',), 102976)
    	 908 (('building',), 122021) (('building', 'yes'), 119519) (('addr:street',), 102976)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city description 118877 795 0 0
    	 2 ('Минск', 118872) ('Могилёв', 5)
    	 121 ('Минская Кольцевая АвтоДорога', 603) ('Рогачев - Поболово (до а/д Минск - Гомель)', 19) ('подъезд к Могилёву', 13)
    	 1136 (('fire_hydrant:type',), 118877) (('emergency', 'fire_hydrant'), 118877) (('emergency',), 118877)
    	 984 (('fire_hydrant:type',), 118877) (('emergency', 'fire_hydrant'), 118877) (('emergency',), 118877)
    	 0
    	 0
    	 0
    	 0
    building addr:district 1324 116388 0 0
    	 7 ('Н', 805) ('н', 276) ('р', 142)
    	 144 ('Минский район', 11907) ('Миорский район', 2463) ('Гродненский район', 2208)
    	 22 (('name',), 239) (('name', 'Н'), 165) (('building:levels',), 147)
    	 87411 (('name',), 239) (('name', 'Н'), 165) (('building:levels',), 147)
    	 0
    	 0
    	 0
    	 0
    name minsk_PT:note 2477 109596 0 0
    	 18 ('Н', 1146) ('н', 831) ('Минск', 126)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 106658) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 1818) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 1120)
    	 174 (('building',), 2307) (('building', 'yes'), 1315) (('building', 'residential'), 843)
    	 4600 (('building',), 2307) (('building', 'yes'), 1315) (('building', 'residential'), 843)
    	 0
    	 0
    	 0
    	 0
    official_short_type official_name 107411 657 224 1
    	 10 ('ВЛ', 62931) ('ПС', 33488) ('Ф', 5856)
    	 321 ('Витебск — Сураж — граница Российской Федерации (Стайки)', 65) ('Подъезд к гр.РП(Берестовица) от а/д Барановичи-Волковыск-Пограничный-Гродно', 31) ('Фаниполь - Черкассы', 14)
    	 2236 (('power',), 106934) (('voltage',), 105436) (('cables',), 68424)
    	 1308 (('power',), 106934) (('voltage',), 105436) (('cables',), 68424)
    	 1 ('ЗТП', 224)
    	 1 ('ЗТП', 1)
    	 334 (('building',), 220) (('ref',), 216) (('power',), 211)
    	 6 (('ref', '3'), 1) (('power',), 1) (('building',), 1)
    was:name:prefix official_name 106766 427 0 0
    	 4 ('деревня', 104528) ('хутор', 1743) ('посёлок', 390)
    	 236 ('Соколовичи - Чернявка - станция Бобр', 8) ('деревня Дубровка', 6) ('деревня Октябрьское', 4)
    	 3050 (('name',), 106766) (('place',), 106766) (('int_name:prefix',), 104932)
    	 1028 (('name',), 106766) (('place',), 106766) (('int_name:prefix',), 104932)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr:place 106608 68259 1 1
    	 24 ('н', 91002) ('Н', 9207) ('к', 3528)
    	 1051 ('СТ "Малинники"', 3260) ('Малейковщизна', 1404) ('СТ "Шарик"', 1268)
    	 171 (('building',), 106502) (('building', 'yes'), 103773) (('addr:street',), 77444)
    	 3113 (('building',), 106502) (('building', 'yes'), 103773) (('addr:street',), 77444)
    	 1 ('СТО "Кола"', 1)
    	 1 ('СТО "Кола"', 1)
    	 4 (('building',), 1) (('addr:place', 'СТО "Кола"'), 1) (('addr:place',), 1)
    	 4 (('building',), 1) (('addr:housename', 'СТО "Кола"'), 1) (('building', 'manufacture'), 1)
    type name 26678 106281 3 13
    	 5 ('ц', 20289) ('ель', 4983) ('Дуб', 1398)
    	 24739 ('Центральная улица', 2649) ('Советская улица', 1990) ('Молодёжная улица', 1672)
    	 11 (('natural',), 26678) (('natural', 'wetland'), 20289) (('natural', 'tree'), 6389)
    	 45107 (('natural',), 26678) (('natural', 'wetland'), 20289) (('natural', 'tree'), 6389)
    	 1 ('Дуб', 3)
    	 1 ('Дуб', 13)
    	 2 (('natural',), 3) (('natural', 'tree'), 3)
    	 15 (('natural',), 13) (('natural', 'tree'), 13) (('leaf_type',), 4)
    building addr:city 16403 106143 0 0
    	 12 ('Н', 12880) ('н', 1584) ('р', 737)
    	 1433 ('Минск', 18760) ('Гродно', 17610) ('Колодищи', 3727)
    	 33 (('name',), 3551) (('name', 'Н'), 2640) (('building:levels',), 819)
    	 26844 (('name',), 3551) (('name', 'Н'), 2640) (('building:levels',), 819)
    	 0
    	 0
    	 0
    	 0
    addr:place official_name 101780 9622 53 25
    	 450 ('Остров', 10512) ('Слобода', 7954) ('Селец', 7378)
    	 1868 ('Борисов — Вилейка — Ошмяны', 232) ('Буда-Кошелево — Уваровичи — Калинино', 144) ('Кривое Село - Вороничи - Любовши - Красный Берег', 86)
    	 1564 (('building',), 98706) (('addr:housenumber',), 98545) (('building', 'house'), 52987)
    	 3285 (('building',), 98706) (('addr:housenumber',), 98545) (('building', 'house'), 52987)
    	 13 ('Адамовичи', 41) ('деревня Белеи', 1) ('деревня Волково', 1)
    	 13 ('деревня Белеи', 2) ('деревня Волково', 2) ('деревня Двуполяны', 2)
    	 100 (('addr:housenumber',), 43) (('building',), 42) (('building', 'house'), 31)
    	 92 (('name',), 25) (('wikidata',), 22) (('official_status', 'ru:деревня'), 22)
    addr:city addr:full 99493 72 0 0
    	 32 ('Минск', 84420) ('Гродно', 11740) ('Брест', 1383)
    	 32 ('д. Яново, Борисовский район, Минская область', 12) ('пересечение а/д М-3 Минск-Витебск и Р111 Бешенковичи-Чашники', 8) ('44 км а/д Минск-Витебск', 4)
    	 21072 (('addr:street',), 95779) (('addr:housenumber',), 93679) (('building',), 71007)
    	 269 (('addr:street',), 95779) (('addr:housenumber',), 93679) (('building',), 71007)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr:housenumber 47343 98306 991 19952
    	 117 ('к', 18914) ('Н', 11997) ('н', 11832)
    	 3890 ('1А', 6530) ('2А', 6420) ('11А', 3432)
    	 377 (('building',), 46207) (('building', 'yes'), 44814) (('addr:street',), 41532)
    	 18289 (('building',), 46207) (('building', 'yes'), 44814) (('addr:street',), 41532)
    	 92 ('Н', 279) ('н', 174) ('кн', 99)
    	 92 ('1А', 3265) ('2А', 3210) ('3А', 1618)
    	 344 (('building',), 980) (('building', 'yes'), 932) (('addr:street',), 786)
    	 8862 (('building',), 19297) (('addr:street',), 18943) (('building', 'yes'), 11818)
    ref wikipedia 96768 48067 0 0
    	 37 ('В', 32144) ('М', 15788) ('М1', 10370)
    	 26153 ('be:Праспект Дзяржынскага (Мінск)', 303) ('ru:Магистраль М12 (Белоруссия)', 156) ('be:Сож', 102)
    	 867 (('aeroway',), 30218) (('aeroway', 'taxiway'), 30198) (('name',), 26759)
    	 69038 (('aeroway',), 30218) (('aeroway', 'taxiway'), 30198) (('name',), 26759)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber addr:subdistrict 94586 9105 0 0
    	 14 ('н', 88228) ('Н', 3120) ('ж', 1960)
    	 475 ('Кобринский р-н', 634) ('Рытанский сельский Совет', 166) ('Ворнянский сельский Совет', 162)
    	 154 (('building',), 94560) (('building', 'yes'), 92634) (('addr:street',), 79626)
    	 17023 (('building',), 94560) (('building', 'yes'), 92634) (('addr:street',), 79626)
    	 0
    	 0
    	 0
    	 0
    name fixme 94379 4115 75 2
    	 168 ('н', 69527) ('Н', 9550) ('п', 2754)
    	 307 ('адрес', 211) ('расположение', 180) ('положение/адрес', 170)
    	 1711 (('building',), 91259) (('building', 'yes'), 76449) (('building', 'residential'), 11325)
    	 1787 (('building',), 91259) (('building', 'yes'), 76449) (('building', 'residential'), 11325)
    	 2 ('Мастерские', 48) ('улица Плеханова', 27)
    	 2 ('Мастерские', 1) ('улица Плеханова', 1)
    	 68 (('building',), 34) (('highway',), 30) (('int_name',), 27)
    	 12 (('addr2:housenumber', '7'), 1) (('addr:housenumber', '14'), 1) (('addr2:street', 'улица Плеханова'), 1)
    addr:housenumber addr:region 1673 94087 0 0
    	 4 ('н', 1644) ('П', 15) ('я', 10)
    	 12 ('Минская область', 41721) ('Гродненская область', 17250) ('Могилёвская область', 12178)
    	 85 (('building',), 1673) (('building', 'yes'), 1631) (('addr:street',), 1411)
    	 88126 (('building',), 1673) (('building', 'yes'), 1631) (('addr:street',), 1411)
    	 0
    	 0
    	 0
    	 0
    addr:housename destination 91286 4021 0 0
    	 17 ('н', 70122) ('Н', 15624) ('к', 2632)
    	 658 ('Мiнск', 267) ('Мінск', 117) ('40-ы кіламетр МКАД;Нарач;Гродна;Вільнюс;Брэст', 54)
    	 105 (('building',), 91099) (('building', 'yes'), 88769) (('addr:street',), 67757)
    	 1034 (('building',), 91099) (('building', 'yes'), 88769) (('addr:street',), 67757)
    	 0
    	 0
    	 0
    	 0
    building description 87616 25078 316 133
    	 50 ('Н', 64561) ('н', 9202) ('р', 4474)
    	 5596 ('Минская Кольцевая АвтоДорога', 2412) ('Шиномонтаж', 358) ('ARMTEK занимается оптовой и розничной торговлей автозапчастями, расходными материалами и аксессуарами для легковых и грузовых автомобилей', 213)
    	 106 (('name',), 18764) (('name', 'Н'), 13233) (('addr:street',), 5787)
    	 16192 (('name',), 18764) (('name', 'Н'), 13233) (('addr:street',), 5787)
    	 19 ('Н', 161) ('КН', 104) ('фундамент', 17)
    	 19 ('н', 53) ('кн', 46) ('кж', 7)
    	 50 (('name',), 63) (('name', 'Н'), 33) (('name', 'КН'), 16)
    	 62 (('building',), 130) (('building', 'yes'), 125) (('addr:street',), 110)
    addr:street old_addr 87132 68 0 0
    	 4 ('улица Энгельса', 52184) ('улица Победы', 18846) ('улица Ломоносова', 15585)
    	 66 ('улица Энгельса, 49А', 2) ('улица Энгельса, 100', 2) ('улица Победы, 15', 1)
    	 1581 (('building',), 85438) (('addr:housenumber',), 83806) (('building', 'yes'), 60047)
    	 155 (('building',), 85438) (('addr:housenumber',), 83806) (('building', 'yes'), 60047)
    	 0
    	 0
    	 0
    	 0
    from addr:street 1245 85648 58 23698
    	 78 ('Гомель', 360) ('Вокзал', 352) ('Минск', 72)
    	 255 ('Советская улица', 30251) ('Молодёжная улица', 16581) ('Солнечная улица', 5425)
    	 655 (('to',), 1245) (('route',), 1245) (('type',), 1245)
    	 12091 (('to',), 1245) (('route',), 1245) (('type',), 1245)
    	 22 ('Автовокзал', 11) ('Молодёжная улица', 8) ('улица Белые Росы', 5)
    	 22 ('Молодёжная улица', 16581) ('улица Победы', 3141) ('улица Крупской', 1361)
    	 179 (('to',), 58) (('route',), 58) (('public_transport:version', '2'), 58)
    	 4176 (('building',), 23221) (('addr:housenumber',), 22768) (('building', 'yes'), 12646)
    building operator 85264 69272 16 30
    	 37 ('Н', 64722) ('н', 6076) ('р', 3552)
    	 5335 ('ГП "Столичный транспорт и связь"', 11748) ('КТУП «Гомельоблпассажиртранс»', 6660) ('ОАО "Гроднооблавтотранс"', 3084)
    	 176 (('name',), 19578) (('name', 'Н'), 13266) (('addr:street',), 4634)
    	 41979 (('name',), 19578) (('name', 'Н'), 13266) (('addr:street',), 4634)
    	 7 ('ТП', 9) ('МЧС', 2) ('дом', 1)
    	 7 ('МЧС', 7) ('РАЙПО', 6) ('ТП', 6)
    	 15 (('addr:street',), 7) (('addr:housenumber',), 2) (('building:levels',), 1)
    	 104 (('building',), 19) (('name',), 17) (('building', 'yes'), 16)
    addr:housenumber fixme 81399 1354 0 0
    	 24 ('н', 68774) ('ж', 5488) ('2А', 3210)
    	 278 ('положение', 78) ('расположение', 72) ('положение/адрес', 68)
    	 2908 (('building',), 81249) (('building', 'yes'), 78636) (('addr:street',), 68727)
    	 1570 (('building',), 81249) (('building', 'yes'), 78636) (('addr:street',), 68727)
    	 0
    	 0
    	 0
    	 0
    name to 77934 4527 5052 601
    	 578 ('н', 52353) ('Н', 4584) ('к', 1680)
    	 375 ('Вокзал', 210) ('ДС Малиновка-4', 128) ('Автовокзал', 104)
    	 5222 (('building',), 65385) (('building', 'yes'), 55972) (('building', 'residential'), 7327)
    	 1651 (('building',), 65385) (('building', 'yes'), 55972) (('building', 'residential'), 7327)
    	 269 ('Молодёжная улица', 1672) ('улица Победы', 311) ('Евроопт', 167)
    	 269 ('Вокзал', 42) ('Гомель', 34) ('Фолюш', 13)
    	 2915 (('highway',), 2960) (('int_name',), 2728) (('highway', 'residential'), 1650)
    	 1284 (('route',), 600) (('name',), 600) (('type',), 599)
    name from 76185 4561 5294 596
    	 582 ('н', 51245) ('Н', 3438) ('к', 1720)
    	 368 ('Вокзал', 220) ('ДС Малиновка-4', 120) ('Гомель', 108)
    	 5456 (('building',), 63476) (('building', 'yes'), 54916) (('building', 'residential'), 6546)
    	 1636 (('building',), 63476) (('building', 'yes'), 54916) (('building', 'residential'), 6546)
    	 259 ('Молодёжная улица', 1672) ('улица Победы', 311) ('Белинвестбанк', 222)
    	 259 ('Вокзал', 44) ('Гомель', 36) ('Фолюш', 13)
    	 3149 (('highway',), 2950) (('int_name',), 2904) (('highway', 'residential'), 1650)
    	 1289 (('name',), 595) (('to',), 594) (('type',), 594)
    addr:city full_name 75834 26 0 0
    	 15 ('Гродно', 64570) ('Минск', 9380) ('Брест', 1383)
    	 24 ('Жилищное ремонтно-эксплуатационное объединение Советского района г.Минска', 2) ('Погранзастава №1 имени Героя Советского Союза лейтенанта В. Усова', 2) ('Государственное предприятие "АгроСолы"', 1)
    	 19543 (('addr:street',), 74787) (('addr:housenumber',), 73780) (('building',), 59303)
    	 208 (('addr:street',), 74787) (('addr:housenumber',), 73780) (('building',), 59303)
    	 0
    	 0
    	 0
    	 0
    designation addr:street 950 75521 0 0
    	 9 ('б', 930) ('Тополь', 4) ('парк', 4)
    	 947 ('Октябрьская улица', 10398) ('Юбилейная улица', 7176) ('Набережная улица', 6128)
    	 57 (('name',), 946) (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 930) (('addr:street',), 930)
    	 11657 (('name',), 946) (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 930) (('addr:street',), 930)
    	 0
    	 0
    	 0
    	 0
    name addr2:street 74297 4152 26069 630
    	 494 ('н', 33240) ('Н', 4966) ('Центральная улица', 2649)
    	 240 ('улица Пушкина', 162) ('переулок Дзержинского', 152) ('Октябрьская улица', 140)
    	 6029 (('building',), 43360) (('building', 'yes'), 36397) (('highway',), 28379)
    	 498 (('building',), 43360) (('building', 'yes'), 36397) (('highway',), 28379)
    	 239 ('Центральная улица', 2649) ('Молодёжная улица', 1672) ('Садовая улица', 1552)
    	 239 ('переулок Дзержинского', 19) ('улица Пушкина', 18) ('Октябрьская улица', 14)
    	 4359 (('highway',), 25412) (('int_name',), 20513) (('highway', 'residential'), 16947)
    	 490 (('addr:street',), 629) (('addr:housenumber',), 629) (('building',), 628)
    addr:housenumber addr:district 38976 72533 0 0
    	 11 ('н', 37812) ('Н', 600) ('ж', 392)
    	 142 ('Минский район', 7938) ('Мядельский район', 1863) ('Поставский район', 1740)
    	 153 (('building',), 38971) (('building', 'yes'), 38341) (('addr:street',), 32848)
    	 87394 (('building',), 38971) (('building', 'yes'), 38341) (('addr:street',), 32848)
    	 0
    	 0
    	 0
    	 0
    official_name addr:street 136 71900 58 9265
    	 15 ('Центр', 42) ('Центральная', 36) ('Дубовляны — Боровляны — Королев Стан', 16)
    	 36 ('Центральная улица', 61478) ('Юбилейная улица', 7176) ('улица Володарского', 1856)
    	 120 (('highway',), 93) (('ref',), 82) (('surface',), 77)
    	 3569 (('highway',), 93) (('ref',), 82) (('surface',), 77)
    	 13 ('Дубовляны — Боровляны — Королев Стан', 16) ('Новый Двор — Михановичи — Пятевщина', 11) ('Асеевка — Михановичи', 6)
    	 13 ('Юбилейная улица', 7176) ('улица Володарского', 1856) ('улица Антонова', 100)
    	 100 (('highway',), 58) (('ref',), 49) (('surface',), 44)
    	 1548 (('building',), 9139) (('addr:housenumber',), 8886) (('building', 'yes'), 5945)
    description note 71737 3776 60 81
    	 97 ('н', 70172) ('ж', 556) ('Н', 149)
    	 1370 ('Не надо ставить эту камеру на линию дороги!', 264) ('На синем фоне', 171) ('Необходим тэг add:street или add:place', 128)
    	 451 (('building',), 71329) (('building', 'yes'), 71258) (('addr:street',), 68469)
    	 3353 (('building',), 71329) (('building', 'yes'), 71258) (('addr:street',), 68469)
    	 18 ('Скорее_твердая:_без_покрытия,_гравий,_хорошо_укатанный_грунт,_песок', 15) ('На синем фоне', 8) ('Котельная', 8)
    	 18 ('На синем фоне', 57) ('Знак на синем фоне', 4) ('АТМ Беларусбанк (BYR)', 2)
    	 172 (('highway',), 26) (('surface',), 25) (('width',), 20)
    	 116 (('name',), 65) (('traffic_sign', 'city_limit'), 62) (('traffic_sign',), 62)
    addr:housename addr:subdistrict 70866 32876 0 0
    	 17 ('н', 56028) ('Н', 7254) ('к', 5355)
    	 766 ('Кобринский р-н', 1902) ('Михалишковский сельский Совет', 428) ('Рожанковский сельский Совет', 350)
    	 100 (('building',), 70806) (('building', 'yes'), 69196) (('addr:street',), 52217)
    	 24826 (('building',), 70806) (('building', 'yes'), 69196) (('addr:street',), 52217)
    	 0
    	 0
    	 0
    	 0
    addr:place wikipedia 70422 2192 0 0
    	 365 ('Красная', 6363) ('Новосёлки', 5481) ('Бор', 5198)
    	 1825 ('be:Прудок (ручай)', 16) ('be:Каменка (прыток Усысы)', 12) ('be:Чарніца (прыток Будавесці)', 10)
    	 1391 (('building',), 68743) (('addr:housenumber',), 68449) (('building', 'house'), 38480)
    	 5071 (('building',), 68743) (('addr:housenumber',), 68449) (('building', 'house'), 38480)
    	 0
    	 0
    	 0
    	 0
    building addr:region 33 65023 0 0
    	 5 ('н', 12) ('М', 8) ('дн', 7)
    	 10 ('Минская область', 27814) ('Гродненская область', 25875) ('Могилёвская область', 6089)
    	 17 (('name',), 12) (('name', 'М'), 8) (('addr:street',), 5)
    	 58671 (('name',), 12) (('name', 'М'), 8) (('addr:street',), 5)
    	 0
    	 0
    	 0
    	 0
    addr:unit addr:housenumber 1599 63584 4 1477
    	 6 ('А', 1028) ('Б', 457) ('5А', 86)
    	 1500 ('1А', 3265) ('2А', 3210) ('5А', 2896)
    	 45 (('addr:street',), 1488) (('addr:housenumber',), 1488) (('addr:city',), 1488)
    	 17597 (('addr:street',), 1488) (('addr:housenumber',), 1488) (('addr:city',), 1488)
    	 4 ('3Н', 1) ('89Г', 1) ('5А', 1)
    	 4 ('5А', 1448) ('1 к3', 25) ('89Г', 3)
    	 29 (('name',), 2) (('operator',), 2) (('building',), 2)
    	 1620 (('building',), 1424) (('addr:street',), 1402) (('building', 'yes'), 851)
    official_short_type operator 62760 2353 411 7
    	 14 ('ТП', 32390) ('ПС', 12012) ('Ф', 10304)
    	 503 ('КУПП "Боровка"', 296) ('Торгово-производственное республиканское унитарное предприятие "Минская Фармация"', 240) ('БПС-Сбербанк', 188)
    	 2217 (('power',), 61608) (('voltage',), 56900) (('ref',), 46658)
    	 4501 (('power',), 61608) (('voltage',), 56900) (('ref',), 46658)
    	 2 ('ТП', 410) ('АТС', 1)
    	 2 ('ТП', 6) ('АТС', 1)
    	 520 (('power',), 399) (('power', 'substation'), 399) (('ref',), 387)
    	 13 (('power',), 6) (('building',), 6) (('power', 'substation'), 6)
    ref operator 21783 59925 41 591
    	 55 ('М', 3728) ('ТП', 2133) ('Т', 2120)
    	 5341 ('ГП "Столичный транспорт и связь"', 7832) ('КТУП «Гомельоблпассажиртранс»', 4995) ('ОАО "Гроднооблавтотранс"', 2056)
    	 638 (('aeroway', 'taxiway'), 6977) (('aeroway',), 6977) (('name',), 4445)
    	 42491 (('aeroway', 'taxiway'), 6977) (('aeroway',), 6977) (('name',), 4445)
    	 11 ('ТП', 27) ('АЗС 22', 3) ('Почта', 2)
    	 11 ('КУПП "Боровка"', 296) ('Белпочта', 197) ('Белтелеком', 53)
    	 162 (('power',), 29) (('building',), 29) (('power', 'substation'), 28)
    	 817 (('power',), 304) (('power', 'pole'), 291) (('amenity',), 236)
    ref addr:place 59297 32578 200 1
    	 48 ('М1', 29036) ('М6', 13871) ('М4', 3556)
    	 754 ('СТ "Малинники"', 3260) ('СТ "Шарик"', 1902) ('СТ "Электрик"', 873)
    	 943 (('highway',), 57590) (('surface',), 57309) (('surface', 'asphalt'), 56849)
    	 2324 (('highway',), 57590) (('surface',), 57309) (('surface', 'asphalt'), 56849)
    	 1 ('Р45', 200)
    	 1 ('Р45', 1)
    	 133 (('surface',), 199) (('surface', 'asphalt'), 199) (('highway', 'primary'), 199)
    	 4 (('addr:city',), 1) (('addr:city', 'Катлоўка'), 1) (('building',), 1)
    name source 25828 59291 631 123
    	 92 ('н', 13850) ('Н', 7258) ('Беларусбанк', 1045)
    	 77 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 25788) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 13224) ('Национальное кадастровое агентство nca.by', 9846)
    	 1777 (('building',), 24277) (('building', 'yes'), 16971) (('building', 'residential'), 5468)
    	 1157 (('building',), 24277) (('building', 'yes'), 16971) (('building', 'residential'), 5468)
    	 9 ('Магазин', 534) ('Ремонт одежды', 88) ('Автотракмоторс', 3)
    	 9 ('Национальное кадастровое агентство', 115) ('Магазин', 1) ('Ремонт одежды', 1)
    	 496 (('shop',), 416) (('building',), 349) (('shop', 'convenience'), 325)
    	 129 (('addr:housenumber',), 117) (('building',), 116) (('building', 'yes'), 115)
    addr:province addr:region 38 56398 7 30437
    	 7 ('Брянская', 24) ('Минская', 4) ('Витебская', 3)
    	 5 ('Минская область', 27814) ('Витебская область', 23848) ('Брестская область', 4563)
    	 95 (('addr:district',), 38) (('building',), 36) (('addr:street',), 34)
    	 51957 (('addr:district',), 38) (('building',), 36) (('addr:street',), 34)
    	 4 ('Витебская область', 2) ('Могилевская область', 2) ('Минская область', 2)
    	 4 ('Минская область', 13907) ('Витебская область', 11924) ('Брестская область', 4563)
    	 57 (('addr:district',), 7) (('building', 'yes'), 5) (('building',), 5)
    	 51810 (('addr:district',), 30348) (('addr:country',), 30078) (('addr:country', 'BY'), 30078)
    addr:housenumber to 55536 965 0 0
    	 18 ('н', 51786) ('Н', 1440) ('ж', 1323)
    	 266 ('рынок "Южный"', 36) ('Молодёжная улица', 32) ('ДС Малиновка-4', 32)
    	 212 (('building',), 55523) (('building', 'yes'), 54390) (('addr:street',), 46769)
    	 1209 (('building',), 55523) (('building', 'yes'), 54390) (('addr:street',), 46769)
    	 0
    	 0
    	 0
    	 0
    to addr:street 1179 55285 57 23697
    	 80 ('Гомель', 340) ('Вокзал', 336) ('Полоцк', 84)
    	 248 ('Молодёжная улица', 16581) ('Солнечная улица', 5425) ('Красноармейская улица', 4811)
    	 634 (('type',), 1179) (('name',), 1179) (('route',), 1177)
    	 8794 (('type',), 1179) (('name',), 1179) (('route',), 1177)
    	 21 ('Автовокзал', 13) ('Молодёжная улица', 8) ('улица Белые Росы', 5)
    	 21 ('Молодёжная улица', 16581) ('улица Победы', 3141) ('улица Крупской', 1361)
    	 180 (('type',), 57) (('from',), 57) (('name',), 57)
    	 4175 (('building',), 23221) (('addr:housenumber',), 22768) (('building', 'yes'), 12646)
    addr:housename fixme 54842 2571 0 0
    	 29 ('н', 43674) ('Н', 6975) ('ж', 2240)
    	 305 ('адрес', 211) ('расположение', 108) ('положение/адрес', 102)
    	 201 (('building',), 54778) (('building', 'yes'), 53461) (('addr:street',), 40443)
    	 1784 (('building',), 54778) (('building', 'yes'), 53461) (('addr:street',), 40443)
    	 0
    	 0
    	 0
    	 0
    description addr:district 7337 54708 0 0
    	 5 ('н', 7314) ('ж', 16) ('Н', 5)
    	 139 ('Минский район', 3969) ('Воложинский район', 1696) ('Островецкий район', 1382)
    	 14 (('building',), 7336) (('building', 'yes'), 7336) (('addr:street',), 7059)
    	 87120 (('building',), 7336) (('building', 'yes'), 7336) (('addr:street',), 7059)
    	 0
    	 0
    	 0
    	 0
    official_status official_name 54213 1742 0 0
    	 6 ('садоводческое товарищество', 40871) ('Садоводческое товарищество', 13233) ('ФАП', 64)
    	 1241 ('Садоводческое товарищество "Строитель"', 24) ('Садоводческое товарищество "Лесная Поляна"', 13) ('Садоводческое товарищество "Дружба"', 10)
    	 4133 (('name',), 54190) (('place', 'allotments'), 52877) (('place',), 52877)
    	 2872 (('name',), 54190) (('place', 'allotments'), 52877) (('place',), 52877)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber from 54116 956 0 0
    	 19 ('н', 50690) ('ж', 1176) ('Н', 1080)
    	 264 ('Молодёжная улица', 32) ('рынок "Южный"', 32) ('ДС Малиновка-4', 30)
    	 212 (('building',), 54106) (('building', 'yes'), 52969) (('addr:street',), 45562)
    	 1185 (('building',), 54106) (('building', 'yes'), 52969) (('addr:street',), 45562)
    	 0
    	 0
    	 0
    	 0
    addr:housename minsk_PT:note 1461 51560 0 0
    	 8 ('Н', 837) ('н', 522) ('ж', 60)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 50192) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 808) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 560)
    	 83 (('building',), 1455) (('building', 'yes'), 1431) (('addr:street',), 1209)
    	 4600 (('building',), 1455) (('building', 'yes'), 1431) (('addr:street',), 1209)
    	 0
    	 0
    	 0
    	 0
    designation addr:region 12 50933 0 0
    	 1 ('б', 12)
    	 12 ('Минская область', 13907) ('Витебская область', 11924) ('Гродненская область', 8625)
    	 8 (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 12) (('addr:street',), 12) (('building', 'yes'), 12)
    	 88118 (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 12) (('addr:street',), 12) (('building', 'yes'), 12)
    	 0
    	 0
    	 0
    	 0
    ref addr:region 24 50855 0 0
    	 6 ('М', 16) ('В', 2) ('Б', 2)
    	 11 ('Минская область', 13907) ('Витебская область', 11924) ('Гродненская область', 8625)
    	 19 (('entrance',), 12) (('entrance', 'yes'), 12) (('aeroway', 'taxiway'), 7)
    	 87886 (('entrance',), 12) (('entrance', 'yes'), 12) (('aeroway', 'taxiway'), 7)
    	 0
    	 0
    	 0
    	 0
    addr:city network 50520 414 9646 11
    	 13 ('Минск', 46900) ('Брест', 2766) ('Полоцк', 317)
    	 16 ('Минский метрополитен', 262) ('Брестское отделение', 70) ('Минское отделение', 50)
    	 13662 (('addr:street',), 48508) (('addr:housenumber',), 47188) (('building',), 36045)
    	 396 (('addr:street',), 48508) (('addr:housenumber',), 47188) (('building',), 36045)
    	 4 ('Минск', 9380) ('Борисов', 125) ('Бобруйск', 124)
    	 4 ('Борисов', 4) ('Смолевичи', 3) ('Минск', 2)
    	 12645 (('addr:street',), 9260) (('addr:housenumber',), 9026) (('building',), 6710)
    	 46 (('name',), 11) (('type',), 9) (('route',), 8)
    addr:unit name 21698 46354 2 3
    	 4 ('Б', 12003) ('А', 9678) ('5А', 16)
    	 20570 ('Беларусбанк', 1045) ('Белагропромбанк', 380) ('Баня', 294)
    	 36 (('addr:street',), 21682) (('addr:housenumber',), 21682) (('addr:city',), 21682)
    	 40297 (('addr:street',), 21682) (('addr:housenumber',), 21682) (('addr:city',), 21682)
    	 2 ('5А', 1) ('А', 1)
    	 2 ('5А', 2) ('А', 1)
    	 9 (('building',), 2) (('building', 'house'), 1) (('addr:street',), 1)
    	 8 (('building',), 2) (('building', 'house'), 2) (('addr:street',), 1)
    addr:unit addr:street 1082 45733 0 0
    	 2 ('Б', 695) ('А', 387)
    	 1070 ('Белорусская улица', 2033) ('Брестская улица', 1183) ('улица Будённого', 1045)
    	 23 (('addr:street',), 1082) (('addr:housenumber',), 1082) (('addr:city',), 1082)
    	 8245 (('addr:street',), 1082) (('addr:housenumber',), 1082) (('addr:city',), 1082)
    	 0
    	 0
    	 0
    	 0
    name fire_hydrant:street 45430 4112 4248 517
    	 237 ('н', 31301) ('Н', 4202) ('Садовая улица', 1552)
    	 210 ('Советская', 200) ('Молодежная', 170) ('Первомайская', 160)
    	 2464 (('building',), 39596) (('building', 'yes'), 33282) (('building', 'residential'), 5203)
    	 573 (('building',), 39596) (('building', 'yes'), 33282) (('building', 'residential'), 5203)
    	 91 ('Садовая улица', 1552) ('Школьная улица', 1214) ('Озёрная улица', 459)
    	 91 ('Советская', 40) ('Молодежная', 34) ('Фрунзе', 31)
    	 1393 (('highway',), 3888) (('int_name',), 2984) (('highway', 'residential'), 2712)
    	 432 (('fire_hydrant:type',), 517) (('fire_hydrant:diameter',), 517) (('name',), 517)
    addr:city brand 45401 25 2 3
    	 12 ('Минск', 37520) ('Гродно', 5870) ('Брест', 1383)
    	 15 ('Минская школа киноискусства', 5) ('Витебскоблсоюзпечать', 3) ('Пинскдрев', 3)
    	 19976 (('addr:street',), 43778) (('addr:housenumber',), 42768) (('building',), 32625)
    	 256 (('addr:street',), 43778) (('addr:housenumber',), 42768) (('building',), 32625)
    	 1 ('Виктория', 2)
    	 1 ('Виктория', 3)
    	 7 (('addr:street',), 2) (('building', 'yes'), 2) (('building',), 2)
    	 24 (('shop', 'supermarket'), 3) (('shop',), 3) (('name', 'Виктория'), 3)
    addr:housenumber minsk_PT:note 1373 45146 0 0
    	 8 ('н', 822) ('Н', 360) ('ж', 147)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 43918) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 808) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 420)
    	 151 (('building',), 1370) (('building', 'yes'), 1329) (('addr:street',), 1157)
    	 4600 (('building',), 1370) (('building', 'yes'), 1329) (('addr:street',), 1157)
    	 0
    	 0
    	 0
    	 0
    ref official_name 28124 44563 2 2
    	 91 ('М', 5256) ('Н', 3320) ('С', 3136)
    	 7617 ('Борисов — Вилейка — Ошмяны', 464) ('Витебск — Городок (до автомобильной дороги М-8)', 438) ('Минск — Гродно — Брузги', 388)
    	 632 (('aeroway', 'taxiway'), 8716) (('aeroway',), 8716) (('name',), 6480)
    	 17068 (('aeroway', 'taxiway'), 8716) (('aeroway',), 8716) (('name',), 6480)
    	 2 ('МАЗС №5', 1) ('Юбилейная улица', 1)
    	 2 ('МАЗС №5', 1) ('Юбилейная улица', 1)
    	 22 (('int_name',), 2) (('name',), 2) (('fuel:lpg',), 1)
    	 57 (('name',), 2) (('fuel:lpg',), 1) (('fuel:HGV_diesel', 'yes'), 1)
    name old_addr 44534 536 4 1
    	 30 ('Н', 19100) ('н', 16343) ('улица Энгельса', 4312)
    	 120 ('улица Энгельса, 49А', 10) ('улица Ломоносова, 18А', 8) ('1-я Новопрудская улица, 15А', 8)
    	 403 (('building',), 37056) (('building', 'yes'), 22177) (('building', 'residential'), 12554)
    	 212 (('building',), 37056) (('building', 'yes'), 22177) (('building', 'residential'), 12554)
    	 1 ('18а', 4)
    	 1 ('18а', 1)
    	 6 (('building',), 4) (('building', 'yes'), 2) (('building', 'house'), 1)
    	 8 (('addr:postcode',), 1) (('addr:street',), 1) (('building',), 1)
    designation name 19593 44498 49 1190
    	 42 ('б', 18221) ('парк', 659) ('Лавка', 140)
    	 18963 ('Беларусбанк', 1045) ('Октябрьская улица', 793) ('Юбилейная улица', 607)
    	 232 (('name',), 19165) (('building',), 18324) (('addr:street',), 18302)
    	 32162 (('name',), 19165) (('building',), 18324) (('addr:street',), 18302)
    	 33 ('Лавка', 10) ('Колодец', 3) ('Детская площадка', 2)
    	 33 ('Каменка', 367) ('БПС-Сбербанк', 179) ('Городище', 146)
    	 183 (('name',), 27) (('amenity',), 21) (('amenity', 'bench'), 10)
    	 1210 (('int_name',), 385) (('amenity',), 255) (('place',), 227)
    building addr:place 7716 43823 0 0
    	 12 ('Н', 5313) ('н', 1046) ('р', 487)
    	 870 ('СТ "Малинники"', 2445) ('СТ "Шарик"', 1268) ('Огородники', 1164)
    	 46 (('name',), 1705) (('name', 'Н'), 1089) (('addr:street',), 534)
    	 2806 (('name',), 1705) (('name', 'Н'), 1089) (('addr:street',), 534)
    	 0
    	 0
    	 0
    	 0
    addr:region addr:full 41852 57 0 0
    	 5 ('Минская область', 27814) ('Гродненская область', 8625) ('Смоленская область', 4236)
    	 35 ('д. Яново, Борисовский район, Минская область', 12) ('д. Рудишки, Ошмянский район, Гродненская область', 8) ('Терехи, Логойский район, Минская область', 2)
    	 39136 (('addr:district',), 41531) (('addr:country',), 41398) (('addr:country', 'BY'), 36082)
    	 267 (('addr:district',), 41531) (('addr:country',), 41398) (('addr:country', 'BY'), 36082)
    	 0
    	 0
    	 0
    	 0
    addr:city destination 41812 540 14093 212
    	 55 ('Минск', 18760) ('Гомель', 16408) ('Берёзовка', 1603)
    	 184 ('Брэст', 45) ('Мінск', 39) ('Гомель', 32)
    	 15010 (('addr:street',), 40258) (('addr:housenumber',), 39443) (('building',), 30181)
    	 376 (('addr:street',), 40258) (('addr:housenumber',), 39443) (('building',), 30181)
    	 41 ('Минск', 9380) ('Берёзовка', 1603) ('Брест', 1383)
    	 41 ('Брэст', 45) ('Мінск', 39) ('Гомель', 32)
    	 14846 (('addr:street',), 13532) (('addr:housenumber',), 13297) (('building',), 10696)
    	 238 (('oneway',), 165) (('oneway', 'yes'), 165) (('highway',), 165)
    addr:city addr:region 21060 41738 9380 8
    	 6 ('Минск', 18760) ('Брест', 1383) ('Гомель', 586)
    	 7 ('Минская область', 13907) ('Витебская область', 11924) ('Могилёвская область', 6089)
    	 14366 (('addr:street',), 20279) (('addr:housenumber',), 19805) (('building',), 15031)
    	 71214 (('addr:street',), 20279) (('addr:housenumber',), 19805) (('building',), 15031)
    	 1 ('Минск', 9380)
    	 1 ('Минск', 8)
    	 12345 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 26 (('building:levels',), 8) (('addr:postcode',), 8) (('addr:street',), 8)
    was:name:prefix wikipedia 41364 139 0 0
    	 6 ('деревня', 37808) ('посёлок', 2535) ('хутор', 996)
    	 118 ('ru:Брагин (городской посёлок)', 4) ('ru:Бобр (городской посёлок)', 4) ('ru:Коханово (городской посёлок, Толочинский район)', 4)
    	 3066 (('name',), 41364) (('place',), 41364) (('abandoned:place',), 40580)
    	 561 (('name',), 41364) (('place',), 41364) (('abandoned:place',), 40580)
    	 0
    	 0
    	 0
    	 0
    destination wikipedia 40849 5372 0 0
    	 171 ('Гомель', 18016) ('Мінск', 7839) ('Магілёў', 3213)
    	 4418 ('be:Праспект Дзяржынскага (Мінск)', 202) ('be:Сож', 51) ('be:Лоша (прыток Ашмянкі)', 25)
    	 609 (('highway',), 36509) (('oneway', 'yes'), 36507) (('oneway',), 36507)
    	 12942 (('highway',), 36509) (('oneway', 'yes'), 36507) (('oneway',), 36507)
    	 0
    	 0
    	 0
    	 0
    addr:city to 39889 185 12796 89
    	 73 ('Минск', 28140) ('Гродно', 5870) ('Гомель', 1172)
    	 84 ('Гомель', 34) ('ДС Малиновка-4', 16) ('Октябрьский', 4)
    	 22036 (('addr:street',), 38232) (('addr:housenumber',), 37263) (('building',), 29080)
    	 505 (('addr:street',), 38232) (('addr:housenumber',), 37263) (('building',), 29080)
    	 38 ('Минск', 9380) ('Гомель', 586) ('Тюрли', 408)
    	 38 ('Гомель', 34) ('Новополоцк', 3) ('Полоцк', 3)
    	 14852 (('addr:street',), 12153) (('addr:housenumber',), 11609) (('building',), 9444)
    	 257 (('route',), 89) (('name',), 89) (('type',), 88)
    description ref 19940 39010 68 780
    	 41 ('н', 10494) ('Н', 7936) ('АЗС', 633)
    	 8568 ('б/н', 799) ('М8', 735) ('Н9031', 96)
    	 261 (('building',), 18940) (('building', 'yes'), 18928) (('addr:street',), 18231)
    	 13142 (('building',), 18940) (('building', 'yes'), 18928) (('addr:street',), 18231)
    	 18 ('кн', 46) ('Колонка', 2) ('Вход в общежитие', 2)
    	 18 ('М8', 735) ('кн', 12) ('ЦТП', 8)
    	 146 (('building',), 54) (('building', 'yes'), 53) (('addr:street',), 51)
    	 409 (('surface',), 734) (('highway',), 734) (('surface', 'asphalt'), 732)
    addr:housename to 38891 2088 3 4
    	 27 ('н', 32886) ('Н', 3348) ('к', 1176)
    	 348 ('Вокзал', 84) ('ДС Малиновка-4', 64) ('Автовокзал', 52)
    	 203 (('building',), 38832) (('building', 'yes'), 37772) (('addr:street',), 28300)
    	 1578 (('building',), 38832) (('building', 'yes'), 37772) (('addr:street',), 28300)
    	 2 ('Больница', 2) ('Хлебозавод', 1)
    	 2 ('Больница', 2) ('Хлебозавод', 2)
    	 15 (('building',), 3) (('addr:street',), 2) (('addr:housenumber',), 2)
    	 26 (('type',), 4) (('from',), 4) (('name',), 4)
    description short_name 37718 1275 2 2
    	 24 ('н', 37312) ('ж', 184) ('Н', 87)
    	 829 ('СТ "Дорожник"', 16) ('СТ "Лесная Поляна"', 14) ('СТ "Надежда"', 14)
    	 96 (('building',), 37680) (('building', 'yes'), 37676) (('addr:street',), 36221)
    	 2626 (('building',), 37680) (('building', 'yes'), 37676) (('addr:street',), 36221)
    	 2 ('Полигон ТБО', 1) ('СТ "Пралеска-2"', 1)
    	 2 ('Полигон ТБО', 1) ('СТ "Пралеска-2"', 1)
    	 6 (('landuse',), 1) (('landuse', 'landfill'), 1) (('name', 'Прудище'), 1)
    	 13 (('name',), 2) (('official_name',), 2) (('landuse',), 2)
    addr:housename from 37450 2074 2 1
    	 27 ('н', 32190) ('Н', 2511) ('к', 1204)
    	 346 ('Вокзал', 88) ('ДС Малиновка-4', 60) ('Автовокзал', 44)
    	 208 (('building',), 37396) (('building', 'yes'), 36349) (('addr:street',), 27129)
    	 1572 (('building',), 37396) (('building', 'yes'), 36349) (('addr:street',), 27129)
    	 1 ('Больница', 2)
    	 1 ('Больница', 1)
    	 15 (('addr:street',), 2) (('building',), 2) (('addr:housenumber',), 2)
    	 16 (('to',), 1) (('ref', '6А'), 1) (('type',), 1)
    operator official_name 31440 37010 55 32
    	 250 ('е', 6711) ('я', 2559) ('Беларусбанк', 2310)
    	 7652 ('Столбцы — Ивацевичи — Кобрин', 606) ('Борисов — Вилейка — Ошмяны', 464) ('Витебск — Городок (до автомобильной дороги М-8)', 292)
    	 8432 (('name',), 25022) (('amenity',), 14885) (('opening_hours',), 10263)
    	 17398 (('name',), 25022) (('amenity',), 14885) (('opening_hours',), 10263)
    	 30 ('УА "Высоцкі дзяржаўны прафесійны ліцэй сельскагаспадарчай вытворчасці"', 6) ('РУП «Издательство «Белбланкавыд»', 5) ('ОАО "Автобусный парк г. Гродно"', 4)
    	 30 ('ЗАСО Белнефтестрах', 2) ('УА "Высоцкі дзяржаўны прафесійны ліцэй сельскагаспадарчай вытворчасці"', 2) ('Белорусский народный банк', 1)
    	 365 (('name',), 49) (('opening_hours',), 29) (('shop',), 16)
    	 295 (('name',), 32) (('addr:street',), 16) (('addr:housenumber',), 15)
    addr:place addr:street 12745 36903 319 6848
    	 105 ('Остров', 2160) ('Первомайский', 2088) ('Бор', 1518)
    	 312 ('Зелёная улица', 6740) ('Набережная улица', 6128) ('улица Калинина', 4896)
    	 799 (('building',), 12305) (('addr:housenumber',), 12300) (('building', 'yes'), 5652)
    	 4441 (('building',), 12305) (('addr:housenumber',), 12300) (('building', 'yes'), 5652)
    	 11 ('Минойты', 236) ('Кирово', 36) ('Бояры', 36)
    	 11 ('Набережная улица', 6128) ('улица 40 лет Победы', 636) ('площадь 17 Сентября', 54)
    	 231 (('addr:housenumber',), 302) (('building',), 302) (('addr:street',), 248)
    	 1358 (('building',), 6752) (('addr:housenumber',), 6498) (('building', 'yes'), 4333)
    building:levels ref 7945 36373 2 8
    	 2 ('Н', 7936) ('2А', 9)
    	 7943 ('Н9031', 96) ('Н9531', 73) ('Н9901', 69)
    	 5 (('building',), 7945) (('building', 'yes'), 7936) (('addr:street',), 9)
    	 9711 (('building',), 7945) (('building', 'yes'), 7936) (('addr:street',), 9)
    	 2 ('2А', 1) ('Н', 1)
    	 2 ('2А', 4) ('Н', 4)
    	 5 (('building',), 2) (('addr:street',), 1) (('addr:street', 'Центральная улица'), 1)
    	 47 (('railway:signal:position', 'right'), 3) (('railway', 'signal'), 3) (('railway',), 3)
    name heritage:description 36324 972 6 7
    	 91 ('н', 25484) ('Н', 3438) ('к', 930)
    	 106 ('Будынак былой жаночай Марыінскай гімназіі', 22) ('Былы гарадскі сад (Цэнтральны дзіцячы парк імя Горкага ў складзе: планіровачная структура, ландшафт, адміністрацыйны будынак, агароджа)', 19) ('Абеліск ”Мінск горад-герой“', 18)
    	 675 (('building',), 34758) (('building', 'yes'), 28658) (('building', 'residential'), 4267)
    	 641 (('building',), 34758) (('building', 'yes'), 28658) (('building', 'residential'), 4267)
    	 5 ('Усходнія могілкі', 2) ('Флігель', 1) ('Будынак былой духоўнай кансісторыі', 1)
    	 5 ('Флігель', 3) ('Усходнія могілкі', 1) ('Будынак былой духоўнай кансісторыі', 1)
    	 54 (('tourism', 'attraction'), 2) (('tourism',), 2) (('bus', 'yes'), 2)
    	 82 (('building',), 6) (('start_date',), 5) (('addr:postcode',), 5)
    addr:housenumber addr2:street 35575 878 0 0
    	 15 ('н', 32880) ('Н', 1560) ('ж', 490)
    	 194 ('Молодёжная улица', 44) ('переулок Дзержинского', 38) ('улица Пушкина', 36)
    	 188 (('building',), 35561) (('building', 'yes'), 34784) (('addr:street',), 29994)
    	 473 (('building',), 35561) (('building', 'yes'), 34784) (('addr:street',), 29994)
    	 0
    	 0
    	 0
    	 0
    ref addr:district 169 35061 0 0
    	 12 ('М', 44) ('Н', 20) ('В', 18)
    	 85 ('Минский район', 3969) ('Воложинский район', 1696) ('Дзержинский район', 1166)
    	 51 (('aeroway', 'taxiway'), 46) (('aeroway',), 46) (('entrance',), 42)
    	 55993 (('aeroway', 'taxiway'), 46) (('aeroway',), 46) (('entrance',), 42)
    	 0
    	 0
    	 0
    	 0
    operator wikipedia 31450 35029 0 0
    	 72 ('е', 13240) ('я', 8543) ('б', 5646)
    	 20158 ('be:Праспект Дзяржынскага (Мінск)', 202) ('be:Альхоўка (басейн Нёмана)', 114) ('ru:Магистраль М12 (Белоруссия)', 78)
    	 850 (('name',), 22738) (('amenity',), 14362) (('amenity', 'atm'), 14214)
    	 54193 (('name',), 22738) (('amenity',), 14362) (('amenity', 'atm'), 14214)
    	 0
    	 0
    	 0
    	 0
    brand operator 34923 7264 2260 3971
    	 98 ('Белоруснефть', 24752) ('Беларусбанк', 6384) ('Белпошта', 492)
    	 298 ('Беларусбанк', 770) ('Мила', 525) ('Белагропромбанк', 456)
    	 6118 (('amenity',), 33365) (('opening_hours',), 29592) (('name',), 27875)
    	 10414 (('amenity',), 33365) (('opening_hours',), 29592) (('name',), 27875)
    	 74 ('Белоруснефть', 884) ('Беларусбанк', 266) ('Белшина', 169)
    	 74 ('Беларусбанк', 770) ('Мила', 525) ('Белагропромбанк', 456)
    	 5857 (('name',), 1801) (('opening_hours',), 1779) (('amenity',), 1777)
    	 4998 (('amenity',), 3078) (('opening_hours',), 2558) (('name',), 2548)
    addr:city via 34555 74 62 15
    	 29 ('Минск', 28140) ('Хойники', 4250) ('Полоцк', 317)
    	 31 ('Речица, Бобруйск, Минск', 4) ('Рогачёв', 4) ('Чечерск', 4)
    	 13758 (('addr:street',), 33232) (('addr:housenumber',), 32418) (('building',), 25341)
    	 106 (('addr:street',), 33232) (('addr:housenumber',), 32418) (('building',), 25341)
    	 6 ('Могилев', 21) ('Лоев', 20) ('Славгород', 7)
    	 6 ('Чечерск', 4) ('Лоев', 4) ('Рогачёв', 2)
    	 386 (('addr:street',), 60) (('addr:housenumber',), 59) (('name',), 49)
    	 45 (('to',), 15) (('route',), 15) (('public_transport:version', '2'), 15)
    addr:city addr:district 19533 34410 57 5288
    	 69 ('Минск', 9380) ('Брест', 5532) ('Гомель', 586)
    	 65 ('Минский район', 7938) ('Островецкий район', 1382) ('Оршанский район', 1064)
    	 16743 (('addr:street',), 18841) (('addr:housenumber',), 18387) (('building',), 15408)
    	 45742 (('addr:street',), 18841) (('addr:housenumber',), 18387) (('building',), 15408)
    	 5 ('Светлогорск', 46) ('Солигорский район', 5) ('Минский район', 4)
    	 5 ('Минский район', 3969) ('Оршанский район', 532) ('Слуцкий район', 432)
    	 341 (('addr:housenumber',), 53) (('addr:street',), 51) (('name',), 47)
    	 5157 (('addr:region',), 5275) (('addr:country',), 5245) (('addr:country', 'BY'), 5245)
    addr:housenumber old_addr 33675 199 0 0
    	 21 ('н', 16166) ('Н', 6000) ('8А', 2554)
    	 116 ('улица Энгельса, 49А', 6) ('1-я Новопрудская улица, 68А', 4) ('1-я Новопрудская улица, 15А', 4)
    	 5291 (('building',), 33258) (('addr:street',), 29881) (('building', 'yes'), 28289)
    	 207 (('building',), 33258) (('addr:street',), 29881) (('building', 'yes'), 28289)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber fire_hydrant:street 33674 1316 1 27
    	 11 ('н', 30962) ('Н', 1320) ('ж', 833)
    	 176 ('Молодежная', 136) ('Набережная', 64) ('Первомайская', 40)
    	 153 (('building',), 33662) (('building', 'yes'), 32923) (('addr:street',), 28369)
    	 541 (('building',), 33662) (('building', 'yes'), 32923) (('addr:street',), 28369)
    	 1 ('Строителей', 1)
    	 1 ('Строителей', 27)
    	 2 (('addr:street',), 1) (('addr:street', '17'), 1)
    	 60 (('fire_hydrant:type',), 27) (('fire_hydrant:diameter',), 27) (('name',), 27)
    name opening_hours 33502 704 1 1
    	 38 ('н', 27977) ('Н', 2674) ('п', 748)
    	 124 ('Пн-Пт 9-18 Сб-Вс 10-17', 18) ('Вт-Чт: 09:00—20:00; Пт: 09:00—18:00; Сб.: 09:00—15:00; Вс.: выходной, Пн.: сандень (график с 1 сентября по 31 мая); Пн.-Чт. 9:00-17:30, Пт. 9:00-16:15, Сб., Вс. выходной (график работы с 1 июня по 31 августа)', 14) ('Понедельник – пятница: 8.30 – 17.30 Обеденный перерыв: 13.00 - 14.00 Выходной: суббота, воскресенье', 12)
    	 174 (('building',), 33199) (('building', 'yes'), 28993) (('building', 'residential'), 3419)
    	 837 (('building',), 33199) (('building', 'yes'), 28993) (('building', 'residential'), 3419)
    	 1 ('не работает', 1)
    	 1 ('не работает', 1)
    	 2 (('amenity', 'cafe'), 1) (('amenity',), 1)
    	 20 (('fuel:octane_95', 'yes'), 1) (('fuel:octane_92', 'yes'), 1) (('website', 'https://www.belorusneft.by/'), 1)
    ref note 33372 2819 423 2
    	 76 ('М1', 16592) ('М8', 5145) ('М10', 2982)
    	 996 ('Не надо ставить эту камеру на линию дороги!', 132) ('Необходим тэг add:street или add:place', 128) ('Внешняя нода для согласования с картой Минска', 90)
    	 953 (('highway',), 29857) (('surface',), 29353) (('surface', 'asphalt'), 29217)
    	 2526 (('highway',), 29857) (('surface',), 29353) (('surface', 'asphalt'), 29217)
    	 1 ('Р99', 423)
    	 1 ('Р99', 2)
    	 206 (('highway',), 422) (('surface',), 390) (('surface', 'asphalt'), 390)
    	 8 (('type', 'destination_sign'), 2) (('type',), 2) (('colour:back',), 2)
    building:levels addr:street 433 32793 0 0
    	 1 ('Н', 433)
    	 433 ('Новая улица', 7383) ('Набережная улица', 6128) ('улица Некрасова', 1329)
    	 2 (('building', 'yes'), 433) (('building',), 433)
    	 5410 (('building', 'yes'), 433) (('building',), 433)
    	 0
    	 0
    	 0
    	 0
    building minsk_PT:note 504 32225 0 0
    	 5 ('Н', 483) ('н', 6) ('Т', 6)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 31370) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 505) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 350)
    	 17 (('name',), 111) (('name', 'Н'), 99) (('building:levels',), 6)
    	 4600 (('name',), 111) (('name', 'Н'), 99) (('building:levels',), 6)
    	 0
    	 0
    	 0
    	 0
    name gomel_PT:note 745 31262 0 0
    	 14 ('Н', 382) ('н', 277) ('Т', 25)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 31262)
    	 54 (('building',), 738) (('building', 'yes'), 419) (('building', 'residential'), 273)
    	 859 (('building',), 738) (('building', 'yes'), 419) (('building', 'residential'), 273)
    	 0
    	 0
    	 0
    	 0
    addr:street:name addr:street 12 31015 1 4
    	 1 ('Центральная', 12)
    	 12 ('Центральная улица', 30739) ('2-я Центральная улица', 154) ('1-я Центральная улица', 79)
    	 8 (('building', 'yes'), 12) (('name',), 12) (('addr:streetnumber', '38'), 12)
    	 2651 (('building', 'yes'), 12) (('name',), 12) (('addr:streetnumber', '38'), 12)
    	 1 ('Центральная', 1)
    	 1 ('Центральная', 4)
    	 8 (('building', 'yes'), 1) (('name',), 1) (('addr:streetnumber', '38'), 1)
    	 25 (('name',), 4) (('highway',), 4) (('name', 'Центральная улица'), 4)
    addr:city destination:lanes:backward 30621 10 0 0
    	 5 ('Минск', 28140) ('Нарочь', 2266) ('Вилейка', 158)
    	 3 ('Сморгонь;Минск;Вилейка;Нарочь|Минск;Вилейка;Нарочь', 4) ('Воложин;Сморгонь|Минск', 3) ('Минск;Вилейка;Нарочь|Минск', 3)
    	 12553 (('addr:street',), 29445) (('addr:housenumber',), 28745) (('building',), 22162)
    	 41 (('addr:street',), 29445) (('addr:housenumber',), 28745) (('building',), 22162)
    	 0
    	 0
    	 0
    	 0
    name full_name 30462 968 7 4
    	 211 ('н', 21883) ('Беларусбанк', 2090) ('к', 620)
    	 85 ('Государственное учреждение образования "Центр творчества детей и молодежи "Спектр" г.Гродно"', 20) ('Обменный пункт №611/5048 ОАО "АСБ Беларусбанк"', 19) ('Государственное учреждение образования "Центр творчества детей и молодежи “Прамень” г. Гродно"', 19)
    	 3233 (('building',), 26722) (('building', 'yes'), 23895) (('amenity',), 2665)
    	 589 (('building',), 26722) (('building', 'yes'), 23895) (('amenity',), 2665)
    	 4 ('Госавтоинспекция', 4) ('Отдел пограничной службы "Гудогай"', 1) ('Гродненский производственно-торговый филиал ОАО «Агрокомбинат "Скидельский"»', 1)
    	 4 ('Госавтоинспекция', 1) ('Отдел пограничной службы "Гудогай"', 1) ('Гродненский производственно-торговый филиал ОАО «Агрокомбинат "Скидельский"»', 1)
    	 46 (('public_transport',), 4) (('shelter', 'yes'), 3) (('shelter',), 3)
    	 39 (('name',), 4) (('addr:city',), 2) (('landuse',), 2)
    building note 30028 5977 1 1
    	 22 ('Н', 23989) ('н', 2648) ('р', 1267)
    	 1464 ('Не надо ставить эту камеру на линию дороги!', 396) ('маршрутам присвоены 3 рефа одновременно', 189) ('Внешняя нода для согласования с картой Минска', 135)
    	 76 (('name',), 6297) (('name', 'Н'), 4917) (('addr:street',), 1616)
    	 3531 (('name',), 6297) (('name', 'Н'), 4917) (('addr:street',), 1616)
    	 1 ('не используется', 1)
    	 1 ('не используется', 1)
    	 6 (('addr:street',), 1) (('addr:housenumber', '1А'), 1) (('name',), 1)
    	 24 (('name', 'Михалово-2'), 1) (('minsk_PT:note',), 1) (('shelter',), 1)
    addr:city from 29931 179 12666 87
    	 74 ('Минск', 18760) ('Гродно', 5870) ('Гомель', 586)
    	 83 ('Гомель', 36) ('ДС Малиновка-4', 15) ('Бобруйская', 6)
    	 22197 (('addr:street',), 28742) (('addr:housenumber',), 28107) (('building',), 22044)
    	 501 (('addr:street',), 28742) (('addr:housenumber',), 28107) (('building',), 22044)
    	 36 ('Минск', 9380) ('Гомель', 586) ('Полоцк', 317)
    	 36 ('Гомель', 36) ('Речица', 4) ('Минск', 3)
    	 15140 (('addr:street',), 12110) (('addr:housenumber',), 11667) (('building',), 9263)
    	 259 (('to',), 87) (('route',), 87) (('name',), 87)
    destination addr:region 38 29771 1 8
    	 4 ('Гомель', 32) ('Могилёв', 3) ('Минск', 2)
    	 5 ('Минская область', 13907) ('Могилёвская область', 6089) ('Гомельская область', 5204)
    	 38 (('oneway',), 33) (('oneway', 'yes'), 33) (('highway',), 33)
    	 50490 (('oneway',), 33) (('oneway', 'yes'), 33) (('highway',), 33)
    	 1 ('Минск', 1)
    	 1 ('Минск', 8)
    	 12 (('maxspeed', '60'), 1) (('maxaxleload', '10'), 1) (('maxaxleload',), 1)
    	 26 (('building:levels',), 8) (('addr:postcode',), 8) (('addr:street',), 8)
    addr:housenumber opening_hours 29709 242 0 0
    	 10 ('н', 27674) ('Н', 840) ('П', 750)
    	 112 ('Пн-Пт 9-18 Сб-Вс 10-17', 6) ('ПН-ПТ с 9.00 до 21.00  СБ, ВС – выходной', 4) ('Вт-Чт: 09:00—20:00; Пт: 09:00—18:00; Сб.: 09:00—15:00; Вс.: выходной, Пн.: сандень (график с 1 сентября по 31 мая); Пн.-Чт. 9:00-17:30, Пт. 9:00-16:15, Сб., Вс. выходной (график работы с 1 июня по 31 августа)', 4)
    	 184 (('building',), 29702) (('building', 'yes'), 28853) (('addr:street',), 24990)
    	 781 (('building',), 29702) (('building', 'yes'), 28853) (('addr:street',), 24990)
    	 0
    	 0
    	 0
    	 0
    addr:city contact:website 29472 15 0 0
    	 10 ('Минск', 28140) ('Гомель', 586) ('Логойск', 274)
    	 8 ('https://www.belinvestbank.by/about-bank/service-points?town=Гомель&type=atm&showList=list', 4) ('https://azs.a-100.by/set-azs/map-azs/?query=Минский р-н, Боровая, 7', 2) ('https://azs.a-100.by/set-azs/map-azs/?query=Минский р-н, трасса на г. Могилев (М4), 4 км от МКАД', 2)
    	 13913 (('addr:street',), 28292) (('addr:housenumber',), 27612) (('building',), 20772)
    	 110 (('addr:street',), 28292) (('addr:housenumber',), 27612) (('building',), 20772)
    	 0
    	 0
    	 0
    	 0
    addr:housename source 14817 28829 37 1
    	 19 ('н', 8700) ('Н', 5301) ('ж', 300)
    	 69 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 12894) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 5510) ('Национальное кадастровое агентство nca.by', 5470)
    	 171 (('building',), 14765) (('building', 'yes'), 14446) (('addr:street',), 11575)
    	 1141 (('building',), 14765) (('building', 'yes'), 14446) (('addr:street',), 11575)
    	 1 ('Магазин', 37)
    	 1 ('Магазин', 1)
    	 55 (('building',), 37) (('addr:street',), 36) (('building', 'yes'), 34)
    	 8 (('designation', 'Магазин мебели'), 1) (('shop', 'supermarket'), 1) (('designation',), 1)
    description inscription 28685 1008 372 16
    	 41 ('н', 27189) ('ж', 510) ('кн', 368)
    	 544 ('На этом месте 26 июня 1944 г. в жестокой схватке с фашистскими оккупантами был спасён от взрыва мост группой бойцов под командованием ст. сержанта Блохина Ф. Т., удостоенного за этот подвиг звания Героя Советского Союза.', 6) ('Продукты', 5) ('Князев Василий Александрович. Герой Сов. Союза, лётчик-истребитель. Совершил 1088 боевых вылетов, сбил 29 самолётов. Уроженец ст. Княжица витебского р-на. Работал в локомотивном депо. Окончил Витебский аэроклуб.', 5)
    	 501 (('building',), 28332) (('building', 'yes'), 28313) (('addr:street',), 27188)
    	 1192 (('building',), 28332) (('building', 'yes'), 28313) (('addr:street',), 27188)
    	 11 ('Шиномонтаж', 358) ('Продукты', 3) ('Детская одежда', 3)
    	 11 ('Продукты', 5) ('Стройматериалы', 2) ('Шиномонтаж', 1)
    	 387 (('shop',), 366) (('service', 'tyres'), 358) (('service',), 358)
    	 109 (('shop',), 10) (('noname',), 10) (('noname', 'yes'), 10)
    name destination:backward 28565 850 90 25
    	 116 ('н', 20221) ('Н', 4202) ('к', 680)
    	 108 ('Мінск', 32) ('прамзона Шабаны', 24) ('Калодзішчы;Заслаўе', 24)
    	 999 (('building',), 27187) (('building', 'yes'), 21990) (('building', 'residential'), 4274)
    	 234 (('building',), 27187) (('building', 'yes'), 21990) (('building', 'residential'), 4274)
    	 9 ('Минск', 42) ('Гомель', 15) ('Гарадзішча', 15)
    	 9 ('Мінск', 8) ('Горкі', 5) ('Гомель', 4)
    	 193 (('admin_level',), 23) (('traffic_sign',), 22) (('traffic_sign', 'city_limit'), 22)
    	 72 (('surface', 'asphalt'), 25) (('surface',), 25) (('highway',), 25)
    name artist_name 28534 1170 1 3
    	 105 ('н', 21052) ('Н', 3820) ('к', 760)
    	 132 ('А.Чумаков', 60) ('Алёна Василькович', 42) ('Пантелеев В. И.', 35)
    	 729 (('building',), 27667) (('building', 'yes'), 22779) (('building', 'residential'), 4053)
    	 577 (('building',), 27667) (('building', 'yes'), 22779) (('building', 'residential'), 4053)
    	 1 ('Заир Азгур', 1)
    	 1 ('Заир Азгур', 3)
    	 4 (('memorial',), 1) (('memorial', 'plaque'), 1) (('historic',), 1)
    	 34 (('memorial', 'statue'), 3) (('artist:wikipedia', 'ru:Азгур, Заир Исаакович'), 3) (('name',), 3)
    addr:city minsk_PT:note 28140 6445 0 0
    	 1 ('Минск', 28140)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 12345 (('addr:street',), 27000) (('addr:housenumber',), 26331) (('building',), 19707)
    	 4600 (('addr:street',), 27000) (('addr:housenumber',), 26331) (('building',), 19707)
    	 0
    	 0
    	 0
    	 0
    addr:region addr:street 28006 2675 0 0
    	 2 ('Минская область', 27814) ('Минск', 192)
    	 24 ('Минская улица', 2295) ('Минский переулок', 102) ('улица Минский Тракт', 81)
    	 21490 (('addr:district',), 27758) (('addr:country',), 27504) (('addr:country', 'BY'), 27504)
    	 1143 (('addr:district',), 27758) (('addr:country',), 27504) (('addr:country', 'BY'), 27504)
    	 0
    	 0
    	 0
    	 0
    description addr:place 27963 18083 1 2
    	 15 ('н', 27719) ('ж', 102) ('кн', 46)
    	 593 ('СТ "Малинники"', 815) ('СТ "Станкостроитель"', 476) ('Огородники', 388)
    	 108 (('building',), 27928) (('building', 'yes'), 27926) (('addr:street',), 26866)
    	 2193 (('building',), 27928) (('building', 'yes'), 27926) (('addr:street',), 26866)
    	 1 ('Коробчицы', 1)
    	 1 ('Коробчицы', 2)
    	 10 (('note',), 1) (('map_size',), 1) (('map_type', 'street'), 1)
    	 28 (('addr:street',), 2) (('addr:housenumber',), 2) (('amenity', 'bar'), 1)
    was:name:prefix name 27942 923 54 2
    	 9 ('деревня', 17792) ('хутор', 5478) ('посёлок', 2470)
    	 619 ('Автостанция', 30) ('Насосная станция', 22) ('Подстанция', 15)
    	 3161 (('name',), 27938) (('place',), 27938) (('abandoned:place',), 27432)
    	 1180 (('name',), 27938) (('place',), 27938) (('abandoned:place',), 27432)
    	 2 ('фольварк', 43) ('околица', 11)
    	 2 ('фольварк', 1) ('околица', 1)
    	 74 (('int_name:prefix',), 54) (('abandoned:place', 'hamlet'), 54) (('int_name:prefix', 'uročyšča'), 54)
    	 10 (('int_name', 'falvarak'), 1) (('historic', 'manor'), 1) (('historic',), 1)
    addr:housenumber heritage:description 27829 326 0 0
    	 14 ('н', 25208) ('Н', 1080) ('ж', 1078)
    	 101 ('Будынак былой жаночай Марыінскай гімназіі', 10) ('Манастырскі корпус', 6) ('Будынак Нацыянальнага музея гісторыі і культуры Рэспублікі Беларусь', 5)
    	 154 (('building',), 27820) (('building', 'yes'), 27272) (('addr:street',), 23436)
    	 615 (('building',), 27820) (('building', 'yes'), 27272) (('addr:street',), 23436)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber brand 27673 2297 1 1
    	 17 ('н', 26304) ('Н', 600) ('П', 390)
    	 127 ('Белоруснефть', 884) ('Беларусбанк', 266) ('Белшина', 169)
    	 192 (('building',), 27668) (('building', 'yes'), 27034) (('addr:street',), 23300)
    	 5362 (('building',), 27668) (('building', 'yes'), 27034) (('addr:street',), 23300)
    	 1 ('Хуторок', 1)
    	 1 ('Хуторок', 1)
    	 4 (('addr:street',), 1) (('building',), 1) (('addr:street', 'улица Лесничество'), 1)
    	 32 (('opening_hours', 'Mo-Su 09:00-23:00'), 1) (('name',), 1) (('opening_hours',), 1)
    note addr:street 262 27285 0 0
    	 12 ('Я', 145) ('лес', 54) ('Поле', 31)
    	 248 ('Полевая улица', 7372) ('улица Якуба Коласа', 2986) ('Полесская улица', 2850)
    	 53 (('building',), 161) (('building:levels',), 158) (('building:levels', '1'), 156)
    	 4370 (('building',), 161) (('building:levels',), 158) (('building:levels', '1'), 156)
    	 0
    	 0
    	 0
    	 0
    operator addr:district 87 26628 0 0
    	 6 ('е', 53) ('б', 17) ('я', 14)
    	 76 ('Брестская обл.', 1932) ('Витебский район', 1434) ('Мядельский район', 1242)
    	 38 (('name',), 73) (('name', 'Складской комплекс «Северный»'), 53) (('landuse',), 53)
    	 43813 (('name',), 73) (('name', 'Складской комплекс «Северный»'), 53) (('landuse',), 53)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr2:street 26228 1768 4 5
    	 18 ('н', 20880) ('Н', 3627) ('к', 959)
    	 240 ('переулок Дзержинского', 57) ('улица Пушкина', 54) ('улица Максима Горького', 52)
    	 131 (('building',), 26191) (('building', 'yes'), 25450) (('addr:street',), 19389)
    	 498 (('building',), 26191) (('building', 'yes'), 25450) (('addr:street',), 19389)
    	 2 ('Лесная улица', 3) ('Пролетарская улица', 1)
    	 2 ('Лесная улица', 3) ('Пролетарская улица', 2)
    	 10 (('building',), 4) (('addr:housenumber',), 4) (('building', 'yes'), 3)
    	 32 (('addr:postcode',), 5) (('addr:street',), 5) (('building',), 5)
    ref minsk_PT:note 36 25780 0 0
    	 4 ('М', 12) ('Н', 12) ('Т', 6)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 25096) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 404) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 280)
    	 33 (('entrance',), 9) (('entrance', 'yes'), 9) (('aeroway', 'taxiway'), 9)
    	 4600 (('entrance',), 9) (('entrance', 'yes'), 9) (('aeroway', 'taxiway'), 9)
    	 0
    	 0
    	 0
    	 0
    addr:housename old_addr 24810 364 0 0
    	 9 ('Н', 13950) ('н', 10266) ('к', 364)
    	 120 ('улица Энгельса, 49А', 6) ('1-я Новопрудская улица, 15А', 6) ('1-я Новопрудская улица, 40А', 5)
    	 91 (('building',), 24650) (('building', 'yes'), 24143) (('addr:street',), 20282)
    	 212 (('building',), 24650) (('building', 'yes'), 24143) (('addr:street',), 20282)
    	 0
    	 0
    	 0
    	 0
    operator addr:place 881 24680 9 130
    	 20 ('е', 516) ('я', 143) ('б', 132)
    	 683 ('Дубровня', 558) ('Старое Село', 383) ('Королищевичи', 372)
    	 162 (('name',), 729) (('landuse',), 518) (('name', 'Складской комплекс «Северный»'), 516)
    	 2063 (('name',), 729) (('landuse',), 518) (('name', 'Складской комплекс «Северный»'), 516)
    	 4 ('Полесье', 3) ('СТ "Криница-Кривополье"', 3) ('Дружба', 2)
    	 4 ('Бобры', 42) ('СТ "Криница-Кривополье"', 37) ('Полесье', 35)
    	 49 (('name',), 6) (('addr:street',), 5) (('shop',), 3)
    	 147 (('building',), 119) (('addr:housenumber',), 117) (('building', 'yes'), 71)
    name destination:forward 24580 853 64 27
    	 108 ('н', 18559) ('Н', 2292) ('М', 754)
    	 97 ('Мiнск', 48) ('12-ы кіламетр МКАД;Слуцк;Гродна;Брэст', 39) ('Барановичи', 25)
    	 807 (('building',), 23420) (('building', 'yes'), 19757) (('building', 'residential'), 2967)
    	 264 (('building',), 23420) (('building', 'yes'), 19757) (('building', 'residential'), 2967)
    	 11 ('Барановичи', 22) ('Гомель', 15) ('Васілеўшчына', 7)
    	 11 ('Гомель', 5) ('Барановичи', 5) ('Мінск', 5)
    	 175 (('public_transport',), 30) (('int_name',), 20) (('bus', 'yes'), 17)
    	 84 (('highway',), 27) (('surface',), 26) (('surface', 'asphalt'), 26)
    fire_hydrant:city addr:street 24501 3727 0 0
    	 3 ('Минск', 24384) ('Микашевичи', 106) ('Могилёв', 11)
    	 35 ('Минская улица', 2295) ('Могилёвская улица', 876) ('Минский переулок', 102)
    	 1399 (('fire_hydrant:type',), 24501) (('emergency', 'fire_hydrant'), 24501) (('emergency',), 24501)
    	 1606 (('fire_hydrant:type',), 24501) (('emergency', 'fire_hydrant'), 24501) (('emergency',), 24501)
    	 0
    	 0
    	 0
    	 0
    addr:housename fire_hydrant:street 24092 2199 2 12
    	 15 ('н', 19662) ('Н', 3069) ('к', 665)
    	 204 ('Молодежная', 136) ('Советская', 120) ('Набережная', 64)
    	 114 (('building',), 24061) (('building', 'yes'), 23422) (('addr:street',), 17689)
    	 572 (('building',), 24061) (('building', 'yes'), 23422) (('addr:street',), 17689)
    	 2 ('Калинина', 1) ('Садовая', 1)
    	 2 ('Калинина', 7) ('Садовая', 5)
    	 17 (('name',), 2) (('addr:street', 'улица Калинина'), 1) (('name', 'Беларусбанк'), 1)
    	 34 (('fire_hydrant:type',), 12) (('fire_hydrant:diameter',), 12) (('name',), 12)
    name branch 23958 657 5 7
    	 66 ('н', 20775) ('Беларусбанк', 1045) ('Н', 382)
    	 88 ('РУП "Минскэнерго"', 135) ('Столбцовских ЭС', 25) ('РУП "Могилёвское отделение белорусской железной дороги", могилёвская дистанция электроснабжения', 18)
    	 1573 (('building',), 22523) (('building', 'yes'), 20552) (('addr:street',), 1755)
    	 499 (('building',), 22523) (('building', 'yes'), 20552) (('addr:street',), 1755)
    	 5 ('РУП "Брестэнерго"', 1) ('Министерство здравоохранения РБ', 1) ('Наровлянский РЭС', 1)
    	 5 ('РУП "Брестэнерго"', 2) ('БГПЗ', 2) ('Министерство здравоохранения РБ', 1)
    	 27 (('office',), 2) (('office', 'government'), 2) (('addr:postcode',), 2)
    	 53 (('power',), 6) (('name',), 6) (('operator',), 6)
    name owner 23778 2045 1270 7
    	 119 ('н', 14127) ('Беларусбанк', 3135) ('Н', 2292)
    	 67 ('ОАО «Белорусский банк развития и реконструкции «Белинвестбанк»', 705) ('ОАО «АСБ Беларусбанк»', 330) ('ОАО «Белагропромбанк»', 130)
    	 2918 (('building',), 18816) (('building', 'yes'), 15679) (('amenity',), 4999)
    	 620 (('building',), 18816) (('building', 'yes'), 15679) (('amenity',), 4999)
    	 7 ('Беларусбанк', 1045) ('БПС-Сбербанк', 179) ('Фармация', 32)
    	 7 ('Беларусбанк', 1) ('БПС-Сбербанк', 1) ('Фармация', 1)
    	 1223 (('amenity',), 1238) (('amenity', 'bank'), 706) (('int_name',), 673)
    	 75 (('name',), 5) (('amenity',), 4) (('opening_hours',), 4)
    addr:housenumber ref:mcrb 23656 725 0 0
    	 20 ('2Г', 9735) ('3Г', 7967) ('13Г', 2313)
    	 352 ('712Ж000215', 6) ('713Г000073', 4) ('713Г000028', 4)
    	 925 (('building',), 22908) (('addr:street',), 22353) (('building', 'yes'), 13678)
    	 1089 (('building',), 22908) (('addr:street',), 22353) (('building', 'yes'), 13678)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber source 23409 23544 6 1
    	 22 ('н', 13700) ('1А', 3265) ('Н', 2280)
    	 62 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 10745) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 5510) ('Национальное кадастровое агентство nca.by', 3282)
    	 4643 (('building',), 23166) (('addr:street',), 20446) (('building', 'yes'), 20222)
    	 1100 (('building',), 23166) (('addr:street',), 20446) (('building', 'yes'), 20222)
    	 1 ('Магазин', 6)
    	 1 ('Магазин', 1)
    	 12 (('addr:street',), 6) (('building', 'yes'), 5) (('building',), 5)
    	 8 (('designation', 'Магазин мебели'), 1) (('shop', 'supermarket'), 1) (('designation',), 1)
    addr:housenumber full_name 23521 223 0 0
    	 18 ('н', 21646) ('ж', 1029) ('П', 390)
    	 85 ('Пункт почтовой связи по приему и выдаче почтовых отправлений', 5) ('Строительное управление «ГРОДНОПРОМСТРОЙ-Атом»', 4) ('Государственное учреждение образования "Центр творчества детей и молодежи “Прамень” г. Гродно"', 4)
    	 215 (('building',), 23520) (('building', 'yes'), 22945) (('addr:street',), 19741)
    	 589 (('building',), 23520) (('building', 'yes'), 22945) (('addr:street',), 19741)
    	 0
    	 0
    	 0
    	 0
    description addr:region 318 23032 0 0
    	 1 ('н', 318)
    	 6 ('Минская область', 13907) ('Гродненская область', 8625) ('Смоленская область', 353)
    	 8 (('building',), 318) (('building', 'yes'), 318) (('addr:street',), 306)
    	 39050 (('building',), 318) (('building', 'yes'), 318) (('addr:street',), 306)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber fire_hydrant:housenumber 22953 187 5943 21
    	 32 ('н', 11234) ('1А', 3265) ('7А', 2782)
    	 99 ('1а', 8) ('-Магазин', 6) ('-Мележа', 6)
    	 5883 (('building',), 22545) (('addr:street',), 20524) (('building', 'yes'), 17867)
    	 122 (('building',), 22545) (('addr:street',), 20524) (('building', 'yes'), 17867)
    	 12 ('5А', 1448) ('7А', 1391) ('9А', 1212)
    	 12 ('1а', 8) ('7А', 2) ('17В', 2)
    	 4145 (('building',), 5729) (('addr:street',), 5650) (('building', 'yes'), 3379)
    	 64 (('fire_hydrant:type',), 21) (('fire_hydrant:diameter',), 21) (('name',), 21)
    addr:housenumber artist_name 22538 266 0 0
    	 12 ('н', 20824) ('Н', 1200) ('П', 330)
    	 104 ('Пантелеев В. И.', 14) ('Аляксей Навумчык', 12) ('Игорь Зосимович, Екатерина Зантария, Полина Богданова', 9)
    	 156 (('building',), 22528) (('building', 'yes'), 21989) (('addr:street',), 19009)
    	 482 (('building',), 22528) (('building', 'yes'), 21989) (('addr:street',), 19009)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber destination:backward 22112 327 0 0
    	 13 ('н', 20002) ('Н', 1320) ('ж', 343)
    	 101 ('Мінск', 16) ('Ашмяны;Вiльнюс', 9) ('Станцыя Ясень', 9)
    	 154 (('building',), 22101) (('building', 'yes'), 21626) (('addr:street',), 18665)
    	 222 (('building',), 22101) (('building', 'yes'), 21626) (('addr:street',), 18665)
    	 0
    	 0
    	 0
    	 0
    name was:ref 21774 111 0 0
    	 1 ('Н', 21774)
    	 57 ('Н10351', 6) ('Н3192', 5) ('Н17508', 5)
    	 22 (('building',), 21660) (('building', 'residential'), 13167) (('building', 'yes'), 6213)
    	 76 (('building',), 21660) (('building', 'residential'), 13167) (('building', 'yes'), 6213)
    	 0
    	 0
    	 0
    	 0
    from wikipedia 21707 1411 0 0
    	 69 ('Гомель', 20268) ('Минск', 720) ('Октябрьский', 158)
    	 1216 ('ru:Улица Есенина (Минск)', 22) ('ru:Красноармейская улица (Минск)', 14) ('ru:Улица Маяковского (Минск)', 12)
    	 416 (('to',), 21707) (('route',), 21707) (('name',), 21707)
    	 4578 (('to',), 21707) (('route',), 21707) (('name',), 21707)
    	 0
    	 0
    	 0
    	 0
    description destination 21535 1026 1 15
    	 5 ('н', 21359) ('ж', 110) ('Н', 56)
    	 427 ('Мiнск', 89) ('Мінск', 39) ('Западная Двина', 30)
    	 20 (('building',), 21534) (('building', 'yes'), 21534) (('addr:street',), 20719)
    	 718 (('building',), 21534) (('building', 'yes'), 21534) (('addr:street',), 20719)
    	 1 ('Западная Двина', 1)
    	 1 ('Западная Двина', 15)
    	 12 (('waterway',), 1) (('waterway', 'river'), 1) (('type',), 1)
    	 76 (('type',), 15) (('name',), 15) (('type', 'waterway'), 15)
    addr2:housenumber addr:housenumber 386 21339 10 10039
    	 10 ('4А', 113) ('1А', 107) ('2А', 98)
    	 366 ('1А', 3265) ('2А', 3210) ('4А', 1581)
    	 47 (('addr:postcode',), 386) (('addr:street',), 386) (('addr2:street',), 386)
    	 9116 (('addr:postcode',), 386) (('addr:street',), 386) (('addr2:street',), 386)
    	 10 ('1 к2', 1) ('2А', 1) ('57А', 1)
    	 10 ('1А', 3265) ('2А', 3210) ('4А', 1581)
    	 47 (('addr:postcode',), 10) (('addr:street',), 10) (('addr2:street',), 10)
    	 6068 (('building',), 9693) (('addr:street',), 9561) (('building', 'yes'), 5731)
    addr:housenumber branch 21005 165 0 0
    	 8 ('н', 20550) ('П', 165) ('ж', 147)
    	 81 ('РУП "Минскэнерго"', 45) ('МСК', 7) ('РУП "Могилёвское отделение белорусской железной дороги", могилёвская дистанция электроснабжения', 5)
    	 150 (('building',), 21004) (('building', 'yes'), 20606) (('addr:street',), 17688)
    	 451 (('building',), 21004) (('building', 'yes'), 20606) (('addr:street',), 17688)
    	 0
    	 0
    	 0
    	 0
    name source:population 5 20696 0 0
    	 2 ('т', 4) ('а', 1)
    	 1 ('Белстат', 20696)
    	 3 (('building',), 5) (('building', 'yes'), 4) (('building', 'house'), 1)
    	 22735 (('building',), 5) (('building', 'yes'), 4) (('building', 'house'), 1)
    	 0
    	 0
    	 0
    	 0
    addr:housename source:population 2 20696 0 0
    	 2 ('а', 1) ('т', 1)
    	 1 ('Белстат', 20696)
    	 13 (('building',), 2) (('addr:postcode',), 1) (('addr:street',), 1)
    	 22735 (('building',), 2) (('addr:postcode',), 1) (('addr:street',), 1)
    	 0
    	 0
    	 0
    	 0
    building short_name 20583 4502 2 3
    	 19 ('Н', 14007) ('Т', 2598) ('н', 1408)
    	 1653 ('СТ "Лесная Поляна"', 28) ('СТ "Мелиоратор"', 27) ('СТ "Строитель"', 26)
    	 40 (('name',), 5389) (('name', 'Н'), 2871) (('name', 'Т'), 1299)
    	 4730 (('name',), 5389) (('name', 'Н'), 2871) (('name', 'Т'), 1299)
    	 2 ('ФОК', 1) ('ИМНС', 1)
    	 2 ('ИМНС', 2) ('ФОК', 1)
    	 6 (('building:levels',), 1) (('addr:street',), 1) (('addr:street', 'улица Карла Маркса'), 1)
    	 36 (('name',), 3) (('building:levels',), 2) (('addr:street',), 2)
    addr:city addr:province 20369 15 0 0
    	 5 ('Минск', 18760) ('Брест', 1383) ('Витебск', 194)
    	 7 ('Минская', 4) ('Витебская', 3) ('Минская область', 2)
    	 13134 (('addr:street',), 19591) (('addr:housenumber',), 19146) (('building',), 14526)
    	 80 (('addr:street',), 19591) (('addr:housenumber',), 19146) (('building',), 14526)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city addr:place 20324 37 0 0
    	 2 ('Минск', 20320) ('Могилёв', 4)
    	 21 ('132-й км дороги М4 Минск-Могилёв', 4) ('61-й км дороги М4 Минск-Могилев', 4) ('74-й км дороги М6 Минск-Гродно', 3)
    	 1136 (('fire_hydrant:type',), 20324) (('emergency', 'fire_hydrant'), 20324) (('emergency',), 20324)
    	 251 (('fire_hydrant:type',), 20324) (('emergency', 'fire_hydrant'), 20324) (('emergency',), 20324)
    	 0
    	 0
    	 0
    	 0
    addr:housename opening_hours 20123 309 0 0
    	 9 ('н', 17574) ('Н', 1953) ('к', 245)
    	 120 ('"Работает летом."', 6) ('круглосуточно', 6) ('Пн-Пт 9-18 Сб-Вс 10-17', 6)
    	 110 (('building',), 20108) (('building', 'yes'), 19626) (('addr:street',), 14480)
    	 816 (('building',), 20108) (('building', 'yes'), 19626) (('addr:street',), 14480)
    	 0
    	 0
    	 0
    	 0
    addr:housename heritage:description 20099 537 0 0
    	 17 ('н', 16008) ('Н', 2511) ('к', 651)
    	 105 ('Будынак былой жаночай Марыінскай гімназіі', 12) ('Абеліск ”Мінск горад-герой“', 10) ('Манастырскі корпус', 10)
    	 114 (('building',), 20067) (('building', 'yes'), 19567) (('addr:street',), 14846)
    	 630 (('building',), 20067) (('building', 'yes'), 19567) (('addr:street',), 14846)
    	 0
    	 0
    	 0
    	 0
    to wikipedia 20092 1374 0 0
    	 77 ('Гомель', 19142) ('Минск', 240) ('Октябрьский', 158)
    	 1184 ('ru:Улица Есенина (Минск)', 22) ('ru:Красноармейская улица (Минск)', 14) ('ru:Улица Маяковского (Минск)', 12)
    	 437 (('route',), 20092) (('from',), 20091) (('type',), 20063)
    	 4496 (('route',), 20092) (('from',), 20091) (('type',), 20063)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city addr:region 2033 20004 1016 8
    	 2 ('Минск', 2032) ('Могилёв', 1)
    	 3 ('Минская область', 13907) ('Могилёвская область', 6089) ('Минск', 8)
    	 1136 (('fire_hydrant:type',), 2033) (('emergency', 'fire_hydrant'), 2033) (('emergency',), 2033)
    	 32574 (('fire_hydrant:type',), 2033) (('emergency', 'fire_hydrant'), 2033) (('emergency',), 2033)
    	 1 ('Минск', 1016)
    	 1 ('Минск', 8)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 26 (('building:levels',), 8) (('addr:postcode',), 8) (('addr:street',), 8)
    addr:housenumber destination:forward 19857 331 0 0
    	 10 ('н', 18358) ('Н', 720) ('ж', 490)
    	 88 ('Мiнск', 32) ('12-ы кіламетр МКАД;Слуцк;Гродна;Брэст', 12) ('Мінск', 10)
    	 152 (('building',), 19851) (('building', 'yes'), 19490) (('addr:street',), 16743)
    	 251 (('building',), 19851) (('building', 'yes'), 19490) (('addr:street',), 16743)
    	 0
    	 0
    	 0
    	 0
    addr:city branch 19490 24 0 0
    	 7 ('Минск', 9380) ('Гродно', 5870) ('Брест', 2766)
    	 9 ('РУП "Минскэнерго"', 15) ('РУП "Брестэнерго"', 2) ('Гомельское областное управление', 1)
    	 20406 (('addr:street',), 19016) (('addr:housenumber',), 18674) (('building',), 14874)
    	 122 (('addr:street',), 19016) (('addr:housenumber',), 18674) (('building',), 14874)
    	 0
    	 0
    	 0
    	 0
    building inscription 19425 1567 0 0
    	 18 ('Н', 16583) ('н', 1026) ('дн', 518)
    	 561 ('На этом месте 26 июня 1944 г. в жестокой схватке с фашистскими оккупантами был спасён от взрыва мост группой бойцов под командованием ст. сержанта Блохина Ф. Т., удостоенного за этот подвиг звания Героя Советского Союза.', 8) ('Ситников Я.Т.;Матвеев А.И.;Понарицкий А.Ф.;Буренков Ф.Е.;Мерзляков А.З.;Муратов Комза М.;Маликов Н.И.;Рижиков М.Пр.;Фимков И.И.;Анабаев Н.;Хибубумни Т.', 7) ('БЕЛАРУСАМ ГЕРОЯМ КОСМАСУ. \nПАМЯТНЫ ЗНАК УСТАЛЯВАНЫ Ў\xa0ДНІ ПРАЦЫ 31-ГА МІЖНАРОДНАГА КАНГРЭСУ АССАЦЫЯЦЫІ ЎДЗЕЛЬНІКАУ КАСМІЧНЫХ ПАЛЁТАЎ 9\xa0верасня 2018\xa0гада', 7)
    	 53 (('name',), 4221) (('name', 'Н'), 3399) (('addr:street',), 689)
    	 1243 (('name',), 4221) (('name', 'Н'), 3399) (('addr:street',), 689)
    	 0
    	 0
    	 0
    	 0
    operator minsk_PT:note 9 19335 0 0
    	 3 ('б', 3) ('я', 3) ('е', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 18822) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 303) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 210)
    	 9 (('amenity', 'atm'), 6) (('name',), 6) (('amenity',), 6)
    	 4600 (('amenity', 'atm'), 6) (('name',), 6) (('amenity',), 6)
    	 0
    	 0
    	 0
    	 0
    description minsk_PT:note 168 19335 0 0
    	 3 ('н', 159) ('ж', 6) ('Н', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 18822) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 303) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 210)
    	 8 (('building',), 168) (('building', 'yes'), 168) (('addr:street',), 162)
    	 4600 (('building',), 168) (('building', 'yes'), 168) (('addr:street',), 162)
    	 0
    	 0
    	 0
    	 0
    addr:city designation 19301 7 497 3
    	 6 ('Минск', 18760) ('Городище', 289) ('Каменка', 206)
    	 7 ('Минская киношкола-студия', 1) ('Минские торты', 1) ('Городище', 1)
    	 12432 (('addr:street',), 18526) (('addr:housenumber',), 18050) (('building',), 13668)
    	 61 (('addr:street',), 18526) (('addr:housenumber',), 18050) (('building',), 13668)
    	 3 ('Городище', 289) ('Каменка', 206) ('Козенки', 2)
    	 3 ('Городище', 1) ('Каменка', 1) ('Козенки', 1)
    	 281 (('building',), 489) (('addr:street',), 485) (('addr:housenumber',), 463)
    	 32 (('name',), 3) (('type',), 2) (('int_name',), 2)
    addr:housename brand 19294 9071 7 1242
    	 23 ('н', 16704) ('Н', 1395) ('к', 609)
    	 177 ('Белоруснефть', 3536) ('Беларусбанк', 1064) ('Копеечка', 819)
    	 178 (('building',), 19263) (('building', 'yes'), 18746) (('addr:street',), 13917)
    	 6962 (('building',), 19263) (('building', 'yes'), 18746) (('addr:street',), 13917)
    	 4 ('Белагропромбанк', 3) ('Беларусбанк', 2) ('Белоруснефть', 1)
    	 4 ('Белоруснефть', 884) ('Беларусбанк', 266) ('Белагропромбанк', 81)
    	 53 (('addr:street',), 5) (('addr:housenumber',), 5) (('name',), 5)
    	 3852 (('amenity',), 1227) (('opening_hours',), 1057) (('name',), 995)
    to addr:region 37 19249 1 8
    	 3 ('Гомель', 34) ('Минск', 2) ('Брянск', 1)
    	 4 ('Минская область', 13907) ('Гомельская область', 5204) ('Брянская область', 130)
    	 103 (('public_transport:version', '2'), 37) (('type',), 37) (('from',), 37)
    	 31002 (('public_transport:version', '2'), 37) (('type',), 37) (('from',), 37)
    	 1 ('Минск', 1)
    	 1 ('Минск', 8)
    	 12 (('route',), 1) (('via',), 1) (('public_transport:version', '2'), 1)
    	 26 (('building:levels',), 8) (('addr:postcode',), 8) (('addr:street',), 8)
    from addr:region 43 19249 3 8
    	 3 ('Гомель', 36) ('Минск', 6) ('Брянск', 1)
    	 4 ('Минская область', 13907) ('Гомельская область', 5204) ('Брянская область', 130)
    	 122 (('to',), 43) (('route',), 43) (('type',), 43)
    	 31002 (('to',), 43) (('route',), 43) (('type',), 43)
    	 1 ('Минск', 3)
    	 1 ('Минск', 8)
    	 25 (('to',), 3) (('route',), 3) (('type',), 3)
    	 26 (('building:levels',), 8) (('addr:postcode',), 8) (('addr:street',), 8)
    destination:backward addr:region 6 19119 1 8
    	 2 ('Гомель', 4) ('Минск', 2)
    	 3 ('Минская область', 13907) ('Гомельская область', 5204) ('Минск', 8)
    	 32 (('surface', 'asphalt'), 6) (('maxaxleload',), 6) (('surface',), 6)
    	 30857 (('surface', 'asphalt'), 6) (('maxaxleload',), 6) (('surface',), 6)
    	 1 ('Минск', 1)
    	 1 ('Минск', 8)
    	 18 (('maxspeed', '90'), 1) (('destination:forward', 'Кобрын;Пiнск'), 1) (('surface',), 1)
    	 26 (('building:levels',), 8) (('addr:postcode',), 8) (('addr:street',), 8)
    ref destination:ref 18949 153 7174 52
    	 37 ('М1', 10370) ('Р2', 1515) ('М6', 1261)
    	 25 ('М6', 30) ('Р5', 16) ('Н6266', 15)
    	 790 (('highway',), 18850) (('surface',), 18681) (('surface', 'asphalt'), 18264)
    	 90 (('highway',), 18850) (('surface',), 18681) (('surface', 'asphalt'), 18264)
    	 19 ('М1', 2074) ('М6', 1261) ('М5', 1230)
    	 19 ('М6', 15) ('Р5', 8) ('М1', 4)
    	 671 (('highway',), 7155) (('surface',), 7074) (('maxaxleload',), 6914)
    	 65 (('oneway', 'yes'), 52) (('oneway',), 52) (('highway',), 52)
    name addr:full 18087 884 1 1
    	 131 ('н', 11080) ('Н', 1910) ('Дом культуры', 615)
    	 50 ('д. Рудишки, Ошмянский район, Гродненская область', 136) ('д. Яново, Борисовский район, Минская область', 108) ('пересечение а/д М-3 Минск-Витебск и Р111 Бешенковичи-Чашники', 32)
    	 1912 (('building',), 15798) (('building', 'yes'), 13026) (('building', 'residential'), 2125)
    	 359 (('building',), 15798) (('building', 'yes'), 13026) (('building', 'residential'), 2125)
    	 1 ('Суражское шоссе, 9-й км', 1)
    	 1 ('Суражское шоссе, 9-й км', 1)
    	 4 (('building', 'yes'), 1) (('building',), 1) (('building:levels',), 1)
    	 12 (('name', 'Витебский областной клинический центр психиатрии и наркологии'), 1) (('healthcare:speciality', 'psychiatry'), 1) (('contact:website',), 1)
    building source 3242 17798 2 1
    	 10 ('Н', 3059) ('н', 100) ('р', 49)
    	 69 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 8596) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 3306) ('Национальное кадастровое агентство nca.by', 3282)
    	 37 (('name',), 673) (('name', 'Н'), 627) (('building:levels',), 78)
    	 1114 (('name',), 673) (('name', 'Н'), 627) (('building:levels',), 78)
    	 1 ('Магазин', 2)
    	 1 ('Магазин', 1)
    	 19 (('name',), 2) (('building:levels',), 2) (('addr:street',), 2)
    	 8 (('designation', 'Магазин мебели'), 1) (('shop', 'supermarket'), 1) (('designation',), 1)
    name related_law 17638 854 0 0
    	 51 ('н', 13850) ('М', 728) ('п', 459)
    	 50 ('Постановление Совета Министров РБ от 27.12.2007 № 1833', 60) ('Постановление Совета Министров РБ 27.12.2007 № 1833', 60) ('Постановление Совета Министров РБ от 04.02.2015 № 71', 48)
    	 637 (('building',), 16552) (('building', 'yes'), 14909) (('building', 'residential'), 1293)
    	 281 (('building',), 16552) (('building', 'yes'), 14909) (('building', 'residential'), 1293)
    	 0
    	 0
    	 0
    	 0
    name_old addr:street 19 17613 3 17329
    	 2 ('Набережная улица', 13) ('Школьная улица', 6)
    	 16 ('Школьная улица', 11201) ('Набережная улица', 6128) ('1-я Набережная улица', 102)
    	 10 (('source', 'http://www.novopolotsk.by/content/view/8414/176/'), 19) (('name',), 19) (('source',), 19)
    	 2362 (('source', 'http://www.novopolotsk.by/content/view/8414/176/'), 19) (('name',), 19) (('source',), 19)
    	 2 ('Школьная улица', 2) ('Набережная улица', 1)
    	 2 ('Школьная улица', 11201) ('Набережная улица', 6128)
    	 10 (('source', 'http://www.novopolotsk.by/content/view/8414/176/'), 3) (('name',), 3) (('source',), 3)
    	 2352 (('building',), 17099) (('addr:housenumber',), 16299) (('building', 'yes'), 10476)
    official_short_type description 17345 472 147 3
    	 15 ('ТП', 7380) ('Ф', 4544) ('ПС', 2912)
    	 237 ('Фирменный магазин Mark Formelle', 81) ('Федоровка - Нисимковичи до а/д Р-38', 21) ('Фаниполь - Победное', 20)
    	 2234 (('power',), 16672) (('voltage',), 15497) (('ref',), 13380)
    	 1260 (('power',), 16672) (('voltage',), 15497) (('ref',), 13380)
    	 2 ('ЦТП', 111) ('КНС', 36)
    	 2 ('ЦТП', 2) ('КНС', 1)
    	 249 (('ref',), 121) (('building',), 104) (('building', 'service'), 101)
    	 12 (('building', 'yes'), 3) (('building',), 3) (('roof:shape', 'gabled'), 1)
    description addr:subdistrict 17194 6005 0 0
    	 8 ('н', 17066) ('ж', 80) ('Н', 26)
    	 371 ('Кобринский р-н', 634) ('Остринский сельский Совет', 162) ('Рожанковский сельский Совет', 140)
    	 33 (('building',), 17184) (('building', 'yes'), 17184) (('addr:street',), 16534)
    	 13399 (('building',), 17184) (('building', 'yes'), 17184) (('addr:street',), 16534)
    	 0
    	 0
    	 0
    	 0
    addr:housename artist_name 16927 701 0 0
    	 15 ('н', 13224) ('Н', 2790) ('к', 532)
    	 131 ('А.Чумаков', 60) ('Алёна Василькович', 24) ('А.Павлючук', 21)
    	 110 (('building',), 16853) (('building', 'yes'), 16428) (('addr:street',), 12542)
    	 572 (('building',), 16853) (('building', 'yes'), 16428) (('addr:street',), 12542)
    	 0
    	 0
    	 0
    	 0
    name fire_hydrant:housenumber 16865 825 363 58
    	 174 ('н', 11357) ('Н', 1146) ('Магазин', 534)
    	 148 ('Автомойка', 54) ('131 -Речицатекстиль', 30) ('-Кострамы', 21)
    	 1730 (('building',), 15250) (('building', 'yes'), 12819) (('building', 'residential'), 1673)
    	 137 (('building',), 15250) (('building', 'yes'), 12819) (('building', 'residential'), 1673)
    	 37 ('Стройматериалы', 96) ('Автомойка', 64) ('Пищеблок', 37)
    	 37 ('1а', 8) ('Автомойка', 6) ('4а', 5)
    	 457 (('building',), 165) (('shop',), 120) (('building', 'yes'), 89)
    	 77 (('fire_hydrant:type',), 58) (('fire_hydrant:diameter',), 58) (('name',), 58)
    addr:housename destination:backward 16681 469 0 0
    	 13 ('н', 12702) ('Н', 3069) ('к', 476)
    	 108 ('Мінск', 24) ('Ванькоўшчына;Спарткомплекс "Стайкі"', 12) ('Калодзішчы;Заслаўе', 12)
    	 92 (('building',), 16650) (('building', 'yes'), 16236) (('addr:street',), 12413)
    	 234 (('building',), 16650) (('building', 'yes'), 16236) (('addr:street',), 12413)
    	 0
    	 0
    	 0
    	 0
    official_short_type short_name 16546 107 0 0
    	 6 ('ПС', 14924) ('ТП', 820) ('Ф', 768)
    	 99 ('ФАП', 3) ('СТ "Флора"', 3) ('РТПС "Теляки"', 2)
    	 1109 (('power',), 16455) (('voltage',), 16241) (('power', 'substation'), 15687)
    	 612 (('power',), 16455) (('voltage',), 16241) (('power', 'substation'), 15687)
    	 0
    	 0
    	 0
    	 0
    official_short_type addr:street 16427 11390 0 0
    	 6 ('ВЛ', 9535) ('Ф', 5280) ('ПС', 1456)
    	 177 ('улица Фрунзе', 2393) ('улица Франциска Скорины', 1149) ('улица 50 лет ВЛКСМ', 776)
    	 1648 (('power',), 16285) (('voltage',), 16075) (('cables',), 14760)
    	 3290 (('power',), 16285) (('voltage',), 16075) (('cables',), 14760)
    	 0
    	 0
    	 0
    	 0
    addr:unit operator 2631 16344 1 1
    	 2 ('А', 1511) ('Б', 1120)
    	 2361 ('ОАО "Гроднооблавтотранс"', 1028) ('ОАО «Витебскоблавтотранс»', 819) ('Беларусбанк', 770)
    	 23 (('addr:street',), 2631) (('addr:housenumber',), 2631) (('addr:city',), 2631)
    	 21354 (('addr:street',), 2631) (('addr:housenumber',), 2631) (('addr:city',), 2631)
    	 1 ('А', 1)
    	 1 ('А', 1)
    	 8 (('addr:street',), 1) (('addr:housenumber', '80'), 1) (('building',), 1)
    	 12 (('to',), 1) (('route',), 1) (('type',), 1)
    fire_hydrant:city inscription 16257 17 0 0
    	 2 ('Минск', 16256) ('Могилёв', 1)
    	 17 ('Памятный знак, посвящённый армянским воинам, принимавшим участие в боях на территории г. Могилёва и Могилёвской обл. в годы ВОВ 1941 - 1945 г.', 1) ('ДОТ №44 9-го батальонного района обороны Минского укрепрайона, "Линия Сталина", ок. 1932 г.', 1) ('ДОТ №45 9-го батальонного района обороны Минского укрепрайона, "Линия Сталина", ок. 1932 г.', 1)
    	 1136 (('fire_hydrant:type',), 16257) (('emergency', 'fire_hydrant'), 16257) (('emergency',), 16257)
    	 48 (('fire_hydrant:type',), 16257) (('emergency', 'fire_hydrant'), 16257) (('emergency',), 16257)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city note 16256 104 0 0
    	 1 ('Минск', 16256)
    	 16 ('Внешняя нода для согласования с картой Минска', 45) ('административная граница г. Минска', 28) ('Решение Минский облсовет 226 08.09.2017 О некоторых вопросах административно-территориального устройства Минской области', 12)
    	 1120 (('emergency', 'fire_hydrant'), 16256) (('fire_hydrant:type',), 16256) (('emergency',), 16256)
    	 192 (('emergency', 'fire_hydrant'), 16256) (('fire_hydrant:type',), 16256) (('emergency',), 16256)
    	 0
    	 0
    	 0
    	 0
    via addr:street 79 16163 7 5
    	 14 ('Гагарина', 16) ('Славгород', 10) ('Депо', 10)
    	 44 ('улица Гагарина', 7725) ('Красноармейская улица', 4811) ('улица Луначарского', 722)
    	 99 (('to',), 79) (('public_transport:version', '2'), 79) (('type',), 79)
    	 3057 (('to',), 79) (('public_transport:version', '2'), 79) (('type',), 79)
    	 3 ('Автовокзал', 4) ('Гагарина', 2) ('Больничный городок', 1)
    	 3 ('Гагарина', 3) ('Больничный городок', 1) ('Автовокзал', 1)
    	 42 (('to',), 7) (('type',), 7) (('public_transport:version', '2'), 7)
    	 19 (('name',), 3) (('building',), 2) (('addr:city',), 2)
    was:addr:housenumber addr:housenumber 366 16144 9 7303
    	 9 ('1А', 107) ('3А', 87) ('1Б', 46)
    	 365 ('1А', 3265) ('3А', 1618) ('11А', 1144)
    	 28 (('was:addr:street',), 356) (('was:addr:street', 'улица Девятовка'), 354) (('was:building',), 354)
    	 7904 (('was:addr:street',), 356) (('was:addr:street', 'улица Девятовка'), 354) (('was:building',), 354)
    	 9 ('127А', 1) ('19А', 1) ('1Б', 1)
    	 9 ('1А', 3265) ('3А', 1618) ('1Б', 911)
    	 28 (('was:addr:street',), 8) (('building:levels',), 7) (('was:addr:street', 'улица Девятовка'), 7)
    	 4684 (('building',), 7056) (('addr:street',), 6963) (('building', 'yes'), 4128)
    addr:housename was:ref 15903 111 0 0
    	 1 ('Н', 15903)
    	 57 ('Н10351', 6) ('Н3192', 5) ('Н17508', 5)
    	 29 (('building',), 15789) (('building', 'yes'), 15618) (('addr:street',), 14364)
    	 76 (('building',), 15789) (('building', 'yes'), 15618) (('addr:street',), 14364)
    	 0
    	 0
    	 0
    	 0
    description source 2720 15553 3 2
    	 8 ('н', 2650) ('ж', 30) ('Н', 19)
    	 55 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 6447) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 3306) ('Национальное кадастровое агентство nca.by', 3282)
    	 32 (('building',), 2717) (('building', 'yes'), 2716) (('addr:street',), 2602)
    	 1056 (('building',), 2717) (('building', 'yes'), 2716) (('addr:street',), 2602)
    	 2 ('Магазин', 2) ('Ремонт одежды', 1)
    	 2 ('Магазин', 1) ('Ремонт одежды', 1)
    	 10 (('shop',), 2) (('name',), 2) (('shop', 'convenience'), 1)
    	 11 (('name',), 2) (('designation', 'Магазин мебели'), 1) (('shop', 'supermarket'), 1)
    addr:housename full_name 15377 408 0 0
    	 25 ('н', 13746) ('к', 434) ('ж', 420)
    	 85 ('Могилёвский аэроклуб имени А.М. Кулагина', 8) ('Филиал «Завод Химволокно» ОАО «Гродно Азот»', 8) ('Мядельский районный отдел Государственного комитета судебных экспертиз Республики Беларусь', 8)
    	 179 (('building',), 15358) (('building', 'yes'), 14962) (('addr:street',), 11009)
    	 589 (('building',), 15358) (('building', 'yes'), 14962) (('addr:street',), 11009)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber owner 15338 361 0 0
    	 11 ('н', 13974) ('Н', 720) ('П', 450)
    	 63 ('ОАО «Белорусский банк развития и реконструкции «Белинвестбанк»', 141) ('ОАО «АСБ Беларусбанк»', 30) ('ОАО «Приорбанк»', 26)
    	 153 (('building',), 15332) (('building', 'yes'), 14859) (('addr:street',), 12899)
    	 595 (('building',), 15332) (('building', 'yes'), 14859) (('addr:street',), 12899)
    	 0
    	 0
    	 0
    	 0
    ref addr:subdistrict 1520 15280 0 0
    	 13 ('С', 741) ('М', 172) ('В', 128)
    	 757 ('Михалишковский сельский Совет', 214) ('Рожанковский сельский Совет', 210) ('Василишковский сельский Совет', 206)
    	 51 (('aeroway', 'taxiway'), 933) (('aeroway',), 933) (('level', '0'), 222)
    	 24233 (('aeroway', 'taxiway'), 933) (('aeroway',), 933) (('level', '0'), 222)
    	 0
    	 0
    	 0
    	 0
    name network 15256 8950 2368 303
    	 99 ('н', 8033) ('Н', 2292) ('Беларусбанк', 1045)
    	 67 ('Барановичское отделение', 3472) ('Минский метрополитен', 3144) ('Брестское отделение', 350)
    	 2674 (('building',), 12389) (('building', 'yes'), 9529) (('building', 'residential'), 2368)
    	 886 (('building',), 12389) (('building', 'yes'), 9529) (('building', 'residential'), 2368)
    	 21 ('Беларусбанк', 1045) ('Белагропромбанк', 380) ('Белинвестбанк', 222)
    	 21 ('Минский метрополитен', 262) ('Беларусбанк', 9) ('Борисов', 4)
    	 2153 (('amenity',), 2192) (('amenity', 'bank'), 1214) (('int_name',), 1188)
    	 368 (('name',), 283) (('railway',), 262) (('colour',), 255)
    addr:district official_name 15102 81 0 0
    	 25 ('Лидский район', 5590) ('Браславский район', 1008) ('Чашникский район', 818)
    	 54 ('Домановичи - Мироненки - Гр. Светлогорского района', 15) ('Костюковка - Н.Жизнь', 6) ('Светлогорск - Сосновый Бор', 5)
    	 18478 (('name',), 15094) (('addr:region',), 15087) (('int_name',), 15033)
    	 313 (('name',), 15094) (('addr:region',), 15087) (('int_name',), 15033)
    	 0
    	 0
    	 0
    	 0
    ref addr:full 14428 144 0 0
    	 19 ('М1', 10370) ('М6', 2522) ('М3', 966)
    	 48 ('пересечение а/д М-3 Минск-Витебск и Р111 Бешенковичи-Чашники', 16) ('д. Рудишки, Ошмянский район, Гродненская область', 16) ('д. Яново, Борисовский район, Минская область', 12)
    	 427 (('highway',), 14243) (('surface',), 14150) (('surface', 'asphalt'), 14086)
    	 352 (('highway',), 14243) (('surface',), 14150) (('surface', 'asphalt'), 14086)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber related_law 14416 204 0 0
    	 9 ('н', 13700) ('П', 465) ('Н', 120)
    	 50 ('Постановление Совета Министров РБ от 27.12.2007 № 1833', 20) ('Постановление Совета Министров РБ 27.12.2007 № 1833', 20) ('Постановление Совета Министров РБ от 04.02.2015 № 71', 16)
    	 151 (('building',), 14415) (('building', 'yes'), 13951) (('addr:street',), 12107)
    	 281 (('building',), 14415) (('building', 'yes'), 13951) (('addr:street',), 12107)
    	 0
    	 0
    	 0
    	 0
    addr:housename destination:forward 14240 525 0 0
    	 15 ('н', 11658) ('Н', 1674) ('к', 427)
    	 97 ('Мiнск', 48) ('12-ы кіламетр МКАД;Слуцк;Гродна;Брэст', 24) ('Барановичи', 15)
    	 96 (('building',), 14219) (('building', 'yes'), 13854) (('addr:street',), 10409)
    	 264 (('building',), 14219) (('building', 'yes'), 13854) (('addr:street',), 10409)
    	 0
    	 0
    	 0
    	 0
    name protection_title 14058 1372 3 8
    	 35 ('н', 11634) ('Н', 764) ('к', 410)
    	 42 ('Республиканский ландшафтный заказник', 242) ('Памятник природы', 224) ('Республиканский биологический заказник', 135)
    	 186 (('building',), 13718) (('building', 'yes'), 12212) (('building', 'residential'), 1209)
    	 582 (('building',), 13718) (('building', 'yes'), 12212) (('building', 'residential'), 1209)
    	 2 ('Ботанический заказник', 2) ('Заказник', 1)
    	 2 ('Заказник', 5) ('Ботанический заказник', 3)
    	 11 (('bus', 'yes'), 2) (('bus',), 2) (('public_transport',), 2)
    	 38 (('name',), 8) (('leisure',), 8) (('boundary', 'protected_area'), 8)
    network addr:region 4 13915 2 8
    	 1 ('Минск', 4)
    	 2 ('Минская область', 13907) ('Минск', 8)
    	 17 (('minsk_PT:note',), 4) (('shelter', 'yes'), 4) (('shelter',), 4)
    	 21490 (('minsk_PT:note',), 4) (('shelter', 'yes'), 4) (('shelter',), 4)
    	 1 ('Минск', 2)
    	 1 ('Минск', 8)
    	 17 (('minsk_PT:note',), 2) (('shelter', 'yes'), 2) (('shelter',), 2)
    	 26 (('building:levels',), 8) (('addr:postcode',), 8) (('addr:street',), 8)
    name via 13902 606 193 56
    	 126 ('н', 9418) ('Н', 764) ('к', 430)
    	 65 ('пл. Ленина', 40) ('Автовокзал', 32) ('Центральный вокзал', 26)
    	 1398 (('building',), 11762) (('building', 'yes'), 10014) (('building', 'residential'), 1415)
    	 316 (('building',), 11762) (('building', 'yes'), 10014) (('building', 'residential'), 1415)
    	 26 ('Автовокзал', 44) ('ТЭЦ', 22) ('Гагарина', 10)
    	 26 ('пл. Ленина', 5) ('Лоев', 4) ('Чечерск', 4)
    	 312 (('public_transport',), 110) (('highway',), 83) (('highway', 'bus_stop'), 81)
    	 182 (('to',), 56) (('public_transport:version', '2'), 56) (('type',), 56)
    addr:city destination:backward 13845 57 9984 20
    	 16 ('Минск', 9380) ('Гомель', 4102) ('Орша', 153)
    	 33 ('Мінск', 8) ('Магілёў;Брэст;Гомель;Масква', 6) ('Брэст', 5)
    	 13620 (('addr:street',), 13299) (('addr:housenumber',), 12973) (('building',), 9699)
    	 135 (('addr:street',), 13299) (('addr:housenumber',), 12973) (('building',), 9699)
    	 6 ('Минск', 9380) ('Гомель', 586) ('Магілёў', 6)
    	 6 ('Мінск', 8) ('Брэст', 5) ('Гомель', 4)
    	 13480 (('addr:street',), 9589) (('addr:housenumber',), 9355) (('building',), 6992)
    	 75 (('surface',), 20) (('surface', 'asphalt'), 20) (('destination:forward',), 20)
    description fixme 13703 1005 12 3
    	 29 ('н', 13303) ('ж', 224) ('улица', 56)
    	 270 ('положение', 78) ('расположение', 72) ('положение/адрес', 68)
    	 118 (('building',), 13613) (('building', 'yes'), 13598) (('addr:street',), 13074)
    	 1528 (('building',), 13613) (('building', 'yes'), 13598) (('addr:street',), 13074)
    	 3 ('улица', 7) ('Мастерские', 4) ('Чаша заброшенного фонтана', 1)
    	 3 ('Чаша заброшенного фонтана', 1) ('Мастерские', 1) ('улица', 1)
    	 26 (('highway',), 7) (('highway', 'residential'), 5) (('building',), 4)
    	 12 (('description',), 1) (('abandoned:amenity', 'fountain'), 1) (('description', 'Чаша заброшенного фонтана'), 1)
    addr:housename branch 13650 287 0 0
    	 14 ('н', 13050) ('Н', 279) ('к', 126)
    	 86 ('РУП "Минскэнерго"', 45) ('МСК', 14) ('Барановичские электросети', 10)
    	 114 (('building',), 13648) (('building', 'yes'), 13325) (('addr:street',), 9558)
    	 482 (('building',), 13648) (('building', 'yes'), 13325) (('addr:street',), 9558)
    	 0
    	 0
    	 0
    	 0
    addr:housename gomel_PT:note 478 13398 0 0
    	 6 ('Н', 279) ('н', 174) ('ж', 20)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 13398)
    	 83 (('building',), 476) (('building', 'yes'), 468) (('addr:street',), 396)
    	 859 (('building',), 476) (('building', 'yes'), 468) (('addr:street',), 396)
    	 0
    	 0
    	 0
    	 0
    addr:city addr:subdistrict 13329 12038 92 102
    	 115 ('Совет', 8107) ('Гомель', 586) ('Сопоцкин', 371)
    	 745 ('Кобринский р-н', 634) ('Октябрьский сельский Совет', 243) ('Первомайский сельский Совет', 192)
    	 3998 (('addr:housenumber',), 12138) (('building',), 12039) (('building', 'house'), 9319)
    	 24462 (('addr:housenumber',), 12138) (('building',), 12039) (('building', 'house'), 9319)
    	 16 ('Блонский сельский Совет', 46) ('Дашковский сельский Совет', 15) ('Вендорожский сельский Совет', 13)
    	 16 ('Щомыслицкий сельский Совет', 14) ('Блонский сельский Совет', 12) ('Заводскослободский сельский Совет', 11)
    	 195 (('addr:housenumber',), 57) (('building',), 54) (('addr:street',), 53)
    	 271 (('name',), 102) (('place',), 101) (('int_name',), 98)
    addr:housenumber designation 12954 139 2 1
    	 15 ('н', 12056) ('Н', 360) ('ж', 196)
    	 62 ('Нужные мелочи', 4) ('Комбинат Нетканых Материалов', 4) ('Пьяный лес', 4)
    	 181 (('building',), 12937) (('building', 'yes'), 12620) (('addr:street',), 10911)
    	 291 (('building',), 12937) (('building', 'yes'), 12620) (('addr:street',), 10911)
    	 1 ('АТС', 2)
    	 1 ('АТС', 1)
    	 5 (('addr:street',), 2) (('building',), 2) (('building', 'yes'), 2)
    	 2 (('amenity',), 1) (('amenity', 'telephone'), 1)
    operator addr:subdistrict 941 12886 0 0
    	 14 ('е', 763) ('б', 91) ('я', 58)
    	 764 ('Кобринский р-н', 634) ('Октябрьский сельский Совет', 243) ('Ворнянский сельский Совет', 162)
    	 99 (('name',), 878) (('name', 'Складской комплекс «Северный»'), 763) (('landuse',), 763)
    	 24768 (('name',), 878) (('name', 'Складской комплекс «Северный»'), 763) (('landuse',), 763)
    	 0
    	 0
    	 0
    	 0
    building addr:subdistrict 5584 12769 0 0
    	 11 ('Н', 4186) ('н', 644) ('р', 304)
    	 572 ('Кобринский р-н', 1902) ('Тарновский сельский Совет', 174) ('Ворнянский сельский Совет', 162)
    	 30 (('name',), 1188) (('name', 'Н'), 858) (('building:levels',), 333)
    	 19395 (('name',), 1188) (('name', 'Н'), 858) (('building:levels',), 333)
    	 0
    	 0
    	 0
    	 0
    building:levels name 4773 12534 2 389
    	 2 ('Н', 4764) ('2А', 9)
    	 4771 ('Новая улица', 798) ('Набережная улица', 597) ('Н', 382)
    	 5 (('building',), 4773) (('building', 'yes'), 4764) (('addr:street',), 9)
    	 11055 (('building',), 4773) (('building', 'yes'), 4764) (('addr:street',), 9)
    	 2 ('2А', 1) ('Н', 1)
    	 2 ('Н', 382) ('2А', 7)
    	 5 (('building',), 2) (('addr:street',), 1) (('addr:street', 'Центральная улица'), 1)
    	 34 (('building',), 387) (('building', 'residential'), 232) (('building', 'yes'), 112)
    destination addr:street 747 12486 1 33
    	 33 ('Гомель', 320) ('Днепр', 189) ('Могилёв', 33)
    	 157 ('Минская улица', 2295) ('Брестская улица', 1183) ('Днепровская улица', 1087)
    	 252 (('highway',), 414) (('oneway', 'yes'), 413) (('oneway',), 413)
    	 3157 (('highway',), 414) (('oneway', 'yes'), 413) (('oneway',), 413)
    	 1 ('МКАД', 1)
    	 1 ('МКАД', 33)
    	 10 (('surface', 'asphalt'), 1) (('hgv', 'yes'), 1) (('maxaxleload',), 1)
    	 134 (('addr:housenumber',), 29) (('building',), 28) (('building', 'service'), 20)
    addr:housenumber addr:full 12087 172 0 0
    	 14 ('н', 10960) ('Н', 600) ('ж', 245)
    	 49 ('д. Яново, Борисовский район, Минская область', 18) ('д. Рудишки, Ошмянский район, Гродненская область', 16) ('Псковская область, Себежский район, д.Долосцы', 10)
    	 161 (('building',), 12082) (('building', 'yes'), 11770) (('addr:street',), 10181)
    	 359 (('building',), 12082) (('building', 'yes'), 11770) (('addr:street',), 10181)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber building 12060 897 792 454
    	 34 ('н', 9864) ('Н', 840) ('П', 510)
    	 93 ('КЖ', 260) ('КН', 208) ('Н', 161)
    	 286 (('building',), 12040) (('building', 'yes'), 11558) (('addr:street',), 10133)
    	 211 (('building',), 12040) (('building', 'yes'), 11558) (('addr:street',), 10133)
    	 20 ('н', 274) ('КН', 150) ('кн', 129)
    	 20 ('Н', 161) ('КЖ', 130) ('КН', 104)
    	 241 (('building',), 784) (('building', 'yes'), 757) (('addr:street',), 666)
    	 138 (('name',), 191) (('building:levels',), 40) (('name', 'Н'), 33)
    addr:city owner 11982 6 0 0
    	 5 ('Гродно', 11740) ('Пинск', 130) ('Орша', 51)
    	 6 ('РУП "Гродноавтодор", ДЭУ-54, ЛДД-543', 1) ('РУП "Гродноавтодор" ДЭУ-52 ЛДД-523', 1) ('Торговое унитарное предприятие Глубокоеторг', 1)
    	 8529 (('addr:street',), 11855) (('addr:housenumber',), 11671) (('building',), 9432)
    	 49 (('addr:street',), 11855) (('addr:housenumber',), 11671) (('building',), 9432)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber protection_title 11900 365 0 0
    	 8 ('н', 11508) ('Н', 240) ('ж', 49)
    	 42 ('Памятник природы', 112) ('Республиканский ландшафтный заказник', 44) ('Республиканский биологический заказник', 15)
    	 151 (('building',), 11898) (('building', 'yes'), 11687) (('addr:street',), 10045)
    	 582 (('building',), 11898) (('building', 'yes'), 11687) (('addr:street',), 10045)
    	 0
    	 0
    	 0
    	 0
    designation operator 1190 11739 8 220
    	 16 ('б', 1091) ('парк', 49) ('Лавка', 20)
    	 1134 ('КТУП «Гомельоблпассажиртранс»', 1665) ('ОАО "Гроднооблавтотранс"', 1028) ('ОАО «Витебскоблавтотранс»', 819)
    	 79 (('name',), 1158) (('addr:street',), 1093) (('building',), 1093)
    	 13632 (('name',), 1158) (('addr:street',), 1093) (('building',), 1093)
    	 7 ('Школа-интернат', 2) ('Минская киношкола-студия', 1) ('БПС-Сбербанк', 1)
    	 7 ('БПС-Сбербанк', 188) ('РМЗ', 21) ('МЧС', 7)
    	 37 (('name',), 6) (('amenity',), 5) (('building',), 3)
    	 215 (('amenity',), 196) (('amenity', 'atm'), 171) (('name',), 86)
    type wikipedia 11375 11706 0 0
    	 3 ('ц', 6950) ('ель', 3345) ('Дуб', 1080)
    	 9874 ('ru:Улица Есенина (Минск)', 22) ('be:Асоцка', 18) ('be:Вуліца Чалюскінцаў (Магілёў)', 15)
    	 3 (('natural',), 11375) (('natural', 'wetland'), 6950) (('natural', 'tree'), 4425)
    	 26926 (('natural',), 11375) (('natural', 'wetland'), 6950) (('natural', 'tree'), 4425)
    	 0
    	 0
    	 0
    	 0
    name subject:wikipedia 11489 388 0 0
    	 96 ('н', 8587) ('Н', 764) ('к', 380)
    	 50 ('ru:Ромашкин, Тимофей Терентьевич', 12) ('be:Міхаіл_Міхайлавіч_Рудкоўскі', 12) ('ru:Янка Купала', 11)
    	 664 (('building',), 10916) (('building', 'yes'), 9299) (('building', 'residential'), 1255)
    	 238 (('building',), 10916) (('building', 'yes'), 9299) (('building', 'residential'), 1255)
    	 0
    	 0
    	 0
    	 0
    hamlet addr:street 374 11488 0 0
    	 1 ('Октябрь', 374)
    	 17 ('Октябрьская улица', 10398) ('Октябрьский переулок', 527) ('2-й Октябрьский переулок', 138)
    	 29 (('addr:street',), 374) (('building', 'yes'), 374) (('building',), 374)
    	 2081 (('addr:street',), 374) (('building', 'yes'), 374) (('building',), 374)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber addr:flats 11432 51 1 1
    	 17 ('1А', 6530) ('5А', 1448) ('6А', 1393)
    	 12 ('61А;61-74', 20) ('19-27;7а;8а;9а', 7) ('61-126В', 6)
    	 5299 (('building',), 11052) (('addr:street',), 10894) (('building', 'yes'), 6503)
    	 17 (('building',), 11052) (('addr:street',), 10894) (('building', 'yes'), 6503)
    	 1 ('1Н', 1)
    	 1 ('1Н', 1)
    	 4 (('addr:street',), 1) (('building',), 1) (('building', 'house'), 1)
    	 4 (('entrance',), 1) (('entrance', 'yes'), 1) (('access', 'customers'), 1)
    building destination 11242 2358 0 0
    	 11 ('Н', 9016) ('н', 806) ('р', 401)
    	 585 ('Мiнск', 178) ('Мінск', 78) ('Брэст', 45)
    	 31 (('name',), 2580) (('name', 'Н'), 1848) (('addr:street',), 489)
    	 905 (('name',), 2580) (('name', 'Н'), 1848) (('addr:street',), 489)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber gomel_PT:note 446 11165 0 0
    	 5 ('н', 274) ('Н', 120) ('ж', 49)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 11165)
    	 131 (('building',), 445) (('building', 'yes'), 437) (('addr:street',), 377)
    	 859 (('building',), 445) (('building', 'yes'), 437) (('addr:street',), 377)
    	 0
    	 0
    	 0
    	 0
    addr:housename owner 11132 852 2 1
    	 14 ('н', 8874) ('Н', 1674) ('к', 343)
    	 67 ('ОАО «Белорусский банк развития и реконструкции «Белинвестбанк»', 235) ('ОАО «АСБ Беларусбанк»', 150) ('ОАО «Белагропромбанк»', 60)
    	 129 (('building',), 11096) (('building', 'yes'), 10820) (('addr:street',), 8228)
    	 620 (('building',), 11096) (('building', 'yes'), 10820) (('addr:street',), 8228)
    	 1 ('Беларусбанк', 2)
    	 1 ('Беларусбанк', 1)
    	 14 (('addr:street',), 2) (('building', 'yes'), 2) (('building',), 2)
    	 4 (('amenity', 'bureau_de_change'), 1) (('amenity',), 1) (('name', 'Беларусбанк'), 1)
    addr:place short_name 11023 271 2970 40
    	 101 ('Горни', 1010) ('СТ "Малинники"', 815) ('Старое Село', 766)
    	 179 ('СТ "Лесное"', 20) ('СТ "Дружба"', 11) ('СТ "Связист"', 7)
    	 902 (('building',), 10550) (('addr:housenumber',), 7973) (('building', 'house'), 4400)
    	 528 (('building',), 10550) (('addr:housenumber',), 7973) (('building', 'house'), 4400)
    	 15 ('СТ "Малинники"', 815) ('СТ "Шарик"', 634) ('СТ "Электрик"', 291)
    	 15 ('СТ "Лесное"', 10) ('СТ "Связист"', 7) ('СТ "Электрик"', 4)
    	 231 (('building',), 2960) (('building', 'yes'), 2134) (('building', 'bungalow'), 737)
    	 85 (('name',), 40) (('place',), 38) (('place', 'allotments'), 38)
    type addr:subdistrict 839 10862 0 0
    	 3 ('ель', 756) ('ц', 71) ('Дуб', 12)
    	 760 ('Сопоцкинский сельский Совет', 132) ('Белицкий сельский Совет', 128) ('Переганцевский сельский Совет', 112)
    	 3 (('natural',), 839) (('natural', 'tree'), 768) (('natural', 'wetland'), 71)
    	 24328 (('natural',), 839) (('natural', 'tree'), 768) (('natural', 'wetland'), 71)
    	 0
    	 0
    	 0
    	 0
    operator source 903 10635 3 3
    	 17 ('Беларусбанк', 770) ('е', 51) ('б', 22)
    	 66 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 4298) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 3306) ('Национальное кадастровое агентство nca.by', 1094)
    	 751 (('amenity',), 813) (('amenity', 'atm'), 560) (('name',), 489)
    	 1112 (('amenity',), 813) (('amenity', 'atm'), 560) (('name',), 489)
    	 3 ('ИП Пашкевич А.В.', 1) ('Автотракмоторс', 1) ('Владелец', 1)
    	 3 ('ИП Пашкевич А.В.', 1) ('Автотракмоторс', 1) ('Владелец', 1)
    	 25 (('name',), 3) (('shop',), 2) (('addr:postcode', '231300'), 1)
    	 38 (('name',), 3) (('addr:postcode',), 3) (('addr:street',), 3)
    name brand:wikipedia 10616 3478 22 1
    	 79 ('н', 6371) ('Беларусбанк', 1045) ('Мила', 568)
    	 34 ('be:Белпошта', 810) ('be:Белаграпрамбанк', 584) ('ru:Fix Price (сеть магазинов)', 528)
    	 4168 (('building',), 7652) (('building', 'yes'), 6996) (('amenity',), 2325)
    	 1892 (('building',), 7652) (('building', 'yes'), 6996) (('amenity',), 2325)
    	 1 ('Милавица', 22)
    	 1 ('Милавица', 1)
    	 61 (('shop',), 22) (('shop', 'clothes'), 22) (('opening_hours',), 10)
    	 22 (('shop', 'clothes'), 1) (('name', 'Милавица'), 1) (('name',), 1)
    ref source:population 1 10348 0 0
    	 1 ('Б', 1)
    	 1 ('Белстат', 10348)
    	 8 (('indoor', 'area'), 1) (('level', '0'), 1) (('indoor',), 1)
    	 22735 (('indoor', 'area'), 1) (('level', '0'), 1) (('indoor',), 1)
    	 0
    	 0
    	 0
    	 0
    operator source:population 1 10348 0 0
    	 1 ('е', 1)
    	 1 ('Белстат', 10348)
    	 4 (('name', 'Складской комплекс «Северный»'), 1) (('landuse',), 1) (('landuse', 'industrial'), 1)
    	 22735 (('name', 'Складской комплекс «Северный»'), 1) (('landuse',), 1) (('landuse', 'industrial'), 1)
    	 0
    	 0
    	 0
    	 0
    addr:unit source:population 1 10348 0 0
    	 1 ('Б', 1)
    	 1 ('Белстат', 10348)
    	 18 (('addr:housenumber', '44'), 1) (('surface',), 1) (('amenity', 'parking'), 1)
    	 22735 (('addr:housenumber', '44'), 1) (('surface',), 1) (('amenity', 'parking'), 1)
    	 0
    	 0
    	 0
    	 0
    description to 10307 556 1 7
    	 16 ('н', 10017) ('улица', 147) ('ж', 54)
    	 218 ('Молодёжная улица', 24) ('Железнодорожный вокзал', 21) ('рынок "Южный"', 18)
    	 69 (('building',), 10146) (('building', 'yes'), 10140) (('addr:street',), 9754)
    	 1002 (('building',), 10146) (('building', 'yes'), 10140) (('addr:street',), 9754)
    	 1 ('Железнодорожный вокзал', 1)
    	 1 ('Железнодорожный вокзал', 7)
    	 6 (('addr:housenumber', '5'), 1) (('addr:street', 'улица Виссариона Белинского'), 1) (('addr:street',), 1)
    	 29 (('route',), 7) (('type',), 7) (('public_transport:version', '2'), 7)
    addr:city addr2:street 10251 105 0 0
    	 19 ('Минск', 9380) ('Полоцк', 317) ('Дзержинск', 224)
    	 26 ('переулок Дзержинского', 19) ('Октябрьская улица', 14) ('улица Дзержинского', 10)
    	 12741 (('addr:street',), 9672) (('addr:housenumber',), 9411) (('building',), 7370)
    	 173 (('addr:street',), 9672) (('addr:housenumber',), 9411) (('building',), 7370)
    	 0
    	 0
    	 0
    	 0
    name was:name 10246 279 1035 26
    	 102 ('н', 6371) ('Н', 1146) ('Мила', 568)
    	 48 ('внутрихозяйственный карьер КСУП "Бородичи"', 14) ('Неман-Лада', 12) ('Гастроном "Днепровский"', 12)
    	 2514 (('building',), 8594) (('building', 'yes'), 7045) (('building', 'residential'), 1262)
    	 341 (('building',), 8594) (('building', 'yes'), 7045) (('building', 'residential'), 1262)
    	 25 ('Мила', 568) ('Белинвестбанк', 222) ('Пинскдрев', 54)
    	 25 ('Вальки', 2) ('Белинвестбанк', 1) ('Рублёвский', 1)
    	 1573 (('opening_hours',), 702) (('shop',), 695) (('operator',), 661)
    	 195 (('was:shop',), 8) (('was:amenity',), 7) (('name',), 7)
    was:addr:street addr:street 17 10212 12 10087
    	 3 ('улица Девятовка', 9) ('улица Дзержинского', 4) ('улица Мира', 4)
    	 7 ('улица Мира', 6328) ('улица Дзержинского', 3756) ('1-я улица Мира', 47)
    	 42 (('was:addr:housenumber',), 17) (('was:building',), 15) (('building:levels',), 8)
    	 2235 (('was:addr:housenumber',), 17) (('was:building',), 15) (('building:levels',), 8)
    	 3 ('улица Девятовка', 9) ('улица Дзержинского', 2) ('улица Мира', 1)
    	 3 ('улица Мира', 6328) ('улица Дзержинского', 3756) ('улица Девятовка', 3)
    	 42 (('was:addr:housenumber',), 12) (('was:building',), 11) (('building:levels',), 8)
    	 2235 (('building',), 9890) (('addr:housenumber',), 9581) (('building', 'yes'), 6327)
    description from 10134 550 1 7
    	 17 ('н', 9805) ('улица', 147) ('кн', 92)
    	 211 ('Молодёжная улица', 24) ('Железнодорожный вокзал', 21) ('рынок "Южный"', 16)
    	 77 (('building',), 9972) (('building', 'yes'), 9965) (('addr:street',), 9583)
    	 988 (('building',), 9972) (('building', 'yes'), 9965) (('addr:street',), 9583)
    	 1 ('Железнодорожный вокзал', 1)
    	 1 ('Железнодорожный вокзал', 7)
    	 6 (('addr:housenumber', '5'), 1) (('addr:street', 'улица Виссариона Белинского'), 1) (('addr:street',), 1)
    	 29 (('to',), 7) (('route',), 7) (('public_transport:version', '2'), 7)
    name clothes 10071 283 0 0
    	 22 ('Н', 4584) ('н', 3601) ('М', 312)
    	 13 ('Женская_одежда;Мужская_одежда;Детская_одежда;Колготки;Чулки;Носки;Белье;Купальники', 85) ('Женская_одежда;Мужская_одежда;Одежда_для_детей;Носки;Колготки;Чулки;Белье;Купальники', 19) ('Женская_одежда;Мужская_одежда;Одежда_для_детей;Чулки;Колготки;Носки;Белье;Купальники', 19)
    	 190 (('building',), 9537) (('building', 'yes'), 5530) (('building', 'residential'), 3394)
    	 117 (('building',), 9537) (('building', 'yes'), 5530) (('building', 'residential'), 3394)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber via 9855 108 0 0
    	 9 ('н', 9316) ('Н', 240) ('П', 180)
    	 48 ('Калинковичи, Мозырь', 6) ('Мозырь, Калинковичи', 6) ('Мозырь, Калинковичи, Стодоличи', 6)
    	 151 (('building',), 9853) (('building', 'yes'), 9606) (('addr:street',), 8296)
    	 235 (('building',), 9853) (('building', 'yes'), 9606) (('addr:street',), 8296)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city addr:city 5954 9736 1889 9674
    	 4 ('Минск', 5080) ('Речица', 766) ('Микашевичи', 106)
    	 9 ('Минск', 9380) ('Могилёв', 213) ('СТ "Могилёвский-Электродвигатель"', 53)
    	 1844 (('fire_hydrant:type',), 5954) (('emergency', 'fire_hydrant'), 5954) (('emergency',), 5954)
    	 12705 (('fire_hydrant:type',), 5954) (('emergency', 'fire_hydrant'), 5954) (('emergency',), 5954)
    	 4 ('Минск', 1016) ('Речица', 766) ('Микашевичи', 106)
    	 4 ('Минск', 9380) ('Могилёв', 213) ('Микашевичи', 52)
    	 1844 (('fire_hydrant:type',), 1889) (('emergency', 'fire_hydrant'), 1889) (('emergency',), 1889)
    	 12689 (('addr:street',), 9287) (('addr:housenumber',), 9043) (('building',), 6748)
    addr:city artist_name 9504 7 0 0
    	 5 ('Минск', 9380) ('Витебск', 97) ('Лебедев', 17)
    	 5 ('Игорь Зосимович, Екатерина Зантария, Полина Богданова', 3) ('Дизайн Студия Стиль Минск', 1) ('ВПК «Поиск» г. Витебск', 1)
    	 12640 (('addr:street',), 9105) (('addr:housenumber',), 8897) (('building',), 6626)
    	 34 (('addr:street',), 9105) (('addr:housenumber',), 8897) (('building',), 6626)
    	 0
    	 0
    	 0
    	 0
    addr:city website 9477 2 0 0
    	 2 ('Минск', 9380) ('Витебск', 97)
    	 2 ('Баня-Минск.бел', 1) ('УП "Витебскоблводоканал"', 1)
    	 12636 (('addr:street',), 9095) (('addr:housenumber',), 8872) (('building',), 6601)
    	 23 (('addr:street',), 9095) (('addr:housenumber',), 8872) (('building',), 6601)
    	 0
    	 0
    	 0
    	 0
    name FIXME 9458 251 0 0
    	 28 ('н', 8310) ('п', 374) ('к', 200)
    	 34 ('беседка? зонтик? ...? нужны доп. теги', 20) ('проверить куда она приведёт', 18) ('необходимо уточнить существуюшие линии тротуаров', 14)
    	 160 (('building',), 9339) (('building', 'yes'), 8654) (('addr:street',), 615)
    	 158 (('building',), 9339) (('building', 'yes'), 8654) (('addr:street',), 615)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber contact:website 9430 57 0 0
    	 15 ('н', 4658) ('2А', 3210) ('2Б', 895)
    	 22 ('https://azs.a-100.by/set-azs/map-azs/?query=п. Привольный, ул. Мира, 2А/2-1', 6) ('https://azs.a-100.by/set-azs/map-azs/?query= ул. Промышленная, 2Б (МКАД)', 6) ('https://azs.a-100.by/set-azs/map-azs/?query=Машиностроителей, 7Б', 4)
    	 3320 (('building',), 9261) (('addr:street',), 8462) (('building', 'yes'), 7483)
    	 227 (('building',), 9261) (('addr:street',), 8462) (('building', 'yes'), 7483)
    	 0
    	 0
    	 0
    	 0
    addr:housename related_law 9428 300 0 0
    	 13 ('н', 8700) ('Н', 279) ('к', 196)
    	 50 ('Постановление Совета Министров РБ от 27.12.2007 № 1833', 20) ('Постановление Совета Министров РБ 27.12.2007 № 1833', 20) ('Постановление Совета Министров РБ от 04.02.2015 № 71', 16)
    	 104 (('building',), 9424) (('building', 'yes'), 9164) (('addr:street',), 6646)
    	 281 (('building',), 9424) (('building', 'yes'), 9164) (('addr:street',), 6646)
    	 0
    	 0
    	 0
    	 0
    addr:unit addr:city 265 9407 0 0
    	 2 ('Б', 207) ('А', 58)
    	 261 ('Берёзовка', 1603) ('Брест', 1383) ('Браково', 360)
    	 23 (('addr:street',), 265) (('addr:housenumber',), 265) (('addr:city',), 265)
    	 3459 (('addr:street',), 265) (('addr:housenumber',), 265) (('addr:city',), 265)
    	 0
    	 0
    	 0
    	 0
    addr:city is_in 9384 6 4 3
    	 2 ('Минск', 9380) ('Минский район', 4)
    	 1 ('Минский район', 6)
    	 12349 (('addr:street',), 9003) (('addr:housenumber',), 8780) (('building',), 6573)
    	 18 (('addr:street',), 9003) (('addr:housenumber',), 8780) (('building',), 6573)
    	 1 ('Минский район', 4)
    	 1 ('Минский район', 3)
    	 17 (('addr:postcode',), 4) (('building',), 4) (('building:levels',), 3)
    	 18 (('addr:postcode',), 3) (('addr:street',), 3) (('building',), 3)
    ref short_name 9381 7578 13 9
    	 31 ('Т', 2598) ('СТ', 2490) ('С', 1529)
    	 1783 ('СТ "Дружба"', 55) ('СТ "Лесная Поляна"', 42) ('СТ "Дорожник"', 40)
    	 244 (('aeroway', 'taxiway'), 3540) (('aeroway',), 3540) (('name',), 3372)
    	 5421 (('aeroway', 'taxiway'), 3540) (('aeroway',), 3540) (('name',), 3372)
    	 7 ('ПАСЧ-2', 4) ('ПАСЧ-1', 4) ('БСМП', 1)
    	 7 ('БСМП', 2) ('ЦУМ', 2) ('ПАСЧ-2', 1)
    	 128 (('name',), 13) (('amenity',), 10) (('amenity', 'fire_station'), 9)
    	 90 (('name',), 9) (('amenity',), 5) (('addr:street',), 4)
    addr:city official_short_type 9380 1 0 0
    	 1 ('Минск', 9380)
    	 1 ('Нотариальная контора №2 Фрунзенского района г.Минска', 1)
    	 12345 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 6 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 0
    	 0
    	 0
    	 0
    addr:city phone 9380 1 0 0
    	 1 ('Минск', 9380)
    	 1 ('Многоканальный по Минску: 160 (гор, vel, mts, life) +375 (17) 207-74-74 Стоматология: +375 (29) 160-03-03', 1)
    	 12345 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 16 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 0
    	 0
    	 0
    	 0
    addr:city fee 9380 1 0 0
    	 1 ('Минск', 9380)
    	 1 ('Москва-Минск', 1)
    	 12345 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 2 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 0
    	 0
    	 0
    	 0
    addr:city contact:facebook 9380 1 0 0
    	 1 ('Минск', 9380)
    	 1 ('https://www.facebook.com/pages/КУП-Минсксанавтотранс/1416766311868086', 1)
    	 12345 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 18 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 0
    	 0
    	 0
    	 0
    addr:city name1 9380 1 0 0
    	 1 ('Минск', 9380)
    	 1 ('Минская районная организация  Белорусского Общества Красного Креста', 1)
    	 12345 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 10 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 0
    	 0
    	 0
    	 0
    addr:city oneway 9380 1 0 0
    	 1 ('Минск', 9380)
    	 1 ('ГП «Минсктранс»', 1)
    	 12345 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 6 (('addr:street',), 9000) (('addr:housenumber',), 8777) (('building',), 6569)
    	 0
    	 0
    	 0
    	 0
    building was:ref 9177 111 0 0
    	 1 ('Н', 9177)
    	 57 ('Н10351', 6) ('Н3192', 5) ('Н17508', 5)
    	 7 (('name',), 1938) (('name', 'Н'), 1881) (('building:levels',), 57)
    	 76 (('name',), 1938) (('name', 'Н'), 1881) (('building:levels',), 57)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city addr:full 9144 16 0 0
    	 1 ('Минск', 9144)
    	 9 ('д. Яново, Борисовский район, Минская область', 6) ('пересечение а/д М-3 Минск-Витебск и Р111 Бешенковичи-Чашники', 2) ('44 км а/д Минск-Витебск', 2)
    	 1120 (('emergency', 'fire_hydrant'), 9144) (('fire_hydrant:type',), 9144) (('emergency',), 9144)
    	 143 (('emergency', 'fire_hydrant'), 9144) (('fire_hydrant:type',), 9144) (('emergency',), 9144)
    	 0
    	 0
    	 0
    	 0
    destination addr:district 51 9138 0 0
    	 11 ('Гомель', 32) ('Брест', 4) ('Лепель', 3)
    	 13 ('Минский район', 3969) ('Бобруйский район', 856) ('Брестская обл.', 644)
    	 73 (('oneway',), 38) (('oneway', 'yes'), 38) (('highway',), 38)
    	 10995 (('oneway',), 38) (('oneway', 'yes'), 38) (('highway',), 38)
    	 0
    	 0
    	 0
    	 0
    addr:housename designation 9136 288 8 6
    	 23 ('н', 7656) ('Н', 837) ('к', 273)
    	 74 ('Лавка', 20) ('Административное здание', 12) ('Школа-интернат', 12)
    	 147 (('building',), 9119) (('building', 'yes'), 8880) (('addr:street',), 6640)
    	 349 (('building',), 9119) (('building', 'yes'), 8880) (('addr:street',), 6640)
    	 5 ('МЧС', 2) ('Проходная', 2) ('АТС', 2)
    	 5 ('Административное здание', 2) ('МЧС', 1) ('Автосервис', 1)
    	 19 (('addr:street',), 8) (('building', 'yes'), 8) (('building',), 8)
    	 22 (('name',), 3) (('building', 'yes'), 3) (('building',), 3)
    addr:district addr:region 5 9126 3 4563
    	 2 ('Брестская область', 3) ('Брестская', 2)
    	 1 ('Брестская область', 9126)
    	 57 (('addr:country',), 5) (('addr:subdistrict',), 5) (('addr:postcode',), 5)
    	 10170 (('addr:country',), 5) (('addr:subdistrict',), 5) (('addr:postcode',), 5)
    	 1 ('Брестская область', 3)
    	 1 ('Брестская область', 4563)
    	 46 (('name',), 3) (('addr:country',), 3) (('addr:subdistrict',), 3)
    	 10170 (('name',), 4562) (('int_name',), 4538) (('addr:district',), 4535)
    addr:housename building 9118 1280 764 451
    	 43 ('н', 6264) ('Н', 1953) ('к', 189)
    	 98 ('КЖ', 390) ('КН', 312) ('Н', 161)
    	 252 (('building',), 9083) (('building', 'yes'), 8857) (('addr:street',), 6813)
    	 224 (('building',), 9083) (('building', 'yes'), 8857) (('addr:street',), 6813)
    	 30 ('Н', 279) ('н', 174) ('кн', 99)
    	 30 ('Н', 161) ('КЖ', 130) ('КН', 104)
    	 215 (('building',), 756) (('building', 'yes'), 739) (('addr:street',), 595)
    	 146 (('name',), 191) (('building:levels',), 41) (('name', 'Н'), 33)
    addr:housenumber network 9102 1788 0 0
    	 8 ('н', 7946) ('Н', 720) ('П', 225)
    	 56 ('Минский метрополитен', 524) ('Барановичское отделение', 496) ('Минское отделение', 100)
    	 150 (('building',), 9096) (('building', 'yes'), 8829) (('addr:street',), 7671)
    	 847 (('building',), 9096) (('building', 'yes'), 8829) (('addr:street',), 7671)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber subject:wikipedia 9045 67 0 0
    	 10 ('н', 8494) ('Н', 240) ('ж', 196)
    	 40 ('be:Народны камісарыят юстыцыі БССР', 4) ('ru:Прилежаев, Николай Александрович', 4) ('ru:Пестрак, Филипп Семёнович', 3)
    	 152 (('building',), 9043) (('building', 'yes'), 8863) (('addr:street',), 7615)
    	 206 (('building',), 9043) (('building', 'yes'), 8863) (('addr:street',), 7615)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr:full 9036 341 0 0
    	 15 ('н', 6960) ('Н', 1395) ('к', 336)
    	 50 ('д. Рудишки, Ошмянский район, Гродненская область', 40) ('д. Яново, Борисовский район, Минская область', 30) ('44 км а/д Минск-Витебск', 12)
    	 118 (('building',), 9022) (('building', 'yes'), 8802) (('addr:street',), 6703)
    	 359 (('building',), 9022) (('building', 'yes'), 8802) (('addr:street',), 6703)
    	 0
    	 0
    	 0
    	 0
    ref gomel_PT:note 9 8932 0 0
    	 4 ('Н', 4) ('Т', 2) ('ж', 2)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 8932)
    	 39 (('railway:signal:position', 'right'), 3) (('railway', 'signal'), 3) (('railway',), 3)
    	 859 (('railway:signal:position', 'right'), 3) (('railway', 'signal'), 3) (('railway',), 3)
    	 0
    	 0
    	 0
    	 0
    building gomel_PT:note 166 8932 0 0
    	 4 ('Н', 161) ('н', 2) ('Т', 2)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 8932)
    	 16 (('name',), 35) (('name', 'Н'), 33) (('building:levels',), 2)
    	 859 (('name',), 35) (('name', 'Н'), 33) (('building:levels',), 2)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city ref 8895 10 0 0
    	 3 ('Минск', 8128) ('Речица', 766) ('Могилёв', 1)
    	 10 ('Речица-Демехи', 1) ('Москва - Могилёв - Гомель', 1) ('эл. Минск - Молодечно', 1)
    	 1620 (('fire_hydrant:type',), 8895) (('emergency', 'fire_hydrant'), 8895) (('emergency',), 8895)
    	 31 (('fire_hydrant:type',), 8895) (('emergency', 'fire_hydrant'), 8895) (('emergency',), 8895)
    	 0
    	 0
    	 0
    	 0
    inscription addr:street 39 8763 0 0
    	 3 ('Мир', 37) ('Гожа', 1) ('Бегомль', 1)
    	 39 ('улица Мира', 6328) ('Мирная улица', 1131) ('проспект Мира', 303)
    	 20 (('note',), 37) (('material', 'steel'), 37) (('wikidata', 'Q11115124'), 37)
    	 1810 (('note',), 37) (('material', 'steel'), 37) (('wikidata', 'Q11115124'), 37)
    	 0
    	 0
    	 0
    	 0
    ref source 207 8716 0 0
    	 19 ('Н', 76) ('ж', 30) ('А', 13)
    	 48 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 4298) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 2204) ('Национальное кадастровое агентство nca.by', 1094)
    	 112 (('railway', 'signal'), 59) (('railway',), 59) (('railway:signal:position',), 59)
    	 862 (('railway', 'signal'), 59) (('railway',), 59) (('railway:signal:position',), 59)
    	 0
    	 0
    	 0
    	 0
    fence_type addr:street 156 8688 0 0
    	 2 ('да', 152) ('Забор', 4)
    	 154 ('улица Володарского', 1856) ('улица Максима Богдановича', 790) ('улица Богдановича', 643)
    	 6 (('barrier',), 156) (('barrier', 'fence'), 156) (('material',), 4)
    	 2817 (('barrier',), 156) (('barrier', 'fence'), 156) (('material',), 4)
    	 0
    	 0
    	 0
    	 0
    cycleway:left addr:street 152 8682 0 0
    	 1 ('да', 152)
    	 152 ('улица Володарского', 1856) ('улица Максима Богдановича', 790) ('улица Богдановича', 643)
    	 6 (('int_name',), 152) (('name', 'улица 1 Мая'), 152) (('name',), 152)
    	 2797 (('int_name',), 152) (('name', 'улица 1 Мая'), 152) (('name',), 152)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber FIXME 8641 71 0 0
    	 8 ('н', 8220) ('ж', 343) ('П', 30)
    	 32 ('беседка? зонтик? ...? нужны доп. теги', 8) ('Соединение дорог на карте не просматривается. Поправьте линки, плз', 3) ('требуется уточнить тип магазина', 3)
    	 114 (('building',), 8641) (('building', 'yes'), 8488) (('addr:street',), 7266)
    	 154 (('building',), 8641) (('building', 'yes'), 8488) (('addr:street',), 7266)
    	 0
    	 0
    	 0
    	 0
    addr:housename fire_hydrant:housenumber 8630 422 8 12
    	 30 ('н', 7134) ('Н', 837) ('к', 315)
    	 133 ('Автомойка', 30) ('131 -Речицатекстиль', 18) ('-Кострамы', 12)
    	 175 (('building',), 8609) (('building', 'yes'), 8326) (('addr:street',), 6319)
    	 127 (('building',), 8609) (('building', 'yes'), 8326) (('addr:street',), 6319)
    	 8 ('3а', 1) ('37а', 1) ('13а', 1)
    	 8 ('4а', 5) ('3а', 1) ('37а', 1)
    	 17 (('building',), 8) (('addr:street',), 6) (('building', 'yes'), 6)
    	 47 (('fire_hydrant:type',), 12) (('fire_hydrant:diameter',), 12) (('name',), 12)
    addr:region is_in:region 8625 1 8625 1
    	 1 ('Гродненская область', 8625)
    	 1 ('Гродненская область', 1)
    	 17907 (('name',), 8625) (('addr:district',), 8604) (('addr:country',), 8578)
    	 20 (('name',), 8625) (('addr:district',), 8604) (('addr:country',), 8578)
    	 1 ('Гродненская область', 8625)
    	 1 ('Гродненская область', 1)
    	 17907 (('name',), 8625) (('addr:district',), 8604) (('addr:country',), 8578)
    	 20 (('wikidata', 'Q2618952'), 1) (('int_name',), 1) (('wikidata',), 1)
    was:name:prefix addr:place 8606 115 0 0
    	 3 ('деревня', 8340) ('посёлок', 260) ('станция', 6)
    	 21 ('посёлок Строителей', 45) ('деревня Селец', 28) ('1-й Рабочий посёлок', 9)
    	 2150 (('name',), 8606) (('place',), 8606) (('int_name:prefix',), 8451)
    	 139 (('name',), 8606) (('place',), 8606) (('int_name:prefix',), 8451)
    	 0
    	 0
    	 0
    	 0
    name architect 8413 265 2 2
    	 56 ('н', 6094) ('Н', 1146) ('к', 220)
    	 30 ('Рубаненко Борис Рафаилович', 27) ('А. Ю. Заболотная', 15) ('Б.Р.Рубаленко', 14)
    	 353 (('building',), 8105) (('building', 'yes'), 6619) (('building', 'residential'), 1238)
    	 244 (('building',), 8105) (('building', 'yes'), 6619) (('building', 'residential'), 1238)
    	 2 ('Витебскгражданпроект', 1) ('Житновичское лесничество', 1)
    	 2 ('Витебскгражданпроект', 1) ('Житновичское лесничество', 1)
    	 25 (('building',), 2) (('building:levels',), 2) (('addr:street',), 2)
    	 16 (('building:part',), 1) (('building:part', 'yes'), 1) (('building:levels',), 1)
    addr:housename protection_title 8302 683 0 0
    	 11 ('н', 7308) ('Н', 558) ('к', 287)
    	 42 ('Памятник природы', 140) ('Республиканский ландшафтный заказник', 110) ('Республиканский биологический заказник', 45)
    	 91 (('building',), 8298) (('building', 'yes'), 8082) (('addr:street',), 5985)
    	 582 (('building',), 8298) (('building', 'yes'), 8082) (('addr:street',), 5985)
    	 0
    	 0
    	 0
    	 0
    type addr:city 312 8260 0 0
    	 3 ('ц', 198) ('ель', 60) ('Дуб', 54)
    	 266 ('Гомель', 586) ('Сопоцкин', 371) ('Селец', 368)
    	 3 (('natural',), 312) (('natural', 'wetland'), 198) (('natural', 'tree'), 114)
    	 4134 (('natural',), 312) (('natural', 'wetland'), 198) (('natural', 'tree'), 114)
    	 0
    	 0
    	 0
    	 0
    building old_addr 8220 163 0 0
    	 3 ('Н', 8050) ('н', 118) ('р', 52)
    	 111 ('1-я Новопрудская улица, 40А', 2) ('1-я Новопрудская улица, 40А к11', 2) ('1-я Новопрудская улица, 11', 2)
    	 15 (('name',), 1700) (('name', 'Н'), 1650) (('building:levels',), 102)
    	 189 (('name',), 1700) (('name', 'Н'), 1650) (('building:levels',), 102)
    	 0
    	 0
    	 0
    	 0
    type official_name 2711 7841 0 0
    	 3 ('ц', 1800) ('Дуб', 501) ('ель', 410)
    	 2218 ('Столбцы — Ивацевичи — Кобрин', 303) ('граница Республики Польша (Песчатка) — Каменец — Шерешево — Свислочь', 144) ('Минск — Калачи — Мядель', 98)
    	 3 (('natural',), 2711) (('natural', 'wetland'), 1800) (('natural', 'tree'), 911)
    	 5901 (('natural',), 2711) (('natural', 'wetland'), 1800) (('natural', 'tree'), 911)
    	 0
    	 0
    	 0
    	 0
    description addr2:street 7736 947 0 0
    	 9 ('н', 6360) ('улица', 1288) ('кн', 46)
    	 213 ('переулок Дзержинского', 38) ('улица Пушкина', 36) ('Молодёжная улица', 33)
    	 38 (('building',), 6442) (('building', 'yes'), 6441) (('addr:street',), 6195)
    	 479 (('building',), 6442) (('building', 'yes'), 6441) (('addr:street',), 6195)
    	 0
    	 0
    	 0
    	 0
    name source:ref 644 7682 0 0
    	 14 ('н', 554) ('к', 20) ('п', 17)
    	 2 ('Публичная кадастровая карта', 7672) ('Договор между РФ и Украиной от 28 января 2003 года (приложение 1)', 10)
    	 44 (('building',), 637) (('building', 'yes'), 587) (('addr:street',), 44)
    	 372 (('building',), 637) (('building', 'yes'), 587) (('addr:street',), 44)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city via 7645 10 0 0
    	 3 ('Речица', 4596) ('Минск', 3048) ('Могилёв', 1)
    	 8 ('Речица, Бобруйск, Минск', 2) ('Минск, Светлогорск, Речица', 2) ('Речица, Светлогоск, Паричи', 1)
    	 1620 (('fire_hydrant:type',), 7645) (('emergency', 'fire_hydrant'), 7645) (('emergency',), 7645)
    	 33 (('fire_hydrant:type',), 7645) (('emergency', 'fire_hydrant'), 7645) (('emergency',), 7645)
    	 0
    	 0
    	 0
    	 0
    to addr:district 49 7565 0 0
    	 11 ('Гомель', 34) ('Брагин', 3) ('Полоцк', 3)
    	 11 ('Минский район', 3969) ('Воложинский район', 848) ('Полоцкий район', 807)
    	 137 (('route',), 49) (('type',), 49) (('from',), 49)
    	 9875 (('route',), 49) (('type',), 49) (('from',), 49)
    	 0
    	 0
    	 0
    	 0
    was:name:prefix addr:city 7548 391 0 0
    	 4 ('деревня', 7228) ('хутор', 249) ('посёлок', 65)
    	 17 ('деревня Круги', 94) ('деревня Большое Запаточье', 86) ('деревня Боровка', 80)
    	 3050 (('name',), 7548) (('place',), 7548) (('abandoned:place',), 7411)
    	 238 (('name',), 7548) (('place',), 7548) (('abandoned:place',), 7411)
    	 0
    	 0
    	 0
    	 0
    type addr:district 23 7459 0 0
    	 3 ('ц', 14) ('ель', 6) ('Дуб', 3)
    	 20 ('Полоцкий район', 807) ('Островецкий район', 691) ('Мядельский район', 621)
    	 3 (('natural',), 23) (('natural', 'wetland'), 14) (('natural', 'tree'), 9)
    	 15335 (('natural',), 23) (('natural', 'wetland'), 14) (('natural', 'tree'), 9)
    	 0
    	 0
    	 0
    	 0
    building:levels addr:housenumber 141 7350 2 3330
    	 2 ('2А', 98) ('Н', 43)
    	 141 ('2А', 3210) ('12А', 1088) ('22А', 744)
    	 5 (('building',), 141) (('addr:street',), 98) (('addr:street', 'Центральная улица'), 98)
    	 4735 (('building',), 141) (('addr:street',), 98) (('addr:street', 'Центральная улица'), 98)
    	 2 ('2А', 1) ('Н', 1)
    	 2 ('2А', 3210) ('Н', 120)
    	 5 (('building',), 2) (('addr:street',), 1) (('addr:street', 'Центральная улица'), 1)
    	 2851 (('building',), 3211) (('addr:street',), 3182) (('building', 'yes'), 1988)
    name website 7334 278 0 0
    	 49 ('н', 5540) ('Баня', 294) ('к', 280)
    	 49 ('https://аптекарь.бел', 24) ('http://островецкое.бел', 18) ('http://чайхана.бел', 12)
    	 534 (('building',), 7114) (('building', 'yes'), 6438) (('addr:street',), 511)
    	 352 (('building',), 7114) (('building', 'yes'), 6438) (('addr:street',), 511)
    	 0
    	 0
    	 0
    	 0
    fixme note 7164 431 311 15
    	 26 ('адрес', 5275) ('положение', 741) ('номер', 270)
    	 135 ('Уточнить обязательно название улицы, если неправильно то исправить!!!', 112) ('Примерное местоположение', 30) ('уточнить покрытие дороги', 15)
    	 635 (('building',), 5714) (('building:levels',), 3627) (('building', 'yes'), 2608)
    	 713 (('building',), 5714) (('building:levels',), 3627) (('building', 'yes'), 2608)
    	 8 ('адрес', 211) ('проверить', 49) ('уточнить адрес', 27)
    	 8 ('адрес', 4) ('проверить адрес', 3) ('уточнить адрес', 2)
    	 304 (('building',), 273) (('building:levels',), 181) (('addr:housenumber',), 144)
    	 40 (('building',), 12) (('addr:street',), 9) (('addr:housenumber',), 9)
    designation official_name 2363 7154 0 0
    	 13 ('б', 2253) ('Каменка', 40) ('Городище', 21)
    	 2315 ('Столбцы — Ивацевичи — Кобрин', 303) ('Витебск — Городок (до автомобильной дороги М-8)', 146) ('граница Республики Польша (Песчатка) — Каменец — Шерешево — Свислочь', 144)
    	 107 (('name',), 2360) (('building', 'yes'), 2255) (('building',), 2255)
    	 6477 (('name',), 2360) (('building', 'yes'), 2255) (('building',), 2255)
    	 0
    	 0
    	 0
    	 0
    addr:housename network 7144 4908 7 12
    	 15 ('н', 5046) ('Н', 1674) ('к', 224)
    	 61 ('Барановичское отделение', 2480) ('Минский метрополитен', 1310) ('Брестское отделение', 210)
    	 134 (('building',), 7124) (('building', 'yes'), 6941) (('addr:street',), 5397)
    	 868 (('building',), 7124) (('building', 'yes'), 6941) (('addr:street',), 5397)
    	 3 ('Белагропромбанк', 3) ('Беларусбанк', 2) ('7а', 2)
    	 3 ('Беларусбанк', 9) ('Белагропромбанк', 2) ('7а', 1)
    	 49 (('building', 'yes'), 6) (('building',), 6) (('addr:street',), 5)
    	 37 (('amenity', 'atm'), 11) (('amenity',), 11) (('operator',), 7)
    name destination:street 7116 367 14 5
    	 60 ('н', 5540) ('Н', 382) ('к', 220)
    	 34 ('праспект Пераможцаў', 56) ('праспект Незалежнасці', 48) ('Партызанскі праспект', 27)
    	 333 (('building',), 6848) (('building', 'yes'), 5945) (('building', 'residential'), 736)
    	 86 (('building',), 6848) (('building', 'yes'), 5945) (('building', 'residential'), 736)
    	 2 ('Лагойскі тракт', 10) ('Партызанскі праспект', 4)
    	 2 ('Партызанскі праспект', 3) ('Лагойскі тракт', 2)
    	 31 (('minsk_PT:note',), 14) (('ref:minsktrans',), 14) (('public_transport',), 14)
    	 21 (('surface',), 5) (('oneway', 'yes'), 5) (('maxaxleload', '11.5'), 5)
    from addr:district 52 7052 0 0
    	 11 ('Гомель', 36) ('Минск', 3) ('Брагин', 3)
    	 11 ('Минский район', 3969) ('Полоцкий район', 807) ('Логойский район', 648)
    	 156 (('to',), 52) (('route',), 52) (('type',), 52)
    	 8773 (('to',), 52) (('route',), 52) (('type',), 52)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber was:name 6978 64 0 0
    	 12 ('н', 6302) ('Н', 360) ('ж', 147)
    	 33 ('Неман-Лада', 4) ('Розовая Пантера Мини', 4) ('внутрихозяйственный карьер КСУП "Бородичи"', 4)
    	 167 (('building',), 6975) (('building', 'yes'), 6796) (('addr:street',), 5879)
    	 226 (('building',), 6975) (('building', 'yes'), 6796) (('addr:street',), 5879)
    	 0
    	 0
    	 0
    	 0
    addr:unit wikipedia 6133 6968 0 0
    	 2 ('Б', 3962) ('А', 2171)
    	 5973 ('be:Бярэзіна', 64) ('ru:Магистраль М12 (Белоруссия)', 39) ('be:Альхоўка (басейн Нёмана)', 38)
    	 23 (('addr:street',), 6133) (('addr:housenumber',), 6133) (('addr:city',), 6133)
    	 17600 (('addr:street',), 6133) (('addr:housenumber',), 6133) (('addr:city',), 6133)
    	 0
    	 0
    	 0
    	 0
    fence_type name 3420 6927 5 4
    	 10 ('да', 3208) ('камень', 77) ('Забор', 64)
    	 3327 ('Слобода', 200) ('улица Максима Богдановича', 103) ('Заборье', 84)
    	 8 (('barrier',), 3420) (('barrier', 'fence'), 3420) (('height',), 67)
    	 8131 (('barrier',), 3420) (('barrier', 'fence'), 3420) (('height',), 67)
    	 2 ('ж.б.', 4) ('камень', 1)
    	 2 ('камень', 3) ('ж.б.', 1)
    	 5 (('barrier',), 5) (('barrier', 'fence'), 5) (('height',), 3)
    	 9 (('historic',), 2) (('historic', 'memorial'), 1) (('tourism',), 1)
    addr:housename via 6915 256 0 0
    	 12 ('н', 5916) ('Н', 558) ('к', 301)
    	 61 ('Автовокзал', 16) ('Мозырь, Калинковичи, Стодоличи', 12) ('Калинковичи, Мозырь', 10)
    	 100 (('building',), 6908) (('building', 'yes'), 6725) (('addr:street',), 5017)
    	 295 (('building',), 6908) (('building', 'yes'), 6725) (('addr:street',), 5017)
    	 0
    	 0
    	 0
    	 0
    name contact:website 6894 208 0 0
    	 61 ('н', 4709) ('Н', 764) ('М', 234)
    	 28 ('https://azs.a-100.by/set-azs/map-azs/?query=Минский р-н, трасса на г. Могилев (М4), 4 км от МКАД', 13) ('https://www.belinvestbank.by/about-bank/service-points?town=Гомель&type=atm&showList=list', 12) ('https://azs.a-100.by/set-azs/map-azs/?query= ул. Промышленная, 2Б (МКАД)', 12)
    	 617 (('building',), 6277) (('building', 'yes'), 5189) (('building', 'residential'), 884)
    	 302 (('building',), 6277) (('building', 'yes'), 5189) (('building', 'residential'), 884)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber was:ref 6840 111 0 0
    	 1 ('Н', 6840)
    	 57 ('Н10351', 6) ('Н3192', 5) ('Н17508', 5)
    	 79 (('building',), 6783) (('building', 'yes'), 6612) (('addr:street',), 5985)
    	 76 (('building',), 6783) (('building', 'yes'), 6612) (('addr:street',), 5985)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber brand:wikipedia 6717 525 0 0
    	 9 ('н', 6302) ('ж', 245) ('магазин', 80)
    	 28 ('ru:Fix Price (сеть магазинов)', 132) ('be:Пріорбанк', 78) ('be:Белаграпрамбанк', 73)
    	 114 (('building',), 6717) (('building', 'yes'), 6562) (('addr:street',), 5653)
    	 1097 (('building',), 6717) (('building', 'yes'), 6562) (('addr:street',), 5653)
    	 0
    	 0
    	 0
    	 0
    operator gomel_PT:note 3 6699 0 0
    	 3 ('б', 1) ('я', 1) ('е', 1)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 6699)
    	 9 (('amenity', 'atm'), 2) (('name',), 2) (('amenity',), 2)
    	 859 (('amenity', 'atm'), 2) (('name',), 2) (('amenity',), 2)
    	 0
    	 0
    	 0
    	 0
    description gomel_PT:note 56 6699 0 0
    	 3 ('н', 53) ('ж', 2) ('Н', 1)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 6699)
    	 8 (('building',), 56) (('building', 'yes'), 56) (('addr:street',), 54)
    	 859 (('building',), 56) (('building', 'yes'), 56) (('addr:street',), 54)
    	 0
    	 0
    	 0
    	 0
    height name 4130 6665 6 1
    	 4 ('ф', 4109) ('КУПП "Боровка"', 18) ('2 м', 2)
    	 4114 ('Белоруснефть', 94) ('Светофор', 56) ('Альфа-Банк', 49)
    	 18 (('barrier',), 4111) (('barrier', 'fence'), 4111) (('power', 'pole'), 18)
    	 10134 (('barrier',), 4111) (('barrier', 'fence'), 4111) (('power', 'pole'), 18)
    	 1 ('КУПП "Боровка"', 6)
    	 1 ('КУПП "Боровка"', 1)
    	 4 (('power', 'pole'), 6) (('power',), 6) (('operator',), 5)
    	 6 (('government', 'social_services'), 1) (('building', 'yes'), 1) (('office', 'government'), 1)
    cycleway:left name 3208 6662 0 0
    	 1 ('да', 3208)
    	 3208 ('Слобода', 200) ('улица Максима Богдановича', 103) ('РУП «Издательство «Белбланкавыд»', 76)
    	 6 (('int_name',), 3208) (('name', 'улица 1 Мая'), 3208) (('name',), 3208)
    	 7890 (('int_name',), 3208) (('name', 'улица 1 Мая'), 3208) (('name',), 3208)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber architect 6611 56 0 0
    	 8 ('н', 6028) ('Н', 360) ('ж', 147)
    	 26 ('А. Ю. Заболотная', 6) ('В. Давыдзёнак', 4) ('С. Мусинский;Н. Кравкова', 3)
    	 151 (('building',), 6608) (('building', 'yes'), 6485) (('addr:street',), 5573)
    	 222 (('building',), 6608) (('building', 'yes'), 6485) (('addr:street',), 5573)
    	 0
    	 0
    	 0
    	 0
    addr:district addr:street 6533 1719 0 0
    	 5 ('Минский район', 3969) ('Дзержинский район', 1749) ('Полоцкий район', 807)
    	 12 ('Брестская улица', 1183) ('Светлогорская улица', 426) ('Светлогорское шоссе', 56)
    	 5244 (('addr:region',), 6513) (('addr:country', 'BY'), 6484) (('addr:country',), 6484)
    	 1070 (('addr:region',), 6513) (('addr:country', 'BY'), 6484) (('addr:country',), 6484)
    	 0
    	 0
    	 0
    	 0
    addr:street wikipedia 6526 487 0 0
    	 17 ('Красноармейская улица', 4811) ('Слободская улица', 718) ('Замковая улица', 517)
    	 433 ('ru:Слободская улица', 11) ('ru:Либаво-Роменская улица (Минск)', 8) ('ru:Красноармейская улица (Минск)', 7)
    	 1973 (('building',), 5950) (('addr:housenumber',), 5914) (('building', 'yes'), 3412)
    	 1597 (('building',), 5950) (('addr:housenumber',), 5914) (('building', 'yes'), 3412)
    	 0
    	 0
    	 0
    	 0
    addr:unit official_name 2123 6502 0 0
    	 2 ('Б', 1445) ('А', 678)
    	 2026 ('Борисов — Вилейка — Ошмяны', 232) ('Минск — Гродно — Брузги', 97) ('Берёза — Антополь', 74)
    	 23 (('addr:street',), 2123) (('addr:housenumber',), 2123) (('addr:city',), 2123)
    	 5662 (('addr:street',), 2123) (('addr:housenumber',), 2123) (('addr:city',), 2123)
    	 0
    	 0
    	 0
    	 0
    addr:housename subject:wikipedia 6462 190 0 0
    	 12 ('н', 5394) ('Н', 558) ('к', 266)
    	 50 ('ru:Богданович, Максим Адамович', 6) ('ru:Прилежаев, Николай Александрович', 6) ('be:Народны камісарыят юстыцыі БССР', 6)
    	 102 (('building',), 6447) (('building', 'yes'), 6274) (('addr:street',), 4727)
    	 238 (('building',), 6447) (('building', 'yes'), 6274) (('addr:street',), 4727)
    	 0
    	 0
    	 0
    	 0
    destination minsk_PT:note 3 6445 0 0
    	 1 ('Минск', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 12 (('maxspeed', '60'), 3) (('maxaxleload', '10'), 3) (('maxaxleload',), 3)
    	 4600 (('maxspeed', '60'), 3) (('maxaxleload', '10'), 3) (('maxaxleload',), 3)
    	 0
    	 0
    	 0
    	 0
    to minsk_PT:note 3 6445 0 0
    	 1 ('Минск', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 12 (('route',), 3) (('via',), 3) (('public_transport:version', '2'), 3)
    	 4600 (('route',), 3) (('via',), 3) (('public_transport:version', '2'), 3)
    	 0
    	 0
    	 0
    	 0
    from minsk_PT:note 9 6445 0 0
    	 1 ('Минск', 9)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 25 (('to',), 9) (('route',), 9) (('type',), 9)
    	 4600 (('to',), 9) (('route',), 9) (('type',), 9)
    	 0
    	 0
    	 0
    	 0
    fixme minsk_PT:note 36 6445 0 0
    	 1 ('тип', 36)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 32 (('name',), 30) (('shop',), 27) (('shop', 'yes'), 21)
    	 4600 (('name',), 30) (('shop',), 27) (('shop', 'yes'), 21)
    	 0
    	 0
    	 0
    	 0
    destination:backward minsk_PT:note 3 6445 0 0
    	 1 ('Минск', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 18 (('maxspeed', '90'), 3) (('destination:forward', 'Кобрын;Пiнск'), 3) (('surface',), 3)
    	 4600 (('maxspeed', '90'), 3) (('destination:forward', 'Кобрын;Пiнск'), 3) (('surface',), 3)
    	 0
    	 0
    	 0
    	 0
    designation minsk_PT:note 3 6445 0 0
    	 1 ('б', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 8 (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 3) (('addr:street',), 3) (('building', 'yes'), 3)
    	 4600 (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 3) (('addr:street',), 3) (('building', 'yes'), 3)
    	 0
    	 0
    	 0
    	 0
    network minsk_PT:note 6 6445 0 0
    	 1 ('Минск', 6)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 17 (('minsk_PT:note',), 6) (('shelter', 'yes'), 6) (('shelter',), 6)
    	 4600 (('minsk_PT:note',), 6) (('shelter', 'yes'), 6) (('shelter',), 6)
    	 0
    	 0
    	 0
    	 0
    fence_type minsk_PT:note 3 6445 0 0
    	 1 ('да', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 2 (('barrier',), 3) (('barrier', 'fence'), 3)
    	 4600 (('barrier',), 3) (('barrier', 'fence'), 3)
    	 0
    	 0
    	 0
    	 0
    addr:region minsk_PT:note 24 6445 0 0
    	 1 ('Минск', 24)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 26 (('building:levels',), 24) (('addr:postcode',), 24) (('addr:street',), 24)
    	 4600 (('building:levels',), 24) (('addr:postcode',), 24) (('addr:street',), 24)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city minsk_PT:note 3048 6445 0 0
    	 1 ('Минск', 3048)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 1120 (('emergency', 'fire_hydrant'), 3048) (('fire_hydrant:type',), 3048) (('emergency',), 3048)
    	 4600 (('emergency', 'fire_hydrant'), 3048) (('fire_hydrant:type',), 3048) (('emergency',), 3048)
    	 0
    	 0
    	 0
    	 0
    building:levels minsk_PT:note 3 6445 0 0
    	 1 ('Н', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 2 (('building', 'yes'), 3) (('building',), 3)
    	 4600 (('building', 'yes'), 3) (('building',), 3)
    	 0
    	 0
    	 0
    	 0
    cycleway:left minsk_PT:note 3 6445 0 0
    	 1 ('да', 3)
    	 3 ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже. Подробнее: https://goo.gl/Bo7ZpS', 6274) ('Этот и другие тэги типа "minsk_PT..." - временные и используются для координации работ по ОТ Минска! Не удаляйте их, если видите - они будут удалены позже. Подробнее о внесении ОТ Минска в OSM вы можете прочесть по ссылке https://goo.gl/Bo7ZpS', 101) ('Тэги типа "minsk_PT..." - временные, для внесения ОТ Минска! Не удаляйте их - они будут удалены позже.', 70)
    	 6 (('int_name',), 3) (('name', 'улица 1 Мая'), 3) (('name',), 3)
    	 4600 (('int_name',), 3) (('name', 'улица 1 Мая'), 3) (('name',), 3)
    	 0
    	 0
    	 0
    	 0
    designation wikipedia 5763 6386 0 0
    	 7 ('б', 5646) ('Каменка', 74) ('парк', 24)
    	 5738 ('be:Альхоўка (басейн Нёмана)', 38) ('be:Каменка (прыток Усысы)', 12) ('ru:Слободская улица', 11)
    	 52 (('name',), 5760) (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 5646) (('addr:street',), 5646)
    	 16798 (('name',), 5760) (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 5646) (('addr:street',), 5646)
    	 0
    	 0
    	 0
    	 0
    network operator 3587 6268 420 3167
    	 29 ('Барановичское отделение', 1488) ('Минский метрополитен', 524) ('Минское отделение', 400)
    	 326 ('Беларусбанк', 770) ('БЧ', 719) ('Белагропромбанк', 456)
    	 688 (('name',), 3254) (('operator',), 2932) (('railway',), 2629)
    	 7111 (('name',), 3254) (('operator',), 2932) (('railway',), 2629)
    	 21 ('Минский метрополитен', 262) ('Минское отделение', 50) ('прыгарад СТіСа', 37)
    	 21 ('Беларусбанк', 770) ('БЧ', 719) ('Белагропромбанк', 456)
    	 535 (('name',), 399) (('railway',), 317) (('colour',), 255)
    	 2561 (('amenity',), 2076) (('name',), 2057) (('amenity', 'atm'), 1344)
    addr:unit addr:district 16 6257 0 0
    	 1 ('Б', 16)
    	 16 ('Браславский район', 1008) ('Брестская обл.', 644) ('Борисовский район', 614)
    	 18 (('addr:housenumber', '44'), 16) (('surface',), 16) (('amenity', 'parking'), 16)
    	 12147 (('addr:housenumber', '44'), 16) (('surface',), 16) (('amenity', 'parking'), 16)
    	 0
    	 0
    	 0
    	 0
    name nat_ref 6180 112 0 0
    	 3 ('Н', 6112) ('Р', 42) ('М', 26)
    	 31 ('Р80', 22) ('Н-28', 22) ('М4', 10)
    	 45 (('building',), 6098) (('building', 'residential'), 3703) (('building', 'yes'), 1753)
    	 136 (('building',), 6098) (('building', 'residential'), 3703) (('building', 'yes'), 1753)
    	 0
    	 0
    	 0
    	 0
    description fire_hydrant:street 6117 650 0 0
    	 8 ('н', 5989) ('улица', 56) ('ж', 34)
    	 124 ('Молодежная', 68) ('Набережная', 48) ('Ленина', 40)
    	 26 (('building',), 6035) (('building', 'yes'), 6035) (('addr:street',), 5808)
    	 391 (('building',), 6035) (('building', 'yes'), 6035) (('addr:street',), 5808)
    	 0
    	 0
    	 0
    	 0
    water_tank:city addr:region 1 6089 0 0
    	 1 ('Могилёв', 1)
    	 1 ('Могилёвская область', 6089)
    	 18 (('water_tank:street', 'улица 30 лет Победы'), 1) (('name',), 1) (('fire_operator',), 1)
    	 12244 (('water_tank:street', 'улица 30 лет Победы'), 1) (('name',), 1) (('fire_operator',), 1)
    	 0
    	 0
    	 0
    	 0
    type addr:place 225 6062 0 0
    	 3 ('ц', 149) ('ель', 43) ('Дуб', 33)
    	 193 ('Белица', 318) ('Дубровня', 279) ('СТ "Строитель 1985"', 245)
    	 3 (('natural',), 225) (('natural', 'wetland'), 149) (('natural', 'tree'), 76)
    	 828 (('natural',), 225) (('natural', 'wetland'), 149) (('natural', 'tree'), 76)
    	 0
    	 0
    	 0
    	 0
    addr:housename clothes 6058 148 0 0
    	 10 ('Н', 3348) ('н', 2262) ('ж', 260)
    	 13 ('Женская_одежда;Мужская_одежда;Детская_одежда;Колготки;Чулки;Носки;Белье;Купальники', 45) ('Женская_одежда;Мужская_одежда;Одежда_для_детей;Носки;Колготки;Чулки;Белье;Купальники', 9) ('Женская_одежда;Мужская_одежда;Детская_одежда;Чулки;Колготки;Носки;Купальники;Белье', 9)
    	 87 (('building',), 6034) (('building', 'yes'), 5933) (('addr:street',), 4996)
    	 117 (('building',), 6034) (('building', 'yes'), 5933) (('addr:street',), 4996)
    	 0
    	 0
    	 0
    	 0
    name phone 6028 131 5 2
    	 35 ('н', 4709) ('МТС', 324) ('М', 130)
    	 27 ('Многоканальный по Минску: 160 (гор, vel, mts, life) +375 (17) 207-74-74 Стоматология: +375 (29) 160-03-03', 12) ('8-02330-21367 (приемная, директор) 8-02330-21237 (заместитель директора по учебной работе', 10) ('Тел. +375 (17) 395-57-50 Велком +375 (29) 663-55-55 МТС +375 (33) 675-11-11', 8)
    	 503 (('building',), 5493) (('building', 'yes'), 4947) (('building', 'residential'), 425)
    	 203 (('building',), 5493) (('building', 'yes'), 4947) (('building', 'residential'), 425)
    	 2 ('10А', 4) ('ООО "Рефреш-К"', 1)
    	 2 ('ООО "Рефреш-К"', 1) ('10А', 1)
    	 15 (('building',), 4) (('addr:street',), 2) (('building', 'house'), 2)
    	 14 (('addr:street',), 2) (('addr:housenumber',), 2) (('website',), 1)
    name official_status 3068 6027 202 10
    	 21 ('н', 2493) ('ФАП', 158) ('п', 136)
    	 17 ('садоводческое товарищество', 5331) ('ru:деревня', 358) ('ru:сельское поселение', 92)
    	 312 (('building',), 2965) (('building', 'yes'), 2744) (('addr:street',), 255)
    	 5201 (('building',), 2965) (('building', 'yes'), 2744) (('addr:street',), 255)
    	 3 ('ФАП', 158) ('Строитель', 40) ('Кветка', 4)
    	 3 ('ФАП', 8) ('Строитель', 1) ('Кветка', 1)
    	 260 (('building',), 140) (('building', 'yes'), 122) (('amenity',), 121)
    	 82 (('name',), 10) (('addr:region', 'Псковская область'), 8) (('amenity', 'doctors'), 8)
    name office 6015 186 127 1
    	 55 ('Н', 2674) ('н', 2216) ('Слобода', 200)
    	 13 ('Копыль-Слобода Кучинка-Песочное', 48) ('Подъез от а/д Н8569 к д. Мысли', 24) ('Станьки-Углы-Закопанка- Новые Докторовичи', 15)
    	 1115 (('building',), 5341) (('building', 'yes'), 3200) (('building', 'residential'), 1796)
    	 56 (('building',), 5341) (('building', 'yes'), 3200) (('building', 'residential'), 1796)
    	 1 ('Белгосстрах', 127)
    	 1 ('Белгосстрах', 1)
    	 233 (('office',), 119) (('office', 'insurance'), 113) (('addr:street',), 53)
    	 6 (('addr:street', 'Слободская улица'), 1) (('name', 'Белгосстрах'), 1) (('addr:street',), 1)
    addr:housenumber destination:street 5977 104 0 0
    	 8 ('н', 5480) ('ж', 294) ('Н', 120)
    	 29 ('праспект Незалежнасці', 18) ('праспект Пераможцаў', 16) ('Партызанскі праспект', 9)
    	 150 (('building',), 5976) (('building', 'yes'), 5858) (('addr:street',), 5024)
    	 75 (('building',), 5976) (('building', 'yes'), 5858) (('addr:street',), 5024)
    	 0
    	 0
    	 0
    	 0
    addr:city addr:street_1 5974 27 0 0
    	 4 ('Брест', 5532) ('Кобрин', 364) ('Жлобин', 60)
    	 8 ('2-й Брестский переулок', 6) ('3-й Брестский переулок', 5) ('1-й Брестский переулок', 5)
    	 1495 (('addr:street',), 5944) (('addr:housenumber',), 5895) (('building',), 5594)
    	 61 (('addr:street',), 5944) (('addr:housenumber',), 5895) (('building',), 5594)
    	 0
    	 0
    	 0
    	 0
    addr:city was:operator 5914 3 0 0
    	 3 ('Гродно', 5870) ('Лепель', 33) ('Бородичи', 11)
    	 3 ('Гроднотеамонтаж', 1) ('ЛКУПП ЖКХ "Лепель"', 1) ('КСУП "Бородичи"', 1)
    	 8164 (('addr:street',), 5856) (('addr:housenumber',), 5764) (('building',), 4683)
    	 27 (('addr:street',), 5856) (('addr:housenumber',), 5764) (('building',), 4683)
    	 0
    	 0
    	 0
    	 0
    addr:housename official_status 1686 5879 12 8
    	 8 ('н', 1566) ('к', 84) ('ФАП', 12)
    	 17 ('садоводческое товарищество', 5331) ('ru:деревня', 358) ('ru:муниципальный район', 54)
    	 75 (('building',), 1685) (('building', 'yes'), 1639) (('addr:street',), 1199)
    	 5201 (('building',), 1685) (('building', 'yes'), 1639) (('addr:street',), 1199)
    	 1 ('ФАП', 12)
    	 1 ('ФАП', 8)
    	 19 (('building',), 12) (('building', 'yes'), 12) (('addr:street',), 11)
    	 76 (('addr:region', 'Псковская область'), 8) (('amenity', 'doctors'), 8) (('name',), 8)
    addr:housenumber phone 5873 43 1180 1
    	 9 ('н', 4658) ('10А', 1180) ('ы', 12)
    	 22 ('Многоканальный по Минску: 160 (гор, vel, mts, life) +375 (17) 207-74-74 Стоматология: +375 (29) 160-03-03', 4) ('+375 17 2373577 (стол справок), +375 17 2924072 (каб. платных услуг)', 3) ('+375 1713 9-73-51 (приемная комиссия)', 3)
    	 1282 (('building',), 5834) (('building', 'yes'), 5310) (('addr:street',), 5080)
    	 183 (('building',), 5834) (('building', 'yes'), 5310) (('addr:street',), 5080)
    	 1 ('10А', 1180)
    	 1 ('10А', 1)
    	 1258 (('building',), 1141) (('addr:street',), 1127) (('building', 'yes'), 693)
    	 6 (('addr:street', 'Грушевская улица'), 1) (('addr:street',), 1) (('building', 'yes'), 1)
    addr:city old_ref 5870 1 0 0
    	 1 ('Гродно', 5870)
    	 1 ('Автостанция "Гродно"', 1)
    	 8135 (('addr:street',), 5813) (('addr:housenumber',), 5742) (('building',), 4641)
    	 6 (('addr:street',), 5813) (('addr:housenumber',), 5742) (('building',), 4641)
    	 0
    	 0
    	 0
    	 0
    operator owner 5869 994 1865 140
    	 61 ('Беларусбанк', 2310) ('БЧ', 719) ('Белагропромбанк', 456)
    	 60 ('ОАО «Белорусский банк развития и реконструкции «Белинвестбанк»', 329) ('ОАО «АСБ Беларусбанк»', 210) ('ОАО «Белагропромбанк»', 70)
    	 2871 (('amenity',), 4876) (('name',), 3336) (('amenity', 'atm'), 3161)
    	 586 (('amenity',), 4876) (('name',), 3336) (('amenity', 'atm'), 3161)
    	 22 ('Беларусбанк', 770) ('БЧ', 719) ('БПС-Сбербанк', 188)
    	 22 ('ОАО «Белорусский банк развития и реконструкции «Белинвестбанк»', 47) ('ОАО «АСБ Беларусбанк»', 30) ('ОАО «Приорбанк»', 13)
    	 1405 (('name',), 1200) (('amenity',), 1139) (('amenity', 'atm'), 756)
    	 345 (('name',), 132) (('amenity',), 131) (('operator',), 124)
    addr:housenumber clothes 5819 113 0 0
    	 8 ('н', 3562) ('Н', 1440) ('ж', 637)
    	 13 ('Женская_одежда;Мужская_одежда;Детская_одежда;Колготки;Чулки;Носки;Белье;Купальники', 35) ('Женская_одежда;Мужская_одежда;Одежда_для_детей;Носки;Колготки;Чулки;Белье;Купальники', 7) ('Женская_одежда;Мужская_одежда;Детская_одежда;Чулки;Колготки;Носки;Купальники;Белье', 7)
    	 134 (('building',), 5807) (('building', 'yes'), 5696) (('addr:street',), 4904)
    	 117 (('building',), 5807) (('building', 'yes'), 5696) (('addr:street',), 4904)
    	 0
    	 0
    	 0
    	 0
    ref nat_ref 5809 349 2342 104
    	 63 ('Р1', 970) ('Р2', 909) ('М4', 889)
    	 31 ('Р80', 66) ('Н-28', 44) ('Н136', 24)
    	 674 (('highway',), 5691) (('surface',), 5599) (('surface', 'asphalt'), 5506)
    	 136 (('highway',), 5691) (('surface',), 5599) (('surface', 'asphalt'), 5506)
    	 29 ('М4', 889) ('Р28', 228) ('Р15', 223)
    	 29 ('Р80', 22) ('Н-28', 22) ('М4', 10)
    	 493 (('highway',), 2323) (('surface',), 2261) (('surface', 'asphalt'), 2230)
    	 129 (('highway',), 93) (('ref',), 84) (('surface',), 67)
    addr:housenumber website 5751 45 0 0
    	 11 ('н', 5480) ('кн', 129) ('ж', 98)
    	 29 ('Баня-Минск.бел', 4) ('http://чайхана.бел', 3) ('https://gacyk.slutsk-vedy.gov.by/гуо-ясли-сад-аг-гацук-слуцкого-района/об-учреждении', 3)
    	 135 (('building',), 5751) (('building', 'yes'), 5655) (('addr:street',), 4839)
    	 216 (('building',), 5751) (('building', 'yes'), 5655) (('addr:street',), 4839)
    	 0
    	 0
    	 0
    	 0
    destination operator 2303 5611 45 4
    	 32 ('Гомель', 1536) ('Минск', 165) ('Мінск', 156)
    	 375 ('КТУП «Гомельоблпассажиртранс»', 1665) ('ОАО "Гомельавтотранс"', 719) ('Минские кабельные сети', 426)
    	 286 (('oneway', 'yes'), 1941) (('oneway',), 1941) (('highway',), 1941)
    	 8178 (('oneway', 'yes'), 1941) (('oneway',), 1941) (('highway',), 1941)
    	 4 ('Гомель', 32) ('Неман', 7) ('Вилия', 4)
    	 4 ('Гомель', 1) ('Ясень', 1) ('Неман', 1)
    	 101 (('oneway',), 33) (('oneway', 'yes'), 33) (('highway',), 33)
    	 30 (('name',), 3) (('opening_hours',), 3) (('shop',), 2)
    addr:housename FIXME 5607 150 0 0
    	 7 ('н', 5220) ('ж', 140) ('к', 140)
    	 34 ('проверить куда она приведёт', 12) ('беседка? зонтик? ...? нужны доп. теги', 10) ('необходимо уточнить существуюшие линии тротуаров', 8)
    	 93 (('building',), 5606) (('building', 'yes'), 5456) (('addr:street',), 3976)
    	 158 (('building',), 5606) (('building', 'yes'), 5456) (('addr:street',), 3976)
    	 0
    	 0
    	 0
    	 0
    destination:forward wikipedia 5603 1719 0 0
    	 22 ('Гомель', 2815) ('Мінск', 1005) ('Барысаў', 456)
    	 1399 ('be:Праспект Дзяржынскага (Мінск)', 202) ('be:Вуліца Чалюскінцаў (Магілёў)', 15) ('be:Першамайская вуліца (Магілёў)', 8)
    	 120 (('highway',), 5603) (('surface', 'asphalt'), 5037) (('surface',), 5037)
    	 4774 (('highway',), 5603) (('surface', 'asphalt'), 5037) (('surface',), 5037)
    	 0
    	 0
    	 0
    	 0
    official_short_type addr:housenumber 5533 102 607 33
    	 11 ('ТП', 3690) ('РП', 589) ('ГРП', 528)
    	 43 ('ТП', 23) ('ГРП', 6) ('ЦТП', 4)
    	 804 (('ref',), 5183) (('power',), 4425) (('building',), 4412)
    	 92 (('ref',), 5183) (('power',), 4425) (('building',), 4412)
    	 6 ('ТП', 410) ('ЦТП', 111) ('ГРП', 44)
    	 6 ('ТП', 23) ('ГРП', 3) ('ЦТП', 2)
    	 726 (('ref',), 555) (('building',), 496) (('building', 'service'), 474)
    	 44 (('building',), 27) (('addr:street',), 26) (('building', 'yes'), 22)
    description brand 5525 1949 362 23
    	 15 ('н', 5088) ('Шиномонтаж', 358) ('кн', 46)
    	 103 ('Белоруснефть', 884) ('Беларусбанк', 266) ('Белшина', 169)
    	 412 (('building',), 5225) (('building', 'yes'), 5219) (('addr:street',), 4998)
    	 5186 (('building',), 5225) (('building', 'yes'), 5219) (('addr:street',), 4998)
    	 4 ('Шиномонтаж', 358) ('Связной', 2) ('Белнефтехим', 1)
    	 4 ('Связной', 14) ('Белнефтехим', 7) ('Шиномонтаж', 1)
    	 357 (('shop',), 360) (('service', 'tyres'), 358) (('service',), 358)
    	 137 (('name',), 22) (('shop',), 18) (('brand:wikidata', 'Q65371'), 14)
    from operator 2688 5449 53 290
    	 51 ('Гомель', 1728) ('Минск', 495) ('Автобусный парк', 95)
    	 362 ('КТУП «Гомельоблпассажиртранс»', 1665) ('ОАО "Гомельавтотранс"', 719) ('Минские кабельные сети', 426)
    	 495 (('to',), 2688) (('route',), 2688) (('type',), 2688)
    	 7880 (('to',), 2688) (('route',), 2688) (('type',), 2688)
    	 11 ('Гомель', 36) ('Химволокно', 5) ('ТЭЦ-2', 3)
    	 11 ('Белинвестбанк', 252) ('Евроопт', 26) ('ОАО "Нафтан"', 3)
    	 165 (('to',), 53) (('route',), 53) (('type',), 53)
    	 419 (('amenity',), 267) (('amenity', 'atm'), 203) (('name',), 151)
    description opening_hours 5428 125 0 0
    	 6 ('н', 5353) ('кн', 46) ('выходные', 12)
    	 107 ('Пн-Пт 9-18 Сб-Вс 10-17', 3) ('01:00-10:00 open "через окно выдачи", 10:00-01:00', 2) ('круглосуточно', 2)
    	 41 (('building',), 5414) (('building', 'yes'), 5413) (('addr:street',), 5208)
    	 755 (('building',), 5414) (('building', 'yes'), 5413) (('addr:street',), 5208)
    	 0
    	 0
    	 0
    	 0
    official_short_type inscription 5393 47 0 0
    	 6 ('ВЛ', 3814) ('Ф', 1152) ('ПС', 364)
    	 45 ('В 1931 – 1936 Г.Г.\nВИЦЕ-ПРЕЗИДЕНТОМ АН БССР\nИ ДИРЕКТОРОМ\nИНСТИТУТА ИСТОРИИ АН БССР\nРАБОТАЛ ИЗВЕСТНЫЙ\nБЕЛОРУССКИЙ СОВЕТСКИЙ ИСТОРИК\nАКАДЕМИК АН БССР\nВАСИЛИЙ КАРПОВИЧ\nЩЕРБАКОВ', 2) ('На этом месте 26 июня 1944 г. в жестокой схватке с фашистскими оккупантами был спасён от взрыва мост группой бойцов под командованием ст. сержанта Блохина Ф. Т., удостоенного за этот подвиг звания Героя Советского Союза.', 2) ('У гэтым доме ў 1919-1931 гг. жыў Адам Сямёнавіч Славінскі, член КПСС з 1907 г., відны партыйны и дзяржаўны дзеяч Беларускай ССР.', 1)
    	 1633 (('power',), 5369) (('voltage',), 5315) (('cables',), 4944)
    	 130 (('power',), 5369) (('voltage',), 5315) (('cables',), 4944)
    	 0
    	 0
    	 0
    	 0
    fence_type source 12 5292 0 0
    	 1 ('да', 12)
    	 12 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 2149) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 1102) ('Национальное кадастровое агентство nca.by', 1094)
    	 2 (('barrier',), 12) (('barrier', 'fence'), 12)
    	 827 (('barrier',), 12) (('barrier', 'fence'), 12)
    	 0
    	 0
    	 0
    	 0
    cycleway:left source 12 5292 0 0
    	 1 ('да', 12)
    	 12 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 2149) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 1102) ('Национальное кадастровое агентство nca.by', 1094)
    	 6 (('int_name',), 12) (('name', 'улица 1 Мая'), 12) (('name',), 12)
    	 827 (('int_name',), 12) (('name', 'улица 1 Мая'), 12) (('name',), 12)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:street addr:region 7 5204 0 0
    	 1 ('Гомельская', 7)
    	 1 ('Гомельская область', 5204)
    	 26 (('fire_hydrant:type',), 7) (('fire_hydrant:position', 'lane'), 7) (('fire_hydrant:diameter',), 7)
    	 10533 (('fire_hydrant:type',), 7) (('fire_hydrant:position', 'lane'), 7) (('fire_hydrant:diameter',), 7)
    	 0
    	 0
    	 0
    	 0
    destination:forward addr:region 5 5204 0 0
    	 1 ('Гомель', 5)
    	 1 ('Гомельская область', 5204)
    	 26 (('highway', 'trunk_link'), 5) (('destination:backward',), 5) (('highway',), 5)
    	 10533 (('highway', 'trunk_link'), 5) (('destination:backward',), 5) (('highway',), 5)
    	 0
    	 0
    	 0
    	 0
    addr:region access 5204 1 0 0
    	 1 ('Гомельская область', 5204)
    	 1 ('Гомельская область,деревня Покалюбичи', 1)
    	 10533 (('name',), 4860) (('addr:district',), 4834) (('addr:country', 'BY'), 4820)
    	 20 (('name',), 4860) (('addr:district',), 4834) (('addr:country', 'BY'), 4820)
    	 0
    	 0
    	 0
    	 0
    type addr:region 1 5204 0 0
    	 1 ('ель', 1)
    	 1 ('Гомельская область', 5204)
    	 2 (('natural',), 1) (('natural', 'tree'), 1)
    	 10533 (('natural',), 1) (('natural', 'tree'), 1)
    	 0
    	 0
    	 0
    	 0
    addr:housename was:name 5168 140 0 0
    	 14 ('н', 4002) ('Н', 837) ('к', 147)
    	 45 ('Неман-Лада', 8) ('Кафе "Метеорит"', 5) ('Белоруснефть, АЗС №37', 5)
    	 128 (('building',), 5152) (('building', 'yes'), 5020) (('addr:street',), 3830)
    	 312 (('building',), 5152) (('building', 'yes'), 5020) (('addr:street',), 3830)
    	 0
    	 0
    	 0
    	 0
    destination:backward wikipedia 5162 1916 0 0
    	 22 ('Гомель', 2252) ('Мінск', 1608) ('Валожын', 300)
    	 1616 ('be:Праспект Дзяржынскага (Мінск)', 101) ('ru:Улица Есенина (Минск)', 22) ('be:Вуліца Чалюскінцаў (Магілёў)', 15)
    	 117 (('surface',), 5162) (('surface', 'asphalt'), 5162) (('highway',), 5162)
    	 5804 (('surface',), 5162) (('surface', 'asphalt'), 5162) (('highway',), 5162)
    	 0
    	 0
    	 0
    	 0
    official_short_type wikipedia 5119 178 0 0
    	 2 ('Ф', 5088) ('РП', 31)
    	 160 ('be:Фядоска', 6) ('be:Фербіна', 4) ('be:Фаміно (Хоцімскі раён)', 2)
    	 119 (('ref',), 5118) (('power',), 5112) (('power', 'minor_line'), 5088)
    	 770 (('ref',), 5118) (('power',), 5112) (('power', 'minor_line'), 5088)
    	 0
    	 0
    	 0
    	 0
    to operator 2234 5092 49 38
    	 51 ('Гомель', 1632) ('Минск', 165) ('Автобусный парк', 76)
    	 347 ('КТУП «Гомельоблпассажиртранс»', 1665) ('ОАО "Гомельавтотранс"', 719) ('Минские кабельные сети', 426)
    	 474 (('type',), 2234) (('name',), 2234) (('type', 'route'), 2234)
    	 7537 (('type',), 2234) (('name',), 2234) (('type', 'route'), 2234)
    	 10 ('Гомель', 34) ('Химволокно', 4) ('ТЭЦ-2', 3)
    	 10 ('Евроопт', 26) ('ОАО "Нафтан"', 3) ('Ледовый дворец', 2)
    	 150 (('route',), 49) (('type',), 49) (('from',), 49)
    	 149 (('name',), 22) (('amenity',), 16) (('fire_hydrant:type',), 9)
    fire_hydrant:city network 5080 321 1016 2
    	 1 ('Минск', 5080)
    	 5 ('Минский метрополитен', 262) ('Минское отделение', 50) ('городские маршруты Минска', 4)
    	 1120 (('emergency', 'fire_hydrant'), 5080) (('fire_hydrant:type',), 5080) (('emergency',), 5080)
    	 341 (('emergency', 'fire_hydrant'), 5080) (('fire_hydrant:type',), 5080) (('emergency',), 5080)
    	 1 ('Минск', 1016)
    	 1 ('Минск', 2)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 17 (('minsk_PT:note',), 2) (('shelter', 'yes'), 2) (('shelter',), 2)
    network addr:district 8 5011 0 0
    	 3 ('Борисов', 4) ('Минск', 2) ('Бобруйск', 2)
    	 3 ('Минский район', 3969) ('Борисовский район', 614) ('Бобруйский район', 428)
    	 40 (('name',), 8) (('route',), 6) (('type',), 6)
    	 4472 (('name',), 8) (('route',), 6) (('type',), 6)
    	 0
    	 0
    	 0
    	 0
    type operator 765 5011 0 0
    	 3 ('ц', 536) ('ель', 199) ('Дуб', 30)
    	 713 ('КТУП «Гомельоблпассажиртранс»', 1665) ('ОАО "Гомельавтотранс"', 719) ('Минские кабельные сети', 426)
    	 3 (('natural',), 765) (('natural', 'wetland'), 536) (('natural', 'tree'), 229)
    	 8465 (('natural',), 765) (('natural', 'wetland'), 536) (('natural', 'tree'), 229)
    	 0
    	 0
    	 0
    	 0
    building fixme 5002 1467 0 0
    	 18 ('Н', 4025) ('н', 502) ('р', 215)
    	 294 ('адрес', 211) ('расположение', 72) ('положение/адрес', 68)
    	 68 (('name',), 991) (('name', 'Н'), 825) (('addr:street',), 263)
    	 1744 (('name',), 991) (('name', 'Н'), 825) (('addr:street',), 263)
    	 0
    	 0
    	 0
    	 0
    addr:housename architect 4966 144 0 0
    	 12 ('н', 3828) ('Н', 837) ('к', 154)
    	 30 ('А. Ю. Заболотная', 12) ('Уладзімір Мікітавіч Еўдакімаў', 10) ('Рубаненко Борис Рафаилович', 9)
    	 94 (('building',), 4949) (('building', 'yes'), 4830) (('addr:street',), 3689)
    	 244 (('building',), 4949) (('building', 'yes'), 4830) (('addr:street',), 3689)
    	 0
    	 0
    	 0
    	 0
    description heritage:description 4935 132 0 0
    	 5 ('н', 4876) ('ж', 44) ('Н', 9)
    	 93 ('Былы гарадскі сад (Цэнтральны дзіцячы парк імя Горкага ў складзе: планіровачная структура, ландшафт, адміністрацыйны будынак, агароджа)', 4) ('Будынак былой жаночай Марыінскай гімназіі', 4) ('Ансамбль будынкаў і бульвар па вул.Леніна ў квартале пр.Незалежнасці – вул.Інтэрнацыянальная', 3)
    	 8 (('building', 'yes'), 4935) (('building',), 4935) (('addr:street',), 4745)
    	 577 (('building', 'yes'), 4935) (('building',), 4935) (('addr:street',), 4745)
    	 0
    	 0
    	 0
    	 0
    designation addr:district 17 4916 0 0
    	 1 ('б', 17)
    	 17 ('Глубокский район', 726) ('Витебский район', 717) ('Брестская обл.', 644)
    	 8 (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 17) (('addr:street',), 17) (('building', 'yes'), 17)
    	 9461 (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 17) (('addr:street',), 17) (('building', 'yes'), 17)
    	 0
    	 0
    	 0
    	 0
    type source 22 4873 0 0
    	 2 ('ц', 20) ('ель', 2)
    	 21 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 2149) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 1102) ('Национальное кадастровое агентство nca.by', 1094)
    	 3 (('natural',), 22) (('natural', 'wetland'), 20) (('natural', 'tree'), 2)
    	 771 (('natural',), 22) (('natural', 'wetland'), 20) (('natural', 'tree'), 2)
    	 0
    	 0
    	 0
    	 0
    building:levels source 19 4818 0 0
    	 1 ('Н', 19)
    	 19 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 2149) ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 1102) ('Национальное кадастровое агентство nca.by', 1094)
    	 2 (('building', 'yes'), 19) (('building',), 19)
    	 605 (('building', 'yes'), 19) (('building',), 19)
    	 0
    	 0
    	 0
    	 0
    name addr:street_1 4695 400 114 48
    	 68 ('н', 3601) ('п', 255) ('к', 230)
    	 29 ('2-й Брестский переулок', 48) ('3-й Брестский переулок', 40) ('1-й Брестский переулок', 40)
    	 406 (('building',), 4392) (('building', 'yes'), 4040) (('building:levels',), 388)
    	 127 (('building',), 4392) (('building', 'yes'), 4040) (('building:levels',), 388)
    	 23 ('Двинская улица', 23) ('Кобринская улица', 15) ('Черниговская улица', 12)
    	 23 ('2-й Брестский переулок', 6) ('1-й Брестский переулок', 5) ('3-й Брестский переулок', 5)
    	 121 (('highway',), 111) (('int_name',), 97) (('highway', 'residential'), 84)
    	 105 (('addr:street',), 48) (('building',), 48) (('addr:housenumber',), 48)
    addr:unit addr:region 2 4693 0 0
    	 1 ('Б', 2)
    	 2 ('Брестская область', 4563) ('Брянская область', 130)
    	 18 (('addr:housenumber', '44'), 2) (('surface',), 2) (('amenity', 'parking'), 2)
    	 10374 (('addr:housenumber', '44'), 2) (('surface',), 2) (('amenity', 'parking'), 2)
    	 0
    	 0
    	 0
    	 0
    destination:backward operator 400 4686 4 1
    	 5 ('Гомель', 192) ('Минск', 165) ('Мінск', 32)
    	 219 ('КТУП «Гомельоблпассажиртранс»', 1665) ('ОАО "Гомельавтотранс"', 719) ('Минские кабельные сети', 426)
    	 77 (('surface',), 400) (('surface', 'asphalt'), 400) (('destination:forward',), 400)
    	 6883 (('surface',), 400) (('surface', 'asphalt'), 400) (('destination:forward',), 400)
    	 1 ('Гомель', 4)
    	 1 ('Гомель', 1)
    	 25 (('surface', 'asphalt'), 4) (('destination:ref:backward',), 4) (('maxaxleload',), 4)
    	 10 (('contact:phone',), 1) (('contact:website',), 1) (('shop',), 1)
    operator note 4537 4672 4 4
    	 59 ('Беларусбанк', 1540) ('е', 1251) ('я', 601)
    	 1389 ('Необходим тэг add:street или add:place', 256) ('Уточнить обязательно название улицы, если неправильно то исправить!!!', 168) ('Не надо ставить эту камеру на линию дороги!', 132)
    	 1510 (('name',), 2969) (('amenity',), 2785) (('amenity', 'atm'), 2154)
    	 3357 (('name',), 2969) (('amenity',), 2785) (('amenity', 'atm'), 2154)
    	 4 ('Стиль', 1) ('Гараж', 1) ('ООО "Чайка",', 1)
    	 4 ('Стиль', 1) ('Гараж', 1) ('ООО "Чайка",', 1)
    	 29 (('shop',), 3) (('name',), 2) (('shop', 'clothes'), 1)
    	 20 (('building',), 3) (('building:levels',), 3) (('building:levels', '1'), 2)
    was:name:prefix note 4651 22 0 0
    	 3 ('деревня', 3892) ('хутор', 747) ('станция', 12)
    	 14 ('несуществующая ныне деревня', 4) ('исчезнувшая деревня', 2) ('официально считается хутором', 2)
    	 2827 (('name',), 4651) (('place',), 4651) (('abandoned:place',), 4566)
    	 121 (('name',), 4651) (('place',), 4651) (('abandoned:place',), 4566)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city to 4614 10 1815 4
    	 4 ('Минск', 3048) ('Речица', 1532) ('Озерщина', 33)
    	 7 ('Национальный Аэропорт "Минск"', 3) ('Речица', 2) ('Автостанция Речица', 1)
    	 1639 (('fire_hydrant:type',), 4614) (('emergency', 'fire_hydrant'), 4614) (('emergency',), 4614)
    	 47 (('fire_hydrant:type',), 4614) (('emergency', 'fire_hydrant'), 4614) (('emergency',), 4614)
    	 3 ('Минск', 1016) ('Речица', 766) ('Озерщина', 33)
    	 3 ('Речица', 2) ('Минск', 1) ('Озерщина', 1)
    	 1631 (('fire_hydrant:type',), 1815) (('emergency', 'fire_hydrant'), 1815) (('emergency',), 1815)
    	 27 (('public_transport:version', '2'), 4) (('type',), 4) (('from',), 4)
    ref destination:ref:forward 4597 19 2413 7
    	 6 ('М1', 4148) ('М14', 187) ('Р53', 152)
    	 3 ('Р53', 12) ('М1', 4) ('М14', 3)
    	 256 (('highway',), 4583) (('surface',), 4545) (('maxaxleload',), 4512)
    	 31 (('highway',), 4583) (('surface',), 4545) (('maxaxleload',), 4512)
    	 3 ('М1', 2074) ('М14', 187) ('Р53', 152)
    	 3 ('Р53', 4) ('М1', 2) ('М14', 1)
    	 205 (('highway',), 2410) (('surface',), 2391) (('maxaxleload',), 2383)
    	 31 (('highway', 'motorway_link'), 7) (('surface', 'asphalt'), 7) (('surface',), 7)
    fire_hydrant:city addr:district 1017 4533 0 0
    	 2 ('Минск', 1016) ('Могилёв', 1)
    	 2 ('Минский район', 3969) ('Могилёвский район', 564)
    	 1136 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 3557 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 0
    	 0
    	 0
    	 0
    name fee 4519 84 1343 7
    	 27 ('н', 2770) ('Беларусбанк', 1045) ('Приорбанк', 197)
    	 13 ('Беларусбанк', 14) ('Для сотрудников импортера VW в РБ', 10) ('Белгазпромбанк', 9)
    	 1431 (('building',), 3265) (('building', 'yes'), 3020) (('amenity',), 1334)
    	 39 (('building',), 3265) (('building', 'yes'), 3020) (('amenity',), 1334)
    	 6 ('Беларусбанк', 1045) ('Приорбанк', 197) ('Белгазпромбанк', 64)
    	 6 ('Беларусбанк', 2) ('Приорбанк', 1) ('БелСвиссБанк', 1)
    	 1276 (('amenity',), 1320) (('amenity', 'bank'), 760) (('int_name',), 702)
    	 14 (('amenity', 'atm'), 7) (('amenity',), 7) (('int_name',), 3)
    addr:housename nat_ref 4466 60 0 0
    	 2 ('Н', 4464) ('М', 2)
    	 17 ('Н-28', 22) ('М4', 10) ('Н136', 6)
    	 29 (('building',), 4434) (('building', 'yes'), 4386) (('addr:street',), 4032)
    	 96 (('building',), 4434) (('building', 'yes'), 4386) (('addr:street',), 4032)
    	 0
    	 0
    	 0
    	 0
    addr:postcode wikipedia 4451 135 0 0
    	 3 ('Жлобин', 4444) ('Лидский район', 6) ('Белтелеком', 1)
    	 108 ('ru:Белтелеком', 3) ('ru:Лебедёвка (Жлобинский район)', 3) ('ru:Жлобин', 2)
    	 66 (('addr:street',), 4444) (('building',), 4444) (('addr:housenumber',), 4444)
    	 446 (('addr:street',), 4444) (('building',), 4444) (('addr:housenumber',), 4444)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber fence_type 4450 269 0 0
    	 7 ('н', 4110) ('ж', 245) ('Ж', 60)
    	 27 ('каменный ж.б.', 147) ('Мелалло профиль', 21) ('ж/б плиты', 16)
    	 83 (('building',), 4450) (('building', 'yes'), 4387) (('addr:street',), 3740)
    	 20 (('building',), 4450) (('building', 'yes'), 4387) (('addr:street',), 3740)
    	 0
    	 0
    	 0
    	 0
    addr:housename brand:wikipedia 4388 1849 0 0
    	 15 ('н', 4002) ('к', 119) ('ж', 100)
    	 34 ('ru:Fix Price (сеть магазинов)', 330) ('be:Белпошта', 324) ('be:Белаграпрамбанк', 292)
    	 137 (('building',), 4380) (('building', 'yes'), 4256) (('addr:street',), 3127)
    	 1892 (('building',), 4380) (('building', 'yes'), 4256) (('addr:street',), 3127)
    	 0
    	 0
    	 0
    	 0
    destination:backward addr:district 5 4381 0 0
    	 2 ('Гомель', 4) ('Минск', 1)
    	 2 ('Минский район', 3969) ('Гомельский район', 412)
    	 32 (('surface', 'asphalt'), 5) (('maxaxleload',), 5) (('surface',), 5)
    	 3293 (('surface', 'asphalt'), 5) (('maxaxleload',), 5) (('surface',), 5)
    	 0
    	 0
    	 0
    	 0
    addr:city fire_hydrant:street 4317 147 31 29
    	 22 ('Брест', 2766) ('Гомель', 1172) ('Киров', 94)
    	 29 ('Советская', 40) ('Первомайская', 20) ('пер. Светлогорский', 8)
    	 2812 (('addr:street',), 4247) (('addr:housenumber',), 4224) (('building',), 3783)
    	 198 (('addr:street',), 4247) (('addr:housenumber',), 4224) (('building',), 3783)
    	 7 ('Урожайная', 23) ('Энергетиков', 2) ('Сосновая', 2)
    	 7 ('Энергетиков', 8) ('Урожайная', 6) ('Садовая', 5)
    	 55 (('building',), 29) (('addr:street',), 28) (('addr:housenumber',), 26)
    	 62 (('fire_hydrant:type',), 29) (('fire_hydrant:diameter',), 29) (('name',), 29)
    description full_name 4299 119 2 2
    	 17 ('н', 4187) ('кн', 46) ('ж', 42)
    	 79 ('Центр технического обслуживания кассовых суммирующих аппаратов', 3) ('“Территориальный центр социального обслуживания населения «Теплый дом»', 3) ('Учреждение образования "Государственный центр коррекционно-развивающего обучения и реабилитации г. Гродно"', 3)
    	 102 (('building',), 4289) (('building', 'yes'), 4284) (('addr:street',), 4119)
    	 564 (('building',), 4289) (('building', 'yes'), 4284) (('addr:street',), 4119)
    	 2 ('Школьный народный минералогический музей "Карат"', 1) ('Станция непрерывного измерения содержания приоритетных загрязняющих веществ в атмосферном воздухе', 1)
    	 2 ('Школьный народный минералогический музей "Карат"', 1) ('Станция непрерывного измерения содержания приоритетных загрязняющих веществ в атмосферном воздухе', 1)
    	 19 (('name',), 2) (('tourism', 'museum'), 1) (('operator', 'СШ №16 г.Гродно'), 1)
    	 33 (('operator',), 2) (('description',), 1) (('tourism', 'museum'), 1)
    addr:housename fire_hydrant:city 371 4199 0 0
    	 4 ('н', 348) ('к', 14) ('М', 6)
    	 5 ('Минск', 3048) ('Речица', 766) ('Микашевичи', 318)
    	 58 (('building',), 371) (('building', 'yes'), 360) (('addr:street',), 259)
    	 1863 (('building',), 371) (('building', 'yes'), 360) (('addr:street',), 259)
    	 0
    	 0
    	 0
    	 0
    building brand 1217 4198 0 0
    	 13 ('Н', 805) ('н', 192) ('р', 82)
    	 147 ('Белоруснефть', 1768) ('Беларусбанк', 532) ('Копеечка', 273)
    	 32 (('name',), 261) (('name', 'Н'), 165) (('addr:street',), 89)
    	 5844 (('name',), 261) (('name', 'Н'), 165) (('addr:street',), 89)
    	 0
    	 0
    	 0
    	 0
    official_short_name name 4189 2224 22 429
    	 5 ('ТП', 3180) ('ГРП', 486) ('ШРП', 228)
    	 1371 ('ТП', 198) ('ЦТП', 126) ('ГРП', 93)
    	 39 (('building',), 4189) (('building', 'service'), 4189) (('ref',), 2859)
    	 1088 (('building',), 4189) (('building', 'service'), 4189) (('ref',), 2859)
    	 5 ('ЗТП', 11) ('ГРП', 3) ('КНС', 3)
    	 5 ('ТП', 198) ('ГРП', 93) ('КНС', 77)
    	 39 (('building',), 22) (('building', 'service'), 22) (('ref',), 17)
    	 136 (('building',), 372) (('building', 'yes'), 224) (('power',), 137)
    addr:housename destination:street 4133 227 0 0
    	 10 ('н', 3480) ('Н', 279) ('к', 154)
    	 34 ('праспект Пераможцаў', 40) ('праспект Незалежнасці', 36) ('Даўгінаўскі тракт', 12)
    	 87 (('building',), 4125) (('building', 'yes'), 4008) (('addr:street',), 3012)
    	 86 (('building',), 4125) (('building', 'yes'), 4008) (('addr:street',), 3012)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:street wikipedia 4105 778 0 0
    	 28 ('Гомельская', 2800) ('Новая', 732) ('Дубро', 143)
    	 692 ('ru:Красноармейская улица (Минск)', 7) ('be:Вуліца Карла Маркса, Мінск', 7) ('ru:Новая Марьевка (Гомельская область)', 4)
    	 202 (('fire_hydrant:type',), 4105) (('fire_hydrant:diameter',), 4105) (('name',), 4105)
    	 2478 (('fire_hydrant:type',), 4105) (('fire_hydrant:diameter',), 4105) (('name',), 4105)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city brand 4064 8 0 0
    	 1 ('Минск', 4064)
    	 4 ('Минская школа киноискусства', 5) ('Минскоблгаз', 1) ('Аква-Минск', 1)
    	 1120 (('emergency', 'fire_hydrant'), 4064) (('fire_hydrant:type',), 4064) (('emergency',), 4064)
    	 162 (('emergency', 'fire_hydrant'), 4064) (('fire_hydrant:type',), 4064) (('emergency',), 4064)
    	 0
    	 0
    	 0
    	 0
    description artist_name 4051 136 2 1
    	 8 ('н', 4028) ('Н', 10) ('Груша Ричард', 4)
    	 84 ('Пантелеев В. И.', 7) ('Алёна Василькович', 6) ('А.Гурщенкова', 5)
    	 35 (('building',), 4040) (('building', 'yes'), 4040) (('addr:street',), 3888)
    	 418 (('building',), 4040) (('building', 'yes'), 4040) (('addr:street',), 3888)
    	 1 ('Груша Ричард', 2)
    	 1 ('Груша Ричард', 1)
    	 12 (('memorial',), 2) (('historic', 'memorial'), 2) (('name',), 2)
    	 10 (('natural',), 1) (('natural', 'stone'), 1) (('inscription',), 1)
    height addr:street 133 4044 0 0
    	 1 ('ф', 133)
    	 133 ('Торфяная улица', 259) ('Краснофлотская улица', 173) ('улица Трифонова', 118)
    	 2 (('barrier',), 133) (('barrier', 'fence'), 133)
    	 1884 (('barrier',), 133) (('barrier', 'fence'), 133)
    	 0
    	 0
    	 0
    	 0
    designation description 2550 4037 11 9
    	 23 ('б', 2431) ('парк', 44) ('Городище', 14)
    	 2482 ('ARMTEK занимается оптовой и розничной торговлей автозапчастями, расходными материалами и аксессуарами для легковых и грузовых автомобилей', 71) ('Октябрьский - Копцевичи', 37) ('Посетив «Царское золото», можно прикоснуться к настоящим дворянским традициям, обрамленным в стиль современности.', 34)
    	 155 (('name',), 2519) (('building',), 2445) (('building', 'yes'), 2443)
    	 8567 (('name',), 2519) (('building',), 2445) (('building', 'yes'), 2443)
    	 7 ('Колодец', 3) ('Автобусная остановка', 2) ('Административное здание', 2)
    	 7 ('Проходная', 2) ('Колодец', 2) ('Автобусная остановка', 1)
    	 57 (('name',), 7) (('amenity',), 4) (('amenity', 'drinking_water'), 3)
    	 86 (('addr:street',), 4) (('building',), 4) (('addr:housenumber',), 4)
    brand official_name 4021 192 1 1
    	 34 ('Белоруснефть', 1768) ('Беларусбанк', 798) ('А-100', 609)
    	 104 ('Лучники - Серяги - Знамя - Ковержицы', 32) ('Замошье - Лучицы - Б.Горожа - М.Горожа', 17) ('Дрозды - Лучежевичи - Меребель', 7)
    	 4563 (('amenity',), 3766) (('name',), 3414) (('opening_hours',), 3340)
    	 718 (('amenity',), 3766) (('name',), 3414) (('opening_hours',), 3340)
    	 1 ('ОАО Лиданефтепродукт', 1)
    	 1 ('ОАО Лиданефтепродукт', 1)
    	 8 (('addr:postcode',), 1) (('addr:street',), 1) (('building', 'retail'), 1)
    	 6 (('name',), 1) (('landuse', 'industrial'), 1) (('start_date',), 1)
    addr:city destination:forward 4014 70 714 25
    	 15 ('Гомель', 3516) ('Орша', 204) ('Барановичи', 110)
    	 31 ('Брэст', 7) ('Мінск;Брэст', 6) ('12-ы кіламетр МКАД;Слуцк;Гродна;Брэст', 6)
    	 2430 (('addr:street',), 3874) (('addr:housenumber',), 3812) (('name',), 2843)
    	 153 (('addr:street',), 3874) (('addr:housenumber',), 3812) (('name',), 2843)
    	 6 ('Гомель', 586) ('Барановичи', 110) ('Магілёў', 6)
    	 6 ('Брэст', 7) ('Гомель', 5) ('Барановичи', 5)
    	 2207 (('addr:street',), 699) (('addr:housenumber',), 688) (('name',), 496)
    	 88 (('highway',), 25) (('surface',), 24) (('surface', 'asphalt'), 24)
    addr:housenumber addr:door 4003 8 21 2
    	 6 ('1А', 3265) ('н', 548) ('Н', 120)
    	 7 ('2н', 2) ('01А', 1) ('100Б', 1)
    	 2929 (('building',), 3895) (('addr:street',), 3735) (('building', 'yes'), 2570)
    	 83 (('building',), 3895) (('addr:street',), 3735) (('building', 'yes'), 2570)
    	 2 ('100Б', 20) ('1а', 1)
    	 2 ('100Б', 1) ('1а', 1)
    	 63 (('building',), 21) (('addr:street',), 19) (('building', 'yes'), 9)
    	 16 (('shop',), 2) (('name',), 2) (('phone',), 1)
    description old_addr 3989 229 0 0
    	 3 ('н', 3127) ('улица', 812) ('Н', 50)
    	 116 ('улица Энгельса, 49А', 4) ('улица Энгельса, 100', 4) ('улица Энгельса, 109Б', 2)
    	 16 (('building',), 3177) (('building', 'yes'), 3177) (('addr:street',), 3059)
    	 207 (('building',), 3177) (('building', 'yes'), 3177) (('addr:street',), 3059)
    	 0
    	 0
    	 0
    	 0
    description branch 3988 103 2 2
    	 8 ('н', 3975) ('ж', 6) ('Центр банковских услуг', 2)
    	 78 ('РУП "Минскэнерго"', 15) ('Центр банковских услуг №106 филиала №113', 3) ('Центр банковских услуг 119/1', 2)
    	 85 (('building',), 3983) (('building', 'yes'), 3983) (('addr:street',), 3835)
    	 415 (('building',), 3983) (('building', 'yes'), 3983) (('addr:street',), 3835)
    	 2 ('РКЦ №29', 1) ('УРМ-237', 1)
    	 2 ('РКЦ №29', 1) ('УРМ-237', 1)
    	 42 (('branch',), 2) (('name',), 2) (('amenity', 'bank'), 2)
    	 42 (('name',), 2) (('amenity', 'bank'), 2) (('amenity',), 2)
    addr:district is_in 3969 3 3969 3
    	 1 ('Минский район', 3969)
    	 1 ('Минский район', 3)
    	 2360 (('addr:region',), 3959) (('addr:region', 'Минская область'), 3959) (('addr:country',), 3945)
    	 18 (('addr:region',), 3959) (('addr:region', 'Минская область'), 3959) (('addr:country',), 3945)
    	 1 ('Минский район', 3969)
    	 1 ('Минский район', 3)
    	 2360 (('addr:region',), 3959) (('addr:region', 'Минская область'), 3959) (('addr:country',), 3945)
    	 18 (('addr:postcode',), 3) (('addr:street',), 3) (('building',), 3)
    destination:backward addr:street 64 3919 0 0
    	 2 ('Гомель', 40) ('Минск', 24)
    	 32 ('Минская улица', 2295) ('Гомельская улица', 923) ('Гомельское шоссе', 142)
    	 32 (('surface', 'asphalt'), 64) (('maxaxleload',), 64) (('surface',), 64)
    	 1276 (('surface', 'asphalt'), 64) (('maxaxleload',), 64) (('surface',), 64)
    	 0
    	 0
    	 0
    	 0
    addr:housename website 3913 146 0 0
    	 14 ('н', 3480) ('к', 196) ('кн', 99)
    	 43 ('https://аптекарь.бел', 12) ('http://чайхана.бел', 6) ('http://www.картошка.com', 6)
    	 103 (('building',), 3913) (('building', 'yes'), 3802) (('addr:street',), 2807)
    	 319 (('building',), 3913) (('building', 'yes'), 3802) (('addr:street',), 2807)
    	 0
    	 0
    	 0
    	 0
    description destination:backward 3895 121 0 0
    	 4 ('н', 3869) ('ж', 14) ('Н', 11)
    	 76 ('Мінск', 8) ('Навагрудак;Парачаны', 4) ('Міханавічы;Гатава;Новы Двор', 4)
    	 8 (('building',), 3895) (('building', 'yes'), 3895) (('addr:street',), 3748)
    	 175 (('building',), 3895) (('building', 'yes'), 3895) (('addr:street',), 3748)
    	 0
    	 0
    	 0
    	 0
    type description 2103 3876 0 0
    	 5 ('ц', 1251) ('ель', 745) ('Дуб', 105)
    	 1805 ('Минская Кольцевая АвтоДорога', 603) ('Голоцк-Зазерье-Седча-Озеричино', 53) ('Торговая марка "Ганна" - это гарантия высокого качества и изысканного, неповторимого вкуса продукции из мяса птицы.', 37)
    	 11 (('natural',), 2103) (('natural', 'wetland'), 1251) (('natural', 'tree'), 852)
    	 6626 (('natural',), 2103) (('natural', 'wetland'), 1251) (('natural', 'tree'), 852)
    	 0
    	 0
    	 0
    	 0
    addr:housename source:ref 389 3842 0 0
    	 6 ('н', 348) ('ж', 20) ('к', 14)
    	 2 ('Публичная кадастровая карта', 3836) ('Договор между РФ и Украиной от 28 января 2003 года (приложение 1)', 6)
    	 61 (('building',), 389) (('building', 'yes'), 379) (('addr:street',), 280)
    	 372 (('building',), 389) (('building', 'yes'), 379) (('addr:street',), 280)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber source:ref 615 3839 0 0
    	 5 ('н', 548) ('ж', 49) ('П', 15)
    	 2 ('Публичная кадастровая карта', 3836) ('Договор между РФ и Украиной от 28 января 2003 года (приложение 1)', 3)
    	 92 (('building',), 615) (('building', 'yes'), 597) (('addr:street',), 514)
    	 372 (('building',), 615) (('building', 'yes'), 597) (('addr:street',), 514)
    	 0
    	 0
    	 0
    	 0
    addr:place note 3816 116 0 0
    	 24 ('номер', 1530) ('Микрорайон', 480) ('Огородники', 388)
    	 82 ('Нумерация уже сменилась на ул.Горького, но по факту на домах старые номера', 13) ('просто "Прудники" в другом месте!', 4) ('Каменка-Коптёвка-Бычки-Кореневичи-Колпаки', 4)
    	 396 (('building',), 3769) (('addr:housenumber',), 3719) (('building', 'house'), 2362)
    	 299 (('building',), 3769) (('addr:housenumber',), 3719) (('building', 'house'), 2362)
    	 0
    	 0
    	 0
    	 0
    network addr:street 97 3816 0 0
    	 4 ('Минск', 48) ('Борисов', 40) ('Бобруйск', 8)
    	 39 ('Минская улица', 2295) ('Бобруйская улица', 536) ('Борисовская улица', 337)
    	 41 (('name',), 97) (('bus', 'yes'), 49) (('bus',), 49)
    	 1396 (('name',), 97) (('bus', 'yes'), 49) (('bus',), 49)
    	 0
    	 0
    	 0
    	 0
    addr:housename contact:website 3802 123 0 0
    	 16 ('н', 2958) ('Н', 558) ('к', 112)
    	 28 ('https://azs.a-100.by/set-azs/map-azs/?query=Минский р-н, трасса на г. Могилев (М4), 4 км от МКАД', 8) ('https://azs.a-100.by/set-azs/map-azs/?query= ул. Промышленная, 2Б (МКАД)', 7) ('https://azs.a-100.by/set-azs/map-azs/?query=ул. Брикета, 23 (МКАД)', 7)
    	 134 (('building',), 3777) (('building', 'yes'), 3679) (('addr:street',), 2811)
    	 302 (('building',), 3777) (('building', 'yes'), 3679) (('addr:street',), 2811)
    	 0
    	 0
    	 0
    	 0
    was:name:prefix description 3788 76 0 0
    	 6 ('деревня', 3336) ('хутор', 249) ('станция', 129)
    	 54 ('ул. Бабушкина , 5, Подстанция Колядичи - 330КВ (объектовый)', 8) ('Насосная станция подкачки 3-го подъема', 5) ('Михайлово-Новый уборок- станция веленский', 3)
    	 2879 (('name',), 3786) (('place',), 3786) (('abandoned:place',), 3721)
    	 283 (('name',), 3786) (('place',), 3786) (('abandoned:place',), 3721)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:housenumber addr:street 21 3782 0 0
    	 5 ('Чапаева', 14) ('Льнозавод', 3) ('-Западная', 2)
    	 21 ('улица Чапаева', 3073) ('переулок Чапаева', 178) ('улица Щербитова', 168)
    	 26 (('fire_hydrant:type',), 21) (('fire_hydrant:position', 'lane'), 21) (('fire_hydrant:diameter',), 21)
    	 911 (('fire_hydrant:type',), 21) (('fire_hydrant:position', 'lane'), 21) (('fire_hydrant:diameter',), 21)
    	 0
    	 0
    	 0
    	 0
    cuisine addr:street 3 3755 0 0
    	 1 ('национальная', 3)
    	 3 ('Интернациональная улица', 3717) ('1-я Интернациональная улица', 27) ('2-я Интернациональная улица', 11)
    	 8 (('building', 'yes'), 3) (('amenity', 'cafe'), 3) (('name',), 3)
    	 1175 (('building', 'yes'), 3) (('amenity', 'cafe'), 3) (('name',), 3)
    	 0
    	 0
    	 0
    	 0
    addr:unit addr:place 163 3753 0 0
    	 2 ('Б', 125) ('А', 38)
    	 162 ('Белица', 318) ('Бердовка', 199) ('Бискупцы', 192)
    	 23 (('addr:street',), 163) (('addr:housenumber',), 163) (('addr:city',), 163)
    	 716 (('addr:street',), 163) (('addr:housenumber',), 163) (('addr:city',), 163)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber desc 3742 100 0 0
    	 13 ('н', 2466) ('П', 1005) ('Н', 120)
    	 74 ('Поворот налево с Немиги на Мясникова запрещен в будние дни c 7 до 22', 5) ('Парковка у строительной выставки', 4) ('магазин аккумуляторных батарей для автомобилей', 4)
    	 170 (('building',), 3741) (('building', 'yes'), 3158) (('addr:street',), 3048)
    	 102 (('building',), 3741) (('building', 'yes'), 3158) (('addr:street',), 3048)
    	 0
    	 0
    	 0
    	 0
    building:levels addr:city 80 3736 0 0
    	 1 ('Н', 80)
    	 80 ('Нарочь', 1133) ('Новосёлки', 572) ('Носилово', 233)
    	 2 (('building', 'yes'), 80) (('building',), 80)
    	 1497 (('building', 'yes'), 80) (('building',), 80)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber addr:street_1 3703 41 0 0
    	 7 ('н', 3562) ('ж', 98) ('П', 15)
    	 18 ('улица Жлобинская', 6) ('Кобринская улица', 4) ('улица Западная', 4)
    	 100 (('building',), 3703) (('building', 'yes'), 3633) (('addr:street',), 3114)
    	 96 (('building',), 3703) (('building', 'yes'), 3633) (('addr:street',), 3114)
    	 0
    	 0
    	 0
    	 0
    addr:province addr:street 61 3652 0 0
    	 4 ('Минская', 24) ('Брянская', 24) ('Витебская', 9)
    	 10 ('Минская улица', 2295) ('Витебская улица', 953) ('Брянская улица', 231)
    	 54 (('building',), 61) (('addr:district',), 61) (('addr:street',), 58)
    	 1116 (('building',), 61) (('addr:district',), 61) (('addr:street',), 58)
    	 0
    	 0
    	 0
    	 0
    name desc 3598 265 33 33
    	 65 ('н', 2493) ('Н', 382) ('к', 100)
    	 76 ('Поворот налево с Немиги на Мясникова запрещен в будние дни c 7 до 22', 14) ('обслуживание сетей Фрунзенского и Центрального районов.', 13) ('тропически-умеренное фьюжен бразильской и белорусской природы', 12)
    	 294 (('building',), 3297) (('building', 'yes'), 2794) (('building', 'residential'), 412)
    	 113 (('building',), 3297) (('building', 'yes'), 2794) (('building', 'residential'), 412)
    	 33 ('ПГ-051С', 1) ('ПГ-022С', 1) ('ПГ-050С', 1)
    	 33 ('ПГ-051С', 1) ('ПГ-022С', 1) ('ПГ-050С', 1)
    	 38 (('emergency', 'fire_hydrant'), 33) (('emergency',), 33) (('desc',), 33)
    	 38 (('emergency', 'fire_hydrant'), 33) (('emergency',), 33) (('name',), 33)
    fire_hydrant:city from 3598 11 1815 8
    	 4 ('Минск', 2032) ('Речица', 1532) ('Озерщина', 33)
    	 6 ('Речица', 4) ('Минск', 3) ('АС Речица', 1)
    	 1639 (('fire_hydrant:type',), 3598) (('emergency', 'fire_hydrant'), 3598) (('emergency',), 3598)
    	 58 (('fire_hydrant:type',), 3598) (('emergency', 'fire_hydrant'), 3598) (('emergency',), 3598)
    	 3 ('Минск', 1016) ('Речица', 766) ('Озерщина', 33)
    	 3 ('Речица', 4) ('Минск', 3) ('Озерщина', 1)
    	 1631 (('fire_hydrant:type',), 1815) (('emergency', 'fire_hydrant'), 1815) (('emergency',), 1815)
    	 45 (('to',), 8) (('type',), 8) (('public_transport:version', '2'), 8)
    fire_hydrant:type addr:street 12 3583 0 0
    	 1 ('Заслонова', 12)
    	 12 ('улица Заслонова', 2854) ('улица Константина Заслонова', 273) ('переулок Заслонова', 235)
    	 18 (('fire_hydrant:position', '39'), 12) (('fire_hydrant:diameter',), 12) (('name',), 12)
    	 932 (('fire_hydrant:position', '39'), 12) (('fire_hydrant:diameter',), 12) (('name',), 12)
    	 0
    	 0
    	 0
    	 0
    description destination:forward 3577 128 0 0
    	 3 ('н', 3551) ('ж', 20) ('Н', 6)
    	 67 ('Мiнск', 16) ('Валожын', 6) ('Барановичи', 5)
    	 8 (('building',), 3577) (('building', 'yes'), 3577) (('addr:street',), 3443)
    	 207 (('building',), 3577) (('building', 'yes'), 3577) (('addr:street',), 3443)
    	 0
    	 0
    	 0
    	 0
    name BY_PT:note 745 3528 0 0
    	 14 ('Н', 382) ('н', 277) ('Т', 25)
    	 1 ('Тэги типа "BY_PT..." - временные, для внесения ОТ Беларуси! Не удаляйте их - они будут удалены позже.', 3528)
    	 56 (('building',), 738) (('building', 'yes'), 419) (('building', 'residential'), 273)
    	 166 (('building',), 738) (('building', 'yes'), 419) (('building', 'residential'), 273)
    	 0
    	 0
    	 0
    	 0
    hamlet name 3481 1297 61 71
    	 4 ('Октябрь', 3410) ('Дуравичи', 64) ('Череповка', 6)
    	 159 ('Октябрьская улица', 793) ('Октябрьский переулок', 92) ('Октябрь', 62)
    	 59 (('building', 'yes'), 3481) (('building',), 3481) (('addr:housenumber',), 3481)
    	 1212 (('building', 'yes'), 3481) (('building',), 3481) (('addr:housenumber',), 3481)
    	 4 ('Дуравичи', 32) ('Октябрь', 22) ('Череповка', 6)
    	 4 ('Октябрь', 62) ('Череповка', 4) ('Дуравичи', 3)
    	 59 (('building', 'yes'), 61) (('building',), 61) (('addr:housenumber',), 61)
    	 254 (('int_name',), 37) (('place',), 36) (('addr:country',), 33)
    addr:housename office 3477 85 1 1
    	 12 ('Н', 1953) ('н', 1392) ('к', 77)
    	 13 ('Копыль-Слобода Кучинка-Песочное', 16) ('Подъез от а/д Н8569 к д. Мысли', 15) ('Подъезд от а/д Н8572 к мемориальному комплексу "Мосевичи"', 8)
    	 94 (('building',), 3462) (('building', 'yes'), 3398) (('addr:street',), 2839)
    	 56 (('building',), 3462) (('building', 'yes'), 3398) (('addr:street',), 2839)
    	 1 ('Белгосстрах', 1)
    	 1 ('Белгосстрах', 1)
    	 12 (('building:levels',), 1) (('name', 'Белгосстрах'), 1) (('office', 'insurance'), 1)
    	 6 (('addr:street', 'Слободская улица'), 1) (('name', 'Белгосстрах'), 1) (('addr:street',), 1)
    official_short_type addr:housename 3429 93 572 12
    	 13 ('ТП', 1230) ('ГРП', 792) ('РП', 682)
    	 38 ('ФАП', 12) ('ГРП', 10) ('ЦТП', 4)
    	 1315 (('ref',), 2903) (('building',), 2564) (('building', 'service'), 2452)
    	 95 (('ref',), 2903) (('building',), 2564) (('building', 'service'), 2452)
    	 6 ('ТП', 410) ('ЦТП', 111) ('ГРП', 44)
    	 6 ('ГРП', 5) ('ЦТП', 2) ('АТС', 2)
    	 678 (('ref',), 543) (('building',), 462) (('building', 'service'), 442)
    	 32 (('building',), 12) (('building', 'yes'), 10) (('addr:street',), 9)
    ref destination:ref:backward 3302 7 1216 3
    	 5 ('М1', 2074) ('М4', 889) ('М14', 187)
    	 3 ('М14', 3) ('М4', 2) ('М7', 2)
    	 272 (('highway',), 3286) (('surface',), 3267) (('oneway',), 3244)
    	 29 (('highway',), 3286) (('surface',), 3267) (('oneway',), 3244)
    	 3 ('М4', 889) ('М14', 187) ('М7', 140)
    	 3 ('М4', 1) ('М7', 1) ('М14', 1)
    	 210 (('surface',), 1213) (('highway',), 1213) (('lanes',), 1195)
    	 29 (('surface', 'asphalt'), 3) (('surface',), 3) (('destination:forward',), 3)
    official_short_name ref 3201 1145 11 34
    	 5 ('ТП', 2997) ('ГРП', 90) ('ЗТП', 88)
    	 1040 ('ТП', 27) ('ЦТП', 8) ('ГРП', 4)
    	 39 (('building',), 3201) (('building', 'service'), 3201) (('ref',), 2160)
    	 452 (('building',), 3201) (('building', 'service'), 3201) (('ref',), 2160)
    	 4 ('ГРП', 3) ('КНС', 3) ('ТП', 3)
    	 4 ('ТП', 27) ('ГРП', 4) ('КНС', 2)
    	 33 (('building',), 11) (('building', 'service'), 11) (('ref',), 6)
    	 50 (('building',), 33) (('power', 'substation'), 30) (('power',), 30)
    designation addr:place 137 3190 2 9
    	 5 ('б', 132) ('парк', 2) ('Городище', 1)
    	 137 ('Дубровня', 279) ('Збляны', 141) ('Шейбаки', 139)
    	 45 (('name',), 137) (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 132) (('addr:street',), 132)
    	 698 (('name',), 137) (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 132) (('addr:street',), 132)
    	 2 ('Городище', 1) ('Каменка', 1)
    	 2 ('Городище', 7) ('Каменка', 2)
    	 27 (('name',), 2) (('historic', 'archaeological_site'), 1) (('name', 'Гора Лисиця'), 1)
    	 14 (('building', 'yes'), 9) (('building',), 9) (('addr:street',), 7)
    addr:housenumber office 3153 54 0 0
    	 10 ('н', 2192) ('Н', 840) ('П', 90)
    	 12 ('Подъез от а/д Н8569 к д. Мысли', 12) ('Копыль-Слобода Кучинка-Песочное', 12) ('Подъезд от а/д Н8572 к мемориальному комплексу "Мосевичи"', 4)
    	 150 (('building',), 3146) (('building', 'yes'), 3042) (('addr:street',), 2677)
    	 51 (('building',), 3146) (('building', 'yes'), 3042) (('addr:street',), 2677)
    	 0
    	 0
    	 0
    	 0
    addr:unit description 1292 3135 0 0
    	 3 ('Б', 828) ('А', 462) ('к. 1', 2)
    	 1187 ('Минская Кольцевая АвтоДорога', 603) ('Аптечная сеть, занимающаяся розничной торговлей товарами для красоты и здоровья', 104) ('Завидовка - Болотня - Алешня - Кристополье', 28)
    	 26 (('addr:street',), 1292) (('addr:housenumber',), 1292) (('addr:city',), 1290)
    	 4693 (('addr:street',), 1292) (('addr:housenumber',), 1292) (('addr:city',), 1290)
    	 0
    	 0
    	 0
    	 0
    name name_old 3130 26 1822 4
    	 15 ('Школьная улица', 1214) ('н', 831) ('Набережная улица', 597)
    	 3 ('Школьная улица', 12) ('Набережная улица', 7) ('Пожарное депо', 7)
    	 652 (('highway',), 1799) (('int_name',), 1377) (('highway', 'residential'), 1306)
    	 17 (('highway',), 1799) (('int_name',), 1377) (('highway', 'residential'), 1306)
    	 3 ('Школьная улица', 1214) ('Набережная улица', 597) ('Пожарное депо', 11)
    	 3 ('Школьная улица', 2) ('Пожарное депо', 1) ('Набережная улица', 1)
    	 558 (('highway',), 1789) (('int_name',), 1367) (('highway', 'residential'), 1306)
    	 17 (('name',), 4) (('source', 'http://www.novopolotsk.by/content/view/8414/176/'), 3) (('source',), 3)
    ref fixme 3127 515 0 0
    	 25 ('М1', 2074) ('ж', 224) ('М14', 187)
    	 175 ('положение', 39) ('расположение', 36) ('режим', 36)
    	 470 (('highway',), 2497) (('surface',), 2475) (('maxaxleload',), 2467)
    	 1195 (('highway',), 2497) (('surface',), 2475) (('maxaxleload',), 2467)
    	 0
    	 0
    	 0
    	 0
    name name_1 3116 68 321 8
    	 28 ('н', 2216) ('Н', 382) ('Баня', 294)
    	 9 ('Холдинг "Пассат"', 18) ('памятники', 7) ('Детская одежда', 7)
    	 392 (('building',), 3013) (('building', 'yes'), 2502) (('building', 'residential'), 395)
    	 103 (('building',), 3013) (('building', 'yes'), 2502) (('building', 'residential'), 395)
    	 6 ('Баня', 294) ('Дискаунтер', 15) ('Детская одежда', 7)
    	 6 ('Холдинг "Пассат"', 3) ('Баня', 1) ('Дискаунтер', 1)
    	 329 (('building',), 241) (('building', 'yes'), 196) (('leisure',), 153)
    	 74 (('name',), 7) (('addr:housenumber',), 7) (('name_2',), 6)
    official_short_type full_name 3104 14 0 0
    	 2 ('ПС', 2912) ('Ф', 192)
    	 14 ('ДО №454 ОАО «БПС-Сбербанк»', 1) ('ПС 35/10 "Огородники"', 1) ('ПС 35/10 кВ №63 Кортеліси', 1)
    	 607 (('power',), 3096) (('voltage',), 3074) (('power', 'substation'), 2904)
    	 115 (('power',), 3096) (('voltage',), 3074) (('power', 'substation'), 2904)
    	 0
    	 0
    	 0
    	 0
    addr:housename phone 3092 72 1 1
    	 9 ('н', 2958) ('к', 70) ('м', 24)
    	 26 ('Многоканальный по Минску: 160 (гор, vel, mts, life) +375 (17) 207-74-74 Стоматология: +375 (29) 160-03-03', 6) ('+375 1562 96260 (Амбулатория), +375 1562 96249 (Стационар)', 5) ('8-02330-21367 (приемная, директор) 8-02330-21237 (заместитель директора по учебной работе', 5)
    	 64 (('building',), 3089) (('building', 'yes'), 3004) (('addr:street',), 2173)
    	 202 (('building',), 3089) (('building', 'yes'), 3004) (('addr:street',), 2173)
    	 1 ('10А', 1)
    	 1 ('10А', 1)
    	 4 (('addr:street',), 1) (('building',), 1) (('addr:street', 'Молодёжная улица'), 1)
    	 6 (('addr:street', 'Грушевская улица'), 1) (('addr:street',), 1) (('building', 'yes'), 1)
    fire_hydrant:city contact:website 3048 3 0 0
    	 1 ('Минск', 3048)
    	 3 ('https://azs.a-100.by/set-azs/map-azs/?query=Минский р-н, Боровая, 7', 1) ('https://azs.a-100.by/set-azs/map-azs/?query=Минский р-н, трасса на г. Могилев (М4), 4 км от МКАД', 1) ('https://azs.a-100.by/set-azs/map-azs/?query=Минский р-н, Новодворский с/с, 82', 1)
    	 1120 (('emergency', 'fire_hydrant'), 3048) (('fire_hydrant:type',), 3048) (('emergency',), 3048)
    	 52 (('emergency', 'fire_hydrant'), 3048) (('fire_hydrant:type',), 3048) (('emergency',), 3048)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city destination:lanes:backward 3048 3 0 0
    	 1 ('Минск', 3048)
    	 3 ('Воложин;Сморгонь|Минск', 1) ('Сморгонь;Минск;Вилейка;Нарочь|Минск;Вилейка;Нарочь', 1) ('Минск;Вилейка;Нарочь|Минск', 1)
    	 1120 (('emergency', 'fire_hydrant'), 3048) (('fire_hydrant:type',), 3048) (('emergency',), 3048)
    	 41 (('emergency', 'fire_hydrant'), 3048) (('fire_hydrant:type',), 3048) (('emergency',), 3048)
    	 0
    	 0
    	 0
    	 0
    addr:district addr:full 3012 37 0 0
    	 11 ('Логойский район', 648) ('Ошмянский район', 644) ('Борисовский район', 614)
    	 24 ('д. Рудишки, Ошмянский район, Гродненская область', 8) ('д. Яново, Борисовский район, Минская область', 6) ('Псковская область, Себежский район, д.Долосцы', 2)
    	 4889 (('addr:region',), 3009) (('name',), 3006) (('addr:country',), 2984)
    	 123 (('addr:region',), 3009) (('name',), 3006) (('addr:country',), 2984)
    	 0
    	 0
    	 0
    	 0
    name was:official_name 2993 164 0 0
    	 52 ('н', 1662) ('Каменка', 367) ('Борки', 126)
    	 10 ('Каменка - Першино - Полишино', 66) ('Красулино - Юрково - Поташи', 24) ('Подъезд к д. Клевки от а/д Лида - Трокели - Геранены - гр. Литвы (Геранены)', 14)
    	 1103 (('building',), 1991) (('building', 'yes'), 1779) (('place',), 614)
    	 30 (('building',), 1991) (('building', 'yes'), 1779) (('place',), 614)
    	 0
    	 0
    	 0
    	 0
    ref inscription 2957 1650 0 0
    	 25 ('ж', 510) ('М', 448) ('Н', 412)
    	 533 ('У ГЭТЫМ\nБУДЫНКУ ПРАЦАВАЎ\nНАРОДНЫ АРТЫСТ БССР,\nПРАФЕСАР, ДРАМАТУРГ\nЕЎСЦІГНЕЙ\nАФІНАГЕНАВІЧ МІРОВІЧ\n- АДЗІН З ЗАСНАВАЛЬНІКАЎ\nБЕЛАРУСКАГА ДЗЯРЖАЎНАГА\nТЭАТРАЛЬНА-МАСТАЦКАГА\nІНСТЫТУТА.', 14) ('В 1931 – 1936 Г.Г.\nВИЦЕ-ПРЕЗИДЕНТОМ АН БССР\nИ ДИРЕКТОРОМ\nИНСТИТУТА ИСТОРИИ АН БССР\nРАБОТАЛ ИЗВЕСТНЫЙ\nБЕЛОРУССКИЙ СОВЕТСКИЙ ИСТОРИК\nАКАДЕМИК АН БССР\nВАСИЛИЙ КАРПОВИЧ\nЩЕРБАКОВ', 13) ('БЕЛАРУСАМ ГЕРОЯМ КОСМАСУ. \nПАМЯТНЫ ЗНАК УСТАЛЯВАНЫ Ў\xa0ДНІ ПРАЦЫ 31-ГА МІЖНАРОДНАГА КАНГРЭСУ АССАЦЫЯЦЫІ ЎДЗЕЛЬНІКАУ КАСМІЧНЫХ ПАЛЁТАЎ 9\xa0верасня 2018\xa0гада', 13)
    	 88 (('aeroway', 'taxiway'), 946) (('aeroway',), 946) (('building',), 607)
    	 1190 (('aeroway', 'taxiway'), 946) (('aeroway',), 946) (('building',), 607)
    	 0
    	 0
    	 0
    	 0
    official_short_type from 2925 40 0 0
    	 4 ('ВЛ', 1907) ('ПС', 728) ('Ф', 288)
    	 13 ('Фолюш', 13) ('Мікрараён Фрунзэ', 7) ('ул. 50 лет ВЛКСМ', 4)
    	 1567 (('power',), 2915) (('voltage',), 2897) (('cables',), 2184)
    	 126 (('power',), 2915) (('voltage',), 2897) (('cables',), 2184)
    	 0
    	 0
    	 0
    	 0
    addr:housename fence_type 2922 627 0 0
    	 9 ('н', 2610) ('ж', 100) ('к', 91)
    	 41 ('каменный ж.б.', 245) ('металло изгородь', 84) ('Арматура', 68)
    	 71 (('building',), 2920) (('building', 'yes'), 2836) (('addr:street',), 2090)
    	 23 (('building',), 2920) (('building', 'yes'), 2836) (('addr:street',), 2090)
    	 0
    	 0
    	 0
    	 0
    addr:street:name name 111 2900 1 23
    	 1 ('Центральная', 111)
    	 111 ('Центральная улица', 2649) ('Центральная', 23) ('Центральная площадь', 23)
    	 8 (('building', 'yes'), 111) (('name',), 111) (('addr:streetnumber', '38'), 111)
    	 1904 (('building', 'yes'), 111) (('name',), 111) (('addr:streetnumber', '38'), 111)
    	 1 ('Центральная', 1)
    	 1 ('Центральная', 23)
    	 8 (('building', 'yes'), 1) (('name',), 1) (('addr:streetnumber', '38'), 1)
    	 87 (('public_transport',), 13) (('highway', 'bus_stop'), 11) (('highway',), 11)
    to official_name 1936 2897 5 5
    	 81 ('Гомель', 986) ('Новополоцк', 129) ('Минск', 125)
    	 569 ('Столбцы — Ивацевичи — Кобрин', 303) ('граница Республики Польша (Песчатка) — Каменец — Шерешево — Свислочь', 144) ('Минск — Калачи — Мядель', 98)
    	 457 (('type',), 1936) (('type', 'route'), 1936) (('route',), 1936)
    	 1933 (('type',), 1936) (('type', 'route'), 1936) (('route',), 1936)
    	 4 ('Носилово', 2) ('Мозырь', 1) ('ул. Лесная', 1)
    	 4 ('Носилово', 2) ('Мозырь', 1) ('ул. Лесная', 1)
    	 31 (('route',), 5) (('type',), 5) (('from',), 5)
    	 37 (('name',), 4) (('int_name',), 3) (('highway',), 3)
    source:ref source 2877 1574 959 7
    	 1 ('Публичная кадастровая карта', 2877)
    	 3 ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 1102) ('Публичная кадастровая карта nca.by', 465) ('Публичная кадастровая карта', 7)
    	 367 (('highway',), 2832) (('ref',), 2808) (('surface',), 2787)
    	 536 (('highway',), 2832) (('ref',), 2808) (('surface',), 2787)
    	 1 ('Публичная кадастровая карта', 959)
    	 1 ('Публичная кадастровая карта', 7)
    	 367 (('highway',), 944) (('ref',), 936) (('surface',), 929)
    	 41 (('int_name',), 7) (('source:ref',), 7) (('name',), 7)
    ref brand 2836 2663 3 41
    	 20 ('М1', 2074) ('М10', 426) ('М', 80)
    	 148 ('Белоруснефть', 884) ('Беларусбанк', 266) ('Белшина', 169)
    	 333 (('highway',), 2498) (('surface',), 2474) (('surface', 'asphalt'), 2474)
    	 6043 (('highway',), 2498) (('surface',), 2474) (('surface', 'asphalt'), 2474)
    	 2 ('Евроопт', 2) ('Белпочта', 1)
    	 2 ('Евроопт', 34) ('Белпочта', 7)
    	 20 (('to',), 2) (('route',), 2) (('public_transport:version', '2'), 2)
    	 119 (('name',), 40) (('brand:wikidata',), 37) (('shop',), 34)
    building to 2823 980 1 2
    	 14 ('Н', 1932) ('н', 378) ('р', 170)
    	 294 ('ДС Малиновка-4', 32) ('Мікрараён Фрунзэ', 21) ('рынок "Южный"', 18)
    	 47 (('name',), 632) (('name', 'Н'), 396) (('addr:street',), 193)
    	 1241 (('name',), 632) (('name', 'Н'), 396) (('addr:street',), 193)
    	 1 ('Больница', 1)
    	 1 ('Больница', 2)
    	 2 (('building:levels', '4'), 1) (('building:levels',), 1)
    	 20 (('public_transport:version', '2'), 2) (('type',), 2) (('network',), 2)
    destination:forward operator 287 2819 5 1
    	 4 ('Гомель', 240) ('Барановичи', 20) ('Мінск', 20)
    	 57 ('КТУП «Гомельоблпассажиртранс»', 1665) ('ОАО "Гомельавтотранс"', 719) ('Гомельэнерго', 133)
    	 79 (('highway',), 287) (('destination:backward',), 266) (('highway', 'trunk_link'), 250)
    	 3155 (('highway',), 287) (('destination:backward',), 266) (('highway', 'trunk_link'), 250)
    	 1 ('Гомель', 5)
    	 1 ('Гомель', 1)
    	 26 (('highway', 'trunk_link'), 5) (('destination:backward',), 5) (('highway',), 5)
    	 10 (('contact:phone',), 1) (('contact:website',), 1) (('shop',), 1)
    operator brand:wikipedia 2817 1262 0 0
    	 28 ('Беларусбанк', 770) ('Мила', 525) ('Белагропромбанк', 456)
    	 32 ('be:Белпошта', 324) ('be:Белаграпрамбанк', 219) ('ru:Белинвестбанк', 136)
    	 3697 (('amenity',), 2177) (('name',), 1862) (('opening_hours',), 1793)
    	 1858 (('amenity',), 2177) (('name',), 1862) (('opening_hours',), 1793)
    	 0
    	 0
    	 0
    	 0
    addr:city image 2812 4 0 0
    	 3 ('Брест', 2766) ('Лепель', 33) ('Пограничный', 13)
    	 3 ('https://upload.wikimedia.org/wikipedia/commons/e/ee/Пограничный_отряд_Брест_имени_Кижеватова_01.jpg', 2) ('https://upload.wikimedia.org/wikipedia/commons/5/56/Брест%2C_ДОТ_у_моста_над_Бугом_04.jpg', 1) ('File:Лепель. Касцёл. Выгляд ад дарогі.jpg', 1)
    	 1069 (('addr:street',), 2804) (('addr:housenumber',), 2763) (('building',), 2662)
    	 32 (('addr:street',), 2804) (('addr:housenumber',), 2763) (('building',), 2662)
    	 0
    	 0
    	 0
    	 0
    destination official_name 2234 2806 1 1
    	 62 ('Гомель', 928) ('Могилёв', 171) ('Барановичи', 162)
    	 653 ('Минск - Могилёв', 174) ('Могилёв — Славгород', 116) ('Ушачи - Вилейка', 108)
    	 413 (('highway',), 1470) (('oneway', 'yes'), 1469) (('oneway',), 1469)
    	 2195 (('highway',), 1470) (('oneway', 'yes'), 1469) (('oneway',), 1469)
    	 1 ('Молчадь', 1)
    	 1 ('Молчадь', 1)
    	 14 (('name', 'Ятранка'), 1) (('waterway',), 1) (('waterway', 'river'), 1)
    	 20 (('waterway', 'river'), 1) (('type',), 1) (('int_name',), 1)
    building network 1154 2806 0 0
    	 8 ('Н', 966) ('н', 58) ('р', 47)
    	 60 ('Барановичское отделение', 992) ('Минский метрополитен', 786) ('прыгарад СТіС', 146)
    	 22 (('name',), 255) (('name', 'Н'), 198) (('building:levels',), 53)
    	 864 (('name',), 255) (('name', 'Н'), 198) (('building:levels',), 53)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber fee 2775 18 0 0
    	 5 ('н', 2740) ('П', 30) ('я', 3)
    	 11 ('Москва-Минск', 3) ('Приорбанк', 2) ('Беларусбанк', 2)
    	 85 (('building',), 2775) (('building', 'yes'), 2716) (('addr:street',), 2336)
    	 23 (('building',), 2775) (('building', 'yes'), 2716) (('addr:street',), 2336)
    	 0
    	 0
    	 0
    	 0
    addr:street old_addr:street 2771 3 2771 3
    	 1 ('улица Максима Горького', 2771)
    	 1 ('улица Максима Горького', 3)
    	 1402 (('addr:housenumber',), 2723) (('building',), 2655) (('building', 'yes'), 1418)
    	 20 (('addr:housenumber',), 2723) (('building',), 2655) (('building', 'yes'), 1418)
    	 1 ('улица Максима Горького', 2771)
    	 1 ('улица Максима Горького', 3)
    	 1402 (('addr:housenumber',), 2723) (('building',), 2655) (('building', 'yes'), 1418)
    	 20 (('old_addr:housenumber',), 3) (('addr:city', 'Гродно'), 3) (('addr:street',), 3)
    name cuisine 2743 51 0 0
    	 15 ('н', 2493) ('к', 80) ('п', 68)
    	 12 ('coffee;блины;кофе;чай;молочный_коктейль;пицца', 9) ('пышки;чай;какао;глинтвейн;russian;brunch', 7) ('блины, драники на огне', 5)
    	 45 (('building',), 2726) (('building', 'yes'), 2506) (('addr:street',), 179)
    	 78 (('building',), 2726) (('building', 'yes'), 2506) (('addr:street',), 179)
    	 0
    	 0
    	 0
    	 0
    description owner 2722 240 0 0
    	 6 ('н', 2703) ('ж', 6) ('Н', 6)
    	 54 ('ОАО «Белорусский банк развития и реконструкции «Белинвестбанк»', 94) ('ОАО «АСБ Беларусбанк»', 30) ('ОАО «Приорбанк»', 13)
    	 31 (('building',), 2721) (('building', 'yes'), 2720) (('addr:street',), 2614)
    	 554 (('building',), 2721) (('building', 'yes'), 2720) (('addr:street',), 2614)
    	 0
    	 0
    	 0
    	 0
    name addr:suburb 2695 1799 11 165
    	 41 ('н', 1939) ('Березина', 124) ('м', 91)
    	 9 ('Октябрьский микрорайон', 520) ('посёлок Строителей', 352) ('микрорайон Полесье', 290)
    	 713 (('building',), 2294) (('building', 'yes'), 2104) (('int_name',), 218)
    	 240 (('building',), 2294) (('building', 'yes'), 2104) (('int_name',), 218)
    	 8 ('Молодёжный микрорайон', 3) ('посёлок Строителей', 2) ('Первомайский микрорайон', 1)
    	 8 ('посёлок Строителей', 44) ('Октябрьский микрорайон', 40) ('Первомайский микрорайон', 29)
    	 28 (('place',), 10) (('residential',), 8) (('landuse', 'residential'), 8)
    	 216 (('addr:housenumber',), 162) (('building',), 160) (('addr:place',), 157)
    description related_law 2683 107 0 0
    	 4 ('н', 2650) ('стр', 30) ('ж', 2)
    	 50 ('Постановление Совета Министров РБ от 27.12.2007 № 1833', 10) ('Постановление Совета Министров РБ 27.12.2007 № 1833', 10) ('Постановление Совета Министров РБ от 04.02.2015 № 71', 8)
    	 8 (('building',), 2683) (('building', 'yes'), 2683) (('addr:street',), 2553)
    	 281 (('building',), 2683) (('building', 'yes'), 2683) (('addr:street',), 2553)
    	 0
    	 0
    	 0
    	 0
    official_short_type note 2682 60 0 0
    	 9 ('ПС', 1092) ('Ф', 1088) ('ТП', 410)
    	 53 ('Линия идёт на КС Михановичи, но в названии указано просто "Михановичи"', 4) ('Изначально это была ТЭЦ4-Дзержинск, потом после постройки ПС Птицефабрика на столбах стали писать ТЭЦ4-Птицефабрика.', 3) ('Не уверен, что ГРП, но номер 252 на будке есть', 2)
    	 1182 (('power',), 2611) (('voltage',), 2511) (('ref',), 1550)
    	 160 (('power',), 2611) (('voltage',), 2511) (('ref',), 1550)
    	 0
    	 0
    	 0
    	 0
    building addr2:street 2673 898 0 0
    	 10 ('Н', 2093) ('н', 240) ('р', 139)
    	 208 ('переулок Дзержинского', 38) ('улица Максима Горького', 26) ('Молодёжная улица', 22)
    	 27 (('name',), 581) (('name', 'Н'), 429) (('building:levels',), 152)
    	 474 (('name',), 581) (('name', 'Н'), 429) (('building:levels',), 152)
    	 0
    	 0
    	 0
    	 0
    building:levels official_name 830 2659 0 0
    	 1 ('Н', 830)
    	 830 ('Любча - Новогрудок - Дятлово', 82) ('Новоельня - Козловщина - Деревная ч/з Дворец', 35) ('Смолевичи — Самохваловичи — Негорелое', 28)
    	 2 (('building', 'yes'), 830) (('building',), 830)
    	 1996 (('building', 'yes'), 830) (('building',), 830)
    	 0
    	 0
    	 0
    	 0
    name disused:name 2657 74 46 8
    	 41 ('н', 1662) ('Н', 382) ('Белсоюзпечать', 189)
    	 16 ('Шоколадница', 9) ('Зимний сад', 7) ('Винный шкаф', 7)
    	 461 (('building',), 2410) (('building', 'yes'), 1943) (('building', 'residential'), 373)
    	 32 (('building',), 2410) (('building', 'yes'), 1943) (('building', 'residential'), 373)
    	 8 ('Ялинка', 25) ('Штолле', 7) ('Кружки', 4)
    	 8 ('Штолле', 1) ('Кружки', 1) ('Ялинка', 1)
    	 145 (('waterway',), 18) (('waterway', 'stream'), 17) (('opening_hours',), 12)
    	 17 (('disused:amenity',), 7) (('disused:amenity', 'cafe'), 4) (('disused:amenity', 'restaurant'), 3)
    name access 2640 77 1 1
    	 37 ('н', 2216) ('к', 80) ('м', 52)
    	 9 ('Ящик для предложений СТ "Криница-Кривополье"', 17) ('Стоянки_им._Жени_Иванова_(с_беседкой)', 15) ('Гомельская область,деревня Покалюбичи', 11)
    	 323 (('building',), 2524) (('building', 'yes'), 2299) (('building', 'residential'), 182)
    	 69 (('building',), 2524) (('building', 'yes'), 2299) (('building', 'residential'), 182)
    	 1 ('Ящик для предложений СТ "Криница-Кривополье"', 1)
    	 1 ('Ящик для предложений СТ "Криница-Кривополье"', 1)
    	 4 (('tourism', 'information'), 1) (('information',), 1) (('tourism',), 1)
    	 12 (('name', 'Ящик для предложений'), 1) (('description',), 1) (('amenity', 'post_box'), 1)
    height operator 403 2618 6 296
    	 2 ('ф', 397) ('КУПП "Боровка"', 6)
    	 398 ('КУПП "Боровка"', 296) ('РУП "Белоруснефть-Минскавтозаправка"', 229) ('Белоруснефть', 161)
    	 6 (('barrier',), 397) (('barrier', 'fence'), 397) (('power', 'pole'), 6)
    	 6204 (('barrier',), 397) (('barrier', 'fence'), 397) (('power', 'pole'), 6)
    	 1 ('КУПП "Боровка"', 6)
    	 1 ('КУПП "Боровка"', 296)
    	 4 (('power', 'pole'), 6) (('power',), 6) (('operator',), 5)
    	 22 (('power',), 296) (('power', 'pole'), 291) (('height', 'КУПП "Боровка"'), 5)
    building official_status 35 2588 0 0
    	 3 ('н', 18) ('р', 14) ('К', 3)
    	 17 ('садоводческое товарищество', 1777) ('ru:деревня', 716) ('ru:муниципальный район', 36)
    	 12 (('building:levels',), 14) (('addr:postcode', '231288'), 14) (('addr:postcode',), 14)
    	 5142 (('building:levels',), 14) (('addr:postcode', '231288'), 14) (('addr:postcode',), 14)
    	 0
    	 0
    	 0
    	 0
    building nat_ref 2578 60 0 0
    	 2 ('Н', 2576) ('М', 2)
    	 17 ('Н-28', 22) ('М4', 10) ('Н136', 6)
    	 8 (('name',), 546) (('name', 'Н'), 528) (('building:levels',), 16)
    	 96 (('name',), 546) (('name', 'Н'), 528) (('building:levels',), 16)
    	 0
    	 0
    	 0
    	 0
    from official_name 2228 2573 1 1
    	 75 ('Гомель', 1044) ('Минск', 375) ('Барановичи', 108)
    	 620 ('граница Республики Польша (Песчатка) — Каменец — Шерешево — Свислочь', 144) ('Минск — Калачи — Мядель', 98) ('Минск — Гродно — Брузги', 97)
    	 488 (('to',), 2228) (('name',), 2228) (('route',), 2228)
    	 2110 (('to',), 2228) (('name',), 2228) (('route',), 2228)
    	 1 ('Аэропорт', 1)
    	 1 ('Аэропорт', 1)
    	 18 (('to',), 1) (('public_transport:version', '2'), 1) (('type',), 1)
    	 8 (('int_name',), 1) (('name',), 1) (('loc_name',), 1)
    operator official_status 18 2561 0 0
    	 4 ('е', 13) ('я', 3) ('б', 1)
    	 15 ('садоводческое товарищество', 1777) ('ru:деревня', 716) ('ru:сельское поселение', 23)
    	 20 (('name',), 15) (('name', 'Складской комплекс «Северный»'), 13) (('landuse',), 13)
    	 5156 (('name',), 15) (('name', 'Складской комплекс «Северный»'), 13) (('landuse',), 13)
    	 0
    	 0
    	 0
    	 0
    name comment 2544 429 1 3
    	 35 ('н', 1939) ('п', 153) ('м', 78)
    	 10 ('Кольцевая дорога, даже H по своему значению не может быть tertiary', 324) ('Учреждение создано в соответствии с приказом Министерства образования и науки Республики Беларусь от 30.09.96 г. № 419 и входит в структуру БГУ. Учредителем государственного учреждения "Республиканский институт высшей школы" является БГУ', 21) ('Вход в общежитие', 21)
    	 305 (('building',), 2437) (('building', 'yes'), 2219) (('building:levels',), 219)
    	 81 (('building',), 2437) (('building', 'yes'), 2219) (('building:levels',), 219)
    	 1 ('Вход в общежитие', 1)
    	 1 ('Вход в общежитие', 3)
    	 2 (('entrance',), 1) (('entrance', 'yes'), 1)
    	 3 (('entrance',), 3) (('entrance', 'service'), 2) (('entrance', 'staircase'), 1)
    addr:housenumber old:addr:housenumber 2536 2 955 1
    	 2 ('4А', 1581) ('14А', 955)
    	 1 ('14А', 2)
    	 2225 (('building',), 2457) (('addr:street',), 2413) (('building', 'yes'), 1473)
    	 26 (('building',), 2457) (('addr:street',), 2413) (('building', 'yes'), 1473)
    	 1 ('14А', 955)
    	 1 ('14А', 1)
    	 1022 (('building',), 935) (('addr:street',), 918) (('building', 'yes'), 569)
    	 26 (('man_made', 'works'), 1) (('official_name', 'ГГКУП "КШП Ленинского района г. Гродно"'), 1) (('alt_name', 'Комбинат школьного питания Ленинского района'), 1)
    addr:housenumber cuisine 2531 21 0 0
    	 4 ('н', 2466) ('ж', 49) ('ы', 10)
    	 11 ('выпечка_и_пирожные', 3) ('блины, драники на огне', 2) ('кондитерская', 2)
    	 74 (('building',), 2531) (('building', 'yes'), 2489) (('addr:street',), 2133)
    	 74 (('building',), 2531) (('building', 'yes'), 2489) (('addr:street',), 2133)
    	 0
    	 0
    	 0
    	 0
    name was:operator 2530 74 1 1
    	 39 ('н', 1385) ('Н', 382) ('ТП', 198)
    	 11 ('Гродненская Овощная Фабрика', 10) ('Группа компаний «А-100»', 9) ('ТПУП "Металлургторг"', 9)
    	 517 (('building',), 2269) (('building', 'yes'), 1726) (('building', 'residential'), 383)
    	 123 (('building',), 2269) (('building', 'yes'), 1726) (('building', 'residential'), 383)
    	 1 ('Гродненская Овощная Фабрика', 1)
    	 1 ('Гродненская Овощная Фабрика', 1)
    	 6 (('shop',), 1) (('building',), 1) (('building', 'kiosk'), 1)
    	 6 (('old_name', 'Поместье'), 1) (('was:opening_hours',), 1) (('old_name',), 1)
    addr:housename addr:street_1 2519 137 0 0
    	 9 ('н', 2262) ('к', 161) ('ж', 40)
    	 29 ('2-й Брестский переулок', 12) ('3-й Брестский переулок', 10) ('1-й Брестский переулок', 10)
    	 71 (('building',), 2517) (('building', 'yes'), 2445) (('addr:street',), 1820)
    	 127 (('building',), 2517) (('building', 'yes'), 2445) (('addr:street',), 1820)
    	 0
    	 0
    	 0
    	 0
    addr:postcode name 2515 257 60 127
    	 6 ('Жлобин', 2464) ('Белтелеком', 31) ('Заводской спуск', 12)
    	 96 ('сарай', 59) ('Белтелеком', 56) ('Жлобинская улица', 8)
    	 75 (('building',), 2479) (('addr:street',), 2476) (('addr:housenumber',), 2476)
    	 502 (('building',), 2479) (('addr:street',), 2476) (('addr:housenumber',), 2476)
    	 6 ('Жлобин', 44) ('Заводской спуск', 12) ('Белтелеком', 1)
    	 6 ('сарай', 59) ('Белтелеком', 56) ('Жлобин', 6)
    	 75 (('building',), 57) (('addr:street',), 56) (('addr:housenumber',), 56)
    	 243 (('building',), 81) (('building', 'yes'), 65) (('office',), 38)
    addr:housenumber official_status 2497 809 3 8
    	 5 ('н', 2466) ('П', 15) ('ы', 10)
    	 10 ('ru:деревня', 716) ('ru:муниципальный район', 36) ('ru:сельское поселение', 23)
    	 90 (('building',), 2497) (('building', 'yes'), 2450) (('addr:street',), 2106)
    	 1183 (('building',), 2497) (('building', 'yes'), 2450) (('addr:street',), 2106)
    	 1 ('ФАП', 3)
    	 1 ('ФАП', 8)
    	 8 (('addr:street',), 3) (('building', 'yes'), 3) (('building',), 3)
    	 76 (('addr:region', 'Псковская область'), 8) (('amenity', 'doctors'), 8) (('name',), 8)
    official_short_type to 2497 45 0 0
    	 4 ('ВЛ', 1907) ('ПС', 364) ('Ф', 224)
    	 10 ('Фолюш', 13) ('ул. 50 лет ВЛКСМ', 12) ('Мікрараён Фрунзэ', 7)
    	 1567 (('power',), 2488) (('voltage',), 2474) (('cables',), 2120)
    	 130 (('power',), 2488) (('voltage',), 2474) (('cables',), 2120)
    	 0
    	 0
    	 0
    	 0
    operator full_name 2491 191 7 2
    	 33 ('Беларусбанк', 1540) ('БПС-Сбербанк', 188) ('Гродноэнерго', 170)
    	 79 ('ДО №454 ОАО «БПС-Сбербанк»', 8) ('ЦБУ №611 ОАО "АСБ Беларусбанк"', 7) ('Обменный пункт №611/5048 ОАО "АСБ Беларусбанк"', 7)
    	 2085 (('amenity',), 2120) (('name',), 1467) (('amenity', 'atm'), 1334)
    	 569 (('amenity',), 2120) (('name',), 1467) (('amenity', 'atm'), 1334)
    	 2 ('ОАО "Автобусный парк г. Гродно"', 4) ('ООО Конно-спортивный центр "Гиппика"', 3)
    	 2 ('ОАО "Автобусный парк г. Гродно"', 1) ('ООО Конно-спортивный центр "Гиппика"', 1)
    	 72 (('name',), 6) (('building', 'yes'), 3) (('tourism',), 3)
    	 19 (('name',), 2) (('office', 'transport'), 1) (('official_name', 'ОАО "Автобусный парк г. Гродно"'), 1)
    source:name source 27 2491 9 267
    	 1 ('ГУП "Национальное кадастровое агентство"', 27)
    	 3 ('Кадастровая карта ГУП "Национальное кадастровое агентство"', 2149) ('ГУП "Национальное кадастровое агентство"', 267) ('ГУП "Национальное кадастровое агентство" публичная карта', 75)
    	 14 (('addr:street', 'Молодёжная улица'), 27) (('addr:street',), 27) (('building', 'yes'), 27)
    	 296 (('addr:street', 'Молодёжная улица'), 27) (('addr:street',), 27) (('building', 'yes'), 27)
    	 1 ('ГУП "Национальное кадастровое агентство"', 9)
    	 1 ('ГУП "Национальное кадастровое агентство"', 267)
    	 14 (('addr:street', 'Молодёжная улица'), 9) (('addr:street',), 9) (('building', 'yes'), 9)
    	 98 (('building',), 267) (('addr:housenumber',), 267) (('addr:street',), 264)
    ref design:ref 2448 461 0 0
    	 11 ('М1', 2074) ('М11', 339) ('М', 12)
    	 16 ('1-464ДН', 336) ('90М', 56) ('М111-90', 33)
    	 320 (('highway',), 2411) (('surface',), 2388) (('surface', 'asphalt'), 2388)
    	 339 (('highway',), 2411) (('surface',), 2388) (('surface', 'asphalt'), 2388)
    	 0
    	 0
    	 0
    	 0
    official_short_type building 2429 72 465 16
    	 8 ('ТП', 820) ('РП', 744) ('ГРП', 572)
    	 32 ('ТП', 9) ('ШРП', 6) ('КНС', 3)
    	 693 (('ref',), 2208) (('building',), 2071) (('building', 'service'), 1985)
    	 12 (('ref',), 2208) (('building',), 2071) (('building', 'service'), 1985)
    	 4 ('ТП', 410) ('КНС', 36) ('ШРП', 14)
    	 4 ('ТП', 9) ('КНС', 3) ('ШРП', 3)
    	 609 (('ref',), 408) (('power',), 406) (('power', 'substation'), 403)
    	 9 (('addr:street',), 4) (('addr:street', 'улица Гагарина'), 1) (('addr:street', 'улица Сергея Санца'), 1)
    ref destination 2406 1928 423 2
    	 16 ('М', 692) ('Р99', 423) ('Н', 224)
    	 554 ('Мiнск', 89) ('Брэст', 45) ('40-ы кіламетр МКАД;Нарач;Гродна;Вільнюс;Брэст', 42)
    	 265 (('aeroway', 'taxiway'), 591) (('aeroway',), 591) (('entrance',), 573)
    	 827 (('aeroway', 'taxiway'), 591) (('aeroway',), 591) (('entrance',), 573)
    	 1 ('Р99', 423)
    	 1 ('Р99', 2)
    	 206 (('highway',), 422) (('surface',), 390) (('surface', 'asphalt'), 390)
    	 8 (('note',), 2) (('type', 'destination_sign'), 2) (('type',), 2)
    operator inscription 2400 1520 2 4
    	 46 ('Беларусбанк', 770) ('е', 507) ('я', 398)
    	 557 ('Дерево посажено Народным артистом БССР Смольским Дмитрием Борисовичем и Филиалом №529 "Белсвязь" ОАО "АСБ Беларусбанк" 2017', 8) ('Здесь 21.07.2011 при совершении парашютного прыжка в ночных условиях погиб офицер сил специальных операций ВС РБ гвардии лейтенант Валюженич Павел Александрович', 7) ("На гэтым месцы стаялі дамы сям'і Луцкевічаў, дзе ў 1896-1906 г.г. жылі вядомыя беларускія дзеячы Антон і Іван Луцкевічы", 6)
    	 1169 (('amenity',), 1617) (('name',), 1518) (('amenity', 'atm'), 1287)
    	 1192 (('amenity',), 1617) (('name',), 1518) (('amenity', 'atm'), 1287)
    	 2 ('Цветы', 1) ('Стройматериалы', 1)
    	 2 ('Цветы', 2) ('Стройматериалы', 2)
    	 13 (('shop',), 2) (('opening_hours',), 1) (('shop', 'florist'), 1)
    	 31 (('shop',), 4) (('opening_hours',), 4) (('noname',), 2)
    fire_hydrant:diameter description 2394 3 0 0
    	 1 ('К-150', 2394)
    	 3 ('ПГ № 57 К-150', 1) ('ПГ №58 К-150', 1) ('ПГ №11 К-150', 1)
    	 519 (('fire_hydrant:type',), 2394) (('name',), 2394) (('fire_operator',), 2394)
    	 6 (('fire_hydrant:type',), 2394) (('name',), 2394) (('fire_operator',), 2394)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber name_1 2387 21 6 1
    	 7 ('н', 2192) ('Н', 120) ('ж', 49)
    	 9 ('Холдинг "Пассат"', 6) ('Натариальная контора', 4) ('Баня', 3)
    	 151 (('building',), 2386) (('building', 'yes'), 2339) (('addr:street',), 2012)
    	 103 (('building',), 2386) (('building', 'yes'), 2339) (('addr:street',), 2012)
    	 1 ('Баня', 6)
    	 1 ('Баня', 1)
    	 10 (('building',), 6) (('building', 'yes'), 6) (('addr:street',), 5)
    	 20 (('addr:street', 'улица Рыбиновского'), 1) (('tourism',), 1) (('name_3',), 1)
    operator short_name 2362 1816 119 37
    	 95 ('е', 688) ('Мила', 525) ('я', 208)
    	 1026 ('СТ "Лесная Поляна"', 28) ('СТ "Дружба"', 22) ('СТ "Строитель"', 13)
    	 2148 (('name',), 1942) (('landuse',), 729) (('landuse', 'industrial'), 707)
    	 3224 (('name',), 1942) (('landuse',), 729) (('landuse', 'industrial'), 707)
    	 29 ('ГрГУ', 38) ('БНТУ', 18) ('Ленинский РОВД', 9)
    	 29 ('ГрГУ', 2) ('БНТУ', 2) ('БНБ', 2)
    	 526 (('name',), 94) (('amenity',), 63) (('addr:street',), 59)
    	 283 (('name',), 36) (('amenity',), 23) (('website',), 17)
    building from 2350 957 2 2
    	 14 ('Н', 1449) ('н', 370) ('р', 166)
    	 286 ('ДС Малиновка-4', 30) ('Мікрараён Фрунзэ', 21) ('рынок "Южный"', 16)
    	 47 (('name',), 536) (('name', 'Н'), 297) (('addr:street',), 195)
    	 1221 (('name',), 536) (('name', 'Н'), 297) (('addr:street',), 195)
    	 2 ('Советская', 1) ('Больница', 1)
    	 2 ('Советская', 1) ('Больница', 1)
    	 6 (('addr:street',), 1) (('addr:housenumber',), 1) (('addr:street', 'Советская улица'), 1)
    	 23 (('to',), 2) (('public_transport:version', '2'), 2) (('type',), 2)
    name sport 2338 88 3 3
    	 27 ('н', 1939) ('п', 102) ('к', 90)
    	 17 ('equestrian;лошади;конный_спорт;конюшня', 9) ('пожарный_спорт;firefighting', 8) ('Воркаут-площадка', 8)
    	 92 (('building',), 2302) (('building', 'yes'), 2086) (('building', 'residential'), 173)
    	 66 (('building',), 2302) (('building', 'yes'), 2086) (('building', 'residential'), 173)
    	 3 ('Айкидо', 1) ('Вьет-Во-Дао', 1) ('Воркаут-площадка', 1)
    	 3 ('Айкидо', 1) ('Вьет-Во-Дао', 1) ('Воркаут-площадка', 1)
    	 22 (('leisure',), 3) (('leisure', 'sports_centre'), 2) (('sport',), 2)
    	 16 (('leisure',), 3) (('leisure', 'sports_centre'), 2) (('name',), 2)
    name start_date 2333 45 0 0
    	 7 ('н', 2216) ('п', 68) ('к', 20)
    	 11 ('XIX - 1-я половина XX', 9) ('1-я половина XX', 9) ('1912, XIX - 1-я половина XX', 6)
    	 30 (('building',), 2327) (('building', 'yes'), 2166) (('addr:street',), 152)
    	 86 (('building',), 2327) (('building', 'yes'), 2166) (('addr:street',), 152)
    	 0
    	 0
    	 0
    	 0
    building fire_hydrant:street 2304 1226 1 40
    	 9 ('Н', 1771) ('н', 226) ('р', 118)
    	 178 ('Молодежная', 68) ('Фрунзе', 62) ('Набережная', 48)
    	 25 (('name',), 498) (('name', 'Н'), 363) (('addr:street',), 132)
    	 508 (('name',), 498) (('name', 'Н'), 363) (('addr:street',), 132)
    	 1 ('Советская', 1)
    	 1 ('Советская', 40)
    	 4 (('addr:street',), 1) (('addr:housenumber',), 1) (('addr:street', 'Советская улица'), 1)
    	 66 (('fire_hydrant:type',), 40) (('fire_hydrant:diameter',), 40) (('name',), 40)
    addr:housenumber access 2280 24 0 0
    	 7 ('н', 2192) ('ж', 49) ('П', 15)
    	 9 ('место_для_инвалидов', 6) ('Гомельская область,деревня Покалюбичи', 3) ('Ящик для предложений СТ "Криница-Кривополье"', 3)
    	 101 (('building',), 2280) (('building', 'yes'), 2233) (('addr:street',), 1919)
    	 69 (('building',), 2280) (('building', 'yes'), 2233) (('addr:street',), 1919)
    	 0
    	 0
    	 0
    	 0
    description protection_title 2233 171 2 1
    	 5 ('н', 2226) ('ж', 2) ('Н', 2)
    	 42 ('Памятник природы', 28) ('Республиканский ландшафтный заказник', 22) ('Республиканский биологический заказник', 15)
    	 47 (('building',), 2230) (('building', 'yes'), 2230) (('addr:street',), 2146)
    	 582 (('building',), 2230) (('building', 'yes'), 2230) (('addr:street',), 2146)
    	 1 ('историко-культурная ценность', 2)
    	 1 ('историко-культурная ценность', 1)
    	 20 (('protected',), 2) (('name',), 2) (('protected', 'yes'), 2)
    	 6 (('name',), 1) (('protect_class', '22'), 1) (('boundary', 'protected_area'), 1)
    fixme gomel_PT:note 12 2233 0 0
    	 1 ('тип', 12)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 2233)
    	 32 (('name',), 10) (('shop',), 9) (('shop', 'yes'), 7)
    	 859 (('name',), 10) (('shop',), 9) (('shop', 'yes'), 7)
    	 0
    	 0
    	 0
    	 0
    designation gomel_PT:note 1 2233 0 0
    	 1 ('б', 1)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 2233)
    	 8 (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 1) (('addr:street',), 1) (('building', 'yes'), 1)
    	 859 (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 1) (('addr:street',), 1) (('building', 'yes'), 1)
    	 0
    	 0
    	 0
    	 0
    fence_type gomel_PT:note 1 2233 0 0
    	 1 ('да', 1)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 2233)
    	 2 (('barrier',), 1) (('barrier', 'fence'), 1)
    	 859 (('barrier',), 1) (('barrier', 'fence'), 1)
    	 0
    	 0
    	 0
    	 0
    building:levels gomel_PT:note 1 2233 0 0
    	 1 ('Н', 1)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 2233)
    	 2 (('building', 'yes'), 1) (('building',), 1)
    	 859 (('building', 'yes'), 1) (('building',), 1)
    	 0
    	 0
    	 0
    	 0
    cycleway:left gomel_PT:note 1 2233 0 0
    	 1 ('да', 1)
    	 1 ('Тэги типа "gomel_PT..." - временные, для внесения ОТ Гомеля! Не удаляйте их - они будут удалены позже.', 2233)
    	 6 (('int_name',), 1) (('name', 'улица 1 Мая'), 1) (('name',), 1)
    	 859 (('int_name',), 1) (('name', 'улица 1 Мая'), 1) (('name',), 1)
    	 0
    	 0
    	 0
    	 0
    building fire_hydrant:city 11 2205 0 0
    	 3 ('М', 6) ('н', 4) ('р', 1)
    	 4 ('Минск', 2032) ('Микашевичи', 106) ('Озерщина', 66)
    	 12 (('name', 'М'), 6) (('name',), 6) (('building:levels',), 1)
    	 1430 (('name', 'М'), 6) (('name',), 6) (('building:levels',), 1)
    	 0
    	 0
    	 0
    	 0
    description fire_hydrant:housenumber 2204 80 8 11
    	 15 ('н', 2173) ('магазин', 4) ('ж', 4)
    	 53 ('Автомойка', 12) ('-Магазин', 4) ('-Романовича', 3)
    	 87 (('building',), 2195) (('building', 'yes'), 2193) (('addr:street',), 2102)
    	 61 (('building',), 2195) (('building', 'yes'), 2193) (('addr:street',), 2102)
    	 6 ('Пищеблок', 3) ('Ателье', 1) ('Автомойка', 1)
    	 6 ('Автомойка', 6) ('Ателье', 1) ('Транспортный цех', 1)
    	 40 (('name',), 7) (('building',), 6) (('building', 'yes'), 5)
    	 26 (('fire_hydrant:type',), 11) (('fire_hydrant:position', 'lane'), 11) (('fire_hydrant:diameter',), 11)
    addr:housenumber start_date 2202 28 0 0
    	 3 ('н', 2192) ('я', 6) ('ы', 4)
    	 10 ('XIX - 1-я половина XX', 6) ('1-я половина XX', 6) ('1912, XIX - 1-я половина XX', 4)
    	 65 (('building',), 2202) (('building', 'yes'), 2164) (('addr:street',), 1858)
    	 79 (('building',), 2202) (('building', 'yes'), 2164) (('addr:street',), 1858)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber fire_hydrant:city 551 2172 0 0
    	 2 ('н', 548) ('М', 3)
    	 4 ('Минск', 2032) ('Микашевичи', 106) ('Озерщина', 33)
    	 59 (('building',), 551) (('building', 'yes'), 543) (('addr:street',), 465)
    	 1430 (('building',), 551) (('building', 'yes'), 543) (('addr:street',), 465)
    	 0
    	 0
    	 0
    	 0
    building destination:backward 2167 282 0 0
    	 8 ('Н', 1771) ('н', 146) ('К', 72)
    	 104 ('Мінск', 16) ('Гродна', 9) ('Навагрудак;Парачаны', 8)
    	 24 (('name',), 491) (('name', 'Н'), 363) (('addr:street',), 83)
    	 223 (('name',), 491) (('name', 'Н'), 363) (('addr:street',), 83)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber comment 2150 132 0 0
    	 7 ('н', 1918) ('ж', 196) ('магазин', 20)
    	 10 ('Кольцевая дорога, даже H по своему значению не может быть tertiary', 108) ('Учреждение создано в соответствии с приказом Министерства образования и науки Республики Беларусь от 30.09.96 г. № 419 и входит в структуру БГУ. Учредителем государственного учреждения "Республиканский институт высшей школы" является БГУ', 6) ('Кинотеатр открыт ежедневно с 10:30. Время закрытия – 15 минут после начала последнего сеанса.', 4)
    	 94 (('building',), 2150) (('building', 'yes'), 2111) (('addr:street',), 1805)
    	 81 (('building',), 2150) (('building', 'yes'), 2111) (('addr:street',), 1805)
    	 0
    	 0
    	 0
    	 0
    description addr:full 2144 74 1 1
    	 8 ('н', 2120) ('ж', 10) ('Н', 5)
    	 43 ('д. Рудишки, Ошмянский район, Гродненская область', 8) ('д. Яново, Борисовский район, Минская область', 6) ('Псковская область, Себежский район, д.Долосцы', 4)
    	 64 (('building', 'yes'), 2142) (('building',), 2142) (('addr:street',), 2057)
    	 311 (('building', 'yes'), 2142) (('building',), 2142) (('addr:street',), 2057)
    	 1 ('155 км дороги М3 Минск-Витебск', 1)
    	 1 ('155 км дороги М3 Минск-Витебск', 1)
    	 40 (('compressed_air',), 1) (('fuel:octane', 'yes'), 1) (('fuel:octane_92', 'yes'), 1)
    	 40 (('compressed_air',), 1) (('fuel:octane', 'yes'), 1) (('fuel:octane_92', 'yes'), 1)
    addr:place addr:subdistrict 2109 723 37 313
    	 41 ('Первомайский', 522) ('Паперня', 316) ('Бор', 299)
    	 52 ('Гудогайский сельский Совет', 72) ('Первомайский сельский Совет', 64) ('Пограничный сельский Совет', 62)
    	 493 (('addr:housenumber',), 2051) (('building',), 2046) (('addr:street',), 1091)
    	 1964 (('addr:housenumber',), 2051) (('building',), 2046) (('addr:street',), 1091)
    	 23 ('Микрорайон "Военный городок"', 14) ('Костюковка', 2) ('Кохановский сельский Совет', 1)
    	 23 ('Гудогайский сельский Совет', 72) ('Логойский сельский Совет', 34) ('Пограничный сельский Совет', 31)
    	 173 (('addr:housenumber',), 37) (('building',), 33) (('building', 'yes'), 24)
    	 1001 (('name',), 294) (('addr:district',), 286) (('int_name',), 285)
    name crop 2103 42 17 2
    	 20 ('н', 1385) ('Продукты', 529) ('к', 40)
    	 9 ('Продукты_из_козьего_молока;Козий_сыр;Йогурут;Козий_творог', 10) ('цветы;саженцы', 6) ('голубика', 6)
    	 558 (('building',), 1731) (('building', 'yes'), 1548) (('shop',), 532)
    	 26 (('building',), 1731) (('building', 'yes'), 1548) (('shop',), 532)
    	 2 ('Смородина', 13) ('Яблоко', 4)
    	 2 ('Яблоко', 1) ('Смородина', 1)
    	 15 (('waterway',), 13) (('waterway', 'stream'), 12) (('tunnel', 'culvert'), 5)
    	 7 (('name',), 2) (('landuse',), 2) (('landuse', 'farmland'), 2)
    addr:housenumber addr:housenumber_1 2078 2 801 1
    	 2 ('8А', 1277) ('18А', 801)
    	 1 ('18А', 2)
    	 1847 (('building',), 2018) (('addr:street',), 1995) (('building', 'yes'), 1200)
    	 8 (('building',), 2018) (('addr:street',), 1995) (('building', 'yes'), 1200)
    	 1 ('18А', 801)
    	 1 ('18А', 1)
    	 829 (('building',), 783) (('addr:street',), 766) (('building', 'yes'), 480)
    	 8 (('addr:postcode',), 1) (('addr:street',), 1) (('building', 'yes'), 1)
    hamlet wikipedia 2063 103 0 0
    	 4 ('Октябрь', 2024) ('Дуравичи', 32) ('Череповка', 6)
    	 95 ('ru:Октябрьский (Гомельская область)', 2) ('ru:Красный Октябрь (Буда-Кошелёвский район)', 2) ('ru:Ковали (Октябрьский район)', 2)
    	 59 (('building', 'yes'), 2063) (('building',), 2063) (('addr:housenumber',), 2063)
    	 371 (('building', 'yes'), 2063) (('building',), 2063) (('addr:housenumber',), 2063)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city destination 2033 6 1017 4
    	 2 ('Минск', 2032) ('Могилёв', 1)
    	 3 ('Могилёв', 3) ('Лёзна;Орша;Минск', 2) ('Минск', 1)
    	 1136 (('fire_hydrant:type',), 2033) (('emergency', 'fire_hydrant'), 2033) (('emergency',), 2033)
    	 35 (('fire_hydrant:type',), 2033) (('emergency', 'fire_hydrant'), 2033) (('emergency',), 2033)
    	 2 ('Минск', 1016) ('Могилёв', 1)
    	 2 ('Могилёв', 3) ('Минск', 1)
    	 1136 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 20 (('type', 'destination_sign'), 3) (('colour:back',), 3) (('type',), 3)
    fire_hydrant:city designation 2032 2 0 0
    	 1 ('Минск', 2032)
    	 2 ('Минская киношкола-студия', 1) ('Минские торты', 1)
    	 1120 (('emergency', 'fire_hydrant'), 2032) (('fire_hydrant:type',), 2032) (('emergency',), 2032)
    	 17 (('emergency', 'fire_hydrant'), 2032) (('fire_hydrant:type',), 2032) (('emergency',), 2032)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city addr:province 2032 6 0 0
    	 1 ('Минск', 2032)
    	 2 ('Минская', 4) ('Минская область', 2)
    	 1120 (('emergency', 'fire_hydrant'), 2032) (('fire_hydrant:type',), 2032) (('emergency',), 2032)
    	 24 (('emergency', 'fire_hydrant'), 2032) (('fire_hydrant:type',), 2032) (('emergency',), 2032)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber sport 2031 23 0 0
    	 4 ('н', 1918) ('ж', 98) ('ы', 14)
    	 10 ('soccer;ы', 7) ('equestrian;лошади;конный_спорт;конюшня', 3) ('Тренажерный_зал,_фитнес', 3)
    	 74 (('building',), 2031) (('building', 'yes'), 2002) (('addr:street',), 1708)
    	 51 (('building',), 2031) (('building', 'yes'), 2002) (('addr:street',), 1708)
    	 0
    	 0
    	 0
    	 0
    building clothes 2018 65 0 0
    	 4 ('Н', 1932) ('К', 36) ('н', 26)
    	 13 ('Женская_одежда;Мужская_одежда;Детская_одежда;Колготки;Чулки;Носки;Белье;Купальники', 20) ('Женская_одежда;Мужская_одежда;Одежда_для_детей;Носки;Колготки;Чулки;Белье;Купальники', 4) ('Женская_одежда;Мужская_одежда;Детская_одежда;Чулки;Колготки;Носки;Купальники;Белье', 4)
    	 9 (('name',), 456) (('name', 'Н'), 396) (('name', 'М'), 24)
    	 117 (('name',), 456) (('name', 'Н'), 396) (('name', 'М'), 24)
    	 0
    	 0
    	 0
    	 0
    name destination:lanes:backward 2015 34 0 0
    	 16 ('н', 831) ('Н', 764) ('Минск', 126)
    	 3 ('Сморгонь;Минск;Вилейка;Нарочь|Минск;Вилейка;Нарочь', 13) ('Воложин;Сморгонь|Минск', 11) ('Минск;Вилейка;Нарочь|Минск', 10)
    	 362 (('building',), 1734) (('building', 'yes'), 1089) (('building', 'residential'), 541)
    	 41 (('building',), 1734) (('building', 'yes'), 1089) (('building', 'residential'), 541)
    	 0
    	 0
    	 0
    	 0
    addr:housename desc 2012 52 0 0
    	 10 ('н', 1566) ('Н', 279) ('к', 70)
    	 11 ('Поворот налево с Немиги на Мясникова запрещен в будние дни c 7 до 22', 7) ('магазин аккумуляторных батарей для автомобилей', 6) ('тропически-умеренное фьюжен бразильской и белорусской природы', 6)
    	 117 (('building',), 2008) (('building', 'yes'), 1957) (('addr:street',), 1490)
    	 76 (('building',), 2008) (('building', 'yes'), 1957) (('addr:street',), 1490)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber addr:suburb 2006 275 0 0
    	 8 ('н', 1918) ('ж', 49) ('П', 30)
    	 8 ('Октябрьский микрорайон', 80) ('микрорайон Полесье', 58) ('Первомайский микрорайон', 58)
    	 96 (('building',), 2005) (('building', 'yes'), 1959) (('addr:street',), 1685)
    	 216 (('building',), 2005) (('building', 'yes'), 1959) (('addr:street',), 1685)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber design:ref 1991 428 0 0
    	 7 ('4А', 1581) ('64А', 141) ('Н', 120)
    	 13 ('1-464ДН', 336) ('90М', 56) ('М111-90', 11)
    	 1815 (('building',), 1921) (('addr:street',), 1857) (('building', 'yes'), 1179)
    	 328 (('building',), 1921) (('addr:street',), 1857) (('building', 'yes'), 1179)
    	 0
    	 0
    	 0
    	 0
    building artist_name 1952 295 0 0
    	 8 ('Н', 1610) ('н', 152) ('р', 85)
    	 117 ('А.Гурщенкова', 10) ('Игорь Зосимович, Екатерина Зантария, Полина Богданова', 9) ('Максим Карпович', 9)
    	 23 (('name',), 417) (('name', 'Н'), 330) (('building:levels',), 95)
    	 512 (('name',), 417) (('name', 'Н'), 330) (('building:levels',), 95)
    	 0
    	 0
    	 0
    	 0
    line addr:street 25 1941 0 0
    	 2 ('Московская', 20) ('Автозаводская', 5)
    	 3 ('Московская улица', 1849) ('Автозаводская улица', 73) ('1-я Московская улица', 19)
    	 48 (('name',), 25) (('operator',), 25) (('colour',), 25)
    	 1252 (('name',), 25) (('operator',), 25) (('colour',), 25)
    	 0
    	 0
    	 0
    	 0
    ref was:ref 1932 488 84 52
    	 103 ('Н2', 575) ('Н3', 270) ('Н', 228)
    	 57 ('Н10351', 30) ('Н2861', 25) ('Н3192', 20)
    	 292 (('highway',), 1674) (('surface',), 1595) (('highway', 'tertiary'), 1567)
    	 76 (('highway',), 1674) (('surface',), 1595) (('highway', 'tertiary'), 1567)
    	 27 ('Н7023', 8) ('Н3170', 8) ('Н3125', 6)
    	 27 ('Н10351', 6) ('Н2861', 5) ('Н2563', 4)
    	 80 (('highway',), 79) (('surface',), 68) (('highway', 'tertiary'), 61)
    	 49 (('highway',), 52) (('surface',), 45) (('surface', 'ground'), 23)
    addr:housenumber was:name:prefix 1927 1176 0 0
    	 3 ('н', 1918) ('я', 5) ('ы', 4)
    	 9 ('деревня', 1112) ('имение', 34) ('застенок', 13)
    	 65 (('building',), 1927) (('building', 'yes'), 1894) (('addr:street',), 1626)
    	 2007 (('building',), 1927) (('building', 'yes'), 1894) (('addr:street',), 1626)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber nat_ref 1921 60 0 0
    	 2 ('Н', 1920) ('М', 1)
    	 17 ('Н-28', 22) ('М4', 10) ('Н136', 6)
    	 80 (('building',), 1905) (('building', 'yes'), 1857) (('addr:street',), 1681)
    	 96 (('building',), 1905) (('building', 'yes'), 1857) (('addr:street',), 1681)
    	 0
    	 0
    	 0
    	 0
    operator source:ref 4 1920 0 0
    	 3 ('я', 2) ('б', 1) ('е', 1)
    	 2 ('Публичная кадастровая карта', 1918) ('Договор между РФ и Украиной от 28 января 2003 года (приложение 1)', 2)
    	 9 (('amenity', 'atm'), 3) (('amenity',), 3) (('name',), 2)
    	 372 (('amenity', 'atm'), 3) (('amenity',), 3) (('name',), 2)
    	 0
    	 0
    	 0
    	 0
    description source:ref 109 1920 0 0
    	 3 ('н', 106) ('ж', 2) ('стр', 1)
    	 2 ('Публичная кадастровая карта', 1918) ('Договор между РФ и Украиной от 28 января 2003 года (приложение 1)', 2)
    	 8 (('building',), 109) (('building', 'yes'), 109) (('addr:street',), 104)
    	 372 (('building',), 109) (('building', 'yes'), 109) (('addr:street',), 104)
    	 0
    	 0
    	 0
    	 0
    building source:ref 6 1920 0 0
    	 2 ('н', 4) ('р', 2)
    	 2 ('Публичная кадастровая карта', 1918) ('Договор между РФ и Украиной от 28 января 2003 года (приложение 1)', 2)
    	 10 (('building:levels',), 2) (('addr:postcode', '231288'), 2) (('addr:postcode',), 2)
    	 372 (('building:levels',), 2) (('addr:postcode', '231288'), 2) (('addr:postcode',), 2)
    	 0
    	 0
    	 0
    	 0
    building heritage:description 1910 270 0 0
    	 10 ('Н', 1449) ('н', 184) ('К', 99)
    	 103 ('Будынак былой жаночай Марыінскай гімназіі', 8) ('Манастырскі корпус', 6) ('Абеліск ”Мінск горад-герой“', 6)
    	 27 (('name',), 433) (('name', 'Н'), 297) (('addr:street',), 102)
    	 618 (('name',), 433) (('name', 'Н'), 297) (('addr:street',), 102)
    	 0
    	 0
    	 0
    	 0
    official_short_type related_law 1907 1 0 0
    	 1 ('ВЛ', 1907)
    	 1 ('ПОСТАНОВЛЕНИЕ СОВЕТА МИНИСТРОВ РЕСПУБЛИКИ БЕЛАРУСЬ 30 июня 2015', 1)
    	 1008 (('power',), 1901) (('cables',), 1896) (('voltage',), 1896)
    	 14 (('power',), 1901) (('cables',), 1896) (('voltage',), 1896)
    	 0
    	 0
    	 0
    	 0
    name name_3 1901 31 4 2
    	 19 ('н', 1385) ('Н', 382) ('ж', 30)
    	 5 ('магазин детской одежды', 11) ('Пошив и ремонт одежды', 7) ('Холдинг "Пассат"', 6)
    	 114 (('building',), 1878) (('building', 'yes'), 1484) (('building', 'residential'), 333)
    	 68 (('building',), 1878) (('building', 'yes'), 1484) (('building', 'residential'), 333)
    	 2 ('Холдинг "Пассат"', 3) ('магазин детской одежды', 1)
    	 2 ('Холдинг "Пассат"', 1) ('магазин детской одежды', 1)
    	 32 (('military',), 1) (('military', 'checkpoint'), 1) (('description',), 1)
    	 33 (('name',), 2) (('name_2',), 2) (('name_1',), 2)
    addr:unit brand 75 1871 0 0
    	 2 ('Б', 58) ('А', 17)
    	 69 ('Белоруснефть', 884) ('Беларусбанк', 266) ('Белшина', 169)
    	 23 (('addr:street',), 75) (('addr:housenumber',), 75) (('addr:city',), 75)
    	 4955 (('addr:street',), 75) (('addr:housenumber',), 75) (('addr:city',), 75)
    	 0
    	 0
    	 0
    	 0
    addr:place addr:district 175 1848 2 1
    	 5 ('Остров', 144) ('Бор', 23) ('Рудня', 4)
    	 5 ('Островецкий район', 691) ('Борисовский район', 614) ('Буда-Кошелёвский район', 471)
    	 150 (('building',), 174) (('addr:housenumber',), 171) (('building', 'yes'), 170)
    	 3952 (('building',), 174) (('addr:housenumber',), 171) (('building', 'yes'), 170)
    	 1 ('Костюковка', 2)
    	 1 ('Костюковка', 1)
    	 42 (('addr:housenumber',), 2) (('addr:city',), 2) (('operator', 'Белагропромбанк'), 1)
    	 34 (('addr:street', 'улица Незалежности'), 1) (('contact:phone', '+375 29 3995054'), 1) (('contact:email',), 1)
    addr:housename fee 1838 48 2 2
    	 8 ('н', 1740) ('к', 63) ('м', 12)
    	 13 ('Беларусбанк', 8) ('БелАгропром банкомат', 6) ('Банкомат', 5)
    	 69 (('building',), 1836) (('building', 'yes'), 1785) (('addr:street',), 1300)
    	 39 (('building',), 1836) (('building', 'yes'), 1785) (('addr:street',), 1300)
    	 1 ('Беларусбанк', 2)
    	 1 ('Беларусбанк', 2)
    	 14 (('addr:street',), 2) (('building', 'yes'), 2) (('building',), 2)
    	 6 (('amenity', 'atm'), 2) (('amenity',), 2) (('name', 'Белагропромбанк'), 1)
    ref network 220 1837 14 2
    	 15 ('М', 48) ('Т', 38) ('СТ', 30)
    	 60 ('Барановичское отделение', 496) ('Минский метрополитен', 262) ('прыгарад СТіС', 219)
    	 113 (('aeroway', 'taxiway'), 69) (('aeroway',), 69) (('name',), 68)
    	 861 (('aeroway', 'taxiway'), 69) (('aeroway',), 69) (('name',), 68)
    	 2 ('7а', 13) ('Брест - Москва', 1)
    	 2 ('7а', 1) ('Брест - Москва', 1)
    	 59 (('type',), 13) (('name',), 12) (('type', 'route'), 11)
    	 24 (('name',), 2) (('public_transport',), 2) (('name', 'Школа #54'), 1)
    designation addr:subdistrict 92 1833 0 0
    	 2 ('б', 91) ('Городище', 1)
    	 92 ('Кобринский р-н', 634) ('Октябрьский сельский Совет', 81) ('Подлабенский сельский Совет', 58)
    	 11 (('name',), 92) (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 91) (('addr:street',), 91)
    	 3816 (('name',), 92) (('name', 'ООО"БЕЛ-ИЗОЛИТ-СЕРВИС"'), 91) (('addr:street',), 91)
    	 0
    	 0
    	 0
    	 0
    addr:city fire_hydrant:housenumber 1828 26 1 1
    	 10 ('Брест', 1383) ('Бобруйск', 124) ('Остров', 96)
    	 11 ('131 -Речицатекстиль', 6) ('-Бобруйская', 6) ('-П.Бровки', 5)
    	 1486 (('addr:housenumber',), 1799) (('addr:street',), 1701) (('building',), 1630)
    	 38 (('addr:housenumber',), 1799) (('addr:street',), 1701) (('building',), 1630)
    	 1 ('35а', 1)
    	 1 ('35а', 1)
    	 2 (('building',), 1) (('building', 'house'), 1)
    	 22 (('fire_hydrant:type',), 1) (('fire_hydrant:position', 'lane'), 1) (('fire_hydrant:diameter',), 1)
    fence_type addr:city 44 1827 0 0
    	 2 ('да', 42) ('Забор', 2)
    	 43 ('Ждановичи', 392) ('Буда-Люшевская', 231) ('Лазовец дачи', 194)
    	 6 (('barrier',), 44) (('barrier', 'fence'), 44) (('material',), 2)
    	 1038 (('barrier',), 44) (('barrier', 'fence'), 44) (('material',), 2)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber disused:name 1821 14 0 0
    	 8 ('н', 1644) ('Н', 120) ('ж', 49)
    	 9 ('Бистрономия', 3) ('Винный шкаф', 2) ('Мама Чанг', 2)
    	 132 (('building',), 1820) (('building', 'yes'), 1791) (('addr:street',), 1535)
    	 15 (('building',), 1820) (('building', 'yes'), 1791) (('addr:street',), 1535)
    	 0
    	 0
    	 0
    	 0
    name wheelchair:description 1813 88 0 0
    	 18 ('н', 1385) ('кн', 246) ('п', 51)
    	 5 ('Очень крутой подъём.', 60) ('Полное отсутствие доступности, много больших ступенек на входе', 12) ('Ступеньки, но есть кнопка вызова', 8)
    	 68 (('building',), 1799) (('building', 'yes'), 1684) (('addr:street',), 116)
    	 56 (('building',), 1799) (('building', 'yes'), 1684) (('addr:street',), 116)
    	 0
    	 0
    	 0
    	 0
    description via 1808 58 0 0
    	 5 ('н', 1802) ('ж', 2) ('Н', 2)
    	 35 ('пл. Ленина', 10) ('Сквер Героя Карвата', 2) ('Снежкова, Бронное, Горошков', 2)
    	 14 (('building',), 1806) (('building', 'yes'), 1806) (('addr:street',), 1738)
    	 204 (('building',), 1806) (('building', 'yes'), 1806) (('addr:street',), 1738)
    	 0
    	 0
    	 0
    	 0
    cycleway:left addr:city 42 1798 0 0
    	 1 ('да', 42)
    	 42 ('Ждановичи', 392) ('Буда-Люшевская', 231) ('Лазовец дачи', 194)
    	 6 (('int_name',), 42) (('name', 'улица 1 Мая'), 42) (('name',), 42)
    	 1031 (('int_name',), 42) (('name', 'улица 1 Мая'), 42) (('name',), 42)
    	 0
    	 0
    	 0
    	 0
    designation source 24 1791 2 2
    	 3 ('б', 22) ('ЯМА', 1) ('отделение ОАО Беларусбанк', 1)
    	 23 ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 1102) ('Публичная кадастровая карта nca.by', 465) ('ГУП "Национальное кадастровое агентство" публичная карта', 75)
    	 18 (('addr:street',), 23) (('building', 'yes'), 23) (('name',), 23)
    	 741 (('addr:street',), 23) (('building', 'yes'), 23) (('name',), 23)
    	 2 ('ЯМА', 1) ('отделение ОАО Беларусбанк', 1)
    	 2 ('ЯМА', 1) ('отделение ОАО Беларусбанк', 1)
    	 15 (('source',), 2) (('source', 'ЯМА'), 1) (('building:levels',), 1)
    	 15 (('designation',), 2) (('designation', 'ЯМА'), 1) (('building:levels',), 1)
    official_status addr:city 1789 95 0 0
    	 3 ('садоводческое товарищество', 1777) ('Садоводческое товарищество', 11) ('Строитель', 1)
    	 3 ('Строитель-2', 91) ('садоводческое товарищество Отдых, Ждановичский сельсовет, Минский район, Минская область, Беларусь', 3) ('Садоводческое товарищество "Усяжа"', 1)
    	 4038 (('name',), 1788) (('place', 'allotments'), 1735) (('place',), 1735)
    	 104 (('name',), 1788) (('place', 'allotments'), 1735) (('place',), 1735)
    	 0
    	 0
    	 0
    	 0
    name fire_hydrant:diameter 1003 1787 805 833
    	 6 ('К-150', 803) ('Т', 100) ('К', 95)
    	 9 ('К-150', 1596) ('Т-100', 102) ('К-350', 32)
    	 545 (('emergency', 'fire_hydrant'), 805) (('emergency',), 805) (('fire_hydrant:type',), 803)
    	 771 (('emergency', 'fire_hydrant'), 805) (('emergency',), 805) (('fire_hydrant:type',), 803)
    	 3 ('К-150', 803) ('К-200', 1) ('Т-100', 1)
    	 3 ('К-150', 798) ('Т-100', 34) ('К-200', 1)
    	 536 (('emergency', 'fire_hydrant'), 805) (('emergency',), 805) (('fire_hydrant:type',), 803)
    	 613 (('fire_hydrant:type',), 833) (('name',), 833) (('fire_operator',), 833)
    addr:housenumber was:official_name 1760 27 0 0
    	 5 ('н', 1644) ('П', 60) ('ж', 49)
    	 7 ('Каменка - Першино - Полишино', 12) ('Красулино - Юрково - Поташи', 4) ('Подъезд к д. Ажугеры от а/д Рымдюны - Солы', 4)
    	 88 (('building',), 1760) (('building', 'yes'), 1704) (('addr:street',), 1475)
    	 23 (('building',), 1760) (('building', 'yes'), 1704) (('addr:street',), 1475)
    	 0
    	 0
    	 0
    	 0
    addr:housename name_1 1755 41 7 1
    	 10 ('н', 1392) ('Н', 279) ('к', 28)
    	 9 ('Холдинг "Пассат"', 9) ('Натариальная контора', 6) ('памятники', 5)
    	 101 (('building',), 1752) (('building', 'yes'), 1708) (('addr:street',), 1294)
    	 103 (('building',), 1752) (('building', 'yes'), 1708) (('addr:street',), 1294)
    	 1 ('Баня', 7)
    	 1 ('Баня', 1)
    	 14 (('addr:street',), 7) (('building', 'yes'), 7) (('building',), 7)
    	 20 (('addr:street', 'улица Рыбиновского'), 1) (('tourism',), 1) (('name_3',), 1)
    name surface 1750 140 13 3
    	 29 ('н', 1385) ('п', 102) ('к', 70)
    	 14 ('асфальт', 30) ('Русловое, сезонного регулирования. Состав сооружений гидроузла: плотина (длина 9,9 км, максимальная высота 5 м), ограждающие дамбы (общая длина 7,8 км, максимальная высота 3,85 м), водосброс, 4 водозабора, насосная станция. Водятся щука, лещ, густера, ук', 20) ('плитка', 20)
    	 152 (('building',), 1689) (('building', 'yes'), 1556) (('building:levels',), 149)
    	 77 (('building',), 1689) (('building', 'yes'), 1556) (('building:levels',), 149)
    	 3 ('Косовщина', 9) ('Стерково', 2) ('Истоки', 2)
    	 3 ('Косовщина', 1) ('Стерково', 1) ('Истоки', 1)
    	 63 (('int_name',), 13) (('place',), 13) (('place', 'hamlet'), 12)
    	 6 (('type', 'associatedStreet'), 3) (('type',), 3) (('noname',), 2)
    destination destination:forward 1722 220 375 123
    	 96 ('Мiнск', 623) ('Брэст', 315) ('Гомель', 192)
    	 79 ('Мiнск', 16) ('12-ы кіламетр МКАД;Слуцк;Гродна;Брэст', 12) ('Мінск;Брэст', 9)
    	 188 (('highway',), 1701) (('oneway', 'yes'), 1700) (('oneway',), 1700)
    	 234 (('highway',), 1701) (('oneway', 'yes'), 1700) (('oneway',), 1700)
    	 66 ('Мiнск', 89) ('Брэст', 45) ('Мінск', 39)
    	 66 ('Мiнск', 16) ('Брэст', 7) ('Барановичи', 5)
    	 161 (('highway',), 371) (('oneway', 'yes'), 370) (('oneway',), 370)
    	 204 (('highway',), 123) (('surface', 'asphalt'), 117) (('surface',), 117)
    name destination:ref 1709 75 3 4
    	 10 ('Н', 1146) ('н', 277) ('М', 208)
    	 25 ('М6', 15) ('М1', 8) ('Р5', 8)
    	 87 (('building',), 1592) (('building', 'residential'), 765) (('building', 'yes'), 682)
    	 90 (('building',), 1592) (('building', 'residential'), 765) (('building', 'yes'), 682)
    	 1 ('М1', 3)
    	 1 ('М1', 4)
    	 23 (('amenity',), 3) (('building',), 2) (('amenity', 'car_wash'), 1)
    	 17 (('oneway',), 4) (('oneway', 'yes'), 4) (('highway',), 4)
    building:levels wikipedia 1461 1698 0 0
    	 1 ('Н', 1461)
    	 1461 ('be:Альхоўка (басейн Нёмана)', 38) ('be:Уса (прыток Нёмана)', 19) ('be:Нявежа', 17)
    	 2 (('building', 'yes'), 1461) (('building',), 1461)
    	 4737 (('building', 'yes'), 1461) (('building',), 1461)
    	 0
    	 0
    	 0
    	 0
    addr:housename cuisine 1661 35 0 0
    	 6 ('н', 1566) ('к', 56) ('ж', 20)
    	 12 ('coffee;блины;кофе;чай;молочный_коктейль;пицца', 5) ('кондитерская', 4) ('выпечка_и_пирожные', 4)
    	 61 (('building',), 1661) (('building', 'yes'), 1613) (('addr:street',), 1179)
    	 78 (('building',), 1661) (('building', 'yes'), 1613) (('addr:street',), 1179)
    	 0
    	 0
    	 0
    	 0
    addr:place from 1659 69 772 13
    	 20 ('Малейковщизна', 351) ('Микрорайон', 210) ('Колядичи', 193)
    	 32 ('ДС Малиновка-4', 15) ('Микрорайон «Северный»', 5) ('Больница Островля', 4)
    	 412 (('building',), 1627) (('addr:housenumber',), 1603) (('building', 'house'), 754)
    	 255 (('building',), 1627) (('addr:housenumber',), 1603) (('building', 'house'), 754)
    	 8 ('Малейковщизна', 351) ('Колядичи', 193) ('Шейбаки', 139)
    	 8 ('Зарица', 3) ('Колядичи', 2) ('Шейбаки', 2)
    	 333 (('building',), 752) (('addr:housenumber',), 746) (('building', 'house'), 579)
    	 82 (('to',), 13) (('name',), 13) (('route',), 13)
    description subject:wikipedia 1654 38 0 0
    	 4 ('н', 1643) ('ж', 8) ('Н', 2)
    	 34 ('ru:Прилежаев, Николай Александрович', 3) ('ru:Пестрак, Филипп Семёнович', 2) ('be:Народны камісарыят юстыцыі БССР', 2)
    	 8 (('building',), 1654) (('building', 'yes'), 1654) (('addr:street',), 1591)
    	 178 (('building',), 1654) (('building', 'yes'), 1654) (('addr:street',), 1591)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber name_3 1644 14 0 0
    	 6 ('н', 1370) ('Н', 120) ('ж', 98)
    	 5 ('Пошив и ремонт одежды', 4) ('магазин детской одежды', 4) ('Банька У Нарвы', 3)
    	 159 (('building',), 1643) (('building', 'yes'), 1600) (('addr:street',), 1384)
    	 68 (('building',), 1643) (('building', 'yes'), 1600) (('addr:street',), 1384)
    	 0
    	 0
    	 0
    	 0
    building opening_hours 1640 205 0 0
    	 7 ('Н', 1127) ('дн', 245) ('н', 202)
    	 110 ('круглосуточно', 4) ('зимний период: с 12.00 до 23:00. летний период: с 10.00 до 01:00, ежедневно без выходных.', 4) ('ПН-ПТ с 9.00 до 21.00  СБ, ВС – выходной', 4)
    	 24 (('name',), 315) (('name', 'Н'), 231) (('addr:street',), 119)
    	 772 (('name',), 315) (('name', 'Н'), 231) (('addr:street',), 119)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber was:operator 1638 16 0 0
    	 9 ('н', 1370) ('Н', 120) ('П', 60)
    	 9 ('ТПУП "Металлургторг"', 3) ('ООО "ОП НИИ ПКД"', 2) ('ЛКУПП ЖКХ "Лепель"', 2)
    	 171 (('building',), 1631) (('building', 'yes'), 1572) (('addr:street',), 1375)
    	 94 (('building',), 1631) (('building', 'yes'), 1572) (('addr:street',), 1375)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber ref:minskgrado 1635 64 0 0
    	 10 ('1Б', 911) ('П', 690) ('1П', 12)
    	 55 ('8.1П', 2) ('9.1П', 2) ('3.1П', 2)
    	 1101 (('building',), 1591) (('addr:street',), 1411) (('building', 'yes'), 849)
    	 199 (('building',), 1591) (('addr:street',), 1411) (('building', 'yes'), 849)
    	 0
    	 0
    	 0
    	 0
    brand brand:wikipedia 1633 366 0 0
    	 24 ('Белоруснефть', 884) ('Беларусбанк', 266) ('Белпошта', 164)
    	 24 ('be:Белпошта', 162) ('ru:Белоруснефть', 55) ('ru:Белинвестбанк', 34)
    	 5019 (('amenity',), 1577) (('name',), 1374) (('opening_hours',), 1300)
    	 1512 (('amenity',), 1577) (('name',), 1374) (('opening_hours',), 1300)
    	 0
    	 0
    	 0
    	 0
    name denomination 1624 49 3 3
    	 25 ('н', 831) ('Н', 382) ('ТП', 198)
    	 10 ('Православый приход свт. Николая Чудотворца', 9) ('Апостольская_церковь', 8) ('Евангельские_христиане-баптисты', 7)
    	 160 (('building',), 1558) (('building', 'yes'), 1112) (('building', 'residential'), 304)
    	 66 (('building',), 1558) (('building', 'yes'), 1112) (('building', 'residential'), 304)
    	 3 ('Хабад', 1) ('православная', 1) ('ТП-262', 1)
    	 3 ('Хабад', 1) ('православная', 1) ('ТП-262', 1)
    	 24 (('amenity',), 2) (('building',), 2) (('addr:housenumber', '67'), 1)
    	 30 (('addr:street',), 3) (('building',), 3) (('addr:housenumber',), 3)
    description FIXME 1617 48 0 0
    	 5 ('н', 1590) ('ж', 14) ('улица', 7)
    	 31 ('беседка? зонтик? ...? нужны доп. теги', 4) ('проверить куда она приведёт', 3) ('Уточнить подъезды по трекам, виды топлива, оператора', 2)
    	 35 (('building',), 1608) (('building', 'yes'), 1607) (('addr:street',), 1546)
    	 147 (('building',), 1608) (('building', 'yes'), 1607) (('addr:street',), 1546)
    	 0
    	 0
    	 0
    	 0
    was:name:prefix addr:street 1614 207 0 0
    	 3 ('посёлок', 1040) ('деревня', 556) ('станция', 18)
    	 23 ('посёлок Славгородский', 57) ('Якимовка станция', 30) ('Заяченье посёлок', 29)
    	 2150 (('name',), 1614) (('place',), 1614) (('abandoned:place',), 1572)
    	 158 (('name',), 1614) (('place',), 1614) (('abandoned:place',), 1572)
    	 0
    	 0
    	 0
    	 0
    name wikipedia:be-tarask 1609 27 0 0
    	 13 ('н', 1108) ('Н', 382) ('к', 40)
    	 5 ('Межава (Аршанскі раён)', 9) ('Паўлінава (Баранавіцкі раён)', 7) ('Лагі (Аршанскі раён)', 6)
    	 137 (('building',), 1567) (('building', 'yes'), 1197) (('building', 'residential'), 313)
    	 62 (('building',), 1567) (('building', 'yes'), 1197) (('building', 'residential'), 313)
    	 0
    	 0
    	 0
    	 0
    addr:place to 1574 68 727 13
    	 17 ('Малейковщизна', 351) ('Микрорайон', 210) ('Колядичи', 193)
    	 29 ('ДС Малиновка-4', 16) ('Микрорайон Северный', 4) ('Больница Островля', 4)
    	 382 (('building',), 1542) (('addr:housenumber',), 1525) (('addr:postcode',), 732)
    	 221 (('building',), 1542) (('addr:housenumber',), 1525) (('addr:postcode',), 732)
    	 7 ('Малейковщизна', 351) ('Колядичи', 193) ('Шейбаки', 139)
    	 7 ('Зарица', 3) ('Колядичи', 2) ('Малейковщизна', 2)
    	 304 (('addr:housenumber',), 708) (('building',), 707) (('building', 'house'), 579)
    	 65 (('route',), 13) (('type',), 13) (('public_transport:version', '2'), 13)
    source:official_name source 3 1574 1 7
    	 1 ('Публичная кадастровая карта', 3)
    	 3 ('Публичная кадастровая карта ГУП Национальное кадастровое агентство', 1102) ('Публичная кадастровая карта nca.by', 465) ('Публичная кадастровая карта', 7)
    	 8 (('official_name', 'Подъезд к кладбищу д.Остров от а/д Гомель - Лопатино - Остров'), 3) (('surface', 'unpaved'), 3) (('surface',), 3)
    	 536 (('official_name', 'Подъезд к кладбищу д.Остров от а/д Гомель - Лопатино - Остров'), 3) (('surface', 'unpaved'), 3) (('surface',), 3)
    	 1 ('Публичная кадастровая карта', 1)
    	 1 ('Публичная кадастровая карта', 7)
    	 8 (('official_name', 'Подъезд к кладбищу д.Остров от а/д Гомель - Лопатино - Остров'), 1) (('surface', 'unpaved'), 1) (('surface',), 1)
    	 41 (('int_name',), 7) (('source:ref',), 7) (('name',), 7)
    fence_type official_name 733 1568 0 0
    	 3 ('да', 706) ('Забор', 24) ('камень', 3)
    	 721 ('Буда-Кошелево — Уваровичи — Калинино', 48) ('Узда - Теляково - Горбаты', 28) ('Лида - Радунь', 24)
    	 6 (('barrier',), 733) (('barrier', 'fence'), 733) (('material',), 24)
    	 2571 (('barrier',), 733) (('barrier', 'fence'), 733) (('material',), 24)
    	 0
    	 0
    	 0
    	 0
    destination destination:backward 1552 240 405 119
    	 122 ('Мiнск', 356) ('Брэст', 270) ('Гомель', 224)
    	 99 ('Калодзішчы;Заслаўе', 18) ('Магілёў;Брэст;Гомель;Масква', 10) ('Ашмяны;Вiльнюс', 9)
    	 203 (('oneway', 'yes'), 1526) (('oneway',), 1526) (('highway',), 1526)
    	 225 (('oneway', 'yes'), 1526) (('oneway',), 1526) (('highway',), 1526)
    	 80 ('Мiнск', 89) ('Брэст', 45) ('Мінск', 39)
    	 80 ('Мінск', 8) ('Калодзішчы;Заслаўе', 6) ('Брэст', 5)
    	 163 (('oneway', 'yes'), 401) (('oneway',), 401) (('highway',), 401)
    	 186 (('highway',), 119) (('surface',), 114) (('surface', 'asphalt'), 114)
    description network 1551 1033 0 0
    	 4 ('н', 1537) ('ж', 6) ('Н', 6)
    	 37 ('Барановичское отделение', 496) ('Минский метрополитен', 262) ('Брестское отделение', 70)
    	 18 (('building',), 1549) (('building', 'yes'), 1549) (('addr:street',), 1491)
    	 632 (('building',), 1549) (('building', 'yes'), 1549) (('addr:street',), 1491)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city fire_hydrant:housenumber 1532 7 0 0
    	 1 ('Речица', 1532)
    	 2 ('131 -Речицатекстиль', 6) ('Речицапиво', 1)
    	 500 (('fire_hydrant:type',), 1532) (('fire_hydrant:position', 'lane'), 1532) (('fire_hydrant:diameter',), 1532)
    	 23 (('fire_hydrant:type',), 1532) (('fire_hydrant:position', 'lane'), 1532) (('fire_hydrant:diameter',), 1532)
    	 0
    	 0
    	 0
    	 0
    substation name 1060 1531 1 198
    	 1 ('ТП', 1060)
    	 1060 ('ТП', 198) ('ЦТП', 126) ('КТП', 8)
    	 8 (('name', 'ТП'), 1060) (('addr:street',), 1060) (('building', 'yes'), 1060)
    	 935 (('name', 'ТП'), 1060) (('addr:street',), 1060) (('building', 'yes'), 1060)
    	 1 ('ТП', 1)
    	 1 ('ТП', 198)
    	 8 (('name', 'ТП'), 1) (('addr:street',), 1) (('building', 'yes'), 1)
    	 86 (('building',), 161) (('power',), 132) (('power', 'substation'), 109)
    addr:province wikipedia 1528 644 0 0
    	 7 ('Минская', 468) ('Витебская', 276) ('Минская область', 230)
    	 372 ('ru:Воропаево (Витебская область)', 4) ('ru:Сураж (Витебская область)', 4) ('ru:Каменский сельсовет (Витебская область)', 4)
    	 95 (('addr:district',), 1528) (('building',), 1346) (('addr:street',), 1252)
    	 1550 (('addr:district',), 1528) (('building',), 1346) (('addr:street',), 1252)
    	 0
    	 0
    	 0
    	 0
    cycleway:left official_name 706 1527 0 0
    	 1 ('да', 706)
    	 706 ('Буда-Кошелево — Уваровичи — Калинино', 48) ('Узда - Теляково - Горбаты', 28) ('Лида - Радунь', 24)
    	 6 (('int_name',), 706) (('name', 'улица 1 Мая'), 706) (('name',), 706)
    	 2549 (('int_name',), 706) (('name', 'улица 1 Мая'), 706) (('name',), 706)
    	 0
    	 0
    	 0
    	 0
    name local_ref 1521 40 18 4
    	 26 ('н', 831) ('Н', 382) ('Больница', 102)
    	 9 ('Автобусная остановка', 10) ('10-я Городская Клиническая Больница', 8) ('Остановка автобуса', 8)
    	 273 (('building',), 1365) (('building', 'yes'), 984) (('building', 'residential'), 310)
    	 41 (('building',), 1365) (('building', 'yes'), 984) (('building', 'residential'), 310)
    	 4 ('Харовичи', 6) ('Носилово', 5) ('Автобусная остановка', 5)
    	 4 ('Носилово', 1) ('Харовичи', 1) ('Автобусная остановка', 1)
    	 74 (('highway', 'bus_stop'), 8) (('highway',), 8) (('public_transport',), 7)
    	 23 (('highway', 'bus_stop'), 4) (('highway',), 4) (('name',), 3)
    addr:housenumber wheelchair:description 1519 15 0 0
    	 6 ('н', 1370) ('кн', 129) ('П', 15)
    	 5 ('Очень крутой подъём.', 6) ('Полное отсутствие доступности, много больших ступенек на входе', 3) ('Ступеньки, но есть кнопка вызова', 3)
    	 124 (('building',), 1519) (('building', 'yes'), 1486) (('addr:street',), 1274)
    	 56 (('building',), 1519) (('building', 'yes'), 1486) (('addr:street',), 1274)
    	 0
    	 0
    	 0
    	 0
    addr:housename BY_PT:note 478 1512 0 0
    	 6 ('Н', 279) ('н', 174) ('ж', 20)
    	 1 ('Тэги типа "BY_PT..." - временные, для внесения ОТ Беларуси! Не удаляйте их - они будут удалены позже.', 1512)
    	 83 (('building',), 476) (('building', 'yes'), 468) (('addr:street',), 396)
    	 166 (('building',), 476) (('building', 'yes'), 468) (('addr:street',), 396)
    	 0
    	 0
    	 0
    	 0
    addr:housename access 1499 42 0 0
    	 9 ('н', 1392) ('к', 56) ('ж', 20)
    	 9 ('место_для_инвалидов', 8) ('Стоянки_им._Жени_Иванова_(с_беседкой)', 6) ('Ящик для предложений СТ "Криница-Кривополье"', 5)
    	 71 (('building',), 1498) (('building', 'yes'), 1458) (('addr:street',), 1068)
    	 69 (('building',), 1498) (('building', 'yes'), 1458) (('addr:street',), 1068)
    	 0
    	 0
    	 0
    	 0
    building was:name:prefix 21 1465 0 0
    	 2 ('н', 14) ('р', 7)
    	 12 ('деревня', 1112) ('хутор', 249) ('фольварк', 43)
    	 10 (('building:levels',), 7) (('addr:postcode', '231288'), 7) (('addr:postcode',), 7)
    	 2976 (('building:levels',), 7) (('addr:postcode', '231288'), 7) (('addr:postcode',), 7)
    	 0
    	 0
    	 0
    	 0
    ref alt_ref 1452 396 379 16
    	 9 ('Р3', 488) ('Р1', 388) ('Р31', 230)
    	 4 ('Р96; Р122', 336) ('Р122', 48) ('Р31', 9)
    	 283 (('highway',), 1438) (('surface', 'asphalt'), 1435) (('surface',), 1435)
    	 98 (('highway',), 1438) (('surface', 'asphalt'), 1435) (('surface',), 1435)
    	 3 ('Р31', 230) ('Р122', 81) ('Р36', 68)
    	 3 ('Р122', 12) ('Р31', 3) ('Р36', 1)
    	 156 (('highway',), 376) (('surface', 'asphalt'), 373) (('surface',), 373)
    	 70 (('maxaxleload', '10'), 16) (('surface',), 16) (('maxspeed',), 16)
    brand full_name 1448 8 0 0
    	 5 ('Белоруснефть', 884) ('Беларусбанк', 532) ('БПС-Сбербанк', 26)
    	 6 ('ЦБУ №611 ОАО "АСБ Беларусбанк"', 2) ('Обменный пункт №611/5048 ОАО "АСБ Беларусбанк"', 2) ('АЗС № 3 «Белоруснефть-Гроднооблнефтепродукт»', 1)
    	 3768 (('amenity',), 1441) (('name',), 1174) (('opening_hours',), 1122)
    	 95 (('amenity',), 1441) (('name',), 1174) (('opening_hours',), 1122)
    	 0
    	 0
    	 0
    	 0
    addr:district full_name 1442 2 0 0
    	 2 ('Миорский район', 821) ('Мядельский район', 621)
    	 2 ('Миорский районный центр гигиены и эпидемиологии', 1) ('Мядельский районный отдел Государственного комитета судебных экспертиз Республики Беларусь', 1)
    	 3019 (('name',), 1440) (('addr:region',), 1440) (('int_name',), 1433)
    	 29 (('name',), 1440) (('addr:region',), 1440) (('int_name',), 1433)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber crop 1440 10 0 0
    	 4 ('н', 1370) ('ж', 49) ('П', 15)
    	 7 ('цветы;саженцы', 3) ('Продукты_из_козьего_молока;Козий_сыр;Йогурут;Козий_творог', 2) ('Смородина', 1)
    	 87 (('building',), 1440) (('building', 'yes'), 1412) (('addr:street',), 1210)
    	 23 (('building',), 1440) (('building', 'yes'), 1412) (('addr:street',), 1210)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber surface 1428 19 0 0
    	 5 ('н', 1370) ('ж', 49) ('ы', 4)
    	 8 ('земля', 5) ('Баскетбольная_площадка', 4) ('Русловое, сезонного регулирования. Состав сооружений гидроузла: плотина (длина 9,9 км, максимальная высота 5 м), ограждающие дамбы (общая длина 7,8 км, максимальная высота 3,85 м), водосброс, 4 водозабора, насосная станция. Водятся щука, лещ, густера, ук', 4)
    	 75 (('building',), 1428) (('building', 'yes'), 1404) (('addr:street',), 1202)
    	 32 (('building',), 1428) (('building', 'yes'), 1404) (('addr:street',), 1202)
    	 0
    	 0
    	 0
    	 0
    addr:housename disused:name 1422 36 0 0
    	 9 ('н', 1044) ('Н', 279) ('к', 49)
    	 15 ('Мама Чанг', 4) ('Шоколадница', 3) ('Набоков', 3)
    	 83 (('building',), 1420) (('building', 'yes'), 1383) (('addr:street',), 1069)
    	 32 (('building',), 1420) (('building', 'yes'), 1383) (('addr:street',), 1069)
    	 0
    	 0
    	 0
    	 0
    addr:housename start_date 1416 34 0 0
    	 4 ('н', 1392) ('к', 14) ('а', 6)
    	 11 ('XIX - 1-я половина XX', 6) ('1-я половина XX', 6) ('XVIII - нач. XIX', 6)
    	 58 (('building',), 1416) (('building', 'yes'), 1378) (('addr:street',), 988)
    	 86 (('building',), 1416) (('building', 'yes'), 1378) (('addr:street',), 988)
    	 0
    	 0
    	 0
    	 0
    name Нагорная 1405 183 3 11
    	 9 ('Н', 764) ('н', 554) ('Колос', 40)
    	 3 ('Я Колоса', 84) ('Наберажная', 55) ('Нагорная', 44)
    	 158 (('building',), 1363) (('building', 'yes'), 763) (('building', 'residential'), 507)
    	 37 (('building',), 1363) (('building', 'yes'), 763) (('building', 'residential'), 507)
    	 1 ('Нагорная', 3)
    	 1 ('Нагорная', 11)
    	 23 (('place',), 3) (('wikipedia:pl', 'Nahornaja (obwód brzeski)'), 2) (('wikidata', 'Q6520228'), 2)
    	 19 (('addr:street',), 11) (('addr:city', 'Акулинка'), 11) (('building',), 11)
    name memorial:subject 1392 41 0 0
    	 29 ('н', 831) ('Н', 382) ('Ленин', 37)
    	 4 ('Герой Советского Союза Серебренников Александр Георгиевич', 16) ('Система хозяйственных судов Республики Беларусь', 15) ('В. И. Ленин (Ульянов)', 5)
    	 288 (('building',), 1296) (('building', 'yes'), 959) (('building', 'residential'), 281)
    	 15 (('building',), 1296) (('building', 'yes'), 959) (('building', 'residential'), 281)
    	 0
    	 0
    	 0
    	 0
    addr:housename comment 1387 212 0 0
    	 12 ('н', 1218) ('ж', 80) ('к', 28)
    	 10 ('Кольцевая дорога, даже H по своему значению не может быть tertiary', 162) ('Учреждение создано в соответствии с приказом Министерства образования и науки Республики Беларусь от 30.09.96 г. № 419 и входит в структуру БГУ. Учредителем государственного учреждения "Республиканский институт высшей школы" является БГУ', 9) ('Вход в общежитие', 9)
    	 107 (('building',), 1386) (('building', 'yes'), 1348) (('addr:street',), 995)
    	 81 (('building',), 1386) (('building', 'yes'), 1348) (('addr:street',), 995)
    	 0
    	 0
    	 0
    	 0
    brand addr:street 108 1382 0 0
    	 9 ('МТС', 38) ('Луч', 32) ('Связной', 14)
    	 50 ('улица Семашко', 92) ('1-я Луческая улица', 71) ('улица МТС', 55)
    	 203 (('shop',), 101) (('name',), 75) (('opening_hours',), 67)
    	 476 (('shop',), 101) (('name',), 75) (('opening_hours',), 67)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber type 1380 26 0 0
    	 4 ('н', 1370) ('ы', 4) ('я', 4)
    	 7 ('Школа_танца', 14) ('Хореография', 3) ('невысокий', 2)
    	 67 (('building',), 1380) (('building', 'yes'), 1355) (('addr:street',), 1165)
    	 33 (('building',), 1380) (('building', 'yes'), 1355) (('addr:street',), 1165)
    	 0
    	 0
    	 0
    	 0
    building:levels addr:place 34 1369 0 0
    	 2 ('Н', 33) ('2А', 1)
    	 34 ('Новый Двор', 243) ('Новосёлки', 203) ('Нетечь', 187)
    	 5 (('building',), 34) (('building', 'yes'), 33) (('addr:street',), 1)
    	 421 (('building',), 34) (('building', 'yes'), 33) (('addr:street',), 1)
    	 0
    	 0
    	 0
    	 0
    name contact:facebook 1362 37 0 0
    	 24 ('н', 1108) ('К', 57) ('Минск', 42)
    	 4 ('https://www.facebook.com/pages/КУП-Минсксанавтотранс/1416766311868086', 11) ('https://www.facebook.com/Еврокэш-магазин-низких-цен-101228458341759', 10) ('https://www.facebook.com/Агроусадьба-Краина-мар-104854864651187/', 8)
    	 258 (('building',), 1270) (('building', 'yes'), 1149) (('building', 'residential'), 93)
    	 59 (('building',), 1270) (('building', 'yes'), 1149) (('building', 'residential'), 93)
    	 0
    	 0
    	 0
    	 0
    name bank 1355 14 1 1
    	 14 ('Беларусбанк', 1045) ('н', 277) ('к', 10)
    	 1 ('ОАО «АСБ Беларусбанк» Отделение №511', 14)
    	 1047 (('amenity',), 1028) (('amenity', 'bank'), 654) (('int_name',), 532)
    	 24 (('amenity',), 1028) (('amenity', 'bank'), 654) (('int_name',), 532)
    	 1 ('ОАО «АСБ Беларусбанк» Отделение №511', 1)
    	 1 ('ОАО «АСБ Беларусбанк» Отделение №511', 1)
    	 24 (('brand:wikipedia', 'en:Belarusbank'), 1) (('building:material',), 1) (('brand', 'Беларусбанк'), 1)
    	 24 (('brand:wikipedia', 'en:Belarusbank'), 1) (('building:material',), 1) (('brand', 'Беларусбанк'), 1)
    official_status addr:street 23 1347 0 0
    	 2 ('СУ', 12) ('Строитель', 11)
    	 13 ('Строительная улица', 1104) ('Строительный переулок', 70) ('1-й Строительный переулок', 41)
    	 64 (('name',), 23) (('addr:region', 'Псковская область'), 12) (('source', 'Главное государственное управление социальной защиты населения Псковской области'), 12)
    	 279 (('name',), 23) (('addr:region', 'Псковская область'), 12) (('source', 'Главное государственное управление социальной защиты населения Псковской области'), 12)
    	 0
    	 0
    	 0
    	 0
    addr:housename sport 1346 43 0 0
    	 6 ('н', 1218) ('к', 63) ('ж', 40)
    	 15 ('Йога,_танцы,_айкидо', 4) ('equestrian;лошади;конный_спорт;конюшня', 4) ('Тренажерный_зал,_фитнес', 4)
    	 65 (('building',), 1345) (('building', 'yes'), 1305) (('addr:street',), 961)
    	 63 (('building',), 1345) (('building', 'yes'), 1305) (('addr:street',), 961)
    	 0
    	 0
    	 0
    	 0
    note wikipedia 1082 1342 0 0
    	 22 ('Я', 533) ('Мінск', 201) ('лес', 181)
    	 1060 ('be:Праспект Дзяржынскага (Мінск)', 101) ('be:Яршоўка', 10) ('be:Вуліца Карла Маркса, Мінск', 7)
    	 71 (('building',), 553) (('addr:street',), 547) (('addr:housenumber',), 547)
    	 3671 (('building',), 553) (('addr:street',), 547) (('addr:housenumber',), 547)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr:suburb 1335 679 0 0
    	 8 ('н', 1218) ('к', 63) ('м', 21)
    	 9 ('Октябрьский микрорайон', 200) ('микрорайон Полесье', 116) ('Первомайский микрорайон', 116)
    	 61 (('building',), 1335) (('building', 'yes'), 1300) (('addr:street',), 958)
    	 240 (('building',), 1335) (('building', 'yes'), 1300) (('addr:street',), 958)
    	 0
    	 0
    	 0
    	 0
    note official_name 580 1329 0 0
    	 20 ('Я', 370) ('лес', 105) ('Поле', 24)
    	 547 ('Сосновый Бор - Полесье', 24) ('Коневцы - Ялуцевичи - Мочулино', 20) ('Ивенец - Сивица - Яцково - Белокорец', 18)
    	 62 (('building',), 407) (('addr:street',), 389) (('addr:housenumber',), 389)
    	 1558 (('building',), 407) (('addr:street',), 389) (('addr:housenumber',), 389)
    	 0
    	 0
    	 0
    	 0
    fence_type wikipedia 1274 1319 0 0
    	 3 ('да', 1192) ('Забор', 80) ('камень', 2)
    	 1234 ('be:Чарніца (прыток Будавесці)', 10) ('be:Градаўка', 8) ('be:Вёска Града, Багушэўскі сельсавет', 3)
    	 6 (('barrier',), 1274) (('barrier', 'fence'), 1274) (('material',), 80)
    	 4050 (('barrier',), 1274) (('barrier', 'fence'), 1274) (('material',), 80)
    	 0
    	 0
    	 0
    	 0
    fee operator 63 1307 6 1121
    	 6 ('Беларусбанк', 48) ('Белгазпромбанк', 5) ('Приорбанк', 4)
    	 38 ('Беларусбанк', 770) ('Приорбанк', 276) ('Белгазпромбанк', 69)
    	 14 (('amenity', 'atm'), 63) (('amenity',), 63) (('int_name',), 29)
    	 1276 (('amenity', 'atm'), 63) (('amenity',), 63) (('int_name',), 29)
    	 5 ('Беларусбанк', 2) ('Приорбанк', 1) ('БелСвиссБанк', 1)
    	 5 ('Беларусбанк', 770) ('Приорбанк', 276) ('Белгазпромбанк', 69)
    	 14 (('amenity', 'atm'), 6) (('amenity',), 6) (('int_name',), 3)
    	 949 (('amenity',), 1114) (('amenity', 'atm'), 755) (('opening_hours',), 576)
    addr:city destination:lanes:forward 1304 6 0 0
    	 4 ('Нарочь', 1133) ('Вилейка', 79) ('Воложин', 70)
    	 2 ('Воложин;Сморгонь|Воложин;Сморгонь|Вилейка;Нарочь', 4) ('Воложин|Сморгонь', 2)
    	 554 (('addr:street',), 1285) (('building',), 1281) (('addr:housenumber',), 1264)
    	 32 (('addr:street',), 1285) (('building',), 1281) (('addr:housenumber',), 1264)
    	 0
    	 0
    	 0
    	 0
    addr:housename was:name:prefix 1293 1128 0 0
    	 5 ('н', 1218) ('к', 49) ('м', 15)
    	 15 ('деревня', 556) ('хутор', 249) ('фольварк', 86)
    	 58 (('building',), 1293) (('building', 'yes'), 1259) (('addr:street',), 917)
    	 3205 (('building',), 1293) (('building', 'yes'), 1259) (('addr:street',), 917)
    	 0
    	 0
    	 0
    	 0
    building destination:forward 1288 282 0 0
    	 7 ('Н', 966) ('н', 134) ('М', 58)
    	 85 ('Мiнск', 32) ('12-ы кіламетр МКАД;Слуцк;Гродна;Брэст', 15) ('Барановичи', 10)
    	 22 (('name',), 306) (('name', 'Н'), 198) (('name', 'М'), 58)
    	 252 (('name',), 306) (('name', 'Н'), 198) (('name', 'М'), 58)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber wikipedia:be-tarask 1284 11 0 0
    	 7 ('н', 1096) ('Н', 120) ('ж', 49)
    	 5 ('Несьцяры', 3) ('Межава (Аршанскі раён)', 3) ('Паўлінава (Баранавіцкі раён)', 2)
    	 150 (('building',), 1283) (('building', 'yes'), 1255) (('addr:street',), 1082)
    	 62 (('building',), 1283) (('building', 'yes'), 1255) (('addr:street',), 1082)
    	 0
    	 0
    	 0
    	 0
    network official_name 1277 1063 0 0
    	 16 ('Барановичское отделение', 496) ('Минск', 250) ('УЗ', 237)
    	 267 ('Борисов — Вилейка — Ошмяны', 232) ('Минск — Калачи — Мядель', 98) ('Минск — Гродно — Брузги', 97)
    	 225 (('name',), 1212) (('operator',), 1075) (('railway',), 783)
    	 1392 (('name',), 1212) (('operator',), 1075) (('railway',), 783)
    	 0
    	 0
    	 0
    	 0
    cycleway:left wikipedia 1192 1274 0 0
    	 1 ('да', 1192)
    	 1192 ('be:Чарніца (прыток Будавесці)', 10) ('be:Градаўка', 8) ('be:Вёска Града, Багушэўскі сельсавет', 3)
    	 6 (('int_name',), 1192) (('name', 'улица 1 Мая'), 1192) (('name',), 1192)
    	 3970 (('int_name',), 1192) (('name', 'улица 1 Мая'), 1192) (('name',), 1192)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber BY_PT:note 446 1260 0 0
    	 5 ('н', 274) ('Н', 120) ('ж', 49)
    	 1 ('Тэги типа "BY_PT..." - временные, для внесения ОТ Беларуси! Не удаляйте их - они будут удалены позже.', 1260)
    	 131 (('building',), 445) (('building', 'yes'), 437) (('addr:street',), 377)
    	 166 (('building',), 445) (('building', 'yes'), 437) (('addr:street',), 377)
    	 0
    	 0
    	 0
    	 0
    boundary_name addr:district 2 1249 1 717
    	 2 ('Орша', 1) ('Витебский район', 1)
    	 2 ('Витебский район', 717) ('Оршанский район', 532)
    	 5 (('historic',), 2) (('historic', 'boundary_stone'), 2) (('name',), 2)
    	 2713 (('historic',), 2) (('historic', 'boundary_stone'), 2) (('name',), 2)
    	 1 ('Витебский район', 1)
    	 1 ('Витебский район', 717)
    	 4 (('historic',), 1) (('name', 'Витебский район'), 1) (('historic', 'boundary_stone'), 1)
    	 1586 (('name',), 717) (('addr:region', 'Витебская область'), 715) (('addr:region',), 715)
    addr:housenumber addr:postcode 1248 98 2 1
    	 7 ('н', 1096) ('Н', 120) ('П', 15)
    	 7 ('Жлобин', 88) ('<различные>', 4) ('Почтовое отделение №32', 2)
    	 143 (('building',), 1247) (('building', 'yes'), 1219) (('addr:street',), 1055)
    	 79 (('building',), 1247) (('building', 'yes'), 1219) (('addr:street',), 1055)
    	 1 ('сарай', 2)
    	 1 ('сарай', 1)
    	 6 (('addr:street',), 2) (('addr:street', 'проспект Октября'), 2) (('building', 'yes'), 2)
    	 2 (('building', 'yes'), 1) (('building',), 1)
    destination:forward addr:street 55 1248 0 0
    	 2 ('Гомель', 50) ('Барановичи', 5)
    	 11 ('Гомельская улица', 923) ('Гомельское шоссе', 142) ('Гомельский переулок', 59)
    	 45 (('highway',), 55) (('highway', 'trunk_link'), 50) (('destination:backward',), 50)
    	 409 (('highway',), 55) (('highway', 'trunk_link'), 50) (('destination:backward',), 50)
    	 0
    	 0
    	 0
    	 0
    description brand:wikipedia 1247 433 0 0
    	 5 ('н', 1219) ('магазин', 16) ('ж', 10)
    	 24 ('ru:Fix Price (сеть магазинов)', 132) ('be:Белаграпрамбанк', 73) ('ru:Белоруснефть', 55)
    	 27 (('building',), 1246) (('building', 'yes'), 1242) (('addr:street',), 1191)
    	 1053 (('building',), 1246) (('building', 'yes'), 1242) (('addr:street',), 1191)
    	 0
    	 0
    	 0
    	 0
    description was:name 1241 37 4 2
    	 9 ('н', 1219) ('ж', 6) ('магазин', 4)
    	 27 ('Неман-Лада', 4) ('Наш магазин', 3) ('Белоруснефть, АЗС №37', 2)
    	 85 (('building',), 1233) (('building', 'yes'), 1232) (('addr:street',), 1185)
    	 204 (('building',), 1233) (('building', 'yes'), 1232) (('addr:street',), 1185)
    	 2 ('Детская одежда', 3) ('Рублёвский', 1)
    	 2 ('Детская одежда', 1) ('Рублёвский', 1)
    	 45 (('name',), 4) (('shop',), 3) (('shop', 'clothes'), 3)
    	 36 (('was:shop',), 1) (('was:shop', 'clothes'), 1) (('clothes', 'children'), 1)
    name image 1234 43 0 0
    	 27 ('н', 831) ('ДОТ', 149) ('Т', 50)
    	 5 ('https://upload.wikimedia.org/wikipedia/commons/e/ee/Пограничный_отряд_Брест_имени_Кижеватова_01.jpg', 12) ('https://upload.wikimedia.org/wikipedia/commons/5/56/Брест%2C_ДОТ_у_моста_над_Бугом_04.jpg', 11) ('https://ru.wikipedia.org/wiki/Белорусский_государственный_аграрный_технический_университет#/media/File:Логотип_БГАТУ.jpg', 11)
    	 258 (('building',), 1068) (('building', 'yes'), 914) (('historic',), 108)
    	 66 (('building',), 1068) (('building', 'yes'), 914) (('historic',), 108)
    	 0
    	 0
    	 0
    	 0
    ref ref:2 1234 6 1230 3
    	 2 ('М5', 1230) ('М', 4)
    	 1 ('М5', 6)
    	 145 (('surface',), 1229) (('surface', 'asphalt'), 1229) (('oneway', 'yes'), 1228)
    	 23 (('surface',), 1229) (('surface', 'asphalt'), 1229) (('oneway', 'yes'), 1228)
    	 1 ('М5', 1230)
    	 1 ('М5', 3)
    	 141 (('surface',), 1229) (('surface', 'asphalt'), 1229) (('oneway', 'yes'), 1228)
    	 23 (('surface',), 3) (('oneway', 'yes'), 3) (('ref:1',), 3)
    ref addr:зд 1234 2 0 0
    	 2 ('М5', 1230) ('М', 4)
    	 1 ('131-й км трассы М5', 2)
    	 145 (('surface',), 1229) (('surface', 'asphalt'), 1229) (('oneway', 'yes'), 1228)
    	 50 (('surface',), 1229) (('surface', 'asphalt'), 1229) (('oneway', 'yes'), 1228)
    	 0
    	 0
    	 0
    	 0
    addr:housename was:operator 1234 33 0 0
    	 12 ('н', 870) ('Н', 279) ('к', 35)
    	 11 ('Группа компаний «А-100»', 5) ('Гроднотеамонтаж', 5) ('ТПУП "Металлургторг"', 4)
    	 91 (('building',), 1231) (('building', 'yes'), 1202) (('addr:street',), 934)
    	 123 (('building',), 1231) (('building', 'yes'), 1202) (('addr:street',), 934)
    	 0
    	 0
    	 0
    	 0
    addr:housename name_3 1233 20 0 0
    	 9 ('н', 870) ('Н', 279) ('ж', 40)
    	 5 ('магазин детской одежды', 7) ('Банька У Нарвы', 4) ('Пошив и ремонт одежды', 4)
    	 114 (('building',), 1230) (('building', 'yes'), 1203) (('addr:street',), 933)
    	 68 (('building',), 1230) (('building', 'yes'), 1203) (('addr:street',), 933)
    	 0
    	 0
    	 0
    	 0
    official_short_type substation 1230 3 410 1
    	 1 ('ТП', 1230)
    	 3 ('ТП', 1) ('ТП-131', 1) ('ТП-513', 1)
    	 516 (('power',), 1197) (('power', 'substation'), 1197) (('ref',), 1158)
    	 15 (('power',), 1197) (('power', 'substation'), 1197) (('ref',), 1158)
    	 1 ('ТП', 410)
    	 1 ('ТП', 1)
    	 516 (('power',), 399) (('power', 'substation'), 399) (('ref',), 386)
    	 8 (('name', 'ТП'), 1) (('addr:street',), 1) (('building', 'yes'), 1)
    name was:addr:street 1216 66 820 12
    	 15 ('улица Мира', 530) ('улица Дзержинского', 284) ('н', 277)
    	 3 ('улица Девятовка', 45) ('улица Дзержинского', 16) ('улица Мира', 5)
    	 541 (('highway',), 806) (('int_name',), 724) (('highway', 'residential'), 472)
    	 42 (('highway',), 806) (('int_name',), 724) (('highway', 'residential'), 472)
    	 3 ('улица Мира', 530) ('улица Дзержинского', 284) ('улица Девятовка', 6)
    	 3 ('улица Девятовка', 9) ('улица Дзержинского', 2) ('улица Мира', 1)
    	 326 (('highway',), 800) (('int_name',), 710) (('highway', 'residential'), 472)
    	 42 (('was:addr:housenumber',), 12) (('was:building',), 11) (('building:levels',), 8)
    addr:street addr:street_1 1200 78 1048 45
    	 26 ('Кобринская улица', 315) ('Двинская улица', 189) ('Черниговская улица', 93)
    	 22 ('2-й Брестский переулок', 12) ('1-й Брестский переулок', 10) ('3-й Брестский переулок', 10)
    	 434 (('addr:housenumber',), 1183) (('building',), 1164) (('building', 'yes'), 783)
    	 94 (('addr:housenumber',), 1183) (('building',), 1164) (('building', 'yes'), 783)
    	 21 ('Кобринская улица', 315) ('Двинская улица', 189) ('Черниговская улица', 93)
    	 21 ('2-й Брестский переулок', 6) ('1-й Брестский переулок', 5) ('3-й Брестский переулок', 5)
    	 419 (('addr:housenumber',), 1035) (('building',), 1016) (('building', 'yes'), 667)
    	 93 (('building',), 45) (('addr:street',), 45) (('addr:housenumber',), 45)
    official_short_type official_short_name 1200 38 728 22
    	 6 ('ТП', 820) ('ЗТП', 224) ('РП', 62)
    	 5 ('ЗТП', 22) ('ГРП', 6) ('ШРП', 4)
    	 853 (('ref',), 1107) (('power',), 1059) (('power', 'substation'), 1059)
    	 39 (('ref',), 1107) (('power',), 1059) (('power', 'substation'), 1059)
    	 5 ('ТП', 410) ('ЗТП', 224) ('ГРП', 44)
    	 5 ('ЗТП', 11) ('ТП', 3) ('КНС', 3)
    	 824 (('ref',), 661) (('building',), 650) (('building', 'service'), 613)
    	 39 (('building',), 22) (('building', 'service'), 22) (('ref',), 17)
    name addr:province 1199 198 12 13
    	 21 ('н', 831) ('Минск', 84) ('к', 80)
    	 8 ('Брянская', 96) ('Минская', 24) ('Витебская', 21)
    	 327 (('building',), 1039) (('building', 'yes'), 924) (('building', 'residential'), 84)
    	 96 (('building',), 1039) (('building', 'yes'), 924) (('building', 'residential'), 84)
    	 6 ('Минская область', 3) ('Витебская область', 2) ('Брестская область', 2)
    	 6 ('Минская', 4) ('Витебская', 3) ('Витебская область', 2)
    	 83 (('int_name',), 7) (('wikidata',), 7) (('wikipedia',), 7)
    	 67 (('addr:district',), 12) (('building',), 11) (('addr:housenumber',), 10)
    official_short_type designation 1199 7 1 1
    	 6 ('ТП', 820) ('ПС', 364) ('БКТП', 8)
    	 5 ('БКТП - 2980', 3) ('ТП320кВА', 1) ('БПС-Сбербанк', 1)
    	 1107 (('power',), 1174) (('power', 'substation'), 1171) (('voltage',), 1061)
    	 19 (('power',), 1174) (('power', 'substation'), 1171) (('voltage',), 1061)
    	 1 ('АТС', 1)
    	 1 ('АТС', 1)
    	 10 (('telecom', 'exchange'), 1) (('addr:street',), 1) (('addr:street', 'улица Гастелло'), 1)
    	 2 (('amenity',), 1) (('amenity', 'telephone'), 1)
    official_short_type owner 1188 11 0 0
    	 2 ('ПС', 1092) ('Ф', 96)
    	 6 ('ОАО «БПС-Сбербанк»', 6) ('ООО «БПС-Банк»', 1) ('БПС-Сбербанк', 1)
    	 607 (('power',), 1185) (('voltage',), 1176) (('power', 'substation'), 1089)
    	 74 (('power',), 1185) (('voltage',), 1176) (('power', 'substation'), 1089)
    	 0
    	 0
    	 0
    	 0
    description architect 1175 34 0 0
    	 3 ('н', 1166) ('ж', 6) ('Н', 3)
    	 24 ('А. Ю. Заболотная', 3) ('Рубаненко Борис Рафаилович', 3) ('Б.Р.Рубаленко', 2)
    	 8 (('building',), 1175) (('building', 'yes'), 1175) (('addr:street',), 1131)
    	 197 (('building',), 1175) (('building', 'yes'), 1175) (('addr:street',), 1131)
    	 0
    	 0
    	 0
    	 0
    operator was:name:prefix 13 1173 0 0
    	 3 ('е', 7) ('я', 5) ('б', 1)
    	 9 ('деревня', 1112) ('имение', 34) ('застенок', 13)
    	 9 (('name',), 8) (('name', 'Складской комплекс «Северный»'), 7) (('landuse',), 7)
    	 2000 (('name',), 8) (('name', 'Складской комплекс «Северный»'), 7) (('landuse',), 7)
    	 0
    	 0
    	 0
    	 0
    building owner 1165 366 0 0
    	 8 ('Н', 966) ('н', 102) ('р', 42)
    	 62 ('ОАО «Белорусский банк развития и реконструкции «Белинвестбанк»', 94) ('ОАО «АСБ Беларусбанк»', 60) ('ОАО «Приорбанк»', 26)
    	 26 (('name',), 236) (('name', 'Н'), 198) (('building:levels',), 49)
    	 598 (('name',), 236) (('name', 'Н'), 198) (('building:levels',), 49)
    	 0
    	 0
    	 0
    	 0
    building office 1159 37 0 0
    	 5 ('Н', 1127) ('н', 16) ('р', 6)
    	 13 ('Копыль-Слобода Кучинка-Песочное', 8) ('Подъез от а/д Н8569 к д. Мысли', 6) ('Подъезд от а/д Н8572 к мемориальному комплексу "Мосевичи"', 4)
    	 17 (('name',), 246) (('name', 'Н'), 231) (('building:levels',), 13)
    	 56 (('name',), 246) (('name', 'Н'), 231) (('building:levels',), 13)
    	 0
    	 0
    	 0
    	 0
    addr:housename was:official_name 1151 69 0 0
    	 9 ('н', 1044) ('к', 56) ('ж', 20)
    	 10 ('Каменка - Першино - Полишино', 30) ('Красулино - Юрково - Поташи', 10) ('Подъезд к д. Ажугеры от а/д Рымдюны - Солы', 7)
    	 65 (('building',), 1149) (('building', 'yes'), 1116) (('addr:street',), 826)
    	 30 (('building',), 1149) (('building', 'yes'), 1116) (('addr:street',), 826)
    	 0
    	 0
    	 0
    	 0
    addr:housename destination:lanes:backward 1135 16 0 0
    	 7 ('Н', 558) ('н', 522) ('к', 21)
    	 3 ('Сморгонь;Минск;Вилейка;Нарочь|Минск;Вилейка;Нарочь', 6) ('Минск;Вилейка;Нарочь|Минск', 5) ('Воложин;Сморгонь|Минск', 5)
    	 83 (('building',), 1131) (('building', 'yes'), 1111) (('addr:street',), 915)
    	 41 (('building',), 1131) (('building', 'yes'), 1111) (('addr:street',), 915)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber contact:facebook 1134 8 0 0
    	 5 ('н', 1096) ('магазин', 20) ('П', 15)
    	 4 ('https://www.facebook.com/pages/КУП-Минсксанавтотранс/1416766311868086', 3) ('https://www.facebook.com/Еврокэш-магазин-низких-цен-101228458341759', 2) ('https://www.facebook.com/people/Конны-Фальварак-Скрабатуны/100043166704824', 2)
    	 99 (('building',), 1134) (('building', 'yes'), 1106) (('addr:street',), 958)
    	 59 (('building',), 1134) (('building', 'yes'), 1106) (('addr:street',), 958)
    	 0
    	 0
    	 0
    	 0
    operator branch 1132 171 46 25
    	 22 ('Беларусбанк', 770) ('Брестэнерго', 110) ('Гродноэнерго', 85)
    	 80 ('РУП "Минскэнерго"', 45) ('Барановичские электросети', 6) ('РУП "Брестэнерго"', 6)
    	 1184 (('amenity',), 792) (('name',), 709) (('amenity', 'atm'), 537)
    	 432 (('amenity',), 792) (('name',), 709) (('amenity', 'atm'), 537)
    	 8 ('РУП "Гродноэнерго"', 20) ('РУП "Минскэнерго"', 9) ('Південно-Західна залізниця', 7)
    	 8 ('РУП "Минскэнерго"', 15) ('БГПЗ', 2) ('РУП "Брестэнерго"', 2)
    	 243 (('name',), 37) (('power',), 24) (('voltage',), 15)
    	 121 (('operator',), 22) (('substation',), 18) (('official_short_type',), 18)
    name fuel:discount 1125 35 0 0
    	 10 ('Н', 764) ('н', 277) ('М', 52)
    	 3 ('Заправляйся выгодно!', 25) ('"РАЗАМ З НАМІ"', 5) ('"РАЗАМ З НАМI"', 5)
    	 71 (('building',), 1096) (('building', 'yes'), 514) (('building', 'residential'), 492)
    	 119 (('building',), 1096) (('building', 'yes'), 514) (('building', 'residential'), 492)
    	 0
    	 0
    	 0
    	 0
    operator was:operator 1118 16 1083 4
    	 11 ('Евроторг', 1024) ('Группа компаний «А-100»', 56) ('ЖКХ', 17)
    	 8 ('Гродненская Овощная Фабрика', 4) ('Группа компаний «А-100»', 3) ('ТПУП "Металлургторг"', 3)
    	 1063 (('name',), 1095) (('opening_hours',), 1075) (('contact:website',), 1035)
    	 80 (('name',), 1095) (('opening_hours',), 1075) (('contact:website',), 1035)
    	 4 ('Евроторг', 1024) ('Группа компаний «А-100»', 56) ('ТПУП "Металлургторг"', 2)
    	 4 ('Группа компаний «А-100»', 1) ('Евроторг', 1) ('ТПУП "Металлургторг"', 1)
    	 973 (('name',), 1082) (('opening_hours',), 1074) (('contact:website',), 1035)
    	 44 (('contact:website',), 2) (('contact:email',), 2) (('was:name',), 2)
    name wikimedia_commons 1116 27 0 0
    	 23 ('н', 554) ('Н', 382) ('Бобр', 35)
    	 2 ('File:Кафедральный собор Николая Чудотворца, Бобруйск.jpg', 14) ('[[File:Драмтеатр им. В.И. Дунина-Мартинкевича.jpg|thumb|]]', 13)
    	 228 (('building',), 1029) (('building', 'yes'), 697) (('building', 'residential'), 278)
    	 20 (('building',), 1029) (('building', 'yes'), 697) (('building', 'residential'), 278)
    	 0
    	 0
    	 0
    	 0
    description website 1116 31 0 0
    	 5 ('н', 1060) ('кн', 46) ('Баня', 4)
    	 22 ('http://чайхана.бел', 3) ('http://островецкое.бел', 3) ('Баня-Минск.бел', 2)
    	 30 (('building',), 1116) (('building', 'yes'), 1115) (('addr:street',), 1068)
    	 172 (('building',), 1116) (('building', 'yes'), 1115) (('addr:street',), 1068)
    	 0
    	 0
    	 0
    	 0
    from note 1115 225 2 2
    	 45 ('Гомель', 720) ('Вокзал', 176) ('Минск', 48)
    	 130 ('Внешняя нода для согласования с картой Минска', 45) ('административная граница г. Минска', 28) ('Решение Минский облсовет 226 08.09.2017 О некоторых вопросах административно-территориального устройства Минской области', 12)
    	 450 (('to',), 1115) (('route',), 1115) (('type',), 1115)
    	 351 (('to',), 1115) (('route',), 1115) (('type',), 1115)
    	 2 ('пос. Ипуть', 1) ('Новая Жизнь', 1)
    	 2 ('пос. Ипуть', 1) ('Новая Жизнь', 1)
    	 20 (('to',), 2) (('type',), 2) (('public_transport:version', '2'), 2)
    	 13 (('type',), 2) (('public_transport:version', '2'), 2) (('type', 'public_transport'), 2)
    addr:housenumber destination:lanes:backward 1114 9 0 0
    	 4 ('н', 822) ('Н', 240) ('ж', 49)
    	 3 ('Сморгонь;Минск;Вилейка;Нарочь|Минск;Вилейка;Нарочь', 3) ('Минск;Вилейка;Нарочь|Минск', 3) ('Воложин;Сморгонь|Минск', 3)
    	 125 (('building',), 1112) (('building', 'yes'), 1094) (('addr:street',), 944)
    	 41 (('building',), 1112) (('building', 'yes'), 1094) (('addr:street',), 944)
    	 0
    	 0
    	 0
    	 0
    name information 1097 22 0 0
    	 17 ('н', 554) ('кладбище', 436) ('м', 26)
    	 2 ('Партизанское кладбище бригад "Штурмовая" и "Дяди Коли" (захоронено более 100 человек)', 15) ('Внимание! Ловля рыбы осуществляется платно', 7)
    	 104 (('building',), 648) (('building', 'yes'), 597) (('landuse', 'cemetery'), 435)
    	 8 (('building',), 648) (('building', 'yes'), 597) (('landuse', 'cemetery'), 435)
    	 0
    	 0
    	 0
    	 0
    name addr:hint 1096 32 0 0
    	 15 ('н', 554) ('Н', 382) ('Автовокзал', 44)
    	 2 ('Напротив магазина «Алми»', 22) ('привокзальная площадь Автовокзала', 10)
    	 187 (('building',), 1016) (('building', 'yes'), 695) (('building', 'residential'), 264)
    	 28 (('building',), 1016) (('building', 'yes'), 695) (('building', 'residential'), 264)
    	 0
    	 0
    	 0
    	 0
    name destination:lanes:forward 1096 22 0 0
    	 14 ('н', 554) ('Н', 382) ('Вилейка', 41)
    	 2 ('Воложин;Сморгонь|Воложин;Сморгонь|Вилейка;Нарочь', 14) ('Воложин|Сморгонь', 8)
    	 267 (('building',), 1015) (('building', 'yes'), 686) (('building', 'residential'), 278)
    	 32 (('building',), 1015) (('building', 'yes'), 686) (('building', 'residential'), 278)
    	 0
    	 0
    	 0
    	 0
    operator fixme 454 1092 0 0
    	 12 ('е', 257) ('я', 85) ('б', 72)
    	 271 ('адрес', 211) ('проверить', 49) ('положение', 39)
    	 88 (('name',), 345) (('landuse',), 259) (('name', 'Складской комплекс «Северный»'), 257)
    	 1674 (('name',), 345) (('landuse',), 259) (('name', 'Складской комплекс «Северный»'), 257)
    	 0
    	 0
    	 0
    	 0
    substation ref 999 1091 1 27
    	 1 ('ТП', 999)
    	 999 ('ТП', 27) ('ЦТП', 8) ('КТП', 4)
    	 8 (('name', 'ТП'), 999) (('addr:street',), 999) (('building', 'yes'), 999)
    	 434 (('name', 'ТП'), 999) (('addr:street',), 999) (('building', 'yes'), 999)
    	 1 ('ТП', 1)
    	 1 ('ТП', 27)
    	 8 (('name', 'ТП'), 1) (('addr:street',), 1) (('building', 'yes'), 1)
    	 41 (('power',), 27) (('building',), 27) (('power', 'substation'), 27)
    name beauty 1084 24 0 0
    	 15 ('н', 554) ('Н', 382) ('ж', 30)
    	 2 ('Наращивание_ресниц;Моделирование_бровей;Перманентный_макияж;Макияж;Обучение_мастеров;eyebrow;eyelash', 14) ('eyelash;eyebrow;lips;перманеннтный_макияж;татуаж;микропигментирование;удаление_перманента;перманентный_макияж_бровей;перманентный_макияж_губ;перманентный_макияж_век;permanent_make-up', 10)
    	 84 (('building',), 1068) (('building', 'yes'), 730) (('building', 'residential'), 286)
    	 63 (('building',), 1068) (('building', 'yes'), 730) (('building', 'residential'), 286)
    	 0
    	 0
    	 0
    	 0
    addr:city related_law 1075 50 0 0
    	 7 ('Витебск', 485) ('Совет', 297) ('Городок', 184)
    	 36 ('Постановление Совета Министров РБ от 27.12.2007 № 1833', 5) ('Постановление Совета Министров РБ 27.12.2007 № 1833', 5) ('Постановление Совета Министров РБ от 04.02.2015 № 71', 4)
    	 766 (('addr:housenumber',), 1023) (('building',), 717) (('addr:street',), 657)
    	 199 (('addr:housenumber',), 1023) (('building',), 717) (('addr:street',), 657)
    	 0
    	 0
    	 0
    	 0
    description destination:street 1074 56 0 0
    	 4 ('н', 1060) ('ж', 12) ('стр', 1)
    	 21 ('праспект Незалежнасці', 18) ('праспект Пераможцаў', 8) ('Даўгінаўскі тракт', 3)
    	 8 (('building',), 1074) (('building', 'yes'), 1074) (('addr:street',), 1033)
    	 69 (('building',), 1074) (('building', 'yes'), 1074) (('addr:street',), 1033)
    	 0
    	 0
    	 0
    	 0
    name historic 1069 36 0 0
    	 15 ('н', 831) ('М', 104) ('м', 39)
    	 6 ('Месца_касцёла_Святой_Сафіі_і_кляштара_дамініканцаў', 9) ('господский_двор_Ратинцы', 7) ('ерей Анатолий Ибрагимов', 7)
    	 82 (('building',), 1023) (('building', 'yes'), 919) (('building', 'residential'), 79)
    	 33 (('building',), 1023) (('building', 'yes'), 919) (('building', 'residential'), 79)
    	 0
    	 0
    	 0
    	 0
    name service 1067 32 1 1
    	 21 ('н', 831) ('ГРП', 93) ('п', 51)
    	 5 ('Подъезд к тракторному гаражу', 11) ('Пинский проезд', 8) ('пер.Звездный', 6)
    	 167 (('building',), 1042) (('building', 'yes'), 943) (('building:levels',), 101)
    	 14 (('building',), 1042) (('building', 'yes'), 943) (('building:levels',), 101)
    	 1 ('Пинский проезд', 1)
    	 1 ('Пинский проезд', 1)
    	 4 (('highway',), 1) (('highway', 'service'), 1) (('int_name', 'Pinski prajezd'), 1)
    	 6 (('int_name',), 1) (('name',), 1) (('highway', 'residential'), 1)
    name historic:name 1061 14 0 0
    	 11 ('н', 554) ('Н', 382) ('Дом', 50)
    	 2 ('Народный Дом', 8) ('Жандармские казармы', 6)
    	 118 (('building',), 1035) (('building', 'yes'), 668) (('building', 'residential'), 279)
    	 39 (('building',), 1035) (('building', 'yes'), 668) (('building', 'residential'), 279)
    	 0
    	 0
    	 0
    	 0
    addr:housenumber name_old 1057 11 0 0
    	 5 ('н', 822) ('Н', 120) ('ж', 98)
    	 3 ('Набережная улица', 4) ('Школьная улица', 4) ('Пожарное депо', 3)
    	 148 (('building',), 1056) (('building', 'yes'), 1031) (('addr:street',), 887)
    	 17 (('building',), 1056) (('building', 'yes'), 1031) (('addr:street',), 887)
    	 0
    	 0
    	 0
    	 0
    water_tank:city addr:street 11 1054 0 0
    	 1 ('Могилёв', 11)
    	 11 ('Могилёвская улица', 876) ('3-й Могилёвский переулок', 47) ('Могилёвский переулок', 42)
    	 18 (('water_tank:street', 'улица 30 лет Победы'), 11) (('name',), 11) (('fire_operator',), 11)
    	 793 (('water_tank:street', 'улица 30 лет Победы'), 11) (('name',), 11) (('fire_operator',), 11)
    	 0
    	 0
    	 0
    	 0
    building addr:full 1049 180 0 0
    	 8 ('Н', 805) ('н', 80) ('дн', 56)
    	 49 ('д. Рудишки, Ошмянский район, Гродненская область', 24) ('д. Яново, Борисовский район, Минская область', 18) ('1-й км юго-западнее деревни Б.Тростенец', 8)
    	 39 (('name',), 237) (('name', 'Н'), 165) (('addr:street',), 63)
    	 359 (('name',), 237) (('name', 'Н'), 165) (('addr:street',), 63)
    	 0
    	 0
    	 0
    	 0
    name source:name 1048 111 0 0
    	 17 ('н', 554) ('Н', 382) ('п', 34)
    	 3 ('ГУП "Национальное кадастровое агентство"', 99) ('Табличка на заборе с западного въезда', 9) ('площадь асфальта', 3)
    	 64 (('building',), 1033) (('building', 'yes'), 695) (('building', 'residential'), 284)
    	 24 (('building',), 1033) (('building', 'yes'), 695) (('building', 'residential'), 284)
    	 0
    	 0
    	 0
    	 0
    brand owner 1044 164 292 2
    	 15 ('Беларусбанк', 798) ('Белагропромбанк', 81) ('БПС-Сбербанк', 52)
    	 17 ('ОАО «АСБ Беларусбанк»', 60) ('ОАО «Белорусский банк развития и реконструкции «Белинвестбанк»', 47) ('ОАО «Приорбанк»', 13)
    	 954 (('amenity',), 1035) (('name',), 936) (('amenity', 'bank'), 885)
    	 318 (('amenity',), 1035) (('name',), 936) (('amenity', 'bank'), 885)
    	 2 ('Беларусбанк', 266) ('БПС-Сбербанк', 26)
    	 2 ('Беларусбанк', 1) ('БПС-Сбербанк', 1)
    	 532 (('amenity',), 290) (('name',), 261) (('amenity', 'bank'), 247)
    	 14 (('amenity', 'bureau_de_change'), 1) (('amenity',), 1) (('name', 'Беларусбанк'), 1)
    name architect:wikipedia 1040 56 0 0
    	 21 ('н', 831) ('Бор', 76) ('к', 30)
    	 4 ('ru:Рубаненко, Борис Рафаилович', 27) ('be:Уладзімір_Мікітавіч_Еўдакімаў', 12) ('ru:Воинов, Александр Петрович', 11)
    	 188 (('building',), 929) (('building', 'yes'), 855) (('place',), 77)
    	 86 (('building',), 929) (('building', 'yes'), 855) (('place',), 77)
    	 0
    	 0
    	 0
    	 0
    to note 1038 223 2 2
    	 45 ('Гомель', 680) ('Вокзал', 168) ('Минск', 16)
    	 128 ('Внешняя нода для согласования с картой Минска', 45) ('административная граница г. Минска', 28) ('Решение Минский облсовет 226 08.09.2017 О некоторых вопросах административно-территориального устройства Минской области', 12)
    	 431 (('route',), 1038) (('type',), 1038) (('from',), 1038)
    	 339 (('route',), 1038) (('type',), 1038) (('from',), 1038)
    	 2 ('пос. Ипуть', 1) ('Новая Жизнь', 1)
    	 2 ('пос. Ипуть', 1) ('Новая Жизнь', 1)
    	 22 (('type',), 2) (('from', 'Вокзал'), 2) (('public_transport:version', '2'), 2)
    	 13 (('type',), 2) (('public_transport:version', '2'), 2) (('type', 'public_transport'), 2)
    addr:housenumber denomination 1034 16 0 0
    	 7 ('н', 822) ('Н', 120) ('П', 60)
    	 7 ('Православый приход свт. Николая Чудотворца', 4) ('Пятидесятники (ХВЕ)', 3) ('ТП-262', 2)
    	 165 (('building',), 1027) (('building', 'yes'), 973) (('addr:street',), 870)
    	 44 (('building',), 1027) (('building', 'yes'), 973) (('addr:street',), 870)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr:unit 1033 22 2 2
    	 6 ('н', 696) ('Н', 279) ('к', 49)
    	 16 ('5А', 2) ('Зал Г, ряд 10 павильон Г-250', 2) ('Зал В, ряд 2 павильон В-40', 2)
    	 88 (('building',), 1028) (('building', 'yes'), 1003) (('addr:street',), 793)
    	 88 (('building',), 1028) (('building', 'yes'), 1003) (('addr:street',), 793)
    	 2 ('А', 1) ('5А', 1)
    	 2 ('А', 1) ('5А', 1)
    	 12 (('addr:street',), 1) (('addr:housenumber', '12'), 1) (('name',), 1)
    	 9 (('building',), 2) (('addr:street',), 1) (('addr:housenumber', '80'), 1)
    addr:housename wikipedia:be-tarask 1031 19 0 0
    	 8 ('н', 696) ('Н', 279) ('к', 28)
    	 5 ('Межава (Аршанскі раён)', 6) ('Лагі (Аршанскі раён)', 4) ('Паўлінава (Баранавіцкі раён)', 4)
    	 88 (('building',), 1027) (('building', 'yes'), 1005) (('addr:street',), 789)
    	 62 (('building',), 1027) (('building', 'yes'), 1005) (('addr:street',), 789)
    	 0
    	 0
    	 0
    	 0
    addr:housename destination:ref 1030 38 0 0
    	 6 ('Н', 837) ('н', 174) ('М', 16)
    	 12 ('М6', 15) ('Бяроза;Антопаль', 4) ('М1', 4)
    	 84 (('building',), 1023) (('building', 'yes'), 1009) (('addr:street',), 879)
    	 66 (('building',), 1023) (('building', 'yes'), 1009) (('addr:street',), 879)
    	 0
    	 0
    	 0
    	 0
    operator fire_hydrant:street 236 1028 0 0
    	 8 ('е', 115) ('я', 86) ('б', 23)
    	 165 ('10 лет Октября', 84) ('Советская', 80) ('Молодежная', 68)
    	 61 (('name',), 150) (('name', 'Складской комплекс «Северный»'), 115) (('landuse',), 115)
    	 488 (('name',), 150) (('name', 'Складской комплекс «Северный»'), 115) (('landuse',), 115)
    	 0
    	 0
    	 0
    	 0
    from destination 1025 100 45 37
    	 8 ('Гомель', 1008) ('Минск', 6) ('Ольшанка', 4)
    	 36 ('Гомель', 32) ('Бабруйск;Гомель', 11) ('Магілёў;Гомель', 7)
    	 153 (('to',), 1025) (('route',), 1025) (('type',), 1025)
    	 103 (('to',), 1025) (('route',), 1025) (('type',), 1025)
    	 4 ('Гомель', 36) ('Ольшанка', 4) ('Минск', 3)
    	 4 ('Гомель', 32) ('Барановичи', 3) ('Минск', 1)
    	 138 (('to',), 45) (('route',), 45) (('type',), 45)
    	 51 (('oneway',), 35) (('oneway', 'yes'), 35) (('highway',), 35)
    addr:housename wheelchair:description 1018 41 0 0
    	 7 ('н', 870) ('кн', 99) ('к', 35)
    	 5 ('Очень крутой подъём.', 24) ('Полное отсутствие доступности, много больших ступенек на входе', 5) ('Ступеньки, но есть кнопка вызова', 5)
    	 86 (('building',), 1018) (('building', 'yes'), 994) (('addr:street',), 731)
    	 56 (('building',), 1018) (('building', 'yes'), 994) (('addr:street',), 731)
    	 0
    	 0
    	 0
    	 0
    addr:district note 1017 4 0 0
    	 3 ('Браславский район', 1008) ('Зарічненський район', 7) ('Костюковка', 2)
    	 4 ('211970 Браславский район', 1) ('мкрн «Костюковка», в сторону Большевика', 1) ('мкрн «Костюковка», в сторону Гомеля', 1)
    	 2194 (('name',), 1017) (('addr:region',), 1015) (('addr:country',), 1011)
    	 34 (('name',), 1017) (('addr:region',), 1015) (('addr:country',), 1011)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city short_name 1017 2 0 0
    	 2 ('Минск', 1016) ('Могилёв', 1)
    	 2 ('СТ "Могилёвские Ведомости"', 1) ('ЦКРОиР Минского района', 1)
    	 1136 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 22 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city branch 1017 16 0 0
    	 2 ('Минск', 1016) ('Могилёв', 1)
    	 2 ('РУП "Минскэнерго"', 15) ('РУП "Могилёвское отделение белорусской железной дороги", могилёвская дистанция электроснабжения', 1)
    	 1136 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 61 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city full_name 1017 2 0 0
    	 2 ('Минск', 1016) ('Могилёв', 1)
    	 2 ('Могилёвский аэроклуб имени А.М. Кулагина', 1) ('Жилищное ремонтно-эксплуатационное объединение Советского района г.Минска', 1)
    	 1136 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 13 (('fire_hydrant:type',), 1017) (('emergency', 'fire_hydrant'), 1017) (('emergency',), 1017)
    	 0
    	 0
    	 0
    	 0
    destination:backward fire_hydrant:city 1 1016 1 1016
    	 1 ('Минск', 1)
    	 1 ('Минск', 1016)
    	 18 (('maxspeed', '90'), 1) (('destination:forward', 'Кобрын;Пiнск'), 1) (('surface',), 1)
    	 1120 (('maxspeed', '90'), 1) (('destination:forward', 'Кобрын;Пiнск'), 1) (('surface',), 1)
    	 1 ('Минск', 1)
    	 1 ('Минск', 1016)
    	 18 (('maxspeed', '90'), 1) (('destination:forward', 'Кобрын;Пiнск'), 1) (('surface',), 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    fire_hydrant:city addr2:street 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('Минская улица', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 10 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city artist_name 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('Дизайн Студия Стиль Минск', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 14 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city website 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('Баня-Минск.бел', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 12 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city official_short_type 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('Нотариальная контора №2 Фрунзенского района г.Минска', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 6 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city phone 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('Многоканальный по Минску: 160 (гор, vel, mts, life) +375 (17) 207-74-74 Стоматология: +375 (29) 160-03-03', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 16 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city fee 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('Москва-Минск', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 2 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city contact:facebook 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('https://www.facebook.com/pages/КУП-Минсксанавтотранс/1416766311868086', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 18 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city name1 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('Минская районная организация  Белорусского Общества Красного Креста', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 10 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city is_in 1016 3 0 0
    	 1 ('Минск', 1016)
    	 1 ('Минский район', 3)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 18 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    fire_hydrant:city oneway 1016 1 0 0
    	 1 ('Минск', 1016)
    	 1 ('ГП «Минсктранс»', 1)
    	 1120 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 6 (('emergency', 'fire_hydrant'), 1016) (('fire_hydrant:type',), 1016) (('emergency',), 1016)
    	 0
    	 0
    	 0
    	 0
    height brand 20 1016 0 0
    	 1 ('ф', 20)
    	 20 ('Белоруснефть', 884) ('Газпромнефть', 52) ('Славнефть', 21)
    	 2 (('barrier',), 20) (('barrier', 'fence'), 20)
    	 3664 (('barrier',), 20) (('barrier', 'fence'), 20)
    	 0
    	 0
    	 0
    	 0
    addr:housename addr:postcode 1015 132 2 1
    	 12 ('н', 696) ('Н', 279) ('к', 21)
    	 9 ('Жлобин', 88) ('Заводской спуск', 24) ('<различные>', 4)
    	 90 (('building',), 1013) (('building', 'yes'), 987) (('addr:street',), 774)
    	 84 (('building',), 1013) (('building', 'yes'), 987) (('addr:street',), 774)
    	 1 ('сарай', 2)
    	 1 ('сарай', 1)
    	 5 (('addr:street',), 2) (('building',), 2) (('building', 'shed'), 2)
    	 2 (('building', 'yes'), 1) (('building',), 1)
    ref BY_PT:note 9 1008 0 0
    	 4 ('Н', 4) ('Т', 2) ('ж', 2)
    	 1 ('Тэги типа "BY_PT..." - временные, для внесения ОТ Беларуси! Не удаляйте их - они будут удалены позже.', 1008)
    	 39 (('railway:signal:position', 'right'), 3) (('railway', 'signal'), 3) (('railway',), 3)
    	 166 (('railway:signal:position', 'right'), 3) (('railway', 'signal'), 3) (('railway',), 3)
    	 0
    	 0
    	 0
    	 0
    building BY_PT:note 166 1008 0 0
    	 4 ('Н', 161) ('н', 2) ('Т', 2)
    	 1 ('Тэги типа "BY_PT..." - временные, для внесения ОТ Беларуси! Не удаляйте их - они будут удалены позже.', 1008)
    	 16 (('name',), 35) (('name', 'Н'), 33) (('building:levels',), 2)
    	 166 (('name',), 35) (('name', 'Н'), 33) (('building:levels',), 2)
    	 0
    	 0
    	 0
    	 0
    ...


## Вынікі сувязей спасылкавай цэласнасьці

### Пазначэньні
- `==` - супадзеньне значэньняў
- `IN` - першае значэньне выкарыстоўваецца ў другім
- `key` - ключ
- `key=val` - тэг
- `key1 + key2` - спалучэньне тэгаў
- `key1 + key2 == key3 + key4` - пры спалучэньні ключэй `key1 + key2` і `key3 + key4` - `key2 == key3`

### Імёны
- `name` IN `official_name` - у адным аб'екце
- `short_name` IN `name` - у адным аб'екце


### Адаміністратыўнае падзяленьне

- `boundary=administrative + admin_level + name` == `addr:region` - вобласьць
- `boundary=administrative + admin_level + name` == `addr:district` - раён
- `boundary=administrative + admin_level + name` == `addr:subdistrict` - сельскі савет

### Места

- `place + name` IN `name + boundary=administrative + admin_level` - вобласьць
- `place + name` IN `name + boundary=administrative + admin_level` - раён
- `place + name` IN `name + boundary=administrative + admin_level` - сельскі савет

- `place + name` == `addr:city` - места
- `place + name` == `addr:place` - места
- `place + name` == `addr:suburb`, `landuse + name` == `addr:suburb` - мікрараён

- `place + name` == `from` - маршрут
- `place + name` == `to` - маршрут
- `place + name` == `via` - маршрут
- `place + name` == `destination + highway` - маршрут
- `place + name` == `destination:backward + highway` - маршрут
- `place + name` == `destination:forward + highway` - маршрут

- `place + name` IN `official_name + highway` - дарога

- `place + name` == `fire_hydrant:city` - места

- `place + name` == `water_tank:city` - вадасхоішча

### Вуліца

- `highway + name` == `addr:street` - вуліца
- `highway + name` == `addr2:street` - вуліца

- `highway + name` == `from` - маршрут
- `highway + name` == `to` - маршрут
- `highway + name` == `via` - маршрут
- `highway + name` == `destination:street + highway` - маршрут
- `highway + name` == `destination:street:backward + highway` - маршрут
- `highway + name` == `destination:street:forward + highway` - маршрут

- `highway + name` == `fire_hydrant:street` - вуліца

### Іншае
- `waterway + name` == `destination + waterway` - рака


```python

```
