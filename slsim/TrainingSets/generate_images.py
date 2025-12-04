from slsim.Deflectors.DeflectorTypes.epl_sersic import EPLSersic
from slsim.LOS.los_individual import LOSIndividual
from slsim.Sources.source import Source
from slsim.Sources.SourceTypes.point_plus_extended_source import PointPlusExtendedSource
from slsim.Lenses.lens import Lens
from slsim.LsstSciencePipeline.lsst_science_pipeline import lens_inejection_fast
from astropy.cosmology import FlatLambdaCDM
import lsst.daf.butler as dafButler # need to be in RSP or NERSC for this?
import numpy as np

# import configuration file stuff (TODO fix this...)
from Configs.example_config import sampling_blocks as config_sampling_blocks

# TODO: choose a cosmology (how to make this clearly defined by the user)
groundtruth_cosmo = FlatLambdaCDM(H0=70, Om0=0.3)

# sample given setup in configuration file
sampled_params_dict = {}
# sample one block at a time
for sampling_blocks in config_sampling_blocks:
    # take a sample
    params_sample = sampling_blocks['sampler_method'](**sampling_blocks['sampler_args'])
    # edge case for 1 param in sampling block
    if np.isscalar(params_sample):
        sampled_params_dict[sampling_blocks['param_keys'][0]] = params_sample
    else: 
        for i in range (0,len(sampling_blocks['param_keys'])):
            sampled_params_dict[sampling_blocks['param_keys'][i]] = params_sample[i]

print(sampled_params_dict)

# make a deflector (captures mass & light of the object...)
epl_sersic_required_params = ['theta_E','gamma',
    'e1_mass','e2_mass','e1_light','e2_light','mag_i','angular_size']

deflector_dict = {}
for key in epl_sersic_required_params:
    if ('deflector_'+key) not in sampled_params_dict.keys():
        raise ValueError('Missing param: deflector_'+key)
    deflector_dict[key] = sampled_params_dict['deflector_'+key]

deflector_obj = EPLSersic(deflector_dict=deflector_dict,z=sampled_params_dict['deflector_z'])

# make a LOS object for ext. shear
los_required_params = ['gamma1','gamma2']
for key in los_required_params:
    if ('los_'+key) not in sampled_params_dict.keys():
        raise ValueError('Missing param: los_'+key)
gamma = [sampled_params_dict['los_gamma1'],sampled_params_dict['los_gamma2']]
los_obj = LOSIndividual(gamma=gamma)

# make a source (captures extended & point source)
source_required_params = ['ps_mag_i','e1','e2',
    'center_x','center_y','mag_i','angular_size','n_sersic']
source_dict = {}
for key in source_required_params:
    if ('source_'+key) not in sampled_params_dict.keys():
        raise ValueError('Missing param: source_'+key)
    source_dict[key] = sampled_params_dict['source_'+key]

# TODO: why are angular_size and n_sersic treated differently than the other params here? 
source_obj = Source(extended_source_type='single_sersic',
    point_source_type='quasar',source_dict=source_dict,
    z=sampled_params_dict['source_z'],
    angular_size=sampled_params_dict['source_angular_size'],
    n_sersic=sampled_params_dict['source_n_sersic'])

# combine into a lens object
lens_obj = Lens(source_class=source_obj,deflector_class=deflector_obj,
    los_class=los_obj,cosmo=groundtruth_cosmo)

# TODO: inject into DP0 co-adds using LsstSciencePipeline code...
# from Narayan:
config = "dp02"
collection = "2.2i/runs/DP0.2"
butler = dafButler.Butler(config, collections=collection)
skymap = butler.get("skyMap")
lens_inejection_fast(lens_pop=[lens_obj])

# TODO: save in MMU .h5 / HuggingFace format 

# TODO: generate a list of unique identifiers up front, and assign as we go (to avoid duplication?)
