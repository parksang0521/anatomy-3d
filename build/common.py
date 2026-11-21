import numpy as np,struct,json
def load(f):
    b=open(f,'rb').read(); n=struct.unpack('<I',b[80:84])[0]
    a=np.frombuffer(b[84:84+n*50],dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]))
    return a['v'].reshape(-1,3).astype(np.float64)
NAMES={l.split('\t')[0]:l.rstrip('\n').split('\t')[1] for l in open('/tmp/stlnames')}
def to_ha(v): # raw axes: x, z, -y
    return np.stack([v[:,0],v[:,2],-v[:,1]],1)/1000.0
