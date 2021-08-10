from vapoursynth import core
import vapoursynth as vs
import mvsfunc as mvf

## Helper

def svpflow(clip,preset="fast"):
    #vectorstr='{block:{w:16,overlap:0},main:{search:{type:2,distance:-6,satd:false},distance:0,bad:{sad:2000}}}'
    superstr='{pel:1,gpu:1}'
    vectorstr='{block:{w:32,h:32,overlap:0},main:{search:{type:2},bad:{sad:2000}}}'
    smoothstr='{rate:{num:2,den:1,abs:false},algo:2,gpuid:0}'
    sup=core.svp1.Super(clip,superstr)
    vec=core.svp1.Analyse(sup["clip"],sup["data"],clip,vectorstr)
    oput=core.svp2.SmoothFps(clip,sup["clip"],sup["data"],vec["clip"],vec["data"],smoothstr)
    oput=core.std.AssumeFPS(oput,fpsnum=oput.fps_num,fpsden=oput.fps_den)
    return oput

## Main
# can't have a fluent playback atm
# thr:      dedup thereshold(if more than $thr frames are the same, the program will ignore it)
# preset :  speed(fast(49fps)medium(47fps)slow(40fps)) therefore don't use fast
def ddfi(clip:vs.VideoNode,thr=2):
    funcname="ddfi"
    if not isinstance(clip, vs.VideoNode):
        raise TypeError(funcname+': This is not a clip!')
    if thr<2 or thr>3:
        raise TypeError(funcname+': thr should be 2\\3.')
    clip=clip.resize.Point(format=vs.YUV420P16)
    smooth=svpflow(clip)[1::2]
    def mod_thr2(n,f): # TODO 开场黑屏
        if n<=1:
            return f[1-n]
        if f[1].props.PlanePSNR>50 and f[2].props.PlanePSNR<=50:
            return f[3]
        else:
            return f[1]

    if thr==2:
        blk=core.std.BlankClip(clip,length=1)
        c0=clip+blk+blk
        c1=blk+clip+blk
        c2=blk+blk+clip
        id01=mvf.PlaneCompare(c0,c1,mae=False,rmse=False,psnr=True,cov=False,corr=False)
        id21=mvf.PlaneCompare(c2,c1,mae=False,rmse=False,psnr=True,cov=False,corr=False)
        oput=c1.std.ModifyFrame([c1,id01,id21,smooth],mod_thr2)
        if oput.num_frames>1:
            return oput.std.Trim(last=oput.num_frames-2)
        return oput
    else:
        raise TypeError(funcname+'unimplemented thr.(2 only)')
