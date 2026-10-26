#!/usr/bin/env python3
"""Nonpublishing YouTube download diagnostic: reports the exact failure stage.

Stages (each recorded separately in output/youtube_diagnostic/report.json):
  1. environment  - yt-dlp / plugin versions, PO-token server socket + HTTP answer
  2. search       - flat ytsearch (no per-video request)
  3. clients      - per player_client metadata check; records whether yt-dlp loaded
                    the bgutil plugin, whether a PO token was actually generated, and
                    whether the bot check came BEFORE any token request (= IP challenge)
  4. download     - one real download with the first client config that passed,
                    validated with ffprobe (video stream, duration > 0, .mp4)

Optional auth: if YT_COOKIES_FILE points at a Netscape cookies file (written by the
workflow from a GitHub secret), a cookies run is added. The file is copied to a
private temp file (yt-dlp rewrites cookie jars), never printed, and deleted.
Exit 0 only when an MP4 downloaded and passed ffprobe.
"""
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'youtube_diagnostic'
REPORT = OUT / 'report.json'
TEST_URL = os.environ.get('BOURIKO_YOUTUBE_TEST_URL',
                          'https://www.youtube.com/watch?v=jNQXAC9IVRw')
CLIENTS = os.environ.get('BOURIKO_YOUTUBE_CLIENTS',
                         'default;mweb,tv,web_safari;mweb;tv;web_safari;tv_simply;web_embedded;android_vr').split(';')
POT_PORT = 4416
# yt-dlp only enables deno by default; GitHub runners ship node, so enable it explicitly.
JS_RUNTIME = os.environ.get('BOURIKO_YTDLP_JS_RUNTIME', 'node')


def redact(text):
    text = re.sub(r'https?://\S+', '[URL]', text)
    text = re.sub(r'(?i)(po[_ -]?token|visitor_?data|authorization|cookie|sapisid|__secure-\S+)\s*[=:]\s*\S+',
                  r'\1=[REDACTED]', text)
    return text


def filtered_lines(log):
    keep = ('PO Token Providers', 'Generating a ', 'Sign in to confirm', 'ERROR:', 'WARNING:',
            'Downloading webpage', 'player API JSON', 'Downloading tv', 'Downloading android',
            'Downloading m3u8', 'Requested format', 'unavailable', '[pot', 'Cookies')
    out = []
    for raw in log.splitlines():
        if any(k.lower() in raw.lower() for k in keep):
            out.append(redact(raw)[:300])
    return out[-30:]


def run_ytdlp(args, cookies=None, timeout=240):
    cmd = [sys.executable, '-m', 'yt_dlp', '--verbose', '--no-playlist',
           '--socket-timeout', '20', '--retries', '1', '--fragment-retries', '1',
           '--js-runtimes', JS_RUNTIME]
    if cookies:
        cmd += ['--cookies', cookies]
    cmd += args
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return p.returncode, (p.stdout or '') + '\n' + (p.stderr or '')
    except subprocess.TimeoutExpired as exc:
        return 124, f'ERROR: timeout after {timeout}s {exc.stdout or ""}{exc.stderr or ""}'


def classify(code, log):
    lower = log.lower()
    bot_idx = lower.find('sign in to confirm')
    tok_idx = lower.find('generating a ')
    info = {
        'plugin_loaded': 'bgutil:http' in lower,
        'po_token_generated': tok_idx >= 0,
        'bot_check': bot_idx >= 0,
        'bot_check_before_any_token': bot_idx >= 0 and (tok_idx < 0 or bot_idx < tok_idx),
    }
    if code == 0:
        info['result'] = 'OK'
    elif bot_idx >= 0:
        info['result'] = 'BOT_CHECK'
    elif 'video is unavailable' in lower:
        info['result'] = 'UNAVAILABLE_TO_THIS_IP_OR_CLIENT'
    elif '429' in lower:
        info['result'] = 'HTTP_429'
    elif 'requested format is not available' in lower or 'no video formats' in lower:
        info['result'] = 'NO_FORMATS'
    else:
        info['result'] = 'OTHER_FAILURE'
    return info


def environment():
    env = {}
    for mod in ('yt_dlp', 'yt_dlp_plugins.extractor.getpot_bgutil_http'):
        try:
            m = __import__(mod, fromlist=['x'])
            env[mod] = getattr(getattr(m, 'version', None), '__version__', None) or 'importable'
        except Exception as exc:  # noqa: BLE001
            env[mod] = f'not importable: {type(exc).__name__}'
    try:
        with socket.create_connection(('127.0.0.1', POT_PORT), timeout=3):
            env['pot_socket'] = 'reachable'
    except OSError as exc:
        env['pot_socket'] = f'unreachable: {exc}'
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{POT_PORT}/ping', timeout=5) as r:
            env['pot_ping'] = {'status': r.status, 'body': r.read(300).decode('utf-8', 'replace')}
    except Exception as exc:  # noqa: BLE001
        env['pot_ping'] = f'failed: {type(exc).__name__}: {str(exc)[:120]}'
    return env


def ffprobe(path):
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                        'format=duration,format_name:stream=codec_type,codec_name,width,height',
                        '-of', 'json', str(path)], text=True, capture_output=True)
    if p.returncode != 0:
        return {'ok': False, 'error': p.stderr[-300:]}
    data = json.loads(p.stdout)
    streams = data.get('streams', [])
    duration = float(data.get('format', {}).get('duration') or 0)
    has_video = any(s.get('codec_type') == 'video' for s in streams)
    return {'ok': has_video and duration > 0 and path.suffix == '.mp4', 'duration': duration,
            'format': data.get('format', {}).get('format_name'), 'streams': streams,
            'bytes': path.stat().st_size}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'source': 'YouTube smoke test only, not an approval for reuse', 'test_url': TEST_URL,
              'mp4_validated': False}
    report['environment'] = environment()

    code, log = run_ytdlp(['--flat-playlist', '--print', 'id', 'ytsearch3:traffic light timelapse'], timeout=90)
    ids = [x for x in log.splitlines() if re.fullmatch(r'[\w-]{11}', x.strip())]
    report['search'] = {'result': 'OK' if code == 0 and ids else 'FAIL', 'ids_found': len(ids),
                        'log': [] if ids else filtered_lines(log)}

    cookie_tmp = None
    src = os.environ.get('YT_COOKIES_FILE')
    report['cookies_supplied'] = bool(src and Path(src).is_file() and Path(src).stat().st_size > 0)
    if report['cookies_supplied']:
        fd, cookie_tmp = tempfile.mkstemp(prefix='ytc_', suffix='.txt')
        os.close(fd)
        os.chmod(cookie_tmp, 0o600)
        shutil.copyfile(src, cookie_tmp)

    configs = [(c.strip(), None) for c in CLIENTS if c.strip()]
    if cookie_tmp:
        configs = [('default', cookie_tmp), ('mweb,tv,web_safari', cookie_tmp)] + configs
    results, winner = [], None
    for client, cookies in configs:
        args = ['--simulate', '--print', 'id']
        if client != 'default':
            args += ['--extractor-args', f'youtube:player_client={client}']
        code, log = run_ytdlp(args + [TEST_URL], cookies=cookies, timeout=120)
        info = {'client': client, 'cookies': bool(cookies), **classify(code, log), 'log': filtered_lines(log)}
        results.append(info)
        print(f"metadata client={client:<22} cookies={bool(cookies)!s:<5} -> {info['result']}"
              f" plugin={info['plugin_loaded']} token={info['po_token_generated']}"
              f" bot_before_token={info['bot_check_before_any_token']}", flush=True)
        if info['result'] == 'OK' and not winner:
            winner = (client, cookies)
            break
        time.sleep(4)
    report['clients'] = results

    if winner:
        client, cookies = winner
        for old in OUT.glob('smoke.*'):
            old.unlink()
        args = ['--format', 'bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/b',
                '--merge-output-format', 'mp4', '-o', str(OUT / 'smoke.%(ext)s')]
        if client != 'default':
            args += ['--extractor-args', f'youtube:player_client={client}']
        code, log = run_ytdlp(args + [TEST_URL], cookies=cookies, timeout=300)
        files = sorted(OUT.glob('smoke.*'))
        report['download'] = {'client': client, 'cookies': bool(cookies), 'exit_code': code,
                              **classify(code, log), 'files': [f.name for f in files],
                              'log': filtered_lines(log)}
        mp4 = next((f for f in files if f.suffix == '.mp4'), None)
        if mp4:
            report['ffprobe'] = ffprobe(mp4)
            report['mp4_validated'] = bool(report['ffprobe']['ok'])

    if cookie_tmp:
        os.unlink(cookie_tmp)

    if report['mp4_validated']:
        report['phase'] = 'PASS'
    elif winner:
        report['phase'] = 'DOWNLOAD_FAILED_AFTER_METADATA_OK'
    elif report['search']['result'] != 'OK':
        report['phase'] = 'SEARCH_FAILED'
    elif results and all(r['bot_check_before_any_token'] or r['result'] == 'UNAVAILABLE_TO_THIS_IP_OR_CLIENT'
                         for r in results):
        report['phase'] = 'IP_CHALLENGE_BEFORE_PO_TOKEN'
    else:
        report['phase'] = 'METADATA_FAILED'

    REPORT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"YOUTUBE DIAGNOSTIC: {report['phase']}")
    return 0 if report['mp4_validated'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
