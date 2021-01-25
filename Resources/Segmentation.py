import numpy as np
import os.path
import time
import csv

import math

from Resources.Regularization import *

# import cProfile, pstats, io

def getListIJKToRas(inputVolume, points):
    """
    """
    for i in range(len(points)): # pour chaque point 
        points[i] = getIJKToRas(inputVolume, points[i])

    return points

def getIJKToRas(inputVolume, point):
    """
    """
    # Get voxel position in IJK coordinate system
    point_Kji = point
    point_Ijk = [point_Kji[2], point_Kji[1], point_Kji[0]]
    
    # Get physical coordinates from voxel coordinates
    volumeIjkToRas = vtk.vtkMatrix4x4()
    inputVolume.GetIJKToRASMatrix(volumeIjkToRas)
    point_VolumeRas = [0, 0, 0, 1]
    volumeIjkToRas.MultiplyPoint(np.append(point_Ijk,1.0), point_VolumeRas)
    
    # If volume node is transformed, apply that transform to get volume's RAS coordinates
    transformVolumeRasToRas = vtk.vtkGeneralTransform()
    slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(inputVolume.GetParentTransformNode(), None, transformVolumeRasToRas)
    return transformVolumeRasToRas.TransformPoint(point_VolumeRas[0:3])
    
######
######

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
    # delta = imageSpacing[2]/imageSpacing[0] if p[2] != q[2] else 1
    
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
    # return mask[voxel[0], voxel[1], voxel[2]] == 1
    for i in range(len(voxel)):
        if voxel[i] < mask[0][i] or voxel[i] > mask[1][i]:
            return False
    return True  

def clip(x, xMin, xMax):
    """
    Return the clipped x value between the interval [xMin, xMax]
    """
    return max(xMin, min(x, xMax))

def segmentation(globalPath, volume, voxels, seeds, nbLabel, marginMask, distance, gamma, regDiameter, threshold, 
    imgLabel=np.array([]), imgIds=np.array([]), imgDist=np.array([])):
    """
    Return the label s image containing the voxels linked to each seed
    """
    ###### Preparation des donnees 
    
    # cp = cProfile.Profile()
    # cp.enable()

    # Creation des masques en fonction des positions des graines et taille max du mask
    masks = getMasks(voxels, seeds, nbLabel, marginMask)

    # Image des masques
    # imgMasks = np.zeros(voxels.shape, dtype=int)

    # for m in masks:
    #     imgMasks[m[0][0]:m[1][0], m[0][1]:m[1][1], m[0][2]:m[1][2]] = 1
    
    # Map de regularisation - dilatation de l'image
    start_time = time.time()
    R = np.copy(voxels)

    # Verifie si cette regularisation a deja ete faite    
    regularizationFile = globalPath + "Regularizations/" + volume.GetName() + "_" + str(regDiameter) + ".regu.npy"
    if os.path.isfile(regularizationFile):
        print("--- Alredy existing regularization")
        R = np.load(regularizationFile)
    else :
        # R = np.copy(voxels)
        print("- Creating new regularization start : ")
        R = regularization(voxels, int(regDiameter/2))
        print("- Creating new regularization end")
        np.save(regularizationFile, R)
    reguliarization_time = time.time() - start_time
    print("- Regularization time : %s seconds -" % reguliarization_time)
    
    ###### Affichage de l'initialisation
    print("Nombre de seeds : " + str(len(seeds)))
    print("Gamme : " + str(gamma))
    # print("Seeds : " + str(seeds))
    # print("Voxels shape : " + str(voxels.shape))
    # print("Masques :", masks)

    ###### Algorithme
    start_time = time.time()
    
    # Image des labels
    if len(imgLabel) == 0:
        imgLabel = np.ndarray(shape=voxels.shape, dtype=int)
        imgLabel.fill(0)

    # Image des ids
    # if len(imgIds) == 0:
    #     imgIds = np.ndarray(shape=voxels.shape, dtype=int)
    #     imgIds.fill(0)

    # Image des distances
    if len(imgDist) == 0:
        imgDist = np.ndarray(shape=voxels.shape, dtype=float)
        imgDist.fill(distance)
    
    # Image des voxels parcourus
    imgVoxelParcourus = np.zeros(voxels.shape, dtype=int)
    
    # Liste des voxels courant a parcourir
    listCurrentVoxels = []
    # Liste des prochains voxels a parcourir
    listNextVoxels = []
    
    # Initialisation des images avec les graines
    for l in range(len(seeds)):
        pos = seeds[l].get("pos")
        listNextVoxels.append([pos[0], pos[1], pos[2]])
        imgDist[pos[0], pos[1], pos[2]] = 0
        imgLabel[pos[0], pos[1], pos[2]] = seeds[l].get("label")
        # imgIds[pos[0], pos[1], pos[2]] = seeds[l].get("id")
        
    imageSpacing = volume.GetSpacing()

    voisins = [np.array([-1, 0, 0]), np.array([1, 0, 0]), np.array([0, -1, 0]), np.array([0, 0, -1]), np.array([0, 1, 0]), np.array([0, 0, 1])]

    while listNextVoxels != []:

        listCurrentVoxels = list(listNextVoxels)
        listNextVoxels = []                    # Liste des prochains voxels a parcourir

        imgVoxelParcourus[1:-1,1:-1,1:-1] = 0    #masque compagnon de listNextVoxels
        
        for p in listCurrentVoxels:
            voxelP = voxels[p[0], p[1], p[2]]
            label_p = imgLabel[p[0], p[1], p[2]]
            # id_p = imgIds[p[0], p[1], p[2]]
            m = masks[label_p - 1]                

            # Calcul la distance des voxels voisins
            for v in voisins:
                q = np.add(p, v)
                voxelQ = voxels[q[0], q[1], q[2]]
    
                # imgVoxelParcourus[q[0], q[1], q[2]] == 1
                if not isVoxelInMaskArea(m, [q[0], q[1], q[2]]) or imgVoxelParcourus[q[0], q[1], q[2]] == 1 or voxelQ < threshold[0] or voxelQ > threshold[1]:
                    continue

                DistBetweenVoxels = getDistanceBetweenVoxel(voxelP, voxelQ, gamma, R[q[0], q[1], q[2]], p, q, imageSpacing)
                DistToSeed = imgDist[p[0], p[1], p[2]]+DistBetweenVoxels

                if imgDist[q[0], q[1], q[2]] > DistToSeed:    #remark : imgDist is initialized to distance everywhere, except at the seed locations
                    imgDist[q[0], q[1], q[2]] = DistToSeed
                    imgLabel[q[0], q[1], q[2]] = label_p
                    # imgIds[q[0], q[1], q[2]] = id_p
                    listNextVoxels.append(q)
                    # imgVoxelParcourus[q[0], q[1], q[2]] = 1
                    imgVoxelParcourus[q[0], q[1], q[2]] = 1

    imgLabel = np.clip(imgLabel, 0, nbLabel)

    # cp.disable()
    # #s = io.StringIO()
    # f = open(globalPath + 'segm.prof', 'w+')
    # sortby = 'cumulative'
    # ps = pstats.Stats(cp, stream=f).sort_stats(sortby).print_stats()
    # f.close()

    #print(s.getvalue())

    ###### Affichage des resultats
    print("- Regularization time : %s seconds -" % reguliarization_time)
    print("- Segmentation time :   %s seconds -" % (time.time() - start_time))

    return imgLabel, imgIds, imgDist