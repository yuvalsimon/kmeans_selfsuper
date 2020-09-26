import argparse
import os
from types import SimpleNamespace

import numpy as np
import torch
from tqdm import tqdm
import torch.nn.functional as F
from PyContrast.pycontrast.networks.build_backbone import build_model
from torch_utils import get_loaders_imagenet, get_loaders_objectnet

device, dtype = 'cuda:0', torch.float32
gh = 'rwightman/pytorch-image-models'

def get_model(model='resnet50_infomin'):
    if model == 'resnet50_infomin':
        args = SimpleNamespace()

        args.jigsaw = True
        args.arch, args.head, args.feat_dim = 'resnet50', 'mlp', 128
        args.mem = 'moco'
        args.modal = 'RGB'
        model, _ = build_model(args)
        cp = torch.load('checkpoints/InfoMin_800.pth')

        sd = cp['model']
        new_sd = {}
        for entry in sd:
            new_sd[entry.replace('module.', '')] = sd[entry]
        model.load_state_dict(new_sd, strict=False)  # no head, don't need linear model

        model = model.to(device=device)
        return model
    elif model == 'resnext152_infomin':
        args = SimpleNamespace()

        args.jigsaw = True
        args.arch, args.head, args.feat_dim = 'resnext152v1', 'mlp', 128
        args.mem = 'moco'
        args.modal = 'RGB'
        model, _ = build_model(args)
        cp = torch.load('checkpoints/InfoMin_resnext152v1_e200.pth')

        sd = cp['model']
        new_sd = {}
        for entry in sd:
            new_sd[entry.replace('module.', '')] = sd[entry]
        model.load_state_dict(new_sd, strict=False)  # no head, don't need linear model

        model = model.to(device=device)
        return model
    elif model == 'resnet50_mocov2':
        args = SimpleNamespace()

        args.jigsaw = False
        args.arch, args.head, args.feat_dim = 'resnet50', 'linear', 2048
        args.mem = 'moco'
        args.modal = 'RGB'
        model, _ = build_model(args)
        cp = torch.load('checkpoints/MoCov2.pth')

        sd = cp['model']
        new_sd = {}
        for entry in sd:
            new_sd[entry.replace('module.', '')] = sd[entry]
        model.load_state_dict(new_sd, strict=False)  # no head, don't need linear model

        model = model.to(device=device)
        return model
    else:
        raise ValueError('Wrong model')


def eval(model, loader):
    reses = []
    labs = []
    with torch.no_grad():
        for batch_idx, (data, target) in enumerate(tqdm(loader)):
            data, target = data.to(device=device, dtype=dtype), target.to(device=device)

            output = model.forward_features(data)
            output = F.adaptive_avg_pool2d(output, output_size=(1,1)).view(output.shape[0], -1)
            reses.append(output.detach().cpu().numpy())
            labs.append(target.detach().cpu().numpy())

    rss = np.concatenate(reses, axis=0)
    lbs = np.concatenate(labs, axis=0)
    return rss, lbs

bss = {'tf_efficientnet_l2_ns_475': 8, 'gluon_resnet152_v1s': 16, 'ig_resnext101_32x48d': 16}
def eval_and_save(model='resnet50_infomin', imagenet_path='~/datasets/imagenet', objectnet_path='~/datasets/objectnet', dim=224):
    mdl = torch.hub.load(gh, model, pretrained=True).cuda()
    bs = 16
    os.makedirs('./results', exist_ok=True)
    if(imagenet_path):
        train_loader, val_loader = get_loaders_imagenet(imagenet_path, bs, bs, dim, 8, 1, 0)
        train_embs, train_labs = eval(mdl, train_loader)
        val_embs, val_labs = eval(mdl, val_loader)
        np.savez(os.path.join('./results', model + '-imagenet_super.npz'), train_embs=train_embs, train_labs=train_labs, val_embs=val_embs,
                val_labs=val_labs)
    if(objectnet_path and imagenet_path):
        obj_loader, _, _, _, _ = get_loaders_objectnet(objectnet_path, imagenet_path, bs, dim, 8, 1, 0)
        obj_embs, obj_labs = eval(mdl, obj_loader)
        np.savez(os.path.join('./results', model + '-objectnet_super.npz'), obj_embs=obj_embs, obj_labs=obj_labs)

models = torch.hub.list(gh)
# models to run:
# tf_efficientnet_l2_ns_475
# gluon_resnet152_v1s
# ig_resnext101_32x48d
parser = argparse.ArgumentParser(description='IM')
parser.add_argument('--model', dest='model', type=str, default='resnext152_infomin',
                    help='Model: one of ' + ', '.join(models))
parser.add_argument('--imagenet', dest='imagenet_path', type=str,
                    help='Imagenet path')
parser.add_argument('--objectnet', dest='objectnet_path', type=str,
                    help='Objectnet path')
args = parser.parse_args()

dims = {'tf_efficientnet_l2_ns_475': 475, 'gluon_resnet152_v1s': 224, 'ig_resnext101_32x48d': 224}
eval_and_save(dim=dims[args.model], **vars(args))
