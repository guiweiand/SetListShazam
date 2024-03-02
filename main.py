# Main
from set_list import SetList

video_url = "https://www.youtube.com/watch?v=YgOmUZx-pL4&t=2800s"
output_folder = ""
filename = "filename"
chunk_length = 1000*30 #ms
sleep_time = 5 #s

setlist = SetList(URL=video_url, filename=filename)

# Download Yt video
video_info = setlist.download_audio_from_youtube()

# Chunk audio
chunk_names = setlist.chunk_audio()

# Discover Songs
results = setlist.get_shazam_data(chunk_names)

# Setlist Intelligence
setlist_results = setlist.setlist_intelligence(results)

# Print Result
setlist.print_setlist(setlist_results)