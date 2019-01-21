
DEFAULT_VIEW_METADATA_MAIN = {
}

DEFAULT_VIEW_METADATA_OVERLAY = {
}

DEFAULT_VIEW_METADATA_ROI = {
    "visible" : True,
    "roi_only" : False,
    "boundary" : "clamp",
    "alpha" : 255,
    "cmap" : "grey",
    "cmap_range" : None,
    "interp_order" : 0,
    "roi-shade" : True,
    "roi-contour" : False,
    "roi-outline_width" : 3.0,
    "z_value" : 1,
}

class OrthoDataView(QtCore.QObject):
    """
    View of a QpData item on a 2D orthographic view
    """
    BOUNDARY_TRANS = 0
    BOUNDARY_CLAMP = 1
    BOUNDARY_LOWERTRANS = 2
    BOUNDARY_UPPERTRANS = 3

    def __init__(self, qpdata, viewbox, **view_metadata):
        """
        :param qpdata: QpData instance
        :param viewbox: pyqtgraph ViewBox instance 
        :param view_metadata: View parameters
        """
        self._qpdata = qpdata
        self._viewbox = viewbox
        self._plane = None
        self._vol = None
        self._qpdata.metadata["DataView"] = dict(view_metadata)
        self._img = MaskableImage()
        self._img.setZValue(-999)
        self._img.setBoundaryMode(self.BOUNDARY_CLAMP)
        self._visible = False
        self._viewbox.addItem(self._img)
        self._histogram.add_img(self._img)

    @property
    def plane(self):
        return self._plane
    
    @plane.setter
    def plane(self, plane):
        if plane != self._plane:
            self._plane = plane
            self.update()

    @property
    def vol(self):
        return self._vol
    
    @vol.setter
    def vol(self, vol):
        if vol != self._vol and vol < self._qpdata.nvols:
            self._vol = vol
            self.update()

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible):
        if visible != self._visible:
            self._visible = visible
            self.update()

    def update(self):
        raise NotImplementedError("OrthoDataView instances must implement update()")

def OrthoMainDataView(OrthoDataView):
    """
    Orthographic view for the main data. 
    
    This is always greyscale and at the bottom of the stack
    """
    def update(self):
        # FIXME interp order
        self._img.setVisible(self._slice is not None and self._visible)
        if self._img.isVisible():
            slicedata, slicemask, scale, offset = self._qpdata.slice_data(self._plane, vol=self._vol, interp_order=1)
            self._img.setTransform(QtGui.QTransform(scale[0, 0], scale[0, 1], scale[1, 0], scale[1, 1], offset[0], offset[1]))
            self._img.setImage(slicedata, autoLevels=False)
            self._img.mask = slicemask
