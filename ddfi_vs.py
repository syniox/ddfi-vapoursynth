from vapoursynth import core
import vapoursynth as vs
import mvsfunc as mvf

## Helper

def frame2clip(frame: vs.VideoFrame, fpsnum=1, fpsden=1, /, *, enforce_cache=True) -> vs.VideoNode:
    """ Ported from vsutils/cilps.py/frame2clip
    Converts a VapourSynth frame to a clip.
    :param frame:          The frame to convert.
    :param enforce_cache:  Forcibly add a cache, even if the ``vapoursynth`` module has this feature disabled.
    :return: A one-frame clip that yields the `frame` passed to the function.
    """
    bc = core.std.BlankClip(
            width=frame.width,
            height=frame.height,
            length=1,
            fpsnum=fpsnum,
            fpsden=fpsden,
            format=frame.format.id
            )
    frame = frame.copy()
    result = bc.std.ModifyFrame([bc], lambda n, f: frame.copy())
    if not core.add_cache and enforce_cache:
        result = result.std.Cache(size=1, fixed=True)
    return result

def mvflow(clip,analparams,blkmode,times):
    sup=core.mv.Super(clip)
    mvbw=core.mv.Analyse(sup,isb=True,**analparams)
    mvfw=core.mv.Analyse(sup,isb=False,**analparams)
    oput=core.mv.BlockFPS(clip,sup,mvbw,mvfw,mode=blkmode,num=clip.fps_num*times,den=clip.fps_den)
    return oput.std.AssumeFPS(clip)

# pos: 0-index
def mvinter(c0,c1,analparams,blkmode,times,pos):
    clip=c0+c1;
    clip=mvflow(clip,analparams,blkmode,times)
    return clip.get_frame(pos)


def Identical(c1,c2):
    """
    if(isinstance(c1,vs.VideoFrame)):
        c1=frame2clip(c1)
    if(isinstance(c2,vs.VideoFrame)):
        c2=frame2clip(c2)
    """
    comp=mvf.PlaneCompare(c1,c2,mae=False,rmse=False,psnr=True,cov=False,corr=False)
    return comp.get_frame(0).props.PlanePSNR>50


## Main
# can't have a fluent playback atm
# thr:      dedup thereshold(if more than $thr frames are the same, the program will ignore it)
# preset :  speed(fast(49fps)medium(47fps)slow(40fps)) therefore don't use fast
def ddfi(clip:vs.VideoNode,thr=2,preset="medium",
        pel=2,block=True,blkmode=None,blksize=None,search=None,overlap=0):
    funcname="ddfi"
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcname+': This is not a clip!')
    if thr<2 or thr>3:
        raise TypeError(funcname+': thr should be 2\\3.')
    pnum={
            'fast':0,
            'medium':1,
            'slow':2
            }.get(preset)
    if pnum==None:
        raise TypeError(funcname+': Preset should be fast\\medium\\slow.')
    if search is None: search=[0,3,3][pnum]
    if blkmode is None: blkmode=[0,0,3][pnum]
    if blksize is None: blksize=[32,16,8][pnum]
    analparams={'overlap':overlap,'search':search,'blksize':blksize}

    def mod_thr2(n,f): # TODO 开场黑屏
        c0=frame2clip(f[0])
        c1=frame2clip(f[1])
        c2=frame2clip(f[2])
        b01=Identical(c0,c1)
        b12=Identical(c1,c2)
        if b01 and not b12:
            return mvinter(c0,c2,analparams,blkmode,2,1)
        else:
            return f[1]

    if thr==2:
        blk=core.std.BlankClip(clip,length=1)
        c0=clip+blk+blk
        c1=blk+clip+blk
        c2=blk+blk+clip
        oput=c0.std.ModifyFrame([c0,c1,c2],mod_thr2)
        return oput
    else:
        raise TypeError(funcname+'unimplemented thr.(2 only)')
