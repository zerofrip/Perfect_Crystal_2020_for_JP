"""Four explicitly requested corrections layered after the faithful 2020 port."""
from fix_moon_ball import apply_moon_ball_fix
from fix_dragon_fang import apply_dragon_fang_fix
from fix_magikarp_comparison import apply_magikarp_comparison_fix
from fix_sharp_stat_drop import apply_sharp_stat_drop_fix

def apply_requested_fixes(original,english_stock,perfect,output):
    ranges=[]
    for feature in (apply_moon_ball_fix,apply_dragon_fang_fix,
                    apply_magikarp_comparison_fix,apply_sharp_stat_drop_fix):
        ranges.extend(feature(original,english_stock,perfect,output))
    return ranges
