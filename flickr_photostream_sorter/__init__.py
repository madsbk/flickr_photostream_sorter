from datetime import timedelta
from datetime import datetime
from os import environ
import json
import time

import flickrapi

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

flickr_key = environ['FLICKR_API_KEY']
flickr_secret = environ['FLICKR_SECRET']
joined_flickr = environ.get('FLICKR_JOINED_DATE', None)

if joined_flickr is not None:
    joined_flickr = datetime.strptime(joined_flickr, DATE_FORMAT)

def main():

    flickr = flickrapi.FlickrAPI(flickr_key, flickr_secret, format='json')

    (token, frob) = flickr.get_token_part_one(perms='write')

    if not token:
        raw_input("Press ENTER after you authorized this program")
        token = flickr.get_token_part_two((token, frob))

    all_photos = []

    print '-----> Fetching all photos'

    total_pages = 1
    page = 1
    while page <= total_pages:
        print '       Fetching page {} out of {}'.format(page, total_pages)
        res = json.loads(flickr.photos_search(user_id='me', page=page, per_page=500, extras='date_upload,date_taken')[14:-1])
        total_pages = res['photos']['pages']
        page = res['photos']['page'] + 1
        photos = res['photos']['photo']
        all_photos.extend(photos)

    # Handle photos before Flickr joined date
    if joined_flickr is not None:
        def datetaken(photo):
            return datetime.strptime(photo['datetaken'], DATE_FORMAT)
        photos_before_joined = []
        photos_after_joined = []
        for p in all_photos:
            if datetaken(p) <= joined_flickr:
                photos_before_joined.append(p)
            else:
                photos_after_joined.append(p)
        photos_before_joined = sorted(photos_before_joined, key=datetaken)
        for i, p in enumerate(photos_before_joined):
            p['datetaken'] = (joined_flickr + timedelta(0,i)).strftime(DATE_FORMAT)
        all_photos = photos_before_joined + photos_after_joined

    print '-----> Updating dates'

    for photo in  all_photos:
        date_taken = photo['datetaken']
        date_taken = datetime.strptime(date_taken, DATE_FORMAT)
        date_posted = int(photo['dateupload'])
        date_posted = datetime.fromtimestamp(date_posted)
        if date_posted != date_taken:
            print '       Updating "{}": change date posted from {} to {}'.format(photo['id'], date_posted, date_taken)
            new_date_posted = time.mktime(date_taken.timetuple())
            res = flickr.photos_setDates(photo_id=photo['id'], date_posted=new_date_posted)
            if "fail" in res:
                print res
        else:
            print '       Skipping "{}": dates match'.format(photo['id'])

    print '-----> Done!'

if __name__ == "__main__":
    main()
