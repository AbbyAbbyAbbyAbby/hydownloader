#!/usr/bin/env python3

# hydownloader
# Copyright (C) 2021  thatfuckingbird

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import shutil
import os
import sqlite3
import time
import subprocess
import re
from typing import Optional
import click
from hydownloader import db, log, gallery_dl_utils

@click.group()
def cli() -> None:
    pass

def clear_test_env() -> None:
    log.info('hydownloader-test', 'Clearing test environment...')
    if os.path.exists(db.get_rootpath()+'/test'):
        shutil.rmtree(db.get_rootpath()+'/test')
    os.makedirs(db.get_rootpath() + "/test")
    log.info('hydownloader-test', 'Test environment cleared')

def check_results_of_post_url(data: dict, sitename: str) -> bool:
    """
    Downloads a URL with gallery-dl, then checks if the
    downloaded filenames, file content and anchor entries match what was provided by the caller.
    """
    url = data['url']
    filenames = data['filenames']
    anchors = data['anchors']
    log.info("hydownloader-test", f'Testing downloading of posts for site {sitename}')
    log_file = db.get_rootpath()+f"/logs/test-site-{sitename}-gallery-dl.txt"
    result_txt = gallery_dl_utils.run_gallery_dl(
        url=url,
        ignore_anchor=False,
        metadata_only=False,
        log_file=log_file,
        console_output_file=db.get_rootpath()+f"/test/test-site-{sitename}-gallery-dl-output.txt",
        unsupported_urls_file=db.get_rootpath()+f"/test/test-site-{sitename}-unsupported-urls-gallery-dl.txt",
        overwrite_existing=False,
        subscription_mode=False,
        test_mode = True
    )
    result = True
    if result_txt:
        log.error("hydownloader-test", f"Error returned for {sitename} download: {result_txt}")
        result = False
    else:
        log.info("hydownloader-test", f"Return code for {sitename} download OK")
    for fname in filenames:
        abs_fname = db.get_rootpath()+"/test/data/gallery-dl/"+fname
        if not os.path.isfile(abs_fname):
            log.error("hydownloader-test", f"Missing expected file: {fname}")
            result = False
        else:
            log.info("hydownloader-test", f"Found expected file: {fname}")
            for content in filenames[fname]:
                with open(abs_fname) as f:
                    if re.search(content, f.read()):
                        log.info("hydownloader-test", "Expected file content found")
                    else:
                        log.error("hydownloader-test", f"Expected file content ({content}) NOT found")
                        result = False
    conn = sqlite3.connect(db.get_rootpath()+"/test/anchor.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    for anchor in anchors:
        try:
            c.execute('select entry from archive where entry = ?', (anchor,))
            if len(c.fetchall()):
                log.info("hydownloader-test", f"Expected anchor {anchor} found in database")
            else:
                log.error("hydownloader-test", f"Expected anchor {anchor} NOT found in database")
                result = False
        except sqlite3.OperationalError as e:
            log.error("hydownloader-test", "Error while trying to query anchor database - download failed?", e)
            result = False
    return result

@cli.command(help='Test downloading from a list of sites.')
@click.option('--path', type=str, required=True, help='Database path.')
@click.option('--sites', type=str, required=True, help='A comma-separated list of sites to test downloading from. Currently supported: environment, gelbooru, pixiv, lolibooru, patreon, danbooru, 3dbooru, nijie, sankaku, idolcomplex, artstation, twitter, deviantart. WARNING: this will attempt to download "sensitive" content.')
def test(path: str, sites: str) -> None:
    log.init(path, True)
    db.init(path)
    test_internal(sites)

def test_internal(sites: str) -> None:
    post_url_data = {
        'gelbooru': {
            'url': "https://gelbooru.com/index.php?page=post&s=view&id=6002236",
            'filenames': {
                "gelbooru/gelbooru_6002236_0ef507cc4c222406da544db3231de323.jpg.json": ["1girl ", "wings", '"rating": "q"', '"tags_general":'],
                "gelbooru/gelbooru_6002236_0ef507cc4c222406da544db3231de323.jpg": []
            },
            'anchors': ["gelbooru6002236"]
        },
        'gelbooru_notes': {
            'url': "https://gelbooru.com/index.php?page=post&s=view&id=5997331",
            'filenames': {
                "gelbooru/gelbooru_5997331_7726d401af0e6bf5b58809f65d08334e.png.json": ['"y": 72', '"x": 35', '"width": 246', '"height": 553', '"body": "Look over this way when you talk~"']
            },
            'anchors': ["gelbooru5997331"]
        },
        'danbooru': {
            'url': "https://danbooru.donmai.us/posts/4455434",
            'filenames': {
                "danbooru/danbooru_4455434_e110444217827ef3f82fb33b45e1841f.png.json": ["1girl ", "tail", '"rating": "q"'],
                "danbooru/danbooru_4455434_e110444217827ef3f82fb33b45e1841f.png": []
            },
            'anchors': ["danbooru4455434"]
        },
        'pixiv': {
            'url': "https://www.pixiv.net/en/artworks/88865254",
            'filenames': {
                "pixiv/3316400 rogia/88865254_p7.jpg.json": [],
                "pixiv/3316400 rogia/88865254_p6.jpg.json": [],
                "pixiv/3316400 rogia/88865254_p5.jpg.json": [],
                "pixiv/3316400 rogia/88865254_p4.jpg.json": [],
                "pixiv/3316400 rogia/88865254_p3.jpg.json": [],
                "pixiv/3316400 rogia/88865254_p2.jpg.json": ["Fate/GrandOrder", '"title": "メイドロリンチちゃん"', '"tags":', '"untranslated_tags":'],
                "pixiv/3316400 rogia/88865254_p1.jpg.json": [],
                "pixiv/3316400 rogia/88865254_p0.jpg.json": [],
                "pixiv/3316400 rogia/88865254_p7.jpg": [],
                "pixiv/3316400 rogia/88865254_p6.jpg": [],
                "pixiv/3316400 rogia/88865254_p5.jpg": [],
                "pixiv/3316400 rogia/88865254_p4.jpg": [],
                "pixiv/3316400 rogia/88865254_p3.jpg": [],
                "pixiv/3316400 rogia/88865254_p2.jpg": [],
                "pixiv/3316400 rogia/88865254_p1.jpg": [],
                "pixiv/3316400 rogia/88865254_p0.jpg": []
            },
            'anchors': ["pixiv88865254_p00","pixiv88865254_p01","pixiv88865254_p02","pixiv88865254_p03","pixiv88865254_p04","pixiv88865254_p05","pixiv88865254_p06", "pixiv88865254_p07"]
        },
        'pixiv_ugoira': {
            'url': "https://www.pixiv.net/en/artworks/88748768",
            'filenames': {
                "pixiv/9313418 thaimay704/88748768_p0.zip": [],
                "pixiv/9313418 thaimay704/88748768_p0.zip.json": [],
                "pixiv/9313418 thaimay704/88748768_p0.webm": []
            },
            'anchors': ["pixiv88748768"]
        },
        'lolibooru': {
            'url': 'https://lolibooru.moe/post/show/178123/1girl-barefoot-brown_eyes-brown_hair-cameltoe-cove',
            'filenames': {
                "lolibooru/lolibooru_178123_a77d70e0019fc77c25d0ae563fc9b324.jpg.json": ["1girl ", " swimsuit", '"rating": "q",'],
                "lolibooru/lolibooru_178123_a77d70e0019fc77c25d0ae563fc9b324.jpg": []
            },
            'anchors': ["lolibooru178123"]
        },
        '3dbooru': {
            'url': "http://behoimi.org/post/show/648363/apron-black_legwear-collar-cosplay-hairband-immora",
            'filenames': {
                "3dbooru/3dbooru_648363_720f344170696293c3fe2640c59d8f41.jpg.json": ["cosplay ", " maid_uniform", '"rating": "s",'],
                "3dbooru/3dbooru_648363_720f344170696293c3fe2640c59d8f41.jpg": []
            },
            'anchors': ["3dbooru648363"]
        },
        'nijie': {
            'url': "https://nijie.info/view.php?id=306993",
            'filenames': {
                "nijie/72870/306993_p0.jpg": [],
                "nijie/72870/306993_p1.jpg": [],
                "nijie/72870/306993_p0.jpg.json": [],
                "nijie/72870/306993_p1.jpg.json": ["\"オリジナル\"", "\"title\": \"朝7時50分の通学路\","]
            },
            'anchors': ["nijie306993_0", "nijie306993_1"]
        },
        'patreon': {
            'url': "https://www.patreon.com/posts/new-cg-set-on-48042243",
            'filenames': {
                "patreon/Osiimi Chan/48042243_NEW CG SET on Gumroad!! Ganyu's Hypnotic Rendezvou_01.png": []
            },
            'anchors': ["patreon48042243_1"]
        },
        'sankaku': {
            'url': "https://chan.sankakucomplex.com/post/show/707246",
            'filenames': {
                "sankaku/sankaku_707246_5da41b5136905c35cad9cbcba89836a3.jpg": [],
                "sankaku/sankaku_707246_5da41b5136905c35cad9cbcba89836a3.jpg.json": ['"kirisame_marisa"', '"3girls"']
            },
            'anchors': ["sankaku707246"]
        },
        'idolcomplex': {
            'url': "https://idol.sankakucomplex.com/post/show/701724",
            'filenames': {
                "idolcomplex/idolcomplex_701724_92b853bcf8dbff393c6217839013bcab.jpg": [],
                "idolcomplex/idolcomplex_701724_92b853bcf8dbff393c6217839013bcab.jpg.json": ['"rating": "q",', 'nikumikyo,']
            },
            'anchors': ["idolcomplex701724"]
        },
        'artstation': {
            'url': "https://www.artstation.com/artwork/W2LROD",
            'filenames': {
                "artstation/sergey_vasnev/artstation_6721469_24728858_Procession.jpg": [],
                "artstation/sergey_vasnev/artstation_6721469_24728858_Procession.jpg.json": ['"title": "Procession",']
            },
            'anchors': ["artstation24728858"]
        },
        'deviantart': {
            'url': "https://www.deviantart.com/squchan/art/Atelier-Ryza-820511154",
            'filenames': {
                "deviantart/SquChan/deviantart_820511154_Atelier Ryza.jpg": [],
                "deviantart/SquChan/deviantart_820511154_Atelier Ryza.jpg.json": ['"is_mature": true,']
            },
            'anchors': ["deviantart820511154"]
        },
        'twitter': {
            'url': "https://twitter.com/momosuzunene/status/1380033327680266244",
            'filenames': {
                "twitter/momosuzunene/1380033327680266244_1.jpg": [],
                "twitter/momosuzunene/1380033327680266244_1.jpg.json": ['"name": "momosuzunene",']
            },
            'anchors': ["twitter1380033327680266244_1"]
        }
    }

    site_set = {site.strip() for site in sites.split(',')}
    for site in site_set:
        clear_test_env()
        log_file = db.get_rootpath()+f"/logs/test-site-{site}-gallery-dl.txt"
        should_break = False
        if site == 'environment':
            log.info("hydownloader-test", "Querying gallery-dl version")
            version_str = gallery_dl_utils.run_gallery_dl_with_custom_args(['--version'], capture_output = True).stdout.strip()
            try:
                if version_str.endswith("-dev"): version_str = version_str[:-4]
                major, minor, patch = tuple(map(int, version_str.split('.')))
                if major != 1 or minor < 17 or minor == 17 and patch < 3:
                    log.error('hydownloader-test', f"Bad gallery-dl version: {version_str}, need 1.17.3 or newer")
                else:
                    log.info('hydownloader-test', f"Found gallery-dl version: {version_str}, this is OK")
            except ValueError as e:
                log.error('hydownloader-test', "Could not recognize gallery-dl version", e)
            try:
                ff_result = subprocess.run(['ffmpeg', '-version'], capture_output = True, text = True, check = False).stdout.split('\n')[0]
                log.info('hydownloader-test', f"Found ffmpeg version: {ff_result}")
            except FileNotFoundError as e:
                log.error('hydownloader-test', "Could not find ffmpeg", e)
            try:
                yt_result = subprocess.run(['youtube-dl', '--version'], capture_output = True, text = True, check = False).stdout.strip()
                log.info('hydownloader-test', f"Found youtube-dl version: {yt_result}")
            except FileNotFoundError as e:
                log.error('hydownloader-test', "Could not find youtube-dl", e)
        elif site == "gelbooru":
            log.info("hydownloader-test", "Testing Gelbooru...")

            log.info("hydownloader-test", 'Testing search of "sensitive" content')
            sensitive_url = "https://gelbooru.com/index.php?page=post&s=list&tags=loli"
            result = gallery_dl_utils.run_gallery_dl_with_custom_args([sensitive_url, '--get-urls', '-o', 'image-range="1-10"', '--write-log', log_file], capture_output = True)
            sensitive_ok = True
            if result.returncode != 0:
                status_txt = gallery_dl_utils.check_return_code(result.returncode)
                log.error("hydownloader-test", f'Error returned while trying to download "sensitive" content: return code {result.returncode}, {status_txt}')
                sensitive_ok = False
                should_break = True
            sensitive_results_cnt = len(re.findall("https://.*?gelbooru.com/images", result.stdout))
            if sensitive_results_cnt < 10:
                log.error("hydownloader-test", f'Failed to find "sensitive" content, insufficient number of results: {sensitive_results_cnt}')
                sensitive_ok = False
                should_break = True
            if sensitive_ok:
                log.info("hydownloader-test", 'Search of "sensitive" content seems to be working OK')

            should_break = not check_results_of_post_url(post_url_data['gelbooru'], site) or should_break

            log.info("hydownloader-test", 'Testing note extraction')
            should_break = not check_results_of_post_url(post_url_data['gelbooru_notes'], site) or should_break
        elif site == "danbooru":
            log.info("hydownloader-test", "Testing danbooru...")

            log.info("hydownloader-test", 'Testing search of "sensitive" content')
            sensitive_url = "https://danbooru.donmai.us/posts?tags=loli"
            result = gallery_dl_utils.run_gallery_dl_with_custom_args([sensitive_url, '--get-urls', '-o', 'image-range="1-10"', '--write-log', log_file], capture_output = True)
            sensitive_ok = True
            if result.returncode != 0:
                status_txt = gallery_dl_utils.check_return_code(result.returncode)
                log.error("hydownloader-test", f'Error returned while trying to download "sensitive" content: return code {result.returncode}, {status_txt}')
                sensitive_ok = False
                should_break = True
            sensitive_results_cnt = len(re.findall("https://danbooru.donmai.us/data", result.stdout))
            if sensitive_results_cnt < 10:
                log.error("hydownloader-test", f'Failed to find "sensitive" content, insufficient number of results: {sensitive_results_cnt}')
                sensitive_ok = False
                should_break = True
            if sensitive_ok:
                log.info("hydownloader-test", 'Search of "sensitive" content seems to be working OK')

            should_break = not check_results_of_post_url(post_url_data['danbooru'], site) or should_break
        elif site == "pixiv":
            log.info("hydownloader-test", "Testing pixiv...")
            should_break = not check_results_of_post_url(post_url_data['pixiv'], site) or should_break
            log.info("hydownloader-test", 'Testing downloading of ugoira')
            should_break = not check_results_of_post_url(post_url_data['pixiv_ugoira'], site) or should_break
        elif site == "lolibooru":
            log.info("hydownloader-test", "Testing lolibooru.moe...")
            should_break = not check_results_of_post_url(post_url_data['lolibooru'], site) or should_break
        elif site == "3dbooru":
            log.info("hydownloader-test", "Testing 3dbooru...")
            should_break = not check_results_of_post_url(post_url_data['3dbooru'], site) or should_break
        elif site == "patreon":
            log.info("hydownloader-test", "Testing Patreon...")
            should_break = not check_results_of_post_url(post_url_data['patreon'], site) or should_break
        elif site == "nijie":
            log.info("hydownloader-test", "Testing nijie.info...")
            should_break = not check_results_of_post_url(post_url_data['nijie'], site) or should_break
        elif site == "sankaku":
            log.info("hydownloader-test", "Testing sankaku...")
            should_break = not check_results_of_post_url(post_url_data['sankaku'], site) or should_break
        elif site == "idolcomplex":
            log.info("hydownloader-test", "Testing idolcomplex...")
            should_break = not check_results_of_post_url(post_url_data['idolcomplex'], site) or should_break
        elif site == "artstation":
            log.info("hydownloader-test", "Testing artstation...")
            should_break = not check_results_of_post_url(post_url_data['artstation'], site) or should_break
        elif site == "twitter":
            log.info("hydownloader-test", "Testing twitter...")
            should_break = not check_results_of_post_url(post_url_data['twitter'], site) or should_break
        elif site == "deviantart":
            log.info("hydownloader-test", "Testing deviantart...")
            should_break = not check_results_of_post_url(post_url_data['deviantart'], site) or should_break
        else:
            log.error("hydownloader-test", f"Site name not recognized: {site}, no testing done")
        if should_break:
            log.error("hydownloader-test", f"Stopping early due to errors while testing {site}, test environment kept for inspection")
            break
        clear_test_env()

@cli.command(help='Print a report about subscriptions and the URL queue, with a focus on finding dead, failing or erroneous subscriptions/URLs.')
@click.option('--path', type=str, required=True, help='Database path.')
@click.option('--verbose', type=bool, required=False, default=False, help='More details (listing individual subscriptions/URLs, not just aggregate numbers). Might produce a lot of output.')
def report(path: str, verbose: bool) -> None:
    log.init(path, True)
    db.init(path)
    db.report(verbose)

@cli.command(help='Acquire OAuth token needed for Pixiv.')
@click.option('--path', type=str, required=True, help='Database path.')
def pixiv_login(path: str) -> None:
    log.init(path, True)
    db.init(path)
    args = ['--cookies', db.get_rootpath()+'/cookies.txt']
    args += ['-o', 'cache.file='+db.get_rootpath()+'/gallery-dl-cache.db']
    args += ['oauth:pixiv']
    gallery_dl_utils.run_gallery_dl_with_custom_args(args)

@cli.command(help='Initialize hydownloader database folder.')
@click.option('--path', type=str, required=True, help='Database path.')
def init_db(path: str) -> None:
    log.init(path, True)
    db.init(path)

@cli.command(help='Queue multiple URLs at once.')
@click.option('--path', type=str, required=True, help='Database path.')
@click.option('--file', type=str, required=True, help='File with URLs, one URL in each line.')
@click.option('--additional-data', type=str, default=None, help='Additional metadata to associate with the downloaded files.')
@click.option('--metadata-only', type=bool, default=False, help='Only download metadata.')
@click.option('--overwrite-existing', type=bool, default=False, help='Overwrite existing files instead of skipping.')
@click.option('--filter', type=str, default=None, help='Filter.')
@click.option('--ignore-anchor', type=bool, default=False, help='Do not check or update download anchor file.')
@click.option('--max-files', type=int, default=None, help='Maximum number of files to download.')
def mass_add_urls(path: str, file_: str, additional_data: Optional[str], metadata_only: bool, overwrite_existing: bool, filter_: Optional[str], ignore_anchor: bool, max_files: Optional[int]) -> None:
    log.init(path, True)
    db.init(path)
    for line in open(file_, 'r'):
        line = line.strip()
        if line:
            db.add_or_update_urls([{
                'url': line,
                'time_added': time.time(),
                'additional_data': additional_data,
                'metadata_only': metadata_only,
                'overwrite_existing': overwrite_existing,
                'filter': filter_,
                'ignore_anchor': ignore_anchor,
                'max_files': max_files
                }])
            log.info("hydownloader-tools", f"Added URL: {line}")

@cli.command(help='Add multiple subscriptions at once.')
@click.option('--path', type=str, required=True, help='Database path.')
@click.option('--file', type=str, required=True, help='File with keywords, one query in each line.')
@click.option('--downloader', type=str, required=True, help='The downloader to use.')
@click.option('--additional-data', type=str, default=None, help='Additional metadata to associate with the downloaded files.')
@click.option('--paused', type=bool, default=False, help='Set added subscriptions to paused.')
@click.option('--filter', type=str, default=None, help='Filter.')
@click.option('--abort-after', type=int, default=20, help='Abort after this many seen files.')
@click.option('--max-files-initial', type=int, default=None, help='Maximum number of files to download on the first check.')
@click.option('--max-files-regular', type=int, default=None, help='Maximum number of files to download on a regular check.')
def mass_add_subscriptions(path: str, file_: str, downloader: str, additional_data: Optional[str], paused: bool, filter_: Optional[str], abort_after: int, max_files_initial: Optional[int], max_files_regular: Optional[int]) -> None:
    log.init(path, True)
    db.init(path)
    for line in open(file_, 'r'):
        line = line.strip()
        if line:
            db.add_or_update_subscriptions([{
                'keywords': line,
                'downloader': downloader,
                'time_created': time.time(),
                'additional_data': additional_data,
                'filter': filter_,
                'max_files_initial': max_files_initial,
                'max_files_regular': max_files_regular,
                'abort_after': abort_after,
                'paused': paused
                }])
            log.info("hydownloader-tools", f"Added subscription {line} with downloader {downloader}")

def main() -> None:
    cli()
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()

if __name__ == "__main__":
    main()