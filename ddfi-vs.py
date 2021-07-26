from vapoursynth import core
import vapoursynth as vs

## Helper
def mvdedup(clip,analparams,blkmode):
	times=clip.num_frames-1
	#print("[debug] times: ",times)
	clip=clip[0]+clip[times]
	sup=core.mv.Super(clip)
	mvbw=core.mv.Analyse(sup,isb=True,**analparams)
	mvfw=core.mv.Analyse(sup,isb=False,**analparams)
	oput=core.mv.BlockFPS(clip,sup,mvbw,mvfw,mode=blkmode,num=clip.fps_num*times,den=clip.fps_den)
	return oput.std.AssumeFPS(clip)

def Identical(c1,c2):
	comp=mvf.PlaneCompare(clip1,clip2,mae=False,rmse=False,psnr=True,cov=False,corr=False)
	return comp[0].props.PlanePSNR>60

## thr(2,3): dedup thereshold
def ddfi(clip:vs.VideoNode,thr=2,preset="fast",
		pel=2,block=True,blkmode=None,blksize=None,search=None,overlap=0):
	funcname="ddfi"
	if not isinstance(clip, vs.VideoNode):
		raise TypeError(funcname+': This is not a clip!')
	if thr<2 or thr>3:
		raise TypeError(funcname+': thr should be 2\\3.')
	if preset=='fast':
		pnum=0
	elif preset=='medium':
		pnum=1
	elif preset=='slow':
		pnum=2
	else:
		raise TypeError(funcname+': Preset should be fast\\medium\\slow.')
	if search is None: search=[0,3,3][pnum]
	if blkmode is None: blkmode=[0,0,3][pnum]
	if blksize is None: blksize=[32,16,8][pnum]
	analparams={'overlap':overlap,'search':search,'blksize':blksize}
	return clip

