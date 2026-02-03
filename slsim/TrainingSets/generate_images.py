from slsim.Deflectors import Deflector
from slsim.LOS.los_individual import LOSIndividual
from slsim.Sources.source import Source
from slsim.Lenses.lens import Lens
from slsim.ImageSimulation.image_simulation import simulate_image
from astropy.cosmology import FlatLambdaCDM
import numpy as np

# NOTE: required parameters
required_parameters = {
    # NOTE: anything with LOG_ prefix will be exponentiated before input
    'deflector_LOG_theta_E','deflector_LOG_gamma_pl','deflector_e1_mass',
    'deflector_e2_mass','deflector_e1_light','deflector_e2_light',
    'deflector_mag_i','deflector_mag_F158',# + any other bands!
    'deflector_LOG_angular_size','deflector_n_sersic',
    'deflector_LOG_z',

    'los_gamma1','los_gamma2',
    
    # NOTE: source redshift is an edge case, treatly separately
    'source_LOG_zS_minus_Zd','source_n_sersic',
    'source_LOG_angular_size','source_e1','source_e2',
    'source_center_x','source_center_y',
    'source_mag_i','source_mag_F158',# + any other bands!
    'source_ps_mag_i','source_ps_mag_F158'# + any other bands!
}

# import configuration file stuff (TODO fix this...)
from Configs.kde_config import sampling_blocks as config_sampling_blocks

# TODO: choose a cosmology (how to make this clearly defined by the user)
groundtruth_cosmo = FlatLambdaCDM(H0=70, Om0=0.3)

def sample_an_image():
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
                sampled_params_dict[sampling_blocks['param_keys'][i]] = params_sample[i].item()

    print(sampled_params_dict)

    # make a deflector (captures mass & light of the object...)
    # TODO: what about n_sersic?
    epl_sersic_required_params = ['LOG_theta_E','LOG_gamma_pl',
        'e1_mass','e2_mass','e1_light','e2_light','mag_i','mag_F158',
        'LOG_angular_size','n_sersic']

    deflector_dict = {}
    for key in epl_sersic_required_params:
        if ('deflector_'+key) not in sampled_params_dict.keys():
            raise ValueError('Missing param: deflector_'+key)
        elif key[:4] == 'LOG_':
            deflector_dict[key[4:]] = np.exp(sampled_params_dict['deflector_'+key])
        else:
            deflector_dict[key] = sampled_params_dict['deflector_'+key]

    deflector_z = np.exp(sampled_params_dict['deflector_LOG_z'])
    # FUN FACT THIS IS WRONG!!!
    #deflector_obj = EPLSersic(deflector_dict=deflector_dict,
    #    z=deflector_z)
    print('input deflector dict: ', deflector_dict)
    deflector_obj = Deflector(deflector_type='EPL_SERSIC',
        z=deflector_z,**deflector_dict)

    # make a LOS object for ext. shear
    los_required_params = ['gamma1','gamma2']
    for key in los_required_params:
        if ('los_'+key) not in sampled_params_dict.keys():
            raise ValueError('Missing param: los_'+key)
    gamma = [sampled_params_dict['los_gamma1'],sampled_params_dict['los_gamma2']]
    los_obj = LOSIndividual(gamma=gamma)

    # make a source (captures extended & point source)
    source_required_params = ['ps_mag_i','ps_mag_F158',
        'e1','e2','center_x','center_y','mag_i','mag_F158',
        'LOG_angular_size','n_sersic']
    source_dict = {}
    for key in source_required_params:
        if ('source_'+key) not in sampled_params_dict.keys():
            raise ValueError('Missing param: source_'+key)
        elif key[:4] == 'LOG_':
            source_dict[key[4:]] = np.exp(sampled_params_dict['source_'+key])
        else:
            source_dict[key] = sampled_params_dict['source_'+key]

    # TODO: why are angular_size and n_sersic treated differently than the other params here? 
    source_z = np.exp(sampled_params_dict['source_LOG_zS_minus_Zd']) - deflector_z
    source_obj = Source(extended_source_type='single_sersic',
        point_source_type='quasar',
        z=source_z,
        **source_dict)

    # combine into a lens object
    slsim_lens_obj = Lens(source_class=source_obj,deflector_class=deflector_obj,
        los_class=los_obj,cosmo=groundtruth_cosmo)
    
    # TODO: check for 2nd brightest image mag., single-image systems
    

    # TODO: simulate an image
    image_LSST_i = simulate_image(
        lens_class=slsim_lens_obj, 
        band='i',
        num_pix=33,
        add_noise=True,observatory="LSST",
        kwargs_psf=None,
        kwargs_numerics=None,
        with_source=True,
        with_deflector=True,
        with_point_source=True
    )

    image_Roman_F158 = simulate_image(
        lens_class=slsim_lens_obj, 
        band='F158',
        num_pix=66,
        add_noise=True,
        observatory="Roman",
        kwargs_psf=None,
        kwargs_numerics=None,
        with_source=True,
        with_deflector=True,
        with_point_source=True
    )

    return image_LSST_i, image_Roman_F158, slsim_lens_obj

# TODO: save in MMU .h5 / HuggingFace format 

# TODO: generate a list of unique identifiers up front, and assign as we go (to avoid duplication?)
