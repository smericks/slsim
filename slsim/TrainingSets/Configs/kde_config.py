from scipy.stats import gaussian_kde, multivariate_normal
from astropy.io import fits
import numpy as np

# keys for Sharma catalog convention (in same order as required_parameters)
keys_of_interest = [
    'theta_E_arcsec', # LOG
    'deflector_pl_slope', # LOG
    'deflector_mass_e1',
    'deflector_mass_e2',
    'deflector_light_e1',
    'deflector_light_e2',
    'deflector_mag_i',
    'deflector_light_R_eff_arcsec', # LOG
    #'deflector_light_n_sersic',
    'z_D', # LOG
    'external_shear_gamma1',
    'external_shear_gamma2',
    'z_S', # EDGE CASE
    #'host_light_n_sersic',
    'host_light_R_eff_arcsec', # LOG
    'host_light_e1',
    'host_light_e2',
    'x_host_position_arcsec',
    'y_host_position_arcsec',
    'unlensed_host_mag_i',
    'unlensed_ps_mag_i'
]

# load in .fits catalog
#fits_file = 'sharma_SLSim_catalog_LSST.fits'
fits_file = '/Users/smericks/Desktop/StrongLensing/project3/slsim/slsim/TrainingSets/Configs/sharma_SLSim_catalog_LSST.fits'
with fits.open(fits_file) as hdul:
    sharma_catalog = hdul[1].data  # assuming the catalog is in the first extension

# initialize with the first key: theta_E_arcsec (which needs a log)
catalog_samps = np.log(sharma_catalog[keys_of_interest[0]])
# now index onwards and vstack for each key
for key in keys_of_interest[1:]:
    # if it needs a log:
    if key in ['theta_E_arcsec','deflector_pl_slope',
        'deflector_light_R_eff_arcsec','z_D',
        'host_light_R_eff_arcsec']:
        catalog_samps = np.vstack((catalog_samps,np.log(sharma_catalog[key])))
    elif key == 'z_S':
        source_z = np.log(sharma_catalog['z_S'] - sharma_catalog['z_D'])
        catalog_samps = np.vstack((catalog_samps,source_z))
    else:
        catalog_samps = np.vstack((catalog_samps,sharma_catalog[key]))


# fit the KDE
print(catalog_samps.shape)
samples_kde = gaussian_kde(catalog_samps)

# required params for training set generation in SLSim Lens() convention
required_parameters = [
    # NOTE: anything with LOG_ prefix will be exponentiated before input
    'deflector_LOG_theta_E',
    'deflector_LOG_gamma',
    'deflector_e1_mass',
    'deflector_e2_mass',
    'deflector_e1_light',
    'deflector_e2_light',
    'deflector_mag_i',# + any other bands!
    'deflector_LOG_angular_size',
    #'deflector_n_sersic',
    'deflector_LOG_z',
    'los_gamma1','los_gamma2',
    
    # NOTE: source redshift is an edge case, treatly separately
    'source_LOG_zS_minus_Zd',
    #'source_n_sersic',
    'source_LOG_angular_size',
    'source_e1','source_e2',
    'source_center_x','source_center_y',
    'source_mag_i',# + any other bands!
    'source_ps_mag_i',# + any other bands!
]


# define the sampling block
# NOTE: treating n_sersic for src. and defl. separately
sampling_blocks = [

    # one KDE sampler that covers all parameters
    { 'param_keys':required_parameters,
    'sampler_method':samples_kde.resample,
    'sampler_args':{
        'size':1,
        }
    },

    # separate handling of n_sersic (not varied in the catalog)
    { 'param_keys':['deflector_n_sersic','source_n_sersic'],
    'sampler_method':multivariate_normal.rvs,
    'sampler_args':{
        'mean':np.asarray([4.,1.]),
        'cov':np.diag([0.1**2,0.1**2])}
    }


]