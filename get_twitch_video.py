from tqdm import tqdm
from glob import glob 
import pickle as pkl 
from pathlib import Path
import time

import asyncio
from requests_html import AsyncHTMLSession

INTERVAL = 5
asession = AsyncHTMLSession()
Path('twitch_video_links/').mkdir(exist_ok=True)

async def get_video(channel):
    res = []
    url = f'https://twitch.tv/{channel}/videos?filter=all&sort=time'
    r = await asession.get(url)
    await r.html.arender(scrolldown=5000)

    videos = r.html.find('div.Layout-sc-1xcs6mc-0.iPAXTU')
    link_path = 'a.ScCoreLink-sc-16kq0mq-0.eYjhIv.ScCoreLink-sc-bhsr9c-0.jYyMcQ.tw-link'
    date_path = 'img.tw-image'
    view_path = 'div.ScMediaCardStatWrapper-sc-anph5i-0.eBmJxH.tw-media-card-stat'

    print('channel_name:', channel, 'len(videos):', len(videos))
    for video in videos:
        date_elems = video.find(date_path)

        for date_elem in date_elems:
            if 'title' in date_elem.attrs.keys():
                date = date_elem.attrs['title']

        temp = {}
        temp['channel_name'] = channel
        temp['video_link'] = video.absolute_links
        temp['video_date'] = date

        stat = [x.text for x in video.find(view_path)]

        temp['video_length'] = stat[0]
        temp['video_views'] = stat[1]
        res.append(temp)

    pkl.dump(res, open(f'twitch_video_links/{channel}.pkl', 'wb'))
    await asyncio.sleep(1)



async def get_videos():
    channel_names = pkl.load(open('temp/df_target_game_streamings_channel_names.pkl', 'rb'))
    crawled = glob(f'twitch_video_links/*.pkl')
    crawled = [x.split('/')[-1].replace('.pkl', '') for x in crawled]

    to_crawl = list(set(channel_names).difference(crawled))


    for i in tqdm(range(0, len(to_crawl), INTERVAL)):
        start_time = time.time()
        tasks = [asyncio.ensure_future(get_video(channel)) for channel in to_crawl[i: i+INTERVAL]]
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)


if __name__ == '__main__':
    ioloop = asyncio.get_event_loop()
    ioloop.run_until_complete(get_videos())
