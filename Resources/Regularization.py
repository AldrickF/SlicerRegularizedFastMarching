
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#STEP 1: FUNCTIONS TO COMPUTE THE REGULARIZATION FIELD
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def Dilation_3D_array(InputArray,RSE):
  """
  Perform the dilation of a 3D array
  InputArray: is a 3D array
  RadiusStructuringElement: Radius of the structuring element -> The structuring element is a cube of size (1+2*RSE) x (1+2*RSE) x (1+2*RSE)
  """

  #1) init
  DilatedArray_tmp=InputArray.copy()
  DilatedArray=InputArray.copy()
  [NX,NY,NZ]=InputArray.shape

  #2) dilation on the 1st axis
  #2.1) first slices
  DataInSE=DilatedArray_tmp[0:2*RSE+1,:,:]
  Max_DataInSE=DataInSE.max(axis=0)

  for slice_ID in range(0,RSE+1):
      DilatedArray[slice_ID,:,:]=Max_DataInSE[:,:]

  #2.2) middle slices
  NewSlice_in_OrigImage=2*RSE+1
  LastSlice_in_SlidingWindow=0
  for slice_ID in  range(RSE+1,NX-RSE):
      #get data
      DataInSE[LastSlice_in_SlidingWindow,:,:]=DilatedArray_tmp[NewSlice_in_OrigImage,:,:]

      #compute the max
      Max_DataInSE=DataInSE.max(axis=0)

      #update DilatedArray
      DilatedArray[slice_ID,:,:]=Max_DataInSE[:,:]

      #prepare the next iteration
      NewSlice_in_OrigImage+=1
      LastSlice_in_SlidingWindow+=1
      if LastSlice_in_SlidingWindow>2*RSE:
          LastSlice_in_SlidingWindow=0

  #2.3) last slices
  for slice_ID in  range(NX-RSE,NX):
      DilatedArray[slice_ID,:,:]=Max_DataInSE[:,:]

  #3) dilation on the 2nd axis

  #3.0) init
  DilatedArray_tmp=DilatedArray.copy()

  #3.1) first slices
  DataInSE=DilatedArray_tmp[:,0:2*RSE+1,:]
  Max_DataInSE=DataInSE.max(axis=1)

  for slice_ID in range(0,RSE+1):
      DilatedArray[:,slice_ID,:]=Max_DataInSE[:,:]

  #3.2) middle slices
  NewSlice_in_OrigImage=2*RSE+1
  LastSlice_in_SlidingWindow=0
  for slice_ID in  range(RSE+1,NY-RSE):
      #get data
      DataInSE[:,LastSlice_in_SlidingWindow,:]=DilatedArray_tmp[:,NewSlice_in_OrigImage,:]

      #compute the max
      Max_DataInSE=DataInSE.max(axis=1)

      #update DilatedArray
      DilatedArray[:,slice_ID,:]=Max_DataInSE[:,:]

      #prepare the next iteration
      NewSlice_in_OrigImage+=1
      LastSlice_in_SlidingWindow+=1
      if LastSlice_in_SlidingWindow>2*RSE:
          LastSlice_in_SlidingWindow=0

  #3.3) last slices
  for slice_ID in  range(NY-RSE,NY):
      DilatedArray[:,slice_ID,:]=Max_DataInSE[:,:]

  #4) dilation on the 3rd axis

  #4.0) init
  DilatedArray_tmp=DilatedArray.copy()

  #4.1) first slices
  DataInSE=DilatedArray_tmp[:,:,0:2*RSE+1]
  Max_DataInSE=DataInSE.max(axis=2)

  for slice_ID in range(0,RSE+1):
      DilatedArray[:,:,slice_ID]=Max_DataInSE[:,:]

  #4.2) middle slices
  NewSlice_in_OrigImage=2*RSE+1
  LastSlice_in_SlidingWindow=0
  for slice_ID in  range(RSE+1,NZ-RSE):
      #get data
      DataInSE[:,:,LastSlice_in_SlidingWindow]=DilatedArray_tmp[:,:,NewSlice_in_OrigImage]

      #compute the max
      Max_DataInSE=DataInSE.max(axis=2)

      #update DilatedArray
      DilatedArray[:,:,slice_ID]=Max_DataInSE[:,:]

      #prepare the next iteration
      NewSlice_in_OrigImage+=1
      LastSlice_in_SlidingWindow+=1
      if LastSlice_in_SlidingWindow>2*RSE:
          LastSlice_in_SlidingWindow=0

  #4.3) last slices
  for slice_ID in  range(NZ-RSE,NZ):
      DilatedArray[:,:,slice_ID]=Max_DataInSE[:,:]


  return DilatedArray


def Erosion_3D_array(InputArray,RSE):
  """
  Perform the erosion of a 3D array
  InputArray: is a 3D array
  RadiusStructuringElement: Radius of the structuring element -> The structuring element is a cube of size (1+2*RSE) x (1+2*RSE) x (1+2*RSE)
  """

  #1) init
  ErodedArray_tmp=InputArray.copy()
  ErodedArray=InputArray.copy()
  [NX,NY,NZ]=InputArray.shape

  #2) dilation on the 1st axis
  #2.1) first slices
  DataInSE=ErodedArray_tmp[0:2*RSE+1,:,:]
  Min_DataInSE=DataInSE.min(axis=0)

  for slice_ID in range(0,RSE+1):
      ErodedArray[slice_ID,:,:]=Min_DataInSE[:,:]

  #2.2) middle slices
  NewSlice_in_OrigImage=2*RSE+1
  LastSlice_in_SlidingWindow=0
  for slice_ID in  range(RSE+1,NX-RSE):
      #get data
      DataInSE[LastSlice_in_SlidingWindow,:,:]=ErodedArray_tmp[NewSlice_in_OrigImage,:,:]

      #compute the min
      Min_DataInSE=DataInSE.min(axis=0)

      #update ErodedArray
      ErodedArray[slice_ID,:,:]=Min_DataInSE[:,:]

      #prepare the next iteration
      NewSlice_in_OrigImage+=1
      LastSlice_in_SlidingWindow+=1
      if LastSlice_in_SlidingWindow>2*RSE:
          LastSlice_in_SlidingWindow=0

  #2.3) last slices
  for slice_ID in  range(NX-RSE,NX):
      ErodedArray[slice_ID,:,:]=Min_DataInSE[:,:]

  #3) dilation on the 2nd axis

  #3.0) init
  ErodedArray_tmp=ErodedArray.copy()

  #3.1) first slices
  DataInSE=ErodedArray_tmp[:,0:2*RSE+1,:]
  Min_DataInSE=DataInSE.min(axis=1)

  for slice_ID in range(0,RSE+1):
      ErodedArray[:,slice_ID,:]=Min_DataInSE[:,:]

  #3.2) middle slices
  NewSlice_in_OrigImage=2*RSE+1
  LastSlice_in_SlidingWindow=0
  for slice_ID in  range(RSE+1,NY-RSE):
      #get data
      DataInSE[:,LastSlice_in_SlidingWindow,:]=ErodedArray_tmp[:,NewSlice_in_OrigImage,:]

      #compute the min
      Min_DataInSE=DataInSE.min(axis=1)

      #update ErodedArray
      ErodedArray[:,slice_ID,:]=Min_DataInSE[:,:]

      #prepare the next iteration
      NewSlice_in_OrigImage+=1
      LastSlice_in_SlidingWindow+=1
      if LastSlice_in_SlidingWindow>2*RSE:
          LastSlice_in_SlidingWindow=0

  #3.3) last slices
  for slice_ID in  range(NY-RSE,NY):
      ErodedArray[:,slice_ID,:]=Min_DataInSE[:,:]

  #4) dilation on the 3rd axis

  #4.0) init
  ErodedArray_tmp=ErodedArray.copy()

  #4.1) first slices
  DataInSE=ErodedArray_tmp[:,:,0:2*RSE+1]
  Min_DataInSE=DataInSE.min(axis=2)

  for slice_ID in range(0,RSE+1):
      ErodedArray[:,:,slice_ID]=Min_DataInSE[:,:]

  #4.2) middle slices
  NewSlice_in_OrigImage=2*RSE+1
  LastSlice_in_SlidingWindow=0
  for slice_ID in  range(RSE+1,NZ-RSE):
      #get data
      DataInSE[:,:,LastSlice_in_SlidingWindow]=ErodedArray_tmp[:,:,NewSlice_in_OrigImage]

      #compute the min
      Min_DataInSE=DataInSE.min(axis=2)

      #update ErodedArray
      ErodedArray[:,:,slice_ID]=Min_DataInSE[:,:]

      #prepare the next iteration
      NewSlice_in_OrigImage+=1
      LastSlice_in_SlidingWindow+=1
      if LastSlice_in_SlidingWindow>2*RSE:
          LastSlice_in_SlidingWindow=0

  #4.3) last slices
  for slice_ID in  range(NZ-RSE,NZ):
      ErodedArray[:,:,slice_ID]=Min_DataInSE[:,:]


  return ErodedArray






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

    # DilatedArray=Dilation_3D_array(InputImage,StructuringElementRadius)
    # ErrodedArray=Erosion_3D_array(InputImage,StructuringElementRadius)

    # return DilatedArray-ErrodedArray