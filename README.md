## ddfi-vapoursynth
dedup frame interpolation.

### Sample Usage

mpv:
```python
from vapoursynth import core
import ddfi_vs

clip=core.std.AssumeFPS(clip,fpsnum=24000,fpsden=1001)
ddfi_vs.ddfi_svp(clip).set_output()
```


### Credits

Original Idea: [Mr-z-2697/ddfi](github.com/Mr-Z-2697/ddfi)
