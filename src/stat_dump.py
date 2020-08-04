import pstats

stats = pstats.Stats('pstats')
stats.sort_stats('time').print_stats()
stats.sort_stats('cumulative').print_stats()