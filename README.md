# OSM Name Migrate

## Binary Dependencies

    apt install osmctools

## Belarus OSM links detection

[belarus-osm-links.ipynb](belarus-osm-links.md)

## Belarus OSM `name`, `name:be`, `name:ru` tags statistic per category

[belarus-osm-name-statistic.ipynb](belarus-osm-name-statistic.md)

## Belarus OSM full language tag statistic per category

[index.html](https://tbicr.github.io/osm-name-migrate/)

To create report run:

    docker-compose run --rm management python belarus_report.py
