from slsim.Deflectors import Deflector
from slsim.LOS.los_individual import LOSIndividual
from slsim.Sources.source import Source
from slsim.Lenses.lens import Lens
from slsim.ImageSimulation.image_simulation import simulate_image
from astropy.cosmology import FlatLambdaCDM
import numpy as np
import pandas as pd
import h5py

# NOTE: required parameters
required_parameters = {
    # NOTE: anything with LOG_ prefix will be exponentiated before input
    'deflector_LOG_theta_E','deflector_LOG_gamma_pl','deflector_e1_mass',
    'deflector_e2_mass',
    'deflector_center_x','deflector_center_y',
    'deflector_e1_light','deflector_e2_light',
    'deflector_mag_i','deflector_mag_F158',# + any other bands!
    'deflector_LOG_angular_size','deflector_n_sersic',
    'deflector_LOG_z',
    # TODO: vary the deflector center!!

    'los_gamma1','los_gamma2',
    
    # NOTE: source redshift is an edge case, treat separately
    'source_LOG_zS_minus_Zd','source_n_sersic',
    'source_LOG_angular_size','source_e1','source_e2',
    'source_center_x','source_center_y',
    'source_mag_i','source_mag_F158',# + any other bands!
    'source_ps_mag_i','source_ps_mag_F158'# + any other bands!

    # microlensing
    'mag_pert_im0','mag_pert_im1','mag_pert_im2','mag_pert_im3','mag_pert_im4',
    'mag_pert_im5'
}

# import configuration file stuff (TODO fix this...)
from Configs.kde_config import sampling_blocks as config_sampling_blocks

# TODO: choose a cosmology (how to make this clearly defined by the user)
groundtruth_cosmo = FlatLambdaCDM(H0=70, Om0=0.3)

def sample_an_image():

    havent_found_lens = True

    while havent_found_lens:

        # sample given setup in configuration file
        sampled_params_dict = {}
        # sample one block at a time
        for sampling_blocks in config_sampling_blocks:
            # take a sample
            params_sample = sampling_blocks['sampler_method'](**sampling_blocks['sampler_args'])
            # edge case for 1 param in sampling block
            if np.isscalar(params_sample):
                sampled_params_dict[sampling_blocks['param_keys'][0]] = params_sample
            # agh what about sampling an array, b/c mag_pert = [0,1,2,3]
            else: 
                for i in range (0,len(sampling_blocks['param_keys'])):
                    sampled_params_dict[sampling_blocks['param_keys'][i]] = params_sample[i].item()


        # make a deflector (captures mass & light of the object...)
        # TODO: what about n_sersic?
        epl_sersic_required_params = ['LOG_theta_E','LOG_gamma_pl',
            'e1_mass','e2_mass','center_x','center_y',
            'e1_light','e2_light','mag_i','mag_F158',
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
        # TODO: need to add microlensing kwargs here?
        slsim_lens_obj = Lens(source_class=source_obj,deflector_class=deflector_obj,
            los_class=los_obj,cosmo=groundtruth_cosmo)
        
        # TODO: check for 2nd brightest image mag., single-image systems before simulating...
        if slsim_lens_obj.image_number[0] > 1: 
            # only do this after confirming multiple images (otherwise, indexing error)
            lenst_kwargs = slsim_lens_obj.lenstronomy_kwargs(band='i')
            second_brightest_im_mag = np.sort(lenst_kwargs[-1]['kwargs_ps'][0]['magnitude'])[1]
            if second_brightest_im_mag < 23.3:
                havent_found_lens = False

    # handle microlensing factors
    mag_pert_array = [sampled_params_dict['mag_pert_im%d'%(n)] for n in range(0,5)]

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
        with_point_source=True,
        mag_pert=mag_pert_array
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
        with_point_source=True,
        mag_pert=mag_pert_array
    )


    # add image positions to sampled_params_dict
    # how to deal with diff. # of images when asking for x_point_source
    sampled_params_dict['num_images'] = slsim_lens_obj.image_number[0]
    # TODO: will it be weird to write an array instead of a single number?
    #sampled_params_dict['source_ps_image_x'] = lenst_kwargs[-1]['kwargs_ps'][0]['ra_image']
    #sampled_params_dict['source_ps_image_y'] = lenst_kwargs[-1]['kwargs_ps'][0]['dec_image']


    return image_LSST_i, image_Roman_F158, slsim_lens_obj, sampled_params_dict


# helper function copied from ddprism: (@swagnerc, @smericks): https://github.com/swagnercarena/ddprism/blob/main/ddprism/hubble_galaxies/build_parent_sample.py
def _extract_numpy(df_column):
    """
    Helper function for dealing with masking in pandas to hdf5.

    Args:
        df_column (pd.DataFrame): Dataframe column to be convereted to numpy.

    Returns:
        Numpy array with NaN values properly dealt with.
    """
    if df_column.dtype.kind in {'f', 'i'}:  # Numeric columns use np.nan.
        return df_column.fillna(np.nan).to_numpy()
    else:  # For non-numeric columns, return NaN string.
        return df_column.fillna("NaN").to_numpy()

# generate 1,000 images
def training_images_to_h5(file_name,N_images,random_seed=1):
    """
    Simulate N_images images and save into a .h5 file for use in ML training
    
    Args:
        file_name (string): .h5 filepath 
        N_images (int): number images to simulate
        random_seed (int): seed for np.random(), ensures reproducibility
    Returns:
    """

    # set random seed
    np.random.seed(random_seed)

    # initialize with a first lens
    image_LSST_i, image_roman_F158, slsim_obj, params_dict = sample_an_image()
    LSST_numpix = np.shape(image_LSST_i)[0]
    roman_numpix = np.shape(image_roman_F158)[0]

    # initialize image arrays
    image_LSST_array = np.empty((N_images,LSST_numpix,LSST_numpix))
    image_Roman_array = np.empty((N_images,roman_numpix,roman_numpix))
    image_LSST_array[0] = image_LSST_i
    image_Roman_array[0] = image_roman_F158

    # initialize a pandas df with the metadata
    metadata_df = pd.DataFrame([params_dict])

    # index from 1 b/c already initialized with i=0
    for i in range(1,N_images):
        image_LSST_i, image_roman_F158, slsim_obj, params_dict = sample_an_image()
        image_LSST_array[i] = image_LSST_i
        image_Roman_array[i] = image_roman_F158
        metadata_df = pd.concat([metadata_df, pd.DataFrame([params_dict])], ignore_index=True)
    
    # TODO: save in MMU .h5 / HuggingFace format 
    with h5py.File(file_name, 'w') as h5f:

        # save the image`` data.
        shape = image_LSST_array.shape
        h5f.create_dataset(
            'image_flux_LSST_i', data=image_LSST_array,
            compression="gzip", chunks=True,
            maxshape=(None, *shape[1:])
        )
        h5f['image_flux_LSST_i'].attrs['description'] = (
            'Flux values of the cutout images in LSST i-band.' \
            'Simulated to emulate LSST WFD 10-year co-add.'
        )

        shape = image_Roman_array.shape
        h5f.create_dataset(
            'image_flux_Roman_F158', data=image_Roman_array,
            compression="gzip", chunks=True,
            maxshape=(None, *shape[1:])
        )
        h5f['image_flux_Roman_F158'].attrs['description'] = (
            'Flux values of the cutout images in Roman F158' \
            'Simulated to emulate HLWAS medium tier'
        )

        # TODO: add in variance map, pixel-masking, object_ID?

        # Optional: add a description for parameters in the metadata
        descriptions={
            'deflector_LOG_theta_E':'log(theta_E) for a PEMD profile',
            'source_LOG_zS_minus_Zd':'log(z_source - z_deflector)',
            'num_images': 'number of point source images as computed by lenstronomy'
        }

        # Save the metadata!
        for key in metadata_df:
            h5f.create_dataset(
                    key, data=_extract_numpy(
                        metadata_df.loc[:, key]
                    ),
                    compression="gzip",
                    chunks=True, maxshape=(None,)
                )
            if key in descriptions.keys():
                h5f[key].attrs['description'] = descriptions[key]

# TODO: generate a list of unique identifiers up front, and assign as we go (to avoid duplication?)
