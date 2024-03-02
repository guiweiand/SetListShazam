import nest_asyncio
nest_asyncio.apply()

import json
from pytube import YouTube
from pydub import AudioSegment
from pydub.utils import make_chunks
import asyncio
from shazamio import Shazam
import time

"""
This class represents a music setlist generator.
From a video URL a setlist list with timestamps is generated.
"""
class SetList:
    """
    Initializes the generator with URL attribute.
    output_folder, filename and chunk_length are optional attributes.
    """
    def __init__(self, URL, output_folder="", filename="filename", chunk_length=1000*30, sleep_time=5):
        self.URL = URL
        self.output_folder = output_folder
        self.filename = filename
        self.chunk_length = chunk_length
        self.sleep_time = sleep_time

    def seconds_to_hms(self, total_seconds):
        # Calculate hours, minutes, and remaining seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return int(hours), int(minutes), int(seconds)

    def timestamp_def(self, hours, minutes, seconds):
        if minutes < 10:
            minutes = '0' + str(minutes)
        if seconds < 10:
            seconds = '0' + str(seconds)
        return '{hours}:{minutes}:{seconds}'.format(hours=hours, minutes=minutes, seconds=seconds) if hours>0 else '{minutes}:{seconds}'.format(minutes=minutes, seconds=seconds)

    # Download file from YouTube Url
    def download_audio_from_youtube(self):
        try:
            # Create a YouTube object
            yt = YouTube(self.URL)

            # Get video info
            video_title = yt.title
            video_author = yt.author
            video_length = yt.length

            # Get the audio stream with the highest quality
            audio_stream = yt.streams.filter(only_audio=True).first()

            # Download the audio stream to the specified output path
            audio_stream.download(self.output_folder, filename=self.filename)

            print(f"Audio downloaded successfully")

            return {'video_title': video_title, 'video_author': video_author, 'video_length': video_length}

        except Exception as e:
            print(f"Error: {e}")
            quit()

    # Chunk the audio
    def chunk_audio(self):
        print(self.filename)
        myaudio = AudioSegment.from_file(self.filename)
        chunks = make_chunks(myaudio, self.chunk_length)

        #Export all of the individual chunks
        chunk_names = list()
        for i, chunk in enumerate(chunks):
            chunk_name = "chunk{0}.mp4".format(i)
            chunk_names.append(chunk_name)
            print("exporting", chunk_name)
            chunk.export(chunk_name)
        return chunk_names

    # Get chunk data from Shazam (Operational)
    def get_shazam_data(self, chunk_names):
        # get data for all the exports
        async def main(file_name):
            shazam = Shazam()
            out = await shazam.recognize_song(file_name)
            #print(json.dumps(out, indent=4))
            #print(out)
            return out

        results = dict()

        # TODO create a binary search algorithm to get the track between a half and a quarter if the same track name check also the middle
        # if same track name too so all this quarter is the same song. if not, keep track of track name and continue binary search untill
        # all timeline is populated
        # this may decrease processing by 10x

        # create an array for every sample (ex. for every 10 sec). and append with the dictionary with all the information
        # then check the title of the samples

        for name in chunk_names:
            try:
                #loop = asyncio.get_event_loop()
                asyncio.set_event_loop(asyncio.SelectorEventLoop())
                results[name] = asyncio.get_event_loop().run_until_complete(main(name))
                #results[name] = loop.run_until_complete(main(name))
                print('getting song data from chunk {name}'.format(name=name))
            except Exception as e:
                print(f'got error in chunk {name}: {e}')
                results[name] = f'Error!!! {e}'
            time.sleep(self.sleep_time)
        return results

    def setlist_intelligence(self, results):
        # Setlist Intelligence

        track_info = list()
        title_exists = 0
        for i in range(len(results)):
            # gets chunk's track names
            if str(results['chunk{i}.mp4'.format(i=i)]).startswith('Error') or 'track' not in results['chunk{i}.mp4'.format(i=i)] or 'title' not in results['chunk{i}.mp4'.format(i=i)]['track']:
                track_name = ''
            else:
                track_name = results['chunk{i}.mp4'.format(i=i)]['track']['title']
                title_exists = 1
            # gets chunk's track author
            if str(results['chunk{i}.mp4'.format(i=i)]).startswith('Error') or 'track' not in results['chunk{i}.mp4'.format(i=i)] or 'subtitle' not in results['chunk{i}.mp4'.format(i=i)]['track']:
                track_author = ''
            else:
                track_author = results['chunk{i}.mp4'.format(i=i)]['track']['subtitle']

            track_info.append({'name': track_name, 'author': track_author})

        #print(track_info)

        if title_exists == 0:
            print('No titles found!!')
            quit()

        # gets setlist
        start_idx = 0
        setlist = list()
        idx_ = len(track_info)

        # populates array end
        if track_info[-1]['name'] == '':
            for idx in range(len(track_info)-1, 0, -1):
                if track_info[idx]['name'] != '':
                    idx_ = idx
                    for aux_idx in range(idx+1, len(track_info)):
                        track_info[aux_idx] = track_info[idx]
                    break
        #print(track_info)

        #populate array gaps
        for idx in range(idx_-1, 0, -1):
            if track_info[idx-1]['name'] == '':
                track_info[idx-1] = track_info[idx]

        #print(track_info)

        for end_idx in range(1, len(track_info)):
            if track_info[end_idx] != track_info[end_idx-1]:
                hours, minutes, seconds = self.seconds_to_hms((start_idx+1) * self.chunk_length / 1000)
                song_start = self.timestamp_def(hours, minutes, seconds)
                hours, minutes, seconds = self.seconds_to_hms((end_idx+1) * self.chunk_length / 1000)
                song_end = self.timestamp_def(hours, minutes, seconds)

                setlist.append('{song_start} - {song_end}: {track_name} - {track_author}'.format(song_start=song_start, song_end=song_end, track_name=track_info[start_idx]['name'], track_author=track_info[start_idx]['author']))
                start_idx = end_idx

        hours, minutes, seconds = self.seconds_to_hms((start_idx+1) * self.chunk_length / 1000)
        song_start = self.timestamp_def(hours, minutes, seconds)
        hours, minutes, seconds = self.seconds_to_hms((len(track_info)+1) * self.chunk_length / 1000)
        song_end = self.timestamp_def(hours, minutes, seconds)
        setlist.append('{song_start} - {song_end}: {track_name} - {track_author}'.format(song_start=song_start, song_end=song_end, track_name=track_info[-1]['name'], track_author=track_info[-1]['author']))

        return setlist

    def print_setlist(self, setlist):
        setlist_ts = ''
        print()
        for timestamp_info in setlist:
            print(timestamp_info)
            setlist_ts += timestamp_info + '\n'
        return setlist_ts