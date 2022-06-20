from vapoursynth import core
import vapoursynth as vs
import mvsfunc as mvf
from functools import partial

## main function: ddfi_mv(wip), ddfi_svp(realtime playback)

## Helper

def mvflow(clip,analparams,blkmode,times):
    sup=core.mv.Super(clip)
    mvbw=core.mv.Analyse(sup,isb=True,**analparams)
    mvfw=core.mv.Analyse(sup,isb=False,**analparams)
    oput=core.mv.BlockFPS(clip,sup,mvbw,mvfw,mode=blkmode,num=clip.fps_num*times,den=clip.fps_den)
    return oput.std.AssumeFPS(clip)

def svpflow(clip,preset="fast"):
    superstr='{pel:1,gpu:1}'
    vectorstr='{block:{w:32,h:32,overlap:0},main:{search:{type:2},bad:{sad:2000}}}'
    smoothstr='{rate:{num:2,den:1,abs:false},algo:2,gpuid:0}'
    sup=core.svp1.Super(clip,superstr)
    vec=core.svp1.Analyse(sup["clip"],sup["data"],clip,vectorstr)
    oput=core.svp2.SmoothFps(clip,sup["clip"],sup["data"],vec["clip"],vec["data"],smoothstr)
    oput=core.std.AssumeFPS(oput,fpsnum=oput.fps_num,fpsden=oput.fps_den)
    return oput

## Core

def ddfi_core_m(clip:vs.VideoNode,smooth:vs.VideoNode,thr=2):
    # TODO try to find a good value
    isstatic=lambda f: bool(f.props.DiffAverage<2e-3) 
    def set_static(n,f):
        fout=f.copy()
        fout.props['DiffAverage']=0
        return fout
    def mod_thr2(n,f,clip,smooth):
        if isstatic(f[0]) and not isstatic(f[1]):
            return smooth
        return clip

    if thr==2:
        mmask=core.motionmask.MotionMask(clip,th1=20)
        mmask=mmask.std.PlaneStats(plane=0,prop='Diff')
        blk=core.std.BlankClip(clip,length=1)
        blk=blk.std.ModifyFrame(blk,set_static)
        m0=mmask         # 前向diff
        m1=mmask[1:]+blk # 后向diff
        fn=partial(mod_thr2,clip=clip,smooth=smooth)
        oput=clip.std.FrameEval(fn,prop_src=[m0,m1])
        return oput
    else:
        raise TypeError(funcname+'unimplemented thr.(2 only)')

# WIP, 164fps
def ddfi_core_f(clip:vs.VideoNode,smooth:vs.VideoNode,thr=2):
    def set_PSNR(n,f,v):
        fout=f.copy()
        fout.props['PlanePSNR']=v
        return fout

    def mod_thr2(n,f,clip,smooth):
        if f[0].props.PlanePSNR>50 and f[1].props.PlanePSNR<=50:
            return smooth
        return clip

    if thr==2: # 前向diff
        blk=core.std.BlankClip(clip,length=1)
        blk=blk.std.ModifyFrame(blk,partial(set_PSNR,v=100))
        t0=blk+clip
        base=mvf.PlaneCompare(clip,t0,mae=False,rmse=False,psnr=True,cov=False,corr=False)
        id01=base
        id12=base[1:]+blk
        fn=partial(mod_thr2,clip=id12,smooth=smooth)
        oput=id12.std.FrameEval(fn,prop_src=[id01,id12])
        return oput
    else:
        raise TypeError(funcname+'unimplemented thr.(2 only)')


## Wrapper

# thr:      dedup thereshold(if more than $thr frames are the same, the program will ignore it)
# preset :  speed(fast,medium,slow) fast has a bad trade-off, unrecommended

# mv version can't have a fluent playback atm
def ddfi_mv(clip:vs.VideoNode,thr=2,preset="medium",pel=2,
        block=True,blkmode=None,blksize=None,search=None,overlap=None):
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
    if overlap is None: overlap=[0,0,2][pnum]
    if search is None: search=[0,3,3][pnum]
    if blksize is None: blksize=[32,16,8][pnum]
    if blkmode is None: blkmode=[0,0,3][pnum]
    analparams={'overlap':overlap,'search':search,'blksize':blksize}

    smooth=mvflow(clip,analparams,blkmode,2)[1::2]
    return ddfi_core(clip,smooth,thr)

def ddfi_svp(clip:vs.VideoNode,thr=2,preset="fast"): # TODO: preset options
    funcname="ddfi"
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcname+': This is not a clip!')
    if thr<2 or thr>3:
        raise TypeError(funcname+': thr should be 2\\3.')
    clip=core.resize.Point(clip,format=vs.YUV420P8)
    smooth=svpflow(clip)[1::2]
    return ddfi_core(clip,smooth,thr)
