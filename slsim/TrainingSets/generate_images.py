from slsim.Deflectors.DeflectorTypes.epl_sersic import EPLSersic
from slsim.LOS.los_individual import LOSIndividual
from slsim.Sources.SourceTypes.point_plus_extended_source import PointPlusExtendedSource
from slsim.Lenses.lens import Lens


# import configuration file stuff (TODO fix this...)
from Configs.example_config import sampling_blocks as config_sampling_blocks

# sample given setup in configuration file
sampled_params_dict = {}
for sampling_blocks in config_sampling_blocks:
    params_sample = sampling_blocks['sampler_method'](**sampling_blocks['sampler_args'])
    for i in range (0,len(sampling_blocks['param_keys'])):
        sampled_params_dict[sampling_blocks['param_keys'][i]] = params_sample[i]

# make a deflector
epl_sersic_required_params = ['theta_E','gamma',
    'e1_mass','e2_mass','e1_light','e2_light','mag_i','angular_size']

deflector_dict = {}
for key in epl_sersic_required_params:
    if ('deflector_'+key) not in sampled_params_dict.keys():
        raise ValueError('Missing param: deflector_'+key)
    deflector_dict[key] = sampled_params_dict['deflector_'+key]

deflector_obj = EPLSersic(deflector_dict)

# make a LOS object for ext. shear
los_required_params = ['gamma1','gamma2']
los_dict = {}
for key in los_required_params:
    if ('los_'+key) not in sampled_params_dict.keys():
        raise ValueError('Missing param: los_'+key)
    los_dict[key] = sampled_params_dict['los_'+key]
los_obj = LOSIndividual()

# make a source
source_obj = PointPlusExtendedSource()

# combine into a lens object
lens_obj = Lens()

# 

