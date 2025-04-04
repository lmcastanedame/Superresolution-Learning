import glob
import random
import os
import numpy as np
from scipy import signal
from scipy import special


'''
Generate patches for the images in the folder dataset/data/Train
The code scans among the training images and then for data_aug_times
'''

class GenerateDataset():

    def symetrisation_patch_gen(self, ima):
        S = np.fft.fftshift(np.fft.fft2(ima[:,:,0]+1j*ima[:,:,1]))
        p = np.zeros((S.shape[0])) # azimut (ncol)
        for i in range(S.shape[0]):
            p[i] = np.mean(np.abs(S[i,:]))
        sp = p[::-1]
        c = np.real(np.fft.ifft(np.fft.fft(p)*np.conjugate(np.fft.fft(sp))))
        d1 = np.unravel_index(c.argmax(),p.shape[0])
        d1 = d1[0]
        shift_az_1 = int(round(-(d1-1)/2))%p.shape[0]+int(p.shape[0]/2)
        p2_1 = np.roll(p,shift_az_1)
        shift_az_2 = int(round(-(d1-1-p.shape[0])/2))%p.shape[0]+int(p.shape[0]/2)
        p2_2 = np.roll(p,shift_az_2)
        window = signal.windows.gaussian(p.shape[0], std=0.2*p.shape[0])
        test_1 = np.sum(window*p2_1)
        test_2 = np.sum(window*p2_2)
        # make sure the spectrum is symetrized and zeo-Doppler centered
        if test_1>=test_2:
            p2 = p2_1
            shift_az = shift_az_1/p.shape[0]
        else:
            p2 = p2_2
            shift_az = shift_az_2/p.shape[0]
        S2 = np.roll(S,int(shift_az*p.shape[0]),axis=0)




        q = np.zeros((S.shape[1])) # range (nlin)
        for j in range(S.shape[1]):
            q[j] = np.mean(np.abs(S[:,j]))
        sq = q[::-1]
        #correlation
        cq = np.real(np.fft.ifft(np.fft.fft(q)*np.conjugate(np.fft.fft(sq))))
        d2 = np.unravel_index(cq.argmax(),q.shape[0])
        d2=d2[0]
        shift_range_1 = int(round(-(d2-1)/2))%q.shape[0]+int(q.shape[0]/2)
        q2_1 = np.roll(q,shift_range_1)
        shift_range_2 = int(round(-(d2-1-q.shape[0])/2))%q.shape[0]+int(q.shape[0]/2)
        q2_2 = np.roll(q,shift_range_2)
        window_r = signal.windows.gaussian(q.shape[0], std=0.2*q.shape[0])
        test_1 = np.sum(window_r*q2_1)
        test_2 = np.sum(window_r*q2_2)
        if test_1>=test_2:
            q2 = q2_1
            shift_range = shift_range_1/q.shape[0]
        else:
            q2 = q2_2
            shift_range = shift_range_2/q.shape[0]


        Sf = np.roll(S2,int(shift_range*q.shape[0]),axis=1)
        ima2 = np.fft.ifft2(np.fft.ifftshift(Sf))
        return np.stack((np.real(ima2),np.imag(ima2)),axis=2)

    def generate_patches(self,src_dir="./dataset/data/Train",pat_size=256,step=0,stride=64,bat_size=4,data_aug_times=1,n_channels=2):
        count = 0
        filepaths = glob.glob(src_dir + '/*.npy')
        print("number of training data %d" % len(filepaths))

        # calculate the number of patches
        for i in range(len(filepaths)):
            img = np.load(filepaths[i])

            im_h = np.size(img, 0)
            im_w = np.size(img, 1)
            for x in range(0+step, (im_h - pat_size), stride):
                for y in range(0+step, (im_w - pat_size), stride):
                    count += 1
        origin_patch_num = count * data_aug_times

        if origin_patch_num % bat_size != 0:
            numPatches = (origin_patch_num / bat_size + 1) * bat_size
        else:
            numPatches = origin_patch_num
        print("total patches = %d , batch size = %d, total batches = %d" % \
              (numPatches, bat_size, numPatches / bat_size))

        # data matrix 4-D
        numPatches=int(numPatches)
        inputs = np.zeros((numPatches, pat_size, pat_size, n_channels), dtype="float32")


        count = 0
        # generate patches
        for i in range(len(filepaths)): #scan through images
            img = np.load(filepaths[i])
            img_s = img
            im_h = np.size(img, 0)
            im_w = np.size(img, 1)
            for x in range(0 + step, im_h - pat_size, stride):
                for y in range(0 + step, im_w - pat_size, stride):
                    inputs[count, :, :, :] = self.symetrisation_patch_gen(img_s[x:x + pat_size, y:y + pat_size, :2])
                    #inputs[count, :, :, :] = img_s[x:x + pat_size, y:y + pat_size, :]
                    count += 1


        # pad the batch
        if count < numPatches:
            to_pad = numPatches - count
            inputs[-to_pad:, :, :, :] = inputs[:to_pad, :, :, :]

        return inputs
