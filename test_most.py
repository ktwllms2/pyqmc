import numpy as np
import testwf
import pytest


def test_wfs():
    from pyscf import lib, gto, scf
    from slater import PySCFSlaterRHF
    from slateruhf import PySCFSlaterUHF
    from jastrow import Jastrow2B
    from multiplywf import MultiplyWF
    mol = gto.M(atom='Li 0. 0. 0.; H 0. 0. 1.5', basis='cc-pvtz',unit='bohr')
    mf = scf.RHF(mol).run()
    mf_rohf = scf.ROHF(mol).run()
    mf_uhf = scf.UHF(mol).run()
    epsilon=1e-5
    nconf=10
    epos=np.random.randn(nconf,4,3)
    for wf in [PySCFSlaterRHF(nconf,mol,mf),Jastrow2B(nconf,mol),
               MultiplyWF(nconf,PySCFSlaterRHF(nconf,mol,mf),Jastrow2B(nconf,mol)), 
               PySCFSlaterUHF(nconf,mol,mf_uhf),PySCFSlaterUHF(nconf,mol,mf), 
               PySCFSlaterUHF(nconf,mol,mf_rohf)]:
        assert testwf.test_wf_gradient(wf, epos, delta=1e-5)[0] < epsilon 
        assert testwf.test_wf_laplacian(wf, epos, delta=1e-5)[0] < epsilon 
        assert testwf.test_wf_gradient(wf, epos, delta=1e-5)[0] < epsilon 
        assert testwf.test_wf_laplacian(wf, epos, delta=1e-5)[0] < epsilon 
        for k,item in testwf.test_updateinternals(wf,epos).items():
            assert item < epsilon


def test_func3d():
    from func3d import PadeFunction,GaussianFunction,test_func3d_gradient,test_func3d_laplacian
    test_functions = {'Pade':PadeFunction(0.2), 'Gaussian':GaussianFunction(0.4)}
    delta=1e-6
    epsilon=1e-5
    
    for name, func in test_functions.items():
        assert test_func3d_gradient(func,delta=delta)[0] < epsilon
        assert test_func3d_laplacian(func,delta=delta)[0] < epsilon
        
    

def test_vmc():
    import pandas as pd
    from mc import vmc,initial_guess
    from pyscf import lib, gto, scf
    from energy import energy
    
    from slater import PySCFSlaterRHF
    from slateruhf import PySCFSlaterUHF
    
    nconf=5000
    mol   = gto.M(atom='Li 0. 0. 0.; Li 0. 0. 1.5', basis='cc-pvtz',unit='bohr',verbose=1)

    mf    =scf.RHF(mol).run()
    mf_uhf=scf.UHF(mol).run()
    nsteps=100
    warmup=30

    for wf,mf in [(PySCFSlaterRHF(nconf,mol,scf.RHF(mol).run()), scf.RHF(mol).run()) , 
                  (PySCFSlaterUHF(nconf,mol,scf.UHF(mol).run()),scf.UHF(mol).run())]:
       
        coords = initial_guess(mol,nconf) 
        df,coords=vmc(mol,wf,coords,nsteps=nsteps,accumulators={'energy':energy} ) 

        df=pd.DataFrame(df)
        df.to_csv("data.csv")
        en=np.mean(df['energytotal'][warmup:])
        err=np.std(df['energytotal'][warmup:])/np.sqrt(nsteps-warmup)
        assert en-mf.energy_tot() < 10*err


