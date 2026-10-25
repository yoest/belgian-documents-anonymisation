from dataclasses import dataclass

from docling_core.types.doc.base import BoundingBox
from docling_core.types.doc.document import DoclingDocument
from docling_core.types.doc.items.node import NodeItem

# Blocks taller than this (in points, about 3 lines) standing side by side mean a multi-column page
_COLUMN_MIN_HEIGHT = 36.0
# Blocks whose tops are this close (points) are on the same row, ordered left to right
_ROW_TOLERANCE = 5.0


@dataclass(frozen=True, slots=True)
class _Position:
    page: int
    box: BoundingBox  # bottom-left origin: higher `t` means higher on the page


class ReadingOrderCorrector:
    """Fixes Docling's reading order on single-column pages.

    The reading-order model sometimes moves narrow centred blocks, typically a document title, to
    the end of the page. On pages where no blocks stand side by side, top-to-bottom order is
    always right; pages with columns keep the model's order.
    """

    def correct(self, document: DoclingDocument) -> None:
        children = list(document.body.children)
        positions = [self._position(document, ref.resolve(document)) for ref in children]
        single_column_pages = self._single_column_pages(positions)

        keys: list[tuple[int, float, float, int]] = []
        previous: tuple[int, float, float, int] = (0, 0.0, 0.0, 0)
        for index, position in enumerate(positions):
            if position is None:
                # Blocks without a position stay right after the block preceding them
                key = (*previous[:3], index)
            elif position.page in single_column_pages:
                row = -round(position.box.t / _ROW_TOLERANCE)
                key = (position.page, row, position.box.l, index)
            else:
                key = (position.page, float(index), 0.0, index)
            keys.append(key)
            previous = key
        order = sorted(range(len(children)), key=lambda i: keys[i])
        document.body.children = [children[i] for i in order]

    @staticmethod
    def _position(document: DoclingDocument, node: NodeItem) -> _Position | None:
        # Groups (lists...) have no position of their own: use their first positioned item
        for item, _level in document.iterate_items(root=node, with_groups=False):
            provenance = getattr(item, "prov", None)
            if provenance:
                page = provenance[0].page_no
                height = document.pages[page].size.height
                return _Position(page, provenance[0].bbox.to_bottom_left_origin(page_height=height))
        return None

    @staticmethod
    def _single_column_pages(positions: list[_Position | None]) -> set[int]:
        by_page: dict[int, list[BoundingBox]] = {}
        for position in positions:
            if position is not None:
                by_page.setdefault(position.page, []).append(position.box)
        single: set[int] = set()
        for page, boxes in by_page.items():
            tall = [box for box in boxes if box.height > _COLUMN_MIN_HEIGHT]
            side_by_side = any(
                a.overlaps_vertically(b) and not a.overlaps_horizontally(b)
                for i, a in enumerate(tall)
                for b in tall[i + 1 :]
            )
            if not side_by_side:
                single.add(page)
        return single
