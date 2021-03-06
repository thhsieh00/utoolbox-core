from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .request import Request

logger = logging.getLogger("utoolbox.io.dataset.format")


class Format(ABC):
    """
    Represents an implementation to read/write a particular dataset format.

    Args:
        name (str): short name of this dataset format
        description (str): one-line description of the format
    """

    def __init__(self, name: str, description: str):
        self._name = name
        self._description = description

    def __repr__(self):
        # short description
        return f"<Dataset {self.name} - {self.description}>"

    ##

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    ##

    def get_reader(self, request: Request, **kwargs):
        return self.Reader(self, request, **kwargs)

    def get_writer(self, request: Request, **kwargs):
        return self.Writer(self, request, **kwargs)

    @abstractmethod
    def can_read(self, request: Request) -> bool:
        """
        Whether this dataset can read data from the specified dataset object.

        Args:
            request (Request): TBD
        """

    @abstractmethod
    def can_write(self, request: Request) -> bool:
        """
        Whether this dataset can write data to the specified dataset object.

        Args:
            request (Request): TBD
        """

    ##

    class BaseReaderWriter(ABC):
        """
        Base class for the Reader/Writer class to implement common context managed
        functions.
        """

        def __init__(self, format: Format, request: Request, **kwargs):
            self._format = format
            self._request = request

            # is this reader/writer op already terminated?
            self._closed = False

            # open the dataset
            self.open(**kwargs)  # TODO move open() to __enter__

        def __enter__(self):
            self._assert_closed()
            return self

        def __exit__(self, *exc):
            self._close()  # use the wrapped close

        ##

        @property
        def closed(self) -> bool:
            """Whether the reader/writer is closed."""
            return self._closed

        @property
        def format(self) -> Format:
            """The dataset object corresponding to current read/write operation."""
            return self._format

        @property
        def request(self) -> Request:
            """The uri to dataset corresponding to current read/write operation."""
            return self._request

        ##

        @abstractmethod
        def open(self, **kwargs):
            """
            It is called when the reader/writer is created. Dataset accessor do its
            initialization here in order to granted reader/writer proper environment to
            work with.
            """

        def close(self):
            """
            Called when the reader/writer is closed. 

            Note:
                It has no effect if the dataset is already closed.
            """
            if self.closed:
                return

            self._closed = True
            self._close()

        ##

        def get_index(self):
            pass

        @abstractmethod
        def set_index(self, **index):
            """
            Set the internal pointer such that the next to :func:`.get_next_data()` 
            returns the data specified this index.
            
            Args:
                **index : TBD
            """

        ##

        def _assert_closed(self):
            if self.closed:
                cname = type(self.dataset).__name__
                raise RuntimeError(f"{cname} is already closed")

        def _close(self):
            """Cleanup resources used during dataset access."""

    class Reader(BaseReaderWriter):
        """
        The purpose of a reader object is to read data from a dataset resource, and 
        should be obtained by calling :func:`.get_reader`.
        """

        def __iter__(self):
            self._assert_closed()
            # TODO loop over all the data by setting index sequentially

        @abstractmethod
        def __len__(self):
            """Get the number of data in the dataset."""

        ##

        @abstractmethod
        def get_data(self, **index):
            """
            Read data from the dataset using provided multi-dimensional index.

            Args:
                **index : TBD
            """

        @abstractmethod
        def get_metadata(self, **index):
            """
            Read metadata of the data at provided index. If the index is None, this returns the global metadata.

            Args:
                **index : TBD
            """
            pass

    class Writer(BaseReaderWriter):
        """
        The purpose of a writer object is to write data to a dataset resource, and 
        should be obtained by calling :func:`.get_writer`.
        """

        @abstractmethod
        def set_data(self, data, **index):
            pass

        @abstractmethod
        def set_metadata(self, data: Dict[str, Any]):
            pass


class FormatManager:
    def __init__(self):
        self._formats = []

    def __repr__(self):
        return f"<FormatManager, {len(self)} registered formats>"

    def __iter__(self):
        return iter(self._formats)

    def __len__(self):
        return len(self._formats)

    def __str__(self):
        if not self:
            return "*empty*"

        ss = []
        for format in self:
            s = f"{format.name} - {format.description}"
            ss.append(s)
        return "\n".join(ss)

    ##

    def add_format(self, format: Format, overwrite: bool = False):
        if not isinstance(format, Format):
            raise TypeError("add_format needs argument to be a Format object")
        elif format in self._formats:
            raise ValueError("format is already registered")
        elif format.name in self.get_format_names():
            if overwrite:
                # TODO overwrite existing format
                pass
            else:
                raise ValueError(
                    f'format with name "{format.name}" is already registered'
                )
        self._formats.append(format)

    def search_read_format(self, request: Request) -> Optional[Format]:
        """
        Search a format that can read the uri.

        Args:
            request (Request): TBD
        """
        for f in self._formats:
            if f.can_read(request):
                return f
        else:
            return None

    def search_write_format(self, request: Request) -> Optional[Format]:
        """
        Search a format that can write the uri.

        Args:
            request (Request): TBD
        """
        for f in self._formats:
            if f.can_write(request):
                return f
        else:
            return None

    def get_format_names(self) -> List[str]:
        return [f.name for f in self]

    def show(self):
        """Show formatted list of available formats."""
        print(self)
