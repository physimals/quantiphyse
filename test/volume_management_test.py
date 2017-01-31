import unittest
import os
import sys
import numpy as np

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(TEST_DIR))
from pkview.volumes.volume_management import Volume, Overlay, Roi, ImageVolumeManagement

TEST_VOLUME = "dce"
TEST_OVERLAY = "overlay"
TEST_ROI = "roi"
TEST_NX = 64
TEST_NY = 64
TEST_NZ = 42
TEST_NT = 106

def test_fn(x, y, z, t=None):
    v = - (x - (TEST_NX / 2) ** 2 - (y - (TEST_NY / 2)) ** 2 + (z - (TEST_NZ / 2)) ** 2)
    if t is not None: v -= (t - (TEST_NT / 2)) ** 2
    return v

TEST_DATA_3D = np.fromfunction(test_fn, [TEST_NX, TEST_NY, TEST_NZ], dtype=np.float)
TEST_DATA_4D = np.fromfunction(test_fn, [TEST_NX, TEST_NY, TEST_NZ, TEST_NT], dtype=np.float)

TEST_DATA_ROI_ALL = np.ones([TEST_NX, TEST_NY, TEST_NZ])
d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
d[0, 0, 0] = 1
TEST_DATA_ROI_SINGLE = d
d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
d[0, 0, 0] = 1
d[0, 0, 1] = 1
TEST_DATA_ROI_PART = d
TEST_DATA_ROI_RAND= np.random.randint(0, 2, [TEST_NX, TEST_NY, TEST_NZ])

class VolumeTest(unittest.TestCase):

    def setUp(self):
        self.v4d = Volume("testvol", data=TEST_DATA_4D)
        self.v3d = Volume("testvol", data=TEST_DATA_3D)

    def testCheckShape4d4dPass(self):
        self.v4d.check_shape([TEST_NX, TEST_NY, TEST_NZ, TEST_NT])

    def testCheckShape4d4dFail1(self):
        self.assertRaises(Exception, self.v4d.check_shape, [TEST_NX+1, TEST_NY, TEST_NZ, TEST_NT])

    def testCheckShape4d4dFail2(self):
        self.assertRaises(Exception, self.v4d.check_shape, [TEST_NX, TEST_NY+1, TEST_NZ, TEST_NT])

    def testCheckShape4d4dFail3(self):
        self.assertRaises(Exception, self.v4d.check_shape, [TEST_NX, TEST_NY, TEST_NZ+1, TEST_NT])

    def testCheckShape4d4dFail4(self):
        self.assertRaises(Exception, self.v4d.check_shape, [TEST_NX, TEST_NY, TEST_NZ, TEST_NT+1])

    def testCheckShape4d3dPass(self):
        self.v4d.check_shape([TEST_NX, TEST_NY, TEST_NZ])

    def testCheckShape4d3dFail1(self):
        self.assertRaises(Exception, self.v4d.check_shape, [TEST_NX+1, TEST_NY, TEST_NZ])

    def testCheckShape4d3dFail2(self):
        self.assertRaises(Exception, self.v4d.check_shape, [TEST_NX, TEST_NY+1, TEST_NZ])

    def testCheckShape4d3dFail3(self):
        self.assertRaises(Exception, self.v4d.check_shape, [TEST_NX, TEST_NY, TEST_NZ+1])

    def testCheckShape3d4dPass(self):
        self.v3d.check_shape([TEST_NX, TEST_NY, TEST_NZ, TEST_NT])

    def testCheckShape3d4dFail1(self):
        self.assertRaises(Exception, self.v3d.check_shape, [TEST_NX+1, TEST_NY, TEST_NZ, TEST_NT])

    def testCheckShape3d4dFail2(self):
        self.assertRaises(Exception, self.v3d.check_shape, [TEST_NX, TEST_NY+1, TEST_NZ, TEST_NT])

    def testCheckShape3d4dFail3(self):
        self.assertRaises(Exception, self.v3d.check_shape, [TEST_NX, TEST_NY, TEST_NZ+1, TEST_NT])

    def testCheckShape3d4dPass2(self):
        self.v3d.check_shape([TEST_NX, TEST_NY, TEST_NZ, TEST_NT+1])

    def test4dData(self):
        self.assertEquals(self.v4d.name, "testvol")
        self.assertEquals(4, self.v4d.ndims)
        self.assertEquals(4, len(self.v4d.shape))
        self.assertEquals(TEST_NX, self.v4d.shape[0])
        self.assertEquals(TEST_NY, self.v4d.shape[1])
        self.assertEquals(TEST_NZ, self.v4d.shape[2])
        self.assertEquals(TEST_NT, self.v4d.shape[3])
        self.assertEquals(1, self.v4d.voxel_sizes[0])
        self.assertEquals(1, self.v4d.voxel_sizes[1])
        self.assertEquals(1, self.v4d.voxel_sizes[2])
        self.assertEquals(1, self.v4d.voxel_sizes[3])
        self.assertEquals(np.min(TEST_DATA_4D), self.v4d.range[0])
        self.assertEquals(np.max(TEST_DATA_4D), self.v4d.range[1])

    def test3dData(self):
        self.assertEquals(self.v3d.name, "testvol")
        self.assertEquals(3, self.v3d.ndims)
        self.assertEquals(3, len(self.v3d.shape))
        self.assertEquals(TEST_NX, self.v3d.shape[0])
        self.assertEquals(TEST_NY, self.v3d.shape[1])
        self.assertEquals(TEST_NZ, self.v3d.shape[2])
        self.assertEquals(1, self.v3d.voxel_sizes[0])
        self.assertEquals(1, self.v3d.voxel_sizes[1])
        self.assertEquals(1, self.v3d.voxel_sizes[2])
        self.assertEquals(np.min(TEST_DATA_3D), self.v3d.range[0])
        self.assertEquals(np.max(TEST_DATA_3D), self.v3d.range[1])

    def testLoadNii4d(self):
        fname = os.path.join(TEST_DIR, "data/%s.nii" % TEST_VOLUME)
        v = Volume("testvol", fname=fname)
        self.assertEquals(v.fname, fname)
        self.assertEquals(4, v.ndims)
        self.assertEquals(TEST_NX, v.shape[0])
        self.assertEquals(TEST_NY, v.shape[1])
        self.assertEquals(TEST_NZ, v.shape[2])
        self.assertEquals(TEST_NT, v.shape[3])

    def testLoadNiiGz4d(self):
        fname = os.path.join(TEST_DIR, "data/%s.nii.gz" % TEST_VOLUME)
        v = Volume("testvol", fname=fname)
        self.assertEquals(v.fname, fname)
        self.assertEquals(4, v.ndims)
        self.assertEquals(TEST_NX, v.shape[0])
        self.assertEquals(TEST_NY, v.shape[1])
        self.assertEquals(TEST_NZ, v.shape[2])
        self.assertEquals(TEST_NT, v.shape[3])

    def testLoadNiiGz3d(self):
        fname = os.path.join(TEST_DIR, "data/%s.nii.gz" % TEST_OVERLAY)
        v = Volume("testvol", fname=fname)
        self.assertEquals(v.fname, fname)
        self.assertEquals(3, v.ndims)
        self.assertEquals(TEST_NX, v.shape[0])
        self.assertEquals(TEST_NY, v.shape[1])
        self.assertEquals(TEST_NZ, v.shape[2])

    def testLoadNoFile(self):
        self.assertRaises(Exception, Volume, "testvol", fname="")

    def testLoadFileNotFound(self):
        fname = os.path.join(TEST_DIR, "data/does_not_exist.nii")
        self.assertRaises(Exception, Volume, "testvol", fname=fname)

    def testLoadInvalidFileType(self):
        fname = os.path.join(TEST_DIR, "data/broken.nii")
        self.assertRaises(Exception, Volume, "testvol", fname=fname)

    def testSave4d(self):
        fname = os.path.join(TEST_DIR, "data/saved4d.nii")
        self.v4d.save_nifti(fname)
        self.assertTrue(os.path.exists(fname))
        os.remove(fname)

    def testSave3d(self):
        fname = os.path.join(TEST_DIR, "data/saved3d.nii")
        self.v3d.save_nifti(fname)
        self.assertTrue(os.path.exists(fname))
        os.remove(fname)

    def testDir(self):
        fname = os.path.join(TEST_DIR, "data/%s.nii.gz" % TEST_OVERLAY)
        v = Volume("testvol", fname=fname)
        self.assertEquals(v.dir, os.path.join(TEST_DIR, "data"))

    def testDirNoFile(self):
        self.assertEquals(self.v3d.dir, None)

    def testBasename(self):
        fname = os.path.join(TEST_DIR, "data/%s.nii.gz" % TEST_OVERLAY)
        v = Volume("testvol", fname=fname)
        self.assertEquals(v.basename, "%s.nii.gz" % TEST_OVERLAY)

    def testBasenameNoFile(self):
        self.assertEquals(self.v3d.basename, None)

class OverlayTest(unittest.TestCase):

    def setUp(self):
        pass

    def test3dData(self):
        v = Overlay("testovl", data=TEST_DATA_3D)
        self.assertEquals(v.name, "testovl")
        self.assertEquals(3, v.ndims)
        self.assertEquals(3, len(v.shape))
        self.assertEquals(TEST_NX, v.shape[0])
        self.assertEquals(TEST_NY, v.shape[1])
        self.assertEquals(TEST_NZ, v.shape[2])
        self.assertEquals(1, v.voxel_sizes[0])
        self.assertEquals(1, v.voxel_sizes[1])
        self.assertEquals(1, v.voxel_sizes[2])
        self.assertEquals(np.min(TEST_DATA_3D), v.range[0])
        self.assertEquals(np.max(TEST_DATA_3D), v.range[1])
        self.assertEquals(np.min(TEST_DATA_3D), v.range_roi[0])
        self.assertEquals(np.max(TEST_DATA_3D), v.range_roi[1])

    def testSetRoi(self):
        v = Overlay("testovl", data=TEST_DATA_3D)
        roi = Roi("testroi", data=TEST_DATA_ROI_SINGLE)
        v.set_roi(roi)
        self.assertEquals(v.data[0,0,0], v.range_roi[0])
        self.assertEquals(v.data[0,0,0], v.range_roi[1])
        self.assertFalse(np.array_equal(v.data, v.data_roi))

class RoiTest(unittest.TestCase):

    def testNoMasking(self):
        v = Roi("testroi", data=TEST_DATA_ROI_ALL)
        self.assertEquals(v.name, "testroi")
        self.assertEquals(3, v.ndims)
        self.assertEquals(3, len(v.shape))
        self.assertEquals(TEST_NX, v.shape[0])
        self.assertEquals(TEST_NY, v.shape[1])
        self.assertEquals(TEST_NZ, v.shape[2])
        self.assertEquals(1, v.voxel_sizes[0])
        self.assertEquals(1, v.voxel_sizes[1])
        self.assertEquals(1, v.voxel_sizes[2])
        self.assertEquals(1, v.range[0])
        self.assertEquals(1, v.range[1])
        self.assertEquals(1, len(v.regions))
        self.assertEquals(1, v.regions[0])

    def testSingleVoxel(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        v = Roi("testroi", data=d)
        self.assertEquals(0, v.range[0])
        self.assertEquals(1, v.range[1])
        self.assertEquals(1, len(v.regions))
        self.assertEquals(1, v.regions[0])

    def testMultiVoxel(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        d[0,0,1] = 1
        v = Roi("testroi", data=d)
        self.assertEquals(0, v.range[0])
        self.assertEquals(1, v.range[1])
        self.assertEquals(1, len(v.regions))
        self.assertEquals(1, v.regions[0])

    def testMultiLevels(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        d[0,0,1] = 2
        v = Roi("testroi", data=d)
        self.assertEquals(0, v.range[0])
        self.assertEquals(2, v.range[1])
        self.assertEquals(2, len(v.regions))
        self.assertEquals(1, v.regions[0])
        self.assertEquals(2, v.regions[1])

    def testGetLutSingleLevelNoAlpha(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        v = Roi("testroi", data=d)
        lut = v.get_lut()
        self.assertEquals(2, len(lut))
        for rgba in lut:
            self.assertEquals(3, len(rgba))

    def testGetLutSingleLevelNoAlphaSkip(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 2
        v = Roi("testroi", data=d)
        lut = v.get_lut()
        self.assertEquals(3, len(lut))
        for rgba in lut:
            self.assertEquals(3, len(rgba))

    def testGetLutMultiLevelNoAlpha(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        d[0, 0, 1] = 2
        v = Roi("testroi", data=d)
        lut = v.get_lut()
        self.assertEquals(3, len(lut))
        for rgba in lut:
            self.assertEquals(3, len(rgba))

    def testGetLutMultiLevelNoAlphaSkip(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        d[0, 0, 1] = 3
        v = Roi("testroi", data=d)
        lut = v.get_lut()
        self.assertEquals(4, len(lut))
        for rgba in lut:
            self.assertEquals(3, len(rgba))

    def testGetLutSingleLevelAlpha(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        v = Roi("testroi", data=d)
        lut = v.get_lut(alpha=123)
        self.assertEquals(2, len(lut))
        for idx, rgba in enumerate(lut):
            self.assertEquals(4, len(rgba))
            if idx == 0:
                self.assertEquals(0, rgba[3])
            else:
                self.assertEquals(123, rgba[3])

    def testGetLutSingleLevelAlphaSkip(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 2
        v = Roi("testroi", data=d)
        lut = v.get_lut(alpha=123)
        self.assertEquals(3, len(lut))
        for idx, rgba in enumerate(lut):
            self.assertEquals(4, len(rgba))
            if idx == 0:
                self.assertEquals(0, rgba[3])
            else:
                self.assertEquals(123, rgba[3])

    def testGetLutMultiLevelAlpha(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        d[0, 0, 1] = 2
        v = Roi("testroi", data=d)
        lut = v.get_lut(alpha=123)
        self.assertEquals(3, len(lut))
        for idx, rgba in enumerate(lut):
            self.assertEquals(4, len(rgba))
            if idx == 0:
                self.assertEquals(0, rgba[3])
            else:
                self.assertEquals(123, rgba[3])

    def testGetLutMultiLevelAlphaSkip(self):
        d = np.zeros([TEST_NX, TEST_NY, TEST_NZ])
        d[0,0,0] = 1
        d[0, 0, 1] = 3
        v = Roi("testroi", data=d)
        lut = v.get_lut(alpha=123)
        self.assertEquals(4, len(lut))
        for idx, rgba in enumerate(lut):
            self.assertEquals(4, len(rgba))
            if idx == 0:
                self.assertEquals(0, rgba[3])
            else:
                self.assertEquals(123, rgba[3])

    def testSaveRoi(self):
        v = Roi("testroi", data=TEST_DATA_ROI_RAND)
        fname = os.path.join(TEST_DIR, "data/savedroi.nii")
        v.save_nifti(fname)
        self.assertTrue(os.path.exists(fname))
        os.remove(fname)

class VolumeManagementTest(unittest.TestCase):

    def setUp(self):
        self.ivm = ImageVolumeManagement()
        self.ivm.sig_main_volume.connect(self.main_volume_slot)
        self.ivm.sig_current_overlay.connect(self.current_overlay_slot)
        self.ivm.sig_current_roi.connect(self.current_roi_slot)
        self.ivm.sig_all_overlays.connect(self.all_overlays_slot)
        self.ivm.sig_all_rois.connect(self.all_rois_slot)
        self.sigs_emitted = []
        self.vol = Volume("main", data=TEST_DATA_4D)

    def main_volume_slot(self, vol):
        self.sigs_emitted.append("main_volume")
        self.main_volume_obj = vol

    def current_overlay_slot(self, ovl):
        self.sigs_emitted.append("current_overlay")
        self.current_overlay_obj = ovl

    def all_overlays_slot(self, ovls):
        self.sigs_emitted.append("all_overlays")
        self.overlays_obj = ovls

    def current_roi_slot(self, roi):
        self.sigs_emitted.append("current_roi")
        self.current_roi_obj = roi

    def all_rois_slot(self, rois):
        self.sigs_emitted.append("all_rois")
        self.rois_obj = rois

    def testAddOverlay(self):
        self.ivm.set_main_volume(self.vol)
        ovl = Overlay("test", data=TEST_DATA_3D)
        self.ivm.add_overlay(ovl, make_current=True)
        self.assertTrue(self.ivm.current_overlay is not None)
        self.assertEquals(self.ivm.current_overlay.name, "test")
        self.assertEquals(3, self.ivm.current_overlay.ndims)
        self.assertEquals(TEST_NX, self.ivm.current_overlay.shape[0])
        self.assertEquals(TEST_NY, self.ivm.current_overlay.shape[1])
        self.assertEquals(TEST_NZ, self.ivm.current_overlay.shape[2])
        self.assertTrue(np.array_equal(ovl.data_roi, ovl.data))
        self.assertEquals(self.ivm.current_overlay, self.ivm.overlays[self.ivm.current_overlay.name])
        self.assertTrue("current_overlay" in self.sigs_emitted)
        self.assertTrue("all_overlays" in self.sigs_emitted)

    def testAddOverlayNotCurrent(self):
        self.ivm.set_main_volume(self.vol)
        ovl = Overlay("test", data=TEST_DATA_3D)
        self.ivm.add_overlay(ovl, make_current=False)
        self.assertTrue(self.ivm.current_overlay is None)
        self.assertEquals(ovl, self.ivm.overlays["test"])
        self.assertFalse("current_overlay" in self.sigs_emitted)
        self.assertTrue("all_overlays" in self.sigs_emitted)

    def testAddOverlayNoVolume(self):
        ovl = Overlay("test", data=TEST_DATA_3D)
        self.assertRaises(Exception, self.ivm.add_overlay, ovl)

    def testAddOverlayWrongDims(self):
        d = np.ones([TEST_NX, TEST_NY+1, TEST_NZ])
        ovl = Overlay("test", data=d)
        self.assertRaises(Exception, self.ivm.add_overlay, ovl)

    def testSetCurrentOverlay(self):
        self.ivm.set_main_volume(self.vol)
        overlay = Overlay("test_overlay", data=TEST_DATA_3D)
        self.ivm.add_overlay(overlay, make_current=False)
        self.assertFalse("current_overlay" in self.sigs_emitted)
        self.assertTrue(self.ivm.current_overlay is None)
        self.ivm.set_current_overlay("test_overlay")
        self.assertTrue(self.ivm.current_overlay is not None)
        self.assertEquals(self.ivm.current_overlay, overlay)
        self.assertTrue("current_overlay" in self.sigs_emitted)

    def testSetCurrentOverlayAlreadyCurrent(self):
        self.ivm.set_main_volume(self.vol)
        overlay = Overlay("test_overlay", data=TEST_DATA_3D)
        self.ivm.add_overlay(overlay, make_current=True)
        self.assertEquals(self.ivm.current_overlay, overlay)
        self.ivm.set_current_overlay("test_overlay")
        self.assertEquals(self.ivm.current_overlay, overlay)

    def testSetCurrentOverlayDifferent(self):
        self.ivm.set_main_volume(self.vol)
        overlay1 = Overlay("test_overlay", data=TEST_DATA_3D)
        self.ivm.add_overlay(overlay1, make_current=True)
        self.assertTrue("current_overlay" in self.sigs_emitted)
        overlay2 = Overlay("test_overlay2", data=TEST_DATA_3D)
        self.sigs_emitted = []
        self.ivm.add_overlay(overlay2, make_current=False)
        self.assertFalse("current_overlay" in self.sigs_emitted)
        self.assertEquals(self.ivm.current_overlay, overlay1)
        self.ivm.set_current_overlay("test_overlay2")
        self.assertEquals(self.ivm.current_overlay, overlay2)
        self.assertTrue("current_overlay" in self.sigs_emitted)

    def testSetCurrentOverlayWrongName(self):
        self.ivm.set_main_volume(self.vol)
        overlay = Overlay("test_overlay", data=TEST_DATA_3D)
        self.ivm.add_overlay(overlay, make_current=False)
        self.assertRaises(Exception, self.ivm.set_current_overlay, "test_overlay2")
        self.assertFalse("current_overlay" in self.sigs_emitted)

    def testSetCurrentOverlayNoVolume(self):
        self.assertRaises(Exception, self.ivm.set_current_overlay, "test_overlay")

    def testAddRoi(self):
        self.ivm.set_main_volume(self.vol)
        roi = Roi("test_roi", data=TEST_DATA_ROI_ALL)
        self.ivm.add_roi(roi, make_current=True)
        self.assertTrue(self.ivm.current_roi is not None)
        self.assertEquals(self.ivm.current_roi.name, "test_roi")
        self.assertEquals(3, self.ivm.current_roi.ndims)
        self.assertEquals(TEST_NX, self.ivm.current_roi.shape[0])
        self.assertEquals(TEST_NY, self.ivm.current_roi.shape[1])
        self.assertEquals(TEST_NZ, self.ivm.current_roi.shape[2])
        self.assertEquals(self.ivm.current_roi, self.ivm.rois[self.ivm.current_roi.name])
        self.assertTrue("current_roi" in self.sigs_emitted)
        self.assertTrue("all_rois" in self.sigs_emitted)

    def testAddRoiNotCurrent(self):
        self.ivm.set_main_volume(self.vol)
        roi = Roi("test_roi", data=TEST_DATA_ROI_ALL)
        self.ivm.add_roi(roi, make_current=False)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEquals(roi, self.ivm.rois["test_roi"])
        self.assertFalse("current_roi" in self.sigs_emitted)
        self.assertTrue("all_rois" in self.sigs_emitted)

    def testAddRoiNoVolume(self):
        roi = Roi("test_roi", data=TEST_DATA_ROI_ALL)
        self.assertRaises(Exception, self.ivm.add_roi, roi)

    def testAddRoiWrongDims(self):
        d = np.ones([TEST_NX, TEST_NY+1, TEST_NZ])
        roi = Roi("test", data=d)
        self.assertRaises(Exception, self.ivm.add_roi, roi)

    def testAddOverlayAndRoi(self):
        self.ivm.set_main_volume(self.vol)
        self.ivm.add_overlay(Overlay("test", data=TEST_DATA_3D), make_current=True)
        roi = Roi("test_roi", data=TEST_DATA_ROI_PART)
        self.ivm.add_roi(roi, make_current=True)
        self.assertFalse(np.array_equal(self.ivm.current_overlay.data_roi, self.ivm.current_overlay.data))

    def testSetCurrentRoi(self):
        self.ivm.set_main_volume(self.vol)
        roi = Roi("test_roi", data=TEST_DATA_ROI_ALL)
        self.ivm.add_roi(roi, make_current=False)
        self.assertFalse("current_roi" in self.sigs_emitted)
        self.assertTrue(self.ivm.current_roi is None)
        self.ivm.set_current_roi("test_roi")
        self.assertTrue(self.ivm.current_roi is not None)
        self.assertEquals(self.ivm.current_roi, roi)
        self.assertTrue("current_roi" in self.sigs_emitted)

    def testSetCurrentRoiAlreadyCurrent(self):
        self.ivm.set_main_volume(self.vol)
        roi = Roi("test_roi", data=TEST_DATA_ROI_ALL)
        self.ivm.add_roi(roi, make_current=True)
        self.assertEquals(self.ivm.current_roi, roi)
        self.ivm.set_current_roi("test_roi")
        self.assertEquals(self.ivm.current_roi, roi)
        self.assertTrue("current_roi" in self.sigs_emitted)

    def testSetCurrentRoiDifferent(self):
        self.ivm.set_main_volume(self.vol)
        roi1 = Roi("test_roi", data=TEST_DATA_ROI_ALL)
        self.ivm.add_roi(roi1, make_current=True)
        self.assertTrue("current_roi" in self.sigs_emitted)
        roi2 = Roi("test_roi2", data=TEST_DATA_ROI_PART)
        self.sigs_emitted = []
        self.ivm.add_roi(roi2, make_current=False)
        self.assertFalse("current_roi" in self.sigs_emitted)
        self.assertEquals(self.ivm.current_roi, roi1)
        self.ivm.set_current_roi("test_roi2")
        self.assertEquals(self.ivm.current_roi, roi2)
        self.assertTrue("current_roi" in self.sigs_emitted)

    def testSetCurrentRoiWrongName(self):
        self.ivm.set_main_volume(self.vol)
        roi = Roi("test_roi", data=TEST_DATA_ROI_ALL)
        self.ivm.add_roi(roi, make_current=False)
        self.assertRaises(Exception, self.ivm.set_current_roi, "test_roi2")
        self.assertFalse("current_roi" in self.sigs_emitted)

    def testSetCurrentRoiNoVolume(self):
        self.assertRaises(Exception, self.ivm.set_current_roi, "test_roi")

    def testGetEnhancementNoVolume(self):
        self.assertRaises(Exception, self.ivm.get_current_enhancement)

    def testGetEnhancementNoOverlays(self):
        self.ivm.set_main_volume(self.vol)
        self.ivm.cim_pos = [0,0,0,0]
        sig, sig_ovl = self.ivm.get_current_enhancement()
        self.assertEquals(0, len(sig_ovl))
        self.assertEquals(TEST_NT, len(sig))

    def testGetEnhancement3dOverlay(self):
        self.ivm.set_main_volume(self.vol)
        ovl = Overlay("test", data=TEST_DATA_3D)
        self.ivm.add_overlay(ovl, make_current=True)
        self.ivm.cim_pos = [0,0,0,0]
        sig, sig_ovl = self.ivm.get_current_enhancement()
        self.assertEquals(0, len(sig_ovl))
        self.assertEquals(TEST_NT, len(sig))

    def testGetEnhancement4dOverlay(self):
        self.ivm.set_main_volume(self.vol)
        ovl = Overlay("test", data=TEST_DATA_4D)
        self.ivm.add_overlay(ovl, make_current=True)
        self.ivm.cim_pos = [0,0,0,0]
        sig, sig_ovl = self.ivm.get_current_enhancement()
        self.assertEquals(1, len(sig_ovl))
        self.assertTrue(sig_ovl.has_key("test"))
        self.assertEquals(TEST_NT, len(sig_ovl["test"]))
        self.assertEquals(TEST_NT, len(sig))

    def testGetEnhancement4dOverlays(self):
        self.ivm.set_main_volume(self.vol)
        ovl = Overlay("test", data=TEST_DATA_4D)
        self.ivm.add_overlay(ovl, make_current=True)
        ovl = Overlay("test2", data=TEST_DATA_4D)
        self.ivm.add_overlay(ovl, make_current=True)
        self.ivm.cim_pos = [0, 0, 0, 0]
        sig, sig_ovl = self.ivm.get_current_enhancement()
        self.assertEquals(2, len(sig_ovl))
        self.assertTrue(sig_ovl.has_key("test"))
        self.assertTrue(sig_ovl.has_key("test2"))
        self.assertEquals(TEST_NT, len(sig_ovl["test"]))
        self.assertEquals(TEST_NT, len(sig_ovl["test2"]))
        self.assertEquals(TEST_NT, len(sig))

    def testOverlayValueCurPos(self):
        self.ivm.set_main_volume(self.vol)
        ovl = Overlay("test", data=TEST_DATA_3D)
        self.ivm.add_overlay(ovl, make_current=True)
        for x in range(TEST_NX):
            for y in range(TEST_NY):
                for z in range(TEST_NZ):
                    for t in range(1):
                        # T should be irrelevant but don't test all values because
                        # it takes too long!
                        self.ivm.cim_pos = [x, y, z, t]
                        vals = self.ivm.get_overlay_value_curr_pos()
                        self.assertEquals(1, len(vals))
                        self.assertTrue(vals.has_key("test"))
                        self.assertEquals(TEST_DATA_3D[x, y, z], vals["test"])

    def testReinitialize(self):
        self.ivm.set_main_volume(self.vol)
        self.sigs_emitted = []
        self.ivm.init(reset=True)
        self.assertTrue(self.ivm.vol is None)
        self.assertTrue(self.ivm.current_overlay is None)
        self.assertEquals(0, len(self.ivm.overlays))
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEquals(0, len(self.ivm.rois))
        self.assertTrue("main_volume" in self.sigs_emitted)
        self.assertTrue("current_overlay" in self.sigs_emitted)
        self.assertTrue("current_roi" in self.sigs_emitted)
        self.assertTrue("all_overlays" in self.sigs_emitted)
        self.assertTrue("all_rois" in self.sigs_emitted)

    def testReinitializeWithRoi(self):
        self.ivm.set_main_volume(self.vol)
        self.ivm.add_roi(Roi("test_roi", data=TEST_DATA_ROI_ALL), make_current=True)
        self.sigs_emitted = []
        self.ivm.init(reset=True)
        self.assertTrue(self.ivm.vol is None)
        self.assertTrue(self.ivm.current_overlay is None)
        self.assertEquals(0, len(self.ivm.overlays))
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEquals(0, len(self.ivm.rois))
        self.assertTrue("main_volume" in self.sigs_emitted)
        self.assertTrue("current_overlay" in self.sigs_emitted)
        self.assertTrue("current_roi" in self.sigs_emitted)
        self.assertTrue("all_overlays" in self.sigs_emitted)
        self.assertTrue("all_rois" in self.sigs_emitted)

    def testReinitializeWithRoiOverlay(self):
        self.ivm.set_main_volume(self.vol)
        self.ivm.add_roi(Roi("test_roi", data=TEST_DATA_ROI_ALL), make_current=True)
        self.ivm.add_overlay(Overlay("test_ovl", data=TEST_DATA_3D), make_current=True)
        self.sigs_emitted = []
        self.ivm.init(reset=True)
        self.assertTrue(self.ivm.vol is None)
        self.assertTrue(self.ivm.current_overlay is None)
        self.assertEquals(0, len(self.ivm.overlays))
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEquals(0, len(self.ivm.rois))
        self.assertTrue("main_volume" in self.sigs_emitted)
        self.assertTrue("current_overlay" in self.sigs_emitted)
        self.assertTrue("current_roi" in self.sigs_emitted)
        self.assertTrue("all_overlays" in self.sigs_emitted)
        self.assertTrue("all_rois" in self.sigs_emitted)


if __name__ == '__main__':
    unittest.main()
