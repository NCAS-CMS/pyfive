from pathlib import Path
from matplotlib import pyplot as plt
import numpy as np

dimensions = np.array([40, 1920, 2560])
requests = 3*2*2, 3*199*2,3*199*299,1920,40*199*199,1920*2560
big_chunks = np.array([10,480,640])
small_chunks = np.array([4, 113, 128])


def get_data(fname, big=True):

    big, small = {}, {}
    block = False
    with open(fname,'r') as f:
        for line in f:

            if line.startswith('bnl'):
                if '-def' in line:
                    inplay = big
                else:
                    inplay = small

            if line.startswith('Reduction over'):
                block=True
                r1,r2,r3 = [],[],[]
                key = line[line.find('over')+5:line.find('chunks')]
                print(key)
                continue
            if line.startswith('Overall'):
                continue
            if block:
                try:
                    v, t = tuple([x.strip() for x in line.split(':')])
                    if t.startswith('Active Regular'):
                        r2.append(v)
                    elif t.startswith('Regular'):
                        r1.append(v)
                    elif t.startswith('Active Remote'):
                        r3.append(v)
                except:
                    inplay[key]=r1,r2,r3
                    print('Skipping End of Block')
                    block = False
            else:
                print('Skipping')
            continue
    inplay[key]=r1,r2,r3
    print(big)
    print(small)
    print(big.keys(), small.keys())
    return small, big

def do_all(hs,hb,ws,wb):

    titles = ['Home - Small Chunks',
              'Home - Big Chunks',
              'Uni - Small Chunks',
              'Uni - Big Chunks']

    fig, axes = plt.subplots(nrows=2, ncols=2)  
    fig.set_size_inches(8, 8)
    axes = axes.flatten()

    for a, d, t in zip(axes, [hs,hb,ws,wb], titles):
        do_plot(a, d, t)
    plt.tight_layout()
    plt.show()

def do_plot(ax, data, t):

    def stats4(d1):
        dd = np.array([float(v) for v in d1])
        return [np.mean(dd),np.min(dd),np.max(dd)]

    keys = list(data.keys())

    x = []
    regular, local, remote = [], [], []
    for k in keys:
        # three time series for each key
        reg, loc, rem = data[k]
        sreg, sloc, srem = stats4(reg), stats4(loc), stats4(rem)
        regular.append(sreg)
        local.append(sloc)
        remote.append(srem)
        x.append(float(k))

    delta = 0
    all = True
    for d,c in zip([regular, local, remote],['g','r','b']):
        x=np.array(x)+delta*0.2
        y = [r[0] for r in d]
        err = [[r[0]-r[1] for r in d],[r[2]-r[0] for r in d]]
        if c == 'b' or all:
            ax.errorbar(x, y, fmt='o', yerr=err, color=c)
        delta+=1
    ax.set_title(t)
    ax.set_xlabel('Chunks Processed')
    ax.set_ylabel('s')

    if t.find('Small') > 0:
        cv = np.prod(small_chunks)*4/1e6
    else:
        cv = np.prod(big_chunks)*4/1e6
    v = np.prod(dimensions)*4/1e6
    r = v/cv
    print(f'Chunk volume {cv}Mb, Dataset volume {v}Mb - ratio {r}')


    def c2v(x):
        return x*cv 
    def v2c(x):
        return x/cv
    

    tax = ax.secondary_xaxis(-0.2, functions=(c2v,v2c))
    tax.set_xlabel('Reductionist Read (MB)')

            

if __name__=="__main__":
    mypath = Path(__file__).parent
    fname = mypath/'work_experiments_bnl.txt'
    ws, wb = get_data(fname)
    fname = mypath/'home_experiments_bnl.txt'
    hs, hb = get_data(fname)
    do_all(hs, hb, ws, wb)


