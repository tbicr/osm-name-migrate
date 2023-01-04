[out:json][timeout:300];
(
    // issues
    node["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"][!"name:be"]({{bbox}});
    convert node ::id=id(), ::geom=geom(), ::=::, x_state="bad";
    way["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"][!"name:be"]({{bbox}});
    convert way ::id=id(), ::geom=geom(), ::=::, x_state="bad";
    relation["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"][!"name:be"]({{bbox}});
    convert relation ::id=id(), ::geom=geom(), ::=::, x_state="bad";

    // partially issue, POI or required migration
    node["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"]["name:be"]({{bbox}})(if: t["name"] != t["name:be"]);
    convert node ::id=id(), ::geom=geom(), ::=::, x_state="part";
    way["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"]["name:be"]({{bbox}})(if: t["name"] != t["name:be"]);
    convert way ::id=id(), ::geom=geom(), ::=::, x_state="part";
    relation["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"]["name:be"]({{bbox}})(if: t["name"] != t["name:be"]);
    convert relation ::id=id(), ::geom=geom(), ::=::, x_state="part";

    // good part, can be dropped to decrease output
    node["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"]["name:be"]({{bbox}})(if: t["name"] == t["name:be"]);
    convert node ::id=id(), ::geom=geom(), ::=::, x_state="good";
    way["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"]["name:be"]({{bbox}})(if: t["name"] == t["name:be"]);
    convert way ::id=id(), ::geom=geom(), ::=::, x_state="good";
    relation["name"~".*[абвгґдеёжзіийклмнопрстуўфхцчшщьыъэюяАБВГҐДЕЁЖЗІИЙКЛМНОПРСТУЎФХЦЧШЩЬЫЪЭЮЯ].*"]["name:be"]({{bbox}})(if: t["name"] == t["name:be"]);
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
