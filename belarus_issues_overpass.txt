[out:json][timeout:25];
(
    // issues
    node["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"][!"name:be"]({{bbox}});
    convert node ::id=id(), ::geom=geom(), ::=::, x_state="bad";
    way["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"][!"name:be"]({{bbox}});
    convert way ::id=id(), ::geom=geom(), ::=::, x_state="bad";
    relation["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"][!"name:be"]({{bbox}});
    convert relation ::id=id(), ::geom=geom(), ::=::, x_state="bad";

    // partially issue, POI or required migration
    node["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"]["name:be"]({{bbox}})(if: t["name"] != t["name:be"]);
    convert node ::id=id(), ::geom=geom(), ::=::, x_state="part";
    way["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"]["name:be"]({{bbox}})(if: t["name"] != t["name:be"]);
    convert way ::id=id(), ::geom=geom(), ::=::, x_state="part";
    relation["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"]["name:be"]({{bbox}})(if: t["name"] != t["name:be"]);
    convert relation ::id=id(), ::geom=geom(), ::=::, x_state="part";

    // good part, can be dropped to decrease output
    node["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"]["name:be"]({{bbox}})(if: t["name"] == t["name:be"]);
    convert node ::id=id(), ::geom=geom(), ::=::, x_state="good";
    way["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"]["name:be"]({{bbox}})(if: t["name"] == t["name:be"]);
    convert way ::id=id(), ::geom=geom(), ::=::, x_state="good";
    relation["name"~".*(а|б|в|г|ґ|д|е|ё|ж|з|і|и|й|к|л|м|н|о|п|р|с|т|у|ў|ф|х|ц|ч|ш|щ|ь|ы|ъ|э|ю|я|А|Б|В|Г|Ґ|Д|Е|Ё|Ж|З|І|И|Й|К|Л|М|Н|О|П|Р|С|Т|У|Ў|Ф|Х|Ц|Ч|Ш|Щ|Ь|Ы|Ъ|Э|Ю|Я).*"]["name:be"]({{bbox}})(if: t["name"] == t["name:be"]);
    convert relation ::id=id(), ::geom=geom(), ::=::, x_state="good";
);
out body;
>;
out skel qt;

{{style:
    node[x_state=bad], way[x_state=bad], relation[x_state=bad] {
        color:red; fill-color:red;
    }
    node[x_state=part], way[x_state=part], relation[x_state=part] {
        color:yellow; fill-color:yellow;
    }
    node[x_state=good], way[x_state=good], relation[x_state=good] {
        color:green; fill-color:green;
    }
}}
