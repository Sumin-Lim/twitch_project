import requests
import json 
import pickle as pkl 
from glob import glob 
from pathlib import Path
from tqdm import tqdm
import time

from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def get_twitch_token(twitch_info):
    url = 'https://id.twitch.tv/oauth2/token'
    r = requests.post(url, 
            data={'client_id': info['Client ID'],
                'client_secret': info['Client Secret'],
                'grant_type': 'client_credentials'})

    res = r.json()
    return res


def get_followers():
    if not Path('temp/streamers.pkl').exists():
        streams = glob('streams/*')
        streamers = [{'channel_id': x.replace('streams/', '').replace('.pkl', '').split('_')[0],
            'channel_name': ''.join(x.replace('streams/', '').replace('.pkl', '').split('_')[1:])}
            for x in streams]
        pkl.dump(streamers, open('temp/streamers.pkl', 'wb'))

    else:
        streamers = pkl.load(open('temp/streamers.pkl', 'rb'))

    twitch_info = json.load(open('temp/twitch_info.json', 'r'))
    twitch_token = json.load(open('temp/twitch_token.json', 'r'))

    num_streamers = len(streamers)

    crawled = glob('followers/*')
    crawled = [x.replace('followers/', '').split('_')[0] for x in crawled]
    crawled = [int(x) for x in crawled]
    done = max(crawled)

    for idx, streamer in tqdm(enumerate(streamers), total=num_streamers):
        if idx < done:
            continue 

        channel_id = streamer['channel_id']
        URL = f'https://api.twitch.tv/helix/channels/followers?broadcaster_id={channel_id}'
        r = requests.get(URL, headers={'Authorization': f'Bearer {twitch_token["access_token"]}',
                                       'Client-Id': twitch_info['Client ID']})

        if r.status_code == 200:
            res = r.json()
            pkl.dump(res, open(f'followers/{idx}_{streamer["channel_id"]}_{streamer["channel_name"]}.pkl', 'wb'))
            #time.sleep(1)
        else:
            print(r.status_code)
            print(r.status_message)
            break

def get_about():
    channel_names = pkl.load(open('temp/df_target_game_streamings_channel_names.pkl', 'rb'))
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    driver = webdriver.Chrome(ChromeDriverManager().install(),
                              seleniumwire_options={'disable_encoding': True,
                                                    'enable_har': True},
                              options=options)

    total = len(channel_names)

    crawled = glob('twitch_data/*')
    if len(crawled) != 0:
        crawled = [x.split('/')[-1].split('_')[0] for x in crawled]
        crawled = max([int(x) for x in crawled]) - 1
    else:
        crawled = -1 

    total_time = 0
    print('current crawled:', crawled)

    for idx, channel_name in enumerate(channel_names):
        if idx < crawled:
            continue 

        cnt_job = 0
        save_path = f'twitch_data/{idx}_{channel_name}'
        Path(save_path).mkdir(parents=True, exist_ok=True)
        driver.get(f'https://twitch.tv/{channel_name}/about')
        har_about = json.loads(driver.har)
        har_about_entries = har_about['log']['entries'].copy()
        driver.backend.storage.clear_requests()

        cnt_about = 0
        start_time = time.time()

        for jdx, entry in enumerate(har_about_entries):
            url = entry['request']['url']
            if (url.startswith('https://gql')) and (entry['request']['method'] == 'POST'):
                temp_text = entry['request']['postData']['text']
                if ('Panel' in temp_text):
                    pkl.dump(entry, open(save_path+f'/about_{jdx}.pkl', 'wb'))
                    cnt_about += 1

        #driver.get(f'https://twitch.tv/{channel_name}/videos?filter=all&sort=time')
        #har_video = json.loads(driver.har)
        #har_video_entries = har_video['log']['entries']

        #cnt_video = 0
        #for jdx, har_entry in enumerate(har_video_entries):
        #    url = har_entry['request']['url']
        #    if (url.startswith('https://gql')) and (har_entry['request']['method'] == 'POST'):
        #        if har_entry['response']['content']['mimeType'] != 'application/json':
        #            continue

        #        entry_text = har_entry['request']['postData']['text']
        #        if 'VideoPreviewCard' in entry_text:
        #            pkl.dump(har_entry, open(save_path+f'/video_{jdx}.pkl', 'wb'))
        #            cnt_video += 1

        cnt_job += 1
        elapsed_time = time.time() - start_time
        total_time += elapsed_time
        mean_time = total_time / cnt_job
        print(f'HAR: [about] {cnt_about} / {len(har_about_entries)}')
        #print(f'HAR: [video] {cnt_video} / {len(har_video_entries)}')
        print(f'[{idx} / {total}, {(idx/total)*100}%] channel_name: {channel_name}')
        print(f'elapsed time: {elapsed_time}s , total time: {total_time}s')
        print(f'mean time: {mean_time}s, ETA: {mean_time*(total-cnt_job)}s \n')


if __name__ == '__main__':
    get_about()
