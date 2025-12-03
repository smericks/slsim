from scipy.stats import truncnorm, lognorm, multivariate_normal
import numpy as np

def RedshiftSampler(z_lens_mean,z_lens_std,z_src_mean,z_src_std):
    """
    Docstring for RedShiftSampler
    
    :param z_lens_mean: Gaussian mean for lens redshift distribution
    :param z_lens_std: Gaussian std dev. for lens redshift distribution
    :param z_src_mean: Gaussian mean for src redshift distribution
    :param z_src_std: Gaussian std. dev. for src redshift distribution

    Returns: (z_lens,z_src)
    """

    z_lens = truncnorm.rvs(-z_lens_mean/z_lens_std,np.inf,loc=z_lens_mean,scale=z_lens_std)
    z_src = truncnorm.rvs((z_lens-z_src_mean)/z_src_std,np.inf,loc=z_src_mean,scale=z_src_std)

    return z_lens,z_src


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
        'deflector_e1_light','deflector_e2_light','deflector_mag_i',
        'deflector_angular_size','deflector_n_sersic',
        'los_gamma1','los_gamma2'],
    'sampler_method':multivariate_normal.rvs,
    'sampler_args':{
        'mean':[2.,0.,0.,0.,0.,20.,1.,4.,0.,0.], # TODO: these are just placeholders for now...
        'cov':np.diag(np.asarray([0.1,0.1,0.1,0.1,0.1,0.4,0.2,0.2,0.1,0.1])**2),
        }
   },

   # Redshifts
   {
       'param_keys':['deflector_z','source_z'],
       'sampler_method': RedshiftSampler,
       'sampler_args':{
           'z_lens_mean':0.5,
           'z_lens_std':0.3,
           'z_src_mean':1.5,
           'z_src_std':0.7,
       }
   },

   # Source params
   { 'param_keys': ['source_ps_mag_i','source_angular_size','source_n_sersic',
        'source_e1','source_e2','source_center_x','source_center_y',
        'source_mag_i'],
    'sampler_method':multivariate_normal.rvs,
    'sampler_args':{
        'mean':[21.,1.,2.,0.,0.,0.,0.,22.5], # TODO: these are just placeholders for now...
        'cov':np.diag(np.asarray([1.,0.2,0.2,0.1,0.1,0.05,0.05,1.])**2),
        }
   },
]