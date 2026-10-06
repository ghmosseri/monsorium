# Multimedia videos

The Multimedia gallery has five framed slots. Each one plays the file with
its slot's name:

| Slot | File |
|---|---|
| XV | `multimedia-01.mp4` |
| XVI | `multimedia-02.mp4` |
| XVII | `multimedia-03.mp4` |
| XVIII | `multimedia-04.mp4` |
| XIX | `multimedia-05.mp4` |

Upload a video into this folder under one of those names and its frame
starts playing it. Slots without a file show as a blank frame marked
"Forthcoming".

- Use MP4 (H.264 video, AAC audio) so it plays in every browser. WebM also
  works: name it `multimedia-0N.webm` instead (an MP4 with the same number wins).
- Frames are 16:9; other shapes are cropped to fill the frame.
- Keep each file under 100 MB (GitHub rejects larger files); for longer
  pieces, compress first or ask to switch the slot to a YouTube/Vimeo embed.
- Set the title, month/year and runtime in the slot's caption in `index.html`
  (search for the slot's numeral, e.g. `XVII.`).
