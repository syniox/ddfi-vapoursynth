## ddfi-vapoursynth
dedup frame interpolation.

### Sample Usage

mpv:
```python
from vapoursynth import core
import ddfi_vs

clip=core.std.AssumeFPS(video_in,fpsnum=24000,fpsden=1001)
ddfi_vs.ddfi_svp(clip).set_output()
```
### Known Issues

1. thr not working

### Credits

Original Idea: [Mr-z-2697/ddfi](github.com/Mr-Z-2697/ddfi)
