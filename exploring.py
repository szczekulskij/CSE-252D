import torch


PATH_STABLE = "sd-image-conditioned-v2.ckpt"
PATH_ZERO123 = "105000.ckpt"

checkpoint_sd = torch.load(PATH_STABLE)
checkpoint_zero123 = torch.load(PATH_ZERO123, map_location=torch.device('cpu'))


stable_checkpoint_key_list = checkpoint_sd["state_dict"].keys()
zero123_checkpoint_key_list = checkpoint_zero123["state_dict"].keys()

print("Keys in stable checkpoint:")
for key in stable_checkpoint_key_list:
    print(key)

print("Keys in zero123 checkpoint:")
for key in zero123_checkpoint_key_list:
    print(key)

print("Keys in stable checkpoint but not in zero123 checkpoint or vice versa:")
distjoint_list = list(set(stable_checkpoint_key_list) ^ set(zero123_checkpoint_key_list))
print(len(distjoint_list))



print("Length of state_dict in stable checkpoint:", len(checkpoint_sd["state_dict"]))
print("Length of state_dict in zero123 checkpoint:", len(checkpoint_zero123["state_dict"]))