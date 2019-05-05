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
        self.placement.x, self.placement.y = \
            self.placement.width * -10, self.placement.height * -10
        self.placement.visibility = ueberzug.Visibility.VISIBLE
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

        def update_position(self, x, y):
            """Updates the position of the image placement.

            Args:
                x (int): self-explanatory
                y (int): self-explanatory
            """
            self.placement.x, self.placement.y = int(x), int(y)


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
        synchronous (bool):
            immediate (/synchronous) drawing
            after sending a set of commands to ueberzug

    Attributes:
        synchronous (bool):
            immediate (/synchronous) drawing
            after sending a set of commands to ueberzug
    """
    def __init__(self, canvas, *args, synchronous=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.synchronous = synchronous
        self._canvas = canvas
        self._last_visible_placements = set()

    def __update_image_positions(self, canvas):
        stack = [(0, 0, canvas)]
        visible_placements = set()

        while stack:
            x, y, current_canvas = stack.pop()
            if isinstance(current_canvas, Image.Canvas):
                visible_placements.add(current_canvas.placement)
                current_canvas.update_position(x, y)
            elif isinstance(current_canvas, urwid.CompositeCanvas):
                stack += [
                    (child_x + x, child_y + y, child_canvas)
                    for child_x, child_y, child_canvas, *_
                    in current_canvas.children
                ]

        disappeared_placements = \
            (self._last_visible_placements ^
             (self._last_visible_placements & visible_placements))
        for placement in disappeared_placements:
            placement.visibility = ueberzug.Visibility.INVISIBLE

        self._last_visible_placements = visible_placements

    def render(self, size, focus=False):
        with (self._canvas.synchronous_lazy_drawing
              if self.synchronous else
              self._canvas.lazy_drawing):
            canvas = super().render(size, focus)
            self.__update_image_positions(canvas)
            return canvas
