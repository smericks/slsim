from scipy.stats import lognorm, multivariate_normal
import numpy as np

sampling_blocks = [

    # Einstein radius (log-normal)
    { 'param_keys':['deflector_theta_E'],
    'sampler_method':lognorm.rvs,
    'sampler_args':{
        's':0.45,
        'loc':0.,
        'scale':0.7
        }
    },

    # Other deflector params from multivariate gaussian
    { 'param_keys':['deflector_gamma','deflector_e1_mass','deflector_e2_mass',
        'deflector_e1_light','deflector_e2_light',
        'deflector_angular_size','deflector_n_sersic'],
    'sampler_method':multivariate_normal.rvs,
    'sampler_args':{
        'mean':[2.,0.,0.,0.,0.,],
        'cov':np.diag(np.asarray([])**2),
        }
   },
]