"""
Custom widgets for the Family Tree application
"""

from .graph_viewer import GraphViewer
from .svg_viewer import SVGViewer
from .web_viewer import SimpleWebViewer, EmbeddedWebViewer
from .embedded_html_viewer import EmbeddedHTMLViewer

__all__ = ['GraphViewer', 'SVGViewer', 'SimpleWebViewer', 'EmbeddedWebViewer', 'EmbeddedHTMLViewer'] 