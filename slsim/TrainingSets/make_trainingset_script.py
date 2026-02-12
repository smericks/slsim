from generate_images import training_images_to_h5

h5_save_path = '10ktest_seed4.h5'
training_images_to_h5(h5_save_path,N_images=10000,random_seed=4)