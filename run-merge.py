#! /usr/bin/env python3
from config import Config
import gathermate

cfg = Config()
print("gathermates: {}".format(repr(cfg.gathermates)))
base = gathermate.load_db(cfg.dbname)
stat_before = gathermate.calc_statistics(base)
for filename in cfg.gathermates:
    addbase = gathermate.load_db(filename)
    print(f"merge with {filename}")
    base = gathermate.deep_merge(base, addbase)
stat_after = gathermate.calc_statistics(base)
gathermate.print_statistics_changes(stat_before, stat_after)
gathermate.save_db(base, cfg.dbname)
