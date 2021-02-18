import numpy as np
import os.path
import time
import csv
import math

def getMasks(img, seeds, nbLabel, marginMask):
    """
    Return for each label a mask built with the two extremum seeds including the margin,
    excluding the background seeds that use a unique mask  
    """
    maskMin = np.ones(3, dtype=int)
    maskMax = np.array([img.shape[0], img.shape[1], img.shape[2]]) - maskMin
    marginMask = [marginMask] * 3
    masksByLabel = []
    for i in range(nbLabel-1):
        masksByLabel.append(np.array([maskMax, maskMin]))
    
    # Find the extremums for each label
    # If background seed : add mask by seed
    for seed in seeds:
        label = seed.get("label") - 1
        if label >= nbLabel - 1: # Back ground seed
            masksByLabel.append( [seed.get("pos"), seed.get("pos")] )
        else : 
            masksByLabel[label][0] = np.minimum(seed.get("pos"), masksByLabel[label][0])
            masksByLabel[label][1] = np.maximum(seed.get("pos"), masksByLabel[label][1])
        
    # Add the margin for each label
    for i in range(len(masksByLabel)):
        borneMin = np.array(masksByLabel[i][0]) - np.array(marginMask)
        borneMax = np.array(masksByLabel[i][1]) + np.array(marginMask)
        masksByLabel[i][0] = np.maximum(borneMin, maskMin)
        masksByLabel[i][1] = np.minimum(borneMax, maskMax)
    
    return masksByLabel

def getDistanceBetweenVoxel(Ip, Iq, gamma, R, p, q, imageSpacing):
    """
    Return the distance between two voxels depending on their intensities and the regularization cost
    """
    R = int(R)
    if p[0] != q[0]:
        delta = imageSpacing[0]
    elif p[1] != q[1]:
        delta = imageSpacing[1]
    elif p[2] != q[2]:
        delta = imageSpacing[2]
    return math.sqrt(delta * (math.pow(Ip - Iq, 2) + gamma * math.pow(R, 2)))


def isVoxelInMaskArea(mask, voxel):
    """
    Check if this voxel is in this mask
    """
    for i in range(len(voxel)):
        if voxel[i] < mask[0][i] or voxel[i] > mask[1][i]:
            return False
    return True  

def clip(x, xMin, xMax):
    """
    Return the clipped x value between the interval [xMin, xMax]
    """
    return max(xMin, min(x, xMax))

def segmentation(volume, voxels, R, seeds, nbLabel, marginMask, distance, gamma, regDiameter, threshold, 
    imgLabel=np.array([]), imgDist=np.array([])):
    """
    Return the label s image containing the voxels linked to each seed
    """

    # cp = cProfile.Profile()
    # cp.enable()
    start_time = time.time()
    
    masks = getMasks(voxels, seeds, nbLabel, marginMask)
    
    # Labels image
    if len(imgLabel) == 0:
        imgLabel = np.ndarray(shape=voxels.shape, dtype=int)
        imgLabel.fill(0)

    # Distances image
    if len(imgDist) == 0:
        imgDist = np.ndarray(shape=voxels.shape, dtype=float)
        imgDist.fill(distance)
    
    # Visited voxels image
    imgVisitedVoxels = np.zeros(voxels.shape, dtype=int)

    # Lists voxels to visit now and the next iteration 
    listCurrentVoxels = []
    listNextVoxels = []
    
    # Initialize the images with the given seeds 
    for l in range(len(seeds)):
        pos = seeds[l].get("pos")
        listNextVoxels.append([pos[0], pos[1], pos[2]])
        imgDist[pos[0], pos[1], pos[2]] = 0
        imgLabel[pos[0], pos[1], pos[2]] = seeds[l].get("label")
        
    imageSpacing = volume.GetSpacing()

    voisins = [np.array([-1, 0, 0]), np.array([1, 0, 0]), np.array([0, -1, 0]), np.array([0, 0, -1]), np.array([0, 1, 0]), np.array([0, 0, 1])]

    while listNextVoxels != []:
        listCurrentVoxels = list(listNextVoxels)
        listNextVoxels = []
        imgVisitedVoxels[1:-1,1:-1,1:-1] = 0
        
        for p in listCurrentVoxels:
            voxelP = voxels[p[0], p[1], p[2]]
            label_p = imgLabel[p[0], p[1], p[2]]
            m = masks[label_p - 1]                

            # Compute distance between neighbors voxels
            for v in voisins:
                q = np.add(p, v)
                voxelQ = voxels[q[0], q[1], q[2]]

                if not isVoxelInMaskArea(m, [q[0], q[1], q[2]]) or imgVisitedVoxels[q[0], q[1], q[2]] == 1 or voxelQ < threshold[0] or voxelQ > threshold[1]:
                    continue

                DistBetweenVoxels = getDistanceBetweenVoxel(voxelP, voxelQ, gamma, R[q[0], q[1], q[2]], p, q, imageSpacing)
                DistToSeed = imgDist[p[0], p[1], p[2]]+DistBetweenVoxels

                if imgDist[q[0], q[1], q[2]] > DistToSeed:    #remark : imgDist is initialized to distance everywhere, except at the seed locations
                    imgDist[q[0], q[1], q[2]] = DistToSeed
                    imgLabel[q[0], q[1], q[2]] = label_p
                    listNextVoxels.append(q)
                    imgVisitedVoxels[q[0], q[1], q[2]] = 1

    imgLabel = np.clip(imgLabel, 0, nbLabel)

    print("- Segmentation time :   %s seconds -" % (time.time() - start_time))
    return imgLabel, imgDist