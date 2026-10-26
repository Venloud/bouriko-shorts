#!/usr/bin/env python3
"""Nonpublishing YouTube download smoke test with stage-specific diagnostics.

Do not confuse plugin discovery, token generation, metadata access, and actual
video download. An MP4 is a pass only after ffprobe validates it.
"""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'youtube_diagnostic'
REPORT = OUT / 'report.json'
TEST_URL = os.environ.get('BOURIKO_YOUTUBE_TEST_URL',
                          'https://www.youtube.com/watch?v=BaW_jenozKc')


def filtered_lines(log):
    keep = ('PO Token Providers:', 'Generating a ', 'Sign in to confirm',
            'ERROR:', 'WARNING:', 'Requested format is not available',
            'No video formats found', 'Downloading webpage',
            'Downloading API JSON', 'Downloading m3u8')
    lines = []
    for raw in log.splitlines():
        if any(tag.lower() in raw.lower() for tag in keep):
            cleaned = re.sub(r'https?://\S+', '[URL]', raw)
            cleaned = re.sub(r'(?i)(?:po[_ -]?token|visitor_data|authorization)\s*[=:]\s*\S+',
                             '[REDACTED]', cleaned)
            lines.append(cleaned[:350])
    return lines[-35:]


def run_ytdlp(*args):
    command = [sys.executable, '-m', 'yt_dlp', '--verbose', '--no-playlist',
               '--extractor-args', 'youtube:player_client=mweb,tv,web_safari',
               '--js-runtimes', 'node',
               '--socket-timeout', '20', '--retries', '1',
               '--fragment-retries', '1', *args, TEST_URL]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=130)
        return result.returncode, (result.stdout or '') + '\n' + (result.stderr or '')
    except subprocess.TimeoutExpired:
        return 124, 'ERROR: yt-dlp timeout (130 seconds)'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    diagnostic = {'source': 'YouTube smoke test only, not an approval for reuse',
                  'video_id': TEST_URL.split('v=')[-1].split('&')[0],
                  'phase': 'setup', 'mp4_validated': False}
    with socket.socket() as s:
        s.settimeout(3)
        diagnostic['po_server_reachable'] = s.connect_ex(('127.0.0.1', 4416)) == 0
    rc, log = run_ytdlp('--simulate', '--no-download')
    lines = filtered_lines(log)
    diagnostic.update({
        'plugin_loaded': any('PO Token Providers:' in x and 'bgutil' in x for x in lines),
        'token_request_seen': any('Generating a ' in x and 'PO Token' in x for x in lines),
        'metadata_result': 'PASS' if rc == 0 else 'FAIL',
        'metadata_log': lines,
    })
    if rc:
        diagnostic['phase'] = 'youtube_metadata_or_ip_challenge'
        diagnostic['failure_class'] = ('YOUTUBE_LOGIN_OR_IP_CHALLENGE' if any('Sign in to confirm' in x for x in lines)
                                      else 'METADATA_FAILURE')
    else:
        diagnostic['phase'] = 'youtube_download'
        rc2, log2 = run_ytdlp('--format', 'best[ext=mp4]/best',
                               '--output', str(OUT / 'smoke.%(ext)s'))
        lines2 = filtered_lines(log2)
        diagnostic['download_log'] = lines2
        diagnostic['token_request_seen'] = diagnostic['token_request_seen'] or any('Generating a ' in x and 'PO Token' in x for x in lines2)
        diagnostic['download_result'] = 'PASS' if rc2 == 0 else 'FAIL'
        if rc2:
            diagnostic['failure_class'] = ('YOUTUBE_LOGIN_OR_IP_CHALLENGE' if any('Sign in to confirm' in x for x in lines2)
                                          else 'DOWNLOAD_FAILURE')
        else:
            video_files = [f for f in OUT.glob('smoke.*') if f.suffix.lower() in {'.mp4', '.mkv', '.webm'}]
            if video_files:
                probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                        '-of', 'default=noprint_wrappers=1:nokey=1', str(video_files[0])],
                                       capture_output=True, text=True)
                if probe.returncode == 0:
                    try:
                        diagnostic['duration_seconds'] = float(probe.stdout.strip())
                        diagnostic['mp4_validated'] = video_files[0].suffix.lower() == '.mp4' and diagnostic['duration_seconds'] > 0
                    except ValueError:
                        pass
            diagnostic['phase'] = 'download_verified' if diagnostic['mp4_validated'] else 'ffprobe_failed'
    REPORT.write_text(json.dumps(diagnostic, indent=2) + '\n')
    print(json.dumps(diagnostic, indent=2), flush=True)
    return 0 if diagnostic['mp4_validated'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
