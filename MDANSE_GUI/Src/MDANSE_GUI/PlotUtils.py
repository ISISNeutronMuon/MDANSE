from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from qtpy.QtGui import QIcon, QPixmap


class MDANSEMatPlotLibNavBar(NavigationToolbar2QT):
    def changeEvent(self, event):
        if event.type() == event.PaletteChange:
            for action in self._actions.values():
                pixmap = action.icon().pixmap(24, 24)
                img = pixmap.toImage()
                img.invertPixels()
                new_pixmap = QPixmap.fromImage(img)
                action.setIcon(QIcon(new_pixmap))
        super().changeEvent(event)
