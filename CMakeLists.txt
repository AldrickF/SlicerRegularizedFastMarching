cmake_minimum_required(VERSION 3.13.4)

project(RegularizedFastMarching)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/RegularizedFastMarching")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Aldrick FAURE (IMT)")
set(EXTENSION_DESCRIPTION "This module performs a regularized fast marching segmentation on volumes. Seeds can be set manually or from file. Seeds label can be set from csv file.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/AldrickF/SlicerRegularizedFastMarching/main/RegularizedFastMarching/Resources/Icons/RegularizedFastMarching.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/AldrickF/SlicerRegularizedFastMarching/main/Docs/SlicerRFM_README_Fig3.png https://raw.githubusercontent.com/AldrickF/SlicerRegularizedFastMarching/main/Docs/SlicerRFM_README_Fig2.png https://raw.githubusercontent.com/AldrickF/SlicerRegularizedFastMarching/main/Docs/SlicerRFM_README_Fig4.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(RegularizedFastMarching)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
