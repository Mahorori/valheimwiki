import os

from database.database import ValheimDatabase
from default_generator.generator import DefaultGenerator
from default_generator.localization import Localization

# ===== paths =====
BepInExPath = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx"

def main():
    localization = Localization()
    localization.load(os.path.join(BepInExPath, "localization"))

    database = ValheimDatabase()
    database.load(BepInExPath)

    generator = DefaultGenerator(localization, database)
    generator.generate('out')

if __name__ == "__main__":
    main()