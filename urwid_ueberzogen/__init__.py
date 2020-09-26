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

        def reavel_image(self, x, y, width, height):
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

    def _indent_level(self, canvas):
        level = 0
        while hasattr(canvas, "parent_canvas"):
            level += 1
            canvas = canvas.parent_canvas
        return level
    
    def __render_images(self, canvas, size):
        stack = [(0, 0, canvas)]
        visible_placements = set()

        if self._visibility == ueberzug.Visibility.VISIBLE:
            while stack:
                x, y, current_canvas = stack.pop()
                if isinstance(current_canvas, Image.Canvas):
                    first_shard_canvas = current_canvas.shards[0][1][0][-1]
                    visible_placements.add(current_canvas.placement)
                    current_canvas.reavel_image(
                        x=first_shard_canvas.total_ltrim,
                        y=y,
                        height=len(current_canvas.text),
                        width=len(current_canvas.text[0]),
                    )
                elif isinstance(current_canvas, urwid.CompositeCanvas):
                    # need to iterate through the shards, not the children!
                    for child_x, child_y, child_canvas, *other in current_canvas.children:
                        setattr(child_canvas, "parent_canvas", current_canvas)
                        stack.append((
                            child_x + x,
                            child_y + y,
                            child_canvas
                        ))

        disappeared_placements = \
            (self._last_visible_placements ^
             (self._last_visible_placements & visible_placements))
        self.__hide(disappeared_placements)
        self._last_visible_placements = visible_placements

    def render(self, size, focus=False):
        canvas = super().render(size, focus)
        self._calculate_trims(canvas)
        with self._lazy_drawing:
            self.__render_images(canvas, size)
            return canvas

    def _calculate_trims(self, canvas):
        curr_ltrim = 0
        curr_row = 1
        ltrims = [] # start_row, end_row, trim_amt
        for rows, shard in canvas.shards:
            total_row_ltrim = 0
            for ltrim_start, ltrim_end, ltrim_amt in ltrims:
                if ltrim_start <= curr_row < ltrim_end:
                    total_row_ltrim += ltrim_amt

            for idx, cview_info in enumerate(shard):
                _, _, cview_ltrim, cview_rows, _, cview_canvas = cview_info
                if idx == 0:
                    ltrims.append((curr_row, curr_row + cview_rows, cview_ltrim))
                setattr(cview_canvas, "total_ltrim", total_row_ltrim)
                total_row_ltrim += cview_ltrim

            curr_row += rows
