from generate_images import training_images_to_h5

h5_save_path = '/pscratch/sd/s/sydney3/project3/10ktest_seed6.h5'
training_images_to_h5(h5_save_path,N_images=10000,random_seed=6)