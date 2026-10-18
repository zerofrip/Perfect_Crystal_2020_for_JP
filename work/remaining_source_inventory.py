"""Categorize the read-only initial-source inventory for final coverage review."""
from pc_env import workspace
from collections import Counter
from pathlib import Path
import json

WORK=(workspace() / 'work')
data=json.loads((WORK/'audit_initial_changes.json').read_text())
remaining={'engine/anim_hp_bar.asm','engine/npctrade.asm','engine/party_menu.asm','maps/SilphCo1F.asm','trainers/dvs.asm'}
clock={'engine/intro_menu.asm','engine/delete_save_change_clock.asm','text/common_5.asm'}
unused={'constants/pokemon_data_constants1.asm','constants/sprite_constants1.asm','engine/mon_icons1.asm','engine/player_movement1.asm'}
for item in data['changes']:
    name=item['path']
    if name in remaining:category='ported_remaining_features'
    elif name in clock:category='covered_clock_module'
    elif name.startswith('battle/') or name=='items/item_effects.asm':category='separate_battle_worker_audit'
    elif name=='items/item_attributes.asm':category='covered_all_255_item_attributes'
    elif name=='data/wild/fish.asm':category='comments_only_actual_484_bytes_identical'
    elif name in unused or name.startswith('gfx/icon1/'):category='unused_no_include_references'
    elif name.startswith('gfx/') and item['status']=='added':category='generated_graphics_build_inputs'
    elif name.startswith('gfx/'):category='covered_restored_sprites_module'
    elif name.endswith(('.zip','.ips')) or name in ('.gitattributes','3840readme.txt','README.md'):category='metadata_documentation_packaged_patch'
    elif name.startswith('data/'):category='covered_full_species_and_encounter_rom_audits'
    elif name=='trainers/trainers.asm':category='covered_full_541_trainer_records'
    elif name in ('engine/tmhm2.asm','engine/player_movement.asm','items/marts.asm'):category='covered_builder_tm_running_marts'
    elif name.startswith(('maps/','constants/')) or name in ('maps.asm','engine/landmarks.asm'):category='covered_gym_cave_gs_ball_red_rewards_maps'
    else:raise AssertionError(('unclassified',name))
    item['coverage_category']=category
data['counts']=dict(Counter(i['coverage_category'] for i in data['changes']))
data['baseline_confidence']='Highest exact path/blob match among 348 first-parent upstream commits from 2015 through 2019-02-07; not an assertion of the exact fork point.'
(WORK/'remaining_source_diff.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data['counts'],indent=2))
