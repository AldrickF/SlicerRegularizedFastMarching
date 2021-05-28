def regularization(InputImage, StructuringElementRadius=3):
    """
    Compute the 3D scalar field that will be used to regularize the seeds propagation
    Inputs:
      * InputImage: the 3D image that will be segmented. Must be a 3D numpy array.
      * StructuringElementRadius: A structuring element of size (1+2*StructuringElementRadius) x (1+2*StructuringElementRadius) x (1+2*StructuringElementRadius) will be used
    Outputs:
      * R: The 3D numpy array having the same size as InputImage, used for the regularization
    """

    from scipy import ndimage
    MSE = StructuringElementRadius
    return ndimage.morphological_gradient(InputImage, size=(MSE, MSE, MSE))