"""Apply the locally generated Japanese IPS with lazy_ips and strict hashes."""
import argparse
from hashlib import sha1,sha256
import json
from pathlib import Path
import sys

from pc_env import workspace

ROOT=workspace()

def main():
    parser=argparse.ArgumentParser(description='Perfect Crystal 2020 Japanese IPS applicator (local files only)')
    parser.add_argument('rom',type=Path,help='Original Pocket Monsters - Crystal Version (Japan).gbc')
    parser.add_argument('--output',required=True,type=Path,help='New output path; existing files are never overwritten')
    args=parser.parse_args()
    package=ROOT/'work/release'
    manifest=json.loads((package/'manifest.json').read_text())
    original=args.rom.read_bytes()
    if (len(original)!=manifest['rom_size'] or
        sha1(original).hexdigest()!=manifest['input_sha1'] or
        sha256(original).hexdigest()!=manifest['input_sha256']):
        parser.error('対象ROMのSHA-1が一致しません。日本語版の原本が必要です。')
    patch=package/manifest['ips_file']
    if sha256(patch.read_bytes()).hexdigest()!=manifest['ips_sha256']:
        parser.error('IPSのSHA-256が一致しません。')
    sys.path.insert(0,str(ROOT/'lazy_ips'))
    from lazy_ips.patch import ips
    output=bytearray(original)
    with patch.open('rb') as stream:
        for record in ips.read_patch(stream):
            end=record.offset+len(record.data)
            if end>len(output):parser.error('IPS書込先がROMサイズを超えています。')
            output[record.offset:end]=record.data
    if sha256(output).hexdigest()!=manifest['output_sha256']:
        parser.error('適用結果のSHA-256が一致しません。出力しません。')
    try:
        with args.output.open('xb') as stream:
            stream.write(output)
    except FileExistsError:
        parser.error('出力先は既に存在します。別の出力先を指定してください。')
    print('適用とSHA-256検証が完了しました:',args.output.resolve())

if __name__=='__main__':main()
