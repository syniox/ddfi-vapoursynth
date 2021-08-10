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

def mvdedup(clip,analparams,blkmode,times):
    if times==None:
        times=clip.num_frames-1
    #print("[debug] times: ",times)
    clip=clip[0]+clip[times]
    sup=core.mv.Super(clip)
    mvbw=core.mv.Analyse(sup,isb=True,**analparams)
    mvfw=core.mv.Analyse(sup,isb=False,**analparams)
    oput=core.mv.BlockFPS(clip,sup,mvbw,mvfw,mode=blkmode,num=clip.fps_num*times,den=clip.fps_den)
    return oput.std.AssumeFPS(clip)

def mvflow(clip,analparams,blkmode,times):
    sup=core.mv.Super(clip)
    mvbw=core.mv.Analyse(sup,isb=True,**analparams)
    mvfw=core.mv.Analyse(sup,isb=False,**analparams)
    oput=core.mv.BlockFPS(clip,sup,mvbw,mvfw,mode=blkmode,num=clip.fps_num*times,den=clip.fps_den)
    return oput.std.AssumeFPS(clip)

def Identical(c1,c2):
    """
    if(isinstance(c1,vs.VideoFrame)):
        c1=frame2clip(c1)
    if(isinstance(c2,vs.VideoFrame)):
        c2=frame2clip(c2)
    """
    comp=mvf.PlaneCompare(c1,c2,mae=False,rmse=False,psnr=True,cov=False,corr=False)
    return comp.get_frame(0).props.PlanePSNR>60


## Main
# thr:      dedup thereshold(if more than $thr frames are the same, the program will ignore it)
def ddfi(clip:vs.VideoNode,thr=2,preset="fast",
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
    c0=frame2clip(clip.get_frame(0),clip.fps_num,clip.fps_den)
    oput=c0
    dup_cnt=0
    for (i,f1) in enumerate(clip.frames()):
        print("processing ",i)
        c1=frame2clip(f1,clip.fps_num,clip.fps_den)
        if not Identical(c0,c1):
            if dup_cnt==0:
                oput+=c1
            elif dup_cnt<thr: ### TODO: SCDetect
                oput+=(mvflow(c0+c1,analparams,blkmode,dup_cnt+1))[1::]
            else:
                oput+=c0*dup_cnt+c1
            dup_cnt=0
        else:
            dup_cnt+=1;
        c0=c1
    if dup_cnt>0:
        oput+=c0*dup_cnt
    return oput
