# Urwid ueberzogen

Urwid ueberzogen provides widgets which allows to easily use ueberzug with urwid.  

## pip package

urwid-ueberzogen

## Widgets

The source code contains a more detailed documentation.

### Container

Positions are calculated relative to this widget  
which means that urwid_ueberzogen.Container has to be the root widget  
in order to calculate the absolute position.  

To make it easier to work with placements  
changes are only transmitted on redrawing the urwid layout.  
This also means that for example calling the hide function  
of this class won't do anything till urwid redraws the screen.  
If you want to see changes immediately you have to use it the following way:  

```python
with canvas.lazy_drawing:
    image_container.hide()
```

### Image

Puts an image placement above an urwid widget.
