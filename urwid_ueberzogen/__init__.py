import enum

import urwid
import ueberzug.lib.v0 as ueberzug


class Image(urwid.WidgetWrap):
    """Puts an image placement above the wrapped widgets.

    Args:
        placement (ueberzug.lib.v0.Placement):
            the image placement which should cover the wrapped widgets

    Attributes:
        placement (ueberzug.lib.v0.Placement):
            the image placement which should cover the wrapped widgets
    """
    no_cache = ['render']

    def __init__(self, placement, widget):
        super().__init__(widget)
        self.placement = placement

    def render(self, size, focus=False):
        canvas = self._w.render(size, focus)
        self.placement.width = canvas.cols()
        self.placement.height = canvas.rows()
        return Image.Canvas(self.placement, canvas)

    class Canvas(urwid.CompositeCanvas):
        """CompositeCanvas extended by the function
        to update the position of an associated image placement.

        Args:
            placement (ueberzug.lib.v0.Placement):
                the image placement which should be positioned
                at the same place as the content of this canvas

        Attributes:
            placement (ueberzug.lib.v0.Placement):
                the image placement which should be positioned
                at the same place as the content of this canvas
        """
        def __init__(self, placement, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.placement = placement

        def reavel_image(self, x, y):
            """Displays the image placement at the given position.

            Args:
                x (int): self-explanatory, unit characters
                y (int): self-explanatory, unit characters
            """
            self.placement.x, self.placement.y = int(x), int(y)
            self.placement.visibility = ueberzug.Visibility.VISIBLE


@enum.unique
class DrawingMoment(enum.Enum):
    """Enum which lists the different drawing moments.
    Either synchronous after sending the last command or asynchronous.
    """
    SYNCHRONOUS = 0
    ASYNCHRONOUS = 1


class Container(urwid.WidgetWrap):
    """This widget calculates and updates
    the image placement position of the Image widgets.

    Urwid offers no way to directly get the position of a widget,
    so that's why positions are calculated relative to this widget
    which means that this widget has to be the root widget
    in order to calculate the absolute position.

    Args:
        canvas (ueberzug.lib.v0.Canvas):
            the canvas of the image placements
        visibility (ueberzug.Visibility):
            the visibility of the placements
            of the Image widgets within this container
        drawing_moment (DrawingMoment):
            immediate (/synchronous) drawing
            after sending a set of commands to ueberzug

    Attributes:
        drawing_moment (DrawingMoment):
            immediate (/synchronous) drawing
            after sending a set of commands to ueberzug
    """
    def __init__(self, canvas, *args,
                 visibility=ueberzug.Visibility.VISIBLE,
                 drawing_moment=DrawingMoment.SYNCHRONOUS,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.drawing_moment = drawing_moment
        self._canvas = canvas
        self._visibility = visibility
        self._last_visible_placements = set()
        self._canvas.automatic_transmission = False

    @property
    def _lazy_drawing(self):
        return (self._canvas.synchronous_lazy_drawing
                if self.drawing_moment == DrawingMoment.SYNCHRONOUS else
                self._canvas.lazy_drawing)

    @property
    def visibility(self):
        """ueberzug.Visibility: the visibility of the placements
            of the Image widgets within this container
            Changes will be applied on the next redraw.
        """
        return self._visibility

    @visibility.setter
    def visibility(self, value):
        if value != self._visibility:
            self._visibility = value
            self._invalidate()

    def hide(self):
        """Hides all displayed image placements instantly.

        Images will reappear on the next redraw if this container is visible.
        If this method isn't called in urwid's render method
        it should be called in a block of a lazy_drawing with statement.
        Otherwise needless redraws could happen.
        """
        self.__hide(self._last_visible_placements)

    @staticmethod
    def __hide(placements):
        for placement in placements:
            placement.visibility = ueberzug.Visibility.INVISIBLE

    def __render_images(self, canvas):
        stack = [(0, 0, canvas)]
        visible_placements = set()

        if self._visibility == ueberzug.Visibility.VISIBLE:
            while stack:
                x, y, current_canvas = stack.pop()
                if isinstance(current_canvas, Image.Canvas):
                    visible_placements.add(current_canvas.placement)
                    current_canvas.reavel_image(x, y)
                elif isinstance(current_canvas, urwid.CompositeCanvas):
                    stack += [
                        (child_x + x, child_y + y, child_canvas)
                        for child_x, child_y, child_canvas, *_
                        in current_canvas.children
                    ]

        disappeared_placements = \
            (self._last_visible_placements ^
             (self._last_visible_placements & visible_placements))
        self.__hide(disappeared_placements)
        self._last_visible_placements = visible_placements

    def render(self, size, focus=False):
        with self._lazy_drawing:
            canvas = super().render(size, focus)
            self.__render_images(canvas)
            return canvas
