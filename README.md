# Marktstammdatenregister Plotter

Draws maps from Marktstammdatenregister.de data.

**Caution**:
This is "research-quality code", i.e., a complete mess that needs to run exactly once.
Also, most of it is AI generated and the AI loves to do be very verbose in random odd places, I didn't clean up anything here.
Good luck.

## Getting Marktstammdatenregister Data

I know, there's an XML export, you should probably use that. But I just scraped the API instead because it already filters it down a bit and it gives me JSON instead of XML. The API is very straightforward to use, I just get the data on a shell like this.

```
seq 7 | xargs -P 4 -I{} curl --get 'https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetErweiterteOeffentlicheEinheitStromerzeugung' \
                                          --data-urlencode 'sort=' \
                                          --data-urlencode 'page={}' \
                                          --data-urlencode 'pageSize=25000' \
                                          --data-urlencode 'group=' \
                                          --data-urlencode 'filter=Energieträger~neq~\'2495\'~and~Energieträger~neq~\'2496\'' \
                                          --data-urlencode 'forExport=true' -o data-{}.json
```

## Getting Map Data

County data is extracted from an OSM export of Germany and then filtered down like this:

```
 osmfilter germany-latest.o5m \
  --keep-nodes="boundary=administrative and ( admin_level=6 or admin_level=4 )" \
  --keep-ways="boundary=administrative and ( admin_level=6 or admin_level=4 )" \
  --keep-relations="boundary=administrative and ( admin_level=6 or admin_level=4 )" \
  --drop-version --drop-author \
  -o=germany_admin_levels_4_6.osm
ogr2ogr -f GPKG germany_kreise.gpkg germany_admin_levels_4_6.osm -sql "SELECT name, admin_level, boundary FROM multipolygons WHERE boundary = 'administrative' and (adm
in_level = '6' or (admin_level = '4' and name IN ('Berlin', 'Hamburg', 'Bremen')))" -nlt MULTIPOLYGON -overwrite -nln multipolygons
```
