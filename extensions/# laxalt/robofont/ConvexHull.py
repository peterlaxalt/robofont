from mojo.roboFont import RGlyph
from fontTools.pens.basePen import BasePen
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber, unregisterGlyphEditorSubscriber, listRegisteredSubscribers
from fontPens.flattenPen import flattenGlyph
from scipy.spatial import ConvexHull

class MyCopyDecomposingPen(BasePen):
    def __init__(self, glyphSet, outPen):
        super(MyCopyDecomposingPen, self).__init__(glyphSet)
        self._moveTo = outPen.moveTo
        self._lineTo = outPen.lineTo
        self._curveToOne = outPen.curveTo
        self._closePath = outPen.closePath
        self._endPath = outPen.endPath


class CentroidPreview(Subscriber):
    debug = False

    def build(self):
        glyphEditor = self.getGlyphEditor()
        self.container = glyphEditor.extensionContainer(
            identifier='com.roboFont.CentroidPreview.background',
            location='background',
            clear=True,
        )
        self.convexHullLayer = self.container.appendPathSublayer(
            strokeColor=(1,0,0,1),
            fillColor=(1,0,0,.05),
            strokeWidth=1,
            )
        self.centroidLayer = self.container.appendSymbolSublayer(
            position=(0,0)
        )

    def destroy(self):
        self.container.clearSublayers()

    def glyphEditorDidSetGlyph(self, info):
        glyph = info['glyph']
        if glyph is not None:
            self.drawCentroid(glyph)

    def glyphEditorGlyphDidChange(self, info):
        glyph = info['glyph']
        if glyph is not None:
            self.drawCentroid(glyph)
        
    def glyphEditorDidMouseDrag(self, info):
        glyph = info['glyph']
        if glyph is not None:
            self.drawCentroid(glyph)


    def centroid(self,vertices):
        # https://stackoverflow.com/questions/75699024/finding-the-centroid-of-a-polygon-in-python
        x, y = 0, 0
        n = len(vertices)
        signed_area = 0
        for i in range(len(vertices)):
            x0, y0 = vertices[i]
            x1, y1 = vertices[(i + 1) % n]
            # shoelace formula
            area = (x0 * y1) - (x1 * y0)
            signed_area += area
            x += (x0 + x1) * area
            y += (y0 + y1) * area
        signed_area *= 0.5
        x /= 6 * signed_area
        y /= 6 * signed_area
        return x, y
    
    def drawCentroid(self, glyph):
        if glyph.isEmpty():
            self.convexHullLayer.setVisible(False)
            self.centroidLayer.setVisible(False)
        else:
            
            self.convexHullLayer.setVisible(True)
            self.centroidLayer.setVisible(True)
            
            tempGlyph = RGlyph()
            tempGlyph.appendGlyph(glyph)
            pen = MyCopyDecomposingPen(glyph.font, tempGlyph.getPen())
            tempGlyph.draw(pen)
            tempGlyph.removeOverlap()
            flattenGlyph(tempGlyph,10)
        
            points = [(point.x,point.y) for contour in tempGlyph.contours for point in contour.points]
            if points:
                hull = ConvexHull(points)
                hullPoints = hull.points[hull.vertices]
    
                pen = self.convexHullLayer.getPen()
                pen.moveTo(hullPoints[0])
                for hp in hullPoints[1:]:
                    pen.lineTo(hp)
                pen.closePath()

                x, y = self.centroid([tuple(p) for p in hullPoints])

                cgPath = pen.path        
                self.convexHullLayer.setPath(cgPath)
            
                self.centroidLayer.setImageSettings(
                    dict(
                        name="star",
                        size=(10,10),
                        fillColor=(1, 0, 0, 1),
                        pointCount=10
                    )
                )
                self.centroidLayer.setPosition((x,y))
            
            
            
if __name__ == '__main__':
    finder = [subs for subs in listRegisteredSubscribers() if 'CentroidPreview' in subs.getIdentifier()]
    if finder:        
        for s in finder:
            unregisterGlyphEditorSubscriber(s)
    else:
        registerGlyphEditorSubscriber(CentroidPreview)
        
            