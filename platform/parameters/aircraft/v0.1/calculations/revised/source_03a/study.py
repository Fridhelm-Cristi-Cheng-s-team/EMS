"""Read-only engineering study; run python study.py > results.json."""
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.integrate import simpson
from scipy.optimize import least_squares

cfg = json.loads(Path(__file__).with_name("candidates.json").read_text())
g = cfg["g"]
eta = np.array(cfg["efficiency"])
axis = np.radians(1)
zero = np.zeros(2)
b_cases = [(37, 1500, 0, 471), (34, 900, 2.5, 471), (34, 900, 5, 471),
           (36, 1000, -1.4, 471), (37, 1500, 0, 435), (37, 1500, 0, 500),
           (37, 0, 0, 471), (37, 2500, 0, 471), (32, 1500, 0, 471)]
labels = ["cruise", "climb", "high climb", "descent", "435 kg", "500 kg",
          "sea level", "2500 m", "32 m/s comparison"]


def density(h):
    ratio = 1 - 0.0065*h/288.15
    return 101325/(287.05287*288.15)*ratio**(g/(287.05287*0.0065)-1)


def geometry(p):
    s, ar, lam = p[:3]
    b = np.sqrt(s*ar)
    root = 2*s/(b*(1+lam))
    c = 2*root*(1+lam+lam**2)/(3*(1+lam))
    return b, root, c


def mass(p, m, cg_shift=0, inertia_scale=1):
    _, _, c = geometry(p)
    a = np.array(cfg["mass_rows"], float)
    nominal = np.average(a[:, 1:3], axis=0, weights=a[:, 0])
    a[-1, 0] = 40 + min(0, m-471)
    if m > 471:
        a = np.vstack((a, [m-471, *nominal, 0]))
    loci = a[:, 1:3]*[-c, c]
    cg = np.average(loci, axis=0, weights=a[:, 0])
    cg[0] -= cg_shift*c
    inertia = sum(a[:, 0]*((a[:, 3]*c)**2+np.sum((loci-cg)**2, axis=1)))
    return cg, inertia*inertia_scale


def derivatives(p, mod=(1, 1, 1)):
    aw = 2*np.pi/(1+2/(0.94*p[1]))
    tail = .90*3.7*.22
    return [aw+.60*tail, 2*tail*2.65, .45*tail,
            (.03*aw-.60*tail*2.65+.27)*mod[0],
            -2*tail*2.65**2*mod[1], -.45*tail*2.65*mod[2]]


def rot(t):
    return np.array([[np.cos(t), np.sin(t)], [np.sin(t), -np.cos(t)]])


def moment(r, f):
    return r[1]*f[0]-r[0]*f[1]


def loads(p, rho, va, alpha, q, de, thrust, cg, mod):
    s, ar = p[:2]
    c = geometry(p)[2]
    ca, cq, ce, ma, mq, me = derivatives(p, mod)
    qhat = q*c/(2*va)
    cl = p[5]+ca*alpha+cq*qhat+ce*de
    cd = p[3]+cl**2/(np.pi*p[4]*ar)
    cm = p[7]+ma*alpha+mq*qhat+me*de
    scale = rho*va**2*s/2
    lift, drag = scale*np.array([cl, cd])
    fa = np.array([lift*np.sin(alpha)-drag*np.cos(alpha),
                   -lift*np.cos(alpha)-drag*np.sin(alpha)])
    ft = thrust*np.array([np.cos(axis), -np.sin(axis)])
    aero = scale*c*cm+moment(np.array([-.28*c, 0])-cg, fa)
    mo = moment(c*np.array([1.13, .015]), ft)
    prop = mo+moment(-cg, ft)
    return fa+ft, aero+prop, [lift, drag, cl, cm, aero, prop, mo]


def rhs(x, de, thrust, p, m, wind=zero, rho=None, shift=0, iy=1, mod=(1,1,1)):
    _, z, u, w, theta, q = x
    cg, inertia = mass(p, m, shift, iy)
    vg = np.array([u, w])
    rotation = rot(theta)
    ua, wa = vg-rotation.T@wind
    va, alpha = np.hypot(ua, wa), np.arctan2(wa, ua)
    f, moment_cg, _ = loads(p, density(z) if rho is None else rho, va, alpha,
                            q, de, thrust, cg, mod)
    return np.r_[rotation@vg, f/m+[-q*w-g*np.sin(theta), q*u+g*np.cos(theta)],
                 q, moment_cg/inertia]


def trim(p, v, h, vz, m, shift=0, iy=1, mod=(1,1,1)):
    rho, c = density(h), geometry(p)[2]
    cg, inertia = mass(p, m, shift, iy)
    gamma = np.arcsin(vz/v)

    def residual(z):
        a, de, tw = z
        f, my, _ = loads(p, rho, v, a, 0, de, tw*m*g, cg, mod)
        return np.r_[(rot(a+gamma)@f-[0, m*g])/(m*g), my/(m*g*c)]

    start = [0.07, -0.06, 0.12]
    bounds = ([-np.pi/36, -np.pi/9, 0], [np.radians(11), np.pi/9, np.inf])
    sol = least_squares(residual, start, bounds=bounds, xtol=1e-12,
                        ftol=1e-12, gtol=1e-12, max_nfev=250)
    a, de, tw = sol.x
    t = tw*m*g
    res = residual(sol.x)
    _, my, dat = loads(p, rho, v, a, 0, de, t, cg, mod)
    lift, drag, cl, cm, ma, mt, mo = dat
    stall = np.sqrt(2*m*g/(rho*p[0]*p[6]))
    status = ("NUMERICAL_FAILURE" if not sol.success else
              "NO_TRIM_FOUND" if np.max(np.abs(res)) > 1e-8 else
              "OUTSIDE_SCREEN" if cl > .85*p[6] or v < 1.30*stall else "FEASIBLE")
    useful = t*v*np.cos(a+axis)
    return dict(v=v, z=h, vz=vz, mass=m, thrust=t, alpha=np.degrees(a),
                theta=np.degrees(a+gamma), elevator=np.degrees(de),
                lift=lift, drag=drag, cl=cl, cm_ref=cm, m_aero=ma,
                m_prop=mt, m_O=mo, m_net=my, useful_kW=useful/1e3,
                stall=stall, residual=list(res*np.array([m*g,m*g,m*g*c])),
                residual_scaled=float(np.max(np.abs(res))), nfev=sol.nfev,
                solver_status=sol.status, status=status, cg=cg.tolist(), iy=inertia)


def jac(f, x, steps):
    d = np.diag(steps)
    return np.column_stack([(f(x+h)-f(x-h))/(2*step) for h, step in zip(d, steps)])


def linear(p, z, shift=0, iy=1, mod=(1,1,1)):
    a = np.radians(z["alpha"])
    x = np.array([0,z["z"],z["v"]*np.cos(a),z["v"]*np.sin(a),a,0])
    control = np.array([np.radians(z["elevator"]), z["thrust"]])
    dx = np.array([.1,.1,1e-3,1e-3,1e-5,1e-5])
    frozen = lambda xx: rhs(xx,*control,p,z["mass"],rho=density(x[1]),shift=shift,iy=iy,mod=mod)
    full = lambda xx: rhs(xx,*control,p,z["mass"],shift=shift,iy=iy,mod=mod)
    B = jac(lambda uu: rhs(x,*uu,p,z["mass"],rho=density(x[1]),
                           shift=shift,iy=iy,mod=mod), control, [1e-5,.01])
    A = jac(frozen,x,dx)
    H = jac(full,x,dx)
    poles = lambda a: [[v.real,v.imag] for v in sorted(np.linalg.eigvals(a),
                                                       key=lambda v: (v.real,v.imag))]
    response = np.array([[np.cos(a),np.sin(a),0,0],
                         [np.sin(a)/z["v"],-np.cos(a)/z["v"],1,0]])@B[2:]
    return dict(A4=A[2:,2:].tolist(), A6_isa=H.tolist(), B4=B[2:].tolist(),
                actual_state_residual=frozen(x)[2:].tolist(),
                dv_dgamma_response=response.tolist(), poles4=poles(A[2:,2:]),
                poles6=poles(H),
                jac_step_error=float(np.max(abs(A-jac(frozen,x,dx/2)))))


def mission(p, m, wind_x=0, distance=120e3, n=41, high=False, cruise_alt=1500, rates=None, **kw):
    up = (5 if high else 2.5) if rates is None else rates[0]
    seg=[]
    for name, speed, vz, za, zb in [("climb",34,up,300,cruise_alt),
                                    ("descent",36,-1.4,cruise_alt,500)]:
        ts = abs(zb-za)/abs(vz)
        cuts = [trim(p,speed,h,vz,m,**kw) for h in np.linspace(za,zb,n)]
        assert all(c["status"]=="FEASIBLE" for c in cuts)
        d = (np.sqrt(speed**2-vz**2)+wind_x)*ts
        e = simpson([c["useful_kW"] for c in cuts],x=np.linspace(0,ts/3600,n))
        seg.append([name,d/1000,ts/60,e])
    c=trim(p,p[-1],cruise_alt,0,m,**kw)
    assert c["status"]=="FEASIBLE"
    d=distance/1000-sum(row[1] for row in seg)
    t=(d*1000)/(p[-1]+wind_x)/60
    seg.insert(1,["cruise",d,t,t*c["useful_kW"]/60])
    totals=np.sum([row[1:] for row in seg],axis=0)
    return dict(segments=seg, totals=totals.tolist(),
                shaft_kWh=(totals[2]/eta[0,::-1]).tolist(),
                mech_kWh=(totals[2]/eta[:2,::-1].prod(axis=0)).tolist(),
                input_kWh=(totals[2]/eta[:,::-1].prod(axis=0)).tolist())


def main():
    ps=cfg["candidates"]
    p=ps["P-B"]
    tr={key:trim(p,*case) for key,case in zip(labels,b_cases)}
    scans=[trim(p,v,h,w,m) for h,m,w,v in itertools.product(
        [0,300,900,1500,2500],[435,471,500],[-1.4,0,2.5,5],range(25,50))]
    feasible=[s for s in scans if s["status"]=="FEASIBLE"]
    stats={key:sum(r["status"]==key for r in scans) for key in sorted({r["status"] for r in scans})}
    extremes={key:[min(feasible,key=lambda r:r[key]),max(feasible,key=lambda r:r[key])]
              for key in ["thrust","useful_kW"]}
    sens={}
    cases=[("mass435",p,{},435,1500,37,0),("mass500",p,{},500,1500,37,0)]
    for k,i in [("area",0),("AR",1),("CD0",3),("e",4)]:
        for ratio in [.9,1.1]:
            r=p.copy();r[i]*=ratio
            cases.append((f"{k} {ratio}",r,{},471,1500,37,0))
    for k,vals in [("v",[34,41]),("h",[0,2500]),("vz",[2.5,5]),
                   ("shift",[-.04,.04]),("iy",[.8,1.2]),
                   ("ma",[.8,1.2]),("mq",[.8,1.2]),("me",[.8,1.2])]:
        for value in vals:
            kw={k:value} if k in ["shift","iy"] else {}
            if k in ["ma","mq","me"]:
                kw["mod"]=tuple(value if symbol==k else 1 for symbol in ["ma","mq","me"])
            cases.append((f"{k} {value}",p,kw,471,value if k=="h" else 1500,
                          value if k=="v" else 37,value if k=="vz" else 0))
    for k,pp,kw,m,h,v,w in cases:
        z=trim(pp,v,h,w,m,**kw)
        poles=linear(pp,z,**kw)["poles4"] if not w else []
        sens[k]=[z["thrust"],z["useful_kW"],z["alpha"],z["elevator"],poles]
    variants={k:dict(geom=geometry(q),aero=derivatives(q),
                    mission=mission(q,471),cruise=trim(q,q[-1],1500,0,471),
                    climb=trim(q,34,900,2.5,471),high=trim(q,34,900,5,471))
              for k,q in ps.items()}
    missions={str(w):mission(p,471,w) for w in [-6,0,6]}
    missions.update(light=mission(p,435),heavy=mission(p,500),high=mission(p,471,high=True),
                    refinement=mission(p,471,n=81))
    mission_sens={}
    for k,pp,kw,m,h,v,w in cases:
        if k=="h 0":
            continue
        qq=pp.copy()
        if k.startswith("v "):
            qq[-1]=v
        result=mission(qq,m,cruise_alt=(h if k.startswith("h ") else 1500),
                       rates=([w] if k.startswith("vz ") else None),**kw)
        mission_sens[k]=result["totals"][2]
    z=tr["cruise"]
    a=np.radians(z["alpha"])
    x=np.array([0,1500,z["v"]*np.cos(a),z["v"]*np.sin(a),a,0])
    earth_wind=np.array([-6.,2.])
    xw=x.copy()
    xw[2:4]+=rot(a).T@earth_wind
    actuator=(np.radians(z["elevator"]),z["thrust"])
    uniform_error=rhs(xw,*actuator,p,471,earth_wind)-rhs(x,*actuator,p,471)
    assert np.max(np.abs(uniform_error-np.r_[earth_wind,np.zeros(4)]))<1e-11
    checks=dict(grid_residual_absolute=np.max(np.abs([t["residual"] for t in feasible]),axis=0).tolist(),
                uniform_wind_error=uniform_error.tolist(),
                no_negative_thrust_domain=trim(p,36,1000,-8,471))
    envelopes={}
    for name, speed, rate, lo, hi in [("normal",34,2.5,300,1500),
                                      ("high",34,5,300,1500),
                                      ("descent",36,-1.4,500,1500)]:
        points=[trim(p,speed,h,rate,471) for h in np.linspace(lo,hi,41)]
        envelopes[name]=dict(thrust=[min(z["thrust"] for z in points),
                                     max(z["thrust"] for z in points)],
                             input_kW=[min(z["useful_kW"] for z in points)/eta[:,1].prod(),
                                       max(z["useful_kW"] for z in points)/eta[:,0].prod()])
    drag_bound = density(1000)*36**2*p[0]/2*(p[3]+(.85*p[6])**2/(np.pi*p[1]*p[4]))
    required_drag = 471*g*8/36
    assert drag_bound < required_drag
    checks.update(phase_envelopes=envelopes, steep_descent_drag_bound=drag_bound,
                  steep_descent_required_drag=required_drag)
    assert all(z["status"]=="FEASIBLE" for z in tr.values())
    assert max(z["residual_scaled"] for z in feasible)<1e-8
    assert abs(missions["0"]["totals"][2]-missions["refinement"]["totals"][2])<1e-6
    print(json.dumps(dict(trim=tr,linear=linear(p,tr["cruise"]),scan=stats,
          extrema=extremes,variants=variants,mission=missions,sensitivity=sens, mission_sensitivity=mission_sens,
          checks=checks,
          max_residual_scaled=max(z["residual_scaled"] for z in feasible),
          guard=trim(p,25,2500,5,500)),indent=2))


if __name__=="__main__":
    main()
