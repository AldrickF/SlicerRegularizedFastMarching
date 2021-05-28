#-----------------------------------------------------------------------------
set(MODULE_NAME RegularizedFastMarching)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  RegularizedFastMarchingLib/__init__.py
  RegularizedFastMarchingLib/Segmentation.py
  RegularizedFastMarchingLib/Regularization.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  Resources/SegmentationFastMarching/Regularizations/.gitkeep
  Resources/SegmentationFastMarching/Seeds/.gitkeep
  Resources/SegmentationFastMarching/Seeds/three.seed
  Resources/SegmentationFastMarching/SeedsLabels/.gitkeep
  Resources/SegmentationFastMarching/SeedsLabels/SeedsNamesLabels_binary.csv
  Resources/SegmentationFastMarching/SeedsLabels/SeedsNamesLabels_brain.csv
  Resources/SegmentationFastMarching/SeedsLabels/SeedsNamesLabels_ganglions.csv
  Resources/SegmentationFastMarching/Segmentations/.gitkeep
  Resources/SegmentationFastMarching/Volumes/.gitkeep
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
