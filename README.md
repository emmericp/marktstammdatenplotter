# Marktstammdatenregister plotter

Draws maps from Marktstammdatenregister.de data.

**Caution**:
This is "research-quality code", i.e., a complete mess that needs to run exactly once.
Also, most of it is AI generated and the AI loves to do be very verbose in random odd places, I didn't clean up anything here.
Good luck.

## Getting Marktstammdatenregister data

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

## Getting map data

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

## Turning results into GIFs

It is surprisingly difficult to turn a bunch of PNGs with names that aren't name like "frame001.png" etc into a video with ffmpeg.
I ended up using this terrible Fish command:

```
set -l file wind; set -l frames_to_repeat 120; mktemp -d | read -l temp_dir; and cp "$file"-*.png $temp_dir; and begin; set -l i 1; set -l last_frame_path ""; for
 f in (ls "$temp_dir/$file"*.png | sort); mv $f (printf "%s/frame%03d.png" $temp_dir $i); set last_frame_path (printf "%s/frame%03d.png" $temp_dir $i); set i (math $i + 1); end; set -l current
_duplicate_index $i; for j in (seq 1 $frames_to_repeat); cp "$last_frame_path" (printf "%s/frame%03d.png" $temp_dir $current_duplicate_index); set current_duplicate_index (math $current_duplic
ate_index + 1); end; end; and ffmpeg -framerate 30 -i "$temp_dir/frame%03d.png" -vf "scale=-1:1200:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse=dither=none" -loop 0 -y "$fil
e".gif; and rm -rf "$temp_dir"
```

Almost all of that is just a convoluted way to rename the files into a pattern accepted by ffmpeg.
Fun fact: This problem is specific to the lack of timestamp metadata on PNGs, if these were JPGs with EXIF data it would be much simpler.
