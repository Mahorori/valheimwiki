# Valheim Wiki Generator

## Deploy
https://mahorori.github.io/valheimwiki/out/

## How to use
1. Install BepInEx5
2. Build Plugin
```
dotnet build MyFirstPlugin
```
3. Run script
```
python3 ./scripts/main.py
```

## How it works
1. Inject dumper code with BepInEx and extracts all game data
2. Generate html files
3. Profit

## TODO
- Shield page details
- tooltier
- buildPieces
- hp/stamina/eitr on card
- biome page
    - locations
    - mobs
    - items
    - ...
- fish biome
- comfort
- use .css...